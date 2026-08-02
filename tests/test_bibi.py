import html
import json
import re
from pathlib import Path

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


class TestChordParsing:
    def test_splits_a_chord_into_its_parts(self):
        from bibi.chords import Chord

        assert Chord.parse("C") == Chord("C", "", "", None)
        assert Chord.parse("Cm7") == Chord("C", "m", "7", None)
        assert Chord.parse("F#m7b5/A") == Chord("F#", "m", "7b5", "A")

    def test_does_not_mistake_the_m_in_maj_for_minor(self):
        from bibi.chords import Chord

        assert Chord.parse("Cmaj7").quality == "maj"

    def test_rejects_ordinary_words(self):
        from bibi.chords import Chord

        for word in ["Chorus", "Bass", "Dad", "Verse", "N.C."]:
            assert Chord.parse(word) is None, word

    def test_round_trips_to_text(self):
        from bibi.chords import Chord

        for token in ["C", "Cm", "Cmaj7", "F#m7b5/A", "Bb/D", "C7sus4", "G5"]:
            assert str(Chord.parse(token)) == token


class TestTransposingChords:
    def _shift(self, token, semitones, flats=False):
        from bibi.chords import Chord

        return str(Chord.parse(token).transposed(semitones, flats))

    def test_shifts_a_triad(self):
        assert self._shift("C", 2) == "D"
        assert self._shift("A", 3) == "C"

    def test_carries_quality_and_extension_through(self):
        assert self._shift("Cm7", 2) == "Dm7"
        assert self._shift("Cmaj7#11", 2) == "Dmaj7#11"

    def test_shifts_root_and_bass_together(self):
        assert self._shift("C/E", 5) == "F/A"
        assert self._shift("D/F#", -2) == "C/E"

    def test_wraps_around_the_octave(self):
        assert self._shift("B", 2) == "C#"
        assert self._shift("C", -1) == "B"

    def test_spelling_follows_the_target_key(self):
        # Same pitch, two spellings. Sharp keys get sharps, flat keys flats.
        assert self._shift("C", 6, flats=False) == "F#"
        assert self._shift("C", 6, flats=True) == "Gb"


class TestTransposingKeys:
    def test_shifts_major_and_minor(self):
        from bibi.chords import transpose_key

        assert transpose_key("C", 2) == "D"
        assert transpose_key("Am", 2) == "Bm"
        assert transpose_key("F#m", 1) == "Gm"

    def test_prefers_the_spelling_with_fewer_accidentals(self):
        from bibi.chords import transpose_key

        assert transpose_key("A", 1) == "Bb"  # not A#, which needs ten sharps
        assert transpose_key("C", 1) == "Db"  # 5 flats beats 7 sharps

    def test_leaves_a_key_it_cannot_read_alone(self):
        from bibi.chords import transpose_key

        assert transpose_key("", 2) == ""
        assert transpose_key("H", 2) == "H"


