# -*- coding: utf-8 -*-
"""단계 2-B (v2): v2 저장 데이터에 오류를 심고 정답 목록을 남긴다.

    python synth/inject_faults_v2.py --cohort LUNG_CANCER --k 3

v1(`inject_faults.py`)은 오류를 하나하나 손으로 적었다. v2 는 규칙이 357개라 그렇게 하면
규칙과 오류가 금방 어긋난다. 그래서 **규칙에서 거꾸로 오류를 만든다** — 규칙이 무엇을 금지하는지
읽고 바로 그것을 어기는 값을 넣는다. 규칙을 늘리면 주입도 따라 늘고, 정답(expected_rules)이
어긋날 일이 없다.

의미 규칙은 여러 테이블이 얽혀 있어 이 방식이 통하지 않으므로 몇 개만 손으로 적었다.

출력: synth/output/dirty_v2/<COHORT>/<TABLE>.csv 와 fault_manifest.csv
manifest 한 행이 심은 오류 하나이고, expected_rules 는 그것을 잡아야 하는 규칙이다.
"""
import argparse
import io
import os
import sys

import numpy as np
import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = yaml.safe_load(open(os.path.join(ROOT, "spec/v2/kai_cdm_spec_v2.yaml"), encoding="utf-8"))["tables"]
PROFILES = yaml.safe_load(open(os.path.join(ROOT, "spec/v2/cohort_profiles_v2.yaml"), encoding="utf-8"))["cohorts"]
RULES = yaml.safe_load(open(os.path.join(ROOT, "rules/rules_structural_v2.yaml"), encoding="utf-8"))["rules"]

# 규칙 하나당 몇 행에 심을지, 그리고 검사 종류마다 규칙을 몇 개나 고를지.
# 전부 심으면 데이터가 오류투성이가 되어 '깨끗한 데이터에서 안 울린다'는 성질을 확인할 수 없다.
RULES_PER_CHECK = 4


