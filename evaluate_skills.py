"""
Evaluation Script for Agentic AI Engineer Intern Work Sample
Prompt: AI and ML: how often are these skill tags right?
Dataset: 50 Job Descriptions (job-descriptions-tagged.csv) & Official Taxonomy (skill-list.csv)
Note: Strictly anonymous submission (no identifying personal info).
"""

import pandas as pd
import re
import os

def load_data(jd_path, skill_path):
    df_jds = pd.read_csv(jd_path)
    df_skills = pd.read_csv(skill_path)
    canonical_skills = set(df_skills['skill'].str.strip())
    return df_jds, canonical_skills

# Canonical Alias Mapping for standard abbreviations / spelling variations
ALIAS_MAP = {
    'Node': 'Node.js',
    'Excel': 'Microsoft Excel',
    'Financial Modeling': 'Financial Modelling',
    'JS': 'JavaScript',
    'Postgres': 'PostgreSQL',
    'ML': 'Machine Learning',
    'API': 'REST APIs',
    'Social Media': 'Social Media Marketing'
}

def extract_ground_truth(desc, canonical_skills):
    """
    Parses a job description to separate required skills from nice-to-have/bonus skills.
    """
    skills_by_len = sorted(list(canonical_skills), key=len, reverse=True)
    sentences = re.split(r'\.\s+(?=[A-Z])', desc)
    sentences = [s.strip().rstrip('.') for s in sentences if s.strip()]
    
    req_s = ""
    bonus_s = ""
    for s in sentences:
        s_lower = s.lower()
        if any(kw in s_lower for kw in ['plus, not a must', 'nice to have', 'bonus if you have used']):
            bonus_s = s
        elif any(kw in s_lower for kw in ['we need someone who knows', 'you will use', 'you must be comfortable with', 'required:']):
            req_s = s
            
    req_skills = []
    temp_req = req_s
    for sk in skills_by_len:
        pat = r'(?<!\w)' + re.escape(sk) + r'(?!\w)'
        if re.search(pat, temp_req, re.IGNORECASE):
            req_skills.append(sk)
            temp_req = re.sub(pat, ' ', temp_req, flags=re.IGNORECASE)
            
    bonus_skills = []
    temp_bonus = bonus_s
    for sk in skills_by_len:
        pat = r'(?<!\w)' + re.escape(sk) + r'(?!\w)'
        if re.search(pat, temp_bonus, re.IGNORECASE):
            bonus_skills.append(sk)
            temp_bonus = re.sub(pat, ' ', temp_bonus, flags=re.IGNORECASE)
            
    return set(req_skills), set(bonus_skills)

