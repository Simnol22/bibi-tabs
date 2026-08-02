import html
import json

import pytest

from bibi.library import Library
from bibi.render import HtmlRenderer
from bibi.song import Song, looks_like_chords
from bibi.ultimate_guitar import NotAChordPage, UltimateGuitar


class TestChordLineDetection:
    """Only decides colour, but getting it wrong makes the sheet unreadable."""

    @pytest.mark.parametrize("line", ["C G Am F", "  Em7   G   Dsus4  ", "F#m7b5/A Bb", "C"])
    def test_accepts_chord_lines(self, line):
        assert looks_like_chords(line)

    @pytest.mark.parametrize(
        "line",
        [
            "the quick brown fox jumps",
            "[Chorus]",
            "Verse 1:",
            "",
            "     ",
            "Capo on 2nd fret",
        ],
    )
    def test_rejects_everything_else(self, line):
        assert not looks_like_chords(line)

    def test_threshold_is_eighty_percent(self):
        assert not looks_like_chords("C G Am hey")  # 3/4
        assert looks_like_chords("C G Am F hey")  # 4/5


class TestSong:
    def test_slug_is_filename_safe(self):
        assert Song(title="Hey Jude!", artist="The Beatles").slug == "the-beatles-hey-jude"
        assert Song(title="Song / Two").slug == "song-two"

    def test_round_trips_through_text(self):
        song = Song(
            title="Placeholder",
            artist="Nobody",
            capo=2,
            key="F#m",
            source="https://example.test/x",
            body="Em      G\naaaa bbbb cccc\n\nD\ndddd",
        )
        assert Song.from_text(song.to_text()) == song

    def test_body_keeps_its_alignment_exactly(self):
        body = "C       G\naaaa bbbb cccc"
        assert Song.from_text(Song(title="x", body=body).to_text()).body == body

    def test_splits_into_chord_and_lyric_lines(self):
        song = Song(title="x", body="C   G\naaaa bbbb")
        assert [line.is_chords for line in song.lines] == [True, False]


def _page(content, song_name="Placeholder", artist="Nobody", capo=2, key="F#m"):
    """A minimal stand-in for a UG page."""
    blob = {
        "store": {
            "page": {
                "data": {
                    "tab": {"song_name": song_name, "artist_name": artist, "tonality_name": key},
                    "tab_view": {"wiki_tab": {"content": content}, "meta": {"capo": capo}},
                }
            }
        }
    }
    escaped = html.escape(json.dumps(blob), quote=True)
    return f'<div class="js-store" data-content="{escaped}"></div>'


class TestUltimateGuitar:
    def test_reads_metadata(self):
        song = UltimateGuitar().parse(_page("[ch]C[/ch]\r\naaaa"), "https://example.test/x")
        assert (song.title, song.artist, song.capo, song.key) == ("Placeholder", "Nobody", 2, "F#m")
        assert song.source == "https://example.test/x"

    def test_strips_markers_without_disturbing_columns(self):
        # The markers sit on top of already-aligned text, so removing them has
        # to leave every chord exactly where it was.
        content = "[tab][ch]Em[/ch]   [ch]G[/ch]   [ch]D[/ch]\r\naaaa bbbb cccc[/tab]"
        body = UltimateGuitar().parse(_page(content)).body
        assert body == "Em   G   D\naaaa bbbb cccc"
        chords, lyric = body.split("\n")
        assert chords.index("G") == 5 and len(lyric) == 14

    def test_normalises_windows_line_endings(self):
        assert "\r" not in UltimateGuitar().parse(_page("A\r\nB\r\nC")).body

    def test_rejects_a_page_with_no_store(self):
        with pytest.raises(NotAChordPage):
            UltimateGuitar().parse("<html><body>nope</body></html>")

    def test_rejects_a_page_with_no_sheet(self):
        with pytest.raises(NotAChordPage):
            UltimateGuitar().parse(_page(""))

    def test_recognises_its_own_urls(self):
        source = UltimateGuitar()
        assert source.matches("https://tabs.ultimate-guitar.com/tab/oasis/x-chords-1")
        assert not source.matches("wonderwall")


class TestLibrary:
    def test_saves_loads_and_finds(self, tmp_path):
        library = Library(home=tmp_path)
        song = Song(title="Placeholder", artist="Nobody", body="C\naaaa")

        saved = library.save(song)
        assert saved.name == "nobody-placeholder.txt"
        assert library.load(saved) == song
        assert library.find("placeholder") == saved
        assert library.find("nobody placeholder") == saved
        assert library.find("absent") is None

    def test_empty_library_is_not_an_error(self, tmp_path):
        assert Library(home=tmp_path / "missing").paths() == []


class TestHtmlRenderer:
    def test_marks_chord_lines_and_leaves_lyrics_plain(self):
        page = HtmlRenderer().render(Song(title="x", body="C   G\naaaa bbbb"))
        assert '<span class="c">C   G</span>' in page
        assert "aaaa bbbb" in page

    def test_escapes_html_in_the_sheet(self):
        page = HtmlRenderer().render(Song(title="<script>", body="a & b"))
        assert "<script>" not in page.split("<style>")[0].replace("<title>", "")
        assert "a &amp; b" in page

    def test_shows_capo_when_there_is_one(self):
        assert "Capo 2" in HtmlRenderer().render(Song(title="x", capo=2))
        assert "Capo" not in HtmlRenderer().render(Song(title="x", capo=0))
