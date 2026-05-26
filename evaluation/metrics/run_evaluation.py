#!/usr/bin/env python3
"""
Evaluation runner for the AI Compiler System.
Tracks: success rate, retries, validation failures, repair count, latency, token cost.
"""

import argparse
import json
import sys
import time
from pathlib import Path

import httpx

DATASETS_DIR = Path(__file__).parent.parent / "datasets"
DEFAULT_API = "http://localhost:8000"


def load_dataset(name: str) -> list[str]:
    path = DATASETS_DIR / f"{name}_prompts.json"
    if not path.exists():
        path = DATASETS_DIR / ("normal_prompts.json" if name == "normal" else "edge_case_prompts.json")
    with open(path) as f:
        data = json.load(f)
    return data["prompts"]


def run_evaluation(api_url: str, dataset: str, skip_repair: bool = False) -> dict:
    prompts = load_dataset(dataset)
    results = []
    total_latency = 0.0

    with httpx.Client(timeout=300.0) as client:
        for i, prompt in enumerate(prompts):
            print(f"[{i + 1}/{len(prompts)}] {prompt[:60]}...")
            start = time.perf_counter()
            try:
                resp = client.post(
                    f"{api_url}/api/generate",
                    json={"prompt": prompt, "skip_repair": skip_repair},
                )
                elapsed = (time.perf_counter() - start) * 1000
                total_latency += elapsed
                data = resp.json()
                state = data.get("state", {})
                validation = state.get("validation", {})
                results.append({
                    "prompt": prompt[:100],
                    "success": data.get("success", False),
                    "latency_ms": round(elapsed, 2),
                    "validation_errors": validation.get("error_count", -1),
                    "validation_warnings": validation.get("warning_count", 0),
                    "repair_count": len(state.get("repair_actions", [])),
                    "stages": len(state.get("stages", [])),
                    "api_error": data.get("error"),
                })
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                total_latency += elapsed
                results.append({
                    "prompt": prompt[:100],
                    "success": False,
                    "latency_ms": round(elapsed, 2),
                    "error": str(e),
                })

    success_count = sum(1 for r in results if r.get("success"))
    total_repairs = sum(r.get("repair_count", 0) for r in results)
    total_errors = sum(r.get("validation_errors", 0) for r in results if r.get("validation_errors", 0) > 0)

    summary = {
        "dataset": dataset,
        "total_prompts": len(prompts),
        "success_count": success_count,
        "success_rate": round(success_count / len(prompts) * 100, 2) if prompts else 0,
        "average_latency_ms": round(total_latency / len(prompts), 2) if prompts else 0,
        "total_repairs": total_repairs,
        "total_validation_failures": total_errors,
        "results": results,
    }

    return summary


def main():
    parser = argparse.ArgumentParser(description="Run AI Compiler evaluation")
    parser.add_argument("--api", default=DEFAULT_API, help="Backend API URL")
    parser.add_argument("--dataset", choices=["normal", "edge_cases", "both"], default="both")
    parser.add_argument("--skip-repair", action="store_true")
    parser.add_argument("--output", type=str, help="Save results to JSON file")
    args = parser.parse_args()

    datasets = ["normal", "edge_cases"] if args.dataset == "both" else [args.dataset]
    all_summaries = []

    for ds in datasets:
        print(f"\n=== Evaluating dataset: {ds} ===\n")
        summary = run_evaluation(args.api, ds, args.skip_repair)
        all_summaries.append(summary)
        print(f"\nSuccess rate: {summary['success_rate']}%")
        print(f"Avg latency: {summary['average_latency_ms']}ms")
        print(f"Total repairs: {summary['total_repairs']}")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(all_summaries, f, indent=2)
        print(f"\nResults saved to {args.output}")

    failed = any(s["success_rate"] < 50 for s in all_summaries)
    sys.exit(1 if failed and args.dataset != "edge_cases" else 0)


if __name__ == "__main__":
    main()
