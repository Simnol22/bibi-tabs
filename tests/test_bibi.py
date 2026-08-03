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


class TestBracketedAndPunctuation:
    """Real sheets decorate chord lines. Found in a live song, where
    `G  (Dmaj7)` scored 1/2 and the whole line stopped reading as chords --
    it rendered as a lyric and could not be edited."""

    def test_a_chord_in_brackets_is_still_a_chord(self):
        from bibi.chords import chord_in

        assert chord_in("(Dmaj7)") == chord_in("Dmaj7")
        assert chord_in("[Am]") == chord_in("Am")

    def test_brackets_inside_a_chord_are_left_alone(self):
        from bibi.chords import Chord, chord_in

        assert chord_in("C(add9)") == Chord.parse("C(add9)")

    def test_a_line_of_optional_chords_reads_as_chords(self):
        assert looks_like_chords("G      (Dmaj7)")
        assert looks_like_chords("(D)")

    def test_bar_lines_count_neither_way(self):
        # Counting them against the line would drag it under the threshold.
        assert looks_like_chords("| C | G | Am |")
        assert looks_like_chords("C  /  /  G")
        assert not looks_like_chords("|")

    def test_transposing_keeps_the_brackets(self):
        from bibi.chords import Transposer

        assert Transposer.for_song("C", "", 2).line("(Dmaj7)") == "(Emaj7)"
        assert Transposer.for_song("C", "", 2).line("| C | G |") == "| D | A |"

    def test_a_bracketed_chord_still_has_a_shape(self):
        from bibi.fingering import shapes

        assert shapes("(Dmaj7)") == shapes("Dmaj7")

    def test_a_bracketed_chord_is_not_muted_as_a_non_chord(self):
        page = HtmlRenderer().render(Song(title="T", body="G      (Dmaj7)\naaaa bbbb"))
        assert 'class="nc"' not in page
        assert 'class="c"' in page


