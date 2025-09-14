import os
import json
import numpy as np

PRODUCTS = [
"Карта для путешествий",
"Премиальная карта",
"Кредитная карта",
"Обмен валют",
"Кредит наличными",
"Депозит Мультивалютный",
"Депозит Сберегательный",
"Депозит Накопительный",
"Инвестиции",
"Золотые слитки",
]

def estimate_benefits(signals):
    benefits = {}
    benefits["Карта для путешествий"] = 0.04 * (signals.get("trips_sum",0) + signals.get("taxi_sum",0))
    avgbal = signals.get("avg_monthly_balance_KZT",0)
    spend = signals.get("monthly_spend",0)
    balance_bonus = 0
    if 1_000_000 <= avgbal <= 6_000_000:
        balance_bonus = 0.01 * spend
    elif avgbal > 6_000_000:
        balance_bonus = 0.02 * spend
    prem = min(100000, 0.02 * spend + balance_bonus)
    if signals.get("status") == "Студент" or avgbal < 200_000:
        prem = 0
    benefits["Премиальная карта"] = prem
    top3 = sum([signals.get("spend_by_category", {}).get(k,0) for k in signals.get("top3_cats",[]) if k])
    benefits["Кредитная карта"] = 0.10 * top3
    fx_count = signals.get("fx_count",0)
    fx_amount = signals.get("fx_amount",0)
    avg_amount = fx_amount / max(1, fx_count)
    benefits["Обмен валют"] = 0.001 * fx_count * avg_amount
    needs_cash = (signals.get("remont_sum",0) + signals.get("mebel_sum",0) + signals.get("cash_out_sum",0))>500_000
    benefits["Кредит наличными"] = 100000 if needs_cash else 0
    spare = signals.get("spare_cash",0)
    benefits["Депозит Мультивалютный"] = spare * 0.1450/12
    benefits["Депозит Сберегательный"] = spare * 0.1650/12
    benefits["Депозит Накопительный"] = spare * 0.1550/12
    benefits["Инвестиции"] = spare * 0.01
    benefits["Золотые слитки"] = spare * 0.005
    return benefits

def percentile_norm(arr):
    arr = np.array(arr, dtype=float)
    if arr.size==0:
        return arr
    ranks = np.argsort(np.argsort(arr))
    if arr.size==1:
        return np.array([1.0])
    return ranks/(arr.size-1)

def compute_scores_and_select(all_signals, debug_dir):
    os.makedirs(debug_dir, exist_ok=True)
    per_product_raw_signal = {p:[] for p in PRODUCTS}
    per_client_benefits = {}
    client_ids = list(all_signals.keys())
    for cid in client_ids:
        s = all_signals[cid]
        b = estimate_benefits(s)
        per_client_benefits[cid] = b
        per_product_raw_signal["Карта для путешествий"].append(s.get("trips_sum",0)+s.get("taxi_sum",0))
        per_product_raw_signal["Премиальная карта"].append(s.get("avg_monthly_balance_KZT",0))
        per_product_raw_signal["Кредитная карта"].append(sum([s.get("spend_by_category",{}).get(k,0) for k in s.get("top3_cats",[])]))
        per_product_raw_signal["Обмен валют"].append(s.get("fx_count",0))
        per_product_raw_signal["Кредит наличными"].append((s.get("remont_sum",0)+s.get("mebel_sum",0)+s.get("cash_out_sum",0)))
        per_product_raw_signal["Депозит Мультивалютный"].append(s.get("spare_cash",0))
        per_product_raw_signal["Депозит Сберегательный"].append(s.get("spare_cash",0))
        per_product_raw_signal["Депозит Накопительный"].append(s.get("spare_cash",0))
        per_product_raw_signal["Инвестиции"].append(s.get("spare_cash",0))
        per_product_raw_signal["Золотые слитки"].append(s.get("spare_cash",0))
    product_norms = {}
    for p, arr in per_product_raw_signal.items():
        product_norms[p] = percentile_norm(np.array(arr))
    results = {}
    for idx, cid in enumerate(client_ids):
        s = all_signals[cid]
        b = per_client_benefits[cid]
        prod_data = {}
        benefits_list = [b[p] for p in PRODUCTS]
        maxb = max(benefits_list) if benefits_list else 0
        minb = min(benefits_list) if benefits_list else 0
        if maxb==minb:
            norm_benefits = [1.0 for _ in benefits_list]
        else:
            norm_benefits = [(x-minb)/(maxb-minb) for x in benefits_list]
        for i,p in enumerate(PRODUCTS):
            raw_signal = per_product_raw_signal[p][idx]
            norm_signal = float(product_norms[p][idx]) if idx < len(product_norms[p]) else 0.0
            norm_benefit = float(norm_benefits[i])
            score = 0.7 * norm_signal + 0.3 * norm_benefit
            prod_data[p] = {
                "raw_signal": raw_signal,
                "norm_signal": norm_signal,
                "benefit": b[p],
                "norm_benefit": norm_benefit,
                "score": score,
            }
        sorted_products = sorted(prod_data.items(), key=lambda x: x[1]["score"], reverse=True)
        top4 = [p for p,_ in sorted_products[:4]]
        chosen = top4[0]
        out = {
            "client_code": cid,
            "raw_signals": s,
            "product_scores": prod_data,
            "top4": top4,
            "chosen": chosen,
        }
        results[cid] = out
        with open(os.path.join(debug_dir, f"client_{cid}_scores.json"), "w", encoding="utf-8") as f:
            json.dump(out, f, ensure_ascii=False, indent=2)
    return results, per_client_benefits
