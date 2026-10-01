# -*- coding: utf-8 -*-
"""
단계 3: 데이터 품질 검증 엔진 (참조 구현)

사용법:
    python dq/engine.py --cohort LUNG_CANCER --data synth/output/clean/LUNG_CANCER --out dq/reports/clean_LUNG_CANCER
    python dq/engine.py --spec v2 --cohort LUNG_CANCER --data synth/output/clean_v2/LUNG_CANCER --out dq/reports/v2_LUNG_CANCER
    python dq/engine.py --spec v3 --cohort LUNG_CANCER --data synth/output/clean_v3/LUNG_CANCER --out dq/reports/clean_v3_LUNG_CANCER

입력  : 코호트 디렉터리의 <TABLE>.csv (UTF-8, 헤더 포함, NULL 은 빈 문자열)
규칙  : rules/rules_structural.yaml (명세에서 자동 생성) + rules/rules_semantic.yaml (수동 작성, DuckDB SQL)
        --spec v2 면 rules/rules_structural_v2.yaml 을 읽는다. v2 의미 규칙은 아직 없다
        (v1 의미 규칙은 v1 테이블 이름으로 쓴 SQL 이라 v2 에 그대로 걸 수 없다).
출력  : findings.csv (위반 행 단위), summary.json (규칙 단위), report.md (사람용 요약)

구조 규칙은 원본 문자열 위에서 검사하고(타입 오류를 잡기 위해), 의미 규칙은 명세 타입으로 변환한 뒤 DuckDB 에서 SQL 로 검사한다.
"""
import argparse, io, json, os, re, sys, datetime as dt
from collections import OrderedDict, defaultdict
import re
import pandas as pd
import yaml
import duckdb

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?$")
INT_RE = re.compile(r"^[+-]?\d+$")
FLOAT_RE = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def load_yaml(p):
    return yaml.safe_load(open(os.path.join(ROOT, p), encoding="utf-8"))


_MASK_QUOTED = re.compile(r"'[^']*'")
_MASK_EQ = re.compile(r"=\S+")
_MASK_DATE = re.compile(r"\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?")
_MASK_NUM = re.compile(r"(?<![A-Za-z_\d.])\d+(?:\.\d+)?(?![A-Za-z_\d])")


def mask_values(detail):
    """보고서 예시에서 데이터 값을 가린다. dq-ts/src/engine.ts 의 maskValues 와 같아야 한다."""
    s = _MASK_QUOTED.sub("'…'", detail)
    s = _MASK_EQ.sub("=…", s)
    s = _MASK_DATE.sub("…", s)
    return _MASK_NUM.sub("…", s)


V1_PATHS = dict(spec="spec/kai_cdm_spec.yaml", codelists="spec/codelists.yaml", profiles="spec/cohort_profiles.yaml",
                structural="rules/rules_structural.yaml", semantic="rules/rules_semantic.yaml")
V3_PATHS = dict(spec="spec/v3/kai_cdm_spec_v3.yaml", codelists="spec/v3/codelists_v3.yaml",
                profiles="spec/v3/cohort_profiles_v3.yaml", structural="rules/rules_structural_v3.yaml",
                semantic="rules/rules_semantic_v3.yaml")

