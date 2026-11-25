# Work Sample Evaluation: Job Description Skill Tagging Accuracy
**Role:** Agentic AI Engineer Intern | **Target:** Tag Quality & Matching Reliability  
*Submission is strictly anonymized in accordance with evaluation guidelines.*

---

### 1. The Check: Evaluation Framework & Ground Rules
A student matching platform relies on tag fidelity: **a false tag directs students to jobs they cannot perform, while a missed tag conceals viable opportunities.** Ground truth was established by extracting all competencies explicitly specified in the 50 job descriptions and benchmarking them against the official 54-skill taxonomy (`skill-list.csv`).

* **What makes a tag correct (True Positive - TP):** A tag is correct if and only if it represents a **mandatory competency** explicitly required in the JD text (e.g., *"We need someone who knows..."*, *"You will use... every day"*, *"Required:"*).
* **What counts as a missed skill (False Negative - FN):** Any mandatory skill stated in the JD that the model failed to output.
* **Handling Nice-to-Have / Bonus Skills:** The JDs explicitly demarcate optional skills (*"X is a plus, not a must"*, *"Nice to have: X"*, *"Bonus if..."*). Omitting an optional skill is **never an FN**, because candidates do not require it to perform the role. In our primary check, tagging an optional skill as an unlabelled, mandatory tag is classified as **Wrong (False Positive)** because it converts a preference into a hard barrier, misrepresenting role requirements and artificially filtering out qualified students. *(We also report a permissive baseline where optional skills are credited as TP).*
* **Handling Synonyms & Taxonomy Aliases:** The model frequently emitted informal abbreviations (`Node`, `JS`, `Excel`, `Postgres`, `ML`, `API`, `Social Media`) and spelling variations (`Financial Modeling` vs. `Financial Modelling`). In our evaluation, we map unambiguous aliases to their canonical taxonomy counterparts prior to scoring. In production, exact-string joins would cause silent match failures.

---

### 2. The Numbers: Empirical Evaluation Across All 50 JDs
We evaluated the complete corpus of 50 JDs (200 model tags generated against 177 true required skills; 50 optional skills present):

| Metric | Primary Standard (Core Requirements Only) | Permissive Standard (Nice-to-Have Accepted as TP) | Strict Literal Standard (No Alias Normalization) |
| :--- | :---: | :---: | :---: |
| **Total Model Tags** | 200 | 200 | 200 |
| **Correct Tags (TP)** | **152** | **172** | **134** |
| **Wrong Tags (FP)** | **48** | **28** | **66** |
| **Missed Skills (FN)** | **25** | **25** | **43** |
| **Tag Accuracy (Precision)** | **76.00%** (152 / 200) | **86.00%** (172 / 200) | **67.00%** (134 / 200) |
| **Skill Miss Rate** | **14.12%** (25 / 177) | **14.12%** (25 / 177) | **24.29%** (43 / 177) |
| **Skill Recall (Coverage)** | **85.88%** (152 / 177) | **85.88%** (152 / 177) | **75.71%** (134 / 177) |

*Behind the numbers:* The 48 errors in the primary check comprise: **16 out-of-taxonomy soft skills**, **12 company-name hallucinations**, and **20 unlabelled optional skills**.

---

### 3. Failure Analysis: Three Systematic Failure Modes
The model’s errors are not random; they cluster into three distinct architectural failures:

1. **Company-Name Hallucination & Semantic Contamination (12 occurrences):**  
   The model over-indexes on keywords in the company name, injecting domain buzzwords that appear nowhere in the job responsibilities:
   * **Orbit *Logistics*:** Injected `SAP` into Content Writing (`JD004`), HR (`JD040`), Content Writing (`JD044`), and Finance (`JD047`).
   * **Lumen *Cloud* Systems:** Injected `Kubernetes` into Finance (`JD007`), Frontend Dev (`JD012`), and Marketing (`JD025`).
   * **Kosha *Fintech*:** Injected `Blockchain` into ML (`JD018`), HR (`JD030`), and Marketing (`JD035`).
   * **Nimbus *AI Labs*:** Injected `Machine Learning` into Marketing (`JD005`) and Data Analyst (`JD041`).

2. **Taxonomy Boundary Failure & Soft-Skill Bleed (16 occurrences):**  
   The model extracts generic soft skills from closing boilerplate (*"Good communication matters in this team"*) or invents behavioral traits, none of which exist in the 54-skill taxonomy:
   * `Leadership`: Hallucinated in `JD003`, `JD011`, `JD015`, `JD025`, `JD026`, `JD030`, `JD040`.
   * `Teamwork`: Injected in `JD001`, `JD019`, `JD039`.
   * `Communication`: Injected in `JD023`, `JD031`. `Problem Solving`: Injected in `JD013`, `JD027`, `JD046`.  
   * *Critical consequence:* Generating these extraneous tags consumed the model's output capacity, directly causing required skills to be dropped (e.g., `Git` missed for `Leadership` in `JD003`; `PostgreSQL` missed for `Problem Solving` in `JD013`).

3. **Taxonomy Drift & Normalization Failure (18 occurrences):**  
   The model recognizes valid competencies in the text but emits colloquial abbreviations or non-standard spellings instead of official taxonomy keys:
   * `Node` instead of `Node.js` (`JD003`, `JD013`, `JD023`, `JD043`).
   * `Excel` instead of `Microsoft Excel` (`JD020`, `JD030`, `JD031`, `JD047`, `JD050`).
   * `Financial Modeling` (single 'l') instead of `Financial Modelling` (`JD007`, `JD017`, `JD027`, `JD047`).
   * `JS` for `JavaScript` (`JD022`), `Postgres` for `PostgreSQL` (`JD033`), `ML` for `Machine Learning` (`JD048`), `API` for `REST APIs` (`JD023`).

---

### 4. Recommended Fix: Constrained Decoding & Context-Masked Extraction
* **The First Change:** Implement **Constrained Schema Generation with Closed-Taxonomy Decoding** (e.g., Instructor/Pydantic or Outlines/vLLM guided decoding constrained to `skill-list.csv`) paired with **Context Masking & Modality Separation**.
  1. *Closed-Taxonomy Constraint:* Restrict the model's token sampling strictly to the 54 allowed taxonomy entries. This mathematically eliminates 100% of soft-skill leaks (16 tags) and 100% of abbreviation/spelling drift (18 tags).
  2. *Modality Schema:* Prompt the model to extract into explicit structured fields: `{"required_skills": [...], "optional_skills": [...]}`.
  3. *Context Isolation:* Strip company name metadata prior to inference and prompt: *"Extract skills exclusively from candidate responsibility and requirement sentences; ignore boilerplate and metadata."*
* **Why This First:** It is a zero-latency, non-retraining architectural safeguard that simultaneously remedies all three failure patterns at the decoding and prompt level.
* **Verification Plan:** Re-run the pipeline across the same 50 JDs using `evaluate_skills.py`. Success criteria:
  1. **Zero Out-of-Taxonomy Tags:** Non-canonical tags drop from 28 to 0.
  2. **Precision $\ge$ 96%:** False positives reduced strictly to edge-case semantic misattributions.
  3. **Miss Rate $\le$ 5%:** Reclaiming hallucinated tag slots recovers previously displaced required skills.
