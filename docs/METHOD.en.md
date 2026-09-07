# Method: compiling a taught rule into an auditable goal at use time

> Guangyao Chi, 2026-09. This is the method statement behind `SKILL.md`: what we claim, what we borrowed, how we
> measured, what we found, and what is still missing. Verdicts use three words only: PASS / FAIL / UNPROVEN (reason).
> 中文版：[METHOD.md](METHOD.md).

## 1. The problem: taught, but not learned

The most basic loop of a self-improving assistant is "the user corrects me once, I do it that way from now on".
*Remembering* is the easy half: write the rule into `CLAUDE.md` / `AGENTS.md`, into a memory note, or, as our
production assistant does, distil it from the conversation into a **learned item** and recall it when relevant.
The hard half is *obeying it after remembering*.

In August 2026 we audited the conversations of 270 production users for "dropped compliance". Of 14 attributable
incidents, 10 had the same shape: **the user had taught the rule long ago, the model had it in context, and it was
still dropped late in a long task**; 3 were recurrences of the same rule for the same user. The literature agrees:

- Within five turns, top models keep only 51.8–54.4 % session stability on system-message constraints; GPT-4o falls
  from 84.8 % at turn 1 to 33.7 % at turn 5 on dependent multi-turn tasks (SysBench, ICLR 2025).
- Models can recite verbatim the constraint they are violating; "knowing violation" rates run 8–99 % across seven
  models, and per-turn automatic monitoring is nearly useless (DriftBench, 2026-04).
- Self-correction without external feedback is often worse than none (Huang et al., ICLR 2024). "Check again" is not a fix.
- What works: **putting the rule back next to generation** (in PrefEval a one-line reminder lifts 10-turn preference
  adherence from about 13 % to about 99 %) and **decomposing the instruction into a checklist verified item by item**
  (RLCF, NeurIPS 2025; DVR, ACL 2025, Mistral-7B 24 % → 73 %).

So the problem splits in two: **① recall the rule in the right turn** (timing) and **② hold it once recalled**
(effect). This skill touches both, but its weight is on ②; ① is carried by one very short description.

## 2. The method: six steps, all performed by the main agent in its original context

| Step | Input | Processing | Output |
|---|---|---|---|
| 1 Three questions | the request + the taught rule present in context | Is there a rule that must not be broken? Who pays what if it is? Is there an artifact to audit? Any "no" exits. | continue / exit (zero cost) |
| 2 Five-line intent | conversation, attachments, recalled rules | deliverable, consumer, success signal, non-goals, cost of one mistake; write "unknown" rather than invent | `intent` |
| 3 Level | cost, recurrence, external exposure | L2 self-check list only; L3 goal + advisory independent evaluation; L4 external / compliance / money / recurred → evaluation mandatory; when unsure, L3 | `level`, `precision` |
| 4 Rubric | rule text + this task's materials | one checkable statement per criterion + how to judge + evidence type + hard/soft + source; proper nouns need a literal source; no vague criteria; each decidable from the artifact; ≤ 12; several rules merged into one rubric; the criterion the user complained about goes first and hard | `rubric.criteria` |
| 5 Goal | the above | write `.gate/goal.json` (`status: active`) before the heavy work; attach a `validator` wherever a criterion is machine-decidable | goal file |
| 6 Completion etiquette | artifact, goal file | treat "done" as unproven; for "every / all / whole document" criteria enumerate the objects first, then audit each; run the deterministic checker; spawn a read-only independent evaluator; on a hard `fail` / `unverifiable` keep working by default; `blocked` only after the same obstacle survives three rounds | `complete` + `evidence`, or `blocked` + `reason` |

Three positions run through the whole method:

1. **Judgment belongs to the agent that has the full context.** Whether it is worth it, how strong, how the criteria
   are written, whether to accept the evaluator's advice: none of this is delegated to keyword tables, to a small model
   in a separate context, or to code as final arbiter. Code and the evaluator only *remind*.
