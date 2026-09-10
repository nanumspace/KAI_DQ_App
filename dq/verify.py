# -*- coding: utf-8 -*-
"""
단계 3-B: 검증 프로그램의 검출 성능 평가

    python dq/verify.py --cohort LUNG_CANCER
    python dq/verify.py --all

clean 실행 결과(오탐 0 확인)와 dirty 실행 결과(fault_manifest 대비 재현율)를 비교해
  dq/reports/verification_<COHORT>.json / .md  와  dq/reports/verification_summary.md 를 만든다.

판정: manifest 의 오류 1건이 '검출' 되려면 expected_rules 중 하나의 규칙이
  (같은 person_id) 또는 (같은 table 의 pk 가 row_key 에 포함) 또는 (테이블 수준 규칙: columns/table_present) 로 findings 에 있어야 한다.
"""
import argparse, io, json, os, sys
from collections import OrderedDict, defaultdict
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COHORTS = ["LUNG_CANCER", "BREAST_CANCER", "COLORECTAL_CANCER", "MASLD", "DIABETES", "LYMPHOMA"]


def verify(cohort):
    rep = os.path.join(ROOT, "dq/reports")
    clean = json.load(open(os.path.join(rep, f"clean_{cohort}/summary.json"), encoding="utf-8"))
    dirty = json.load(open(os.path.join(rep, f"dirty_{cohort}/summary.json"), encoding="utf-8"))
    findings = pd.read_csv(os.path.join(rep, f"dirty_{cohort}/findings.csv"), dtype=str, keep_default_na=False)
    manifest = pd.read_csv(os.path.join(ROOT, f"synth/output/dirty/{cohort}/fault_manifest.csv"), dtype=str, keep_default_na=False)

    by_rule = defaultdict(list)
    for _, f in findings.iterrows():
        by_rule[f["rule_id"]].append(f)
    results = []
    for _, m in manifest.iterrows():
        rules = [r for r in m["expected_rules"].split("|") if r]
        hit = None
        for r in rules:
            for f in by_rule.get(r, []):
                table_level = f["row_key"] == "" and f["person_id"] == ""
                if table_level and f["table"] == m["table"]:
                    hit = r; break
                if m["person_id"] and f["person_id"] == m["person_id"]:
                    hit = r; break
                if m["pk"] and (f["row_key"] == m["pk"] or f["row_key"].endswith(":" + m["pk"]) or (":" not in f["row_key"] and f["row_key"] == m["pk"])):
                    hit = r; break
            if hit: break
        results.append(OrderedDict(fault_id=m["fault_id"], fault_type=m["fault_type"], category=m["category"], table=m["table"],
                                   field=m["field"], expected_rules=m["expected_rules"], detected=bool(hit), detected_by=hit or ""))
    res = pd.DataFrame(results)
    total = len(res); det = int(res["detected"].sum())
    by_type = res.groupby("fault_type").agg(n=("detected", "size"), detected=("detected", "sum")).reset_index()
    by_type["recall"] = (by_type["detected"] / by_type["n"]).round(3)
    by_cat = res.groupby("category").agg(n=("detected", "size"), detected=("detected", "sum")).reset_index()
    by_cat["recall"] = (by_cat["detected"] / by_cat["n"]).round(3)
    expected_rule_set = set(r for rs in manifest["expected_rules"] for r in rs.split("|") if r)
    fired = set(findings["rule_id"])
    collateral = sorted(fired - expected_rule_set)
    out = OrderedDict(
        cohort=cohort,
        clean=dict(rules=clean["rules_total"], violations=clean["violations_total"], failed_rules=clean["rules_failed"], false_positive_rate=0.0 if clean["violations_total"] == 0 else None),
        dirty=dict(rules=dirty["rules_total"], violations=dirty["violations_total"], failed_rules=dirty["rules_failed"]),
        faults_total=total, faults_detected=det, recall=round(det / total, 4) if total else None,
        fault_types=len(by_type), fault_types_fully_detected=int((by_type["recall"] == 1).sum()),
        missed=res[~res["detected"]].to_dict(orient="records"),
        by_type=by_type.to_dict(orient="records"), by_category=by_cat.to_dict(orient="records"),
        collateral_rules=collateral,
    )
    json.dump(out, open(os.path.join(rep, f"verification_{cohort}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    with open(os.path.join(rep, f"verification_{cohort}.md"), "w", encoding="utf-8") as fh:
        fh.write(f"# 검출 성능 검증: {cohort}\n\n")
        fh.write(f"- clean 데이터: 규칙 {clean['rules_total']}개 실행, 위반 {clean['violations_total']}건 (오탐)\n")
        fh.write(f"- dirty 데이터: 주입 오류 {total}건 중 {det}건 검출, 재현율 {out['recall']}\n")
        fh.write(f"- 오류 유형 {len(by_type)}종 중 전부 검출 {out['fault_types_fully_detected']}종\n")
        fh.write(f"- 주입 오류의 부수 효과로 함께 발화한 규칙: {', '.join(collateral) if collateral else '없음'}\n\n")
        fh.write("| 오류 유형 | 분류 | 주입 | 검출 | 재현율 |\n|---|---|---|---|---|\n")
        cat_of = dict(zip(res["fault_type"], res["category"]))
        for _, r in by_type.iterrows():
            fh.write(f"| {r['fault_type']} | {cat_of[r['fault_type']]} | {r['n']} | {r['detected']} | {r['recall']} |\n")
        if out["missed"]:
            fh.write("\n## 미검출\n\n| fault_id | 유형 | 테이블 | 필드 | 기대 규칙 |\n|---|---|---|---|---|\n")
            for m in out["missed"]:
                fh.write(f"| {m['fault_id']} | {m['fault_type']} | {m['table']} | {m['field']} | {m['expected_rules']} |\n")
    print(f"[{cohort}] clean violations={clean['violations_total']}  dirty faults={total} detected={det} recall={out['recall']}  collateral={len(collateral)}")
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort"); ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    outs = [verify(c) for c in (COHORTS if a.all else [a.cohort])]
    if a.all:
        with open(os.path.join(ROOT, "dq/reports/verification_summary.md"), "w", encoding="utf-8") as fh:
            fh.write("# 검증 프로그램 검출 성능 요약 (6개 코호트)\n\n| 코호트 | 규칙 수 | clean 오탐 | 주입 오류 | 검출 | 재현율 | 오류 유형(전부 검출/전체) |\n|---|---|---|---|---|---|---|\n")
            for o in outs:
                fh.write(f"| {o['cohort']} | {o['dirty']['rules']} | {o['clean']['violations']} | {o['faults_total']} | {o['faults_detected']} | {o['recall']} | {o['fault_types_fully_detected']}/{o['fault_types']} |\n")
        json.dump(outs, open(os.path.join(ROOT, "dq/reports/verification_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
