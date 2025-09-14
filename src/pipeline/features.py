import numpy as np
from collections import Counter

TRAVEL_CATS = {"Путешествия","Отели","Такси"}

def compute_signals_for_client(client):
    tr = client.get("transactions")
    transfers = client.get("transfers")
    profile = client.get("profile", {})
    signals = {}
    signals["avg_monthly_balance_KZT"] = float(profile.get("avg_monthly_balance_KZT") or 0)
    signals["status"] = profile.get("status")
    signals["name"] = profile.get("name")
    signals["client_code"] = int(profile.get("client_code"))
    signals["month_reference"] = None
    if tr is not None and not tr.empty:
        signals["month_reference"] = tr["date"].max().strftime("%m.%Y")
    cats = Counter()
    if tr is not None and not tr.empty:
        for _, r in tr.iterrows():
            cat = r.get("category")
            amt = float(r.get("amount") or 0)
            cats[cat] += amt
    signals["spend_by_category"] = dict(cats)
    top3 = [k for k,_ in cats.most_common(3)]
    while len(top3)<3:
        top3.append(None)
    signals["top3_cats"] = top3
    trips_sum = sum(v for k,v in cats.items() if k in TRAVEL_CATS)
    trips_count = 0
    taxi_sum = cats.get("Такси", 0)
    if tr is not None and not tr.empty:
        trips_count = tr[tr["category"].isin(list(TRAVEL_CATS))].shape[0]
    signals["trips_sum"] = float(trips_sum)
    signals["trips_count"] = int(trips_count)
    signals["taxi_sum"] = float(taxi_sum)
    signals["restaurant_sum"] = float(cats.get("Кафе и рестораны", 0))
    signals["jewelry_sum"] = float(cats.get("Ювелирные украшения", 0))
    signals["remont_sum"] = float(cats.get("Ремонт дома", 0))
    signals["mebel_sum"] = float(cats.get("Мебель", 0))
    signals["cash_out_sum"] = 0
    if transfers is not None and not transfers.empty:
        dir_lower = transfers["direction"].astype(str).str.lower()
        mask = dir_lower.isin(["out","p2p_out","card_out"])
        if mask.any():
            signals["cash_out_sum"] = float(transfers.loc[mask, "amount"].abs().sum())
    fx_count = 0
    fx_amount = 0
    if transfers is not None and not transfers.empty and "type" in transfers.columns:
        fx = transfers[transfers["type"].str.contains("fx", case=False, na=False)]
        fx_count = fx.shape[0]
        fx_amount = float(fx["amount"].abs().sum())
    signals["fx_count"] = int(fx_count)
    signals["fx_amount"] = float(fx_amount)
    monthly_spend = float(client.get("monthly_spend", 0))
    signals["monthly_spend"] = monthly_spend
    avg_bal = signals["avg_monthly_balance_KZT"]
    spare_cash = max(0.0, avg_bal - monthly_spend)
    signals["spare_cash"] = spare_cash
    invest_in = 0
    if transfers is not None and not transfers.empty and "invest_in" in transfers["type"].values:
        invest_in = transfers[transfers["type"]=="invest_in"].shape[0]
    signals["invest_in_count"] = int(invest_in)
    return signals

def compute_all_signals(clients_agg):
    signals = {}
    for cid, c in clients_agg.items():
        signals[cid] = compute_signals_for_client(c)
    return signals
