# World-Class Improvements Backlog

A structured running list of improvements that would take openlegalcommentary
from "early beta" toward a singular, world-class legal commentary platform.
Compiled during Phase 2 batch wait (2026-04-11) from observations made across
Phases 0–2 and from gaps surfaced by user feedback.

Each item: **rationale**, **scope**, **rough effort**, **priority tag**.

Priority tags:
- **P0** — fixes a known production issue, blocks something important
- **P1** — meaningfully improves the project's core value proposition
- **P2** — quality-of-life, polish, future-proofing
- **P3** — speculative or distant

---

## A. Pipeline reliability & safety

### A1. Investigate Sonnet write-skip root cause [P0]

**Observed:** Sonnet 4.6 occasionally completes its agent loop without calling
`write_layer_content`. Hit on BGFA Art. 12 (1× in Phase 0), BV Art. 75b (3×
consecutively in Phase 2 — triggered the rollback safeguard). Rate appears
to be ~5–10% on the small sample so far.

**Hypotheses to investigate:**
1. Articles with terse statute text (Art. 75b is short) may lead the agent to
   produce a final "the existing content is fine" text response without a
   tool call.
2. The current law-agent prompt's tool list says `write_layer_content` is
   one option among many, not a mandatory final step. May not be assertive
   enough.
3. The `read_layer_content` tool, when called on a non-trivial existing
   doctrine, may bias the agent into a "verify and approve" mode rather
   than a "regenerate" mode.

**Actions:**
- Read the actual conversation transcript for a write-skipping run, find
  the agent's final text turn, and identify the reasoning failure.
- Tighten `LAYER_INSTRUCTIONS["doctrine"]` in `agents/prompts.py` with
  explicit "you MUST end your run with a write_layer_content call" language.
- Consider removing `read_layer_content` from the law-agent tool list if it
  turns out to be the trigger — the agent doesn't need to read existing
  content to regenerate.

**Effort:** ~1 day (investigation + prompt tweak + test run on 5 historically
write-skipping articles).

### A2. Investigate Art. 78 translation skip mystery [P0]

**Observed:** During Phase 1b, BV Art. 78's law-agent and evaluator phases
ran successfully but the translator pass and `_update_meta_layer` did not
fire. Doctrine.md was modified, no FR/IT/EN translations, no meta version
bump. Cause unknown.

**Actions:**
- Re-run BV Art. 78 with full debug logging (no grep filter)
- Check for an exception in `process_article` between `evaluate_layer` and
  the translator loop
- Verify `eval_result.passed` was True when Art. 78 returned
- Check Python warnings (the run might have hit a soft error caught
  silently)

**Effort:** ~2 hours.

### A3. Convert pipeline cost reporting to include all phases [P1]

**Observed:** `LayerResult.cost_usd` only includes the law-agent cost. The
evaluator and translators are separate `run_agent` calls whose costs are
not tracked back to the article. Real per-article cost is ~3x what the
pipeline reports.

**Actions:**
- Track evaluator cost on `EvalResult`
- Track per-translator cost in the `process_article` translation loop
- Aggregate into a richer per-article cost record
- Bonus: per-token breakdown for cost analysis

**Effort:** ~4 hours.

### A4. Pipeline batch dashboard / progress reporting [P1]

**Observed:** During Phase 2 batch runs, monitoring required tailing log
files manually. There's no structured progress (X of Y articles complete,
estimated time remaining, running cost, success rate).

**Actions:**
- Add a `bootstrap_state.json`-style progress file the batch updates after
  each article
- Add a `pipeline status` subcommand that reads the file and renders a
  live progress table
- Optional: a simple terminal UI (`rich` or similar) showing parallel
  batch progress

**Effort:** 1–2 days.

### A5. Pipeline rate-limit awareness [P2]

**Observed:** Two parallel Phase 2 batches share rate limits. Each can
hit Anthropic 429s independently. Currently no handling — anthropic SDK
retries silently.

**Actions:**
- Surface rate-limit hits as warnings in the agent logs
- Optionally back off explicitly before continuing
- Record rate-limit events for batch postmortem

