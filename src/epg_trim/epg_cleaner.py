from __future__ import annotations

import gzip
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Iterator

from lxml import etree

from epg_trim.playlist_parser import normalize_identifier


@dataclass
class FilterStats:
    channels_processed: int = 0
    channels_kept: int = 0
    programmes_processed: int = 0
    programmes_kept: int = 0


def _free_element_memory(element: etree._Element) -> None:
    element.clear()
    while element.getprevious() is not None:
        del element.getparent()[0]


@contextmanager
def _open_epg_stream(epg_path: Path) -> Iterator[BinaryIO]:
    # Some downloads are stored without a .gz suffix; detect gzip via magic bytes.
    with epg_path.open("rb") as probe_stream:
        header = probe_stream.read(2)

    is_gzip = epg_path.suffix.lower() == ".gz" or header == b"\x1f\x8b"

    if is_gzip:
        with gzip.open(epg_path, "rb") as stream:
            yield stream
        return

    with epg_path.open("rb") as stream:
        yield stream


def _collect_kept_channels(
    epg_path: Path,
    identifiers: set[str],
    channels_temp_path: Path,
    stats: FilterStats,
) -> tuple[dict[str, set[str]], set[str], str, dict[str, str], dict[str | None, str]]:
    identifier_to_channel_ids: dict[str, set[str]] = {}
    kept_channel_ids: set[str] = set()
    root_tag = "tv"
    root_attrib: dict[str, str] = {}
    root_nsmap: dict[str | None, str] = {}

    channels_temp_path.parent.mkdir(parents=True, exist_ok=True)
    with etree.xmlfile(channels_temp_path, encoding="utf-8") as channels_writer:
        channels_writer.write_declaration()
        with channels_writer.element("channels"):
            with _open_epg_stream(epg_path) as epg_stream:
                context = etree.iterparse(epg_stream, events=("start", "end"), recover=True)
                for event, element in context:
                    local_name = etree.QName(element.tag).localname if isinstance(element.tag, str) else ""

                    if event == "start" and local_name == "tv" and not root_attrib:
                        root_tag = element.tag
                        root_attrib = dict(element.attrib)
                        root_nsmap = dict(element.nsmap or {})
                        continue

                    if event == "end" and local_name == "channel":
                        stats.channels_processed += 1
                        channel_id = element.get("id")
                        channel_id_norm = normalize_identifier(channel_id)
                        display_name_norms = {
                            normalize_identifier(child.text)
                            for child in element
                            if isinstance(child.tag, str)
                            and etree.QName(child.tag).localname == "display-name"
                            and child.text
                        }

                        matched_identifiers: set[str] = {
                            name for name in display_name_norms if name and name in identifiers
                        }
                        if channel_id_norm and channel_id_norm in identifiers:
                            matched_identifiers.add(channel_id_norm)

                        if channel_id and matched_identifiers:
                            channels_writer.write(element)
                            stats.channels_kept += 1
                            kept_channel_ids.add(channel_id)
                            for matched_identifier in matched_identifiers:
                                identifier_to_channel_ids.setdefault(matched_identifier, set()).add(channel_id)

                        _free_element_memory(element)

    return identifier_to_channel_ids, kept_channel_ids, root_tag, root_attrib, root_nsmap


def _write_filtered_output(
    epg_path: Path,
    channels_temp_path: Path,
    output_xml_path: Path,
    kept_channel_ids: set[str],
    root_tag: str,
    root_attrib: dict[str, str],
    root_nsmap: dict[str | None, str],
    stats: FilterStats,
) -> None:
    output_xml_path.parent.mkdir(parents=True, exist_ok=True)

    with etree.xmlfile(output_xml_path, encoding="utf-8") as xf:
        xf.write_declaration()
        with xf.element(root_tag, attrib=root_attrib, nsmap=root_nsmap):
            with channels_temp_path.open("rb") as channels_stream:
                channels_context = etree.iterparse(channels_stream, events=("end",), recover=True)
                for _, channel_element in channels_context:
                    local_name = etree.QName(channel_element.tag).localname if isinstance(channel_element.tag, str) else ""
                    if local_name != "channel":
                        continue
                    xf.write(channel_element)
                    _free_element_memory(channel_element)

            with _open_epg_stream(epg_path) as epg_stream:
                context = etree.iterparse(epg_stream, events=("end",), recover=True)
                for _, element in context:
                    local_name = etree.QName(element.tag).localname if isinstance(element.tag, str) else ""
                    if local_name != "programme":
                        continue

                    stats.programmes_processed += 1
                    programme_channel = element.get("channel")
                    if programme_channel in kept_channel_ids:
                        xf.write(element)
                        stats.programmes_kept += 1

                    _free_element_memory(element)


def _write_gzip_copy(source_xml_path: Path, output_gzip_path: Path) -> None:
    with source_xml_path.open("rb") as source_file:
        with gzip.open(output_gzip_path, "wb") as gzip_file:
            for chunk in iter(lambda: source_file.read(1024 * 64), b""):
                gzip_file.write(chunk)


def clean_epg(epg_path: Path, identifiers: set[str], output_xml_path: Path, output_gzip_path: Path) -> tuple[Path, Path, FilterStats]:
    stats = FilterStats()
    channels_temp_path = output_xml_path.parent / "_channels.tmp.xml"

    try:
        _, kept_channel_ids, root_tag, root_attrib, root_nsmap = _collect_kept_channels(
            epg_path=epg_path,
            identifiers=identifiers,
            channels_temp_path=channels_temp_path,
            stats=stats,
        )
        _write_filtered_output(
            epg_path=epg_path,
            channels_temp_path=channels_temp_path,
            output_xml_path=output_xml_path,
            kept_channel_ids=kept_channel_ids,
            root_tag=root_tag,
            root_attrib=root_attrib,
            root_nsmap=root_nsmap,
            stats=stats,
        )
        _write_gzip_copy(output_xml_path, output_gzip_path)
        return output_xml_path, output_gzip_path, stats
    finally:
        channels_temp_path.unlink(missing_ok=True)
