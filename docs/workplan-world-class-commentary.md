# Workplan: World-Class Commentary System

**Objective:** Build and deploy an open-access Swiss constitutional commentary that is citable in Federal Supreme Court briefs, grounded exclusively in verified primary sources, and updated daily.

**Principle:** Every citation must be traceable to a source we actually accessed. No fabricated Randziffer numbers. No hallucinated journal articles. If we can't verify it, we don't cite it.

---

## Phase 0: Source Audit & Citation Reform (Week 1)

### 0.1 Audit current citations

Scan all 232 BV doctrine files for citation patterns and classify:
- **Verified:** BGE citations (cross-checkable via opencaselaw)
- **Partially verified:** BSK author positions (from our ref metadata, but N. numbers unverified)
- **Unverified:** Textbook citations with specific N./page numbers, journal articles

Deliverable: `scripts/audit_citations.py` → report of verified vs. unverified citation counts

### 0.2 Define honest citation policy

Update `guidelines/global.md` and `guidelines/bv.md`:

**Tier 1 citations (verified, always allowed):**
- BGE with Erwägung: **BGE 139 I 161 E. 3.2.1** — verified via opencaselaw full text
- Botschaft with BBl number: **BBl 1997 I 141** — verified once Botschaft texts integrated
- Statute text: verified via Fedlex

**Tier 2 citations (metadata-verified, permitted with care):**
- BSK/Commentary author + article: "Waldmann, BSK BV, Art. 8" — author attribution verified from ref data
- Commentary position summaries — verified from our structured extraction
- Do NOT cite specific N./Randziffer numbers unless from our ref data

**Tier 3 citations (training-data sourced, restricted):**
- Textbook references without specific page/N.: "Häfelin/Haller/Keller/Thurnherr, Bundesstaatsrecht" — permitted as general reference
- Do NOT cite specific paragraph numbers from textbooks we haven't read
- Do NOT cite journal articles unless verified

**Forbidden:**
- Fabricated N./page numbers from any source
- Journal articles the system hasn't accessed
- Positions attributed to specific authors without verification

### 0.3 Update evaluator criteria

Modify `guidelines/evaluate.md` to:
- Accept Tier 1 citations as fully verified
- Accept Tier 2 citations with author attribution only
- Reject Tier 3 citations with specific page/N. numbers
- Add a new non-negotiable: "No unverifiable specific citations"

### 0.4 Regenerate prompts

Update `agents/prompts.py`:
- Instruct the law agent to only cite BGE with specific Erwägungen
- Instruct to reference textbooks by name only, not by fabricated N.
- Instruct to use BSK ref data positions exactly as provided

---

## Phase 1: Primary Source Integration (Weeks 1-2)

### 1.1 Botschaften (Federal Council Messages)

The Botschaft is the single most important source for legislative history. For BV, the key document is BBl 1997 I 1 (Botschaft über eine neue Bundesverfassung).

**Action:**
1. Download BV Botschaft PDF from Fedlex: `https://www.fedlex.admin.ch/eli/fga/1997/1_1_1_1/de`
2. Extract text via PyMuPDF (same pipeline as commentary extraction)
3. Split into per-article sections (the Botschaft discusses each article)
4. Store as `scripts/botschaft_texts/bv.json` keyed by article number
5. Inject relevant Botschaft excerpt into the generation prompt for each article

**Also integrate:**
- Botschaft zur Totalrevision (BBl 1997 I 1) — main source
- Botschaften for subsequent amendments (Art. 121a, 118b, 197, etc.)

Deliverable: `scripts/extract_botschaft.py`, `scripts/botschaft_texts/bv.json`

### 1.2 Parliamentary Debates (Curia Vista)

The Amtliches Bulletin records every parliamentary speech about each article.

**Action:**
1. Query Curia Vista for BV totalrevision debates (Geschäft 96.091)
2. Extract per-article debate excerpts (key votes, minority positions, explanations)
3. Store as `scripts/parliamentary_debates/bv.json`
4. For Tier 1 articles: include full debate context in prompt
5. For other tiers: include vote results and key positions only

Deliverable: `scripts/fetch_debates.py`, `scripts/parliamentary_debates/bv.json`

### 1.3 ECtHR Case Law (HUDOC)

For fundamental rights (Art. 7-36 BV), the Strasbourg case law is essential.

**Action:**
1. Map each BV fundamental right to its EMRK counterpart (manual, ~30 mappings)
2. Query HUDOC API for cases against Switzerland under each EMRK article
3. Also query for landmark cases from other states that shaped the doctrine
4. Store as `scripts/echr_cases/bv.json` keyed by BV article
5. Inject relevant ECtHR cases into caselaw generation prompt

Deliverable: `scripts/fetch_echr.py`, `scripts/echr_cases/bv.json`, `scripts/emrk_mapping.json`

### 1.4 Implementing Legislation Mapping

Map each BV competence/mandate article to its concretizing federal legislation.