class TestTransposingALine:
    """Columns are the product. A chord that moves off its syllable is a bug."""

    def _line(self, text, semitones, key="C"):
        from bibi.chords import Transposer

        return Transposer.for_song(key, "", semitones).line(text)

    def test_keeps_chords_in_their_original_columns(self):
        #        0    5    10
        line = "C    G    Am"
        out = self._line(line, 2)
        assert out == "D    A    Bm"
        assert [m.start() for m in re.finditer(r"\S+", out)] == [0, 5, 10]

    def test_a_widening_chord_still_starts_in_the_same_column(self):
        # C from C major goes up one into Db: two characters where one was.
        out = self._line("C     G", 1)
        assert out.index("Db") == 0
        assert out.index("Ab") == 6

    def test_a_narrowing_chord_holds_its_column_too(self):
        out = self._line("Bb    Eb", -1)
        assert [m.start() for m in re.finditer(r"\S+", out)] == [0, 6]

    def test_pushes_a_collision_right_by_the_minimum(self):
        # Two characters of chord where one used to fit: the next one shifts by
        # exactly one, rather than everything after it drifting.
        assert self._line("C G", 1) == "Db Ab"

    def test_leaves_tokens_that_are_not_chords_alone(self):
        assert "x4" in self._line("C   x4   G", 2)

    def test_zero_semitones_is_the_original_text_untouched(self):
        line = "C     G      Am"
        assert self._line(line, 0) == line

    def test_spells_from_the_key_the_song_lands_in(self):
        from bibi.chords import Transposer

        # A up one is Bb major, so the chords read flat.
        assert Transposer.for_song("A", "", 1).line("A D") == "Bb Eb"
        # D up one is Eb major.
        assert Transposer.for_song("D", "", 1).line("D G") == "Eb Ab"
        # G up two is A major, which is sharp.
        assert Transposer.for_song("G", "", 2).line("G C") == "A D"

    def test_stops_at_the_twelve_practical_note_names(self):
        from bibi.chords import Transposer

        # F up one lands in Gb major, where strict theory spells pitch 11 as Cb.
        # We print B. Chasing Cb and E# needs a per-key diatonic speller and
        # puts chords on the page no guitarist wants to read.
        assert Transposer.for_song("F", "", 1).line("F Bb") == "Gb B"

    def test_falls_back_to_the_accidentals_already_on_the_sheet(self):
        from bibi.chords import Transposer

        flat_song = Transposer.for_song("", "Bb Eb Ab", 1)
        assert flat_song.flats is True


class TestFingerings:
    def test_finds_the_open_shape_for_a_plain_triad(self):
        from bibi.fingering import shapes

        found = shapes("C")
        assert len(found) > 1  # alternate voicings exist
        assert found[0].frets == (-1, 3, 2, 0, 1, 0)
        assert found[0].base_fret == 1

    @pytest.mark.parametrize(
        "token", ["Am", "Cm7", "G7", "Fmaj7", "Dsus4", "Eadd9", "Bdim", "Caug", "A7sus4"]
    )
    def test_finds_the_usual_shapes(self, token):
        from bibi.fingering import shapes

        assert shapes(token), token

    def test_reads_a_barre_as_a_barre(self):
        from bibi.fingering import shapes

        assert shapes("F")[0].barres

    def test_enharmonic_roots_are_the_same_chord(self):
        from bibi.fingering import shapes

        assert shapes("Db") == shapes("C#")
        assert shapes("D#m") == shapes("Ebm")

    def test_accepts_the_quality_spellings_the_parser_allows(self):
        from bibi.fingering import shapes

        assert shapes("C-7") == shapes("Cm7")
        assert shapes("C+") == shapes("Caug")

    def test_falls_back_to_the_base_chord_for_an_unknown_bass(self):
        from bibi.fingering import shapes

        # Better the F#m7b5 shape than an empty box.
        assert shapes("F#m7b5/A") == shapes("F#m7b5")

    @pytest.mark.parametrize("token", ["N.C.", "Chorus", "", "Cmaj7b13"])
    def test_returns_nothing_rather_than_guessing(self, token):
        from bibi.fingering import shapes

        assert shapes(token) == ()

    def test_every_root_has_a_major_and_a_minor(self):
        from bibi.fingering import shapes

        for root in ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]:
            assert shapes(root), root
            assert shapes(f"{root}m"), f"{root}m"


