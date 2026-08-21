# GEM-EduScore Tool Scope V0.1

## 1. 项目定义

**GEM-EduScore** 是一个面向 iGEM Education 活动的证据驱动型 AI 辅助诊断工具。

工具通过读取教育活动策划案、活动总结或 Education Wiki，利用大语言模型（LLM）提取教育设计相关信息，再依据固定 Rubric 对活动进行结构化评价，并进一步结合往届优秀 Education 案例进行比较，最终输出评分、证据完整度、优势、短板和改进建议。

工具主要回答：

> **“我们的教育活动设计得怎么样？当前材料能够证明什么？与优秀案例相比还缺什么？下一步应该怎么改？”**

它不是 iGEM 官方评分工具，也不用于预测 Best Education 获奖概率。

---

## 2. 目标用户

V0.1 主要面向：

- 正在策划 iGEM Education 活动的团队；
- 已完成活动、正在总结的团队；
- 正在撰写 Education Wiki 的团队成员。

暂不用于：

- 学生个人能力评价；
- 教师绩效评价；
- 普通学校考试评价；
- iGEM 官方奖项预测。

---

## 3. 评价对象

基本评价单位为一个 **Education Portfolio**。

可以是：

- 一场独立活动；
- 一个 Workshop；
- 一个夏令营；
- 一组连续教育活动；
- 一个团队完整 Education 项目。

因此，一场活动也可以看成只有一个 Activity 的 Portfolio。

---

## 4. 支持输入

V0.1 优先支持文字材料：

### Plan Mode

输入：

- 活动策划案；
- 教案；
- 教育活动方案。

用于活动前诊断。

### Review Mode

输入：

- 活动总结；
- 活动报告；
- Education Wiki；
- Word / PDF / Markdown 整理文本。

用于活动后评价。

V0.1 暂不重点处理：

- 视频；
- 录音；
- 大量照片；
- 社交媒体评论；
- 聊天记录。

---

## 5. Plan Mode 与 Review Mode

### Plan Mode

评价：

> **活动设计是否完整。**

例如策划案写：

> “活动结束后计划进行5题后测。”

则只能标记：

`Planned`

不能认为后测已经发生。

主要输出：

- 已设计环节；
- 缺失环节；
- 活动开始前应补充什么；
- 后续应该收集哪些 Evidence。

### Review Mode

评价：

> **实际实施情况 + 当前已有证据。**

如果总结只写：

> “原计划进行后测。”

却没有说明真正实施，

则标记：

`Not Evidenced`

---

## 6. Evidence 状态

统一使用四种状态：

```text
Planned
Implemented
Observed Outcome
Not Evidenced
```

例如：

> “计划设计调查问卷”

属于：

`Planned`

> “活动后回收有效问卷56份”

属于：

`Implemented`

> “后测正确率由61%提高至82%”

属于：

`Observed Outcome`

---

## 7. 核心原则

### Evidence First

所有判断尽量建立在输入材料能够验证的信息上。

### No Evidence → No Claim

材料没有提供的信息不得自行补充。

例如：

> “学生反响很好。”

不能自动推断：

> “进行了正式调查问卷。”

应标记：

`Formal Questionnaire: Not Evidenced`

---

## 8. 输出内容

### 8.1 Education Profile

提取：

- 活动名称；
- 教育对象；
- 人数；
- 时间；
- 活动形式；
- 教育目标；
- 互动方式；
- 评价方法；
- Reuse 材料；
- 伦理与公平设计。

### 8.2 iGEM-aligned Diagnostic

从四个方面辅助诊断：

1. Mutual Learning / Dialogue
2. Documentation / Build Upon
3. Thoughtful Implementation
4. Enable Participation in Synthetic Biology

每项采用 1–6 档。

该结果只能描述为：

> **iGEM-aligned diagnostic**

不得描述为：

> iGEM Official Score

或：

> Best Education 获奖预测。

### 8.3 Education Design Score

输出：

> **0–100分**

用于观察活动不同设计维度的优势和短板。

### 8.4 Evidence Coverage

输出：

> **0–100%**

例如：

```text
Education Design Score: 84/100
Evidence Coverage: 61%
```

表示活动设计较好，但部分结论缺乏充分材料支撑。

### 8.5 Strengths & Gaps

输出主要优势和明显缺失。

### 8.6 Improvement Suggestions

建议必须具体、可执行。

例如：

> “增加5道核心知识前后测，并保存匿名化统计结果。”

而不是：

> “建议加强评估。”

---

## 9. Context Metrics

以下信息提取，但不直接计入核心质量评分：

- 参与人数；
- 覆盖学校；
- 覆盖城市；
- 线上浏览量；
- 活动持续时间；
- 活动预算；
- 举办次数。

原因是：

> **Reach ≠ Education Quality**

例如：

```text
Reach:
Participants = 34

Engagement:
2-day laboratory workshop
```

和：

```text
Reach:
Views = 50,000

Engagement:
90-second video
```

不能简单按照人数比较。

这些指标主要用于活动描述、Benchmark 匹配和可视化。

---

## 10. V0.1 不做的事情

### 不预测获奖概率

不输出：

> “Best Education 获奖概率73%。”

### 不根据人数直接评价教育质量

人数只作为 Context / Reach 指标。

### 不评价学生个人能力

评价对象是 Education Activity / Portfolio。

### 不虚构 Evidence

无证据：

`Not Evidenced`

### 不替代人工和官方评审

GEM-EduScore 是辅助诊断工具，而非官方评委。

---

## 11. 技术路线

```text
活动策划案 / 总结 / Wiki
          ↓
       LLM读取
          ↓
 Evidence Extraction
          ↓
 Education Profile
          ↓
 Rubric Scoring
          ↓
 Benchmark Comparison
          ↓
Strength / Gap / Improvement
          ↓
 Score + Visualization
```

技术核心：

> **LLM + Rubric + Skill + Benchmark**

其中：

- **LLM**：理解文本并提取信息；
- **Rubric**：规定评价规则；
- **Skill**：固定“提取—评分—比较—建议”流程；
- **Benchmark**：提供往届优秀 Education 案例参照。

---

## 12. V0.1 成功标准

第一版只要求：

1. AI能够正确读取 Education 材料；
2. 大部分判断能给出原文证据；
3. 同一材料重复评价时结果基本稳定；
4. 能识别明显优势和明显缺陷；
5. 改进建议具有实际操作价值；
6. 最终结果能够通过评分、表格或雷达图清晰展示。