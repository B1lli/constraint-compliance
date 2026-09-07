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

## Inputs and defaults

`--root` defaults to the current working directory. The goal path is relative to the current working directory,
not to `--root`; `check.json` is written beside the goal file (normally `.gate/check.json`).
`file` and the `file_exists.pattern` glob resolve against `--root`; absolute paths also work.
Globs use Python `glob` with `recursive=True` (`**` is supported). Every matched path must pass;
no matches fails. Matches are not restricted to regular files: `file_exists` also accepts a directory,
while text validators try to open each matched path. Text is read as UTF-8 with invalid bytes replaced.

A criterion defaults to `hard: true`. An absent, null, or empty `validator` is treated as no check.
Supply `type` and a nonempty `file` for text checks: a text validator with a missing or empty `file` has no
artifact to read and is reported as undecided (`ok: null`), which fails a hard criterion. The checker does not
validate the whole goal schema or change its status.

Regexes use Python `re`. Only `forbidden_terms`, `required_terms`, `regex_absent`, `regex_present`, and the
**term** searches in `section_required_terms` honor `ignore_case` (default `true`). Other regex searches
are case-sensitive regardless of that field; use an inline `(?i)` where needed. No search automatically
sets multiline or dot-all flags; use `(?m)` / `(?s)` explicitly.

Headings are lines beginning with one to six `#` characters followed by whitespace. The parser does not
parse full Markdown: it does not recognize Setext headings or exclude fenced code blocks. A section includes
its own heading and all child subsections, ending before the next heading of the same or a higher level.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | At least one validator ran and every hard criterion with a validator passed. Soft failures or undecided soft checks do not fail the run. |
| `1` | At least one hard criterion with a validator failed, **or could not be decided** (illegal regex, unknown type, unreadable file). Undecided is treated as not passed. |
| `2` | No goal argument, missing/empty/non-list `rubric.criteria`, or no criterion has a nonempty validator. Zero checks is not a pass. |

Criteria without a validator are reported as `未判` (not checked) and left to the agent's audit and the independent evaluator.

Invalid JSON, an unreadable goal, or failure to write the result raises an uncaught error (normally exit 1),
without a fresh result report. Missing/invalid criteria write a report with `"nothing_checked": true` and empty
`results` before exiting 2, so a stale `check.json` from an earlier run is never left behind. A nonempty criteria
list with no validators writes the normal report and then exits 2.

## Types

Fields below are required unless marked `?`. See the shared defaults above.

| Type | Fields | Passes when |
|---|---|---|
| `forbidden_terms` | `file`, `terms` (regex list), `ignore_case?` | no term matches anywhere; empty `terms` passes |
| `required_terms` | `file`, `terms` (regex list), `ignore_case?` | every term matches at least once; empty `terms` passes |
| `heading_order` | `file`, `headings` (regex list) | the first match for each regex exists in strictly increasing heading positions; empty list passes |
| `section_required_terms` | `file`, `heading` (regex), `terms` (regex list), `ignore_case?` | the first matching section contains every term, including in its heading or children; missing heading fails, empty terms pass if the section exists |
| `ids_covered` | `file`, `ids` (literal string list), `as_heading?` (default `true`) | every id occurs case-sensitively in a heading with no adjacent word character or hyphen; with `false`, a literal substring anywhere suffices; empty list passes |
| `regex_absent` | `file`, `pattern` (regex), `ignore_case?` | the pattern matches nowhere |
| `regex_present` | `file`, `pattern` (regex), `ignore_case?` | the pattern matches at least once |
| `file_exists` | `pattern` (glob) | at least one path matches, including directories; `file` is unused |
| `numbers_subset` | `file`, `allowed?` (list, default `[]`), `ignore?` (list, default `[]`), `exclude_line_regex?` (default no exclusion) | every token matched by `\d+(?:\.\d+)?` outside excluded lines equals a stringified member of `allowed` or `ignore`; no numeric tokens passes |
| `table_header` | `file`, `first_cell` (literal string), `columns` (string list) | the first line starting with `\|` after stripping whitespace and containing `first_cell` anywhere yields exactly `columns` after splitting on pipes and stripping cell whitespace; no match fails |
| `status_vocab` | `file`, `id_regex` (regex), `vocab` (regex list) | every matching heading's section contains **at least one** vocabulary match (case-sensitive substring regex search, including the heading and children); zero matching headings fails |

`numbers_subset` compares textual tokens, not numeric values: signs are not part of tokens, commas split
numbers, and `1.0` differs from `1`. `status_vocab` does not require exactly one status, a standalone word,
or a status in the first sentence. `table_header` does not require a Markdown separator row or verify that
`first_cell` is the first cell.

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

Every RFP clause section must contain at least one of three status expressions:

```json
{ "type": "status_vocab", "file": "RFP响应.md", "id_regex": "^R-\\d\\d(?:\\s|$)", "vocab": ["不支持", "部分支持", "支持"] }
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

`ok` is `true` / `false` / `null` (not decided or no validator). For hard criteria **with a validator**, fix failures or undecided checks and rerun. Criteria without a validator remain `null`; assess them with artifact evidence in the agent audit and independent evaluation. Exit 0 does not establish whole-rubric compliance.
