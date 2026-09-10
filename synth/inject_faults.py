# -*- coding: utf-8 -*-
"""
단계 2-B: 오류 주입 (dirty 데이터셋 + 정답 manifest)

    python synth/inject_faults.py --cohort LUNG_CANCER --k 3
    python synth/inject_faults.py --all

clean 디렉터리의 CSV 를 읽어 오류 유형 카탈로그(FAULTS)를 적용하고
  synth/output/dirty/<COHORT>/<TABLE>.csv  와  synth/output/dirty/<COHORT>/fault_manifest.csv 를 쓴다.
manifest 의 각 행: fault_id, fault_type, category, table, pk, person_id, field, original, injected, expected_rules
expected_rules 는 "이 오류를 잡아야 하는 규칙 id" 목록(|구분). 검증(dq/verify.py)은 이 중 하나라도 검출되면 '검출' 로 본다.
"""
import argparse, io, os, sys, json
import numpy as np
import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = yaml.safe_load(open(os.path.join(ROOT, "spec/kai_cdm_spec.yaml"), encoding="utf-8"))["tables"]
PROFILES = yaml.safe_load(open(os.path.join(ROOT, "spec/cohort_profiles.yaml"), encoding="utf-8"))["cohorts"]
RULES_ST = yaml.safe_load(open(os.path.join(ROOT, "rules/rules_structural.yaml"), encoding="utf-8"))["rules"]
CONCEPTS = yaml.safe_load(open(os.path.join(ROOT, "spec/concepts.yaml"), encoding="utf-8"))
CANCER = ["LUNG_CANCER", "BREAST_CANCER", "COLORECTAL_CANCER"]
ANTP_COHORTS = [c for c, v in PROFILES.items() if "ANTP_THERAPY" in v["tables"]]
NON_ANTP = [c for c in PROFILES if c not in ANTP_COHORTS]


def st_rule(table, check, field=None, group_anchor=None):
    for r in RULES_ST:
        if r["table"] != table or r["check"] != check:
            continue
        if field is not None and (not r["fields"] or r["fields"][0] != field) and check not in ("group_anchor",):
            continue
        if check == "group_anchor" and r["params"].get("anchor") != group_anchor:
            continue
        return r["id"]
    return None


