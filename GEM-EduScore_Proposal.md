# GEM-EduScore

## An LLM-based Evaluation Framework for iGEM Education Practices


# 1. Project Background


## 1.1 Current Challenges in iGEM Education Evaluation


iGEM teams conduct various Education activities every year, including:

- Science lectures
- Workshops
- Experimental education
- Public engagement
- Digital education
- Ethics discussions


These activities contribute significantly to science communication and public engagement.

However, current Education documentation still faces several challenges.


## Challenge 1: Difficulty in Comparing Different Education Practices


Different iGEM teams describe Education activities using different formats.

Some teams focus on:

- Number of participants
- Number of activities
- Geographic coverage


while others emphasize:

- Teaching design
- Learning process
- Long-term influence


Because of these differences, it is difficult to objectively compare and analyze different Education practices.


## Challenge 2: Lack of Evidence-based Evaluation


Many Education reports describe:

- What activities were conducted
- Who participated
- What content was delivered


However, they often lack systematic evidence about:

- Whether participants actually learned
- Whether attitudes or understanding changed
- Whether feedback influenced later improvements


Therefore, educational impact is difficult to measure and verify.


## Challenge 3: Difficulty in Reusing Excellent Practices


Many high-quality Education practices are stored in scattered iGEM Wiki pages and reports.

However, it is difficult to automatically identify:

- Effective teaching strategies
- Reusable activity structures
- Common weaknesses
- Improvement directions


Therefore, valuable educational experiences are difficult to share and reuse.


---

# 2. Proposed Solution


GEM-EduScore proposes an AI-assisted Education evaluation framework based on:

- Large Language Models (LLM)
- Evidence Schema
- Rubric-based Evaluation
- Benchmark Analysis


The core idea is:

Do not directly ask AI to score Education activities.

Instead:

First extract structured evidence.

Then evaluate educational quality based on evidence.


The overall workflow is:

Education Material

↓

Evidence Extraction

↓

Structured Evidence Profile

↓

Rubric-based Evaluation

↓

Evaluation Report

↓

Improvement Suggestions


---

# 3. Framework Design


## Module 1: Evidence Extraction


### Purpose

Transform unstructured Education materials into structured evidence.


### Input

The system can process:

- iGEM Education Wiki pages
- Education activity reports
- Project documentation


### Extracted Information

The system extracts:

- Education goals
- Target audience
- Teaching methods
- Activity sequence
- Interaction methods
- Assessment evidence
- Accessibility
- Sustainability
- Ethics and responsibility


### Core Principle

No Evidence → No Claim


The system distinguishes:

- Planned
- Implemented
- Observed Outcome
- Not Evidenced


This prevents unsupported assumptions and improves evaluation reliability.


---

## Module 2: Rubric-based Evaluation


Based on extracted Evidence Profiles, GEM-EduScore evaluates Education practices through ten dimensions.


D1 Goal & Audience Alignment

D2 Education Design Quality

D3 Learning Interaction

D4 Educational Outcome Assessment

D5 Feedback & Iteration

D6 Documentation & Reusability

D7 Participant Empowerment

D8 Accessibility & Inclusivity

D9 Sustainability

D10 Ethics & Responsibility


The evaluation produces:

- Education Design Score
- Evidence Coverage
- Strength Analysis
- Evidence Gap Analysis
- Improvement Suggestions


---

## Module 3: Benchmark Analysis


Future versions will introduce benchmark comparison.

By analyzing excellent iGEM Education practices, the system can identify:

- Common characteristics of high-quality Education activities
- Missing evidence in current activities
- Possible improvement directions


The purpose is not ranking teams.

The purpose is helping teams design better Education practices.


---

# 4. Prototype Demonstration


## Case Study

JLU-CP 2025 Education Portfolio


## Input

Official Education materials from JLU-CP iGEM Wiki.


## Processing Pipeline


JLUCP_input.md

↓

Evidence Extractor

↓

Structured Evidence Profile

↓

Rubric Scorer

↓

Evaluation Report


## Prototype Results


The prototype demonstrates that:


### 1. Education Portfolio Structuring


The system can transform complex Education descriptions into structured Records and Evidence fields.


### 2. Evidence-based Diagnosis


The system can identify:

- Strong educational design
- Missing evaluation evidence
- Weak feedback mechanisms
- Sustainability gaps


### 3. Actionable Improvement Suggestions


The generated report provides practical suggestions for future Education improvement.


---

# 5. Innovation


## 5.1 Evidence-driven Evaluation


Traditional Education evaluation often focuses on:

- Participant numbers
- Activity frequency
- Publicity scale


GEM-EduScore focuses on:

- Educational design
- Learning process
- Evidence quality
- Long-term impact


This provides a more comprehensive evaluation perspective.


---

## 5.2 Separation of Design Quality and Evidence Coverage


A key feature of GEM-EduScore is separating:

Education Design Quality

and

Evidence Coverage


For example:

An activity may have:

High educational design quality

but

Low evidence coverage


This means:

The activity itself may be well designed, but the documentation and evaluation evidence are insufficient.


This distinction helps teams understand whether they need:

- Better activity design

or

- Better evaluation methods


---

## 5.3 Reusable Education Intelligence


By extracting patterns from excellent Education practices, GEM-EduScore can gradually build an Education knowledge base.


Future applications may include:

- Recommended activity structures
- Evaluation templates
- Evidence collection strategies
- Education design suggestions


---

# 6. Current Prototype Status


Completed:

- Tool Scope Design
- Education Evaluation Rubric
- Evidence Schema
- Evidence Extraction Prompt
- Rubric Scoring Prompt
- JLU-CP Education Case Demonstration


Prototype Version:

V0.1


---

# 7. Future Development Roadmap


## Stage 1: Benchmark Database


Collect excellent iGEM Education cases.


Process:

Benchmark Education Case

↓

Evidence Extraction

↓

Rubric Evaluation

↓

Benchmark Feature Library


Purpose:

Identify common patterns of high-quality Education practices.


---

## Stage 2: Automated Comparison


Compare:

Current Education Practice

and

Benchmark Education Practice


Generate:

- Strengths
- Weaknesses
- Improvement Suggestions


---

## Stage 3: Visualization Dashboard


Future visualization functions may include:

- Dimension radar charts
- Evidence coverage charts
- Benchmark comparison graphs


---

## Stage 4: AI Skill Deployment


Package GEM-EduScore into an AI Skill.


Input:

Education Material


Output:

Complete Education Evaluation Report


Workflow:

1. Extract Evidence

2. Apply Rubric

3. Generate Diagnosis

4. Provide Improvement Suggestions


---

# 8. Expected Impact


GEM-EduScore aims to help iGEM teams:

- Design higher-quality Education activities
- Collect stronger educational evidence
- Learn from excellent practices
- Improve educational impact


Ultimately, GEM-EduScore provides a possible pathway toward:

More comparable, evidence-driven, and reusable Education practices in iGEM.