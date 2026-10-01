# -*- coding: utf-8 -*-
"""단계 2-B (v3): v3 clean 데이터에 오류를 심고 정답 목록(manifest)을 남긴다.

    python synth/inject_faults_v3.py --cohort LUNG_CANCER
    python synth/inject_faults_v3.py --all

구조 규칙(rules_structural_v3.yaml)은 **규칙에서 거꾸로** 만든다. 규칙이 무엇을 금지하는지 읽고
바로 그것을 어기는 값을 넣으므로 규칙을 늘려도 주입이 따라 늘고, 정답(expected_rules)이 어긋나지 않는다.
적용 가능한 규칙마다 기본 1행씩 심는다(--k 로 늘림).
의미 규칙(rules_semantic_v3.yaml)은 여러 테이블이 얽혀 있어 손으로 적었다:
  SEM3-COM-001~010, SEM3-SACT-001~006, SEM3-LC-001~004(폐암), SEM3-LY-001·002(림프종) 를 모두 한 번 이상 어긴다.

출력: synth/output/dirty_v3/<COHORT>/<TABLE>.csv 와 fault_manifest.csv
manifest 한 행이 심은 오류 하나이고 expected_rules 는 그것을 잡아야 하는 규칙이다(| 구분, 하나라도 잡으면 검출).
pk / person_id 는 **주입 뒤** 값으로 적는다 — 엔진이 내는 row_key/person_id 와 같은 모양이어야 맞춰진다.
"""
import argparse
import io
import os
import re
import sys

import numpy as np
import pandas as pd
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SPEC = yaml.safe_load(open(os.path.join(ROOT, "spec/v3/kai_cdm_spec_v3.yaml"), encoding="utf-8"))["tables"]
PROFILES = yaml.safe_load(open(os.path.join(ROOT, "spec/v3/cohort_profiles_v3.yaml"), encoding="utf-8"))["cohorts"]
RULES = yaml.safe_load(open(os.path.join(ROOT, "rules/rules_structural_v3.yaml"), encoding="utf-8"))["rules"]
SEM_RULES = yaml.safe_load(open(os.path.join(ROOT, "rules/rules_semantic_v3.yaml"), encoding="utf-8"))["rules"]
CONCEPTS = yaml.safe_load(open(os.path.join(ROOT, "spec/concepts.yaml"), encoding="utf-8"))
COHORTS = list(PROFILES)
# 참조표 하나를 통째로 빼 table_present 규칙을 검증한다. 의미 규칙이 쓰지 않는 테이블이어야 하고,
# 그 테이블의 다른 규칙은 건너뛰어지므로 한 코호트에서만 한다.
DROP_TABLE = ("DIABETES", "DRUG_INGREDIENT_STRUCTURE")
SEM_SQL = "\n".join(r["sql"] for r in SEM_RULES)
L01 = {int(k) for k, v in CONCEPTS["drugs"].items() if v.get("category") in (1, 2, 4, 5)}
L02 = {int(k) for k, v in CONCEPTS["drugs"].items() if v.get("category") == 3}
DLBCL = {"9680/3", "9684/3", "9688/3"}
CAT = {r["id"]: r["category"] for r in SEM_RULES}


def day(s, n):
    return (pd.Timestamp(s) + pd.Timedelta(days=n)).date().isoformat()


