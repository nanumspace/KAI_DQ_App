# -*- coding: utf-8 -*-
"""
단계 3: 데이터 품질 검증 엔진 (참조 구현)

사용법:
    python dq/engine.py --cohort LUNG_CANCER --data synth/output/clean/LUNG_CANCER --out dq/reports/clean_LUNG_CANCER

입력  : 코호트 디렉터리의 <TABLE>.csv (UTF-8, 헤더 포함, NULL 은 빈 문자열)
규칙  : rules/rules_structural.yaml (명세에서 자동 생성) + rules/rules_semantic.yaml (수동 작성, DuckDB SQL)
출력  : findings.csv (위반 행 단위), summary.json (규칙 단위), report.md (사람용 요약)

구조 규칙은 원본 문자열 위에서 검사하고(타입 오류를 잡기 위해), 의미 규칙은 명세 타입으로 변환한 뒤 DuckDB 에서 SQL 로 검사한다.
"""
import argparse, io, json, os, re, sys, datetime as dt
from collections import OrderedDict, defaultdict
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


class Engine:
    def __init__(self, cohort, today=None, max_examples=50):
        self.cohort = cohort
        self.today = today or dt.date.today()
        self.max_examples = max_examples
        self.spec = load_yaml("spec/kai_cdm_spec.yaml")["tables"]
        cl = load_yaml("spec/codelists.yaml")
        self.codelists = {}
        for sect in cl.values():
            for k, v in sect.items():
                self.codelists[k] = {str(c) for c in v.keys()}
        self.concepts = load_yaml("spec/concepts.yaml")
        self.profile = load_yaml("spec/cohort_profiles.yaml")["cohorts"][cohort]
        self.tables_in_cohort = self.profile["tables"]
        self.disease_table = [t for t in self.tables_in_cohort if self.spec[t]["category"] == "disease"][0]
        self.rules_struct = load_yaml("rules/rules_structural.yaml")["rules"]
        self.rules_sem = load_yaml("rules/rules_semantic.yaml")["rules"]
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
                f = fields[0]
                null = df[f] == ""
                for i in df.index[null]:
                    self.add(rule, table, f, "", pid[i], "PK NULL")
                dup = df[f].duplicated(keep=False) & ~null
                for i in df.index[dup]:
                    self.add(rule, table, f, df.at[i, f], pid[i], f"PK 중복: {df.at[i, f]}")
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
        ac = [dict(concept_id=int(k), name=v["name"]) for k, v in self.concepts["drugs"].items() if v.get("category") is not None]
        con.register("_ac", pd.DataFrame(ac))
        con.execute("CREATE TABLE _ANTICANCER_DRUGS AS SELECT * FROM _ac")

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
            sql = rule["sql"]
            for k, v in subst.items():
                sql = sql.replace(k, v)
            try:
                res = con.execute(sql).fetchall()
            except Exception as e:
                st["status"] = "error"; st["note"] = f"SQL 오류: {str(e)[:200]}"; continue
            for person_id, row_key, detail in res:
                self.add(rule, st["table"], "", row_key, None if person_id is None else int(person_id), detail or "")
            if st["violations"] > 0:
                st["status"] = "fail"
        con.close()

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
        pd.DataFrame(self.findings).to_csv(os.path.join(out_dir, "findings.csv"), index=False, encoding="utf-8-sig")
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
                    ex[f["rule_id"]].append(f["detail"])
            for r in s["rules"]:
                if r["status"] == "fail":
                    fh.write(f"| {r['rule_id']} {r['name']} | {r['category']} | {r['severity']} | {r['table']} | {r['violations']} | {' / '.join(ex[r['rule_id']])[:150]} |\n")
            errs = [r for r in s["rules"] if r["status"] == "error"]
            if errs:
                fh.write("\n## 규칙 실행 오류\n\n" + "\n".join(f"- {r['rule_id']}: {r['note']}" for r in errs) + "\n")
        return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--today", default=None)
    a = ap.parse_args()
    today = dt.date.fromisoformat(a.today) if a.today else None
    e = Engine(a.cohort, today=today).load(a.data)
    e.run_structural()
    e.run_semantic()
    s = e.write(a.out)
    print(f"[{a.cohort}] rules={s['rules_total']} failed={s['rules_failed']} skipped={s['rules_skipped']} error={s['rules_error']} "
          f"violations={s['violations_total']} (error={s['violations_error']}, warning={s['violations_warning']})")


if __name__ == "__main__":
    main()
