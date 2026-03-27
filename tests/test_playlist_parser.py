from __future__ import annotations

from pathlib import Path
import unittest

from epg_trim.playlist_parser import parse_playlist_identifiers


class PlaylistParserTests(unittest.TestCase):
    def test_parse_playlist_identifiers_priority_and_normalization(self) -> None:
        with self.subTest("priority and normalization"):
            from tempfile import TemporaryDirectory

            with TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                playlist = tmp_path / "playlist.m3u"
                playlist.write_text(
                    "\n".join(
                        [
                            "#EXTM3U",
                            '#EXTINF:-1 tvg-id="ARD.DE" tvg-name="ARD Name",Das Erste',
                            "http://example/1",
                            '#EXTINF:-1 tvg-name="   Channel Two   ",Ignored Display',
                            "http://example/2",
                            "#EXTINF:0 tvg-rec=\"0\",  First Channel HD  ",
                            "http://example/3",
                            "#EXTINF:0 tvg-rec=\"0\",FIRST CHANNEL HD",
                            "http://example/4",
                        ]
                    ),
                    encoding="utf-8",
                )

                identifiers = parse_playlist_identifiers(playlist)
                self.assertEqual(identifiers, {"ard.de", "channel two", "first channel hd"})

    def test_parse_playlist_identifiers_supports_utf8_bom(self) -> None:
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            playlist = tmp_path / "playlist.m3u8"
            content = "\ufeff#EXTM3U\n#EXTINF:-1, My Channel \nhttp://example/stream\n"
            playlist.write_text(content, encoding="utf-8")

            identifiers = parse_playlist_identifiers(playlist)
            self.assertEqual(identifiers, {"my channel"})


if __name__ == "__main__":
    unittest.main()