class InjectorV3:
    def __init__(self, cohort, k=1, seed=777):
        self.cohort, self.k = cohort, k
        self.rng = np.random.default_rng(seed)
        self.tables = list(PROFILES[cohort]["tables"])
        self.disease = [t for t in self.tables if SPEC[t]["category"] == "disease"][0]
        self.data, self.clean, self.manifest, self.n = {}, {}, [], 0
        self.used = set()          # 이미 오류를 심은 (table, 행). 한 행에 둘을 심으면 서로를 가린다
        self.dropped_columns, self.dropped_tables, self.deleted_rows = {}, set(), {}

    def load(self, d):
        for t in self.tables:
            p = os.path.join(d, f"{t}.csv")
            if os.path.exists(p):
                self.data[t] = pd.read_csv(p, dtype=str, keep_default_na=False)
                self.clean[t] = self.data[t].copy()     # 의미 규칙 오류를 고를 때 찾아보는 용도(이미 깨진 값을 믿지 않는다)
        return self

    def intact(self, table):
        """아직 손대지 않은 행의 원래 값. 다른 행을 가리키는 오류는 가리키는 쪽이 멀쩡해야 규칙에 걸린다."""
        df = self.clean[table]
        return df[[(table, i) not in self.used for i in df.index]]

    # ------------------------------------------------------------- 기록
    def log(self, ftype, category, table, i, field, injected, rules, original="", note=""):
        df = self.data[table]
        pk = SPEC[table]["pk"]
        self.n += 1
        self.manifest.append(dict(
            fault_id=f"F{self.n:03d}", fault_type=ftype, category=category, table=table,
            pk=df.at[i, pk] if (i is not None and pk in df.columns) else "",
            person_id=df.at[i, "person_id"] if (i is not None and "person_id" in df.columns) else "",
            field=field, original=original, injected=injected,
            expected_rules="|".join(r for r in rules if r), note=note))

    def put(self, ftype, category, table, i, field, value, rules, note=""):
        before = self.data[table].at[i, field] if field in self.data[table].columns else ""
        self.data[table].at[i, field] = value
        self.log(ftype, category, table, i, field, value, [rules] if isinstance(rules, str) else rules, original=before, note=note)

    def rows(self, table, mask=None, k=None):
        """오류를 심을 행을 고른다. 손대지 않은 행만. 자리가 모자라면 적게 심는다."""
        if table not in self.data:
            return []
        df = self.data[table]
        idx = list(df.index if mask is None else df.index[mask])
        free = [i for i in idx if (table, i) not in self.used]
        if not free:
            return []
        picked = [int(i) for i in self.rng.choice(free, size=min(k or self.k, len(free)), replace=False)]
        for i in picked:
            self.used.add((table, i))
        return picked

    # ------------------------------------------------- 구조 규칙: 규칙에서 거꾸로
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
            if (self.cohort, r["table"]) == DROP_TABLE and r["check"] != "table_present":
                continue            # 파일째 없앨 테이블이라 다른 오류를 심어도 검사되지 않는다
            if r["check"] == "fk" and r["params"]["ref_table"] not in self.tables:
                continue
            if not len(self.data[r["table"]]):
                continue
            out.append(r)
        return out

    def structural(self):
        pkcol = lambda t: SPEC[t]["pk"]
        for r in self.applicable("not_null"):
            t, f = r["table"], r["fields"][0]
            if f == pkcol(t):
                continue            # PK 비우기는 아래 pk_unique 에서 따로 한다
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("REQUIRED_NULL", "Completeness", t, i, f, "", r["id"])
        for r in self.applicable("type"):
            t, f = r["table"], r["fields"][0]
            ty = r["params"]["type"]
            bad = {"date": "2026-13-45", "timestamp": "2026-13-45 99:99:99"}.get(ty, "NOT_A_NUMBER")
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("TYPE_BAD", "Conformance", t, i, f, bad, r["id"])
        for r in self.applicable("fk"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("FK_BROKEN", "Conformance", t, i, f, "999999999", r["id"])
        for r in self.applicable("pk_unique"):
            t = r["table"]
            cols = r["params"].get("columns", r["fields"])
            df = self.data[t]
            if len(df) < 3:
                continue
            picked = self.rows(t, k=3)
            if len(picked) < 3:
                continue
            src, dst, blank = picked
            for c in cols:
                df.at[dst, c] = df.at[src, c]
            self.log("PK_DUP", "Conformance", t, dst, "+".join(cols), df.at[src, cols[0]], [r["id"]])
            # PK 를 비운다 (PK NULL)
            before = df.at[blank, cols[0]]
            for c in cols:
                df.at[blank, c] = ""
            self.log("PK_NULL", "Completeness", t, blank, "+".join(cols), "", [r["id"]], original=before)
        for r in self.applicable("codelist"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("CODELIST", "Conformance", t, i, f, "9999999", r["id"])
        for r in self.applicable("range"):
            t, f = r["table"], r["fields"][0]
            hi = r["params"]["max"]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("RANGE", "Plausibility", t, i, f, str(int(abs(hi) * 10 + 1000)), r["id"])
        for r in self.applicable("pattern"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("PATTERN", "Conformance", t, i, f, "BAD-CODE", r["id"])
        for r in self.applicable("not_future"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t, mask=self.data[t][f] != ""):
                self.put("FUTURE_DATE", "Plausibility", t, i, f, "2099-01-01", r["id"])
        for r in self.applicable("must_be_null"):
            t, f = r["table"], r["fields"][0]
            for i in self.rows(t):
                self.put("MUST_BE_NULL", "Conformance", t, i, f, "12345", r["id"])

    def structure(self):
        """컬럼/테이블을 통째로 없앤다. 맨 마지막에 하고, 다른 오류·의미 규칙이 쓰지 않는 것만 고른다."""
        used_cols = {(m["table"], m["field"]) for m in self.manifest}
        for m in self.manifest:
            if "+" in m["field"]:
                used_cols |= {(m["table"], c) for c in m["field"].split("+")}
        rules = self.applicable("columns")
        rng_order = list(self.rng.permutation(len(rules)))
        done = 0
        for ix in rng_order:
            r = rules[ix]
            t = r["table"]
            if (self.cohort, t) == DROP_TABLE:
                continue
            df = self.data[t]
            keep = {SPEC[t]["pk"], "person_id"}
            cand = [c for c in df.columns if c not in keep and (t, c) not in used_cols
                    and not re.search(rf"\b{re.escape(c)}\b", SEM_SQL)]
            if not cand:
                continue
            c = cand[len(cand) // 2]
            self.log("COLUMN_MISSING", "Conformance", t, None, c, "(컬럼 삭제)", [r["id"]])
            self.dropped_columns.setdefault(t, []).append(c)
            done += 1
            if done >= 2:
                break
        if self.cohort == DROP_TABLE[0] and DROP_TABLE[1] in self.data:
            t = DROP_TABLE[1]
            rid = next(r["id"] for r in RULES if r["table"] == t and r["check"] == "table_present")
            self.log("TABLE_MISSING", "Completeness", t, None, "", "(테이블 삭제)", [rid])
            self.dropped_tables.add(t)

    # ------------------------------------------------- 의미 규칙(손으로 적음)
    def semantic(self):
        d = self.data
        V, P, M, DR = d["VISIT_OCCURRENCE"], d["PERSON"], d["MEASUREMENT"], d["DRUG_EXPOSURE"]
        dis = d[self.disease]
        pids = list(self.clean["PERSON"]["person_id"])

        def other_person(pid):
            return next(x for x in pids if x != pid)

        # COM-001 방문 종료일이 시작일보다 앞
        for i in self.rows("VISIT_OCCURRENCE", mask=V["visit_start_date"] != "", k=2):
            self.put("VISIT_END_BEFORE_START", "Plausibility", "VISIT_OCCURRENCE", i, "visit_end_date",
                     day(V.at[i, "visit_start_date"], -1), "SEM3-COM-001", note="종료일을 시작일보다 하루 앞으로")
        # COM-002 출생연도 이전 방문
        for i in self.rows("VISIT_OCCURRENCE", mask=V["visit_start_date"] != ""):
            self.put("VISIT_BEFORE_BIRTH", "Plausibility", "VISIT_OCCURRENCE", i, "visit_start_date", "1890-01-01", "SEM3-COM-002")
        # COM-003 사망 이후 이벤트: 사망일을 환자의 첫 방문 전으로 당긴다
        cV = self.clean["VISIT_OCCURRENCE"]
        vstart = cV[cV["visit_start_date"] != ""].groupby("person_id")["visit_start_date"].min()
        for i in self.rows("PERSON", mask=(P["death_date"] == "") & P["person_id"].isin(vstart.index)):
            self.put("EVENT_AFTER_DEATH", "Plausibility", "PERSON", i, "death_date", day(vstart[P.at[i, "person_id"]], -5), "SEM3-COM-003")
        # COM-010 이상사례 발생일이 사망일 이후
        A = self.clean["ADVERSE_EVENT"]
        ae_first = A[A["adverse_event_start_date"] != ""].groupby("person_id")["adverse_event_start_date"].min()
        for i in self.rows("PERSON", mask=(P["death_date"] == "") & P["person_id"].isin(ae_first.index)):
            self.put("AE_AFTER_DEATH", "Plausibility", "PERSON", i, "death_date", day(ae_first[P.at[i, "person_id"]], -1),
                     ["SEM3-COM-010", "SEM3-COM-003"])
        # COM-004 이벤트-방문 환자 불일치
        good_visits = set(self.intact("VISIT_OCCURRENCE")["visit_occurrence_id"])
        for i in self.rows("MEASUREMENT", mask=M["visit_occurrence_id"].isin(good_visits), k=2):
            self.put("EVENT_VISIT_PERSON_MISMATCH", "Conformance", "MEASUREMENT", i, "person_id", other_person(M.at[i, "person_id"]), "SEM3-COM-004")
        # COM-005 약물 기간 / days_supply
        for i in self.rows("DRUG_EXPOSURE", mask=DR["days_supply"] != "", k=2):
            self.put("DAYS_SUPPLY_MISMATCH", "Plausibility", "DRUG_EXPOSURE", i, "days_supply", "99", "SEM3-COM-005")
        for i in self.rows("DRUG_EXPOSURE", mask=DR["drug_exposure_start_date"] != ""):
            self.put("DRUG_END_BEFORE_START", "Plausibility", "DRUG_EXPOSURE", i, "drug_exposure_end_date",
                     day(DR.at[i, "drug_exposure_start_date"], -3), "SEM3-COM-005")
        # COM-006 투여 빈도/간격 조건부 필수
        for i in self.rows("DRUG_EXPOSURE", mask=DR["frequency_per_day"] != ""):
            self.put("FREQ_WITHOUT_DAYS_SUPPLY", "Completeness", "DRUG_EXPOSURE", i, "days_supply", "", "SEM3-COM-006")
        interval = pd.to_numeric(DR["dosing_interval_day"].replace("", None), errors="coerce")
        for i in self.rows("DRUG_EXPOSURE", mask=(interval > 1) & (DR["dosing_number"] != "")):
            self.put("INTERVAL_WITHOUT_NUMBER", "Completeness", "DRUG_EXPOSURE", i, "dosing_number", "", "SEM3-COM-006")
        # COM-007 정상범위 하한 > 상한
        for i in self.rows("MEASUREMENT", mask=(M["range_low"] != "") & (M["range_high"] != ""), k=2):
            self.put("RANGE_LOW_GT_HIGH", "Plausibility", "MEASUREMENT", i, "range_low", str(float(M.at[i, "range_high"]) + 100), "SEM3-COM-007")
        # COM-009 특화 테이블 방문의 환자 불일치
        for i in self.rows(self.disease, mask=dis["visit_occurrence_id"] != ""):
            pid = dis.at[i, "person_id"]
            iv = self.intact("VISIT_OCCURRENCE")
            other = iv[iv["person_id"] != pid]
            self.put("DISEASE_VISIT_PERSON_MISMATCH", "Conformance", self.disease, i, "visit_occurrence_id",
                     other["visit_occurrence_id"].iloc[int(self.rng.integers(len(other)))], "SEM3-COM-009")

        if "SACT" in d:
            S = d["SACT"]
            # SACT-001 종료일 < 시작일, line 번호 불일치
            for i in self.rows("SACT", mask=S["regimen_start_date"] != ""):
                self.put("SACT_END_BEFORE_START", "Plausibility", "SACT", i, "regimen_end_date", day(S.at[i, "regimen_start_date"], -1), "SEM3-SACT-001")
            for i in self.rows("SACT", mask=S["line_of_therapy"] != ""):
                self.put("SACT_LINE_MISMATCH", "Plausibility", "SACT", i, "line_of_therapy", "9", "SEM3-SACT-001")
            # SACT-002 시작일이 연결 약물 최소 시작일과 다름 (1차 요법을 앞으로 당기면 line 순서는 그대로)
            for i in self.rows("SACT", mask=S["line_of_therapy"] == "1"):
                self.put("SACT_START_NE_DRUG_MIN", "Plausibility", "SACT", i, "regimen_start_date", day(S.at[i, "regimen_start_date"], -3), "SEM3-SACT-002")
            # SACT-003 진행일 < 시작일
            for i in self.rows("SACT", mask=S["regimen_start_date"] != ""):
                self.put("PROGRESSION_BEFORE_START", "Plausibility", "SACT", i, "date_of_progression", day(S.at[i, "regimen_start_date"], -10), "SEM3-SACT-003")
            # SACT-004 약물-요법 환자 불일치
            sact_person = dict(zip(*[self.intact("SACT")[c] for c in ("sact_id", "person_id")]))
            for i in self.rows("DRUG_EXPOSURE", mask=DR["sact_id"].isin(sact_person)):
                pid = DR.at[i, "person_id"]
                other = [s for s, p_ in sact_person.items() if p_ != pid]
                self.put("DRUG_SACT_PERSON_MISMATCH", "Conformance", "DRUG_EXPOSURE", i, "sact_id", other[int(self.rng.integers(len(other)))], "SEM3-SACT-004")
            # SACT-005 항종양제인데 sact_id 없음
            is_l01 = pd.to_numeric(DR["drug_concept_id"], errors="coerce").isin(L01) & (DR["sact_id"] != "")
            for i in self.rows("DRUG_EXPOSURE", mask=is_l01, k=2):
                self.put("L01_WITHOUT_SACT", "Completeness", "DRUG_EXPOSURE", i, "sact_id", "", "SEM3-SACT-005")
            # SACT-006 내분비 치료제 sact_id 없음 (경고)
            is_l02 = pd.to_numeric(DR["drug_concept_id"], errors="coerce").isin(L02) & (DR["sact_id"] != "")
            for i in self.rows("DRUG_EXPOSURE", mask=is_l02):
                self.put("L02_WITHOUT_SACT", "Completeness", "DRUG_EXPOSURE", i, "sact_id", "", "SEM3-SACT-006")

        if self.cohort == "LUNG_CANCER":
            # LC-001 병기가 판수의 병기군이 아님 / 판수 없이 AJCC 병기
            ed = dis["clinical_stage_ajcc_edition"]
            for i in self.rows(self.disease, mask=ed == "8"):
                self.put("STAGE_NOT_IN_EDITION", "Conformance", self.disease, i, "clinical_stage", "IV", "SEM3-LC-001", note="8판에 없는 병기 IV")
            for i in self.rows(self.disease, mask=ed == "7"):
                self.put("STAGE_NOT_IN_EDITION", "Conformance", self.disease, i, "clinical_stage", "IA1", "SEM3-LC-001", note="7판에 없는 병기 IA1")
            for i in self.rows(self.disease, mask=ed != ""):
                self.put("STAGE_WITHOUT_EDITION", "Completeness", self.disease, i, "clinical_stage_ajcc_edition", "", "SEM3-LC-001")
            # LC-002 LD/ED 는 소세포폐암에만, 판수 없이
            for i in self.rows(self.disease, mask=dis["histologic_diagnosis"] == "1"):
                self.put("LDED_NOT_SMALL_CELL", "Conformance", self.disease, i, "clinical_stage", "ED", "SEM3-LC-002", note="선암에 ED")
            for i in self.rows(self.disease, mask=(dis["histologic_diagnosis"] == "4") & dis["clinical_stage"].isin(["LD", "ED"])):
                self.put("LDED_WITH_EDITION", "Conformance", self.disease, i, "clinical_stage_ajcc_edition", "8", "SEM3-LC-002")
            # LC-003 조직형과 ICD-O-3 형태 코드 불일치
            for i in self.rows(self.disease, mask=dis["histologic_diagnosis"] == "1"):
                self.put("HISTOLOGY_CODE_MISMATCH", "Plausibility", self.disease, i, "histology_icdo3_code", "8041/3", "SEM3-LC-003", note="선암에 소세포 코드")
            for i in self.rows(self.disease, mask=dis["histologic_diagnosis"] == "2"):
                self.put("HISTOLOGY_CODE_MISMATCH", "Plausibility", self.disease, i, "histology_icdo3_code", "8140/3", "SEM3-LC-003", note="편평상피에 선암 코드")
            # LC-004 원발 부위가 폐가 아님
            for i in self.rows(self.disease):
                self.put("PRIMARY_SITE_NOT_LUNG", "Plausibility", self.disease, i, "primary_site_icdo3_code", "C50.9", "SEM3-LC-004")
        if self.cohort == "LYMPHOMA":
            # LY-001 DLBCL 인데 cell_of_origin 없음
            for i in self.rows(self.disease, mask=dis["histology_icdo3_code"].isin(DLBCL) & (dis["cell_of_origin"] != ""), k=2):
                self.put("DLBCL_WITHOUT_COO", "Completeness", self.disease, i, "cell_of_origin", "", "SEM3-LY-001")
            # LY-002 DLBCL 이 아닌데 cell_of_origin 있음
            for i in self.rows(self.disease, mask=~dis["histology_icdo3_code"].isin(DLBCL) & (dis["cell_of_origin"] == "")):
                self.put("COO_NOT_DLBCL", "Plausibility", self.disease, i, "cell_of_origin", "GCB", "SEM3-LY-002")

        # COM-008 특화 테이블에 행이 없는 환자 (행을 지운다. 맨 마지막)
        ok_persons = set(self.intact("PERSON")["person_id"])        # PERSON 행이 멀쩡해야 '행 없는 환자'로 보고된다
        for i in self.rows(self.disease, mask=dis["person_id"].isin(ok_persons)):
            pid = dis.at[i, "person_id"]
            self.n += 1
            self.manifest.append(dict(
                fault_id=f"F{self.n:03d}", fault_type="PERSON_WITHOUT_DISEASE_ROW", category="Completeness", table=self.disease,
                pk=pid, person_id=pid, field="person_id", original=pid, injected="(행 삭제)", expected_rules="SEM3-COM-008", note=""))
            self.deleted_rows.setdefault(self.disease, []).append(i)

    def run(self):
        self.structural()
        self.semantic()
        self.structure()
        return self

    # ------------------------------------------------------------- 쓰기
    def write(self, out):
        out = os.path.join(out, self.cohort)
        os.makedirs(out, exist_ok=True)
        for t, df in self.data.items():
            p = os.path.join(out, f"{t}.csv")
            if t in self.dropped_tables:
                if os.path.exists(p):
                    os.remove(p)
                continue
            df = df.drop(index=self.deleted_rows.get(t, []), errors="ignore")
            df = df.drop(columns=self.dropped_columns.get(t, []), errors="ignore")
            df.to_csv(p, index=False, encoding="utf-8")
        pd.DataFrame(self.manifest).to_csv(os.path.join(out, "fault_manifest.csv"), index=False, encoding="utf-8")
        return len(self.manifest)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--k", type=int, default=1, help="규칙마다 심을 행 수")
    ap.add_argument("--seed", type=int, default=777)
    ap.add_argument("--clean", default=os.path.join(ROOT, "synth/output/clean_v3"))
    ap.add_argument("--out", default=os.path.join(ROOT, "synth/output/dirty_v3"))
    a = ap.parse_args()
    for c in (COHORTS if a.all else [a.cohort]):
        inj = InjectorV3(c, k=a.k, seed=a.seed).load(os.path.join(a.clean, c)).run()
        n = inj.write(a.out)
        print(f"[{c}] 심은 오류 {n}건 → {os.path.relpath(os.path.join(a.out, c), ROOT)}")


if __name__ == "__main__":
    main()
