# -*- coding: utf-8 -*-
"""
단계 1-A: 명세에서 구조 규칙을 자동 생성한다.

    python rules/generate_structural_rules.py             # v1 명세 -> rules/rules_structural.yaml
    python rules/generate_structural_rules.py --spec v2   # v2 명세 -> rules/rules_structural_v2.yaml

v1 과 v2 는 당분간 나란히 돈다. 병원이 쓰던 v1 경로를 끊지 않고 v2 를 견주어 보기 위해서다.

규칙 분류는 Kahn 프레임워크(OHDSI DataQualityDashboard 와 동일)를 따른다.
  Conformance  : 값/관계/계산 적합성 (타입, 코드표, 패턴, PK/FK)
  Completeness : 필수값, 그룹 anchor, 테이블/컬럼 존재
  Plausibility : 범위, 시간 순서, 환자 불변성 (구조 규칙에서는 범위와 불변성만)

출력: rules/rules_structural.yaml
"""
import sys, io, yaml
from collections import OrderedDict
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

V2 = "--spec" in sys.argv and sys.argv[sys.argv.index("--spec") + 1] == "v2"
if V2:
    SPEC = yaml.safe_load(open("spec/v2/kai_cdm_spec_v2.yaml", encoding="utf-8"))
    PROFILES = yaml.safe_load(open("spec/v2/cohort_profiles_v2.yaml", encoding="utf-8"))["cohorts"]
    NONCANCER = [c for c, v in PROFILES.items() if "ANTP_THERAPY" not in (v.get("extension_tables") or []) + (v.get("omop_tables") or [])]
    OUT = "rules/rules_structural_v2.yaml"
    # 값 집합의 허용 concept_id 목록. v2 는 코드 문자열이 아니라 concept_id 로 값을 받는다.
    import csv
    CONCEPT = list(csv.DictReader(open("spec/v2/vocab/CONCEPT.csv", encoding="utf-8")))
    SET_IDS = {}
    for c in CONCEPT:
        if c["concept_class_id"] == "Value" and c["key"].startswith("CS:"):
            SET_IDS.setdefault(c["key"].split(":")[1], []).append(int(c["concept_id"]))
else:
    SPEC = yaml.safe_load(open("spec/kai_cdm_spec.yaml", encoding="utf-8"))
    PROFILES = yaml.safe_load(open("spec/cohort_profiles.yaml", encoding="utf-8"))["cohorts"]
    NONCANCER = [c for c, v in PROFILES.items() if "ANTP_THERAPY" not in v["tables"]]
    OUT = "rules/rules_structural.yaml"

rules = []
def add(rid, name, category, subcategory, table, check, severity="error", fields=None, params=None, desc="", scope="all"):
    r = OrderedDict(id=rid, name=name, category=category, subcategory=subcategory, table=table,
                    fields=fields or [], severity=severity, check=check, params=params or {}, desc=desc, scope=scope,
                    source="auto:spec")
    rules.append(r)

n = 0
def nid(prefix):
    global n; n += 1
    return f"{prefix}-{n:04d}"

