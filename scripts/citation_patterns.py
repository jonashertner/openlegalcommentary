"""Citation pattern matching for Swiss legal commentary.

Provides regex patterns and extraction functions for all citation types
used in openlegalcommentary: BGE references, BGer unpublished decisions,
BSK/CR references, BBl (Botschaft) references, and literature citations.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum


class CitationType(Enum):
    """Types of citations found in Swiss legal commentary."""

    BGE = "bge"  # Published Federal Supreme Court decisions
    BGER = "bger"  # Unpublished Federal Supreme Court decisions
    BSK = "bsk"  # Basler Kommentar references
    CR = "cr"  # Commentaire Romand references
    BBL = "bbl"  # Botschaft / Federal Gazette references
    STGALLER = "stgaller"  # St. Galler Kommentar references
    LITERATURE = "literature"  # General literature citations
    ARTICLE_REF = "article_ref"  # Cross-references to other articles


@dataclass
class Citation:
    """A citation extracted from commentary text."""

    type: CitationType
    raw: str  # The raw matched text
    reference: str  # Normalized reference string
    line_number: int = 0
    details: dict = field(default_factory=dict)
    verified: bool | None = None  # None = not checked, True/False = result
    verification_note: str = ""


# ── BGE patterns ────────────────────────────────────────────────────

# BGE 130 III 182 E. 5.5.1
BGE_PATTERN = re.compile(
    r"\*?\*?BGE\s+(\d+)\s+([IVX]+)\s+(\d+)"
    r"(?:\s+E\.\s*([\d.]+))?\*?\*?",
)

# ── BGer unpublished patterns ───────────────────────────────────────

# Urteil 4A_123/2024 vom 15.3.2024 E. 3.2
BGER_PATTERN = re.compile(
    r"Urteil\s+(\d[A-Z]_\d+/\d{4})"
    r"(?:\s+vom\s+([\d.]+\d{4}))?"
    r"(?:\s+E\.\s*([\d.]+))?",
)

# ── BSK patterns ────────────────────────────────────────────────────

# BSK BV-Waldmann, Art. 8 N 51
# BSK OR I, Art. 41 N. 12
# Kessler, BSK OR I, Art. 41 N. 12
BSK_PATTERN = re.compile(
    r"(?:(\w[\w/\-]+),\s+)?"  # Optional author prefix
    r"BSK\s+([\w\s]+?)"  # BSK + law
    r"(?:[-–](\w[\w\-/]+))?"  # Optional -Author suffix
    r",\s*Art\.\s*(\d+[a-z]*)"  # Article number
    r"(?:\s+N\.?\s*(\d[\d\s,\-–ff.]*))?",  # Optional Randziffer
)

# ── CR patterns ─────────────────────────────────────────────────────

# Thévenoz, CR CO I, Art. 41 N. 8
CR_PATTERN = re.compile(
    r"(?:(\w[\w/\-éèêëàâùûôïîç]+),\s+)?"  # Optional author
    r"CR\s+([\w\s]+?)"  # CR + law
    r",\s*Art\.\s*(\d+[a-z]*)"  # Article
    r"(?:\s+N\.?\s*(\d[\d\s,\-–ff.]*))?",  # Optional N.
)

# ── St. Galler Kommentar patterns ───────────────────────────────────

# St. Galler Kommentar-Schweizer/Mohler, Art. 8 N 43
# Tschannen, in: St. Galler Kommentar, Vorbem. zu Art. 7-36 N 38
STGALLER_PATTERN = re.compile(
    r"(?:(\w[\w/\-]+),\s+(?:in:\s+)?)?"
    r"St\.\s*Galler\s+Kommentar"
    r"(?:[-–](\w[\w\-/]+))?"
    r"(?:,\s*(?:Vorbem\.\s+zu\s+)?Art\.\s*([\d\-a-z]+))?"
    r"(?:\s+N\.?\s*(\d[\d\s,\-–ff.]*))?",
)

# ── BBl patterns ────────────────────────────────────────────────────

# BBl 1997 I 1, BBl 2001 4202, BBl 1997 I 141 f.
BBL_PATTERN = re.compile(
    r"BBl\s+(\d{4})\s+([IVX]+\s+)?(\d+)"
    r"(?:\s+f{1,2}\.)?",
)

# ── Literature patterns ─────────────────────────────────────────────

# Gauch/Schluep/Schmid, OR AT, 11. Aufl. 2020, N 2850
# Häfelin/Haller/Keller/Thurnherr, Bundesstaatsrecht, N 324
# Müller/Schefer, Grundrechte, N 754
LITERATURE_PATTERN = re.compile(
    r"((?:[A-ZÄÖÜ]\w+(?:/[A-ZÄÖÜ]\w+)*)"  # Author(s)
    r",\s+"
    r"([\w\s\-äöüéèêëàâùûôïîç.]+?)"  # Title
    r"(?:,\s+(\d+)\.\s*Aufl\.\s*(\d{4}))?"  # Edition + year
    r"(?:,\s*N\.?\s*(\d[\d\s,\-–ff.]*))?)"  # Randziffer
    r"(?=[\s;,.\)])",
)

# ── Article cross-reference patterns ────────────────────────────────

# → Art. 9 BV, ↔ Art. 41 OR, Art. 36 BV
ARTICLE_REF_PATTERN = re.compile(
    r"(?:[→↔]\s+)?Art\.\s*(\d+[a-z]*)\s+([A-ZÄÖÜ]{2,})",
)


def extract_citations(text: str) -> list[Citation]:
    """Extract all citations from a commentary text.

    Returns a list of Citation objects with type, raw text,
    and normalized reference.
    """
    citations = []
    lines = text.split("\n")

    for line_num, line in enumerate(lines, 1):
        # BGE
        for m in BGE_PATTERN.finditer(line):
            ref = f"BGE {m.group(1)} {m.group(2)} {m.group(3)}"
            if m.group(4):
                ref += f" E. {m.group(4)}"
            citations.append(Citation(
                type=CitationType.BGE,
                raw=m.group(0),
                reference=ref,
                line_number=line_num,
                details={
                    "volume": int(m.group(1)),
                    "part": m.group(2),
                    "page": int(m.group(3)),
                    "erwaegung": m.group(4),
                },
            ))

        # BGer unpublished
        for m in BGER_PATTERN.finditer(line):
            ref = f"Urteil {m.group(1)}"
            citations.append(Citation(
                type=CitationType.BGER,
                raw=m.group(0),
                reference=ref,
                line_number=line_num,
                details={
                    "docket": m.group(1),
                    "date": m.group(2),
                    "erwaegung": m.group(3),
                },
            ))

        # BSK
        for m in BSK_PATTERN.finditer(line):
            author = m.group(1) or m.group(3) or ""
            law = m.group(2).strip()
            article = m.group(4)
            rz = m.group(5)
            ref = f"BSK {law}, Art. {article}"
            if author:
                ref = f"{author}, {ref}"
            if rz:
                ref += f" N. {rz.strip()}"
            citations.append(Citation(
                type=CitationType.BSK,
                raw=m.group(0),
                reference=ref,
                line_number=line_num,
                details={
                    "author": author,
                    "law": law,
                    "article": article,
                    "randziffer": rz.strip() if rz else None,
                },
            ))

        # CR
        for m in CR_PATTERN.finditer(line):
            author = m.group(1) or ""
            law = m.group(2).strip()
            article = m.group(3)
            rz = m.group(4)
            ref = f"CR {law}, Art. {article}"
            if author:
                ref = f"{author}, {ref}"
            if rz:
                ref += f" N. {rz.strip()}"
            citations.append(Citation(
                type=CitationType.CR,
                raw=m.group(0),
                reference=ref,
                line_number=line_num,
                details={
                    "author": author,
                    "law": law,
                    "article": article,
                    "randziffer": rz.strip() if rz else None,
                },
            ))

        # St. Galler Kommentar
        for m in STGALLER_PATTERN.finditer(line):
            author = m.group(1) or m.group(2) or ""
            article = m.group(3)
            rz = m.group(4)
            ref = "St. Galler Kommentar"
            if author:
                ref = f"{author}, {ref}"
            if article:
                ref += f", Art. {article}"
            if rz:
                ref += f" N. {rz.strip()}"
            citations.append(Citation(
                type=CitationType.STGALLER,
                raw=m.group(0),
                reference=ref,
                line_number=line_num,
                details={
                    "author": author,
                    "article": article,
                    "randziffer": rz.strip() if rz else None,
                },
            ))

        # BBl
        for m in BBL_PATTERN.finditer(line):
            vol = m.group(2).strip() if m.group(2) else ""
            ref = f"BBl {m.group(1)}"
            if vol:
                ref += f" {vol}"
            ref += f" {m.group(3)}"
            citations.append(Citation(
                type=CitationType.BBL,
                raw=m.group(0),
                reference=ref,
                line_number=line_num,
                details={
                    "year": int(m.group(1)),
                    "volume": vol,
                    "page": int(m.group(3)),
                },
            ))

    return citations


def extract_bge_references(text: str) -> list[str]:
    """Extract just BGE reference strings from text."""
    return [
        f"BGE {m.group(1)} {m.group(2)} {m.group(3)}"
        for m in BGE_PATTERN.finditer(text)
    ]


def extract_bbl_references(text: str) -> list[str]:
    """Extract just BBl reference strings from text."""
    refs = []
    for m in BBL_PATTERN.finditer(text):
        vol = m.group(2).strip() if m.group(2) else ""
        ref = f"BBl {m.group(1)}"
        if vol:
            ref += f" {vol}"
        ref += f" {m.group(3)}"
        refs.append(ref)
    return refs


def has_fabricated_randziffer(citation: Citation) -> bool:
    """Heuristic: detect likely fabricated Randziffer numbers.

    A Randziffer is likely fabricated if it's in a general literature
    citation (not BSK/CR which have verified ref data) and contains
    a specific N. number. These were commonly hallucinated by the
    generation pipeline.
    """
    if citation.type != CitationType.LITERATURE:
        return False
    rz = citation.details.get("randziffer")
    return rz is not None and rz.strip() != ""
