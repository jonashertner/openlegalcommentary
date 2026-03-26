# Workplan: World-Class Commentary — Revised

**Objective:** Deploy a trustworthy, open-access commentary on Swiss federal law. Every citation verified. Depth scaled by importance. Live and updating daily.

**Core principle:** A commentary with 20 verified Randziffern is infinitely more valuable than one with 150 partially fabricated ones.

---

## What We Have

- 232 BV articles with 3-layer commentary in 4 languages
- ~80% of the content is solid analysis grounded in real case law
- ~20% contains citations with fabricated textbook paragraph numbers
- A complete site with search, i18n, responsive design, SEO
- $565 already invested in content generation

## What We Don't Have

- The site isn't deployed yet
- Citations aren't verified — textbook N. numbers may be wrong
- No access to Botschaft full text (just BBl reference numbers)
- No EMRK case law integration
- No daily update automation

---

## Phase 1: Citation Cleanup & Deploy (3 days, ~$50)

The fastest path to a trustworthy live site.

### 1.1 Fix the citation policy (Day 1)

Update `guidelines/global.md`:
- BGE with Erwägungen: **always cite, always verified** via opencaselaw
- Botschaft with BBl number: **cite the number**, not a page we haven't read
- BSK/Commentary authors: **cite by name and article** (e.g., "Waldmann, BSK BV, Art. 8"), NOT fabricated Randziffer numbers
- Textbooks: **cite by author/title** (e.g., "Häfelin/Haller/Keller/Thurnherr, Bundesstaatsrecht"), NOT paragraph numbers
- Remove all specific N./page numbers from textbook citations unless from our BSK ref data

### 1.2 Batch-fix existing citations (Day 1-2, ~$50)

Write `scripts/fix_citations.py` that:
1. Scans all doctrine.md files for citation patterns
2. Strips fabricated N. numbers from textbook citations (regex: keep author/title, remove ", N \d+")
3. Keeps BSK citations that match our ref data
4. Keeps all BGE citations (verified via opencaselaw)
5. Regenerates affected translations

This is NOT regeneration — it's surgical cleanup of existing good content.

### 1.3 Deploy (Day 2-3)

- Configure Vercel or GitHub Pages
- Point openlegalcommentary.ch DNS
- Set up HTTPS
- Configure GitHub Secrets (ANTHROPIC_API_KEY, HF_TOKEN)
- Enable build-site.yml workflow
- Verify all pages render

**Milestone: Site live at openlegalcommentary.ch with honest citations.**

---

## Phase 2: Integrate the Botschaft (3 days, ~$100)

The single highest-ROI source integration. One PDF covers all 232 BV articles.

### 2.1 Extract Botschaft text

- Download BBl 1997 I 1 (Botschaft über eine neue Bundesverfassung) from Fedlex
- Extract via PyMuPDF
- Split into per-article sections
- Store as `scripts/botschaft_texts/bv.json`

### 2.2 Enrich Entstehungsgeschichte

For each article:
1. Load the relevant Botschaft excerpt
2. Generate an improved Entstehungsgeschichte section that quotes the actual Botschaft text
3. Replace only the Entstehungsgeschichte section of the existing doctrine (keep everything else)
4. Translate the updated section

This is a targeted improvement, not full regeneration.

### 2.3 Update prompts for future generation

Modify `agents/prompts.py` so that all future BV generation includes the Botschaft excerpt as context.

**Milestone: Every BV article cites the actual Botschaft text, not just a BBl number.**

---

## Phase 3: Deepen Foundational Articles (1 week, ~$300)

Only 15-20 articles need deeper treatment. The rest are fine at current depth.

### 3.1 Identify foundational articles

```
Tier 1 (~15 articles): Art. 5, 8, 9, 10, 13, 26, 27, 29, 29a, 35, 36, 41, 49, 190
```

These are cited in virtually every constitutional case. They deserve 40-80 Randziffern.

### 3.2 Deep generation for Tier 1

For each Tier 1 article:
1. Load the full text of top 20 leading cases via opencaselaw `get_decision`
2. Load the Botschaft excerpt
3. Load BSK ref data positions
4. Generate expanded doctrine with:
   - Full case law evolution narrative (not just a list)
   - All BSK author positions attributed correctly
   - EMRK parallel analysis (cited by article number, not fabricated ECtHR case law)
   - Practical application scenarios
5. Evaluate against enhanced criteria
6. Translate to FR/IT/EN

