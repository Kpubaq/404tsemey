import os
import json
import pandas as pd
from typing import Tuple, Dict

def load_profiles(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

def load_client_files(data_dir: str, profiles: pd.DataFrame) -> Tuple[Dict[int, Dict[str, pd.DataFrame]], Dict[int, list]]:
    clients = {}
    missing = {}
    for _, row in profiles.iterrows():
        cid = int(row["client_code"])
        tx_file = os.path.join(data_dir, f"client_{cid}_transactions_3m.csv")
        tr_file = os.path.join(data_dir, f"client_{cid}_transfers_3m.csv")
        clients[cid] = {}
        missing[cid] = []
        if os.path.exists(tx_file):
            clients[cid]["transactions"] = pd.read_csv(tx_file)
        else:
            missing[cid].append(tx_file)
        if os.path.exists(tr_file):
            clients[cid]["transfers"] = pd.read_csv(tr_file)
        else:
            missing[cid].append(tr_file)
        if not clients[cid]:
            del clients[cid]
    missing = {k:v for k,v in missing.items() if v}
    return clients, missing

def write_results(results: Dict[int, dict], path: str):
    rows = []
    for cid, r in results.items():
        rows.append({"client_code": cid, "product": r["product"], "push_notification": r["push"]})
    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)

def write_missing_report(missing: dict, debug_dir: str):
    os.makedirs(debug_dir, exist_ok=True)
    with open(os.path.join(debug_dir, "missing_files.json"), "w", encoding="utf-8") as f:
        json.dump(missing, f, ensure_ascii=False, indent=2)