class TestChordsAmongWords:
    """A chord in an intro note or annotation sits on a line that never reaches
    the 80% threshold. Measured across four real songs: doing this per token
    gains 4 genuine chords and costs 4 false positives, all of them single
    letters -- which is exactly what the ambiguity rule excludes."""

    def _page(self, body, **kw):
        return HtmlRenderer().render(Song(title="T", body=body, **kw))

    def test_an_unmistakable_spelling_counts_anywhere(self):
        from bibi.chords import unambiguous_chord

        for token in ["Dmaj7", "A7sus4", "Bb", "F#m7b5", "C7", "Em"]:
            assert unambiguous_chord(token), token

    def test_a_spelling_that_is_also_a_word_does_not(self):
        from bibi.chords import unambiguous_chord

        for token in ["A", "C", "E", "G", "Am"]:
            assert unambiguous_chord(token) is None, token

    def test_a_chord_among_words_is_coloured_and_hoverable(self):
        page = self._page("Intro : Dmaj7 puis on repart\naaaa bbbb")
        assert '<span class="ch" tabindex="0">Dmaj7' in page

    def test_a_lone_letter_among_words_is_left_alone(self):
        page = self._page("aaaa A bbbb cccc dddd\neeee")
        assert 'class="ch"' not in page

    def test_a_stray_chord_still_moves_with_the_transposition(self):
        # Left behind, it would say Dmaj7 while every real chord had shifted.
        page = self._page("Intro : Dmaj7 puis on repart\naaaa", key="D")
        assert "Dmaj7" in page
        shifted = HtmlRenderer().render(
            Song(title="T", key="D", body="Intro : Dmaj7 puis on repart\naaaa"), semitones=2
        )
        assert "Emaj7" in shifted and ">Dmaj7<" not in shifted

    def test_the_rest_of_the_line_stays_plain(self):
        page = self._page("Intro : Dmaj7 puis on repart\naaaa")
        assert "puis on repart" in page
        assert 'class="nc"' not in page  # words are not muted typos


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

    def _marker(self, svg):
        return re.findall(r'text-anchor="end"[^>]*>(\d+)fr<', svg)

    def test_barred_strings_carry_no_number_of_their_own(self):
        # F is barred across three strings; that used to print "1" three times.
        svg = self._svg("F")
        assert self._dot_numbers(svg) == ["3", "4", "2"]  # only the free fingers
        assert "1" not in self._dot_numbers(svg)

    def test_the_marker_gives_the_fret_the_barre_sits_on(self):
        # F#m barres the 2nd fret. A bare "1" there read as a fret and was the
        # finger, which is exactly the confusion "fr" removes.
        assert self._marker(self._svg("F#m")) == ["2"]
        assert self._marker(self._svg("Bm")) == ["2"]
        assert self._marker(self._svg("F")) == ["1"]

    def test_the_marker_counts_from_where_the_diagram_starts(self):
        from bibi.diagram import symbol
        from bibi.fingering import Shape

        # Grid begins at fret 5, barre on its second row: that is fret 6.
        shape = Shape(frets=(2, 2, 2, 2, 2, 2), fingers=(1,) * 6, base_fret=5, barres=(2,))
        assert self._marker(symbol(shape, 0)) == ["6"]

    def test_a_shape_up_the_neck_is_labelled_even_without_a_barre(self):
        from bibi.diagram import symbol
        from bibi.fingering import Shape

        shape = Shape(frets=(-1, 1, 3, 3, 3, -1), fingers=(0, 1, 2, 3, 4, 0), base_fret=7)
        assert self._marker(symbol(shape, 0)) == ["7"]

    def test_an_open_shape_at_the_nut_needs_no_marker(self):
        assert self._marker(self._svg("Em")) == []
        assert self._marker(self._svg("C")) == []

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
        assert self._marker(svg) == []

    def test_there_is_only_ever_one_fret_marker(self):
        # It used to be two numbers on opposite sides -- barre finger left,
        # base fret right -- which is what made either one ambiguous.
        for token in ["F", "F#m", "Bm", "C", "Em", "Bb"]:
            assert len(self._marker(self._svg(token))) <= 1, token

    def test_every_shape_fits_the_fixed_box(self):
        from bibi.diagram import HEIGHT, WIDTH
        from bibi.fingering import shapes

        for token in ["C", "F", "Bm", "C6", "F#m7b5", "Ab", "D#m"]:
            for shape in shapes(token):
                assert max(shape.frets) <= 4, token
        assert (WIDTH, HEIGHT) == (113, 102)


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


def _bac_page(lines, title="Chanson (Nobody) - Paroles et accords - x", capo="II", key="Db"):
    """A minimal stand-in for a boiteachansons.net page."""
    body = "".join(lines)
    return (
        f'<meta property="og:title" content="{title}">'
        f'<input type="hidden" id="tonalite" name="tonalite" value="{key}">'
        f'<input type="hidden" id="capo" name="capo" value="{capo}">'
        '<div style="display:none;" id="divPartitionPerso" class="divPartition">'
        '<div class="pL">ignored, this is the hidden edit copy</div></div>'
        f'<div id="divPartition" class="divPartition">{body}</div>'
    )


def _pl(*pieces):
    inner = "".join(
        f'<span class="a" data-a="{p[1:]}"></span>' if p.startswith("@") else p
        for p in pieces
    )
    return f'<div class="pL">{inner}</div>'


