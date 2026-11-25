# AI & ML Skill Tagging Evaluation — Work Sample

An empirical evaluation and error analysis framework assessing the quality and precision of an automated skill-tagging model for job descriptions.

---

## 📌 Executive Summary

This repository evaluates an AI model tasked with extracting skill tags from job descriptions against an official 54-skill canonical taxonomy (`skill-list.csv`). In student job matching, **a wrong tag sends candidates to roles they cannot do, while a missed tag conceals roles they could.**

Across a benchmark of 50 job descriptions:
* **Total Tags Evaluated:** 200 model tags generated against 177 true required skills.
* **Tag Accuracy (Precision):** **76.00%** (152 / 200 correct tags).
* **Skill Miss Rate:** **14.12%** (25 / 177 required skills missed; Recall: **85.88%**).
* **Primary Error Root Causes:** 16 out-of-taxonomy soft skills, 12 company-name hallucinations, and 20 unflagged optional skills.

---

## 📊 Summary Metrics

| Metric | Primary Standard (Core Requirements Only) | Permissive Standard (Bonus Accepted as TP) | Strict Literal Standard (No Alias Mapping) |
| :--- | :---: | :---: | :---: |
| **Total Model Tags** | 200 | 200 | 200 |
| **Correct Tags (TP)** | **152** | **172** | 134 |
| **Wrong Tags (FP)** | **48** | **28** | 66 |
| **Missed Skills (FN)** | **25** | **25** | 43 |
| **Tag Accuracy (Precision)** | **76.00%** | **86.00%** | 67.00% |
| **Skill Miss Rate** | **14.12%** | **14.12%** | 24.29% |
| **Skill Recall (Coverage)** | **85.88%** | **85.88%** | 75.71% |

---

## 📐 Evaluation Framework (The "Check")

1. **What makes a tag Correct (True Positive - TP):**
   * Must correspond to a **mandatory competency** explicitly required in the JD text (e.g., *"We need someone who knows..."*, *"You will use... every day"*, *"Required:"*).
2. **What counts as a Missed Skill (False Negative - FN):**
   * Any mandatory skill stated in the description that the model failed to output.
3. **Handling Nice-to-Have Skills:**
   * Descriptions explicitly isolate optional competencies (e.g. *"is a plus, not a must"*, *"Nice to have:"*, *"Bonus if..."*).
   * **Rule:** Omitting an optional skill is **never an FN** (candidates do not require it). Tagging an optional skill as an unlabelled mandatory tag is classified as **Wrong (FP)** in our primary check because it creates an artificial barrier, falsely filtering out qualified candidates.
4. **Handling Synonyms & Aliases:**
   * Informal abbreviations (`Node`, `JS`, `Excel`, `Postgres`, `ML`, `API`, `Social Media`) and spelling variations (`Financial Modeling`) are mapped to canonical taxonomy keys (`skill-list.csv`) prior to scoring.

---

## 🔍 Failure Analysis: Three Systematic Modes

### 1. Company-Name Hallucination / Semantic Contamination (12 cases)
The model over-indexes on keywords in the company name, injecting domain buzzwords absent from role duties:
* **Orbit *Logistics*:** Injected `SAP` into Content Writing (`JD004`, `JD044`), HR (`JD040`), and Finance (`JD047`).
* **Lumen *Cloud* Systems:** Injected `Kubernetes` into Finance (`JD007`), Frontend Dev (`JD012`), and Marketing (`JD025`).
* **Kosha *Fintech*:** Injected `Blockchain` into ML (`JD018`), HR (`JD030`), and Marketing (`JD035`).
* **Nimbus *AI Labs*:** Injected `Machine Learning` into Marketing (`JD005`) and Data Analyst (`JD041`).

### 2. Taxonomy Boundary Failure & Soft-Skill Bleed (16 cases)
The model extracts conversational buzzwords from closing culture statements (*"Good communication matters in this team"*) or invents behavioral traits outside the 54-skill list:
* `Leadership` injected into 7 roles (`JD003`, `JD011`, `JD015`, `JD025`, `JD026`, `JD030`, `JD040`).
* `Teamwork` (`JD001`, `JD019`, `JD039`), `Communication` (`JD023`, `JD031`), `Problem Solving` (`JD013`, `JD027`, `JD046`), `Time Management` (`JD008`).
* **Impact:** Extraneous soft tags crowded out the model's output budget, directly causing required skills to be missed (e.g., `Git` dropped for `Leadership` in `JD003`; `PostgreSQL` dropped for `Problem Solving` in `JD013`).

### 3. Taxonomy Drift & Normalization Failure (18 cases)
Accurately identified technical skills were emitted in non-canonical formats:
* `Node` $\rightarrow$ `Node.js` (`JD003`, `JD013`, `JD023`, `JD043`)
* `Excel` $\rightarrow$ `Microsoft Excel` (`JD020`, `JD030`, `JD031`, `JD047`, `JD050`)
* `Financial Modeling` $\rightarrow$ `Financial Modelling` (`JD007`, `JD017`, `JD027`, `JD047`)
* `JS` $\rightarrow$ `JavaScript` (`JD022`); `Postgres` $\rightarrow$ `PostgreSQL` (`JD033`); `API` $\rightarrow$ `REST APIs` (`JD023`); `ML` $\rightarrow$ `Machine Learning` (`JD048`).

---

## 💡 Recommended Fix: Constrained Closed-Taxonomy Decoding

1. **Closed-Taxonomy Constraint:** Restrict token generation strictly to the 54 taxonomy terms (via guided decoding / JSON schema validation). Eliminates 100% of out-of-taxonomy soft skills (16 tags) and 100% of abbreviation/spelling drift (18 tags).
2. **Modality Schema:** Extract into explicit structured fields:
   ```json
   {
     "required_skills": ["Python", "SQL"],
     "optional_skills": ["Pandas"]
   }
   ```
3. **Context Isolation:** Strip company name metadata prior to inference to eliminate domain keyword contamination.

---

## 📁 Repository Structure

```text
├── REPORT.pdf                  # Official 1-page executive evaluation report
├── REPORT.md                   # Markdown source of the evaluation report
├── labels.csv                  # Judged labels (jd_id, right, wrong, missing) for all 50 JDs
├── labels_annotated.csv        # Detailed reference sheet with grounding & error explanations
├── evaluate_skills.py          # Standalone reproducible evaluation script
├── job-descriptions-tagged.csv # Input dataset of 50 job descriptions
├── skill-list.csv              # Official 54-skill taxonomy
└── README.md                   # Evaluation framework and repository documentation
```

---

## 🚀 How to Run the Evaluation

To reproduce all counts and regenerate `labels.csv`:

```bash
# Clone the repository
git clone https://github.com/kvmkashyap-stack/InsiderOne-Assessment.git
cd InsiderOne-Assessment

# Run the evaluation script
python evaluate_skills.py
```
