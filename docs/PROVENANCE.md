# 设计与实现时间线 · Provenance

本文回答两件事：这套方法是谁、在什么时候做出来的；公开之后别人怎么核对这些日期。
时间戳一律写日期与时区（-0400，作者所在机器时区）。仓库内 SHA 指作者所在团队私有仓库里的提交，只有仓库成员能核；**对外可核的时间戳从本仓库第一次公开推送与打 tag 开始**，见第三节。

## 一、时间线

| 日期 | 事件 | 载体 |
|---|---|---|
| 2026-08-07 | 产品 V2 设计文档 §二.8「门控动作：验收门与独立验收」定稿：三件目标工具、两种验收形态、标志位循环门、四态结论、四条红线 | 内部飞书文档 |
| 2026-08-11 | 《强约束化：把「以后 XX 时必须 XX」编译成验收门》设计稿：对 270 个生产用户会话做「掉遵循」审计，14 个事件中 10 个是**用户教过、模型知道、长任务后期照样掉**；提出四档强度统一模型（L1 注入 / L2 软门 / L3 硬门 / L4 独立验收）与复发升档 | 内部设计文档 `docs/constraint-compiler-gate-design.md` |
| 2026-09-02 | 门控总账 v1 提交（`82a90a93`）：五档强度、路由判据、运行机制、模块波次；同日 skill 方法书第一版提交（`f7767845`，`prompt/skills/builtin/constraint-compliance/SKILL.md`） | 私有仓库 |
| 2026-09-03 | 总账 v3 定稿：按产品负责人修正——**不做小模型结构化触发、不在独立上下文里判意图；判断全部由主 Agent 在原始上下文里做；档位不在教学时定、由 Agent 使用时定；独立评估器只建议不阻塞；目标循环照抄 Codex** | 私有仓库 |
| 2026-09-04 ～ 09-06 | 效果测试装置与用例：五个合成 BA/SE 场景、三条真实事故复刻、阴性对照；三宿主（Codex、Claude Code、生产真栈）对照；先例统计（54 条做法分档）与同形状先例对照（Codex `/goal`、Claude Code `/goal`、Managed Agents Outcomes） | 私有仓库 |
| 2026-09-05 | 第六节补「全都要」型标准的逐个普查与脚本覆盖面提示（`0c0ff011`）；description 第一次重写（`d6705f9a`） | 私有仓库 |
| 2026-09-06 | description 收敛为单一信号「命中教过的规矩」，Claude Code 宿主 11/12 触发、0/2 误触发（`97f55141`） | 私有仓库 |
| 2026-09-07 | 移除死旋钮 `reviewModelTier`（`667e501a`）；本仓库建立，以 Apache-2.0 公开 | 本仓库 |

## 二、什么是本团队独立提出的、什么是借的

写在方法说明 [METHOD.md](METHOD.md) 第三节，此处只列结论：

- **独立提出**：由「用户教过的规矩在场 + 本轮要交付」触发门控；验收标准与目标从已学规矩加意图洞察**在使用时刻生成**；档位由主 Agent 在使用时决定；评估器与校验器**只建议不阻塞**；「没核不算过、零核对不算过」的 fail-closed 计量纪律。
- **明确借用**：目标循环与「完成审计」模板的措辞取自 OpenAI Codex `/goal`（2026-04-30 版）；「规矩拆成逐项清单再验」的思路与 RLCF、DVR 同源；「判官必须读产物」与 Agent-as-a-Judge 一致。

## 三、公开时间戳怎么核

下面每条都写明「证据是什么、谁记录的、怎么自己核」。归档服务尚未给出可核标识的，不视为已经归档。

1. **GitHub release 的发布时间（服务端记录）**：`v0.1.0` 的 release 由 GitHub 在 2026-09-07T15:59:08Z 记录发布（`published_at` 字段），仓库创建时间 2026-09-07T15:58:53Z。核法：
   `gh api repos/B1lli/constraint-compliance/releases/tags/v0.1.0 --jq .published_at`。
   注意 **Git tag 自带的 tagger 日期不是这个**：它存在本地 Git 对象里、由创建者设置，不能单独用来证明公开时间（见 [Git tag 文档](https://git-scm.com/docs/git-tag)）。
2. **Software Heritage 永久归档**：2026-09-07T15:59:24Z 完成首次访问，快照标识 `swh:1:snp:b8a315b25f63f42e1d15a03048f72818a8f8d5e7`。核法：
   https://archive.softwareheritage.org/browse/origin/directory/?origin_url=https://github.com/B1lli/constraint-compliance ，或用 API 查该 origin 的 visits。
3. **Zenodo DOI**：尚未取得。取得后在此登记 DOI 与归档记录时间；未登记前不据此声称已归档。
4. 仓库内 commit 的作者时间只作参考，不作为对外证据。

## 四、命名与归属

- 仓库归作者个人 GitHub 账号 `B1lli`，版权人为作者个人；fork 会保留「forked from B1lli/constraint-compliance」。
- skill 名保持功能性的 `constraint-compliance`，不加产品前缀：这是功能命名选择，不是触发效果结论。[METHOD.md 第五节](METHOD.md#五怎么量量到了什么)没有提供名称或前缀的对照实验，其触发影响为 UNPROVEN；作者归属放在 `NOTICE`、`CITATION.cff`、`SKILL.md` 的 frontmatter `metadata` 与本文里。
