"""Tests for structured commentary digestion."""
from __future__ import annotations

import json

import pytest

from scripts.commentary_schema import ArticleRef, Position
from scripts.digest_commentary import (
    DigestState,
    build_digestion_prompt,
    chunk_long_article,
    estimate_tokens,
    merge_chunk_results,
    parse_digest_response,
)


def test_build_digestion_prompt():
    prompt = build_digestion_prompt(
        "Art. 41\n\nKessler\n\nSome commentary text...", "OR", "de",
    )
    assert "Art. 41" in prompt
    assert "authors" in prompt.lower()
    assert "randziffern" in prompt.lower()


def test_build_digestion_prompt_french():
    prompt = build_digestion_prompt(
        "Art. 41\n\nThévenoz\n\nTexte...", "OR", "fr",
    )
    assert "German" in prompt  # output should be in German


def test_parse_digest_response_valid():
    response = json.dumps({
        "authors": ["Kessler"],
        "edition": "Doctrinal OR I, 7. Aufl. 2019",
        "randziffern_map": {"1-3": "Entstehungsgeschichte"},
        "positions": [
            {"author": "Kessler", "n": "N. 12", "topic": "Test", "position": "Pos"},
        ],
        "controversies": [],
        "cross_refs": [],
        "key_literature": [],
    })
    result = parse_digest_response(response)
    assert isinstance(result, ArticleRef)
    assert result.authors == ["Kessler"]


def test_parse_digest_response_with_markdown():
    inner = json.dumps({
        "authors": ["Kessler"], "edition": "Doctrinal OR I", "positions": [],
    })
    response = f"Here is the result:\n```json\n{inner}\n```"
    result = parse_digest_response(response)
    assert result.authors == ["Kessler"]


def test_parse_digest_response_invalid():
    with pytest.raises(ValueError):
        parse_digest_response("not json at all")


def test_parse_digest_response_missing_required():
    response = json.dumps({"edition": "Doctrinal OR I"})  # missing authors
    with pytest.raises(ValueError):
        parse_digest_response(response)


def test_estimate_tokens():
    # ~4 chars per token
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("a" * 400) == 100


def test_chunk_short_article():
    text = "N. 1 Short article text N. 2 more text"
    chunks = chunk_long_article(text, max_tokens=10000)
    assert len(chunks) == 1
    assert chunks[0][1] is None  # No primary range needed


def test_chunk_long_article():
    # Build a text that exceeds max_tokens with Randziffern markers
    parts = []
    for i in range(1, 51):
        parts.append(f"N. {i} " + "x" * 2000)
    text = "\n".join(parts)
    chunks = chunk_long_article(text, max_tokens=5000)
    assert len(chunks) > 1
    # Each chunk should have a primary range
    for _, primary_range in chunks:
        assert primary_range is not None
        assert primary_range[0] <= primary_range[1]


def test_merge_chunk_results_deduplicates():
    ref1 = ArticleRef(
        authors=["Kessler"], edition="Doctrinal OR I",
        positions=[
            Position(author="Kessler", n="N. 5", topic="T", position="P1"),
        ],
        cross_refs=["Art. 97 OR"],
        key_literature=["Gauch"],
    )
    ref2 = ArticleRef(
        authors=["Kessler"], edition="Doctrinal OR I",
        positions=[
            Position(author="Kessler", n="N. 15", topic="T2", position="P2"),
        ],
        cross_refs=["Art. 97 OR", "Art. 55 OR"],  # Art. 97 is duplicate
        key_literature=["Gauch", "Schwenzer"],  # Gauch is duplicate
    )
    result = merge_chunk_results([(ref1, (1, 10)), (ref2, (11, 20))])
    assert len(result.cross_refs) == 2  # Art. 97, Art. 55
    assert len(result.key_literature) == 2  # Gauch, Schwenzer
    assert len(result.positions) == 2  # N. 5 from chunk1, N. 15 from chunk2


class TestDigestState:
    def test_load_new(self, tmp_path):
        state = DigestState.load(tmp_path / "state.json")
        assert state.completed_keys == set()

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "state.json"
        state = DigestState.load(path)
        state.mark_completed("41")
        state.mark_completed("42")
        state.save()
        loaded = DigestState.load(path)
        assert loaded.completed_keys == {"41", "42"}

    def test_is_completed(self, tmp_path):
        state = DigestState.load(tmp_path / "state.json")
        assert not state.is_completed("41")
        state.mark_completed("41")
        assert state.is_completed("41")