class Engine:
    def __init__(self, cohort, today=None, max_examples=50, spec="v1"):
        self.cohort = cohort
        self.today = today or dt.date.today()
        self.max_examples = max_examples
        self.spec_version = spec
        if spec == "v2":
            self.spec = load_yaml("spec/v2/kai_cdm_spec_v2.yaml")["tables"]
            self.profile = load_yaml("spec/v2/cohort_profiles_v2.yaml")["cohorts"][cohort]
            self.tables_in_cohort = list(self.profile["omop_tables"]) + list(self.profile["extension_tables"])
            self.disease_table = None
            self.rules_struct = load_yaml("rules/rules_structural_v2.yaml")["rules"]
            self.rules_sem = load_yaml("rules/rules_semantic_v2.yaml")["rules"]
            self.codelists = {}
            # 검사항목 타당 범위는 v2 명세에 아직 없어 v1 표를 빌려 쓴다(OMOP 검사 concept_id 는 같다)
            self.concepts = load_yaml("spec/concepts.yaml")
            # 값 집합: 코드와 concept_id 둘 다 쓴다(컬럼 타입에 따라 다르다)
            import csv as _csv
            self.set_codes, self.set_ids, self.code_of_concept = {}, {}, {}
            for r in _csv.DictReader(open(os.path.join(ROOT, "spec/v2/vocab/CONCEPT_SET_ITEM.csv"), encoding="utf-8")):
                self.set_codes.setdefault(r["concept_set_id"], set()).add(str(r["code"]))
                self.set_ids.setdefault(r["concept_set_id"], set()).add(str(r["concept_id"]))
                self.code_of_concept[str(r["concept_id"])] = str(r["code"])
        else:
            # v1 과 v3(의뢰사 9/30 매뉴얼 수정안)는 같은 '질환별 표' 구조라 경로만 다르다.
            paths = V3_PATHS if spec == "v3" else V1_PATHS
            self.spec = load_yaml(paths["spec"])["tables"]
            cl = load_yaml(paths["codelists"])
            self.codelists = {}
            for sect in cl.values():
                for k, v in sect.items():
                    self.codelists[k] = {str(c) for c in v.keys()}
            self.concepts = load_yaml("spec/concepts.yaml")
            self.profile = load_yaml(paths["profiles"])["cohorts"][cohort]
            self.tables_in_cohort = self.profile["tables"]
            self.disease_table = [t for t in self.tables_in_cohort if self.spec[t]["category"] == "disease"][0]
            self.rules_struct = load_yaml(paths["structural"])["rules"]
            self.rules_sem = load_yaml(paths["semantic"])["rules"]
        self.findings = []
        self.rule_stats = OrderedDict()
        self.aliases_applied = []

    # ------------------------------------------------------------------ data
    def load(self, data_dir):
        self.raw = {}
        for t in self.tables_in_cohort:
            p = os.path.join(data_dir, f"{t}.csv")
            if os.path.exists(p):
                df = pd.read_csv(p, dtype=str, keep_default_na=False, encoding="utf-8")
                df.columns = [c.strip() for c in df.columns]
                # 별칭 처리 (antp_therapy_id -> antp_id)
                if "antp_therapy_id" in df.columns and "antp_id" not in df.columns:
                    df = df.rename(columns={"antp_therapy_id": "antp_id"})
                    self.aliases_applied.append((t, "antp_therapy_id", "antp_id"))
                self.raw[t] = df
        return self

    # --------------------------------------------------------------- helpers
    def add(self, rule, table, field, row_key, person_id, detail, count_only=False):
        st = self.rule_stats[rule["id"]]
        st["violations"] += 1
        if st["violations"] <= self.max_examples or not count_only:
            self.findings.append(OrderedDict(
                rule_id=rule["id"], rule_name=rule["name"], category=rule["category"], severity=rule["severity"],
                table=table, field=field, row_key=str(row_key), person_id=str(person_id) if person_id is not None else "",
                detail=detail))

    def init_stat(self, rule, table):
        self.rule_stats[rule["id"]] = OrderedDict(
            rule_id=rule["id"], name=rule["name"], category=rule["category"], subcategory=rule.get("subcategory", ""),
            severity=rule["severity"], table=table, fields=",".join(rule.get("fields", [])), check=rule.get("check", "sql"),
            status="pass", violations=0, rows_checked=0, note="")

    def pk_of(self, table):
        return self.spec[table]["pk"]

    def keys(self, df, table):
        pk = self.pk_of(table)
        cols = [c.strip() for c in str(pk).split("+")]          # v2 는 복합 PK 를 'a+b+c' 로 적는다
        if len(cols) > 1 and all(c in df.columns for c in cols):
            pkcol = df[cols].astype(str).agg("+".join, axis=1)
        else:
            pkcol = df[pk] if pk in df.columns else pd.Series([""] * len(df), index=df.index)
        pid = df["person_id"] if "person_id" in df.columns else pd.Series([""] * len(df), index=df.index)
        return pkcol, pid

    # ------------------------------------------------------- structural pass
    def run_structural(self):
        for rule in self.rules_struct:
            table = rule["table"]
            if table not in self.tables_in_cohort:
                continue
            scope = rule.get("scope", "all")
            if scope != "all" and self.cohort not in scope:
                continue
            self.init_stat(rule, table)
            st = self.rule_stats[rule["id"]]
            chk = rule["check"]
            if chk == "table_present":
                if table not in self.raw:
                    self.add(rule, table, "", "", None, f"{table}.csv 없음")
                continue
            if table not in self.raw:
                st["status"] = "skipped"; st["note"] = "테이블 없음"; continue
            df = self.raw[table]
            st["rows_checked"] = len(df)
            pkcol, pid = self.keys(df, table)
            fields = rule.get("fields", [])
            p = rule.get("params", {})
            if chk == "columns":
                exp = set(p["expected"]); have = set(df.columns)
                for c in sorted(exp - have):
                    self.add(rule, table, c, "", None, f"컬럼 누락: {c}")
                for c in sorted(have - exp):
                    self.add(rule, table, c, "", None, f"명세에 없는 컬럼: {c} (경고)")
                for (t, a, b) in self.aliases_applied:
                    if t == table:
                        self.add(rule, table, a, "", None, f"별칭 컬럼 {a} 를 {b} 로 해석함 (경고)")
                continue
            # 이하 필드 기반 검사: 필드가 없으면 columns 규칙이 이미 잡았으므로 건너뜀
            missing = [f for f in fields if f not in df.columns]
            if missing and chk not in ("group_anchor", "person_invariant"):
                st["status"] = "skipped"; st["note"] = f"컬럼 없음: {missing}"; continue
            if chk == "pk_unique":
                cols = p.get("columns", fields)          # v2 는 복합 PK 가 있다
                null = df[cols].eq("").any(axis=1)
                for i in df.index[null]:
                    self.add(rule, table, "+".join(cols), "", pid[i], "PK NULL")
                dup = df[cols].duplicated(keep=False) & ~null
                for i in df.index[dup]:
                    key = "+".join(str(df.at[i, c]) for c in cols)
                    self.add(rule, table, "+".join(cols), key, pid[i], f"PK 중복: {key}")
            elif chk == "not_null":
                f = fields[0]
                for i in df.index[df[f] == ""]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f} NULL")
            elif chk == "type":
                f = fields[0]; ty = p["type"]
                rx = {"integer": INT_RE, "float": FLOAT_RE, "date": DATE_RE, "timestamp": TS_RE}[ty]
                vals = df[f]
                bad = (vals != "") & ~vals.str.match(rx)
                if ty in ("date", "timestamp"):
                    ok_fmt = (vals != "") & vals.str.match(rx)
                    parsed = pd.to_datetime(vals.where(ok_fmt, None), errors="coerce")
                    bad = bad | (ok_fmt & parsed.isna())
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}='{vals[i]}' 은 {ty} 아님")
            elif chk == "fk":
                f = fields[0]; rt = p["ref_table"]; rc = p["ref_field"]
                if rt not in self.tables_in_cohort:
                    st["status"] = "skipped"; st["note"] = f"참조 테이블 {rt} 코호트에 없음"; continue
                if rt not in self.raw or rc not in self.raw[rt].columns:
                    st["status"] = "skipped"; st["note"] = f"참조 테이블 {rt} 없음"; continue
                refset = set(self.raw[rt][rc][self.raw[rt][rc] != ""])
                vals = df[f]
                bad = (vals != "") & ~vals.isin(refset)
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}={vals[i]} 가 {rt}.{rc} 에 없음")
            elif chk == "concept_set":
                # v2: *_concept_id 컬럼은 값 집합의 concept_id 만 가질 수 있다
                f = fields[0]; allowed = {str(i) for i in p.get("concept_ids", [])}
                vals = df[f]
                bad = (vals != "") & ~vals.isin(allowed)
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}={vals[i]} 는 값 집합({p['concept_set']}) 의 concept_id 가 아니다")
            elif chk == "concept_code":
                # v2: 예/아니오 같은 컬럼은 concept_id 가 아니라 코드를 담는다
                f = fields[0]; allowed = {str(c) for c in p.get("codes", [])}
                vals = df[f]
                bad = (vals != "") & ~vals.isin(allowed)
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}={vals[i]} 는 값 집합({p['concept_set']}) 의 코드가 아니다 (허용: {sorted(allowed)})")
            elif chk == "concept_set_empty":
                st["status"] = "skipped"; st["note"] = f"값 집합 {p['concept_set']} 이 비어 있어 검사할 수 없다"
            elif chk == "not_null_when":
                # v2: 필수 여부가 다른 컬럼의 값에 걸린다. 조건은 모두 만족해야 필수다.
                f = fields[0]
                sel = pd.Series(True, index=df.index); why = []
                wc, wcode = p.get("when_column"), p.get("when_code")
                if wc:
                    if wc not in df.columns:
                        st["status"] = "skipped"; st["note"] = f"조건 컬럼 {wc} 없음"; continue
                    sel &= df[wc].map(lambda v: self.code_of_concept.get(str(v), "")) == wcode
                    why.append(f"{wcode} 행")
                wf = p.get("when_filled")
                if wf:
                    if wf not in df.columns:
                        st["status"] = "skipped"; st["note"] = f"조건 컬럼 {wf} 없음"; continue
                    sel &= df[wf] != ""
                    why.append(f"{wf} 이 채워진 행")
                wcc, wct = p.get("when_contains_column"), p.get("when_contains_text")
                if wcc:
                    if wcc not in df.columns:
                        st["status"] = "skipped"; st["note"] = f"조건 컬럼 {wcc} 없음"; continue
                    sel &= df[wcc].str.contains(wct, regex=False, na=False)
                    why.append(f"{wcc} 에 '{wct}' 가 든 행")
                wec, wev = p.get("when_equals_column"), p.get("when_equals_value")
                if wec:
                    if wec not in df.columns:
                        st["status"] = "skipped"; st["note"] = f"조건 컬럼 {wec} 없음"; continue
                    sel &= df[wec] == str(wev)
                    why.append(f"{wec} 이 {wev} 인 행")
                bad = sel & (df[f] == "")
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{' 이고 '.join(why)} 인데 {f} 가 비어 있다")
            elif chk == "not_null_either":
                # v2: 참조표를 싣기 전에는 concept_id 를 채울 수 없으므로 원천값이라도 있어야 한다
                cols = [c for c in p["columns"] if c in df.columns]
                if not cols:
                    st["status"] = "skipped"; st["note"] = "대상 컬럼 없음"; continue
                sel = pd.Series(True, index=df.index)
                if p.get("when_column") and p["when_column"] in df.columns:
                    kind = df[p["when_column"]].map(lambda v: self.code_of_concept.get(str(v), ""))
                    sel = kind == p["when_code"]
                bad = sel & df[cols].eq("").all(axis=1)
                for i in df.index[bad]:
                    self.add(rule, table, cols[0], pkcol[i], pid[i], f"{' 와 '.join(cols)} 가 모두 비어 있다")
            elif chk == "codelist":
                f = fields[0]; allowed = self.codelists.get(p["codelist"], set())
                vals = df[f]
                bad = (vals != "") & ~vals.isin(allowed)
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}={vals[i]} 코드표({p['codelist']}) 밖")
            elif chk == "range":
                f = fields[0]; lo, hi = p["min"], p["max"]
                num = pd.to_numeric(df[f].replace("", None), errors="coerce")
                bad = num.notna() & ((num < lo) | (num > hi))
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}={df.at[i, f]} 범위 [{lo},{hi}] 밖")
            elif chk == "pattern":
                f = fields[0]; rx = re.compile(p["regex"])
                vals = df[f]
                bad = (vals != "") & ~vals.apply(lambda v: bool(rx.match(v)))
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}='{vals[i]}' 패턴 불일치")
            elif chk == "not_future":
                f = fields[0]
                d = pd.to_datetime(df[f].replace("", None), errors="coerce")
                bad = d.notna() & (d > pd.Timestamp(self.today))
                for i in df.index[bad]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}={df.at[i, f]} 미래 날짜")
            elif chk == "group_anchor":
                anchor = p["anchor"]; members = [m for m in p["members"] if m in df.columns]
                if anchor not in df.columns or not members:
                    st["status"] = "skipped"; st["note"] = "anchor/멤버 컬럼 없음"; continue
                any_member = (df[members] != "").any(axis=1)
                bad = any_member & (df[anchor] == "")
                for i in df.index[bad]:
                    filled = [m for m in members if df.at[i, m] != ""][:3]
                    self.add(rule, table, anchor, pkcol[i], pid[i], f"{filled} 값 있으나 anchor {anchor} NULL")
            elif chk == "person_invariant":
                fs = [f for f in p["fields"] if f in df.columns]
                if "person_id" not in df.columns or not fs:
                    st["status"] = "skipped"; continue
                for f in fs:
                    sub = df[df[f] != ""][["person_id", f]]
                    n = sub.groupby("person_id")[f].nunique()
                    for person in n.index[n > 1]:
                        vals = sorted(set(sub[sub.person_id == person][f]))
                        self.add(rule, table, f, "", person, f"{f} 값이 환자 내에서 다름: {vals}")
            elif chk == "must_be_null":
                f = fields[0]
                for i in df.index[df[f] != ""]:
                    self.add(rule, table, f, pkcol[i], pid[i], f"{f}={df.at[i, f]} (이 코호트에서는 NULL 이어야 함)")
        for st in self.rule_stats.values():
            if st["violations"] > 0:
                st["status"] = "fail"

    # --------------------------------------------------------- typed frames
    def typed(self, table):
        df = self.raw[table]
        cols = {}
        for f in self.spec[table]["fields"]:
            n = f["name"]
            if n not in df.columns:
                continue
            s = df[n].replace("", None)
            t = f["type"]
            if t == "integer":
                cols[n] = pd.to_numeric(s, errors="coerce").astype("Int64")
            elif t == "float":
                cols[n] = pd.to_numeric(s, errors="coerce")
            elif t in ("date", "timestamp"):
                cols[n] = pd.to_datetime(s, errors="coerce")
            else:
                cols[n] = s
        return pd.DataFrame(cols, index=df.index)

    # ------------------------------------------------------- semantic pass
    def run_semantic(self):
        con = duckdb.connect()
        for t in self.tables_in_cohort:
            if t not in self.raw:
                continue
            df = self.typed(t)
            con.register(f"_raw_{t}", df)
            casts = []
            for f in self.spec[t]["fields"]:
                n = f["name"]
                if n not in df.columns:
                    continue
                if f["type"] == "date":
                    casts.append(f'CAST("{n}" AS DATE) AS "{n}"')
                else:
                    casts.append(f'"{n}"')
            con.execute(f'CREATE TABLE "{t}" AS SELECT {", ".join(casts)} FROM _raw_{t}')
        # 보조 테이블
        mc = self.concepts["measurements"]
        con.register("_mc", pd.DataFrame([dict(concept_id=int(k), name=v["name"], lo=float(v["plausible"][0]), hi=float(v["plausible"][1])) for k, v in mc.items()]))
        con.execute("CREATE TABLE _MEASUREMENT_CONCEPTS AS SELECT * FROM _mc")
        ac = [dict(concept_id=int(k), name=v["name"], category=int(v["category"])) for k, v in self.concepts["drugs"].items() if v.get("category") is not None]
        con.register("_ac", pd.DataFrame(ac))
        con.execute("CREATE TABLE _ANTICANCER_DRUGS AS SELECT * FROM _ac")

        if self.spec_version == "v2":
            # 행 종류 코드를 SQL 에서도 쓸 수 있게 보조 테이블로 올린다(예: 수술 병리만 고르기)
            con.register("_rk", pd.DataFrame([dict(concept_id=int(k), code=v) for k, v in self.code_of_concept.items()]))
            con.execute("CREATE TABLE _ROW_KIND AS SELECT * FROM _rk")
            # EPISODE_EVENT 가 어느 테이블을 가리키는지는 field concept 으로 정해진다.
            # 테이블마다 id 가 1부터 따로 매겨지므로 이걸 봐야 같은 번호끼리 헷갈리지 않는다.
            import csv as _csv2
            seed = {r["key"]: int(r["concept_id"]) for r in
                    _csv2.DictReader(open(os.path.join(ROOT, "spec/v2/vocab/CONCEPT.csv"), encoding="utf-8"))}
            con.register("_sd", pd.DataFrame([dict(key=k, concept_id=v) for k, v in seed.items() if k.startswith("F_")]))
            con.execute("CREATE TABLE _EPISODE_FIELD AS SELECT * FROM _sd")
            subst = {"{TODAY}": f"DATE '{self.today.isoformat()}'"}
            present = set(self.raw)
            for rule in self.rules_sem:
                scope = rule.get("scope", "all")
                if scope != "all" and self.cohort not in scope:
                    continue
                req = set(rule.get("requires", []))
                self.init_stat(rule, ",".join(sorted(req)) if req else "")
                st = self.rule_stats[rule["id"]]
                if not req.issubset(present):
                    st["status"] = "skipped"; st["note"] = f"필요 테이블 없음: {sorted(req - present)}"; continue
                self._run_one_sem(con, rule, subst)
            return self

        cd = self.concepts["cohort_definition"][self.cohort]
        dtab = self.disease_table
        kcd_field = {"LUNG_CANCER": "lucn_diag_kncd", "BREAST_CANCER": "brcn_diag_kncd", "COLORECTAL_CANCER": "clcn_diag_kncd"}.get(dtab, "NULL")
        kcd_match = " OR ".join([f"kcd LIKE '{p}%'" for p in cd["kcd_prefix"]])
        subst = {
            "{TODAY}": f"DATE '{self.today.isoformat()}'",
            "{COHORT_CONDITION_IDS}": ",".join(str(x) for x in cd["condition_concept_ids"]),
            "{DISEASE}": dtab, "{DISEASE_PK}": self.pk_of(dtab), "{DISEASE_KCD}": kcd_field, "{KCD_MATCH}": kcd_match,
            "{FEMALE_MIN}": str(cd["female_ratio"]["min"]), "{FEMALE_MAX}": str(cd["female_ratio"]["max"]),
            "{AGE_MIN}": str(cd["age_at_index"]["median_min"]), "{AGE_MAX}": str(cd["age_at_index"]["median_max"]),
        }
        present = set(self.raw)
        for rule in self.rules_sem:
            scope = rule.get("scope", "all")
            if scope != "all" and self.cohort not in scope:
                continue
            req = set(rule.get("requires", []))
            self.init_stat(rule, ",".join(sorted(req)) if req else dtab)
            st = self.rule_stats[rule["id"]]
            if not req.issubset(present) or dtab not in present:
                st["status"] = "skipped"; st["note"] = f"필요 테이블 없음: {sorted(req - present)}"; continue
            self._run_one_sem(con, rule, subst)
        con.close()
        return self

    def _run_one_sem(self, con, rule, subst):
        """의미 규칙 하나를 돌린다. SELECT 는 person_id, row_key, detail 순서로 낸다."""
        st = self.rule_stats[rule["id"]]
        sql = rule["sql"]
        for k, v in subst.items():
            sql = sql.replace(k, v)
        try:
            res = con.execute(sql).fetchall()
        except Exception as e:
            st["status"] = "error"; st["note"] = f"SQL 오류: {str(e)[:200]}"; return
        for person_id, row_key, detail in res:
            # 오류 데이터에서는 person_id 가 숫자가 아닐 수 있다(그 자체가 검출 대상이다).
            # 엔진이 여기서 넘어지면 정작 그 오류를 보고하지 못한다.
            if person_id is None:
                pid = None
            else:
                try:
                    pid = int(person_id)
                except (TypeError, ValueError):
                    pid = str(person_id)
            self.add(rule, st["table"], "", row_key, pid, detail or "")
        if st["violations"] > 0:
            st["status"] = "fail"

    # --------------------------------------------------------------- report
    def summary(self):
        stats = list(self.rule_stats.values())
        by_cat = defaultdict(lambda: dict(rules=0, failed=0, violations=0))
        for s in stats:
            b = by_cat[s["category"]]; b["rules"] += 1
            if s["status"] == "fail": b["failed"] += 1
            b["violations"] += s["violations"]
        return OrderedDict(
            cohort=self.cohort, run_date=self.today.isoformat(),
            tables={t: len(df) for t, df in self.raw.items()},
            rules_total=len(stats), rules_failed=sum(s["status"] == "fail" for s in stats),
            rules_skipped=sum(s["status"] == "skipped" for s in stats), rules_error=sum(s["status"] == "error" for s in stats),
            violations_total=sum(s["violations"] for s in stats),
            violations_error=sum(s["violations"] for s in stats if s["severity"] == "error"),
            violations_warning=sum(s["violations"] for s in stats if s["severity"] == "warning"),
            by_category=dict(by_cat), rules=stats)

    def write(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        # 위반이 없어도 머리글은 쓴다. 빈 DataFrame 을 그대로 쓰면 컬럼조차 없는 파일이 되어
        # 읽는 쪽이 '형식이 잘못된 파일'로 본다(TypeScript 구현과도 어긋난다).
        cols = ["rule_id", "rule_name", "category", "severity", "table", "field", "row_key", "person_id", "detail"]
        pd.DataFrame(self.findings, columns=cols).to_csv(
            os.path.join(out_dir, "findings.csv"), index=False, encoding="utf-8-sig")
        s = self.summary()
        json.dump(s, open(os.path.join(out_dir, "summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
        with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as fh:
            fh.write(f"# 데이터 품질 검증 보고서: {self.cohort} ({self.profile['kor']})\n\n")
            fh.write(f"검증일 {s['run_date']} / 테이블 {len(s['tables'])}개 / 규칙 {s['rules_total']}개 (실패 {s['rules_failed']}, 건너뜀 {s['rules_skipped']}, 오류 {s['rules_error']})\n\n")
            fh.write(f"위반 {s['violations_total']}건 (error {s['violations_error']}, warning {s['violations_warning']})\n\n")
            fh.write("| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |\n|---|---|---|---|\n")
            for c in ("Conformance", "Completeness", "Plausibility"):
                b = s["by_category"].get(c, dict(rules=0, failed=0, violations=0))
                fh.write(f"| {c} | {b['rules']} | {b['failed']} | {b['violations']} |\n")
            fh.write("\n## 테이블 행수\n\n" + "\n".join(f"- {t}: {n}" for t, n in s["tables"].items()) + "\n")
            fh.write("\n## 실패 규칙\n\n| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |\n|---|---|---|---|---|---|\n")
            ex = defaultdict(list)
            for f in self.findings:
                if len(ex[f["rule_id"]]) < 2:
                    ex[f["rule_id"]].append(mask_values(f["detail"]))
            for r in s["rules"]:
                if r["status"] == "fail":
                    fh.write(f"| {r['rule_id']} {r['name']} | {r['category']} | {r['severity']} | {r['table']} | {r['violations']} | {' / '.join(ex[r['rule_id']])[:150]} |\n")
            errs = [r for r in s["rules"] if r["status"] == "error"]
            if errs:
                fh.write("\n## 규칙 실행 오류\n\n" + "\n".join(f"- {r['rule_id']}: {mask_values(r['note'] or '')}" for r in errs) + "\n")
        return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--today", default=None)
    ap.add_argument("--spec", default="v1", choices=["v1", "v2", "v3"])
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else None
    e = Engine(a.cohort, today=today, spec=a.spec).load(a.data)
    e.run_structural()
    e.run_semantic()
    s = e.write(a.out)
    print(f"[{a.cohort}] rules={s['rules_total']} failed={s['rules_failed']} skipped={s['rules_skipped']} error={s['rules_error']} "
          f"violations={s['violations_total']} (error={s['violations_error']}, warning={s['violations_warning']})")


if __name__ == "__main__":
    main()