class TestBoiteAChansons:
    def _parse(self, page, url="https://www.boiteachansons.net/partitions/a/b"):
        from bibi.boite_a_chansons import BoiteAChansons

        return BoiteAChansons().parse(page, url)

    def test_builds_columns_from_inline_anchors(self):
        # Their chords are anchored between syllables rather than positioned in
        # a column, so the alignment has to be constructed: F belongs above the
        # third word, which starts at column 10.
        song = self._parse(_bac_page([_pl("@Em", "aaaa bbbb ", "@F", "cccc")]))
        chords, lyric = song.body.split("\n")
        assert lyric == "aaaa bbbb cccc"
        assert [(m.group(), m.start()) for m in re.finditer(r"\S+", chords)] == [
            ("Em", 0),
            ("F", 10),
        ]
        assert lyric[10] == "c"

    def test_a_line_with_no_chords_stays_a_single_line(self):
        assert self._parse(_bac_page([_pl("aaaa bbbb")])).body == "aaaa bbbb"

    def test_reads_the_metadata(self):
        song = self._parse(_bac_page([_pl("@C", "aaaa")]))
        assert (song.title, song.artist) == ("Chanson", "Nobody")
        assert song.key == "Db"
        assert song.site == "Boîte à Chansons"

    def test_reads_a_roman_numeral_capo(self):
        # They write "Capo III", not "Capo 3".
        assert self._parse(_bac_page([_pl("@C", "a")], capo="III")).capo == 3
        assert self._parse(_bac_page([_pl("@C", "a")], capo="")).capo == 0

    def test_ignores_the_hidden_edit_copy(self):
        assert "hidden edit copy" not in self._parse(_bac_page([_pl("@C", "aaaa")])).body

    def test_section_labels_survive_as_their_own_lines(self):
        page = _bac_page(['<div class="pLS">Refrain</div>', _pl("@C", "aaaa")])
        assert "Refrain" in self._parse(page).body.split("\n")

    def test_a_page_with_no_sheet_is_rejected(self):
        from bibi.boite_a_chansons import BoiteAChansons

        with pytest.raises(NotAChordPage):
            BoiteAChansons().parse("<html><body>rien</body></html>")

    @pytest.mark.parametrize(
        "url",
        ["https://www.boiteachansons.net/partitions/a/b", "https://boiteachansons.net/x"],
    )
    def test_accepts_its_own_urls(self, url):
        from bibi.boite_a_chansons import BoiteAChansons

        assert BoiteAChansons().matches(url)

    @pytest.mark.parametrize(
        "url",
        [
            "https://evil-boiteachansons.net/x",  # substring matching would pass this
            "https://boiteachansons.net.evil.test/x",
            "https://tabs.ultimate-guitar.com/tab/x",
            "file:///etc/passwd",
        ],
    )
    def test_rejects_everything_else(self, url):
        from bibi.boite_a_chansons import BoiteAChansons

        assert not BoiteAChansons().matches(url)


class TestBoiteAChansonsSearch:
    def _results(self, page):
        from bibi.boite_a_chansons import BoiteAChansons

        return BoiteAChansons()._results(page)

    def _link(self, href, title):
        return f'<a data="on-affiche" href="{href}" title="{title}">x</a>'

    def test_reads_title_and_artist_from_the_link(self):
        page = self._link(
            "https://www.boiteachansons.net/partitions/nobody/chanson",
            "Chanson - Nobody - Paroles et accords",
        )
        [result] = self._results(page)
        assert (result.title, result.artist) == ("Chanson", "Nobody")
        assert result.source == "Boîte à Chansons"

    def test_skips_the_menu_links_that_share_the_prefix(self):
        # nouveautes and friends live under /partitions/ with one path segment.
        page = (
            self._link("https://www.boiteachansons.net/partitions/nouveautes", "Liste")
            + self._link("https://www.boiteachansons.net/partitions/top50Chansons", "Top")
            + self._link(
                "https://www.boiteachansons.net/partitions/nobody/chanson",
                "Chanson - Nobody - Paroles et accords",
            )
        )
        assert [r.title for r in self._results(page)] == ["Chanson"]

    def test_keeps_a_title_that_contains_a_dash(self):
        page = self._link(
            "https://www.boiteachansons.net/partitions/nobody/x",
            "Un - Deux - Trois - Nobody - Paroles et accords",
        )
        [result] = self._results(page)
        assert (result.title, result.artist) == ("Un - Deux - Trois", "Nobody")

    def test_the_same_song_twice_is_listed_once(self):
        link = self._link(
            "https://www.boiteachansons.net/partitions/nobody/chanson",
            "Chanson - Nobody - Paroles et accords",
        )
        assert len(self._results(link + link)) == 1