**Action:**
1. Use opencaselaw `search_laws` to find laws that reference each BV article
2. Manual verification and enrichment
3. Store as `scripts/implementing_laws/bv.json`
4. Include in prompt: "Art. 8 BV is concretized by GlG (SR 151.1) and BehiG (SR 151.3)"

Deliverable: `scripts/map_implementing_laws.py`, `scripts/implementing_laws/bv.json`

---

## Phase 2: Article Classification & Context Generation (Week 2)

### 2.1 Significance Classification

Classify every BV article into tiers:

```
Tier 1 (Foundational, ~25 articles):
  Art. 1-6, 8-10, 13, 26-27, 29, 29a, 35-36, 41, 49, 121, 190, 191

Tier 2 (Important, ~55 articles):
  Remaining fundamental rights (Art. 7, 11-28, 30-34, 37-40)
  Key competences (Art. 54, 62, 72, 75, 89, 95, 104, 117-119)
  Key org provisions (Art. 148, 174, 188-189)

Tier 3 (Standard, ~100 articles):
  Most competence norms, organizational provisions

Tier 4 (Brief, ~50 articles):
  Transitional provisions (Art. 196-197), repealed content,
  minor organizational details
```

Deliverable: `scripts/article_classification.json`

### 2.2 Per-Article Context Generation

For each article, generate a structured research context by querying all integrated sources:

```python
# scripts/generate_article_context.py
for article in bv_articles:
    context = {
        "article": article.number,
        "tier": classification[article.number],
        "norm_type": classify_norm_type(article),  # grundrecht/kompetenz/organisation/programmatik
        "article_text": fedlex_text[article.number],
        "botschaft_excerpt": botschaft_texts.get(article.number, ""),
        "parliamentary_debate": debates.get(article.number, ""),
        "leading_cases": opencaselaw.find_leading_cases(article),
        "all_decisions_count": opencaselaw.count_decisions(article),
        "bsk_ref_data": bsk_refs.get(article.number, {}),
        "emrk_parallel": emrk_mapping.get(article.number, []),
        "echr_cases": echr_cases.get(article.number, []),
        "implementing_laws": implementing_laws.get(article.number, []),
        "cross_references": identify_cross_refs(article),
    }
    save(f"scripts/article_context/bv/{article.number}.json", context)
```

Deliverable: `scripts/generate_article_context.py`, `scripts/article_context/bv/*.json`

---

## Phase 3: Multi-Pass Generation Pipeline (Weeks 2-3)

### 3.1 Pipeline Architecture

Replace single-pass generation with a multi-pass pipeline:

```
Research Brief (from Phase 2 context)
    │
    ├─ Pass 1: Entstehungsgeschichte (historical analysis)
    │   Inputs: Botschaft excerpt, parliamentary debate, BSK historical positions
    │   Output: 5-20 N. depending on tier
    │
    ├─ Pass 2: Systematische Einordnung (systematic context)
    │   Inputs: Cross-references, norm type, EMRK parallels, implementing laws
    │   Output: 3-10 N.
    │
    ├─ Pass 3: Norminhalt (doctrinal core) — per paragraph of article
    │   Inputs: Article text paragraph, BSK positions, leading cases on this aspect
    │   Output: 10-30 N. per paragraph
    │
    ├─ Pass 4: Rechtsprechungsanalyse (case law synthesis)
    │   Inputs: ALL leading cases with full text (via opencaselaw)
    │   Output: Narrative of doctrinal evolution, not just a list
    │
    ├─ Pass 5: Praxis & Kritik (practice + critical assessment)
    │   Inputs: Implementing laws, practical scenarios, open questions
    │   Output: 5-15 N.
    │
    └─ Assembly: Combine passes, unify Randziffern numbering, cross-reference
        │
        └─ Evaluation: Verify citations against source data
```

### 3.2 Specialized Prompts

Each pass gets a specialized system prompt:

**Pass 1 (History):**
> "You are writing the Entstehungsgeschichte section. You have access to the actual Botschaft text and parliamentary debate records. Cite ONLY from these provided texts. Use exact BBl page references. Quote specific passages from the parliamentary debate. Do not fabricate parliamentary quotes."

**Pass 3 (Doctrinal Core):**
> "You are analyzing [specific paragraph]. The BSK reference data identifies the following scholarly positions: [inject BSK positions]. Attribute these positions to their authors. For case law, read the full BGE text via the tools provided and cite specific Erwägungen. Do not cite textbook paragraph numbers you cannot verify."

**Pass 4 (Case Law Synthesis):**
> "Read the full text of each leading case via get_decision. Analyze how the Federal Supreme Court's interpretation evolved. Identify: (a) the initial position, (b) turning points where doctrine shifted, (c) the current state, (d) open questions. Quote decisive passages with exact Erwägung references."

### 3.3 Source-Verified Evaluation

Update the evaluator to verify citations against actual source data:

1. **BGE verification:** For each BGE citation, check via opencaselaw that the case exists and relates to the article
2. **Botschaft verification:** For each BBl citation, check that the page exists in our extracted Botschaft text
3. **BSK position verification:** For each author attribution, check against BSK ref data
4. **No phantom citations:** Any citation to a source not in our data → rejection

