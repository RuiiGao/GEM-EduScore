# GEM-EduScore Evidence Schema V0.2

## 1. 基本原则

LLM读取Education材料后，不直接评分。

第一阶段只负责提取Evidence，并生成结构化Education Profile。

系统需要首先判断输入材料中包含：

- 单个教育活动；
- 多个教育活动；
- 教育工具；
- 教育资源；
- 教育传播项目；
- 或由多个上述内容组成的完整Education Portfolio。

如果材料中存在多个不同活动或教育工具，必须分别建立独立Record，不得将不同活动的人数、形式、结果和Evidence混合记录。

每一个判断统一记录：

- **Value**：提取结果
- **Status**：证据状态
- **Evidence**：支持该判断的原文
- **Confidence**：提取置信度

若原文没有提供相关信息：

```text
Value = Not Evidenced
```

---

## 2. Evidence Status

所有Evidence统一使用以下四种状态：

```text
Planned
Implemented
Observed Outcome
Not Evidenced
```

具体含义：

- **Planned**：材料明确说明该内容已经被纳入计划或设计，但尚不能证明实际实施。
- **Implemented**：材料明确证明相关活动、措施或评价已经实际实施。
- **Observed Outcome**：材料不仅证明已经实施，还提供了实际观察到的结果或效果。
- **Not Evidenced**：当前材料中没有找到足够证据证明该内容。

例如：

> “计划设计调查问卷。”

属于：

```text
Planned
```

> “活动结束后共回收有效问卷56份。”

属于：

```text
Implemented
```

> “后测正确率由61%提高至82%。”

属于：

```text
Observed Outcome
```

---

## 3. Confidence

LLM对Evidence提取结果的置信度统一使用：

```text
High
Medium
Low
```

---

# P. Portfolio Overview

当输入材料中包含多个Education活动、工具或资源时，首先建立Portfolio层级信息。

如果输入材料只描述一个独立活动，也可以建立一个仅包含单一Record的Portfolio。

## P1 Portfolio Name

整个Education项目或Education页面的名称。

## P2 Team

开展该Education Portfolio的iGEM团队。

## P3 Year

项目年份。

## P4 Portfolio Goal

提取整个Education体系希望解决的主要教育问题和总体目标。

## P5 Records Included

列出材料中识别出的所有独立教育Record。

例如：

```text
Record 01: Middle School Lecture
Record 02: Experiment Summer Camp
Record 03: Debate Competition
Record 04: iGEM Tutor Model
Record 05: Social Media Education
```

## P6 Cross-Record Relationships

记录不同Record之间是否存在明确联系。

例如：

- 一个活动是否引出了另一个活动；
- 一个活动的反馈是否影响后续活动；
- 一个教育工具是否被用于多个活动；
- 某一活动是否属于另一活动的延伸；
- 多个活动是否共同服务于同一教育目标。

如果材料没有明确说明Record之间的关系：

```text
Not Evidenced
```

---

# Record Extraction Rule

Portfolio中的每一个独立教育活动、工具、资源或传播项目，都必须分别建立一个Record。

以下 A～K 字段需要对**每一个Record分别提取**。

不得将不同Record的信息直接合并。

例如：

```text
Record 01
Middle School Lecture
→ 单独填写A-K

Record 02
Experiment Summer Camp
→ 单独填写A-K

Record 03
Debate Competition
→ 单独填写A-K
```

---

# A. Basic Information

## A0 Record ID

为每个独立Record分配编号。

例如：

```text
R01
R02
R03
```

## A1 Activity / Record Name

活动、教育工具或教育项目名称。

## A2 Team

开展该Record的iGEM团队。

## A3 Year

该Record对应年份。

## A4 Record Category

判断该Record在Education体系中属于哪一类对象。

允许类型包括：

```text
Educational Activity
Educational Tool
Educational Resource
Educational Campaign
Educational Program
Other
```

例如：

- 一场讲座 → Educational Activity
- 一个AI Tutor → Educational Tool
- 一本绘本或教材 → Educational Resource
- 系列社交媒体科普 → Educational Campaign
- 长期课程体系 → Educational Program

## A5 Activity Type

识别教育形式。

允许的主要类型包括：

```text
Lecture
Workshop
Camp
Experiment
Debate
Game
Digital Education
Social Media
Public Engagement
Teacher Education
Other
```

