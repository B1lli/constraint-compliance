# constraint-compliance

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![CI](https://github.com/B1lli/constraint-compliance/actions/workflows/ci.yml/badge.svg)](https://github.com/B1lli/constraint-compliance/actions/workflows/ci.yml)
[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](scripts/gate_check.py)
[![Agent Skill](https://img.shields.io/badge/type-agent_skill-6f42c1.svg)](SKILL.md)

**An agent skill that turns a rule the user taught earlier into an auditable goal, at the moment it matters.**

When a request falls under a rule the user taught before (kept in a project instruction file, a memory note, or a
learned item), the agent decides *at use time* whether this delivery is worth a hard-compliance gate, compiles the
rule into verifiable acceptance criteria, sets a goal, audits the artifact against the criteria before declaring
completion, and answers an independent, advisory evaluator. Nothing is hand-written in advance; the rubric grows out of
the taught rule and the agent's reading of the task.

Written by Guangyao Chi ([B1lli](https://github.com/B1lli)). It began as the built-in skill of a production AI work
assistant and is released here under Apache-2.0. 中文说明见 [README.zh-CN.md](README.zh-CN.md)。

## Contents

- [Why](#why)
- [How it works](#how-it-works)
- [Install](#install)
- [Quick start](#quick-start)
- [What is in the repository](#what-is-in-the-repository)
- [Measurements](#measurements)
- [Differences from the production version](#differences-from-the-production-version)
- [Limitations](#limitations)
- [Contributing](#contributing)
- [Citation](#citation)
- [License](#license)

## Why

"Taught, but not learned." A user tells an assistant *"proposals must open with a section on the customer's
environment constraints"* or *"never answer an RFP capability question with 'planned for a future release'"*. The
sentence is saved, recalled next time, present in context, and the deliverable still violates it once the
conversation gets long and the work gets messy. Benchmarks call this knowing violation: models can recite the
constraint they are breaking (DriftBench, 2026), and system-prompt compliance halves within five turns (SysBench,
ICLR 2025). Reminding again does not fix it; "check your work again" without an external standard does not either
(Huang et al., ICLR 2024).

This skill gives a present rule teeth instead of repeating it:

1. **Three questions** decide whether a gate is worth its cost: is there a rule that must not be broken? who pays
   what if it is? is there an artifact to audit? Any "no" exits at zero cost.
2. **Five-line intent**: deliverable, consumer, success signal, non-goals, cost of one mistake. Written in context,
   never asked of the user.
3. **Level**: L2 attaches a self-check list; L3 sets a goal plus advisory independent evaluation; L4 (external
   delivery, compliance, money, or a rule that has already recurred) makes independent evaluation mandatory. The
   agent picks the level when the rule is *used*, not when it was taught.
4. **Rubric**: each criterion is one checkable statement about the artifact with a how-to-judge, an evidence type,
   hard/soft, and a source. Proper nouns need a literal source; vague criteria are banned; at most twelve.
5. **Goal**: written to `.gate/goal.json` before the heavy work starts.
6. **Completion etiquette**: treat "done" as unproven; enumerate before auditing "every"/"all" criteria; run the
   deterministic checker; spawn a read-only independent evaluator; on a hard `fail` or `unverifiable`, keep working
   by default.

The full method, what is original and what is borrowed, and the measurements are in
[docs/METHOD.en.md](docs/METHOD.en.md) (English) and [docs/METHOD.md](docs/METHOD.md) (中文).

## How it works

```
request hits a taught rule
        │
        ▼
 three questions ──no──▶ exit (zero cost)
        │ yes
        ▼
 intent (5 lines) ──▶ level L2 / L3 / L4 ──▶ rubric (≤12 criteria, validators where decidable)
        │
        ▼
 .gate/goal.json  (status: active)
        │
        ▼  ...do the work...
        │
 audit every criterion against the artifact
 python3 scripts/gate_check.py .gate/goal.json --root .      # deterministic checks → .gate/check.json
 independent evaluator (read-only sub-agent) → .gate/verdict.json
        │
        ▼
 hard fail / unverifiable ──▶ fix, re-audit, re-check, re-evaluate
 all hard pass ──▶ status: complete + per-criterion evidence
```

## Install

The skill is a directory with a `SKILL.md`; any host that reads that format can use it. Python 3.8+ (standard
library only) is needed for the checker.

**Claude Code**, user-wide:

```bash
git clone https://github.com/B1lli/constraint-compliance.git ~/.claude/skills/constraint-compliance
```

or project-wide by cloning into `<project>/.claude/skills/constraint-compliance`.

**Codex and other hosts**: place the directory under the host's skills folder. `SKILL.md` names the sub-agent
facility to use for independent evaluation on each host (`Agent` tool on Claude Code, `spawn_agent` on Codex) and
falls back to a fresh-eyes re-read where none exists.

The skill body is written in Chinese; the trigger description is bilingual. See [Limitations](#limitations).

## Quick start

Run the checker on the bundled example:

```bash
cd examples/rfp-response
python3 ../../scripts/gate_check.py .gate/goal.json --root .
```

Four of the six criteria carry validators and are checked; the other two are reported as "not checked, left to the
audit and the independent evaluator". Now edit `RFP响应.md` so one clause says the capability is "后续规划" (planned
for later) and run again: criterion c5 turns red and the script exits non-zero.

Run the test suite:

```bash
python3 -m unittest discover -s tests
```

## What is in the repository

| Path | What it is |
|---|---|
| [`SKILL.md`](SKILL.md) | The skill: trigger description and the six-section method |
| [`scripts/gate_check.py`](scripts/gate_check.py) | Deterministic checker: eleven validator types, fail-closed exit codes ([reference](docs/validators.md)) |
| [`scripts/check_markers.py`](scripts/check_markers.py) | Commit hygiene check used by the git hooks and CI |
| [`tests/`](tests/) | Positive and negative controls for every validator, exit-code semantics |
| [`examples/rfp-response/`](examples/rfp-response/) | A runnable goal file and artifact |
| [`docs/METHOD.en.md`](docs/METHOD.en.md) · [`docs/METHOD.md`](docs/METHOD.md) | Method statement, prior art, measurements, limitations |
| [`docs/PROVENANCE.md`](docs/PROVENANCE.md) | Dated design history and how to verify public timestamps |
| [`docs/validators.md`](docs/validators.md) | Validator reference |

## Measurements

Summary; details and the measurement discipline are in [docs/METHOD.en.md §5](docs/METHOD.en.md#5-how-we-measured-and-what-we-found).

| Setting | Result |
|---|---|
| Claude Code host, rule kept only in `CLAUDE.md` or local memory, never repeated in the conversation, three synthetic scenarios | skill fired in the right turn in **11 of 12** positive runs; **0 of 2** false fires on negative controls; artifact held the rule in **12 of 12** |
| Same body with a 683-character description, real-incident replay case | fired in **0 of 11** runs |
| Short description, number of installed skills raised from 18 to 33 | 2 of 2 → 0 of 2 (direction only, n = 2) |
| Production stack, rule confirmed delivered into context | fired in **1 of 4** positive runs; 0 of 1 false fires |

Two facts held on both hosts regardless of description: **a rule being delivered is not the rule being obeyed**, and
**the skill firing is not the artifact being compliant**.

## Differences from the production version

In the production assistant the skill is paired with a runtime: three goal tools (`create_goal` / `get_goal` / `update_goal`),
automatic continuation while a goal is open, an in-process judge and a hidden review session. This release swaps those
bindings for things every host has: the goal is a JSON file, the checks are a script, the evaluator is the host's
sub-agent. **The six-section method text is otherwise identical to the product version.** The production runtime and the
learning-item generation and recall pipeline are not part of this repository.

## Limitations

- Triggering rests on one short description and is sensitive to how many skills the host lists. On the production stack
  only 1 of 4 delivered positives fired; the cause is not isolated (four variables changed at once).
- The evaluator is advisory. An agent determined to ship can ignore it. This is a design choice (no user-facing
  confirmation gates, no code as final arbiter), and the cost is stated.
- Deterministic validators cover eleven decidable shapes; semantic criteria rely on the audit and the evaluator.
- The skill body is Chinese only. An English body has not been written or measured.
- A-grade evidence on the "holds the rule" side (baseline red, gated green, replicated) exists for one real-incident
  replay case so far.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues describing a case where the skill did not fire, or fired and the
artifact still violated the rule, are the most useful contribution; please say which of the two you saw.

## Citation

```bibtex
@software{chi_constraint_compliance_2026,
  author  = {Chi, Guangyao},
  title   = {constraint-compliance: a use-time gate that compiles a taught rule into an auditable goal},
  year    = {2026},
  version = {0.1.0},
  license = {Apache-2.0},
  url     = {https://github.com/B1lli/constraint-compliance}
}
```

Also available as [`CITATION.cff`](CITATION.cff).

## License

Apache License 2.0. See [LICENSE](LICENSE); keep [NOTICE](NOTICE) when redistributing.

## Acknowledgements

The goal loop and the wording of the completion audit follow OpenAI Codex's `/goal` continuation template.
Checklist-style decomposition of instructions follows RLCF (NeurIPS 2025) and DVR (ACL 2025). "The judge must read the
artifact" follows Agent-as-a-Judge (ICML 2025). Full references in [docs/METHOD.en.md](docs/METHOD.en.md#references).