### 3.4 Tier-Specific Generation Parameters

| Tier | Passes | Max turns/pass | Target N. | Est. cost |
|------|--------|---------------|-----------|-----------|
| 1 | All 5 | 30 | 80-150 | $15-25 |
| 2 | Passes 1,3,4,5 | 25 | 40-80 | $8-15 |
| 3 | Passes 1,3,4 | 20 | 25-50 | $4-8 |
| 4 | Single pass | 15 | 10-25 | $2-4 |

---

## Phase 4: Proof of Concept (Week 3)

### 4.1 Test on 5 Tier 1 Articles

Select 5 diverse Tier 1 articles to test the full pipeline:
- **Art. 8** (Rechtsgleichheit) — fundamental right, extensive case law
- **Art. 5** (Rechtsstaatsprinzip) — foundational principle
- **Art. 36** (Grundrechtseinschränkungen) — methodological cornerstone
- **Art. 49** (Vorrang Bundesrecht) — federalism core
- **Art. 190** (Massgebendes Recht) — constitutional review limitation

### 4.2 Quality Comparison

For each test article:
1. Generate with the new multi-pass pipeline
2. Compare side-by-side with current output
3. Verify every citation against source data
4. Measure: Randziffern count, citation accuracy, depth of analysis
5. Have a Swiss law expert review if possible

### 4.3 Iterate

Based on proof of concept results:
- Adjust prompt templates
- Refine tier boundaries
- Calibrate evaluation criteria
- Fix citation verification gaps

---

## Phase 5: Full BV Regeneration (Weeks 3-4)

### 5.1 Generate All 232 Articles

Run the multi-pass pipeline on all BV articles:
- Tier 1 first (highest quality standard)
- Then Tier 2, 3, 4
- Translation follows generation (FR/IT/EN)

### 5.2 Translation with Context

For translations, provide the translator with:
- The German source text
- The official Fedlex translation of the article text (for terminology consistency)
- The standard legal terminology from Fedlex termdat

### 5.3 Quality Assurance Pass

After full generation:
1. Run citation audit on all articles
2. Verify no Tier 3 citations with fabricated numbers remain
3. Check cross-reference consistency
4. Verify all BGE citations exist in opencaselaw

---

## Phase 6: Deployment (Week 4)

### 6.1 Site Deployment

- Deploy to Vercel or GitHub Pages
- Point openlegalcommentary.ch DNS
- Configure SSL
- Verify all pages render correctly

### 6.2 Automated Pipelines

Configure GitHub Actions secrets and enable:
- `daily-update.yml` — daily caselaw updates via opencaselaw
- `export-huggingface.yml` — auto-export to HuggingFace on content changes
- `build-site.yml` — auto-build and deploy on push

### 6.3 Monitoring

- Set up GitHub Actions failure notifications
- Monitor daily pipeline costs
- Track citation verification pass rates

---

## Phase 7: Continuous Improvement (Ongoing)

### 7.1 Daily Case Law Updates

The daily pipeline checks opencaselaw for new BGE decisions, regenerates affected caselaw layers, and deploys automatically.

### 7.2 Source Expansion

Incrementally add verified sources:
- Additional Botschaften for BV amendments
- Cantonal constitutional case law
- Federal Administrative Court decisions
- Additional commentary reference data

### 7.3 Law Expansion

After BV is world-class, apply the same system to:
1. OR (highest practical demand)
2. StGB (high public interest)
3. ZGB, ZPO, StPO, SchKG, VwVG

Each law requires its own:
- Significance classification
- Key literature identification
- Botschaft integration
- Commentary reference extraction

---

## Cost Estimate

| Phase | Effort | API Cost | Total |
|-------|--------|----------|-------|
| Phase 0: Citation reform | 1 day dev | $0 | $0 |
| Phase 1: Source integration | 3 days dev | ~$10 (API calls) | $10 |
| Phase 2: Classification + context | 1 day dev | ~$25 (context generation) | $25 |
| Phase 3: Pipeline build | 2 days dev | $0 | $0 |
| Phase 4: Proof of concept (5 articles) | 1 day | ~$100 | $100 |
| Phase 5: Full BV regeneration | 2 days runtime | ~$2,000 | $2,000 |
| Phase 6: Deployment | 1 day dev | $0 | $0 |
| **Total** | **~10 days** | **~$2,135** | **~$2,135** |

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Avg. Randziffern per article | 20 | 50+ (scaled by tier) |
| Citation verification rate | Unknown (many fabricated) | 100% verified |
| BGE coverage | Partial | All leading cases with analysis |
| Botschaft citations | BBl number only | Exact page + quoted passages |
| EMRK parallel coverage | Mentioned | Systematic comparison for all Grundrechte |
| Scholarly positions | ~3 per article | All major positions from BSK ref data |
| Practical application scenarios | 1 generic example | Domain-specific scenarios |
| Comparable to | Generic AI output | St. Galler Kommentar depth |