同一个Record可以同时属于多个类型。

对于并非传统活动的Educational Tool或Educational Resource，可根据实际用途选择最接近的类型；若无合适类型则使用Other。

## A6 Delivery Mode

判断该Record的主要实施或传播方式。

允许：

```text
Offline
Online
Hybrid
Asynchronous Digital
Not Applicable
Not Evidenced
```

例如：

- 线下课堂 → Offline
- Zoom讲座 → Online
- 线上线下同步活动 → Hybrid
- 社交媒体、在线资源库 → Asynchronous Digital
- 某些单纯教育资源 → Not Applicable

## A7 Target Audience

目标受众。

## A8 Age / Education Level

参与者年龄或教育阶段。

## A9 Participant Count

参与人数。

如果是数字教育、教育工具或传播活动，可以记录已知的用户人数或参与人数；如果只有浏览量而没有实际参与人数，不得把浏览量直接当作Participant Count。

## A10 Duration

活动持续时间。

对于持续开放的教育工具或教育资源，如无明确活动时间：

```text
Not Evidenced
```

或记录材料明确说明的开放周期。

## A11 Location

活动地点。

对于线上活动，可以记录：

```text
Online
```

## A12 Number of Sessions

活动开展次数或场次。

## A13 Collaborating Organizations

合作学校、机构、社区或其他组织。

---

# B. Goal & Audience

## B1 Education Goal

提取活动希望参与者：

- 学到什么；
- 理解什么；
- 能做什么；
- 改变态度或意识什么。

## B2 Audience Need

判断材料是否解释：

- 为什么选择这一群体；
- 他们原本有什么问题；
- 他们存在哪些学习需求。

## B3 Audience Adaptation

判断活动是否根据以下因素进行了调整：

- 年龄；
- 知识基础；
- 兴趣；
- 语言；
- 教育资源；
- 身体条件；
- 其他差异。

## B4 Audience Research

判断活动开展前是否进行：

- 调研；
- 访谈；
- 问卷；
- 教师咨询；
- 文献研究；
- 其他需求分析。

---

# C. Education Design

## C1 Teaching Methods

识别是否存在以下教学方式：

- Lecture
- Q&A
- Discussion
- Experiment
- Group Work
- Game
- Workshop
- Debate
- Case Study
- Design Task
- Student Presentation
- AI Interaction
- Other

## C2 Activity Sequence

提取活动实际流程。

例如：

```text
Introduction
→ Knowledge Learning
→ Experiment
→ Group Discussion
→ Presentation
→ Feedback
```

对于Educational Tool、Educational Resource等不存在传统活动流程的Record，可以提取其主要使用流程。

例如：

```text
User Question
→ AI Response
→ Follow-up Interaction
→ Knowledge Support
```

如果无法提取：

```text
Not Evidenced
```

## C3 Practice Component

判断是否存在：

- 实验；
- 模型搭建；
- 设计任务；
- 数据分析；
- 创作；
- 实际操作。

## C4 Student Output

判断学生是否产生：

- 作品；
- 方案；
- 实验结果；
- 展示；
- 报告；
- 问题；
- 观点。

---

# D. Interaction

## D1 Q&A

是否存在问答互动。

## D2 Group Interaction

是否存在：

- 小组合作；
- 小组讨论；
- 小组任务。

## D3 Student Expression

学生是否：

- 提问；
- 展示；
- 解释；
- 辩论；
- 表达自己的观点。

## D4 Participant Feedback

是否收集参与者意见。

## D5 Participant Influence

参与者的意见是否真正影响：

- 活动内容；
- 教学形式；
- 后续活动；
- 项目设计。

## D6 Co-design

参与者是否参与：

- 活动设计；
- 内容设计；
- 教材开发；
- 后续项目共同创造。

---

# E. Assessment & Evidence

## E1 Pre-test

是否有前测。

## E2 Post-test

是否有后测。

## E3 Questionnaire

是否进行正式问卷。

## E4 Interview

是否开展访谈。

## E5 Observation

是否存在系统性的行为观察记录。

## E6 Student Work

是否保存学生作品或任务成果。

## E7 Quantitative Results

是否存在量化数据。

例如：

- 正确率变化；
- 分数变化；
- 满意度；
- 完成率；
- 参与率。

## E8 Qualitative Results

是否存在：

