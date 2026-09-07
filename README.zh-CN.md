# constraint-compliance · 强遵循门控

> 一份给长任务、多轮对话 Agent 用的 skill：当这次要做的事命中了用户**以前教过**的一条规矩，
> 由 Agent 自己在交付前判断值不值得上门，把那条规矩**当场编译**成能逐条核对的验收标准，立目标、审计、回应独立评估，然后才说「做完了」。
>
> 作者池光耀（Guangyao Chi，GitHub [B1lli](https://github.com/B1lli)）。原为一款生产环境 AI 工作助理的内置 skill，2026 年 9 月以 Apache-2.0 公开。
> 方法说明见 [docs/METHOD.md](docs/METHOD.md)，设计时间线见 [docs/PROVENANCE.md](docs/PROVENANCE.md)，校验器参考见 [docs/validators.md](docs/validators.md)。English README: [README.md](README.md).

## 它解决什么

「教过，但没教会。」用户对 Agent 说过「以后写方案先列客户环境约束」「投标应答不许用『后续规划』糊弄能力」，这句话被记进了
`CLAUDE.md`、记忆文件或产品的学习项库。下一次同类任务，规矩也确实被召回、进了上下文——但对话一长、活一杂，交付出来还是违反了它。
文献里这叫**知而违**：模型能逐字复述它正在违反的约束（DriftBench，2026），五轮对话系统提示遵循率就掉一半（SysBench，ICLR 2025）。

这份 skill 不是再提醒一遍。它把「规矩在场」变成「规矩有牙」：

1. **三问值不值**：有没有一条不该违反的规矩？做错了谁付什么代价？有没有可核对的产物？任一答「不」就退出，零成本。
2. **意图五行**：交付物、消费者、成功信号、非目标、错一次的代价——在当前上下文里写清，不问用户。
3. **选档**：L2 只附自检清单；L3 立目标 + 独立评估建议；L4 对外交付、合规、资金或已复发时，独立评估必做。档位由 Agent 在**使用时**定，不在教学时预设。
4. **写验收标准（rubric）**：每条是一句关于产物的可判断言，带判法、证据类型、硬/软、来源。专名必须有字面来源；禁空话；条数上限 12。
5. **立目标**：写进工作区 `.gate/goal.json`，在重活开始之前。
6. **收尾礼仪**：把「已完成」当作未证明逐条核；「每条 / 全文」类标准先列清单再普查，不许抽样冒充；跑确定性核对脚本；起独立评估者只读产物给逐条建议；建议是建议，但硬标准没过默认继续干。

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

需要 Python 3.8+（只用标准库）来跑 `scripts/gate_check.py`。

## 试一下

```bash
cd examples/rfp-response
python3 ../../scripts/gate_check.py .gate/goal.json --root .
```

会看到六条标准里挂了校验器的四条逐条过 / 不过，另两条标「无脚本校验，靠审计与独立评估」。把 `RFP响应.md` 里某一条的「支持」改成「后续规划支持」再跑，c5 会变红并以非零退出。

跑控制组测试（每种校验器一正一负，四条退出码语义）：

```bash
python3 -m unittest discover -s tests
```

## 目录

| 路径 | 是什么 |
|---|---|
| `SKILL.md` | skill 本体：触发描述 + 六节方法（何时用、意图、选档、rubric、立目标、收尾） |
| `scripts/gate_check.py` | 确定性核对：执行 rubric 里挂了 `validator` 的标准，写 `.gate/check.json`。11 种校验器；「没核」不算通过 |
| `tests/test_gate_check.py` | 校验器的正控与负控、退出码语义 |
| `examples/rfp-response/` | 一个能跑的最小例子：产物 + `.gate/goal.json` |
| `docs/METHOD.md` · `docs/METHOD.en.md` | 方法说明（中 / 英）：主张、与先例的关系、实测、局限 |
| `docs/validators.md` | 11 种校验器的参考 |
| `CONTRIBUTING.md` · `CHANGELOG.md` | 参与方式、版本记录 |
| `docs/PROVENANCE.md` | 设计与实现的时间线、公开时间戳怎么核 |

## 与产品版的差别

原产品里的 skill 与运行时配套：`create_goal` / `get_goal` / `update_goal` 三个工具、目标未完成时的自动续行、进程内判官与隐藏验收会话。
这里的开源版把这些绑定换成任何宿主都有的东西：目标是一个 JSON 文件，核对是一个脚本，独立评估用宿主自带的子代理。
**六节方法正文与产品版逐字一致**（只改了工具绑定处的句子）。产品运行时、学习项的生成与召回不在本仓库内。

## 实测读数（摘要，细节见 METHOD.md §5）

在 Claude Code 宿主上，规矩只放在 `CLAUDE.md` 或本机记忆里、对话原话不复述规矩：三个自拟场景正例 **11/12** 在该触发的那一轮调起了 skill，
阴性对照 **0/2** 误触发，产物 **12/12** 守住规矩；同一正文配旧版长描述在真实事故复刻用例上是 0/11。
两条与描述无关、两个宿主都出现的事实：**规矩送达 ≠ 规矩被遵循；skill 触发 ≠ 产物合格**。

## 许可与归属

Apache License 2.0，见 [LICENSE](LICENSE)。再分发须保留 [NOTICE](NOTICE)。引用见 [CITATION.cff](CITATION.cff)。参与见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## English summary

**constraint-compliance** is an agent skill for long-running, multi-turn assistants. When a request falls under a rule the user taught earlier
(persisted in a project instruction file, a memory note, or a learned item), the agent itself decides *at use time* whether this delivery is worth a
hard-compliance gate (three questions), writes a five-line intent, picks a level (L2 checklist / L3 goal + advisory evaluation / L4 mandatory independent
evaluation), compiles the rule into a rubric of verifiable criteria (literal-source rule for proper nouns, no vague criteria, ≤12), sets a goal in
`.gate/goal.json`, and before declaring completion audits the artifact criterion by criterion, runs a deterministic checker, and answers an independent
read-only evaluator whose verdict is advisory. Rubric and goal are *generated from the taught rule at use time*, not hand-written in advance; the level is
chosen by the agent when the rule is used, not when it was taught. Originally the built-in skill of a production AI work assistant; the six-section method text is
identical to the product version, only the tool bindings are swapped for a file protocol. See `docs/METHOD.md` for claims, prior art, measurements and
limitations. Apache-2.0; keep `NOTICE` on redistribution.
