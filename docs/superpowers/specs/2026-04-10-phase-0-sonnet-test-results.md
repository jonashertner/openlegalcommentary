# Phase 0 — Sonnet 4.6 test results

Experiment: can Sonnet 4.6 replace Opus 4.6 as the doctrine generator,
under Opus 4.6 as evaluator, to keep the BV+BGFA arc within a realistic
budget envelope? Motivation: the realised per-article cost on Opus 4.6 smoke
testing came in at ~\$13.50 — about 6x my pre-experiment estimate — which
would have blown the arc budget from ~\$930 to ~\$5,000.

## Experiment design

- **Generator:** Sonnet 4.6 (temporarily overridden in `agents/config.py`,
  reverted immediately after each test run)
- **Evaluator:** Opus 4.6 (unchanged — independent judge)
- **Translators:** Sonnet 4.6 (unchanged)
- **Sample:** 2 articles, 3 runs total (one re-run to test reliability)
- **Baseline:** currently-committed Opus-4-generated doctrine on disk

## Article selection

| Article | Law | Complexity | Baseline size |
|---|---|---|---|
| **BGFA Art. 12** (Berufsregeln) | BGFA (smallest law) | Moderate | 53-line doctrine |
| **BV Art. 9** (Willkürverbot + Treu und Glauben) | BV (flagship) | High (constitutional, tier-1) | 84-line doctrine |

## Runs and outcomes

### Run 1: BGFA Art. 12 (first attempt) — **invalid test**

Passed the evaluator with score 0.92 and the pipeline reported \$0.84 in
law-agent cost. **But Sonnet's law agent never called `write_layer_content`
for the German `doctrine` layer.** The existing Opus-4 content on disk was
untouched. The evaluator then read the (unmodified) baseline and scored it
0.92. The pipeline's PASS was for the pre-existing content, not for
anything Sonnet produced.

Evidence: `grep "Tool call: write_layer_content" <raw log> | uniq -c` showed
only 3 writes (`doctrine.en`, `doctrine.fr`, `doctrine.it` — the translators),
zero writes to `doctrine`. `git diff` against the baseline showed zero
changes to `content/bgfa/art-012/doctrine.md`.

This is a **reliability failure mode** worth naming: Sonnet's law agent
completed successfully (no error, stop_reason != tool_use) without
persisting its output. Possible causes include the agent reading the
existing doctrine via `read_layer_content` and concluding the task was
already done, or producing the final layer as text without wrapping it
in a `write_layer_content` call.

### Run 2: BV Art. 9 — **valid test**

| Metric | Sonnet | Opus-4 baseline | Delta |
|---|---|---|---|
| Cost (law agent) | **\$0.91** | ~\$5.50/attempt (estimate) | ~6x cheaper per attempt |
| Attempts | **1** | ? (not re-run) | — |
| Quality score | **0.92** | ? (not recorded) | Above 0.90 threshold |
| Doctrine lines | **108** | 84 | **+29%** |
| Randziffern | **27** | 21 | **+29%** |
| BGE citations | **15** | 3 | **+400%** |
| Flagged citations | **0** | 1 | 1 resolved |
| Verification rate | **92.9%** | 77.3% | +15.6 pts |

Sonnet wrote 177 lines of diff against the baseline — genuinely fresh
content, not a reproduction. Structure complete (all 6 required sections
plus a bonus bibliography), prose clean, citations properly formatted.
Passed Opus 4.6 evaluator on the first attempt.

### Run 3: BGFA Art. 12 re-run — **valid test, proves run 1 was non-deterministic skip**

Same config, same article, different outcome.

| Metric | Sonnet (re-run) | Opus-4 baseline | Delta |
|---|---|---|---|
| Cost | **\$1.18** | ? | — |
| Attempts | **1** | ? | — |
| Quality score | **0.92** | ? | Above threshold |
| Doctrine lines | **134** | 53 | **+153%** |
| Randziffern | **34** | 19 | **+79%** |
| Total citations | **59** | 29 | **+103%** |
| BGE citations | **54** | 19 | **+184%** |
| Flagged citations | **0** | 0 | stayed clean |
| Verification rate | **91.5%** | 65.5% | +26 pts |

The re-run wrote a dramatically richer doctrine than the Opus-4 baseline:
2.5x longer, 34 Randziffern covering 4 subsection categories (3.1–3.6,
5.1–5.4), 54 BGE citations. All 4 `write_layer_content` calls fired
correctly (`doctrine`, `doctrine.en`, `doctrine.fr`, `doctrine.it`).

## Headline findings

### 1. Sonnet 4.6 is dramatically cheaper than Opus 4.6

Realised per-article law-agent cost on 3 Sonnet runs: **\$0.84 – \$1.18**.
Compared to Opus's ~\$5-6 per attempt × ~2 attempts average = ~\$11-12 per
article for the law agent alone, Sonnet is **roughly 10-13x cheaper**.

This is smaller than the 5x headline for the token pricing alone because
the Opus generator in this pipeline needs more attempts on average
(evaluator rejections on Konzision) and the agentic loop accumulates more
input-cost overhead per attempt.

### 2. Sonnet 4.6 produces measurably better content than the Opus-4 baseline

**Across both valid test cases**, Sonnet 4.6 produced substantially more
substantive doctrine than the Opus-4 baseline: more Randziffern, dramatically
more BGE citations, zero flagged BSK citations. The audit verification rate
jumped 15-26 percentage points compared to the baseline.

### 3. Sonnet citation style is cleaner than Opus-4 in this pipeline