class TestBarreDiagrams:
    """A barre is one finger doing one thing, so it gets one number."""

    def _svg(self, token, voicing=0):
        from bibi.diagram import symbol
        from bibi.fingering import shapes

        return symbol(shapes(token)[voicing], 0)

    def _dot_numbers(self, svg):
        return re.findall(r'fill="var\(--bg\)">(\d)<', svg)

    def _margin_numbers(self, svg):
        return re.findall(r'text-anchor="end" fill="currentColor">(\d)<', svg)

    def test_barred_strings_carry_no_number_of_their_own(self):
        # F is barred at fret 1 across three strings; that used to print "1"
        # three times over.
        svg = self._svg("F")
        assert self._dot_numbers(svg) == ["3", "4", "2"]  # only the free fingers
        assert "1" not in self._dot_numbers(svg)

    def test_the_barre_finger_goes_in_the_margin(self):
        assert self._margin_numbers(self._svg("F")) == ["1"]
        assert self._margin_numbers(self._svg("Bm")) == ["1"]

    def test_the_margin_number_is_not_always_one(self):
        # This C6 shape barres with the third finger. A hardcoded "1" would lie.
        assert self._margin_numbers(self._svg("C6", voicing=1)) == ["3"]

    def test_a_negative_finger_is_not_printed_as_a_number(self):
        # Some rows use -1 rather than 0 for "no finger" on a muted string.
        assert "-1" not in self._svg("F", voicing=1)

    def test_barred_positions_draw_no_separate_dot(self):
        from bibi.fingering import shapes

        shape = shapes("F")[0]
        fretted = sum(1 for f in shape.frets if f > 0)
        barred = sum(1 for f in shape.frets if f in shape.barres)
        assert len(re.findall(r"<circle", self._svg("F"))) == fretted - barred

    def test_an_open_chord_keeps_its_numbers_in_the_dots(self):
        svg = self._svg("Em")
        assert self._dot_numbers(svg) == ["2", "3"]
        assert self._margin_numbers(svg) == []

    def test_the_base_fret_stays_on_the_other_side(self):
        # Right margin, so it can never be mistaken for the barre finger.
        svg = self._svg("Bb", voicing=1)  # this one starts at the third fret
        assert re.search(r'opacity="\.7">3</text>', svg)
        assert self._margin_numbers(svg) == ["1"]

    def test_every_shape_fits_the_fixed_box(self):
        from bibi.diagram import HEIGHT, WIDTH
        from bibi.fingering import shapes

        for token in ["C", "F", "Bm", "C6", "F#m7b5", "Ab", "D#m"]:
            for shape in shapes(token):
                assert max(shape.frets) <= 4, token
        assert (WIDTH, HEIGHT) == (111, 102)


class TestDiagramsOnThePage:
    def _page(self, body, **kw):
        return HtmlRenderer().render(Song(title="x", body=body, **kw))

    def test_each_chord_becomes_a_hover_target(self):
        page = self._page("C   G\naaaa bbbb")
        assert page.count('class="ch"') == 2

    def test_a_chord_is_reachable_without_a_mouse(self):
        # Hover alone would leave touch and keyboard users with nothing.
        assert 'tabindex="0"' in self._page("C\naaaa")

    def test_a_distinct_chord_is_drawn_once_however_often_it_appears(self):
        page = self._page("C   C   C\naaaa\nC   G\nbbbb")
        assert page.count("<symbol ") == 2  # C and G, not five copies
        assert page.count("<use ") == 5

    def test_a_chord_with_no_known_shape_is_left_as_plain_text(self):
        page = self._page("Cmaj7b13 x4\naaaa")
        assert "Cmaj7b13" in page
        assert 'class="ch"' not in page

    def test_columns_survive_the_markup(self):
        # The spans add no characters, so the sheet still lines up.
        page = self._page("C    G\naaaa bbbb")
        line = re.search(r'<span class="c">(.*?)</span>\n', page, re.S).group(1)
        assert re.sub(r"<[^>]+>", "", line) == "C    G"

    def test_diagrams_follow_the_transposition(self):
        from bibi.diagram import Diagrams
        from bibi.fingering import shapes

        page = HtmlRenderer().render(Song(title="x", key="C", body="C\naaaa"), semitones=2)
        # Shifted to D, so the D shape is what gets drawn.
        expected = Diagrams()
        expected.add("D")
        assert expected.defs() in page

    def test_no_definitions_when_nothing_is_recognised(self):
        assert "<symbol" not in self._page("aaaa bbbb\ncccc")


class TestSong:
    def test_slug_is_filename_safe(self):
        assert Song(title="Hey Jude!", artist="The Beatles").slug == "the-beatles-hey-jude"
        assert Song(title="Song / Two").slug == "song-two"

    def test_slug_folds_accents_instead_of_dropping_them(self):
        # Most French titles hit this; dropping gives "dr-le-de-temps".
        assert Song(title="Drôle de temps").slug == "drole-de-temps"
        assert Song(title="Été", artist="Coeur de Pirate").slug == "coeur-de-pirate-ete"

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