class TestSources:
    def _sources(self):
        from bibi.sources import Sources

        return Sources()

    def test_routes_a_url_to_the_site_that_owns_it(self):
        sources = self._sources()
        assert sources.name_for("https://tabs.ultimate-guitar.com/tab/x") == "Ultimate Guitar"
        assert sources.name_for("https://www.boiteachansons.net/partitions/a/b") == "Boîte à Chansons"
        assert sources.name_for("https://evil.test/x") == ""

    def test_refuses_a_url_no_source_owns(self):
        assert not self._sources().matches("https://evil.test/x")
        with pytest.raises(NotAChordPage):
            self._sources().fetch("https://evil.test/x")

    def test_interleaves_so_neither_site_buries_the_other(self):
        from bibi.song import SearchResult
        from bibi.sources import Sources

        def stub(name, count):
            class Stub:
                def search(self, query):
                    return [
                        SearchResult(title=f"{name}{i}", artist="", url=f"u{i}", source=name)
                        for i in range(count)
                    ]

            return Stub()

        merged = Sources([stub("A", 4), stub("B", 2)]).search("x")
        assert [r.source for r in merged] == ["A", "B", "A", "B", "A", "A"]

    def test_one_site_being_down_does_not_lose_the_other(self):
        from bibi.song import SearchResult
        from bibi.sources import Sources

        class Broken:
            def search(self, query):
                raise OSError("no network")

        class Fine:
            def search(self, query):
                return [SearchResult(title="ok", artist="", url="u", source="Fine")]

        assert [r.title for r in Sources([Broken(), Fine()]).search("x")] == ["ok"]


class TestEditingChords:
    """Only chord lines are editable, and blank means gone."""

    def _song(self, body):
        return Song(title="T", body=body)

    def test_moving_a_chord_is_just_moving_its_column(self):
        song = self._song("C\naaaa bbbb")
        assert song.edited({"l0": "     C"}).body == "     C\naaaa bbbb"

    def test_clearing_a_field_removes_the_chord_line(self):
        song = self._song("C   G\naaaa bbbb\nF\ncccc")
        assert song.edited({"l0": "   "}).body == "aaaa bbbb\nF\ncccc"

    def test_typing_into_an_empty_field_adds_a_chord_line(self):
        song = self._song("aaaa bbbb")
        assert song.edited({"n0": "C    G"}).body == "C    G\naaaa bbbb"

    def test_adding_and_removing_in_one_pass(self):
        song = self._song("C\naaaa\nbbbb")
        assert song.edited({"l0": "", "n2": "  G"}).body == "aaaa\n  G\nbbbb"

    def test_untouched_lines_come_back_unchanged(self):
        body = "C\naaaa bbbb\n\ncccc   dddd"
        edited = self._song(body).edited({"l0": "G"})
        assert edited.body == "G\naaaa bbbb\n\ncccc   dddd"

    def test_blank_lines_and_spacing_survive(self):
        body = "C\naaaa\n\n\nbbbb"
        assert self._song(body).edited({}).body == body

    def test_submitting_nothing_changes_nothing(self):
        body = "C   G\naaaa bbbb"
        assert self._song(body).edited({}).body == body

    def test_trailing_spaces_are_trimmed_but_leading_ones_are_not(self):
        # Leading spaces are the chord's position; trailing ones are noise.
        assert self._song("C\naaaa").edited({"l0": "   C   "}).body == "   C\naaaa"

    def test_the_edit_survives_a_round_trip_to_disk(self, tmp_path):
        library = Library(home=tmp_path)
        library.save(self._song("C\naaaa bbbb"))
        song = library.load(library.paths()[0])

        library.save(song.edited({"l0": "      C"}))

        assert library.load(library.paths()[0]).body == "      C\naaaa bbbb"