Both Sonnet outputs cited textbook authors in literature format
(Häfelin/Haller/Keller/Thurnherr, Rhinow/Schefer/Uebersax, Fellmann, etc.)
rather than using "BSK BV-Waldmann, Art. 8 N 51" style BSK citations.
This is more consistent with how Swiss constitutional and professional-
regulation practitioners actually cite sources in practice. It also
**eliminates the primary failure mode** the Phase 1 intervention was
supposed to target: fabricated "BSK author, N. number" references that
the ref data can't verify.

### 4. Sonnet has a non-zero write-skip failure mode

**1 out of 3 runs** (BGFA Art. 12 first attempt) completed the law-agent
loop without calling `write_layer_content` for the target German layer.
The evaluator then read the existing baseline content and scored it 0.92.
The pipeline reported PASS. Git diff revealed no content change.

This is the most important caveat in the report. If Sonnet becomes the
default doctrine generator, the pipeline needs a safeguard that verifies
the target file was actually written before marking the attempt as
successful. Without mitigation, ~33% of Sonnet runs (based on this tiny
sample) might silently pass without producing any new content.

## Caching verification

Caching is active on both Opus and Sonnet:

```
turn 0 usage: input=485  cache_write=4678 cache_read=0
turn 1 usage: input=5157 cache_write=0    cache_read=4678
...
turn 6 usage: input=80039 cache_write=0   cache_read=4678
```

Cache write once at turn 0, cache read on every subsequent turn of the
agentic loop. The system prompt at ~4,678 tokens is above the 1,024-token
minimum for Sonnet prompt caching to engage.

## Cost tally for Phase 0 so far

| Item | Cost |
|---|---|
| BV Art. 8 full regen (Opus 4.6 smoke test) | \$13.86 |
| BV Art. 67 partial regen (stopped mid-run) | ~\$6.10 |
| BGFA Art. 12 run 1 (Sonnet, invalid) | \$0.84 |
| BV Art. 9 (Sonnet, valid) | \$0.91 |
| BGFA Art. 12 run 2 (Sonnet, valid) | \$1.18 |
| **Total Phase 0 API spend** | **~\$22.89** |

Modestly over the \$10 Phase 0 estimate but justified by the blocker
discovery (Opus cost 6x estimate) and the Sonnet reliability discovery
(write-skip failure mode).

## Revised arc budget with Sonnet + reliability mitigation

Assumptions:
- Sonnet law-agent cost: **~\$1.00/attempt** (midpoint of \$0.84–\$1.18)
- Write-skip retry rate: **~30%** (1 in 3 × safeguard detection → retry)
- Effective per-article cost: ~\$1.00 × 1.3 = **~\$1.30**
- Evaluator + translators: not separately reported by pipeline (folded into
  the number above is an oversimplification — see caveat below)

| Phase | Revised estimate |
|---|---|
| Phase 0 | ~\$23 (actual, done) |
| Phase 1 (10 articles × 3 iter rounds × \$1.30) | ~\$40 |
| Phase 2 (271 articles × \$1.30) | **~\$355** |
| Phase 3 | ~\$75 |
| Phase 4 | \$0 |
| Contingency (25% — larger due to reliability risk) | ~\$125 |
| **Total arc** | **~\$620** |

**Still well under the \$930 original estimate**, with ~25% contingency
for iteration, extra retries from the write-skip issue, and unforeseen
failure modes.

### Caveat on the per-article cost

The pipeline's per-article PASS cost is the law-agent cost only. It does
not include the evaluator (separate Opus call) or the 3 translators
(separate Sonnet calls). Real total per article is closer to:

- Law agent: ~\$1.00
- Evaluator: ~\$0.50 (Opus)
- 3 translators: ~\$0.30 (Sonnet × 3)
- **Real total: ~\$1.80 per article**

At the real total, Phase 2 becomes 271 × \$1.80 = **~\$488**, and the full
arc is **~\$760-\$820**. Still well under the \$930 original.

## Recommended next steps

1. **Add a write-skip safeguard to `agents/generation.py`**: after
   `run_agent` returns, verify that the target layer file was modified
   (either by mtime comparison or by diff against pre-run content). If
   not, mark the attempt as failed and trigger a retry. This converts the
   reliability risk into a deterministic retry cost.

2. **Commit the switch to Sonnet for doctrine** in `agents/config.py`
   (`model_doctrine: str = "sonnet"`). Strong recommendation, based on:
   cost, quality, and citation-style advantage.

3. **Consider whether to commit the regenerated Sonnet content** (BGFA
   Art. 12, BV Art. 9, plus the earlier Opus 4.6 regen of BV Art. 8) or
   roll them into the Phase 2 bulk rollout. Either is defensible.

4. **Proceed to Phase 1** with Sonnet as the doctrine generator and the
   new write-skip safeguard in place. Phase 1's 10-article sample becomes
   both a prompt-intervention test AND a broader Sonnet quality validation.

## Open questions

- Why did Sonnet skip the write on run 1 of BGFA Art. 12? Is it related to
  Sonnet reading the existing doctrine via `read_layer_content`, or to
  the smaller article size, or something else?
- Does the write-skip rate hold at 33%, or was run 1 an unusual draw that
  would smooth out with a larger sample?
- Do translations stay byte-identical across Sonnet runs when the source
  German content changes? (The translator agents may benefit from the
  same reliability mitigation.)
- Would switching the evaluator from Opus to Sonnet also be safe? (Not
  tested here — evaluator quality is load-bearing and we intentionally
  left it on Opus for this experiment.)
