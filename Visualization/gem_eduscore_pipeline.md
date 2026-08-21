# GEM-EduScore Pipeline Overview V0.1


# 1. System Overview


GEM-EduScore is an LLM-based Education Practice Evaluation Framework.

The system integrates:

- Evidence Extraction;
- Rubric Evaluation;
- Benchmark Analysis;
- Improvement Recommendation.


The goal is to transform unstructured Education materials into structured evidence, evaluation results, and optimization suggestions.



---

# 2. Overall Workflow


The complete workflow:


Education Material

↓

Input Structuring

↓

Evidence Extraction

↓

Evidence Profile

↓

Rubric Evaluation

↓

Benchmark Feature Extraction

↓

Comparison Analysis

↓

Improvement Recommendation



---

# 3. Module Description


# Module 1: Education Input


## Purpose


Collect and organize Education materials.


## Input Sources


Examples:


- iGEM Education Wiki;
- Activity reports;
- Education summaries;
- Teaching materials.


## Output


Structured input document.


Example:

JLUCP_input.md



---

# Module 2: Evidence Extraction


## Purpose


Convert unstructured Education descriptions into structured evidence.


## Process


Education Material

↓

LLM-based Evidence Extraction

↓

Evidence Profile



## Extracted Information


Including:


- Education goals;
- Target audience;
- Teaching methods;
- Activity design;
- Interaction;
- Evaluation evidence;
- Accessibility;
- Sustainability;
- Ethics.



## Principle


No Evidence → No Claim



---

# Module 3: Rubric Evaluation


## Purpose


Evaluate Education practices based on extracted evidence.


## Evaluation Dimensions


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



## Output


Generate:


- Education Design Score;
- Evidence Coverage;
- Strength Analysis;
- Evidence Gap Analysis.



---

# Module 4: Benchmark Extraction


## Purpose


Analyze excellent Education practices and extract reusable features.


## Input


Benchmark Education Cases.


## Output


Benchmark Feature Profile.


Examples:


- Successful design patterns;
- Effective teaching strategies;
- Evidence collection methods;
- Reusable resources.



---

# Module 5: Benchmark Comparison


## Purpose


Compare current Education practices with benchmark cases.


## Process


Current Practice

VS

Benchmark Features


↓

Gap Analysis


## Output


Identify:


- Existing strengths;
- Missing elements;
- Improvement opportunities.



---

# Module 6: Improvement Recommendation


## Purpose


Transform analysis results into actionable suggestions.


## Output


Generate:


- Short-term improvements;
- Medium-term strategies;
- Long-term development directions.



---

# 4. Complete System Logic


GEM-EduScore follows:


Input

↓

Understand Education Practice

↓

Extract Evidence

↓

Evaluate Quality

↓

Compare With Excellent Cases

↓

Recommend Improvements



---

# 5. Prototype Demonstration


Current validation case:


Current Practice:

JLU-CP 2025 Education Portfolio


Benchmark:

HK-United 2024 Education Portfolio


The prototype demonstrates:


- Education material structuring;
- Evidence extraction;
- Rubric-based evaluation;
- Benchmark feature analysis;
- Improvement recommendation.



---

# 6. Future Development


Future versions may include:


- Automated data collection;
- Larger benchmark database;
- Visualization dashboard;
- AI Skill deployment;
- Education recommendation system.



---

# Version

V0.1