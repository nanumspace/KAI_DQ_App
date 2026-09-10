# -*- coding: utf-8 -*-
"""
전체 파이프라인 실행: 생성(clean) -> 검증(clean) -> 오류 주입(dirty) -> 검증(dirty) -> 검출 성능 평가

    python dq/run_all.py            # 6개 코호트 전부
    python dq/run_all.py --cohort LUNG_CANCER
"""
import argparse, os, subprocess, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COHORTS = ["LUNG_CANCER", "BREAST_CANCER", "COLORECTAL_CANCER", "MASLD", "DIABETES", "LYMPHOMA"]
ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONWARNINGS="ignore")


def sh(*args):
    r = subprocess.run([sys.executable] + list(args), cwd=ROOT, env=ENV, capture_output=True, text=True, encoding="utf-8")
    out = (r.stdout or "").strip()
    if out: print(out)
    if r.returncode != 0:
        print(r.stderr[-2000:]); raise SystemExit(f"failed: {args}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--cohort"); ap.add_argument("--n", type=int, default=100); ap.add_argument("--today", default="2026-09-07")
    a = ap.parse_args()
    cohorts = [a.cohort] if a.cohort else COHORTS
    for i, c in enumerate(cohorts):
        sh("synth/generate.py", "--cohort", c, "--n", str(a.n), "--seed", str(20260907 + COHORTS.index(c)))
        sh("dq/engine.py", "--cohort", c, "--data", f"synth/output/clean/{c}", "--out", f"dq/reports/clean_{c}", "--today", a.today)
        sh("synth/inject_faults.py", "--cohort", c)
        sh("dq/engine.py", "--cohort", c, "--data", f"synth/output/dirty/{c}", "--out", f"dq/reports/dirty_{c}", "--today", a.today)
        sh("dq/verify.py", "--cohort", c)
    if not a.cohort:
        sh("dq/verify.py", "--all")
        counts = {}
        for c in COHORTS:
            s = json.load(open(os.path.join(ROOT, f"dq/reports/clean_{c}/summary.json"), encoding="utf-8"))
            counts[c] = s["tables"]
        json.dump(counts, open(os.path.join(ROOT, "synth/output/clean/_counts.json"), "w", encoding="utf-8"), indent=1)
        print(open(os.path.join(ROOT, "dq/reports/verification_summary.md"), encoding="utf-8").read())
