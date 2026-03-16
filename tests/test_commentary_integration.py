"""Integration tests: commentary refs flow through the pipeline."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from agents.config import AgentConfig
from agents.evaluator import evaluate_layer
from agents.law_agent import generate_layer


@pytest.fixture
def config_with_refs(tmp_path):
    """Config with content, guidelines, and commentary refs."""
    # Content
    content_root = tmp_path / "content"
    art_dir = content_root / "or" / "art-041"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: OR\narticle: 41\ntitle: Haftung\n"
        "sr_number: '220'\nabsatz_count: 2\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    (art_dir / "doctrine.md").write_text("# Doktrin\n\nPlaceholder.")

    # Guidelines
    guidelines = tmp_path / "guidelines"
    guidelines.mkdir()
    (guidelines / "global.md").write_text("# Global\n\nTest guidelines.")
    (guidelines / "or.md").write_text("# OR\n\nTest OR guidelines.")
    (guidelines / "evaluate.md").write_text("# Evaluation\n\nTest rubric.")

    # Commentary refs
    refs_dir = tmp_path / "commentary_refs"
    refs_dir.mkdir()
    refs_data = {
        "OR": {
            "41": {
                "authors": ["Kessler", "Widmer Lüchinger"],
                "edition": "BSK OR I, 7. Aufl. 2019",
                "randziffern_map": {"1-3": "Entstehungsgeschichte"},
                "positions": [
                    {
                        "author": "Kessler", "n": "N. 12",
                        "topic": "Widerrechtlichkeit",
                        "position": (
                            "Erfolgsunrecht genügt bei "
                            "absoluten Rechtsgütern"
                        ),
                    },
                ],
                "controversies": [
                    {
                        "topic": "Organhaftung",
                        "positions": {
                            "Kessler (N. 30)": "Art. 55 ist lex specialis",
                            "Huguenin": "Parallelanwendung möglich",
                        },
                    },
                ],
                "cross_refs": ["Art. 97 OR"],
                "key_literature": ["Gauch/Schluep/Schmid, OR AT"],
            },
        },
    }
    (refs_dir / "or_bsk.json").write_text(json.dumps(refs_data))

    return AgentConfig(
        content_root=content_root,
        guidelines_root=guidelines,
        commentary_refs_root=refs_dir,
    )


def test_generate_doctrine_includes_commentary_refs(config_with_refs):
    """Commentary refs appear in the prompt for doctrine layers."""
    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(generate_layer(
            config_with_refs, "OR", 41, "", "doctrine",
        ))
        prompt = mock_run.call_args.kwargs["prompt"]
        assert "Kessler" in prompt
        assert "BSK OR I" in prompt
        assert "N. 12" in prompt
        assert "Organhaftung" in prompt


def test_generate_caselaw_excludes_commentary_refs(config_with_refs):
    """Commentary refs are NOT injected for caselaw layers."""
    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(generate_layer(
            config_with_refs, "OR", 41, "", "caselaw",
        ))
        prompt = mock_run.call_args.kwargs["prompt"]
        assert "BSK OR I" not in prompt


def test_evaluator_includes_commentary_refs(config_with_refs):
    """Commentary refs are injected into evaluator prompt."""
    verdict = json.dumps({
        "verdict": "publish",
        "non_negotiables": {"keine_unbelegten_rechtsaussagen": True},
        "scores": {"praezision": 0.96},
        "feedback": {"blocking_issues": []},
    })
    mock_run = AsyncMock(return_value=(verdict, 0.05))
    with patch("agents.evaluator.run_agent", mock_run):
        asyncio.run(evaluate_layer(
            config_with_refs, "OR", 41, "", "doctrine",
        ))
        prompt = mock_run.call_args.kwargs["prompt"]
        assert "Kessler" in prompt
        assert "BSK OR I" in prompt


def test_generate_doctrine_no_refs_for_uncovered_law(config_with_refs):
    """No crash when law has no commentary refs."""
    # Create ZGB content dir (no BSK refs for ZGB)
    art_dir = config_with_refs.content_root / "zgb" / "art-001"
    art_dir.mkdir(parents=True)
    (art_dir / "meta.yaml").write_text(
        "law: ZGB\narticle: 1\ntitle: Test\n"
        "sr_number: '210'\nabsatz_count: 1\n"
        "fedlex_url: https://example.com\nlayers: {}\n"
    )
    guidelines = config_with_refs.guidelines_root
    (guidelines / "zgb.md").write_text("# ZGB\n\nTest.")

    mock_run = AsyncMock(return_value=("Generated content.", 0.05))
    with patch("agents.law_agent.run_agent", mock_run):
        asyncio.run(generate_layer(
            config_with_refs, "ZGB", 1, "", "doctrine",
        ))
        prompt = mock_run.call_args.kwargs["prompt"]
        assert "BSK" not in prompt  # no BSK data for ZGB
