#!/usr/bin/env python3
"""Deterministic gate checks for .gate/goal.json.

usage: gate_check.py .gate/goal.json --root <workspace root>

Each rubric criterion may carry a `validator` object. Supported types (all fields relative to --root):
  {"type":"forbidden_terms",        "file":"path or glob", "terms":["regex", ...], "ignore_case":true}
  {"type":"required_terms",         "file":"...", "terms":["regex", ...]}                # every regex must match
  {"type":"heading_order",          "file":"...", "headings":["regex1","regex2",...]}    # all present, in this order
  {"type":"section_required_terms", "file":"...", "heading":"regex", "terms":["regex",...]}  # inside one section
  {"type":"ids_covered",            "file":"...", "ids":["R-01","R-02"], "as_heading":true}
  {"type":"regex_absent",           "file":"...", "pattern":"regex"}
  {"type":"regex_present",          "file":"...", "pattern":"regex"}
  {"type":"file_exists",            "pattern":"glob relative to root"}
  {"type":"numbers_subset",         "file":"...", "allowed":["120000","1.8"], "ignore":["2026"], "exclude_line_regex":"^关键词"}
  {"type":"table_header",           "file":"...", "first_cell":"用例编号", "columns":["用例编号","场景",...]}
  {"type":"status_vocab",           "file":"...", "id_regex":"R-\\d\\d", "vocab":["不满足","部分满足","满足"]}
Results: printed and written to .gate/check.json.
Exit 1 if any hard criterion with a validator fails, or if such a criterion could not be decided
(illegal regex / unknown validator type / unreadable file) - "not checked" is not a pass.
When `file` is a glob, every matching file must pass.
"""
import sys, os, json, re, glob

def read(p):
    with open(p, encoding='utf-8', errors='replace') as f: return f.read()

def resolve_all(root, pat):
    return sorted(glob.glob(os.path.join(root, pat), recursive=True))

def headings(text):
    out = []
    for i, line in enumerate(text.splitlines()):
        m = re.match(r'^(#{1,6})\s+(.*?)\s*#*\s*$', line)
        if m: out.append((i, len(m.group(1)), m.group(2)))
    return out

def section(text, pat):
    hs = headings(text); lines = text.splitlines()
    for k, (ln, lvl, title) in enumerate(hs):
        if re.search(pat, title):
            end = len(lines)
            for ln2, lvl2, _ in hs[k+1:]:
                if lvl2 <= lvl: end = ln2; break
            return '\n'.join(lines[ln:end])
    return ''

def run_one_file(root, v, f):
    t = v.get('type')
    if t == 'file_exists':
        hits = sorted(glob.glob(os.path.join(root, v['pattern']), recursive=True))
        return bool(hits), f"匹配 {v['pattern']!r} 的文件：{hits[:3] or '无'}"
    text = read(f) if f else ''
    flags = re.I if v.get('ignore_case', True) else 0
    if t == 'forbidden_terms':
        hits = [(term, text[max(0, m.start()-20):m.end()+20].replace('\n', ' ')) for term in v['terms'] for m in re.finditer(term, text, flags)]
        return not hits, ('无命中' if not hits else f"{len(hits)} 处命中：" + '；'.join(f'[{a}] …{b}…' for a, b in hits[:6]))
    if t == 'required_terms':
        missing = [term for term in v['terms'] if not re.search(term, text, flags)]
        return not missing, f'缺少：{missing}' if missing else '全部出现'
    if t == 'heading_order':
        hs = headings(text); pos = []
        for pat in v['headings']:
            idx = next((i for i, (_, _, title) in enumerate(hs) if re.search(pat, title)), None); pos.append((pat, idx))
        missing = [p for p, i in pos if i is None]
        ok = not missing and all(pos[k][1] < pos[k+1][1] for k in range(len(pos)-1))
        return ok, f"缺少标题：{missing}" if missing else ('顺序正确' if ok else f'顺序不对：{[(p, i) for p, i in pos]}')
    if t == 'section_required_terms':
        sec = section(text, v['heading'])
        if not sec: return False, f"找不到标题 {v['heading']!r}"
        missing = [term for term in v['terms'] if not re.search(term, sec, flags)]
        return not missing, f'该节缺少：{missing}' if missing else '该节六项齐全' if len(v['terms']) == 6 else '该节全部出现'
    if t == 'ids_covered':
        hs = [title for _, _, title in headings(text)]
        missing = [i for i in v['ids'] if not (any(re.search(r'(?<![\w-])' + re.escape(i) + r'(?![\w-])', h) for h in hs) if v.get('as_heading', True) else re.search(re.escape(i), text))]
        return not missing, f'缺少编号：{missing}' if missing else '编号齐全'
    if t == 'regex_absent':
        m = list(re.finditer(v['pattern'], text, flags))
        return not m, ('无命中' if not m else f"{len(m)} 处：" + '；'.join(text[max(0, x.start()-20):x.end()+20].replace('\n', ' ') for x in m[:5]))
    if t == 'regex_present':
        m = re.search(v['pattern'], text, flags)
        return bool(m), (text[max(0, m.start()-20):m.end()+20].replace('\n', ' ') if m else '未出现')
    if t == 'numbers_subset':
        body = '\n'.join(l for l in text.splitlines() if not (v.get('exclude_line_regex') and re.search(v['exclude_line_regex'], l)))
        nums = re.findall(r'\d+(?:\.\d+)?', body)
        allowed = set(map(str, v.get('allowed', []))) | set(map(str, v.get('ignore', [])))
        bad = sorted(set(n for n in nums if n not in allowed))
        return not bad, f'不在允许表里的数字：{bad[:20]}' if bad else '全部数字都在允许表里'
    if t == 'table_header':
        for line in text.splitlines():
            if line.strip().startswith('|') and v['first_cell'] in line:
                cols = [c.strip() for c in line.strip().strip('|').split('|')]
                return cols == v['columns'], f'表头={cols}'
        return False, '找不到表头'
    if t == 'status_vocab':
        hs = headings(text); lines = text.splitlines(); bad = []; seen = 0
        for k, (ln, lvl, title) in enumerate(hs):
            m = re.search(v['id_regex'], title)
            if not m: continue
            end = len(lines)
            for ln2, lvl2, _ in hs[k+1:]:
                if lvl2 <= lvl: end = ln2; break
            body = '\n'.join(lines[ln:end])
            seen += 1
            if not any(re.search(w, body) for w in v['vocab']): bad.append(m.group(0))
        if not seen:
            return False, f"没有任何标题匹配 {v['id_regex']!r}，零个条款不算通过"
        return not bad, f'缺状态词的条款：{bad}' if bad else f'{seen} 条都有状态词'
    return None, f'未知校验类型 {t!r}'

