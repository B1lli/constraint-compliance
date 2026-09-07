# Validator reference

`scripts/gate_check.py` runs the deterministic checks attached to rubric criteria in `.gate/goal.json` and writes the result to `.gate/check.json`.

```bash
python3 scripts/gate_check.py .gate/goal.json --root <workspace root>
```

A criterion carries a check by adding a `validator` object:

```json
{ "id": "c5", "text": "…", "howToJudge": "…", "expectedEvidence": "artifact", "hard": true,
  "validator": { "type": "forbidden_terms", "file": "RFP响应.md", "terms": ["后续规划"] } }
```

All `file` values are relative to `--root` and may be globs. When a glob matches several files, **every** file must pass. Regular expressions use Python `re` syntax; matching is case-insensitive unless `"ignore_case": false`.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | Every hard criterion that has a validator passed. Soft failures are printed but do not fail the run. |
| `1` | At least one hard criterion with a validator failed, **or could not be decided** (illegal regex, unknown type, unreadable file). Undecided is treated as not passed. |
| `2` | Nothing was checked: the goal has no `rubric.criteria`, or no criterion has a validator. Zero checks is not a pass. |

Criteria without a validator are reported as `未判` (not checked) and left to the agent's audit and the independent evaluator.

## Types

| Type | Fields | Passes when |
|---|---|---|
| `forbidden_terms` | `file`, `terms` (regex list), `ignore_case?` | none of the terms match anywhere in the file |
| `required_terms` | `file`, `terms` (regex list) | every term matches at least once |
| `heading_order` | `file`, `headings` (regex list) | every heading regex matches some Markdown heading, and they appear in the given order |
| `section_required_terms` | `file`, `heading` (regex), `terms` (regex list) | the section under the first heading matching `heading` contains every term |
| `ids_covered` | `file`, `ids` (literal list), `as_heading?` (default `true`) | every id appears in a heading (`as_heading: true`) or anywhere in the text (`false`) |
| `regex_absent` | `file`, `pattern` | the pattern matches nowhere |
| `regex_present` | `file`, `pattern` | the pattern matches at least once |
| `file_exists` | `pattern` (glob) | at least one file matches |
| `numbers_subset` | `file`, `allowed` (list), `ignore?` (list), `exclude_line_regex?` | every number in the file (outside excluded lines) is in `allowed` ∪ `ignore` |
| `table_header` | `file`, `first_cell`, `columns` (list) | the first Markdown table row containing `first_cell` has exactly these columns in this order |
| `status_vocab` | `file`, `id_regex`, `vocab` (regex list) | every section whose heading matches `id_regex` contains one of the vocab terms; zero matching sections fails |

## Examples

Forbid marketing superlatives in a customer-facing article:

```json
{ "type": "forbidden_terms", "file": "案例/*.md", "terms": ["最佳", "第一", "国家级", "顶级"] }
```

Require the six sub-items of a "customer environment constraints" section:

```json
{ "type": "section_required_terms", "file": "方案.md", "heading": "客户环境约束",
  "terms": ["网络", "信创", "运维", "部署环境", "已有系统", "安全合规"] }
```

Every RFP clause must carry exactly one of three status words:

```json
{ "type": "status_vocab", "file": "RFP响应.md", "id_regex": "R-\\d\\d", "vocab": ["不支持", "部分支持", "支持"] }
```

Numbers in a case study must come from the latest data sheet (years ignored, the keyword line excluded):

```json
{ "type": "numbers_subset", "file": "案例.md", "allowed": ["120000", "1.8", "37"], "ignore": ["2026"], "exclude_line_regex": "^关键词" }
```

## Output

`.gate/check.json`:

```json
{ "checked_at": "2026-09-07T12:00:00-0400", "hard_fail": 0, "hard_unproven": 0,
  "results": [ { "id": "c1", "hard": true, "ok": true, "note": "编号齐全", "has_validator": true },
               { "id": "c2", "hard": true, "ok": null, "note": "无脚本校验，靠审计与独立评估" } ] }
```

`ok` is `true` / `false` / `null` (not decided or no validator). The agent is expected to fix the artifact until every hard `ok` is `true`, then continue with its own audit and the independent evaluation.