- 学生反馈；
- 教师反馈；
- 访谈内容；
- 开放回答；
- 观察记录。

## E9 Goal-Outcome Alignment

现有评价是否真正对应最初的教育目标。

---

# F. Feedback & Iteration

## F1 Feedback Collection

是否正式收集反馈。

## F2 Feedback Analysis

是否对反馈进行：

- 分类；
- 统计；
- 总结；
- 编码；
- 比较。

## F3 Modification

反馈是否导致活动修改。

## F4 Reimplementation

修改后的方案是否再次实施。

## F5 Re-evaluation

第二次实施后是否重新评价效果。

---

# G. Documentation & Reuse

## G1 Teaching Materials

是否提供：

- PPT；
- 教案；
- Worksheet；
- Handout；
- Video；
- Reading Material。

对于Educational Tool或Educational Resource，应记录该工具或资源本身是否能够继续被他人访问和使用。

## G2 Activity Protocol

是否提供详细活动流程。

## G3 Experiment Protocol

如果涉及实验，是否提供实验步骤。

## G4 Implementation Guidance

是否说明：

- 所需人员；
- 时间；
- 设备；
- 材料；
- 注意事项。

## G5 Reflection

是否记录：

- 成功经验；
- 失败经验；
- 踩坑；
- 改进建议。

## G6 Localization

是否说明如何根据以下条件调整活动：

- 年龄；
- 地区；
- 资源条件；
- 文化；
- 语言。

## G7 Actual Reuse

是否已有其他团队、学校或机构实际复用。

---

# H. Empowerment

## H1 Knowledge Acquisition

参与者是否获得基础知识。

## H2 Skill Development

是否获得：

- 实验能力；
- 设计能力；
- 数据分析能力；
- 信息判断能力；
- 科学表达能力。

## H3 Independent Thinking

参与者是否形成自己的：

- 问题；
- 判断；
- 观点；
- 设计。

## H4 Independent Practice

参与者是否能够自主完成任务。

## H5 Continued Participation

是否有证据显示参与者之后继续：

- 学习SynBio；
- 参加活动；
- 开展项目；
- 加入社区。

## H6 New Contribution

参与者是否进一步：

- 制作教育资源；
- 组织活动；
- 贡献项目；
- 共同创造。

---

# I. Accessibility & Inclusivity

## I1 Resource Accessibility

是否考虑教育资源差异以及资源获取条件。

## I2 Digital Accessibility

是否考虑：

- 网络条件；
- 电子设备；
- 数字平台；
- 在线工具使用条件。

对于依赖AI、在线平台或其他数字工具的Record，应重点提取相关证据。

## I3 Language Accessibility

是否考虑语言差异和理解障碍。

## I4 Age Adaptation

是否针对不同年龄群体进行适配。

## I5 Disability Accessibility

是否考虑残障或其他特殊身体条件群体的参与需求。

## I6 Geographic Accessibility

是否考虑地理位置造成的教育资源差异。

## I7 Economic Accessibility

是否考虑参与成本和经济条件造成的限制。

## I8 Special / Underserved Groups

是否关注特殊群体或教育资源不足群体。

---

# J. Sustainability

## J1 Follow-up

活动结束后是否进行后续跟踪。

## J2 Repeated Activities

是否重复或连续开展相关活动。

## J3 Long-term Partnership

是否与学校、机构、社区等形成长期合作。

## J4 Community Building

是否形成持续参与的学习或教育社区。

## J5 Continued Resource Availability

教育资源是否能够在活动结束后继续获得和使用。

对于数字化教育工具、在线资源和社交媒体教育内容，应记录其是否可以持续访问。

## J6 Independent Sustainability

活动或相关资源是否具备在原团队退出后继续存在或运行的可能。

---

# K. Ethics & Responsibility

## K1 Ethical Issues Introduced

是否介绍以下相关伦理或责任问题：

- 生物伦理；
- AI伦理；
- 隐私；
- 技术风险；
- 公平；
- 科研责任；
- 社会影响。

## K2 Ethical Discussion

参与者是否真正讨论伦理问题。

## K3 Multiple Perspectives

是否比较不同立场或观点。

## K4 Ethical Argumentation

参与者是否需要形成并解释自己的判断。

## K5 Ethics Affecting Action

伦理思考是否进一步影响：

- 活动设计；
- 项目决策；
- 技术使用。

---