for tname, t in (SPEC["tables"].items() if not V2 else []):
    fields = t["fields"]
    fnames = [f["name"] for f in fields]
    add(nid("ST"), f"{tname} 테이블 존재", "Completeness", "table", tname, "table_present",
        desc=f"코호트 구성에 포함된 {tname} 테이블이 제출되어야 한다.")
    add(nid("ST"), f"{tname} 컬럼 구성", "Conformance", "structure", tname, "columns", severity="error",
        params=dict(expected=fnames, aliases={"antp_therapy_id": "antp_id"}),
        desc="명세의 모든 컬럼이 존재해야 한다. 명세에 없는 컬럼은 경고. antp_therapy_id 는 antp_id 의 별칭으로 허용(경고).")
    if t.get("pk"):
        add(nid("ST"), f"{tname}.{t['pk']} PK 유일성", "Conformance", "relational", tname, "pk_unique",
            fields=[t["pk"]], desc="PK 는 NULL 이 아니고 유일해야 한다.")
    for f in fields:
        fn = f["name"]
        if f.get("required") and f.get("key") != "PK":
            add(nid("ST"), f"{tname}.{fn} 필수", "Completeness", "value", tname, "not_null", fields=[fn],
                desc=f"필수 필드 {fn} 은 NULL 일 수 없다.")
        if f["type"] in ("integer", "float", "date", "timestamp"):
            add(nid("ST"), f"{tname}.{fn} 타입({f['type']})", "Conformance", "value", tname, "type", fields=[fn],
                params=dict(type=f["type"]), desc=f"{fn} 은 {f['type']} 형식이어야 한다 (날짜는 YYYY-MM-DD).")
        if f.get("key") == "FK" and f.get("ref"):
            rt, rc = f["ref"].split(".")
            add(nid("ST"), f"{tname}.{fn} -> {f['ref']} 참조무결성", "Conformance", "relational", tname, "fk",
                fields=[fn], params=dict(ref_table=rt, ref_field=rc),
                desc=f"{fn} 의 값은 {f['ref']} 에 존재해야 한다 (참조 테이블이 코호트에 없으면 건너뜀).")
        if f.get("codelist"):
            add(nid("ST"), f"{tname}.{fn} 코드표", "Conformance", "value", tname, "codelist", fields=[fn],
                params=dict(codelist=f["codelist"]),
                severity="error" if not f["codelist"].startswith("OMOP.") else "warning",
                desc=f"{fn} 값은 코드표 {f['codelist']} 에 있어야 한다. (OMOP 집합은 병원 설정으로 확장 가능하므로 경고)")
        if f.get("range"):
            add(nid("ST"), f"{tname}.{fn} 범위", "Plausibility", "atemporal", tname, "range", fields=[fn],
                params=dict(min=f["range"][0], max=f["range"][1]), severity="warning",
                desc=f"{fn} 은 [{f['range'][0]}, {f['range'][1]}] 범위여야 한다.")
        if f.get("pattern"):
            add(nid("ST"), f"{tname}.{fn} 패턴", "Conformance", "value", tname, "pattern", fields=[fn],
                params=dict(regex=f["pattern"]), severity="warning", desc=f"{fn} 은 정규식 {f['pattern']} 에 맞아야 한다.")
        if f["type"] in ("date", "timestamp"):
            add(nid("ST"), f"{tname}.{fn} 미래 날짜 금지", "Plausibility", "temporal", tname, "not_future", fields=[fn],
                desc=f"{fn} 은 검증 실행일보다 미래일 수 없다.")
    # 이벤트 그룹 규칙 (결정 D-01)
    if "groups" in t:
        for g, gv in t["groups"].items():
            anchor = gv.get("anchor")
            members = [f["name"] for f in fields if f.get("group") == g and f["name"] != anchor]
            if anchor and members:
                add(nid("ST"), f"{tname} 그룹 '{g}' anchor 날짜", "Completeness", "group", tname, "group_anchor",
                    fields=[anchor] + members, params=dict(anchor=anchor, members=members),
                    desc=f"그룹 '{g}' 의 필드({len(members)}개) 중 하나라도 값이 있으면 anchor {anchor} 가 있어야 한다.")
        inv = [f["name"] for f in fields if f.get("group") == "patient" and f["name"] not in ("antp_id", "file_id")]
        if inv:
            add(nid("ST"), f"{tname} 환자 불변 필드 일관성", "Plausibility", "atemporal", tname, "person_invariant",
                fields=inv, params=dict(fields=inv), severity="warning",
                desc="환자 수준 필드는 동일 person_id 의 모든 행에서 값이 같아야 한다 (NULL 은 무시).")
    # 비항암 코호트에서 antp_id NULL (결정 D-11)
    if "antp_id" in fnames and tname != "ANTP_THERAPY":
        add(nid("ST"), f"{tname}.antp_id 비항암 코호트 NULL", "Conformance", "relational", tname, "must_be_null",
            fields=["antp_id"], scope=NONCANCER, desc="항암 테이블이 없는 코호트에서는 antp_id 가 항상 NULL 이어야 한다.")

