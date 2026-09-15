# -*- coding: utf-8 -*-
"""
단계 2-A: 깨끗한(golden) 가상데이터 생성

    python synth/generate.py --cohort LUNG_CANCER --n 100 --seed 20260907 --out synth/output/clean
    python synth/generate.py --all
    python synth/generate.py --spec v2 --cohort LUNG_CANCER      # v2 저장 테이블로

v1 과 v2 를 나란히 둔다. v2 는 아직 폐암만 옮겨져 있고, 나머지 코호트는 --spec v2 로 부르면
무엇이 아직 없는지 알려준다.
"""
import argparse, importlib, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
from framework import Ctx, PROFILES, ROOT

SCENARIOS = {"LUNG_CANCER": "lung", "BREAST_CANCER": "breast", "COLORECTAL_CANCER": "colorectal",
             "MASLD": "masld", "DIABETES": "diabetes", "LYMPHOMA": "lymphoma"}
SCENARIOS_V2 = {"LUNG_CANCER": "lung_v2", "DIABETES": "diabetes_v2", "MASLD": "masld_v2", "COLORECTAL_CANCER": "colorectal_v2", "LYMPHOMA": "lymphoma_v2", "BREAST_CANCER": "breast_v2"}   # 옮긴 만큼 늘린다


def run(cohort, n, seed, out, spec="v1"):
    if spec == "v2":
        if cohort not in SCENARIOS_V2:
            raise SystemExit(f"{cohort} 는 아직 v2 로 옮기지 않았다. 지금 되는 것: {', '.join(SCENARIOS_V2)}")
        from framework_v2 import CtxV2
        mod = importlib.import_module(f"scenarios.{SCENARIOS_V2[cohort]}")
        ctx = CtxV2(cohort, seed=seed)
        mod.generate(ctx, n)
        counts = ctx.write(os.path.join(out, cohort))
        print(f"[{cohort} · v2] " + ", ".join(f"{t}={c}" for t, c in counts.items() if c))
        return counts
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
    ap.add_argument("--out"); ap.add_argument("--spec", default="v1", choices=["v1", "v2"])
    a = ap.parse_args()
    out = a.out or os.path.join(ROOT, "synth/output/clean" + ("_v2" if a.spec == "v2" else ""))
    cohorts = (list(SCENARIOS_V2) if a.spec == "v2" else list(SCENARIOS)) if a.all else [a.cohort]
    summary = {}
    os.makedirs(out, exist_ok=True)
    for i, c in enumerate(cohorts):
        summary[c] = run(c, a.n, a.seed + i, out, a.spec)
    a.out = out
    json.dump(summary, open(os.path.join(a.out, "_counts.json"), "w", encoding="utf-8"), indent=1)
