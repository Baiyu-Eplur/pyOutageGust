# Redundancy Audit — Draft.docx

Scope: manuscript-wide redundancy and repetition audit. Diagnosis only — no edits were made to Draft.docx.

Method: full read-through of the manuscript (~264 paragraphs, Abstract through References), cross-checked with an automated near-duplicate sentence scan, with every algorithmic match manually inspected in context before being reported here.

## Manuscript structure note

There is no separate "Discussion" heading — Section 5 is titled **Conclusion** but functions as Discussion+Conclusion combined (interpretation, limitations, future work, and synthesis all appear in one section, [P227–P234]). Content in that section was judged accordingly when assessing cross-section repetition.

---

## HIGH-CONFIDENCE TRUE REDUNDANCY

### 1. Duplicated closing sentence (Conclusion, final paragraph)

- **Location 1:** "This general approach is not specific to UK Power Networks, and could be applied to any distribution network operator that reports outage incidents at the level of individual restoration stages, under a comparable regulatory framework."
- **Location 2:** immediately following: "The same approach could be applied to any distribution network operator that reports outage incidents at the level of individual restoration stages, under a comparable regulatory framework."
- **Repeated idea:** the method generalizes beyond UKPN to any comparable DNO.
- **Classification:** A — TRUE REDUNDANCY.
- **Why:** The second sentence adds no new content, qualifier, or function — it restates the first almost verbatim. This reads as a leftover editing artifact (e.g., an unresolved revision where a rewritten sentence wasn't deleted).
- **Recommended action:** **DELETE** the second sentence.
- **Estimated removable words:** ~24
- **Confidence:** HIGH

### 2. Duplicated model-specification detail (Section 3.3, Model specification, two adjacent paragraphs)

- **Location 1** (equation-description paragraph): "…and ε is the error term. For the recovery margin, X_i additionally includes affected customers and its square."
- **Location 2** (very next paragraph): "For the recovery margin, the dependent variable is the natural logarithm of restoration duration, and the model additionally includes affected customers and its square as covariates."
- **Repeated idea:** the recovery model includes affected customers and its square as covariates.
- **Classification:** A — TRUE REDUNDANCY (paragraph-level).
- **Why:** The fact is stated once when defining the equation notation, then restated three sentences later with no new information — same specification detail, same function (defining the recovery model's covariate set).
- **Recommended action:** **MERGE** — keep the fact in one location (most naturally the notation sentence) and drop it from the prose sentence, which can simply state the recovery model's dependent variable.
- **Estimated removable words:** ~12
- **Confidence:** HIGH

---

## MEDIUM-CONFIDENCE — SHORTEN/REPHRASE CANDIDATES

### 3. Introduction: contribution paragraph vs. chapter roadmap ([P13] vs [P14])

- **Location 1** [P13]: "The first gap is addressed by characterising the exposure and recovery response to gust intensity using a quadratic specification… The second gap is addressed by quantifying the explanatory weight of gust relative to the affected-customer scale, both across the full population… and within the subset of events for which weather is the recorded cause."
- **Location 2** [P14]: "Section 4.1 establishes the nonlinear gust-outage response and reports the critical wind threshold… Section 4.2 quantifies the explanatory weight of gust relative to the affected-customer scale across the full population of outages. Section 4.3 examines whether this weight changes within the subset of events attributed to weather…"
- **Repeated idea:** what each of the two research gaps consists of and how Sections 4.1–4.3 resolve them — stated twice in immediate succession.
- **Classification:** Section-level — borderline A/B (repeated contribution claim). The roadmap sentence for Sections 2, 3, and 5 adds real navigational value; the Section 4.1–4.3 portion mostly re-describes what P13 just said.
- **Why not full deletion:** A roadmap paragraph is conventional and expected by readers/reviewers; removing it entirely would reduce navigability.
- **Recommended action:** **SHORTEN** — compress the Section 4.1–4.3 descriptions in the roadmap to short section labels (e.g., "Section 4.1 establishes the shape of this response; Sections 4.2–4.3 quantify its explanatory weight"), since the substantive description was already delivered in P13.
- **Estimated removable words:** ~40–60
- **Confidence:** MEDIUM-HIGH

### 4. Repeated "storm → same-day records not independent" justification (Section 3.2 vs Section 3.3)

- **Location 1** (Validation protocol, cross-validation folds): "The folds are built by date, not by individual record… This matters because a single storm can generate many outage records on the same day. These records are not independent of each other."
- **Location 2** (Model specification, SE clustering): "Standard errors are clustered by Local Authority District… A given storm can affect many incidents in the same district on the same day, so errors within a district are unlikely to be independent of each other."
- **Repeated idea:** storms create same-day, spatially clustered records that violate independence — used to justify two separate design choices (fold construction; SE clustering).
- **Classification:** Paragraph-level, borderline A/B (repeated methodological justification).
- **Why:** the underlying rationale is identical and re-derived from scratch rather than cross-referenced, even though it supports two distinct choices.
- **Recommended action:** **SHORTEN** — in Section 3.3, reference the rationale already given in 3.2 ("for the same reason as in Section 3.2") instead of restating it in full.
- **Estimated removable words:** ~15–20
- **Confidence:** MEDIUM

### 5. Near-verbatim limitation restated (Section 4.4 vs Conclusion)

- **Location 1** (4.4, Robustness): "The confirmation sample covers six months within a single autumn and winter period, rather than a full annual cycle, and is about one fifth of the size of the development sample."
- **Location 2** (Conclusion, limitations paragraph): "The temporal holdout used in Section 4.4 covers six months within a single autumn and winter period, rather than a full annual cycle."
- **Repeated idea:** the confirmation/holdout sample's limited seasonal coverage.
- **Classification:** C — NECESSARY RECAP (a limitations paragraph needs to stand alone for a reader who jumps straight to it), but the wording is copy-adapted almost verbatim.
- **Recommended action:** **REPHRASE** the Conclusion instance (e.g., "As noted in Section 4.4, the holdout does not span a full annual cycle…") rather than repeating the identical clause.
- **Estimated removable words:** ~8–10 (rewording, not deletion)
- **Confidence:** MEDIUM

### 6. Compressed restatement within one paragraph (end of Section 4.3, storm evidence)

- **Location:** "…a model that explains only a small share of total variation is not expected to track individual incidents closely once storms concentrate unmodelled sources of variation… into a short period. Weaker individual-incident tracking during storms and a modest population-level share of explained variance describe the same underlying limitation, not two separate findings."
- **Repeated idea:** weak storm-level tracking and low population-level R² are the same limitation.
- **Classification:** Sentence-level, borderline A/D. The final sentence mostly re-labels what the previous sentence already explained causally.
- **Why not high confidence:** the final sentence does add a small interpretive framing ("not two separate findings") that a reader might value.
- **Recommended action:** **MERGE** the two sentences into one if trimming is wanted; otherwise **KEEP**.
- **Estimated removable words:** ~15–20
- **Confidence:** MEDIUM (leaning D — author judgement)

---

## FUNCTIONAL REPETITION — NOT FLAGGED FOR REMOVAL (for transparency)

These recur across Abstract / Results / Conclusion but each instance does distinct rhetorical work, so they should be **KEPT**:

- **"Gust accounts for a modest/small share of variation, below affected customers" — Abstract, end of §4.2, Conclusion.** Abstract = whole-paper summary; §4.2 close = section-specific synthesis with a forward pointer to §4.3; Conclusion = whole-paper synthesis with practical implication drawn out. Classification: B. One minor note unrelated to redundancy: §4.2 uses "small" while Abstract/Conclusion use "modest" for the same quantity — a terminology-consistency point, not a redundancy issue.
- **"Two independent lines of evidence (recorded cause / named storms)" — §4.3 opening, §4.3 close, Abstract, Conclusion.** The §4.3 opening/close pair is normal section framing (announce → summarize); the Abstract/Conclusion pair is conventional summary-echo. Classification: B/C. Low priority even for rephrasing.
- **Exposure-margin turning-point caveat ("not confirmed under the same holdout") — Abstract, §4.4, Conclusion.** Each states the caveat at the altitude appropriate to its section (headline caveat → detailed robustness finding → reader-facing guidance). Classification: B.
- **Forward-pointers to the "restoration-stages" explanation — §2.3 (descriptive stats), §2.3 (correlation discussion), delivered in §4.1/Appendix D.** Two separate forward-references, each attached to a different empirical observation (bimodal duration distribution; near-zero customer/duration correlation), both resolved later. Classification: C — necessary recap/forward-reference, not redundant.
- **Figure/table captions restating body text** (e.g., Figure 4, Figure 9, Table 2 caption vs. its introducing sentence). This is standard, expected practice — captions must be self-contained. Not flagged.

---

## Summary

| # | Location(s) | Action | Confidence |
|---|---|---|---|
| 1 | Conclusion, final paragraph | DELETE duplicate sentence | HIGH |
| 2 | §3.3, two adjacent paragraphs | MERGE | HIGH |
| 3 | Intro §1, P13 vs P14 roadmap | SHORTEN | MEDIUM-HIGH |
| 4 | §3.2 vs §3.3 clustering rationale | SHORTEN | MEDIUM |
| 5 | §4.4 vs Conclusion limitations | REPHRASE | MEDIUM |
| 6 | End of §4.3 storm evidence | MERGE (optional) | MEDIUM |

Total realistically removable without any loss of meaning: roughly **110–150 words** across items 1–6 — small relative to the ~11,900-word manuscript, which reflects that this draft is generally tight; most apparent cross-section repetition is functional (Results → Discussion/Conclusion doing legitimate report → interpret → synthesize work) rather than true redundancy.

## Functional-completeness retrospective

- Covered all four requested levels (sentence, paragraph, section, cross-section) across the entire manuscript, including References for false-positive-checking.
- Preserved locked meaning — no wording was changed; this is diagnosis only, no file was edited.
- Distinguished true redundancy from functional repetition/necessary recap/author judgement as instructed, and reported the reasoning for each classification rather than flagging on lexical overlap alone.
- Used a deterministic near-duplicate sentence scan as supporting evidence, then manually inspected every flagged pair in context (several algorithmic matches were confirmed as false positives — e.g., parallel exposure/recovery reporting, reference-list formatting — and excluded).
- No blockers or unavailable sources; this was a bounded, single-document read-only task, so no project-state file was created.
