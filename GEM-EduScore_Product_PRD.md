# GEM-EduScore Product Requirements Document (PRD)


Version: V1.0


---

# 1. Product Overview


## Product Name


GEM-EduScore


## Product Type


AI-powered Education Practice Evaluation Platform


## Product Goal


Build a lightweight but functional AI application that can analyze iGEM Education practices and generate:


- Education quality evaluation;
- Evidence analysis;
- Benchmark comparison;
- Improvement recommendations.


The goal of this project is not to build a commercial system.

The goal is to create a demonstrable prototype that shows:

"How LLM can assist Education practice evaluation and optimization."



---

# 2. Background


iGEM teams conduct many Education activities every year.

However, Education documentation has several problems:


1. Different teams describe activities differently.


2. Educational impact is difficult to evaluate.


3. Excellent Education strategies are difficult to reuse.


GEM-EduScore aims to solve these problems by combining:


- Large Language Model;
- Structured Evidence Extraction;
- Rubric Evaluation;
- Benchmark Analysis.



---

# 3. Target Users


Primary users:


## iGEM Teams


They can use the platform to:


- Evaluate Education activities;
- Identify weaknesses;
- Learn from excellent examples;
- Improve future Education design.



Secondary users:


## Education Researchers


They can analyze:


- Education strategies;
- Evaluation methods;
- Educational impact.



---

# 4. Product Core Workflow


The application should implement the following workflow:


Education Material Input

↓

AI Evidence Extraction

↓

Education Quality Evaluation

↓

Benchmark Comparison

↓

Improvement Recommendation

↓

Visual Report



---

# 5. Functional Requirements


# Function 1: Education Material Upload


## Description


Users upload Education materials.


Supported formats:


- Markdown (.md)
- Text (.txt)
- PDF (.pdf) (optional)


Examples:


- iGEM Education Wiki export;
- Activity summary;
- Education report.



## Interface


The homepage should contain:


Upload component:

"Upload Education Material"


Button:

"Start Evaluation"



---

# Function 2: Evidence Extraction


## Purpose


Extract structured information from uploaded materials.



## Extract Fields


The system should identify:


### Education Goal

- Objectives;
- Expected outcomes.



### Target Audience

- Age group;
- Background;
- Community.



### Education Design

- Activity format;
- Teaching methods;
- Interaction.



### Evidence

- Evaluation data;
- Feedback;
- Outcomes.



### Additional Factors

- Accessibility;
- Sustainability;
- Ethics.



## Output


Generate:

Evidence Profile



---

# Function 3: Rubric Evaluation


## Purpose


Evaluate Education practice quality.


The system should evaluate:


## Ten Dimensions


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


- Dimension score;
- Strength;
- Weakness;
- Evidence gap.



---

# Function 4: Benchmark Comparison


## Purpose


Compare uploaded Education practice with benchmark examples.



## Current Benchmark


Use:


HK-United 2024 Education Portfolio


as default benchmark.



## Comparison Output


Generate:


- Similarities;
- Differences;
- Missing elements;
- Improvement opportunities.



---

# Function 5: Improvement Recommendation


## Purpose


Provide actionable suggestions.



Output:


## Short-term Suggestions


Examples:


- Add surveys;
- Improve evidence collection;
- Record feedback.



## Medium-term Suggestions


Examples:


- Build reusable materials;
- Create activity templates.



## Long-term Suggestions


Examples:


- Establish sustainable education system;
- Build education database.



---

# 6. User Interface Requirements


The application should use:

Streamlit


Reason:

- Fast development;
- Suitable for AI prototype;
- Easy demonstration.



---

# Page Design


## Page 1: Home


Display:


Title:


GEM-EduScore


Subtitle:


AI-powered Education Practice Evaluation Platform


Components:


- Upload file area;
- Benchmark selection;
- Start analysis button.



---

## Page 2: Analysis Result


Display:


## Overall Evaluation


Example:


Education Quality Score

85/100



## Dimension Analysis


Show:


D1-D10 evaluation.



Recommended visualization:


- Bar chart;
- Radar chart.



---

## Evidence Analysis


Display:


Strong Evidence:


...

Missing Evidence:


...



---

## Benchmark Comparison


Display:


Current Practice

VS

Benchmark Practice



---

## Improvement Recommendation


Display:


Actionable suggestions.



---

# 7. Technical Requirements


## Programming Language


Python


## Frontend


Streamlit


## AI Backend


LLM API


Compatible with:


- OpenAI API;
- OpenAI-compatible API endpoint.



## Visualization


Recommended:


- Plotly;
- Streamlit charts.



## File Processing


Support:


- Markdown parsing;
- Text extraction;
- PDF extraction (optional).



---

# 8. Recommended Project Structure


Create:


GEM-EduScore-Product/


├── app.py


├── modules/


│
├── extractor.py


├── evaluator.py


├── benchmark.py


├── recommender.py



├── prompts/


│
├── master_prompt.txt


├── evidence_prompt.txt


├── rubric_prompt.txt



├── data/


│
├── benchmark_cases/



├── outputs/


│
├── reports/



├── requirements.txt


└── README.md



---

# 9. Development Priority


The development should follow:


## Phase 1: Basic Demo


Implement:


- Streamlit interface;
- File upload;
- LLM call;
- Text analysis;
- Result display.



Goal:


A working prototype.



---

## Phase 2: Evaluation Enhancement


Add:


- Rubric scoring;
- Dimension visualization;
- Evidence analysis.



---

## Phase 3: Benchmark System


Add:


- Benchmark database;
- Comparison module;
- Gap analysis.



---

## Phase 4: Product Optimization


Add:


- Better UI;
- Report export;
- More benchmark cases.



---

# 10. Development Constraints


Important:


Do NOT over-engineer.


This is a prototype demonstration project.


Avoid:


- Complex backend;
- Database system;
- User authentication;
- Large-scale deployment.



Prioritize:


- Functionality;
- Demonstration effect;
- Clear workflow;
- Good UI.



---

# 11. Expected Final Demo


The final product should allow a user to:


1. Upload an Education document.


2. Click "Start Evaluation".


3. Wait for AI analysis.


4. Receive:


- Education Evaluation Report;
- Dimension scores;
- Benchmark comparison;
- Improvement recommendations.



The final result should look like:


An AI Education Consultant Platform.



---

# 12. Success Criteria


The prototype is considered successful if:


✓ Users can upload Education materials.


✓ AI can analyze the materials.


✓ The system generates structured evaluation results.


✓ Benchmark comparison is demonstrated.


✓ Improvement recommendations are generated.


✓ The interface is visually presentable.



---

# End of PRD