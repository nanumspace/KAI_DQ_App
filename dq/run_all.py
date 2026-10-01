# -*- coding: utf-8 -*-
"""
전체 파이프라인 실행: 생성(clean) -> 검증(clean) -> 오류 주입(dirty) -> 검증(dirty) -> 검출 성능 평가

    python dq/run_all.py            # 6개 코호트 전부
    python dq/run_all.py --cohort LUNG_CANCER
    python dq/run_all.py --spec v2  # v2 경로(지금은 폐암만 옮겨져 있다)
    python dq/run_all.py --spec v3  # v3(의뢰사 9/30 매뉴얼 + 10/01 검토 결정) 6개 코호트
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
    ap.add_argument("--spec", default="v1", choices=["v1", "v2", "v3"])
    a = ap.parse_args()
    if a.spec == "v2":
        # v2 는 옮긴 코호트만 돈다. 옮기는 대로 generate.py 의 SCENARIOS_V2 가 늘어난다.
        # import 하면 그 모듈이 stdout 을 바꿔 버리므로 코드를 읽기만 한다.
        import ast
        src = ast.parse(open(os.path.join(ROOT, "synth/generate.py"), encoding="utf-8").read())
        v2_cohorts = next(list(ast.literal_eval(n.value)) for n in ast.walk(src)
                          if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SCENARIOS_V2")
        for c in ([a.cohort] if a.cohort else v2_cohorts):
            sh("synth/generate.py", "--spec", "v2", "--cohort", c, "--n", str(a.n))
            sh("dq/engine.py", "--spec", "v2", "--cohort", c, "--data", f"synth/output/clean_v2/{c}", "--out", f"dq/reports/clean_v2_{c}", "--today", a.today)
            sh("synth/inject_faults_v2.py", "--cohort", c)
            sh("dq/engine.py", "--spec", "v2", "--cohort", c, "--data", f"synth/output/dirty_v2/{c}", "--out", f"dq/reports/dirty_v2_{c}", "--today", a.today)
            sh("dq/verify.py", "--spec", "v2", "--cohort", c)
        raise SystemExit(0)
    if a.spec == "v3":
        cohorts = [a.cohort] if a.cohort else COHORTS
        for c in cohorts:
            sh("synth/generate.py", "--spec", "v3", "--cohort", c, "--n", str(a.n), "--seed", str(20260907 + COHORTS.index(c)))
            sh("dq/engine.py", "--spec", "v3", "--cohort", c, "--data", f"synth/output/clean_v3/{c}", "--out", f"dq/reports/clean_v3_{c}", "--today", a.today)
            clean_summary = json.load(open(os.path.join(ROOT, f"dq/reports/clean_v3_{c}/summary.json"), encoding="utf-8"))
            if clean_summary["violations_total"] or clean_summary["rules_error"]:
                raise SystemExit(f"{c}: clean v3 must pass all rules ({clean_summary['violations_total']} violations)")
            sh("synth/inject_faults_v3.py", "--cohort", c)
            sh("dq/engine.py", "--spec", "v3", "--cohort", c, "--data", f"synth/output/dirty_v3/{c}", "--out", f"dq/reports/dirty_v3_{c}", "--today", a.today)
            sh("dq/verify.py", "--spec", "v3", "--cohort", c)
        if not a.cohort:
            sh("dq/verify.py", "--spec", "v3", "--all")
            counts = {}
            for c in COHORTS:
                s = json.load(open(os.path.join(ROOT, f"dq/reports/clean_v3_{c}/summary.json"), encoding="utf-8"))
                counts[c] = s["tables"]
            json.dump(counts, open(os.path.join(ROOT, "synth/output/clean_v3/_counts.json"), "w", encoding="utf-8"), indent=1)
            sh("synth/build_good_samples_v3.py")
            for c in COHORTS:
                sh("dq/engine.py", "--spec", "v3", "--cohort", c, "--data", f"synth/output/good_v3/{c}", "--out", f"dq/reports/good_v3_{c}", "--today", a.today)
                good_summary = json.load(open(os.path.join(ROOT, f"dq/reports/good_v3_{c}/summary.json"), encoding="utf-8"))
                if good_summary["violations_total"] or good_summary["rules_error"]:
                    raise SystemExit(f"{c}: Good Sample must pass all rules ({good_summary['violations_total']} violations)")
            sh("synth/check_samples_v3.py")
            print(open(os.path.join(ROOT, "dq/reports/verification_summary_v3.md"), encoding="utf-8").read())
        raise SystemExit(0)
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