def run_evaluation(df_jds, canonical_skills):
    results = []
    
    # Counters for Standard A (Strict Core: Nice-to-have tagged without label is FP)
    counts_a = {'total_tags': 0, 'tp': 0, 'fp': 0, 'fn': 0, 'total_req': 0}
    # Counters for Standard B (Permissive Relevance: Nice-to-have tagged is TP, but omitted is not FN)
    counts_b = {'total_tags': 0, 'tp': 0, 'fp': 0, 'fn': 0, 'total_req': 0}
    
    for _, row in df_jds.iterrows():
        jd_id = row['jd_id']
        desc = row['description']
        raw_tags = str(row['model_tags'])
        model_tags = [t.strip() for t in raw_tags.split(';') if t.strip()]
        
        req_set, bonus_set = extract_ground_truth(desc, canonical_skills)
        counts_a['total_req'] += len(req_set)
        counts_b['total_req'] += len(req_set)
        
        right_a, wrong_a = [], []
        right_b, wrong_b = [], []
        covered_a = set()
        
        for t in model_tags:
            counts_a['total_tags'] += 1
            counts_b['total_tags'] += 1
            canon = ALIAS_MAP.get(t, t)
            
            if canon in req_set:
                right_a.append(t)
                right_b.append(t)
                covered_a.add(canon)
                counts_a['tp'] += 1
                counts_b['tp'] += 1
            elif canon in bonus_set:
                # Under Standard A, tagging optional without distinction is a mismatch risk -> FP
                wrong_a.append(t)
                counts_a['fp'] += 1
                # Under Standard B, tagging optional is relevant -> TP
                right_b.append(t)
                counts_b['tp'] += 1
            else:
                wrong_a.append(t)
                wrong_b.append(t)
                counts_a['fp'] += 1
                counts_b['fp'] += 1
                
        missing_a = sorted(list(req_set - covered_a))
        counts_a['fn'] += len(missing_a)
        counts_b['fn'] += len(missing_a)
        
        results.append({
            'jd_id': jd_id,
            'title': row['title'],
            'company': row['company'],
            'model_tags': "; ".join(model_tags),
            'right': "; ".join(right_a) if right_a else "None",
            'wrong': "; ".join(wrong_a) if wrong_a else "None",
            'missing': "; ".join(missing_a) if missing_a else "None"
        })
        
    return results, counts_a, counts_b

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))
    jd_path = os.path.join(base_dir, "job-descriptions-tagged.csv")
    skill_path = os.path.join(base_dir, "skill-list.csv")
    
    df_jds, canonical_skills = load_data(jd_path, skill_path)
    labels, counts_a, counts_b = run_evaluation(df_jds, canonical_skills)
    
    # Save standard labels CSV
    df_labels = pd.DataFrame(labels)[['jd_id', 'right', 'wrong', 'missing']]
    labels_csv_path = os.path.join(base_dir, "labels.csv")
    df_labels.to_csv(labels_csv_path, index=False)
    print(f"[SUCCESS] Saved {labels_csv_path}")
    
    print("\n==========================================")
    print("EVALUATION METRICS SUMMARY (50 JDs)")
    print("==========================================")
    print(f"Total Model Tags Generated: {counts_a['total_tags']}")
    print(f"Total True Required Skills: {counts_a['total_req']}\n")
    
    prec_a = (counts_a['tp'] / counts_a['total_tags']) * 100
    miss_a = (counts_a['fn'] / counts_a['total_req']) * 100
    rec_a = 100 - miss_a
    
    print("--- Primary Check: Core Requirement Standard (Bonus Tagged = Wrong) ---")
    print(f"  Right Tags (TP)   : {counts_a['tp']} / {counts_a['total_tags']}")
    print(f"  Wrong Tags (FP)   : {counts_a['fp']} / {counts_a['total_tags']}")
    print(f"  Missed Skills (FN): {counts_a['fn']} / {counts_a['total_req']}")
    print(f"  Tag Accuracy (Precision) : {prec_a:.2f}% ({counts_a['tp']}/{counts_a['total_tags']})")
    print(f"  Skill Miss Rate          : {miss_a:.2f}% ({counts_a['fn']}/{counts_a['total_req']})")
    print(f"  Skill Recall (Coverage)  : {rec_a:.2f}% ({counts_a['tp']}/{counts_a['total_req']})\n")
    
    prec_b = (counts_b['tp'] / counts_b['total_tags']) * 100
    miss_b = (counts_b['fn'] / counts_b['total_req']) * 100
    rec_b = 100 - miss_b
    
    print("--- Permissive Standard (Bonus Tagged = Right) ---")
    print(f"  Right Tags (TP)   : {counts_b['tp']} / {counts_b['total_tags']}")
    print(f"  Wrong Tags (FP)   : {counts_b['fp']} / {counts_b['total_tags']}")
    print(f"  Missed Skills (FN): {counts_b['fn']} / {counts_b['total_req']}")
    print(f"  Tag Accuracy (Precision) : {prec_b:.2f}% ({counts_b['tp']}/{counts_b['total_tags']})")
    print(f"  Skill Miss Rate          : {miss_b:.2f}% ({counts_b['fn']}/{counts_b['total_req']})")
    print(f"  Skill Recall (Coverage)  : {rec_b:.2f}%")
    print("==========================================")