# ---------------------------------------------------------------- v2 명세에서 생성
# v1 과 다른 점: 값이 코드 문자열이 아니라 concept_id 이고(concept_set), 코호트 범위가
# 테이블이 아니라 컬럼마다 붙으며, 그룹 anchor 대신 event_date 표시가 있다.
if V2:
    TYPE_RULE = {"integer": "integer", "bigint": "integer", "float": "float", "date": "date"}
    for tname, t in SPEC["tables"].items():
        fields = t["fields"]
        fnames = [f["name"] for f in fields]
        tscope = sorted({c for f in fields for c in (f.get("cohorts") or [])}) or "all"
        add(nid("SV"), f"{tname} 테이블 존재", "Completeness", "table", tname, "table_present", scope=tscope,
            desc=f"코호트 구성에 포함된 {tname} 테이블이 제출되어야 한다.")
        add(nid("SV"), f"{tname} 컬럼 구성", "Conformance", "structure", tname, "columns",
            params=dict(expected=fnames), scope=tscope, desc="명세의 모든 컬럼이 존재해야 한다. 명세에 없는 컬럼은 경고.")
        if t.get("pk"):
            add(nid("SV"), f"{tname}.{t['pk']} PK 유일성", "Conformance", "relational", tname, "pk_unique",
                fields=[t["pk"]], scope=tscope, desc="PK 는 NULL 이 아니고 유일해야 한다.")
        for f in fields:
            fn, scope = f["name"], sorted(f.get("cohorts") or []) or tscope
            # 필수: OMOP 이 요구하거나(required) 배치표가 '필수' 로 정한 것
            key = (f.get("key") or "").upper()
            if (f.get("required") or f.get("tier") == "필수") and key != "PK":
                add(nid("SV"), f"{tname}.{fn} 필수", "Completeness", "value", tname, "not_null", fields=[fn],
                    scope=scope, desc=f"필수 필드 {fn} 은 NULL 일 수 없다.")
            if f["type"] in TYPE_RULE:
                add(nid("SV"), f"{tname}.{fn} 타입({f['type']})", "Conformance", "value", tname, "type", fields=[fn],
                    params=dict(type=TYPE_RULE[f["type"]]), scope=scope,
                    desc=f"{fn} 은 {f['type']} 형식이어야 한다 (날짜는 YYYY-MM-DD).")
            if key == "FK" and f.get("ref"):
                rt, rc = f["ref"].split(".")
                add(nid("SV"), f"{tname}.{fn} -> {f['ref']} 참조무결성", "Conformance", "relational", tname, "fk",
                    fields=[fn], params=dict(ref_table=rt, ref_field=rc), scope=scope,
                    desc=f"{fn} 의 값은 {f['ref']} 에 존재해야 한다 (참조 테이블이 코호트에 없으면 건너뜀).")
            cs = f.get("concept_set")
            if cs and SET_IDS.get(cs):
                add(nid("SV"), f"{tname}.{fn} 값 집합({cs})", "Conformance", "value", tname, "concept_set", fields=[fn],
                    params=dict(concept_set=cs, concept_ids=sorted(SET_IDS[cs])), scope=scope,
                    desc=f"{fn} 은 값 집합 {cs} 의 concept_id 여야 한다.")
            elif cs:
                add(nid("SV"), f"{tname}.{fn} 값 집합({cs}) 비어 있음", "Conformance", "value", tname, "concept_set_empty",
                    fields=[fn], params=dict(concept_set=cs), severity="warning", scope=scope,
                    desc=f"{cs} 에 아직 값이 없어 {fn} 을 검사할 수 없다. 값 집합을 채우면 검사가 생긴다.")
            if f["type"] == "date":
                add(nid("SV"), f"{tname}.{fn} 미래 날짜 금지", "Plausibility", "temporal", tname, "not_future",
                    fields=[fn], scope=scope, desc=f"{fn} 은 검증 실행일보다 미래일 수 없다.")
        # v1 의 그룹 anchor 자리. v2 는 서식마다 사건 날짜 한 개를 둔다.
        anchors = [f["name"] for f in fields if f.get("event_date")]
        members = [f["name"] for f in fields if f["name"] not in anchors and not f.get("key")]  # 키 컬럼은 제외
        if len(anchors) == 1 and members:
            add(nid("SV"), f"{tname} 사건 날짜 필수", "Completeness", "group", tname, "group_anchor",
                fields=anchors + members, params=dict(anchor=anchors[0], members=members), scope=tscope,
                desc=f"어느 값이라도 채워졌으면 사건 날짜 {anchors[0]} 이 있어야 한다.")
        elif len(anchors) > 1:
            print(f"  경고: {tname} 에 사건 날짜가 {len(anchors)}개다 ({', '.join(anchors)}) — anchor 규칙을 만들지 않았다")

class D(yaml.SafeDumper): pass
D.add_representer(OrderedDict, lambda d, data: d.represent_dict(data.items()))
with open(OUT, "w", encoding="utf-8") as fh:
    yaml.dump(dict(rules=rules), fh, Dumper=D, allow_unicode=True, sort_keys=False, width=160)

from collections import Counter
print(f"structural rules ({'v2' if V2 else 'v1'}): {len(rules)} -> {OUT}")
print(Counter(r["category"] for r in rules))
print(Counter(r["check"] for r in rules))