### 3.3 EMRK mapping (manual, no API needed)

Create `scripts/emrk_mapping.json` with 30 verified mappings:
```json
{
  "7": ["Art. 2 EMRK (Recht auf Leben)"],
  "8": ["Art. 14 EMRK (Diskriminierungsverbot)", "Protokoll 12 (nicht ratifiziert)"],
  "10": ["Art. 2 EMRK (Recht auf Leben)", "Art. 3 EMRK (Folterverbot)"],
  "13": ["Art. 8 EMRK (Achtung des Privatlebens)"],
  "15": ["Art. 9 EMRK (Gedanken-, Gewissens- und Religionsfreiheit)"],
  ...
}
```
This is constitutional law 101 — no API needed, just knowledge.

**Milestone: 15 foundational articles at world-class depth with verified citations.**

---

## Phase 4: Daily Automation (1 day, $0)

### 4.1 Enable daily-update.yml

Configure the GitHub Action with ANTHROPIC_API_KEY. The pipeline:
1. Queries opencaselaw for new BGE decisions
2. Maps them to BV articles via citation graph
3. Regenerates affected caselaw layers
4. Translates
5. Commits and deploys

### 4.2 HuggingFace auto-export

Enable export-huggingface.yml with HF_TOKEN. Every content push auto-exports.

**Milestone: Fully automated daily updates. The commentary is "living."**

---

## Phase 5: Expand to Other Laws (ongoing, ~$1,500/law)

Apply the proven pipeline to the next law. Priority order:

1. **OR** — highest practical demand (contract law, corporate law)
2. **StGB** — high public interest (criminal law)
3. **ZGB** — civil law fundamentals
4. **ZPO, StPO** — procedural codes
5. **SchKG, VwVG** — specialized

For each law:
1. Fetch articles and scaffold content (~$0)
2. Extract Botschaft text (~$0)
3. Generate commentary with honest citation policy (~$1,500)
4. Translate to 4 languages (included in generation)
5. Classify articles and deepen Tier 1 (~$300)

---

## What We're NOT Doing (and why)

| Rejected Idea | Why |
|---------------|-----|
| Regenerate all 232 BV articles from scratch | Wastes $565 of existing work. Fix citations instead. |
| 5-pass generation for every article | Over-engineered. Only Tier 1 needs deep treatment. |
| HUDOC API integration | Unreliable API, enormous data volume. Manual EMRK mapping is faster and more reliable. |
| Curia Vista scraping | Messy data, hard to parse per-article. Botschaft covers 90% of legislative history value. |
| Match St. Galler Kommentar depth | Wrong benchmark. We're the first FREE commentary. Our benchmark is: honest, useful, accessible. |
| 150 Randziffern for every article | Art. 155 (Parliamentary Services) doesn't need 150 N. It needs 15 good ones. |

---

## Budget

| Phase | Dev Time | API Cost |
|-------|----------|----------|
| Phase 1: Citation fix + deploy | 3 days | $50 |
| Phase 2: Botschaft integration | 3 days | $100 |
| Phase 3: Deepen Tier 1 | 5 days | $300 |
| Phase 4: Daily automation | 1 day | $0 |
| Phase 5: Next law (OR) | 5 days | $1,500 |
| **Total through OR** | **~17 days** | **~$1,950** |

---

## Success Criteria

1. **Site is live** at openlegalcommentary.ch
2. **Zero fabricated citations** — every N. number verified against our data
3. **15 foundational articles** at deep analysis level (40-80 N.)
4. **Daily automated updates** from opencaselaw
5. **All 4 languages** with consistent quality
6. **Botschaft text** actually quoted in Entstehungsgeschichte
7. **Users can trust** what they read — transparent about AI generation, honest about sources

---

## The Real Differentiation

We're not competing with BSK or St. Galler Kommentar. Those cost CHF 300-500 per volume and are behind paywalls. We're competing with **nothing** — there is no free, structured, multilingual commentary on Swiss federal law.

Our differentiation:
- **Free** (CC BY-SA 4.0)
- **4 languages** (no commercial commentary offers EN)
- **Daily updated** (commercial commentaries update every 5-10 years)
- **Machine-readable** (HuggingFace dataset, full-text search)
- **Honest about sources** (transparent citation policy, open methodology)
- **Living** (automated daily caselaw updates)

That's world-class for what it is. Not a replacement for BSK, but something that didn't exist before.