**Effort:** ~3 hours.

### A6. Recover from total bash-batch interruption [P2]

**Observed:** If a long batch run is killed mid-way, there's no resumption
mechanism. The articles already completed have committed state in their
files, but no list of "still to do" survives.

**Actions:**
- Have batch scripts maintain a state file: queued / in-progress / done /
  failed per article
- Add a `pipeline batch resume <state-file>` command
- Or: use the existing `bootstrap_state.json` machinery for ad-hoc
  batches too

**Effort:** ~1 day.

---

## B. Content quality & verification

### B1. Wire up literature-citation extraction in the audit [P1]

**Observed:** `scripts/citation_patterns.py` defines `LITERATURE_PATTERN`
and `has_fabricated_randziffer`, but `extract_citations()` doesn't use
them. The audit can't currently flag fabricated literature N. numbers
(e.g., "Häfelin/Haller, Bundesstaatsrecht, N 1234" — is N 1234 real?).

**Actions:**
- Add LITERATURE extraction to `extract_citations`
- Build/curate a known-author whitelist with valid Randziffer ranges
- Flag literature citations with N numbers outside known ranges
- Avoid double-extraction with BSK_PATTERN (which also matches
  literature-shaped strings)

**Effort:** ~1 week (the whitelist curation is the slow part).

### B2. Verify BGE references against opencaselaw [P0]

**Observed:** The audit currently *trusts* every BGE citation as
"verifiable via opencaselaw" without actually verifying. A fabricated
"BGE 999 III 999" would pass.

**Actions:**
- Batch-query opencaselaw with all extracted BGE refs
- Record per-article verified-vs-not state
- Flag fabricated BGE refs in the audit
- Cache results to avoid repeated network calls

**Effort:** ~2 days.

### B3. Verify BBl page references against preparatory-materials data [P1]

**Observed:** The audit checks BBl pages against `bgfa.json`-style prep
data. Only BGFA has prep data, and the file is empty. So 100% of BBl
citations on every other law are unchecked.

**Actions:**
- Fix the preparatory-materials pipeline (see C-section)
- Once prep data exists for BV / OR / ZGB, the existing audit code
  starts working without modification
- Unlocks ~600+ verifications on BV alone

**Effort:** depends on C-section.

### B4. Cross-reference graph extraction & visualization [P2]

**Observed:** Doctrine layers use → and ↔ arrow notation for
cross-references. The site doesn't currently extract these into a
navigation graph or visualize them. The audit doesn't track them either.

**Actions:**
- Extract cross-references with `ARTICLE_REF_PATTERN` (already defined,
  not used)
- Build a per-law adjacency map
- Site: hover-card for cross-references showing the target's title and
  first paragraph
