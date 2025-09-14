import pandas as pd

def try_parsers(s):
    if pd.isna(s):
        return pd.NaT
    if isinstance(s, pd.Timestamp):
        return s
    if isinstance(s, (int, float)):
        try:
            return pd.to_datetime(s, unit='s')
        except Exception:
            return pd.NaT
    parsers = [
        ("%Y-%m-%d %H:%M:%S", False),
        ("%Y-%m-%dT%H:%M:%S", False),
        ("%Y-%m-%d", False),
        ("%d.%m.%Y %H:%M:%S", True),
        ("%d.%m.%Y", True),
        ("%d/%m/%Y", True),
        ("%Y/%m/%d", False),
    ]
    for fmt, dayfirst in parsers:
        try:
            res = pd.to_datetime(s, format=fmt, dayfirst=dayfirst, errors='coerce')
            if not pd.isna(res):
                return res
        except Exception:
            pass
    try:
        res = pd.to_datetime(s, dayfirst=False, errors='coerce')
        if not pd.isna(res):
            return res
    except Exception:
        pass
    try:
        res = pd.to_datetime(s, dayfirst=True, errors='coerce')
        if not pd.isna(res):
            return res
    except Exception:
        pass
    return pd.NaT

def parse_date_column(series):
    return series.apply(try_parsers)

def build_clients_agg(clients_raw, profiles):
    all_clients = {}
    for _, row in profiles.iterrows():
        cid = int(row["client_code"])
        if cid not in clients_raw:
            continue
        tr = clients_raw[cid].get("transactions")
        transfers = clients_raw[cid].get("transfers")
        if tr is not None and "date" in tr.columns:
            tr = tr.copy()
            tr["date"] = parse_date_column(tr["date"])
            tr["amount"] = pd.to_numeric(tr["amount"], errors="coerce").fillna(0)
        if transfers is not None and "date" in transfers.columns:
            transfers = transfers.copy()
            transfers["date"] = parse_date_column(transfers["date"])
            if "amount" in transfers.columns:
                transfers["amount"] = pd.to_numeric(transfers["amount"], errors="coerce").fillna(0)
        agg = {}
        agg["transactions"] = tr
        agg["transfers"] = transfers
        agg["profile"] = row.to_dict()
        agg["monthly_spend"] = 0.0
        if tr is not None and not tr.empty:
            three_month_spend = tr.loc[tr["amount"]>0, "amount"].sum()
            agg["monthly_spend"] = float(three_month_spend) / 3.0
        all_clients[cid] = agg
    return all_clients
