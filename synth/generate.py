# -*- coding: utf-8 -*-
"""
단계 2-A: 깨끗한(golden) 가상데이터 생성

    python synth/generate.py --cohort LUNG_CANCER --n 100 --seed 20260907 --out synth/output/clean
    python synth/generate.py --all
"""
import argparse, importlib, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from framework import Ctx, PROFILES, ROOT

SCENARIOS = {"LUNG_CANCER": "lung", "BREAST_CANCER": "breast", "COLORECTAL_CANCER": "colorectal",
             "MASLD": "masld", "DIABETES": "diabetes", "LYMPHOMA": "lymphoma"}


def run(cohort, n, seed, out):
    mod = importlib.import_module(f"scenarios.{SCENARIOS[cohort]}")
    ctx = Ctx(cohort, seed=seed)
    mod.generate(ctx, n)
    counts = ctx.write(os.path.join(out, cohort))
    print(f"[{cohort}] " + ", ".join(f"{t}={c}" for t, c in counts.items()))
    return counts


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort"); ap.add_argument("--all", action="store_true")
    ap.add_argument("--n", type=int, default=100); ap.add_argument("--seed", type=int, default=20260907)
    ap.add_argument("--out", default=os.path.join(ROOT, "synth/output/clean"))
    a = ap.parse_args()
    cohorts = list(SCENARIOS) if a.all else [a.cohort]
    summary = {}
    for i, c in enumerate(cohorts):
        summary[c] = run(c, a.n, a.seed + i, a.out)
    json.dump(summary, open(os.path.join(a.out, "_counts.json"), "w", encoding="utf-8"), indent=1)
