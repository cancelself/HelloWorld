"""Tests for global_symbols.py — .hw-driven loading and metadata parsing."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from global_symbols import (
    GlobalVocabulary, GlobalSymbol, GLOBAL_SYMBOLS,
    _load_from_hw, _parse_description, _fallback_symbols, reload_symbols,
)


class TestHWLoading:
    """Test that symbols are loaded from vocabularies/HelloWorld.hw."""

    def test_symbols_loaded_from_hw(self):
        """GLOBAL_SYMBOLS should contain all symbols defined in HelloWorld.hw."""
        assert len(GLOBAL_SYMBOLS) >= 30, f"Expected >=30 symbols, got {len(GLOBAL_SYMBOLS)}"

    def test_root_symbol_present(self):
        """The # symbol (bare hash) should be loaded."""
        assert "#" in GLOBAL_SYMBOLS

    def test_helloworld_symbol_present(self):
        """#HelloWorld should be loaded from the level-1 heading description."""
        assert "#HelloWorld" in GLOBAL_SYMBOLS

    def test_all_expected_symbols_present(self):
        """Spot-check that key symbols from the .hw file are present."""
        expected = [
            "#", "#HelloWorld", "#Agent", "#Object", "#parse",
            "#dispatch", "#interpret", "#Collision", "#Entropy",
            "#Sunyata", "#Love", "#Runtime", "#MCP",
        ]
        for sym in expected:
            assert sym in GLOBAL_SYMBOLS, f"Missing symbol: {sym}"


class TestDefinitions:
    """Test that definition text is correctly extracted from .hw descriptions."""

    def test_definition_text(self):
        """Definition should contain the description without metadata."""
        defn = GlobalVocabulary.definition("#parse")
        assert "Decomposing syntax into abstract structure" in defn

    def test_definition_includes_domain(self):
        """str(GlobalSymbol) includes domain in brackets."""
        defn = GlobalVocabulary.definition("#parse")
        assert "[computation]" in defn

    def test_unknown_symbol_message(self):
        """Unknown symbols return an error message."""
        defn = GlobalVocabulary.definition("#nonexistent_xyz")
        assert "Unknown symbol" in defn


class TestWikidataMetadata:
    """Test that Wikidata IDs are parsed from inline (Q-number) convention."""

    def test_wikidata_id_parsed(self):
        """Symbols with (Q-number) in their description should have wikidata_id."""
        sym = GlobalVocabulary.get("#parse")
        assert sym is not None
        assert sym.wikidata_id == "Q2290007"

    def test_wikidata_url(self):
        """wikidata_url should return a valid URL for symbols with IDs."""
        url = GlobalVocabulary.wikidata_url("#Sunyata")
        assert url == "https://www.wikidata.org/wiki/Q546054"

    def test_no_wikidata_for_meta_symbols(self):
        """Symbols without (Q-number) should have None wikidata_id."""
        sym = GlobalVocabulary.get("#Collision")
        assert sym is not None
        assert sym.wikidata_id is None

    def test_wikidata_url_none_for_missing(self):
        """wikidata_url returns None for symbols without IDs."""
        url = GlobalVocabulary.wikidata_url("#Collision")
        assert url is None


class TestParseDescription:
    """Test the _parse_description helper directly."""

    def test_full_metadata(self):
        text = "Some definition [my domain] (Q12345)"
        defn, domain, wikidata = _parse_description(text)
        assert defn == "Some definition"
        assert domain == "my domain"
        assert wikidata == "Q12345"

    def test_domain_only(self):
        text = "Some definition [my domain]"
        defn, domain, wikidata = _parse_description(text)
        assert defn == "Some definition"
        assert domain == "my domain"
        assert wikidata is None

    def test_no_metadata(self):
        text = "Just a plain definition"
        defn, domain, wikidata = _parse_description(text)
        assert defn == "Just a plain definition"
        assert domain == ""
        assert wikidata is None


class TestFallback:
    """Test fallback when .hw file is missing."""

    def test_fallback_returns_minimal_set(self):
        """Fallback should return exactly 3 bootstrap symbols."""
        fb = _fallback_symbols()
        assert len(fb) == 3
        assert "#" in fb
        assert "#HelloWorld" in fb
        assert "#Agent" in fb

    def test_load_from_missing_file_raises(self):
        """_load_from_hw should raise when file doesn't exist."""
        try:
            _load_from_hw("/nonexistent/path/to/file.hw")
            assert False, "Should have raised"
        except Exception:
            pass

    def test_reload_with_custom_hw(self):
        """reload_symbols with a custom .hw path should update GLOBAL_SYMBOLS."""
        # Write a minimal .hw file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.hw', delete=False) as f:
            f.write("# TestRoot\n")
            f.write("- Test root description [test]\n")
            f.write("## Foo\n")
            f.write("- A foo thing [testing] (Q999)\n")
            tmp_path = f.name

        try:
            reload_symbols(tmp_path)
            assert "#TestRoot" in GLOBAL_SYMBOLS
            assert "#Foo" in GLOBAL_SYMBOLS
            assert GLOBAL_SYMBOLS["#Foo"].wikidata_id == "Q999"
        finally:
            os.unlink(tmp_path)
            # Restore original symbols
            reload_symbols()


class TestGlobalVocabularyAPI:
    """Test that the GlobalVocabulary API works correctly with .hw-loaded data."""

    def test_all_symbols_returns_set(self):
        syms = GlobalVocabulary.all_symbols()
        assert isinstance(syms, set)
        assert "#parse" in syms

    def test_has_symbol(self):
        assert GlobalVocabulary.has("#Agent")
        assert not GlobalVocabulary.has("#nonexistent_xyz")

    def test_get_returns_global_symbol(self):
        sym = GlobalVocabulary.get("#Agent")
        assert isinstance(sym, GlobalSymbol)
        assert sym.name == "#Agent"
