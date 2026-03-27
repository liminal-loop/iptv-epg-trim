from __future__ import annotations

import gzip
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from lxml import etree

from epg_trim.epg_cleaner import clean_epg


class EPGCleanerTests(unittest.TestCase):
    def test_clean_epg_filters_channels_and_programmes(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            epg = tmp_path / "input.xml"
            epg.write_text(
                """<?xml version="1.0" encoding="UTF-8"?>
<tv generator-info-name="test-gen">
  <channel id="A-1">
    <display-name>  First Channel HD  </display-name>
  </channel>
  <channel id="B-2">
    <display-name>Second Channel</display-name>
  </channel>
  <programme channel="A-1" start="20260101000000 +0000" stop="20260101010000 +0000">
    <title>Keep me</title>
  </programme>
  <programme channel="B-2" start="20260101000000 +0000" stop="20260101010000 +0000">
    <title>Drop me</title>
  </programme>
</tv>
""",
                encoding="utf-8",
            )

            output_xml = tmp_path / "epg.cleaned.xml"
            output_gz = tmp_path / "epg.cleaned.xml.gz"

            xml_path, gz_path, stats = clean_epg(
                epg_path=epg,
                identifiers={"first channel hd"},
                output_xml_path=output_xml,
                output_gzip_path=output_gz,
            )

            self.assertTrue(xml_path.exists())
            self.assertTrue(gz_path.exists())
            self.assertEqual(stats.channels_processed, 2)
            self.assertEqual(stats.channels_kept, 1)
            self.assertEqual(stats.programmes_processed, 2)
            self.assertEqual(stats.programmes_kept, 1)

            tree = etree.parse(str(output_xml))
            channels = tree.findall("channel")
            programmes = tree.findall("programme")

            self.assertEqual([ch.get("id") for ch in channels], ["A-1"])
            self.assertEqual([pr.get("channel") for pr in programmes], ["A-1"])

            with gzip.open(output_gz, "rb") as gz_file:
                gz_text = gz_file.read().decode("utf-8")
            xml_text = output_xml.read_text(encoding="utf-8")
            self.assertEqual(gz_text, xml_text)

    def test_clean_epg_supports_gz_input(self) -> None:
        source_xml = """<?xml version="1.0" encoding="UTF-8"?>
<tv>
  <channel id="c1"><display-name>One</display-name></channel>
  <programme channel="c1" start="20260101000000 +0000" stop="20260101010000 +0000"><title>X</title></programme>
</tv>
"""
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            epg_gz = tmp_path / "input.xml.gz"
            with gzip.open(epg_gz, "wb") as out:
                out.write(source_xml.encode("utf-8"))

            output_xml = tmp_path / "out.xml"
            output_gz = tmp_path / "out.xml.gz"

            clean_epg(epg_gz, {"c1"}, output_xml, output_gz)

            tree = etree.parse(str(output_xml))
            self.assertEqual(len(tree.findall("channel")), 1)
            self.assertEqual(len(tree.findall("programme")), 1)

        def test_clean_epg_keeps_multiple_channels_for_same_identifier(self) -> None:
          with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            epg = tmp_path / "input.xml"
            epg.write_text(
              """<?xml version="1.0" encoding="UTF-8"?>
      <tv>
        <channel id="A-1"><display-name>Shared Name</display-name></channel>
        <channel id="B-2"><display-name>Shared Name</display-name></channel>
        <programme channel="A-1" start="20260101000000 +0000" stop="20260101010000 +0000"><title>P1</title></programme>
        <programme channel="B-2" start="20260101000000 +0000" stop="20260101010000 +0000"><title>P2</title></programme>
      </tv>
      """,
              encoding="utf-8",
            )

            output_xml = tmp_path / "out.xml"
            output_gz = tmp_path / "out.xml.gz"

            _, _, stats = clean_epg(epg, {"shared name"}, output_xml, output_gz)

            tree = etree.parse(str(output_xml))
            channel_ids = [ch.get("id") for ch in tree.findall("channel")]
            programme_channels = [pr.get("channel") for pr in tree.findall("programme")]

            self.assertEqual(set(channel_ids), {"A-1", "B-2"})
            self.assertEqual(set(programme_channels), {"A-1", "B-2"})
            self.assertEqual(stats.channels_kept, 2)
            self.assertEqual(stats.programmes_kept, 2)

        def test_clean_epg_matches_by_channel_id_per_instructions(self) -> None:
          with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            epg = tmp_path / "input.xml"
            epg.write_text(
              """<?xml version="1.0" encoding="UTF-8"?>
      <tv>
        <channel id="Exact-Id"><display-name>Different Display Name</display-name></channel>
        <programme channel="Exact-Id" start="20260101000000 +0000" stop="20260101010000 +0000"><title>P</title></programme>
      </tv>
      """,
              encoding="utf-8",
            )

            output_xml = tmp_path / "out.xml"
            output_gz = tmp_path / "out.xml.gz"

            clean_epg(epg, {"exact-id"}, output_xml, output_gz)

            tree = etree.parse(str(output_xml))
            self.assertEqual([ch.get("id") for ch in tree.findall("channel")], ["Exact-Id"])
            self.assertEqual([pr.get("channel") for pr in tree.findall("programme")], ["Exact-Id"])


if __name__ == "__main__":
    unittest.main()