def _search_page(results):
    blob = {"store": {"page": {"data": {"results": results}}}}
    return f'<div class="js-store" data-content="{html.escape(json.dumps(blob), quote=True)}"></div>'


def _hit(name="Placeholder", type_="Chords", host="tabs.ultimate-guitar.com", votes=10, **kw):
    return {
        "song_name": name,
        "artist_name": "Nobody",
        "type": type_,
        "tab_url": f"https://{host}/tab/nobody/x-chords-1",
        "version": 2,
        "rating": 4.5,
        "votes": votes,
        **kw,
    }


class TestSearch:
    def test_reads_results(self):
        found = UltimateGuitar().parse_search(_search_page([_hit()]))
        assert len(found) == 1
        assert (found[0].title, found[0].artist, found[0].version) == ("Placeholder", "Nobody", 2)
        assert (found[0].rating, found[0].votes) == (4.5, 10)

    def test_drops_paid_pro_entries(self):
        # These carry no sheet, so fetching one would only ever error.
        page = _search_page(
            [_hit(type_=None, host="www.ultimate-guitar.com"), _hit()]
        )
        assert len(UltimateGuitar().parse_search(page)) == 1

    def test_drops_anything_not_on_the_sheet_host(self):
        assert UltimateGuitar().parse_search(_search_page([_hit(host="evil.test")])) == []

    def test_most_voted_first(self):
        page = _search_page([_hit(votes=10), _hit(votes=900), _hit(votes=100)])
        assert [r.votes for r in UltimateGuitar().parse_search(page)] == [900, 100, 10]

    def test_no_results_is_not_an_error(self):
        assert UltimateGuitar().parse_search(_search_page([])) == []


class TestUrlMatching:
    """The local /add endpoint fetches whatever this approves, so it is strict."""

    @pytest.mark.parametrize(
        "url",
        [
            "https://tabs.ultimate-guitar.com/tab/oasis/x-chords-1",
            "https://www.ultimate-guitar.com/search.php?value=x",
        ],
    )
    def test_accepts_real_ug_urls(self, url):
        assert UltimateGuitar().matches(url)

    @pytest.mark.parametrize(
        "url",
        [
            "https://evil-ultimate-guitar.com/tab/x",  # substring match would pass this
            "https://ultimate-guitar.com.evil.test/x",
            "file:///etc/passwd",
            "http://127.0.0.1:8777/add",
            "wonderwall",
            "",
        ],
    )
    def test_rejects_everything_else(self, url):
        assert not UltimateGuitar().matches(url)

    def test_fetch_refuses_a_url_it_does_not_own(self):
        with pytest.raises(NotAChordPage):
            UltimateGuitar().fetch("https://evil.test/x")