- Site: per-article "incoming references" list ("This article is
  referenced by …")
- Optional visualization: a small interactive graph for cross-cutting
  topics

**Effort:** ~1 week.

### B5. Per-article citation badge in the site UI [P2]

**Observed:** The audit produces per-article verification rates and
flagged-citation counts. The site doesn't show any of this to readers.

**Actions:**
- After each pipeline run, write `.citations.json` per article (already
  happens) and copy the summary into `meta.yaml` (verified, flagged,
  unchecked counts)
- Site renders a small badge: "Verified citations: 92.9%" with a
  tooltip explaining the audit
- Per-citation, link the BGE ref to opencaselaw and the BSK ref to a
  description of what BSK is

**Effort:** ~3 days.

---

## C. Reference-data ecosystem

### C1. Re-run `fetch_article_texts_i18n.py` for suffix articles [P0]

**Observed:** All 35 BV suffix articles are missing or empty in the
statute-text JSON files. Same systematic bug across DE/FR/IT/EN. Other
laws likely affected the same way. The Art. 5a fix in `946a2399` is a
manual hardcoded one-off — not scalable.

**Actions:**
- Investigate why MCP `get_law(law, "5a")` returns empty/parse-failing
  output
- Either fix the parser in `_parse_article_text` or add a fallback
- Re-run for all 4 languages and 9 laws
- Verify against the site

**Effort:** ~1 day.

### C2. Generate preparatory-materials data for BV [P0]

**Observed:** `scripts/preparatory_materials/bgfa.json` is the only
non-empty file in that directory and it's literally empty (`articles: {}`).
The pipeline ran on 2026-04-06 and produced nothing for BGFA. BV has 0
prep data, which means 600+ BBl citations on BV are forever unchecked.

**Actions:**
- Diagnose why BGFA produced empty output (see Phase 3 in the roadmap)
- Fix and re-run for BGFA, then BV, then the other 7 laws
- Document the pipeline so it can be re-run as Botschaften are amended

**Effort:** ~3 days.

### C3. Build BSK / CR commentary reference data for the other 8 laws [P1]

**Observed:** Only `scripts/commentary_refs/bv_refs.json` exists. The
audit can only verify BSK citations on BV. For OR, ZGB, and the other 7
laws, all BSK citations are unchecked.

**Actions:**
- Use `digest_commentary.py` to build reference data for OR (largest law,
  most BSK content)
- Then ZGB, then ZPO, then the rest
- This requires access to the BSK PDFs (the user noted these are coming
  in the BSK/CR Commentary Integration project memory)

**Effort:** ~1 week per law (with BSK PDFs available).

### C4. Build CR (Commentaire Romand) reference data [P1]

**Observed:** No CR reference data anywhere. The audit's `_verify_cr_citation`
returns "No CR ref data available" for every CR citation.

**Actions:**
- Same approach as C3 but for CR commentaries
- Important for legal coverage of French-Swiss perspectives
- Not a substitute for translations — CR is its own commentary tradition

**Effort:** ~1 week per law.

### C5. Article texts (Gesetzestext) live-fetch from Fedlex [P2]

**Observed:** The statute texts are static JSON files. When Swiss law is
amended, the JSON files lag until manually re-run. Suffix articles still
broken even after the Art. 5a fix.

**Actions:**
- Add a daily/weekly cron that fetches all article texts from Fedlex
  via the MCP
- Detect amendments and emit a "law amended" signal that triggers a
  cascade regeneration
- Cache the fetches so the site doesn't hit Fedlex on every build

**Effort:** ~2 days.

---

## D. Authoring guidelines & prompt engineering

### D1. Tighten doctrine prompt's tool-call discipline [P0]

**Observed:** Sonnet's write-skip failure mode (A1) likely stems from
under-specified tool-call requirements in the doctrine prompt.

**Actions:**
- See A1.

### D2. Standardize Randziffer citation format [P1]

**Observed:** Across guidelines, prompts, and content, citation formats
are inconsistent: `N. 5`, `N 5`, `Rn. 5`, `N° 5` (in FR). The audit
patterns are loose enough to handle most variations, but the lack of a
canonical form is a quality smell.

**Actions:**
- Pick a canonical format per language (`N. 5` for DE, `n° 5` for FR,
  `n. 5` for IT, `N. 5` for EN — matching scholarly Swiss conventions)
- Update guidelines, prompts, and existing content
- Add a validator that catches non-canonical forms

**Effort:** ~1 day.

### D3. Per-law doctrine guidelines need depth [P2]

**Observed:** `guidelines/{law}.md` files exist but are mostly thin
(150–300 lines). They cover characteristic citation styles, key
authorities, and common pitfalls — but they could be much richer about
*how to think* in each law's domain.

**Actions:**
- Per-law style guide expansion
- Worked examples per major article type (right vs. organizational
  norm vs. competence rule)
- "Failure modes" section per law — known LLM hallucination patterns
  in that law's domain

**Effort:** ~3 days per law.

### D4. Citation format negotiation: BSK vs. textbook [P1]

**Observed:** Sonnet tends to cite textbook authors in literature format
(Häfelin/Haller etc.) rather than constructing BSK-style references. The
Phase 1b results showed this *eliminates* fabricated BSK author/Rn
combinations — a quality win. The current prompt asks for both styles
without a clear preference.

**Actions:**
- Make literature-format the preferred default in `LAYER_INSTRUCTIONS`
- Reserve BSK format for cases where the BSK reference data has been
  loaded for that article
- This codifies what Sonnet is already doing well

**Effort:** ~2 hours.

### D5. Evaluator: add a "regression check" criterion [P2]

**Observed:** The Opus evaluator scores 5 dimensions but doesn't
explicitly compare against the existing baseline. A regenerated article
that's slightly worse than the existing one can still pass.

**Actions:**
- Add an "improvement vs. baseline" criterion to the evaluator (load
  the previous version, compare on key dimensions: citation count,
  Randziffer count, structure completeness)
- Reject regenerations that are *worse* than the baseline on any
  measurable dimension
- This is a stronger guarantee than just rollback-on-failure

**Effort:** ~1 day.

---

## E. Site UX & reader experience

### E1. Cross-reference click-through navigation [P1]

**Observed:** Arrows like `→ Art. 8 BV` are rendered as plain text. They
should be links to the target article (or hover cards previewing the
target).

**Actions:**
- Markdown post-processor that converts arrow notation to links
- Optional hover card showing target article title + first paragraph
- Already partially supported via `getCrossReferences` — just needs
  inline rendering in the doctrine prose

**Effort:** ~3 days.

### E2. BGE reference auto-linking to opencaselaw [P1]

**Observed:** **BGE 130 III 182 E. 5.5.1** is rendered as bold text. It
should be a link to the actual decision on opencaselaw.ch (or another
canonical Swiss case-law source).

**Actions:**
- Markdown post-processor that turns BGE refs into links
- URL pattern: opencaselaw.ch URL or bger.ch search URL
- Same for BGer unpublished decisions (Urteil X_123/2024)

**Effort:** ~1 day.

### E3. Per-article verification & quality badges [P2]

**Observed:** Readers have no signal about how trustworthy any individual
article is.

**Actions:**
- See B5
- Surface evaluator quality scores too (precision, concision,
  accessibility, relevance, academic rigor)
- "Last regenerated" timestamp visible

**Effort:** ~3 days (depends on B5).

### E4. Article changelog / diff view [P2]

**Observed:** Articles get regenerated periodically. There's no visible
history of what changed, when, or why. The git history exists but isn't
exposed to readers.

**Actions:**
- Per-article "Versions" tab showing regeneration timeline
- Diff view between consecutive versions (using the `version` field in
  meta.yaml)
- Optional: "Why was this regenerated?" annotation pulled from commit
  messages

**Effort:** ~1 week.

### E5. Reader feedback / correction submission [P1]

**Observed:** No way for a reader to flag an error or submit a
correction. World-class legal scholarship has tight feedback loops with
practitioners.

**Actions:**
- "Report an issue" link per article (jumps to a pre-filled GitHub issue
  with the article context)
- Optional: a structured feedback form (flag a specific paragraph,
  classify the issue, add a note)
- Pipeline integration: feedback gets fed into the next regeneration
  attempt as `feedback` parameter

**Effort:** ~1 week.

### E6. Citation export (BibTeX, Zotero) [P2]

**Observed:** Academic users want to cite this commentary in their own
work. Currently they have to construct citations by hand.

**Actions:**
- Per-article "Cite this" button → BibTeX, Zotero, RIS formats
- Generated from meta.yaml (author=AI, title, last_updated, URL)
- Make it explicit that the AI is the author so academic norms are
  respected

**Effort:** ~2 days.

### E7. Mobile polish [P1]

**Observed:** The recent Swiss redesign already handles mobile through
the responsive nav. But several touchpoints could be smoother on small
screens.

**Actions:**
- Article tabs (Übersicht / Doktrin / Rechtsprechung) — vertical
  swipe? horizontal scroll?
- TOC sidebar collapses well but could be more discoverable
- Long article reading on narrow screens: line length, font size

**Effort:** ~1 week.

### E8. Reading experience: article structure navigation [P2]

**Observed:** Long doctrine layers (BV Art. 9 has 27 Randziffern, Art. 116
has 30+) are hard to navigate.

**Actions:**
- Sticky TOC for the current section
- Jump-to-Randziffer (input box: "go to N. 15")
- "On this page" sidebar with section headings
- Scroll progress indicator

**Effort:** ~3 days.

---

## F. Quality measurement & methodology

### F1. Human reviewer integration [P1]

**Observed:** No human reviewer touches the content currently. The
salvage-branch editorial workflow was rejected as speculative, but a
*minimum* form (random spot-check sampling) would significantly improve
quality.

**Actions:**
- Per regeneration cycle, randomly sample 5% of articles for human
  review
- Lightweight review form: "this article reads correctly / has issues"
- Issues feed back into prompt refinement
- Reviewer pool: starts as user (sole reviewer), grows over time

**Effort:** ~1 week (workflow design + implementation).

### F2. Adversarial test set for the evaluator [P2]

**Observed:** The evaluator's quality scores are calibrated against the
generated content but not against an adversarial test set with known
issues.

**Actions:**
- Curate ~20 articles with planted errors (fabricated BGE, wrong
  Erwägung, missing required section, etc.)
- Run the evaluator on them
- Verify it catches the planted errors
- This becomes a regression test for the evaluator prompt

**Effort:** ~3 days.

### F3. Quality metrics dashboard [P2]

**Observed:** The audit produces per-article stats but no aggregate
views over time.

**Actions:**
- A `pipeline metrics` subcommand that aggregates audit + evaluator
  scores across all content
- Trend line (after each regeneration cycle): verification rate, mean
  quality score, etc.
- Per-law breakdown
- Optional: a small static dashboard page on the site showing
  aggregate health

**Effort:** ~1 week.

---

## G. Content strategy & coverage

### G1. Cantonal law expansion (eventually) [P3]

**Observed:** CLAUDE.md scopes the project to federal law. Cantonal law
is a separate, larger universe — but the most-cited cantonal codes (ZH
Civil Procedure, GE Code, etc.) are central to actual legal practice.

**Actions:** explicitly out-of-scope for now per project vision. Note for
the long term: when federal coverage is solid, the same pipeline can
trivially extend to cantonal codes.

**Effort:** N/A — placeholder.

### G2. Concept pages: more depth & cross-linking [P1]

**Observed:** Concept pages (under `content/concepts/`) cover
cross-cutting legal concepts. They're a great pattern, but the current
set is small.

**Actions:**
- Identify the top 30 concepts that span multiple laws
  (Verhältnismässigkeit, Treu und Glauben, Willkür, etc.)
- Generate concept pages for each
- Bidirectional linking: each article that touches a concept gets a
  link to the concept page; each concept page links to all relevant
  articles

**Effort:** ~2 weeks (generation + curation).

### G3. Contested questions: format refinement [P2]

**Observed:** Contested questions (`content/contested/`) document
doctrinal debates. Format could be sharper:
- "Position A" / "Position B" with named authors and arguments
- "Court status" — what has the Federal Supreme Court said?
- "Practical implications"

**Actions:**
- Update `guidelines/contested.md` with the sharper format
- Regenerate existing contested pages

**Effort:** ~3 days.

### G4. Comparative law integration [P2]

**Observed:** Swiss law is heavily influenced by German, French, and
international law. The current commentary mentions parallels (ECHR,
EU directives) but doesn't systematically integrate them.

**Actions:**
- Add a "Comparative" section to doctrine layers for relevant
  articles (e.g., Art. 8 BV → ECHR Art. 14, EU Charter Art. 21,
  German Grundgesetz Art. 3)
- Per-law guidelines specify which foreign systems to compare to
- Optional: link to authoritative foreign-law sources

**Effort:** ~1 week per law.

---

## H. Open source & community

### H1. Contribution guide [P1]

**Observed:** No `CONTRIBUTING.md`. No issue templates. No clear
on-ramp for outside contributors.

**Actions:**
- Write CONTRIBUTING.md covering: how to set up the dev environment,
  how to propose content fixes, how to propose pipeline improvements
- Issue templates: "Article correction", "Pipeline bug", "Feature
  request"
- Code of conduct (Swiss legal community is small; clarity matters)

**Effort:** ~1 day.

### H2. Reader-facing changelog [P2]

**Observed:** `content/changelog/` has entries but they're terse and
operations-focused. Readers want to know "what changed in BV last
month".

**Actions:**
- Auto-generated reader-facing changelog from git history + meta.yaml
  versions
- Filter by law, date range
- Highlight major regenerations vs. minor fixes

**Effort:** ~3 days.

### H3. CI/CD pipeline [P1]

**Observed:** Tests run locally. No CI on push. No automated build
verification. No deploy automation.

**Actions:**
- GitHub Actions: lint + test on PR
- Nightly: scheduled audit + report
- Optional: nightly site build + deploy

**Effort:** ~2 days.

### H4. Public API for the corpus [P3]

**Observed:** Data is on disk in JSON/Markdown but not exposed via an
API. Programmatic access requires cloning the repo.

**Actions:**
- Static JSON dump per law (already kind of exists in `export/`)
- Optional REST API for live queries (overkill for now?)
- HuggingFace dataset (already exists per CLAUDE.md, just keep it
  current)

**Effort:** ~1 week if we go with REST.

---

## I. Trust, transparency & legal disclaimers

### I1. Per-article methodology disclosure [P1]

**Observed:** Each article was generated by an AI agent following a
specific prompt and tool set. Readers deserve to know the exact
methodology for each piece.

**Actions:**
- "How this was generated" expandable section per article
- Shows: model used, prompt version, evaluator scores, regeneration
  history, citation verification rate
- Builds trust by being transparent about the AI process

**Effort:** ~2 days.

### I2. Methodology page expansion [P1]

**Observed:** `/methodology` exists but is thin. Should explain:
- The full pipeline (research → generate → evaluate → translate)
- How citations are verified
- Known limitations and failure modes
- The audit methodology
- The role of the human (currently: minimal)

**Actions:**
- Comprehensive methodology rewrite
- Include the audit results aggregate ("As of 2026-04-11, 92.4% of
  citations are verified")
- Link out to the technical architecture (commit log, plans, etc.)

**Effort:** ~3 days.

### I3. Legal disclaimer / use as a starting point [P1]

**Observed:** Beta bar says "in active development" but doesn't make
the use-at-your-own-risk nature explicit enough for legal practitioners.

**Actions:**
- Per-article disclaimer footer: "This commentary is AI-generated and
  intended as a starting point. Always verify against primary sources
  before relying on it in legal proceedings."
- Methodology page: explicit statement about scope, limitations, and
  liability disclaimer
- Possibly a one-time modal on first visit (annoying but legally
  cleaner)

**Effort:** ~2 days.

---

## J. Distinctively-world-class moves

These are the moves that would distinguish openlegalcommentary from
other legal commentary projects (BSK, CR, OnlineKommentar, etc.) — not
just keep up.

### J1. Semantic search across the corpus [P1]

**Observed:** Pagefind handles keyword search. But "find articles
about state liability for unconstitutional acts" should also work.

**Actions:**
- Generate embeddings for each Randziffer (or each section)
- Vector search via FAISS or similar
- Hybrid keyword + semantic results
- Practitioners would use this constantly

**Effort:** ~1 week.

### J2. "Why this answer" trail [P2]

**Observed:** A reader who clicks through case law citations or BSK
references on Swiss commentary loses the trail. World-class would mean
showing the reasoning chain: "you asked X → here's the doctrine →
here's the leading case → here's the BSK position → here's the
parliamentary debate".

**Actions:**
- A "trail" UI per article: starts with statute text, expands to
  doctrine, expands to caselaw, expands to BSK, expands to Botschaft
- Each step is explicitly cited
- Practitioner can verify any link in the chain

**Effort:** ~2 weeks.

### J3. AI-assisted research mode (chat with the corpus) [P3]

**Observed:** The corpus is structured. With proper RAG, a practitioner
could ask "what's the current state of Swiss case law on X?" and get
a sourced answer.

**Actions:**
- A `/ask` interface that takes a legal question
- Retrieves relevant articles, cases, and Botschaft passages
- Generates a sourced answer with citations
- Distinct from the commentary (this is research assistance, not
  commentary)

**Effort:** ~1 month.

### J4. Daily "what changed yesterday" digest [P2]

**Observed:** The pipeline is *daily-updated* (per project vision).
Readers don't currently have a way to see what changed each day.

**Actions:**
- Daily email / RSS digest of regenerated articles
- Subject lines: "Art. 67 BV — new BGer decision integrated"
- Subscribers: practitioners who want to stay current

**Effort:** ~3 days (mostly RSS / email plumbing).

### J5. Academic integration [P3]

**Observed:** Swiss law schools use BSK and other commentaries
extensively. openlegalcommentary could be the open-access alternative
that gets adopted in teaching.

**Actions:**
- Outreach to law schools (UZH, UniBe, UniLU, UniGE)
- Citation format that academic norms accept
- Per-article DOI assignment
- Possibly partnership with a Swiss law journal for editorial review

**Effort:** N/A — relationship building, not engineering.

---

## K. Technical / infrastructure debt

### K1. Test coverage gaps [P1]

**Observed:** Test suite has 189 tests. Gaps:
- No integration test for the full `process_article` flow with mocked
  Anthropic responses
- No tests for `agents/translator.py`
- No tests for `agents/coordinator.py`
- No tests for the site (Astro / TypeScript)

**Actions:**
- Audit `coverage.py` output
- Fill the most painful gaps first (translator + integration)

**Effort:** ~1 week.

### K2. Type checking [P2]

**Observed:** Project uses Python 3.12 type hints but no `mypy` or
`pyright` enforcement.

**Actions:**
- Add `mypy --strict` to the dev workflow
- Or `pyright` if it's lighter weight
- Fix the resulting errors gradually

**Effort:** ~3 days for setup + initial pass.

### K3. Documentation: architecture & runbook [P1]

**Observed:** CLAUDE.md is the operator's guide. There's no architecture
overview, no runbook for common operations, no incident postmortems.

**Actions:**
- `docs/architecture.md` — high-level diagram of agents, pipeline, data
  flow
- `docs/runbook.md` — how to run a daily pipeline, how to investigate
  failures, how to roll back content
- `docs/postmortems/` — keep postmortems of significant issues (e.g.,
  the Sonnet write-skip discovery)

**Effort:** ~2 days.

### K4. Logging discipline [P2]

**Observed:** Logs are unstructured prose. Hard to parse, hard to
aggregate.

**Actions:**
- Structured logging (JSON lines) for the agent pipeline
- Keep human-readable logs for interactive runs
- Log fields: article, layer, attempt, outcome, cost_breakdown,
  duration

**Effort:** ~3 days.

---

## Snapshot priorities (next ~2 weeks if I had to commit)

If we're choosing from this list for the next sprint after Phase 2:

**Must-do (P0):**
- A1 — investigate Sonnet write-skip
- A2 — investigate Art. 78 translation skip
- C1 — fix `fetch_article_texts_i18n.py` for suffix articles
- C2 — fix preparatory-materials pipeline (BV first)
- D1 — tighten doctrine prompt (depends on A1)

**Should-do (P1):**
- A3 — full cost reporting
- B1 — wire up literature citation extraction
- B2 — verify BGE refs against opencaselaw
- D4 — codify literature-format preference
- E1 — cross-reference click-through
- E2 — BGE auto-linking
- I1 — per-article methodology disclosure
- K3 — architecture & runbook docs
- H3 — CI on PRs

**Defer (P2/P3):**
- Everything else

Total P0 + P1 effort: roughly **3–5 weeks of focused work**. After that
the project would be in a meaningfully more world-class state across
quality, transparency, and reader experience dimensions.