class Injector:
    def __init__(self, cohort, k=3, seed=777):
        self.cohort = cohort
        self.k = k
        self.rng = np.random.default_rng(seed)
        self.tables = PROFILES[cohort]["tables"]
        self.disease = [t for t in self.tables if SPEC[t]["category"] == "disease"][0]
        self.dpk = SPEC[self.disease]["pk"]
        self.data = {}
        self.manifest = []
        self.n = 0

    def load(self, d):
        for t in self.tables:
            self.data[t] = pd.read_csv(os.path.join(d, f"{t}.csv"), dtype=str, keep_default_na=False)
        return self

    def pick(self, df, mask=None, k=None):
        k = k or self.k
        idx = df.index if mask is None else df.index[mask]
        if len(idx) == 0:
            return []
        return list(self.rng.choice(idx, size=min(k, len(idx)), replace=False))

    def log(self, ftype, category, table, i, field, injected, rules, df=None, note=""):
        df = self.data[table] if df is None else df
        self.n += 1
        pk = SPEC[table]["pk"]
        self.manifest.append(dict(
            fault_id=f"F{self.n:03d}", fault_type=ftype, category=category, table=table,
            pk=df.at[i, pk] if (i is not None and pk in df.columns) else "", person_id=df.at[i, "person_id"] if (i is not None and "person_id" in df.columns) else "",
            field=field, original=df.at[i, field] if (i is not None and field in df.columns) else "", injected=injected,
            expected_rules="|".join(r for r in rules if r), note=note))

    def set(self, ftype, category, table, i, field, value, rules, note=""):
        self.log(ftype, category, table, i, field, value, rules, note=note)
        self.data[table].at[i, field] = value

    # ------------------------------------------------------------- faults
    def run(self):
        d = self.data; dis = self.disease; D = d[dis]
        # F-01 필수값 NULL
        for i in self.pick(d["PERSON"]):
            self.set("REQUIRED_NULL", "Completeness", "PERSON", i, "gender_concept_id", "", [st_rule("PERSON", "not_null", "gender_concept_id")])
        for i in self.pick(d["VISIT_OCCURRENCE"]):
            self.set("REQUIRED_NULL", "Completeness", "VISIT_OCCURRENCE", i, "visit_start_date", "", [st_rule("VISIT_OCCURRENCE", "not_null", "visit_start_date")])
        # F-02 PK 중복
        m = d["MEASUREMENT"]
        for i in self.pick(m):
            j = self.pick(m, k=1)[0]
            self.set("PK_DUPLICATE", "Conformance", "MEASUREMENT", i, "measurement_id", m.at[j, "measurement_id"], [st_rule("MEASUREMENT", "pk_unique", "measurement_id")])
        # F-03 FK 고아
        for i in self.pick(d["DRUG_EXPOSURE"]):
            self.set("FK_ORPHAN", "Conformance", "DRUG_EXPOSURE", i, "visit_occurrence_id", "999999999", [st_rule("DRUG_EXPOSURE", "fk", "visit_occurrence_id")])
        for i in self.pick(D):
            self.set("FK_ORPHAN", "Conformance", dis, i, "person_id", "888888888", [st_rule(dis, "fk", "person_id")])
        # F-04 타입 오류
        for i in self.pick(d["VISIT_OCCURRENCE"]):
            self.set("TYPE_DATE", "Conformance", "VISIT_OCCURRENCE", i, "visit_start_date", "2024/13/40", [st_rule("VISIT_OCCURRENCE", "type", "visit_start_date")])
        for i in self.pick(d["MEASUREMENT"]):
            self.set("TYPE_NUMBER", "Conformance", "MEASUREMENT", i, "value_as_number", "N/A", [st_rule("MEASUREMENT", "type", "value_as_number")])
        for i in self.pick(d["CONDITION_OCCURRENCE"]):
            self.set("TYPE_DATE", "Conformance", "CONDITION_OCCURRENCE", i, "condition_start_date", "2023-02-30", [st_rule("CONDITION_OCCURRENCE", "type", "condition_start_date")])
        # F-05 코드표 밖 값
        for i in self.pick(d["PERSON"]):
            self.set("CODELIST", "Conformance", "PERSON", i, "gender_concept_id", "9999", [st_rule("PERSON", "codelist", "gender_concept_id")])
        for i in self.pick(d["ADVERSE_EVENT"]):
            self.set("CODELIST", "Conformance", "ADVERSE_EVENT", i, "severity_concept_id", "7", [st_rule("ADVERSE_EVENT", "codelist", "severity_concept_id")])
        cl_fields = [f["name"] for f in SPEC[dis]["fields"] if f.get("codelist") and not f["codelist"].startswith("OMOP")]
        if cl_fields:
            f = cl_fields[0]
            for i in self.pick(D, D[f] != ""):
                self.set("CODELIST", "Conformance", dis, i, f, "99", [st_rule(dis, "codelist", f)])
        # F-06 범위 밖
        rf = [f for f in SPEC[dis]["fields"] if f.get("range") and (D[f["name"]] != "").any()]
        for f in rf[:2]:
            for i in self.pick(D, D[f["name"]] != "", k=2):
                self.set("RANGE", "Plausibility", dis, i, f["name"], str(f["range"][1] * 10 + 1000), [st_rule(dis, "range", f["name"])])
        # F-07 패턴
        pf = [f for f in SPEC[dis]["fields"] if f.get("pattern") and (D[f["name"]] != "").any()]
        for f in pf[:2]:
            for i in self.pick(D, D[f["name"]] != "", k=2):
                self.set("PATTERN", "Conformance", dis, i, f["name"], "Stage 4?", [st_rule(dis, "pattern", f["name"])])
        # F-08 그룹 anchor 누락
        anchors = {}
        for f in SPEC[dis]["fields"]:
            if f.get("anchor"):
                anchors.setdefault(f["anchor"], []).append(f["name"])
        for anchor, members in list(anchors.items())[:6]:
            mask = (D[anchor] != "") & (D[members] != "").any(axis=1)
            for i in self.pick(D, mask, k=1):
                self.set("GROUP_ANCHOR_NULL", "Completeness", dis, i, anchor, "", [st_rule(dis, "group_anchor", group_anchor=anchor)])
        # F-09 환자 불변 필드 불일치
        inv = [f for f in SPEC[dis]["fields"] if f.get("group") == "patient" and f["name"] not in ("antp_id", "file_id") and (D[f["name"]] != "").any()]
        if inv:
            f = inv[0]
            rule = st_rule(dis, "person_invariant")
            for i in self.pick(D, D[f["name"]] != ""):
                old = D.at[i, f["name"]]
                new = ("2" if old != "2" else "1") if f["type"] == "integer" else ("1950-01-01" if f["type"] == "date" else old + "_X")
                self.set("PERSON_INVARIANT", "Plausibility", dis, i, f["name"], new, [rule])
        # F-10 방문 종료일 < 시작일
        for i in self.pick(d["VISIT_OCCURRENCE"]):
            self.set("VISIT_END_BEFORE_START", "Plausibility", "VISIT_OCCURRENCE", i, "visit_end_date", "2000-01-01", ["SEM-COM-001"])
        # F-11 사망 후 이벤트
        dead = d["PERSON"][d["PERSON"]["death_date"] != ""]
        if len(dead):
            for _, prow in dead.head(self.k).iterrows():
                mm = d["MEASUREMENT"]
                cand = mm.index[mm["person_id"] == prow["person_id"]]
                if len(cand):
                    i = cand[0]
                    self.set("EVENT_AFTER_DEATH", "Plausibility", "MEASUREMENT", i, "measurement_date", "2026-08-30", ["SEM-COM-003"])
        # F-12 이벤트-방문 환자 불일치
        pids = list(d["PERSON"]["person_id"])
        for i in self.pick(d["MEASUREMENT"]):
            other = [x for x in pids if x != d["MEASUREMENT"].at[i, "person_id"]][0]
            self.set("VISIT_PERSON_MISMATCH", "Conformance", "MEASUREMENT", i, "person_id", other, ["SEM-COM-005"])
        # F-13 약물 종료 < 시작
        for i in self.pick(d["DRUG_EXPOSURE"]):
            self.set("DRUG_END_BEFORE_START", "Plausibility", "DRUG_EXPOSURE", i, "drug_exposure_end_date", "2001-01-01", ["SEM-COM-007"])
        # F-14 검사값 모두 NULL
        for i in self.pick(d["MEASUREMENT"], d["MEASUREMENT"]["value_as_number"] != ""):
            self.set("MEASUREMENT_NO_VALUE", "Completeness", "MEASUREMENT", i, "value_as_number", "", ["SEM-COM-009"])
        # F-15 age_at_index 불일치
        for i in self.pick(d["PERSON"]):
            self.set("AGE_AT_INDEX_MISMATCH", "Plausibility", "PERSON", i, "age_at_index", str(int(d["PERSON"].at[i, "age_at_index"]) + 15), ["SEM-COM-012"])
        # F-16 AE 가 항암 시작 전
        if "ANTP_THERAPY" in d:
            ae = d["ADVERSE_EVENT"]
            for i in self.pick(ae, ae["antp_id"] != ""):
                self.set("AE_BEFORE_ANTP", "Plausibility", "ADVERSE_EVENT", i, "adverse_event_start_date", "2015-01-01", ["SEM-COM-016"])
        # F-17 비항암 코호트에서 antp_id 존재
        if self.cohort in NON_ANTP:
            for i in self.pick(d["DRUG_EXPOSURE"]):
                self.set("ANTP_IN_NONCANCER", "Conformance", "DRUG_EXPOSURE", i, "antp_id", "1", [st_rule("DRUG_EXPOSURE", "must_be_null", "antp_id")])
        # F-18 line 번호 건너뜀
        if "ANTP_THERAPY" in d:
            a = d["ANTP_THERAPY"]
            for i in self.pick(a, a["regimen_or_line_of_therapy"] == "1"):
                self.set("LINE_GAP", "Plausibility", "ANTP_THERAPY", i, "regimen_or_line_of_therapy", "5", ["SEM-COM-018"])
        # F-19 검사값 타당 범위 밖 (HbA1c 45 등)
        mc = {str(k) for k in CONCEPTS["measurements"]}
        for i in self.pick(d["MEASUREMENT"], d["MEASUREMENT"]["measurement_concept_id"].isin(mc) & (d["MEASUREMENT"]["value_as_number"] != "")):
            self.set("MEASUREMENT_IMPLAUSIBLE", "Plausibility", "MEASUREMENT", i, "value_as_number", "99999", ["SEM-COM-011"])
        # F-20 질환별 계산/논리 규칙
        self.disease_specific()
        # F-23 미래 날짜
        for i in self.pick(d["NOTE"]):
            self.set("FUTURE_DATE", "Plausibility", "NOTE", i, "note_date", "2030-01-01", [st_rule("NOTE", "not_future", "note_date")])
        # F-24 컬럼 구성: 알 수 없는 컬럼 추가 / 컬럼 누락
        d["PERSON"]["extra_col"] = "x"
        self.log("UNKNOWN_COLUMN", "Conformance", "PERSON", None, "extra_col", "x", [st_rule("PERSON", "columns")])
        d["OBSERVATION"] = d["OBSERVATION"].drop(columns=["value_as_string"])
        self.log("MISSING_COLUMN", "Conformance", "OBSERVATION", None, "value_as_string", "(dropped)", [st_rule("OBSERVATION", "columns")])
        # F-25 별칭 컬럼
        d["ADVERSE_EVENT"] = d["ADVERSE_EVENT"].rename(columns={"antp_id": "antp_therapy_id"})
        self.log("ALIAS_COLUMN", "Conformance", "ADVERSE_EVENT", None, "antp_therapy_id", "(renamed)", [st_rule("ADVERSE_EVENT", "columns")])
        # F-26 특화 테이블 death_date 가 PERSON 과 불일치
        alive = set(d["PERSON"]["person_id"][d["PERSON"]["death_date"] == ""])
        for i in self.pick(D, D["person_id"].isin(alive) & (D["death_date"] == "")):
            self.set("DEATH_DATE_MISMATCH", "Conformance", dis, i, "death_date", "2024-01-01", ["SEM-COM-029"])
        # F-27 중복 진단 레코드
        c = d["CONDITION_OCCURRENCE"]
        for i in self.pick(c):
            dup = c.loc[[i]].copy(); dup["condition_occurrence_id"] = str(int(c["condition_occurrence_id"].astype(int).max()) + self.n + 1)
            d["CONDITION_OCCURRENCE"] = pd.concat([d["CONDITION_OCCURRENCE"], dup], ignore_index=True)
            self.log("DUPLICATE_RECORD", "Plausibility", "CONDITION_OCCURRENCE", i, "condition_occurrence_id", dup["condition_occurrence_id"].iloc[0], ["SEM-COM-023"], df=c)
        # F-28 코호트 정의 진단 삭제
        cids = {str(x) for x in CONCEPTS["cohort_definition"][self.cohort]["condition_concept_ids"]}
        c = d["CONDITION_OCCURRENCE"]
        victims = list(c["person_id"][c["condition_concept_id"].isin(cids)].unique()[:2])
        for v in victims:
            mask = (c["person_id"] == v) & c["condition_concept_id"].isin(cids)
            i = c.index[mask][0]
            self.log("COHORT_CONDITION_MISSING", "Completeness", "CONDITION_OCCURRENCE", i, "condition_concept_id", "(rows deleted)", ["SEM-COM-013"], df=c)
            d["CONDITION_OCCURRENCE"] = c = c[~mask]
        # F-29 중대 AE 논리
        ae = d["ADVERSE_EVENT"]
        for i in self.pick(ae, ae["is_serious"] == "1"):
            self.set("SERIOUS_AE_INCOMPLETE", "Completeness", "ADVERSE_EVENT", i, "seriousness_concept_id", "", ["SEM-COM-017"])
        # F-30 투여빈도 있으나 days_supply 없음
        de = d["DRUG_EXPOSURE"]
        for i in self.pick(de, de["frequency_per_day"] != ""):
            self.set("FREQ_WITHOUT_DAYS", "Completeness", "DRUG_EXPOSURE", i, "days_supply", "", ["SEM-COM-008", "SEM-COM-007"])

    def disease_specific(self):
        d = self.data; dis = self.disease; D = d[dis]; c = self.cohort
        if c in CANCER:
            for i in self.pick(D, D["bmi_vl"] != ""):
                self.set("BMI_MISMATCH", "Plausibility", dis, i, "bmi_vl", "19.9" if D.at[i, "bmi_vl"] != "19.9" else "31.1", ["SEM-CA-004"])
            for i in self.pick(D, D["rd_totl_gy"] != "", k=2):
                self.set("RT_DOSE_MISMATCH", "Plausibility", dis, i, "rd_totl_gy", "12.5", ["SEM-CA-003"])
            for i in self.pick(D, D["afop_path_tnm_stag_vl"] != "", k=2):
                self.set("TNM_CONCAT_MISMATCH", "Conformance", dis, i, "afop_path_tnm_stag_vl", "T1N0M1", ["SEM-CA-002"])
            for i in self.pick(D, D["srgc_ptem_ymd"] != "", k=2):
                self.set("PATH_BEFORE_SURGERY", "Plausibility", dis, i, "srgc_ptem_ymd", "2010-01-01", ["SEM-CA-001"])
            if c == "LUNG_CANCER":
                for i in self.pick(D, D["afop_path_t_stag_vl"].str.contains("T1", na=False) & (D["tumr_max_diam_vl"] != ""), k=2):
                    self.set("SIZE_VS_TSTAGE", "Plausibility", dis, i, "tumr_max_diam_vl", "8.5", ["SEM-LC-003"])
                for i in self.pick(D, D["shis_yn_noans_spcd"] == "N", k=2):
                    self.set("SMOKING_LOGIC", "Plausibility", dis, i, "smok_qty", "1.5", ["SEM-LC-002"])
            else:
                for i in self.pick(D, D["totl_ln_cnt"] != "", k=2):
                    self.set("POS_LN_GT_TOTAL", "Plausibility", dis, i, "pstv_ln_cnt", str(int(float(D.at[i, "totl_ln_cnt"])) + 5), ["SEM-CA-007"])
            if c == "BREAST_CANCER":
                for i in self.pick(D, D["menopause_status"] == "1", k=2):
                    self.set("MENOPAUSE_LOGIC", "Plausibility", dis, i, "meno_age_vl", "50", ["SEM-BC-002"])
            if c == "COLORECTAL_CANCER":
                for i in self.pick(D, D["lapr_conv_yn_unid_spcd"] == "Y", k=2):
                    self.set("CONVERSION_REASON_MISSING", "Completeness", dis, i, "lapr_conv_resn_spcd", "", ["SEM-CC-002"])
                for i in self.pick(D, D["impt_read_ymd"] != "", k=2):
                    self.set("READ_BEFORE_EXAM", "Plausibility", dis, i, "impt_read_ymd", "2010-01-01", ["SEM-CA-008"])
        elif c == "MASLD":
            for i in self.pick(D, D["fib4_score"] != ""):
                self.set("FIB4_MISMATCH", "Plausibility", dis, i, "fib4_score", str(round(float(D.at[i, "fib4_score"]) * 3 + 2, 2)), ["SEM-MA-001", "SEM-MA-004"])
            for i in self.pick(D, D["bmi_vl"] != "", k=2):
                self.set("BMI_MISMATCH", "Plausibility", dis, i, "bmi_vl", "19.9" if D.at[i, "bmi_vl"] != "19.9" else "31.1", ["SEM-CA-004"])
            for i in self.pick(D, D["drnk_nt"] != "", k=2):
                self.log("ALCOHOL_ABOVE_THRESHOLD", "Plausibility", dis, i, "drnk_qty", "10", ["SEM-MA-003"])
                D.at[i, "drnk_qty"] = "10"; D.at[i, "drnk_nt"] = "30"
            for i in self.pick(D, D["age"] != "", k=2):
                self.set("SCORE_AGE_MISMATCH", "Plausibility", dis, i, "age", str(int(float(D.at[i, "age"])) + 20), ["SEM-MA-002", "SEM-MA-001"])
        elif c == "DIABETES":
            for i in self.pick(D, D["visit_start_date"] != ""):
                self.set("DM_VISIT_MISMATCH", "Conformance", dis, i, "visit_start_date", "2011-01-01", ["SEM-DM-001"])
            for i in self.pick(D, D["value_as_number"] != ""):
                self.set("DM_MEASUREMENT_MISMATCH", "Conformance", dis, i, "value_as_number", "123.4", ["SEM-DM-002"])
            for i in self.pick(D, D["visit_concept_id"] != "", k=2):
                self.set("DM_VISIT_NOT_OUTPATIENT", "Conformance", dis, i, "visit_concept_id", "9201", ["SEM-DM-004", "SEM-DM-001"])
            for i in self.pick(D, D["drug_concept_id"] != "", k=2):
                self.set("DM_DRUG_MISMATCH", "Conformance", dis, i, "drug_concept_id", "1503297" if D.at[i, "drug_concept_id"] != "1503297" else "1597756", ["SEM-DM-003"])
        elif c == "LYMPHOMA":
            for i in self.pick(D, D["ipi_score"] != ""):
                self.set("IPI_RISK_MISMATCH", "Conformance", dis, i, "ipi_risk_group", "high" if D.at[i, "ipi_risk_group"] != "high" else "low", ["SEM-LY-005"])
            for i in self.pick(D, D["b_symptom_yn"] == "0", k=2):
                self.set("B_SYMPTOM_LOGIC", "Plausibility", dis, i, "stage_suffix", "B", ["SEM-LY-002"])
            for i in self.pick(D, D["vital_status"].str.lower() == "alive", k=2):
                self.set("VITAL_STATUS_LOGIC", "Plausibility", dis, i, "vital_status", "dead", ["SEM-LY-009"])
            for i in self.pick(D, D["treatment_start_date"] != "", k=2):
                self.set("TX_LINE_MISMATCH", "Conformance", dis, i, "current_line_of_therapy", "9", ["SEM-LY-006"])
            for i in self.pick(D, D["deauville_score"].isin(["1", "2", "3"]) & (D["metabolic_response"] == "CMR"), k=2):
                self.set("DEAUVILLE_RESPONSE_MISMATCH", "Plausibility", dis, i, "metabolic_response", "PMD", ["SEM-LY-008"])

    def write(self, out):
        os.makedirs(out, exist_ok=True)
        for t, df in self.data.items():
            df.to_csv(os.path.join(out, f"{t}.csv"), index=False, encoding="utf-8")
        pd.DataFrame(self.manifest).to_csv(os.path.join(out, "fault_manifest.csv"), index=False, encoding="utf-8-sig")
        print(f"[{self.cohort}] faults injected: {len(self.manifest)} ({len(set(m['fault_type'] for m in self.manifest))} types)")
        return len(self.manifest)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort"); ap.add_argument("--all", action="store_true"); ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--clean", default=os.path.join(ROOT, "synth/output/clean")); ap.add_argument("--out", default=os.path.join(ROOT, "synth/output/dirty"))
    a = ap.parse_args()
    for i, c in enumerate(list(PROFILES) if a.all else [a.cohort]):
        inj = Injector(c, k=a.k, seed=777 + i).load(os.path.join(a.clean, c))
        inj.run()
        inj.write(os.path.join(a.out, c))