class TestServer:
    """Page building only -- no sockets involved."""

    def _server(self, tmp_path, source=None):
        from bibi.server import Server

        return Server(library=Library(home=tmp_path), source=source or UltimateGuitar())

    def test_index_lists_saved_songs(self, tmp_path):
        server = self._server(tmp_path)
        server.library.save(Song(title="Placeholder", artist="Nobody", body="C\naaaa"))
        page = server.index_page()
        assert "Placeholder" in page and 'href="/song/nobody-placeholder"' in page

    def test_index_says_so_when_empty(self, tmp_path):
        assert "Nothing saved yet" in self._server(tmp_path).index_page()

    def test_song_page_renders_a_saved_song(self, tmp_path):
        server = self._server(tmp_path)
        server.library.save(Song(title="Placeholder", body="C   G\naaaa bbbb"))
        page = server.song_page("placeholder")
        assert 'class="c"' in page and ">C<" in page
        assert "aaaa bbbb" in page

    def test_song_page_is_none_when_missing(self, tmp_path):
        assert self._server(tmp_path).song_page("nope") is None

    @pytest.mark.parametrize("slug", ["../../etc/passwd", "a/b", ".hidden", ""])
    def test_song_page_refuses_to_escape_the_library(self, tmp_path, slug):
        assert self._server(tmp_path).song_page(slug) is None

    @pytest.mark.parametrize("action", ["view_page", "save"])
    def test_refuses_a_foreign_url_before_fetching(self, tmp_path, action):
        class Exploder(UltimateGuitar):
            def fetch(self, url):
                raise AssertionError("should never have been called")

        server = self._server(tmp_path, Exploder())
        with pytest.raises(NotAChordPage):
            getattr(server, action)("https://evil.test/x")

    def test_search_page_survives_the_network_being_down(self, tmp_path):
        class Offline(UltimateGuitar):
            def search(self, query):
                raise OSError("no network")

        page = self._server(tmp_path, Offline()).search_page("wonderwall")
        assert "Nothing found" in page and "Saved" in page

    def test_blank_search_just_shows_the_library(self, tmp_path):
        assert "Results for" not in self._server(tmp_path).search_page("   ")

    def test_results_link_to_a_preview_not_a_save(self, tmp_path):
        from bibi.song import SearchResult

        class Found(UltimateGuitar):
            def search(self, query):
                return [SearchResult(title="P", artist="N", url="https://x.test/a")]

        page = self._server(tmp_path, Found()).search_page("p")
        assert "/view?url=" in page and "/save?url=" not in page


class TestViewingBeforeSaving:
    """Opening a song must not put it in the library."""

    def _server(self, tmp_path, song):
        from bibi.server import Server

        class Fixed(UltimateGuitar):
            def fetch(self, url):
                return song

        return Server(library=Library(home=tmp_path), source=Fixed())

    def test_viewing_does_not_save(self, tmp_path):
        song = Song(title="Placeholder", artist="Nobody", body="C\naaaa")
        server = self._server(tmp_path, song)

        page = server.view_page("https://tabs.ultimate-guitar.com/tab/x-chords-1")

        assert server.library.paths() == []
        assert 'action="/save"' in page
        assert "aaaa" in page

    def test_saving_keeps_it(self, tmp_path):
        song = Song(title="Placeholder", artist="Nobody", body="C\naaaa")
        server = self._server(tmp_path, song)

        slug = server.save("https://tabs.ultimate-guitar.com/tab/x-chords-1")

        assert slug == "nobody-placeholder"
        assert [p.stem for p in server.library.paths()] == ["nobody-placeholder"]

    def test_a_song_already_saved_offers_no_save_button(self, tmp_path):
        song = Song(title="Placeholder", artist="Nobody", body="C\naaaa")
        server = self._server(tmp_path, song)
        server.library.save(song)

        page = server.view_page("https://tabs.ultimate-guitar.com/tab/x-chords-1")

        assert 'action="/save"' not in page
        assert "Saved" in page

    def test_every_server_page_can_get_home(self, tmp_path):
        song = Song(title="Placeholder", body="C\naaaa")
        server = self._server(tmp_path, song)
        server.library.save(song)

        for page in [
            server.view_page("https://tabs.ultimate-guitar.com/tab/x-chords-1"),
            server.song_page("placeholder"),
        ]:
            assert 'href="/"' in page

    def test_the_standalone_file_has_no_dead_back_link(self, tmp_path):
        # The CLI writes a file:// page -- a link to "/" would go nowhere.
        page = HtmlRenderer().render(Song(title="Placeholder", body="C\naaaa"))
        assert 'href="/"' not in page


class TestDeleting:
    def _server(self, tmp_path):
        from bibi.server import Server

        return Server(library=Library(home=tmp_path))

    def test_removes_the_file(self, tmp_path):
        server = self._server(tmp_path)
        server.library.save(Song(title="Placeholder", artist="Nobody"))

        server.delete("nobody-placeholder")

        assert server.library.paths() == []

    def test_deleting_something_absent_is_harmless(self, tmp_path):
        self._server(tmp_path).delete("nope")

    @pytest.mark.parametrize("slug", ["../../../etc/passwd", "a/b", ".bashrc", ""])
    def test_refuses_to_delete_outside_the_library(self, tmp_path, slug):
        assert self._server(tmp_path).library.delete(slug) is False

    def test_landing_page_offers_a_delete_for_each_song(self, tmp_path):
        server = self._server(tmp_path)
        server.library.save(Song(title="Placeholder", artist="Nobody"))

        page = server.index_page()

        assert 'method="post" action="/delete"' in page
        assert 'value="nobody-placeholder"' in page