2. **Decide at the moment of use, when information is complete, not at teaching time.** Nobody can foresee every
   future scenario when the rule is taught, and pre-assigning a level makes teaching heavier. At teaching time only the
   sentence and a coarse audit question are kept; level, precision and rubric grow when the rule is used.
3. **Stronger is dearer; pay only when it is worth it.** L2 costs almost nothing; L3 adds one evaluation and some
   rework; L4 adds an independent session. The three questions are the toll gate.

## 3. Relation to prior work: what is ours, what is borrowed

Products with the same shape (searched 2026-09-06; scope and unchecked items at the end):

| | OpenAI Codex `/goal` (2026-04-30) | Claude Code `/goal` (2026-06) | Claude Managed Agents Outcomes (2026-05) | this method |
|---|---|---|---|---|
| Where the goal / rubric comes from | user-written objective | user-written condition (≤ 4,000 chars) | developer-written or uploaded rubric | **generated at use time from the taught rule + intent** |
| When it triggers | user types `/goal` or the model calls `create_goal` | user types `/goal` | developer configuration | **the request hits a rule the user taught and this turn delivers; judged by the agent** |
| Who judges completion | same model self-audits (completion-audit template in the continuation message) | a separate small model that only sees the dialogue, not the files | independent grader that reads the artifact | agent's own audit + deterministic checks + **independent evaluator that reads the artifact and only advises** |
| Levels | none | none | none | **L2 / L3 / L4 chosen by the agent at use time** |

**What we believe is original to this work**:

- the trigger source is "a taught rule is present and this turn delivers", not an explicit user command or a developer
  pre-configuration;
- the acceptance criteria and the goal are **generated from the taught rule plus intent at use time**, with a set of
  writing rules that makes them reproducible (literal source for proper nouns, no vague statements, decidable from the
  artifact, ≤ 12, merged, complained-about first);
- the strength level is chosen by the main agent at use time, and recurrence raises it;
- the evaluator and the deterministic validators **advise but never block**, yet the agent must answer them;
- fail-closed measurement discipline: a validator that cannot decide is UNPROVEN, not a pass; no validators at all is
  "nothing checked", not a pass; sampling one place is not a census.

**Borrowed, with thanks**: the goal loop and the wording of the completion audit come from the Codex `/goal`
continuation template (treat completion as unproven, find authoritative evidence per criterion, a narrow check does
not support a broad claim, `blocked` only after three rounds on the same obstacle); checklist decomposition follows
RLCF / DVR; "the judge must read the artifact" follows Agent-as-a-Judge (ICML 2025); "completion must carry evidence"
follows Evidence-Carrying Termination (2026-08).

**Not borrowed**: a dialogue-only small-model judge as the sole judge; code as a final contract enforcer; keyword
triggers; per-turn automatic violation scans.

## 4. Relation to "self-evolution"

No weights change here. Evolution lives in two places: the **persisted learned rules** (one correction leaves a
trace) and the **compilation at use time** (before each delivery the trace is recompiled into this delivery's
acceptance criteria). Memory systems solve *remembering*; this method solves *obeying after remembering*; the two are
complementary. Without the former, nothing triggers except the fourth situation (external requirements the agent
identifies itself); without the latter, remembered rules still drop in long tasks. Recurrence escalation is the one
point in the loop that gets "stronger with use": a rule that was violated once becomes dearer and harder next time.

## 5. How we measured and what we found

**Discipline.** Fixtures must not disclose that they are a test (a note such as "synthetic material for acceptance"
changes the model's behaviour in both directions). Every validator has a positive control (a compliant artifact must
pass) and a negative control (each mutation must turn exactly the named criterion red). Changes to the description
pass an over-fitting check against the test cases' own wording; a version that copies case text must be flagged.
UNPROVEN is a first-class verdict and is never folded into PASS or FAIL. Real-model readings on a shared gateway are
taken serially.

