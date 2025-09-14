import os
import json
import pandas as pd

def score_push_quality(text, name):
    pts = 0
    if name and name in text:
        pts += 2
    if any(c.isdigit() for c in text):
        pts += 1
    l = len(text)
    if 180<=l<=220:
        pts += 2
    if text.lower().count('!')<=1 and not any(ch.isupper() for ch in text if ch.isalpha()):
        pts += 1
    if any(w in text for w in ['Открыть','Оформить','Настроить','Посмотреть']):
        pts += 2
    if '₸' in text and ',' in text:
        pts += 2
    return min(20, pts*2)

def evaluate_results(results, debug_dir):
    os.makedirs(debug_dir, exist_ok=True)
    rows = []
    total = 0
    count = 0
    for cid, r in results.items():
        product = r['product']
        push = r['push']
        name = None
        try:
            debug = json.load(open(os.path.join(debug_dir, f"client_{cid}_scores.json"), encoding='utf-8'))
            name = debug.get('raw_signals',{}).get('name')
        except Exception:
            pass
        push_pts = score_push_quality(push, name)
        rows.append({"client_code": cid, "product": product, "push_points": push_pts})
        total += push_pts
        count += 1
    avg = total/count if count else 0
    summary = {"average_push_quality": avg, "clients_evaluated": count}
    with open(os.path.join(debug_dir, "evaluation_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    pd.DataFrame(rows).to_csv(os.path.join(debug_dir, "evaluation_per_client.csv"), index=False)
    return summary