class TestConfig:
    def test_defaults_when_there_is_no_config(self, tmp_path):
        from bibi.config import DEFAULT_LIBRARY, Config

        assert Config(path=tmp_path / "absent.json").library == DEFAULT_LIBRARY

    def test_remembers_a_library_path(self, tmp_path):
        from bibi.config import Config

        config = Config(path=tmp_path / "cfg.json")
        config.set_library(tmp_path / "songs")

        assert Config(path=tmp_path / "cfg.json").library == tmp_path / "songs"

    def test_expands_a_tilde(self, tmp_path):
        from bibi.config import Config

        config = Config(path=tmp_path / "cfg.json")
        (tmp_path / "cfg.json").write_text('{"library": "~/elsewhere"}')

        assert config.library == Path.home() / "elsewhere"

    def test_a_corrupt_config_falls_back_rather_than_crashing(self, tmp_path):
        from bibi.config import DEFAULT_LIBRARY, Config

        path = tmp_path / "cfg.json"
        path.write_text("{ this is not json")

        assert Config(path=path).library == DEFAULT_LIBRARY


class TestChangingTheLibraryFolder:
    def _server(self, tmp_path):
        from bibi.config import Config
        from bibi.server import Server

        return Server(
            library=Library(home=tmp_path / "old"),
            config=Config(path=tmp_path / "cfg.json"),
        )

    def test_moves_the_songs_along(self, tmp_path):
        server = self._server(tmp_path)
        server.library.save(Song(title="Placeholder", artist="Nobody", body="C\naaaa"))

        server.set_library(str(tmp_path / "new"))

        assert (tmp_path / "new" / "nobody-placeholder.txt").is_file()
        assert not (tmp_path / "old" / "nobody-placeholder.txt").exists()
        assert server.library.home == tmp_path / "new"

    def test_the_choice_survives_a_restart(self, tmp_path):
        from bibi.config import Config

        self._server(tmp_path).set_library(str(tmp_path / "new"))

        assert Config(path=tmp_path / "cfg.json").library == tmp_path / "new"

    def test_never_overwrites_a_song_already_there(self, tmp_path):
        server = self._server(tmp_path)
        server.library.save(Song(title="Placeholder", body="C\nfrom old"))
        (tmp_path / "new").mkdir()
        (tmp_path / "new" / "placeholder.txt").write_text("title: Placeholder\n\nkeep me")

        server.set_library(str(tmp_path / "new"))

        assert "keep me" in (tmp_path / "new" / "placeholder.txt").read_text()

    @pytest.mark.parametrize("bad", ["", "   ", "songs", "./songs"])
    def test_rejects_anything_that_is_not_a_full_path(self, tmp_path, bad):
        server = self._server(tmp_path)

        page = server.set_library(bad)

        assert "Give a full path" in page
        assert server.library.home == tmp_path / "old"

    def test_settings_page_shows_where_songs_are(self, tmp_path):
        assert str(tmp_path / "old") in self._server(tmp_path).settings_page()

    def test_landing_page_links_to_settings(self, tmp_path):
        assert 'href="/settings"' in self._server(tmp_path).index_page()


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
        assert 'class="c"' in page
        assert "aaaa bbbb" in page

    def test_escapes_html_in_the_sheet(self):
        page = HtmlRenderer().render(Song(title="<script>", body="a & b"))
        assert "<script>" not in page.split("<style>")[0].replace("<title>", "")
        assert "a &amp; b" in page

    def test_shows_capo_when_there_is_one(self):
        assert "Capo 2" in HtmlRenderer().render(Song(title="x", capo=2))
        assert "Capo" not in HtmlRenderer().render(Song(title="x", capo=0))