class InjectorV2:
    def __init__(self, cohort, k=3, seed=777):
        self.cohort, self.k = cohort, k
        self.rng = np.random.default_rng(seed)
        self.tables = list(PROFILES[cohort]["omop_tables"]) + list(PROFILES[cohort]["extension_tables"])
        self.data, self.manifest, self.n = {}, [], 0
        self.dropped_columns = {}
        code_item = pd.read_csv(os.path.join(ROOT, "spec/v2/vocab/CONCEPT_SET_ITEM.csv"), dtype=str, keep_default_na=False)
        self.kind_of = dict(zip(code_item["concept_id"], code_item["code"]))

    def load(self, d):
        for t in self.tables:
            p = os.path.join(d, f"{t}.csv")
            if os.path.exists(p):
                self.data[t] = pd.read_csv(p, dtype=str, keep_default_na=False)
        return self

    # ------------------------------------------------------------- 기록
    def log(self, ftype, category, table, i, field, injected, rule_id, note="", original=None):
        df = self.data[table]
        # 엔진은 복합 PK 를 'a+b+c' 로 이어 붙여 row_key 로 쓴다. 정답도 같은 모양이어야 맞춰진다.
        pk_cols = [c.strip() for c in str(SPEC[table]["pk"]).split("+")]
        have_pk = i is not None and all(c in df.columns for c in pk_cols)
        # 환자를 가리키는 컬럼 이름이 테이블마다 다르다(COHORT 는 subject_id).
        pid_col = next((c for c in ("person_id", "subject_id") if c in df.columns), None)
        self.n += 1
        self.manifest.append(dict(
            fault_id=f"F{self.n:03d}", fault_type=ftype, category=category, table=table,
            pk="+".join(str(df.at[i, c]) for c in pk_cols) if have_pk else "",
            person_id=df.at[i, pid_col] if (i is not None and pid_col) else "",
            field=field,
            original=original if original is not None else (df.at[i, field] if (i is not None and field in df.columns) else ""),
            injected=injected, expected_rules=rule_id, note=note))

    def put(self, ftype, category, table, i, field, value, rule_id, note=""):
        # 값을 먼저 넣고 나서 기록한다. 심는 컬럼이 복합 PK 의 일부이면(예: COHORT.cohort_start_date)
        # 주입 전 PK 로 적어 두면 엔진이 내는 row_key 와 달라져 정답을 맞출 수 없다.
        before = self.data[table].at[i, field] if field in self.data[table].columns else ""
        self.data[table].at[i, field] = value
        self.log(ftype, category, table, i, field, value, rule_id, note, original=before)

    def rows(self, table, mask=None, k=None):
        df = self.data[table]
        idx = df.index if mask is None else df.index[mask]
        if not len(idx):
            return []
        return list(self.rng.choice(idx, size=min(k or self.k, len(idx)), replace=False))

    # ------------------------------------------------- 규칙에서 거꾸로 만들기
    def applicable(self, check):
        out = []
        for r in RULES:
            if r["check"] != check or r["table"] not in self.data:
                continue
            scope = r.get("scope", "all")
            if scope != "all" and self.cohort not in scope:
                continue
            if r["fields"] and not all(f in self.data[r["table"]].columns for f in r["fields"]):
                continue
            if not len(self.data[r["table"]]):
                continue
            out.append(r)
        return out

    def sample_rules(self, check, n=RULES_PER_CHECK):
        rs = self.applicable(check)
        if len(rs) <= n:
            return rs
        pick = self.rng.choice(len(rs), size=n, replace=False)
        return [rs[i] for i in pick]

    def run(self):
        # ---- 필수값을 비운다
        for r in self.sample_rules("not_null"):
            f = r["fields"][0]
            for i in self.rows(r["table"], mask=self.data[r["table"]][f] != ""):
                self.put("REQUIRED_NULL", "Completeness", r["table"], i, f, "", r["id"])

        # ---- 그 행 종류에서만 필수인 값을 비운다
        for r in self.sample_rules("not_null_when"):
            t, f = r["table"], r["fields"][0]
            wc, code = r["params"]["when_column"], r["params"]["when_code"]
            df = self.data[t]
            if wc not in df.columns:
                continue
            mask = (df[f] != "") & df[wc].map(lambda v: self.kind_of.get(v) == code)
            for i in self.rows(t, mask=mask):
                self.put("REQUIRED_NULL_WHEN", "Completeness", t, i, f, "", r["id"], note=f"{code} 행")

        # ---- 코드도 원천값도 없게 만든다
        for r in self.sample_rules("not_null_either"):
            t, cols = r["table"], r["params"]["columns"]
            df = self.data[t]
            cols = [c for c in cols if c in df.columns]
            if not cols:
                continue
            mask = df[cols].ne("").any(axis=1)
            for i in self.rows(t, mask=mask):
                self.log("REQUIRED_EITHER_NULL", "Completeness", t, i, cols[0], "", r["id"])
                for c in cols:
                    df.at[i, c] = ""

        # ---- 타입을 깬다
        for r in self.sample_rules("type"):
            t, f = r["table"], r["fields"][0]
            bad = "2026-13-45" if r["params"]["type"] == "date" else "NOT_A_NUMBER"
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("TYPE_BAD", "Conformance", t, i, f, bad, r["id"])

        # ---- 참조를 끊는다
        for r in self.sample_rules("fk"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("FK_BROKEN", "Conformance", t, i, f, "999999999", r["id"])

        # ---- PK 를 겹치게 한다
        for r in self.sample_rules("pk_unique", n=3):
            t = r["table"]
            cols = r["params"].get("columns", r["fields"])
            df = self.data[t]
            if len(df) < 2 or not all(c in df.columns for c in cols):
                continue
            src, dst = self.rows(t, k=2)[:2] if len(self.rows(t, k=2)) == 2 else (None, None)
            if src is None:
                continue
            self.log("PK_DUP", "Conformance", t, dst, "+".join(cols), df.at[src, cols[0]], r["id"])
            for c in cols:
                df.at[dst, c] = df.at[src, c]

        # ---- 값 집합 밖의 concept_id / 코드를 넣는다
        for r in self.sample_rules("concept_set"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("CONCEPT_OUT_OF_SET", "Conformance", t, i, f, "10000099999", r["id"])
        for r in self.sample_rules("concept_code"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("CODE_OUT_OF_SET", "Conformance", t, i, f, "7", r["id"])

        # ---- 미래 날짜
        for r in self.sample_rules("not_future"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("FUTURE_DATE", "Plausibility", t, i, f, "2099-01-01", r["id"])

        # ---- 사건 날짜만 비운다(다른 값은 그대로 두어야 규칙이 걸린다)
        for r in self.sample_rules("group_anchor", n=2):
            t, a = r["table"], r["params"]["anchor"]
            members = [m for m in r["params"]["members"] if m in self.data[t].columns]
            df = self.data[t]
            if a not in df.columns or not members:
                continue
            mask = (df[a] != "") & df[members].ne("").any(axis=1)
            for i in self.rows(t, mask=mask):
                self.put("ANCHOR_MISSING", "Completeness", t, i, a, "", r["id"])

        # ---- 컬럼 자체를 없앤다
        for r in self.sample_rules("columns", n=1):
            t = r["table"]
            df = self.data[t]
            drop = [c for c in df.columns if c not in (str(SPEC[t]["pk"]).split("+")[0].strip(), "person_id")]
            if drop:
                c = drop[len(drop) // 2]
                self.log("COLUMN_MISSING", "Conformance", t, None, c, "(컬럼 삭제)", r["id"])
                self.dropped_columns.setdefault(t, []).append(c)

        self.semantic()
        return self

    # ------------------------------------------------- 의미 규칙용(손으로 적음)
    def semantic(self):
        d = self.data
        if "VISIT_OCCURRENCE" in d:
            for i in self.rows("VISIT_OCCURRENCE"):
                # 같은 날로 두면 규칙(<)에 걸리지 않는다. 하루 앞으로 보낸다.
                start = pd.to_datetime(d["VISIT_OCCURRENCE"].at[i, "visit_start_date"])
                self.put("VISIT_END_BEFORE_START", "Plausibility", "VISIT_OCCURRENCE", i, "visit_end_date",
                         (start - pd.Timedelta(days=1)).date().isoformat(), "SEMV-COM-001",
                         note="종료일을 시작일보다 하루 앞으로")
            # 방문 기간을 그대로 두고 시작일만 출생 전으로 보낸다
            for i in self.rows("VISIT_OCCURRENCE", k=2):
                self.put("VISIT_BEFORE_BIRTH", "Plausibility", "VISIT_OCCURRENCE", i, "visit_start_date",
                         "1890-01-01", "SEMV-COM-002")
        if "DEATH" in d and len(d["DEATH"]) and "MEASUREMENT" in d:
            dead = set(d["DEATH"]["person_id"])
            m = d["MEASUREMENT"]
            mask = m["person_id"].isin(dead)
            for i in self.rows("MEASUREMENT", mask=mask, k=2):
                self.put("EVENT_AFTER_DEATH", "Plausibility", "MEASUREMENT", i, "measurement_date",
                         "2026-08-31", "SEMV-COM-003")
        if "DRUG_EXPOSURE" in d:
            for i in self.rows("DRUG_EXPOSURE"):
                self.put("DAYS_SUPPLY_MISMATCH", "Plausibility", "DRUG_EXPOSURE", i, "days_supply",
                         "99", "SEMV-COM-009")
        if "EPISODE" in d:
            mask = d["EPISODE"]["episode_end_date"] != ""
            for i in self.rows("EPISODE", mask=mask, k=2):
                self.put("EPISODE_END_BEFORE_START", "Plausibility", "EPISODE", i, "episode_end_date",
                         "2000-01-01", "SEMV-EP-001")
        if "PATHOLOGY_REPORT" in d:
            pr = d["PATHOLOGY_REPORT"]
            if "lymph_nodes_examined" in pr.columns:
                mask = pr["lymph_nodes_examined"] != ""
                for i in self.rows("PATHOLOGY_REPORT", mask=mask, k=2):
                    self.put("NODES_POSITIVE_GT_EXAMINED", "Plausibility", "PATHOLOGY_REPORT", i,
                             "lymph_nodes_positive", "999", "SEMV-PA-002")
            mask = pr["specimen_date"] != ""
            for i in self.rows("PATHOLOGY_REPORT", mask=mask, k=2):
                self.put("SPECIMEN_DATE_MISMATCH", "Conformance", "PATHOLOGY_REPORT", i, "specimen_date",
                         "2001-01-01", "SEMV-PA-001")

    # ------------------------------------------------------------- 쓰기
    def write(self, out):
        out = os.path.join(out, self.cohort)
        os.makedirs(out, exist_ok=True)
        for t, df in self.data.items():
            df = df.drop(columns=self.dropped_columns.get(t, []), errors="ignore")
            df.to_csv(os.path.join(out, f"{t}.csv"), index=False, encoding="utf-8")
        pd.DataFrame(self.manifest).to_csv(os.path.join(out, "fault_manifest.csv"), index=False, encoding="utf-8")
        return len(self.manifest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--seed", type=int, default=777)
    ap.add_argument("--clean", default=os.path.join(ROOT, "synth/output/clean_v2"))
    ap.add_argument("--out", default=os.path.join(ROOT, "synth/output/dirty_v2"))
    a = ap.parse_args()
    inj = InjectorV2(a.cohort, k=a.k, seed=a.seed).load(os.path.join(a.clean, a.cohort)).run()
    n = inj.write(a.out)
    print(f"[{a.cohort}] 심은 오류 {n}건 → {os.path.relpath(os.path.join(a.out, a.cohort), ROOT)}")


if __name__ == "__main__":
    main()