class TestTheEditScreen:
    def _page(self, body):
        return HtmlRenderer().edit(Song(title="T", body=body))

    def test_every_line_gets_a_field(self):
        page = self._page("C   G\naaaa\nF\nbbbb")
        for i in range(4):
            assert f'name="l{i}"' in page

    def test_every_lyric_without_chords_gets_an_empty_one(self):
        page = self._page("aaaa\nbbbb")
        assert 'name="n0"' in page and 'name="n1"' in page

    def test_a_lyric_that_already_has_chords_gets_no_extra_field(self):
        page = self._page("C\naaaa")
        assert 'name="n1"' not in page

    def test_fields_carry_the_line_verbatim_so_columns_hold(self):
        page = self._page("C     G\naaaa bbbb")
        assert 'value="C     G"' in page

    def test_fields_are_as_wide_as_the_longest_line(self):
        # ch units are monospace columns, so the grid lines up with the lyrics.
        page = self._page("C\naaaaaaaaaa")
        assert "width:18ch" in page

    def test_it_posts_to_edit_with_the_slug(self):
        page = self._page("C\naaaa")
        assert 'action="/edit"' in page and 'name="slug"' in page

    def test_there_is_a_way_out_without_saving(self):
        assert "Cancel" in self._page("C\naaaa")

    def test_the_transposer_is_absent_while_editing(self):
        # Editing happens in the stored key; offering to transpose here would
        # invite saving an edit against a shifted view.
        assert 'class="tr"' not in self._page("C\naaaa")


class TestFormsDoNotLayOutThePage:
    """The edit screen wraps the whole page in a <form>. A bare
    `form { display:flex }` therefore laid nav, header and sheet out in a row,
    shifting everything sideways."""

    def test_no_bare_form_layout_rule(self):
        from bibi.render import _CSS

        assert not re.search(r"(^|})\s*form\s*{[^}]*display\s*:\s*flex", _CSS)

    def test_the_edit_form_claims_no_layout_class(self):
        page = HtmlRenderer().edit(Song(title="T", body="C\naaaa"))
        assert 'action="/edit"' in page
        assert 'class="bar"' not in page

    def test_the_search_and_settings_bars_still_get_it(self, tmp_path):
        assert 'class="bar" action="/search"' in HtmlRenderer().index([])
        assert 'class="bar" method="post" action="/settings"' in (
            HtmlRenderer().settings(tmp_path)
        )


class TestUnrecognisedTokens:
    def test_something_that_is_not_a_chord_is_muted(self):
        # You can type anything into a chord field, so a typo should look
        # different from a chord once the song is locked again.
        page = HtmlRenderer().render(Song(title="T", body="C  G  Am  F  zzz\naaaa"))
        assert '<span class="nc">zzz</span>' in page

    def test_a_real_chord_is_not_muted(self):
        page = HtmlRenderer().render(Song(title="T", body="C   G\naaaa bbbb"))
        assert 'class="nc"' not in page

    def test_a_common_annotation_reads_as_not_a_chord(self):
        page = HtmlRenderer().render(Song(title="T", body="C  G  Am  F  x4\naaaa"))
        assert '<span class="nc">x4</span>' in page

    def test_too_much_nonsense_and_the_line_stops_being_chords_at_all(self):
        # The 80% threshold decides that, and it decides it per line. Two
        # chords and one typo is 67%, so the whole line reads as a lyric.
        assert not looks_like_chords("C  G  zzz")
        page = HtmlRenderer().render(Song(title="T", body="C  G  zzz\naaaa"))
        assert 'class="c"' not in page


class TestATypoCannotFreezeALine:
    """Locking lyrics down sounded safer until a mistyped chord stopped reading
    as a chord line: the line then had no field at all, so the typo could not be
    undone from inside the app."""

    def test_a_line_that_no_longer_reads_as_chords_is_still_editable(self):
        # "g" lowercase is not a chord, so this line reads as a lyric now.
        body = "g   Dmaj7\naaaa bbbb"
        assert not looks_like_chords(body.split("\n")[0])

        page = HtmlRenderer().edit(Song(title="T", body=body))
        assert 'name="l0"' in page
        assert 'value="g   Dmaj7"' in page

    def test_and_the_fix_can_be_saved(self):
        song = Song(title="T", body="g   Dmaj7\naaaa bbbb")
        fixed = song.edited({"l0": "G   Dmaj7"})
        assert looks_like_chords(fixed.body.split("\n")[0])

    def test_a_lyric_field_is_not_dressed_up_as_a_chord(self):
        page = HtmlRenderer().edit(Song(title="T", body="C\naaaa bbbb"))
        assert 'class="chl" name="l0"' in page  # chords
        assert 'class="chl lyr" name="l1"' in page  # words

    def test_editing_a_lyric_is_allowed_now(self):
        song = Song(title="T", body="C\naaaa bbbb")
        assert song.edited({"l1": "cccc dddd"}).body == "C\ncccc dddd"


