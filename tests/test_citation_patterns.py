"""Tests for regex-based citation extraction."""
from scripts.citation_patterns import (
    CitationType,
    extract_bbl_references,
    extract_bge_references,
    extract_citations,
)


def test_extract_bge_with_erwaegung():
    text = "Siehe BGE 130 III 182 E. 5.5.1 zum Thema."
    citations = extract_citations(text)
    bges = [c for c in citations if c.type == CitationType.BGE]
    assert len(bges) == 1
    assert bges[0].details["volume"] == 130
    assert bges[0].details["part"] == "III"
    assert bges[0].details["page"] == 182
    assert bges[0].details["erwaegung"] == "5.5.1"


def test_extract_bge_without_erwaegung():
    text = "Vgl. BGE 145 IV 250 sowie weitere."
    citations = extract_citations(text)
    bges = [c for c in citations if c.type == CitationType.BGE]
    assert len(bges) == 1
    assert bges[0].details["volume"] == 145
    assert bges[0].details["erwaegung"] is None


def test_extract_bge_bold_formatting():
    text = "Im Leitentscheid **BGE 130 III 182** hielt das Gericht fest."
    citations = extract_citations(text)
    bges = [c for c in citations if c.type == CitationType.BGE]
    assert len(bges) == 1
    assert bges[0].details["volume"] == 130


def test_extract_bger_unpublished():
    text = "Urteil 4A_123/2024 vom 15.3.2024 E. 3.2 ist einschlägig."
    citations = extract_citations(text)
    bgers = [c for c in citations if c.type == CitationType.BGER]
    assert len(bgers) == 1
    assert bgers[0].details["docket"] == "4A_123/2024"
    assert bgers[0].details["date"] == "15.3.2024"
    assert bgers[0].details["erwaegung"] == "3.2"


def test_extract_bsk_with_author():
    text = "Kessler, BSK OR I, Art. 41 N. 12 verweist darauf."
    citations = extract_citations(text)
    bsks = [c for c in citations if c.type == CitationType.BSK]
    assert len(bsks) >= 1
    # Either group 1 (prefix) or group 3 (suffix) author should be captured
    authors = {c.details["author"] for c in bsks}
    assert any("Kessler" in a for a in authors)
    assert any(c.details["article"] == "41" for c in bsks)


def test_extract_bsk_suffix_author():
    text = "Der BSK BV-Waldmann, Art. 8 N 51 folgt dieser Linie."
    citations = extract_citations(text)
    bsks = [c for c in citations if c.type == CitationType.BSK]
    assert len(bsks) >= 1
    assert any(c.details["article"] == "8" for c in bsks)


def test_extract_cr_with_author():
    text = "Thévenoz, CR CO I, Art. 41 N. 8 zum Deliktrecht."
    citations = extract_citations(text)
    crs = [c for c in citations if c.type == CitationType.CR]
    assert len(crs) >= 1
    assert any(c.details["article"] == "41" for c in crs)


def test_extract_bbl_simple():
    text = "Vgl. BBl 2001 4202 zur Begründung."
    citations = extract_citations(text)
    bbls = [c for c in citations if c.type == CitationType.BBL]
    assert len(bbls) == 1
    assert bbls[0].details["year"] == 2001
    assert bbls[0].details["page"] == 4202


def test_extract_bbl_with_roman_volume():
    text = "BBl 1997 I 1 ist die relevante Stelle."
    citations = extract_citations(text)
    bbls = [c for c in citations if c.type == CitationType.BBL]
    assert len(bbls) == 1
    assert bbls[0].details["year"] == 1997
    assert bbls[0].details["volume"] == "I"
    assert bbls[0].details["page"] == 1


def test_extract_multiple_citation_types_same_line():
    text = "BGE 130 III 182 und Kessler, BSK OR I, Art. 41 N. 12 stimmen überein."
    citations = extract_citations(text)
    assert any(c.type == CitationType.BGE for c in citations)
    assert any(c.type == CitationType.BSK for c in citations)


def test_extract_bge_references_helper():
    text = "BGE 130 III 182 und BGE 145 IV 250 sind einschlägig."
    refs = extract_bge_references(text)
    assert "BGE 130 III 182" in refs
    assert "BGE 145 IV 250" in refs
    assert len(refs) == 2


def test_extract_bbl_references_helper():
    text = "Siehe BBl 1997 I 141 und BBl 2001 4202."
    refs = extract_bbl_references(text)
    assert len(refs) == 2
    assert any("1997" in r for r in refs)
    assert any("2001" in r for r in refs)


def test_empty_text_returns_no_citations():
    assert extract_citations("") == []


def test_plain_text_returns_no_citations():
    assert extract_citations("Dies ist ein normaler Satz ohne Zitate.") == []


def test_line_numbers_are_tracked():
    text = "Erste Zeile ohne Zitat.\nZweite Zeile mit BGE 130 III 182."
    citations = extract_citations(text)
    bges = [c for c in citations if c.type == CitationType.BGE]
    assert len(bges) == 1
    assert bges[0].line_number == 2
