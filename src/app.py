import argparse
import os
from src.utils.io import load_profiles, load_client_files, write_results, write_missing_report
from src.pipeline.preprocess import build_clients_agg
from src.pipeline.features import compute_all_signals
from src.pipeline.scorer import compute_scores_and_select
from src.pipeline.generator import generate_pushes_batch
from src.eval.evaluate import evaluate_results

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--use-ai", choices=["true","false"], default="false")
    parser.add_argument("--debug-dir", default="debug")
    args = parser.parse_args()
    os.makedirs(args.debug_dir, exist_ok=True)
    profiles = load_profiles(os.path.join(args.data_dir, "clients.csv"))
    clients_raw, missing = load_client_files(args.data_dir, profiles)
    write_missing_report(missing, args.debug_dir)
    clients_agg = build_clients_agg(clients_raw, profiles)
    signals = compute_all_signals(clients_agg)
    scores, per_client_product_benefits = compute_scores_and_select(signals, args.debug_dir)
    results = generate_pushes_batch(scores, per_client_product_benefits, profiles, use_ai=(args.use_ai=="true"))
    write_results(results, args.output)
    eval_report = evaluate_results(results, args.debug_dir)
    print("Pipeline finished. Results:", args.output)

if __name__ == "__main__":
    main()
