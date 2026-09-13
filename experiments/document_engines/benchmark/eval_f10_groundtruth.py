"""Pokreni F10 evaluaciju nad ground-truth JSON fajlovima."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from quality_gate import evaluate_f10


GT_DIR = Path("H:/parser_studio/tests/fakture_ground_truth")
OUT_DIR = Path("H:/parser_studio/experiments/document_engines/outputs")


def main():
    results = {}
    for gt_file in sorted(GT_DIR.glob("*_ground_truth.json")):
        name = gt_file.stem.replace("_ground_truth", "")
        with open(gt_file, "r", encoding="utf-8") as f:
            gt = json.load(f)
        # Prefer sampled_rows_for_f10 (sa q/p/a), fallback na rows
        rows = gt.get("sampled_rows_for_f10", gt.get("rows", []))
        # Filtriraj samo redove sa numeric q/p/a
        rows = [r for r in rows if r.get("quantity") is not None and r.get("unit_price") is not None and r.get("line_amount") is not None]
        if not rows:
            print(f"{name}: NO F10 ROWS in ground-truth", flush=True)
            continue
        res = evaluate_f10(rows)
        print(f"{name}: {res['verdict']} eligible={res['eligible_rows']} failed={res['failed_rows']} rate={res['failed_rate']} severe={res['severe_mismatches']}", flush=True)
        results[name] = res
        out = OUT_DIR / f"f10_{name.lower()}_evaluation.json"
        out.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path = OUT_DIR / "f10_groundtruth_summary.json"
    summary_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"summary: {summary_path}", flush=True)


if __name__ == "__main__":
    main()
