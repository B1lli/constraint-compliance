# -*- coding: utf-8 -*-
"""gate_check.py 的正控与负控。

每种校验器至少一对：合格产物必须判「通过」，一个点名的缺陷必须让它单独变红。
另外钉住四条退出码语义：全过 0；硬标准不成立或未判定 1；没有任何 validator / 没有 criteria 2。
运行：python3 -m unittest discover -s tests
"""
import io, json, os, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, '..', 'scripts', 'gate_check.py')
sys.path.insert(0, os.path.dirname(SCRIPT))
import gate_check  # noqa: E402


def write(root, rel, text):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with io.open(p, 'w', encoding='utf-8') as f:
        f.write(text)
    return p


GOOD_DOC = """# RFP 响应

## R-17 审批流
支持。审批流可配置 5 级，见《配置说明》第 3 节。

## R-18 单点登录
部分支持。已支持 OIDC，待补证据：SAML 对接记录。

## R-19 审计日志
支持。保留 180 天，见 audit.md。

| 用例编号 | 场景 | 结论 |
|---|---|---|
| T-01 | 登录 | 通过 |

关键词：审批流、单点登录
"""


class ValidatorPairs(unittest.TestCase):
    """run_one 层：每个类型一正一负。"""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        write(self.root, 'doc.md', GOOD_DOC)

    def run_v(self, v):
        return gate_check.run_one(self.root, v)

    def test_forbidden_terms(self):
        self.assertTrue(self.run_v({'type': 'forbidden_terms', 'file': 'doc.md', 'terms': ['后续规划', 'GPT']})[0])
        self.assertFalse(self.run_v({'type': 'forbidden_terms', 'file': 'doc.md', 'terms': ['审批流']})[0])

    def test_required_terms(self):
        self.assertTrue(self.run_v({'type': 'required_terms', 'file': 'doc.md', 'terms': ['审批流', 'OIDC']})[0])
        self.assertFalse(self.run_v({'type': 'required_terms', 'file': 'doc.md', 'terms': ['审批流', 'SAML 已上线']})[0])

    def test_heading_order(self):
        self.assertTrue(self.run_v({'type': 'heading_order', 'file': 'doc.md', 'headings': ['R-17', 'R-18', 'R-19']})[0])
        self.assertFalse(self.run_v({'type': 'heading_order', 'file': 'doc.md', 'headings': ['R-18', 'R-17']})[0])
        self.assertFalse(self.run_v({'type': 'heading_order', 'file': 'doc.md', 'headings': ['R-17', 'R-20']})[0])

    def test_section_required_terms(self):
        self.assertTrue(self.run_v({'type': 'section_required_terms', 'file': 'doc.md', 'heading': 'R-18', 'terms': ['部分支持', 'OIDC']})[0])
        self.assertFalse(self.run_v({'type': 'section_required_terms', 'file': 'doc.md', 'heading': 'R-18', 'terms': ['180 天']})[0])
        self.assertFalse(self.run_v({'type': 'section_required_terms', 'file': 'doc.md', 'heading': 'R-99', 'terms': ['x']})[0])

    def test_ids_covered(self):
        self.assertTrue(self.run_v({'type': 'ids_covered', 'file': 'doc.md', 'ids': ['R-17', 'R-18', 'R-19']})[0])
        self.assertFalse(self.run_v({'type': 'ids_covered', 'file': 'doc.md', 'ids': ['R-17', 'R-20']})[0])
        # 只在正文出现、不在标题：as_heading 默认 true 判缺，关掉才算覆盖
        write(self.root, 'body.md', '# 响应\n\nR-21 支持。\n')
        self.assertFalse(self.run_v({'type': 'ids_covered', 'file': 'body.md', 'ids': ['R-21']})[0])
        self.assertTrue(self.run_v({'type': 'ids_covered', 'file': 'body.md', 'ids': ['R-21'], 'as_heading': False})[0])

    def test_regex_absent_present(self):
        self.assertTrue(self.run_v({'type': 'regex_absent', 'file': 'doc.md', 'pattern': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'})[0])
        self.assertFalse(self.run_v({'type': 'regex_absent', 'file': 'doc.md', 'pattern': r'R-1\d'})[0])
        self.assertTrue(self.run_v({'type': 'regex_present', 'file': 'doc.md', 'pattern': r'^关键词：'})[0] or
                        self.run_v({'type': 'regex_present', 'file': 'doc.md', 'pattern': r'关键词：'})[0])
        self.assertFalse(self.run_v({'type': 'regex_present', 'file': 'doc.md', 'pattern': r'来源：'})[0])

    def test_file_exists(self):
        self.assertTrue(self.run_v({'type': 'file_exists', 'pattern': 'doc.md'})[0])
        self.assertFalse(self.run_v({'type': 'file_exists', 'pattern': '归档/*.md'})[0])

    def test_numbers_subset(self):
        v = {'type': 'numbers_subset', 'file': 'doc.md', 'allowed': ['5', '180', '3'], 'ignore': ['17', '18', '19', '01'], 'exclude_line_regex': r'^\|'}
        self.assertTrue(self.run_v(v)[0])
        v2 = dict(v, allowed=['5', '3'])
        self.assertFalse(self.run_v(v2)[0])

    def test_table_header(self):
        self.assertTrue(self.run_v({'type': 'table_header', 'file': 'doc.md', 'first_cell': '用例编号', 'columns': ['用例编号', '场景', '结论']})[0])
        self.assertFalse(self.run_v({'type': 'table_header', 'file': 'doc.md', 'first_cell': '用例编号', 'columns': ['用例编号', '结论', '场景']})[0])
        self.assertFalse(self.run_v({'type': 'table_header', 'file': 'doc.md', 'first_cell': '编号X', 'columns': ['编号X']})[0])

    def test_status_vocab(self):
        v = {'type': 'status_vocab', 'file': 'doc.md', 'id_regex': r'R-\d\d', 'vocab': ['不支持', '部分支持', '支持']}
        self.assertTrue(self.run_v(v)[0])
        write(self.root, 'bad.md', GOOD_DOC.replace('部分支持。已支持 OIDC', '正在评估 OIDC'))
        self.assertFalse(self.run_v(dict(v, file='bad.md'))[0])
        # 一个条款都没匹配到：零个不算通过
        self.assertFalse(self.run_v(dict(v, id_regex=r'Q-\d\d'))[0])

    def test_glob_every_file_must_pass(self):
        write(self.root, 'out/a.md', '干净\n')
        write(self.root, 'out/b.md', '这里有 GPT\n')
        ok, note = self.run_v({'type': 'forbidden_terms', 'file': 'out/*.md', 'terms': ['GPT']})
        self.assertFalse(ok)
        self.assertIn('1/2', note)

    def test_missing_file_and_unknown_type(self):
        self.assertFalse(self.run_v({'type': 'forbidden_terms', 'file': 'nope.md', 'terms': ['x']})[0])
        self.assertIsNone(self.run_v({'type': 'no_such_type', 'file': 'doc.md'})[0])


class ExitCodes(unittest.TestCase):
    """main 层：退出码与 check.json。"""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        write(self.root, 'doc.md', GOOD_DOC)

    def run_main(self, goal):
        gp = write(self.root, '.gate/goal.json', json.dumps(goal, ensure_ascii=False))
        r = subprocess.run([sys.executable, '-X', 'utf8', SCRIPT, gp, '--root', self.root], capture_output=True, text=True)
        chk = os.path.join(self.root, '.gate', 'check.json')
        data = json.load(io.open(chk, encoding='utf-8')) if os.path.exists(chk) else None
        return r.returncode, r.stdout, data

    def goal(self, criteria):
        return {'status': 'active', 'level': 'L3', 'objective': 'o', 'intent': 'i',
                'rubric': {'precision': 'precise', 'criteria': criteria}}

    def test_all_pass_exit_0(self):
        code, out, data = self.run_main(self.goal([
            {'id': 'c1', 'hard': True, 'validator': {'type': 'forbidden_terms', 'file': 'doc.md', 'terms': ['GPT']}},
            {'id': 'c2', 'hard': True, 'text': '语义标准，不挂脚本'},
        ]))
        self.assertEqual(code, 0, out)
        self.assertEqual(data['hard_fail'], 0)
        self.assertEqual(data['hard_unproven'], 0)
        self.assertEqual([r['ok'] for r in data['results']], [True, None])

    def test_hard_fail_exit_1_soft_fail_exit_0(self):
        code, out, _ = self.run_main(self.goal([
            {'id': 'c1', 'hard': True, 'validator': {'type': 'forbidden_terms', 'file': 'doc.md', 'terms': ['审批流']}}]))
        self.assertEqual(code, 1, out)
        code, out, _ = self.run_main(self.goal([
            {'id': 'c1', 'hard': False, 'validator': {'type': 'forbidden_terms', 'file': 'doc.md', 'terms': ['审批流']}}]))
        self.assertEqual(code, 0, out)

    def test_unproven_hard_is_exit_1(self):
        # 非法正则：挂了 validator 却判不出来，硬标准按不通过处理
        code, out, data = self.run_main(self.goal([
            {'id': 'c1', 'hard': True, 'validator': {'type': 'regex_absent', 'file': 'doc.md', 'pattern': '('}}]))
        self.assertEqual(code, 1, out)
        self.assertEqual(data['hard_unproven'], 1)
        # 未知类型同理
        code, out, data = self.run_main(self.goal([
            {'id': 'c1', 'hard': True, 'validator': {'type': 'no_such_type', 'file': 'doc.md'}}]))
        self.assertEqual(code, 1, out)

    def test_no_validator_at_all_is_exit_2(self):
        code, out, _ = self.run_main(self.goal([{'id': 'c1', 'hard': True, 'text': '只有语义标准'}]))
        self.assertEqual(code, 2, out)
        self.assertIn('没核', out)

    def test_no_criteria_is_exit_2(self):
        code, out, _ = self.run_main({'status': 'active', 'objective': 'o', 'rubric': {'criteria': []}})
        self.assertEqual(code, 2, out)


if __name__ == '__main__':
    unittest.main()
