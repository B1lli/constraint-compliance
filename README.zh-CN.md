# constraint-compliance · 强遵循门控

> 一份给长任务、多轮对话 Agent 用的 skill：当这次要做的事命中了用户**以前教过**的一条规矩，
> 由 Agent 自己在交付前判断值不值得进行强遵循核对，把那条规矩**当场编译**成能逐条核对的验收标准，立目标、审计、回应独立评估，然后才说「做完了」。
>
> 作者池光耀（Guangyao Chi，GitHub [B1lli](https://github.com/B1lli)）。原为一款生产环境 AI 工作助理的内置 skill，2026 年 9 月以 Apache-2.0 公开。
> 方法说明见 [docs/METHOD.md](docs/METHOD.md)，设计时间线见 [docs/PROVENANCE.md](docs/PROVENANCE.md)，校验器参考见 [docs/validators.md](docs/validators.md)。English README: [README.md](README.md).

## 目录导航

- [它解决什么](#它解决什么)
- [工作流程](#工作流程)
- [安装](#安装)
- [试一下](#试一下)
- [目录](#目录)
- [实测读数](#实测读数)
- [与产品版的差别](#与产品版的差别)
- [局限](#局限)
- [参与](#参与)
- [引用](#引用)
- [许可](#许可)
- [致谢](#致谢)

## 它解决什么

「教过，但没教会。」用户对 Agent 说过「以后写方案先列客户环境约束」「投标应答不许用『后续规划』糊弄能力」，这句话被记进了
`CLAUDE.md`、记忆文件或产品的学习项库。下一次同类任务，规矩也确实被召回、进了上下文——但对话一长、活一杂，交付出来还是违反了它。
「学习项」指持久化保存的一条已学规矩；RFP 指征求建议书，响应文档用于逐条回答采购要求。
文献里这叫**知而违**：模型能逐字复述它正在违反的约束（DriftBench，2026），五轮对话系统提示遵循率就掉一半（SysBench，ICLR 2025）。
重复提醒不够；没有外部标准的「再检查一遍」也不解决问题（Huang 等，ICLR 2024）。

这份 skill 不是再提醒一遍。它把「规矩在场」变成「规矩有牙」：

1. **三问值不值**：有没有一条不该违反的规矩？做错了谁付什么代价？有没有可核对的产物？任一答「不」就退出，零成本。
2. **意图五行**：交付物、消费者、成功信号、非目标、错一次的代价——在当前上下文里写清，不问用户。
3. **选档**：L2 只附自检清单；L3 立目标 + 独立评估建议；L4 对外交付、合规、资金或已复发时，独立评估必做。档位由 Agent 在**使用时**定，不在教学时预设。
4. **写验收标准（rubric）**：每条是一句关于产物的可判断言，带判法、证据类型、硬/软、来源。专名必须有字面来源；禁空话；条数上限 12。
5. **立目标**：写进工作区 `.gate/goal.json`，在重活开始之前。
6. **收尾礼仪**：把「已完成」当作未证明逐条核；「每条 / 全文」类标准先列清单再普查，不许抽样冒充；跑确定性核对脚本；起独立评估者只读产物给逐条建议；建议是建议，但硬标准没过默认继续干。

完整方法、借鉴来源与读数见 [中文说明](docs/METHOD.md)和[英文说明](docs/METHOD.en.md)。

## 工作流程

```text
请求命中已学规矩
  → 三问（任一答否则退出，零成本）
  → 意图五行 → 选档 L2 / L3 / L4 → 验收标准（≤12 条，可判定项挂校验器）
  → .gate/goal.json（active；L2 不立目标）
  → 执行任务 → 逐条审计产物
  → python3 scripts/gate_check.py .gate/goal.json --root . → .gate/check.json
  → 只读独立评估（L3 建议，L4 必做）→ .gate/verdict.json
  → 硬标准 fail / unverifiable：修复、重新审计、核对与评估
  → 硬标准全过：complete + 逐条证据
```

## 安装

任何读 `SKILL.md` 的宿主都能用。Claude Code：

```bash
git clone https://github.com/B1lli/constraint-compliance.git ~/.claude/skills/constraint-compliance
```

放进项目级 `.claude/skills/constraint-compliance/` 也可以。

Codex，用户级安装：

```bash
git clone https://github.com/B1lli/constraint-compliance.git ~/.agents/skills/constraint-compliance
```

项目级则克隆到 `<project>/.agents/skills/constraint-compliance`。
见[宿主技能目录说明](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)。
其他宿主：把整个目录放到它的 skills 目录下。正文说明了各宿主的独立评估机制；没有子代理时，退回换一副陌生读者的眼光重读。

安装后，在要使用它的项目中新开宿主会话，请 Agent 对受已存规矩约束的交付使用 `constraint-compliance`，确认它读取本仓库的 `SKILL.md`。
安装只使技能可用，不证明它会自动触发或产物已合格。

正文只有中文，触发描述为中英双语；见[局限](#局限)。

需要 Python 3.8+（只用标准库）来跑 `scripts/gate_check.py`。

## 试一下

先进入克隆的仓库目录（上述用户级安装对应 `cd ~/.claude/skills/constraint-compliance` 或
`cd ~/.agents/skills/constraint-compliance`）。以下命令从仓库根目录运行；括号中的子 shell 不改变后续命令的工作目录。

```bash
(
  cd examples/rfp-response
  python3 ../../scripts/gate_check.py .gate/goal.json --root .
)
```

会看到六条标准里挂了校验器的四条逐条过 / 不过，另两条标「无脚本校验，靠审计与独立评估」。把 `examples/rfp-response/RFP响应.md` 里某一条的「支持」改成「后续规划支持」再跑，c5 会变红并以退出码 1 退出。撤销该编辑再跑，恢复退出码 0。

跑控制组测试（每种校验器一正一负，四条退出码语义）：

```bash
python3 -m unittest discover -s tests
```

## 目录

| 路径 | 是什么 |
|---|---|
| [`SKILL.md`](SKILL.md) | skill 本体：触发描述与六节方法 |
| [`scripts/gate_check.py`](scripts/gate_check.py) | 确定性核对：11 种校验器；「没核」不算通过（[参考](docs/validators.md)） |
| [`scripts/check_markers.py`](scripts/check_markers.py) | Git 钩子与 CI 使用的提交卫生检查 |
| [`tests/`](tests/) | 每种校验器的正控、负控和退出码语义 |
| [`examples/rfp-response/`](examples/rfp-response/) | 可运行的目标文件与产物 |
| [`docs/METHOD.en.md`](docs/METHOD.en.md) · [`docs/METHOD.md`](docs/METHOD.md) | 方法、先例、实测、局限 |
| [`docs/PROVENANCE.md`](docs/PROVENANCE.md) | 设计时间线与公开时间戳核对方式 |
| [`docs/validators.md`](docs/validators.md) | 校验器参考 |

## 实测读数

细节与计量纪律见 [METHOD.md 第五节](docs/METHOD.md#五怎么量量到了什么)。

| 场景 | 结果 |
|---|---|
| Claude Code，规矩只存于 `CLAUDE.md` 或本机记忆，对话不复述，三个自拟场景 | 正例 **11/12** 在正确轮次触发；阴性 **0/2** 误触发；产物 **12/12** 守住规矩 |
| 同一正文配 683 字符的长描述，真实事故复刻用例 | **0/11** 触发 |
| 短描述，可选技能数从 18 增至 33 | 2/2 → 0/2（仅方向，样本 2） |
| 生产真栈，已确认规矩送达上下文 | 正例 **1/4** 触发；阴性 **0/1** 误触发 |

两条与描述无关、两个宿主都出现的事实：**规矩送达 ≠ 规矩被遵循；skill 触发 ≠ 产物合格**。

## 与产品版的差别

原产品里的 skill 与运行时配套：`create_goal` / `get_goal` / `update_goal` 三个工具、目标未完成时的自动续行、进程内判官与隐藏验收会话。
这里的开源版把这些绑定换成任何宿主都有的东西：目标是一个 JSON 文件，核对是一个脚本，独立评估用宿主自带的子代理。
**六节方法正文与产品版逐字一致**（只改了工具绑定处的句子）。产品运行时、学习项的生成与召回不在本仓库内。

## 局限

- 触发依赖短描述，受宿主技能清单长度影响。生产真栈仅 1/4 已送达正例触发；四个变量同时变化，原因尚未隔离。
- 评估只是建议，Agent 可以忽略；这是不增加用户确认闸、不让代码终裁的设计选择。
- 确定性校验器覆盖 11 种可判定形状；语义标准依赖审计与独立评估。
- 正文只有中文；英文正文尚未编写或测试。
- 生效侧 A 档证据（基线红、启用后绿、多次复现）目前只有一条真实事故复刻用例。

## 参与

见 [CONTRIBUTING.md](CONTRIBUTING.md)。最有用的问题报告是「技能未触发」或「触发了但产物仍违规」的具体案例，请区分两者。

## 引用

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

也可使用 [`CITATION.cff`](CITATION.cff).

## 许可

Apache License 2.0，见 [LICENSE](LICENSE)；再分发须保留 [NOTICE](NOTICE)。

## 致谢

目标循环与完成审计措辞借鉴 Codex `/goal` 续行模板。指令清单分解借鉴 RLCF（NeurIPS 2025）与 DVR（ACL 2025）；
「评估者必须读产物」借鉴 Agent-as-a-Judge（ICML 2025）。完整参考见 [METHOD.md](docs/METHOD.md#参考)。