class TestLockAndUnlock:
    def _server(self, tmp_path):
        from bibi.server import Server

        server = Server(library=Library(home=tmp_path))
        server.library.save(Song(title="T", key="C", body="C   G\naaaa bbbb"))
        return server

    def test_a_saved_song_offers_the_lock(self, tmp_path):
        page = self._server(tmp_path).song_page("t")
        assert "?edit=1" in page

    def test_unlocking_shows_the_editor(self, tmp_path):
        page = self._server(tmp_path).song_page("t", editing=True)
        assert 'action="/edit"' in page and 'name="l0"' in page

    def test_unlocking_ignores_the_transposition(self, tmp_path):
        # The whole trap: editing a view shifted to D must not save D chords.
        page = self._server(tmp_path).song_page("t", semitones=2, editing=True)
        assert 'value="C   G"' in page
        assert "value=\"D   A\"" not in page

    def test_locking_saves_and_reloads_changed(self, tmp_path):
        server = self._server(tmp_path)

        assert server.edit_song("t", {"l0": "      C"}) == "t"

        assert "      C" in server.library.load(server.library.paths()[0]).body
        assert 'class="c"' in server.song_page("t")

    def test_editing_a_song_that_is_gone_is_not_a_crash(self, tmp_path):
        assert self._server(tmp_path).edit_song("absent", {"l0": "C"}) is None


class TestCliWiring:
    """The command builds its own objects, so it can silently disagree with the
    server's defaults. It did: `bibi` searched only Ultimate Guitar while
    Sources knew about two sites."""

    def test_the_command_searches_every_site(self, tmp_path):
        from bibi.cli import App
        from bibi.sources import Sources

        app = App(library=Library(home=tmp_path))
        assert isinstance(app.source, Sources)
        assert {s.name for s in app.source.all} == {"Ultimate Guitar", "Boîte à Chansons"}

    def test_the_command_accepts_a_url_from_either_site(self, tmp_path):
        from bibi.cli import App

        app = App(library=Library(home=tmp_path))
        assert app.source.matches("https://tabs.ultimate-guitar.com/tab/x")
        assert app.source.matches("https://www.boiteachansons.net/partitions/a/b")

    def test_the_server_it_starts_uses_the_same_sources(self, tmp_path):
        from bibi.cli import App
        from bibi.server import Server

        app = App(library=Library(home=tmp_path))
        server = Server(app.library, app.source, app.renderer)
        assert server.source is app.source


class TestSourceLabels:
    """Which site a sheet came from, in the three places it matters."""

    def test_search_results_say_which_site(self):
        from bibi.song import SearchResult

        page = HtmlRenderer().index(
            [], "q", [SearchResult(title="T", artist="A", url="u", source="Boîte à Chansons")]
        )
        assert "Boîte à Chansons" in page

    def test_the_library_shows_provenance(self):
        page = HtmlRenderer().index([Song(title="T", site="Boîte à Chansons")])
        assert "Boîte à Chansons" in page

    def test_the_song_page_names_its_source_link(self):
        page = HtmlRenderer().render(
            Song(title="T", source="https://example.test/x", site="Boîte à Chansons")
        )
        assert ">Boîte à Chansons</a>" in page

    def test_an_older_song_without_a_site_still_links_out(self):
        page = HtmlRenderer().render(Song(title="T", source="https://example.test/x"))
        assert ">source</a>" in page

    def test_the_site_round_trips_through_the_file(self):
        song = Song(title="T", site="Boîte à Chansons", body="C\naaaa")
        assert Song.from_text(song.to_text()).site == "Boîte à Chansons"


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