# L. Context Metrics

以下指标仅作为活动背景信息记录，不直接用于核心教育质量评分。

Context Metrics原则上应当按照每一个Record分别记录。

如需要，也可以在Portfolio层级进一步汇总，但汇总时必须避免重复计算同一参与者。

## L1 Offline Participants

线下参与人数。

## L2 Online Reach

线上传播或触达人数。

注意：

Online Reach不等同于实际教育参与人数。

例如：

```text
Video Views = 10,000
```

只能作为Online Reach记录，不得自动视为：

```text
Participants = 10,000
```

## L3 Number of Schools

覆盖学校数量。

## L4 Number of Cities / Regions

覆盖城市或地区数量。

## L5 Number of Audience Groups

涉及的不同受众群体数量。

## L6 Duration

活动持续时间。

## L7 Number of Sessions

活动开展场次。

## L8 Budget

活动预算。

## L9 Number of Organizers

活动组织人员数量。

## L10 Number of Partners

合作机构或合作方数量。

---

# 4. 标准Evidence输出格式

LLM对每一个Schema字段进行提取时，统一按照以下格式输出：

```text
Record:
R03 — Debate Competition

Field:
D5 Participant Influence

Value:
Participants' feedback influenced the subsequent education activity.

Status:
Implemented

Evidence:
“[原文中能够直接支持该判断的内容]”

Confidence:
High
```

其中：

- **Record**：说明该Evidence属于哪个独立教育Record；
- **Field**：对应Schema中的具体字段；
- **Value**：从材料中得到的结构化判断；
- **Status**：Planned / Implemented / Observed Outcome / Not Evidenced；
- **Evidence**：支持判断的原文；
- **Confidence**：High / Medium / Low。

---

# 5. 无Evidence时的输出格式

如果材料中没有找到相关信息，统一输出：

```text
Record:
R02 — Experiment Summer Camp

Field:
E1 Pre-test

Value:
Not Evidenced

Status:
Not Evidenced

Evidence:
None

Confidence:
High
```

这里：

```text
Confidence: High
```

表示：

> LLM对于“当前提供的材料中没有发现前测相关证据”这一判断具有较高置信度。

它并不意味着：

> 团队在现实中一定没有开展前测。

系统只能评价当前输入材料能够证明的信息。

---

# 6. 多Record材料处理规则

如果一份Education Wiki中包含多个不同活动或教育工具：

必须首先：

```text
Identify Portfolio
        ↓
Identify Independent Records
        ↓
Assign Record IDs
        ↓
Extract Evidence for Each Record Separately
```

例如：

```text
Portfolio:
JLU-CP Education

R01:
Middle School Lecture

R02:
Experiment Summer Camp

R03:
Debate Competition

R04:
iGEM Tutor Model

R05:
Social Media
```

禁止将：

```text
R01的参与人数
+
R02的实验形式
+
R03的伦理讨论
+
R04的AI工具
```

直接合并成一个虚构的“综合活动”。

Portfolio层级可以总结不同活动之间的整体联系，但Rubric评分时必须明确评分对象是：

- 单一Record；
- 或完整Portfolio。

---

# 7. Educational Tool处理规则

对于AI Tutor、在线平台、教材库等Educational Tool或Educational Resource：

不强制要求其具备传统活动的：

- Participant Count；
- Duration；
- Number of Sessions；
- Group Interaction。

如果材料没有这些信息，应正常填写：

```text
Not Evidenced
```

而不是因此认定工具设计失败。

评价时应更加关注：

- Education Goal；
- Knowledge Accessibility；
- User Interaction；
- Documentation；
- Reuse；
- Accessibility；
- Sustainability；
- Educational Outcome Evidence。

---

# 8. Schema使用原则

本Schema只负责：

> **从Education材料中提取结构化Evidence。**

在该阶段：

- 不进行Rubric评分；
- 不计算Education Design Score；
- 不计算Evidence Coverage；
- 不与Benchmark案例比较；
- 不生成最终活动排名。

标准工作流程为：

```text
Education Material
        ↓
Identify Portfolio / Records
        ↓
Evidence Extraction
        ↓
Education Profile
        ↓
Rubric Scoring
        ↓
Benchmark Comparison
        ↓
Improvement Suggestions
```

因此，本Schema是：

> **原始Education材料与后续Rubric评分之间的结构化信息层。**