**Three hosts.** Codex CLI (multi-turn resume), Claude Code (`claude -p` multi-turn), and the production stack
(learned item auto-generated → recalled → delivered → skill listed).

**Triggering (problem ①):**

| Reading | Result | Verdict |
|---|---|---|
| Claude Code; description reduced to the single signal "hits a rule the user taught"; rule kept only in `CLAUDE.md` or local memory; never repeated in the conversation; three synthetic scenarios | fired in the right turn in **11 of 12** positive runs; **0 of 2** false fires; artifact held the rule in **12 of 12** | PASS (feasible on Claude Code) |
| same body with a 683-character description; real-incident replay case RC-01 | **0 of 11** | FAIL (a long description never fires) |
| short description; installed skills raised from 18 to 33 (description fully delivered) | 2 of 2 → 0 of 2 | direction holds, n = 2 |
| production stack; positives with the rule confirmed delivered | fired in **1 of 4**; 0 of 1 false fires | partially feasible; stuck at triggering |

**Effect (problem ②):** five synthetic scenarios ran green on Codex and Claude Code *without* the skill (120–180k
context, 4–6 compactions), meaning synthetic scenarios do not reach the real failure zone. The real-incident replay
case RC-01 never passed whole on the baseline arm; the one run where the skill fired *and was actually followed through*
passed whole. **"Fired" and "followed through" are two different things**; the method can only guarantee that the
first gives the second a chance.

**Two facts independent of the description, seen on both hosts:** a rule being delivered is not the rule being
obeyed; the skill firing is not the artifact being compliant (and not firing does not imply non-compliance). All four
combinations were observed.

## 6. Known limitations

1. Triggering rests on one sentence and is very sensitive to the host's skill-list length and description budget; on
   the production stack only 1 of 4 delivered positives fired, cause not isolated (four variables changed together).
2. The evaluator only advises; an agent determined to ship can ignore it. This is a design choice (no user-facing
   confirmation gates, no code as final arbiter) and the cost is stated.
3. Deterministic validators cover eleven decidable shapes; semantic criteria rely entirely on the audit and the evaluator.
4. The skill body is Chinese (the description is bilingual). An English body has not been written or measured.
5. A-grade evidence on the effect side (baseline red, gated green, replicated) exists for one real-incident replay case.

## 7. Glossary

- **Learned item**: one rule persisted from a user correction (our product's term); on other hosts, one entry in a memory or instruction file.
- **Three questions**: is there a rule that must not be broken / who pays what if it is / is there an artifact to audit.
- **Five-line intent**: deliverable, consumer, success signal, non-goals, cost of one mistake.
- **L2 / L3 / L4**: self-check list / goal + advisory evaluation / goal + mandatory independent evaluation.
- **Precision (precise / coarse)**: criteria written by the rules above, or the learned item's own coarse audit question reused.
- **Completion etiquette**: the audit, census, checks, evaluation and response to advice before marking complete.
- **Census for "all" criteria**: list the objects first, audit each; sampling does not count.
- **UNPROVEN**: not checked, not run, or premise failed; neither PASS nor FAIL.

## References

Codex `/goal` (OpenAI, CLI 0.128.0, 2026-04-30); Claude Code `/goal` (2026-06); Claude Managed Agents Outcomes
(public beta 2026-05); SysBench (arXiv 2408.10943, ICLR 2025); PrefEval (ICLR 2025); DriftBench (2026-04);
Huang et al., *Large Language Models Cannot Self-Correct Reasoning Yet* (ICLR 2024); RLCF (NeurIPS 2025); DVR (ACL 2025);
Agent-as-a-Judge (arXiv 2410.10934, ICML 2025); Evidence-Carrying Termination (arXiv 2608.23623, 2026-08);
Instruction (In)Stability (arXiv 2402.10962, COLM 2024). Prior-art search 2026-09-05/06 over arXiv, the ACL Anthology
and vendor documentation; Chinese-language communities and closed-source internals were not covered.