def run_one(root, v):
    """file 是 glob 时逐个校验全部命中文件，全部通过才算通过。
    以前只取排序后的第一个文件，另外几个文件违规也判绿。"""
    if v.get('type') == 'file_exists' or not v.get('file'):
        return run_one_file(root, v, None)
    files = resolve_all(root, v['file'])
    if not files:
        return False, f"找不到文件 {v['file']!r}"
    rows = []
    for f in files:
        ok, note = run_one_file(root, v, f)
        rows.append((os.path.relpath(f, root), ok, note))
    if any(ok is None for _, ok, _ in rows):
        return None, '；'.join(f'{n}：{note}' for n, ok, note in rows if ok is None)
    bad = [(n, note) for n, ok, note in rows if ok is False]
    if bad:
        return False, f'{len(bad)}/{len(rows)} 个文件不成立：' + '；'.join(f'{n}：{note}' for n, note in bad[:4])
    return True, (rows[0][2] if len(rows) == 1 else f'{len(rows)} 个文件全部成立')

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    goal_path = sys.argv[1]; root = '.'
    if '--root' in sys.argv: root = sys.argv[sys.argv.index('--root') + 1]
    goal = json.load(open(goal_path, encoding='utf-8'))
    criteria = (goal.get('rubric') or {}).get('criteria')
    if not isinstance(criteria, list) or not criteria:
        print('不能核对：goal.json 里没有 rubric.criteria（标准列表）。本脚本只认这个形状：')
        print('  {"status":"active","level":"L3|L4","objective":"…","intent":"…","rubric":{"precision":"precise|coarse","criteria":[{"id":"c1","text":"…","howToJudge":"…","expectedEvidence":"artifact","hard":true,"validator":{…}}]}}')
        print('把标准写进 rubric.criteria 再跑。零条标准 = 什么都没核对，不是通过。')
        sys.exit(2)
    results = []; hard_fail = 0; hard_unproven = 0
    for c in criteria:
        v = c.get('validator')
        if not v: results.append(dict(id=c.get('id'), hard=c.get('hard', True), ok=None, note='无脚本校验，靠审计与独立评估')); continue
        try: ok, note = run_one(root, v)
        except Exception as e: ok, note = None, f'校验器异常：{e}'
        results.append(dict(id=c.get('id'), hard=c.get('hard', True), ok=ok, note=note, has_validator=True))
        if c.get('hard', True):
            if ok is False: hard_fail += 1
            # 挂了 validator 却没判出结果（非法正则、未知校验类型、读文件失败）：
            # 这是「没核」不是「通过」。硬标准一律 fail-closed 记 UNPROVEN 并让整体非零退出。
            elif ok is None: hard_unproven += 1
    out = dict(checked_at=__import__('time').strftime('%Y-%m-%dT%H:%M:%S%z'), hard_fail=hard_fail, hard_unproven=hard_unproven, results=results)
    os.makedirs(os.path.dirname(os.path.abspath(goal_path)), exist_ok=True)
    with open(os.path.join(os.path.dirname(os.path.abspath(goal_path)), 'check.json'), 'w', encoding='utf-8') as f: json.dump(out, f, ensure_ascii=False, indent=1)
    print('提醒：下面每条只是脚本读到的事实，不决定目标过不过；硬标准不过请先改产物。')
    for r in results:
        mark = {True: '通过', False: '不成立', None: '未判'}[r['ok']]
        print(f"- {r['id']} [{'硬' if r['hard'] else '软'}] {mark}：{r['note']}")
    ran = sum(1 for r in results if r['ok'] is not None)
    print(f'硬标准不成立：{hard_fail} 条；硬标准未判定（UNPROVEN）：{hard_unproven} 条；有脚本校验的标准：{ran}/{len(results)} 条')
    if hard_unproven:
        print('注意：上面标「未判」的硬标准挂了 validator 却没跑出结果（非法正则／未知校验类型／读不到文件）。没核不等于通过，按不通过处理。')
    if ran == 0:
        print('注意：没有任何一条标准挂了 validator，确定性核对一条都没跑。这不是通过，是「没核」。能判死的标准请挂上 validator 再跑。')
        sys.exit(2)
    sys.exit(1 if (hard_fail or hard_unproven) else 0)

if __name__ == '__main__':
    main()
