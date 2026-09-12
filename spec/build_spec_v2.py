# -*- coding: utf-8 -*-
"""
사전 v2 변환기 · 1단계 배치표(엑셀) → 명세 YAML, 코드표, 코호트 구성, 파생 변수, 팀 배포용 사전(엑셀), 보고서.

입력
  internal/decisions/배치표_v0_YYYYMMDD.xlsx   (시트: 자문항목, 현명세필드, 테이블정의, 코드표)
  spec/kai_cdm_spec.yaml, spec/codelists.yaml    (v1: 코어 테이블과 '유지' 테이블의 필드, 내장 코드표)
  spec/v2_field_names.py                          (자문 항목 → 영문 필드명, 단위)
출력 (spec/v2/)
  kai_cdm_spec_v2.yaml     테이블(층·행 단위·키·상위 FK)과 필드
  codelists_v2.yaml        닫힌 범주 값 집합 + 표준 매핑 자리
  cohort_profiles_v2.yaml  코호트별 테이블 구성
  derived_v2.yaml          코어에서 파생하는 변수(입력 항목 아님)와 파생 점수
  legacy_fields_v2.yaml    v1 필드 중 자문 항목과 합쳐지지 않은 '이동' 필드 (승격 여부 검토용)
  dictionary_v2.xlsx       팀 배포용 사전
  spec_v2_report.md        통계·경고·검토 목록

원칙
  - 한 테이블 = 행 단위 하나. 질환 확장 표는 배치표의 행 단위에 따라 <질환>_BASELINE / _EXAM / _EVENT / _ASSESSMENT / _SURGERY 로 나눈다.
  - 코어 8개(+DEATH)가 검사·약물·시술·진단·방문·사망의 유일한 원천. 확장 표에 코어 컬럼 복사 금지.
  - 병원은 코드표(한글 라벨 + 짧은 코드)에서 고르고, 명세가 SNOMED/LOINC/OMOP 매핑을 보유한다.
  - '필수' 등급은 완전성 규칙의 근거(tier)로 기록하고, 행 단위 NOT NULL 은 키·사건일에만 건다.

    python spec/build_spec_v2.py [배치표.xlsx] [--out spec/v2]
"""
import sys, os, re, json, datetime, collections
import yaml
import openpyxl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "spec"))
from v2_field_names import FIELD_NAMES, UNITS, CODELIST_OVERRIDE, TYPE_OVERRIDE  # noqa: E402

args = [a for a in sys.argv[1:] if not a.startswith("--")]
XLSX = args[0] if args else os.path.join(ROOT, "internal/decisions/배치표_v0_20260912.xlsx")
OUT = os.path.join(ROOT, "spec/v2")
if "--out" in sys.argv: OUT = sys.argv[sys.argv.index("--out") + 1]
os.makedirs(OUT, exist_ok=True)

V1 = yaml.safe_load(open(os.path.join(ROOT, "spec/kai_cdm_spec.yaml"), encoding="utf-8"))["tables"]
V1_CODES = yaml.safe_load(open(os.path.join(ROOT, "spec/codelists.yaml"), encoding="utf-8"))
COHORT_OF = {"폐암": "LUNG_CANCER", "유방암": "BREAST_CANCER", "대장암": "COLORECTAL_CANCER", "대사이상지방간염": "MASLD", "당뇨병": "DIABETES", "림프종": "LYMPHOMA"}
COHORT_KOR = {"LUNG_CANCER": "폐암", "BREAST_CANCER": "유방암", "COLORECTAL_CANCER": "대장암", "MASLD": "대사이상지방간", "DIABETES": "당뇨병", "LYMPHOMA": "림프종"}
CORE = ["PERSON", "DEATH", "VISIT_OCCURRENCE", "CONDITION_OCCURRENCE", "PROCEDURE_OCCURRENCE", "DRUG_EXPOSURE", "MEASUREMENT", "OBSERVATION", "NOTE"]
KEEP_V1 = {"ANTP_THERAPY", "ADVERSE_EVENT"}
DISEASE_CRF = {"LUNG_CRF": "LUNG", "BREAST_CRF": "BREAST", "COLORECTAL_CRF": "COLORECTAL", "MASLD_CRF": "MASLD", "DIABETES_CRF": "DIABETES", "LYMPHOMA_CRF": "LYMPHOMA"}
warnings, notes = [], []

# ---------------------------------------------------------------- 배치표 읽기
wb = openpyxl.load_workbook(XLSX, data_only=True)
def rows_of(sheet):
    ws = wb[sheet]; hdr = [c.value for c in ws[1]]
    return [dict(zip(hdr, r)) for r in ws.iter_rows(min_row=2, values_only=True) if any(v is not None for v in r)]
ITEMS = rows_of("자문항목"); V1FIELDS = rows_of("현명세필드"); TDEF = rows_of("테이블정의"); CODES = rows_of("코드표")

# ---------------------------------------------------------------- 테이블 정의
tables = collections.OrderedDict()
def add_table(name, layer, kor, grain, pk, parent, desc):
    tables[name] = dict(name=name, layer=layer, kor=kor, grain=grain, pk=pk, parent=parent or None, desc=desc, cohorts=set(), fields=collections.OrderedDict())
for t in TDEF:
    add_table(t["테이블"], t["층"], t["한글"], t["행 단위"], t["고유키"], t["상위 FK"], t["설명"])

# 질환 확장 표는 행 단위별로 분해
SPLIT = {"환자 1": ("BASELINE", "환자 1"), "검사 1": ("EXAM", "검사 1"), "사건 1": ("EVENT", "사건 1"), "평가 1": ("ASSESSMENT", "평가 1"), "수술 1": ("SURGERY_DETAIL", "수술 1 (SURGERY 자식)")}
def split_disease_table(dest, grain_text):
    base = DISEASE_CRF[dest]
    key = next((k for k in SPLIT if grain_text and grain_text.startswith(k)), None)
    if key is None:
        key = "환자 1"; warnings.append(f"행 단위 불명 → BASELINE 으로 배치: {dest} / {grain_text}")
    suffix, grain = SPLIT[key]
    name = f"{base}_{suffix}"
    if name not in tables:
        BASE_COHORT = {"LUNG": "LUNG_CANCER", "BREAST": "BREAST_CANCER", "COLORECTAL": "COLORECTAL_CANCER", "MASLD": "MASLD", "DIABETES": "DIABETES", "LYMPHOMA": "LYMPHOMA"}
        kor = f"{COHORT_KOR[BASE_COHORT[base]]} {dict(BASELINE='기저(환자 1)', EXAM='검사(검사 1)', EVENT='사건(사건 1)', ASSESSMENT='평가(평가 1)', SURGERY_DETAIL='수술 세부(수술 1)')[suffix]}"
        parent = {"BASELINE": "COHORT_INDEX", "EXAM": "PROCEDURE_OCCURRENCE", "EVENT": "COHORT_INDEX", "ASSESSMENT": "COHORT_INDEX", "SURGERY_DETAIL": "SURGERY"}[suffix]
        add_table(name, "질환 확장", kor, grain, f"{name.lower()}_id", parent, tables[dest]["desc"] + f" — 행 단위 {grain}")
        tables[name]["origin"] = dest
    return name

# ---------------------------------------------------------------- 유형·단위·코드표
def field_type(kind, name, item):
    if kind == "날짜": return "date"
    if kind in ("예/아니오", "예/아니오+날짜"): return "integer"
    if kind == "수치":
        if re.search(r"count|_n$|number|regions|sites_count|children|fractions|cycles|lines|line_number|age$|year$|score$|grade$", name) and not re.search(r"percent|ratio", name): return "integer"
        return "float"
    if kind == "텍스트": return "text"
    return "varchar"
def unit_of(name, item):
    m = re.search(r"\((Gy|cm|mm|mg/dL|%|kPa|dB/m|μm|um|mmHg|mL|ng/mL)\)", item)
    if m: return {"μm": "um", "mmHg": "mm[Hg]"}.get(m.group(1), m.group(1))
    return UNITS.get(name)
def codelist_for(row, name, kind):
    cl = (row.get("코드표") or "").strip()
    if kind in ("예/아니오", "예/아니오+날짜"): return "YN"
    if kind not in ("닫힌 범주",): return None
    if not cl or cl.endswith("*") or "/" in cl:
        first = cl.split("/")[0].strip() if cl else ""
        if first and not first.endswith("*") and first in CODE_IDS: return first
        return "CL_" + name.upper()          # 값 집합 미정의 → 자리 표시 (보고서에 기록)
    return cl
CODE_IDS = {c["코드표"] for c in CODES}

# ---------------------------------------------------------------- 자문 항목 → 필드 / 파생
derived = []   # 코어 파생 변수
scores = []    # 파생 점수
def tier_of(g):
    g = str(g or "")
    return "필수" if g.startswith("필수") else ("권고" if g.startswith("권고") else "보류")

for r in ITEMS:
    cohort = COHORT_OF[r["질환"]]; item = r["항목"]; way = r["갈래"]; dest = r["목적지 테이블"]; kind = r["값 종류"] or "닫힌 범주"
    name = FIELD_NAMES.get(item)
    if not name:
        name = "item_" + re.sub(r"\W+", "_", item)[:30].lower(); warnings.append(f"영문 필드명 없음 → 임시 이름: {item} ({cohort})")
    tier = tier_of(r["등급"])
    std = r.get("표준 매핑 후보") or ""
    if way == "코어 파생":
        derived.append(dict(name=name, kor=item, cohort=cohort, source_table=dest, value_kind=kind, tier=tier, concept_set=(r.get("코드표") or None), standard=std or None, note=r.get("메모") or None))
        if dest in tables: tables[dest]["cohorts"].add(cohort)
        continue
    if dest in DISEASE_CRF: dest = split_disease_table(dest, r.get("행 단위"))
    if dest not in tables:
        warnings.append(f"목적지 테이블 미정의: {dest} ← {item}"); continue
    T = tables[dest]; T["cohorts"].add(cohort)
    f = T["fields"].get(name)
    if f is None:
        ty, pat = TYPE_OVERRIDE.get(name, (field_type(kind, name, item), None))
        cl = CODELIST_OVERRIDE[name] if name in CODELIST_OVERRIDE else codelist_for(r, name, kind)
        if name in CODELIST_OVERRIDE and CODELIST_OVERRIDE[name] == "YN": kind = "예/아니오"
        if pat: kind = "패턴"
        elif ty in ("float", "integer") and kind == "닫힌 범주": kind = "수치"
        f = dict(name=name, kor=item, type=ty, value_kind=kind, tier=tier, required=False,
                 codelist=cl, unit=unit_of(name, item) if ty in ("float", "integer") else None, standard=std or None,
                 cohorts=set(), sources=[], legacy=[], desc=None, pattern=pat)
        if kind == "열린 표준 코드" or (name == "diagnosis_name"): f["vocabulary"] = std or "참조표"
        if way == "파생 점수": f["derived_score"] = True; scores.append(dict(name=name, kor=item, table=dest, cohort=cohort))
        T["fields"][name] = f
    else:
        if f["kor"] != item: f["sources"].append(item)
        if tier == "필수": f["tier"] = "필수"
        elif tier == "권고" and f["tier"] == "보류": f["tier"] = "권고"
    f["cohorts"].add(cohort)
    cur = r.get("현 명세 대응 필드")
    if cur and cur not in f["legacy"]: f["legacy"].append(f"{r['현 테이블']}.{cur}")
    if r.get("메모"): f["desc"] = (f.get("desc") or "") + ("; " if f.get("desc") else "") + r["메모"] if r["메모"] not in (f.get("desc") or "") else f.get("desc")

# ---------------------------------------------------------------- 구조 필드(키·사건일) 삽입
EVENT_DATE = {"COHORT_INDEX": ("index_date", "코호트 진입일 (기준일)"), "STAGING": ("staging_date", "병기 평가일"), "PATHOLOGY_REPORT": ("specimen_date", "검체 채취일"),
              "BIOMARKER": ("test_date", "검사일"), "SURGERY": ("surgery_date", "수술 시행일"), "RADIOTHERAPY": ("rt_start_date", "방사선치료 시작일"),
              "RESPONSE_ASSESSMENT": ("response_assessment_date", "반응평가 기준일"), "FAMILY_HISTORY": (None, None), "PATHOLOGY_TUMOR": (None, None)}
def structural(T):
    name = T["name"]; pk = T["pk"]; fields = collections.OrderedDict()
    fields[pk] = dict(name=pk, kor=f"{T['kor']} ID", type="integer", value_kind="키", tier="필수", required=True, key="pk", cohorts=set(T["cohorts"]), sources=[], legacy=[], codelist=None, unit=None, standard=None, desc="행 고유키")
    if pk != "person_id":
        fields["person_id"] = dict(name="person_id", kor="환자 ID", type="integer", value_kind="키", tier="필수", required=True, key="fk", ref="PERSON.person_id", cohorts=set(T["cohorts"]), sources=[], legacy=[], codelist=None, unit=None, standard=None, desc="PERSON 외래키")
    parent = T.get("parent")
    if parent and parent not in ("PERSON", "COHORT_INDEX", "") and not parent.startswith("COHORT_INDEX"):
        p = parent.split(" ")[0]
        pt = tables.get(p) or {"pk": {"PROCEDURE_OCCURRENCE": "procedure_occurrence_id", "PROCEDURE": "procedure_occurrence_id"}.get(p, p.lower() + "_id")}
        pk_name = pt["pk"] if isinstance(pt, dict) else pt
        fields[pk_name] = dict(name=pk_name, kor=f"{p} 외래키", type="integer", value_kind="키", tier="권고", required=False, key="fk", ref=f"{p if p!='PROCEDURE' else 'PROCEDURE_OCCURRENCE'}.{pk_name}", cohorts=set(T["cohorts"]), sources=[], legacy=[], codelist=None, unit=None, standard=None, desc=f"{parent} 연결")
    if T["layer"] != "코어" and name not in ("FAMILY_HISTORY", "PATHOLOGY_TUMOR", "COHORT_INDEX"):
        fields["visit_occurrence_id"] = dict(name="visit_occurrence_id", kor="방문 ID", type="integer", value_kind="키", tier="권고", required=False, key="fk", ref="VISIT_OCCURRENCE.visit_occurrence_id", cohorts=set(T["cohorts"]), sources=[], legacy=[], codelist=None, unit=None, standard=None, desc="관련 방문(선택)")
    ed = EVENT_DATE.get(name)
    if ed is None and T["layer"] == "질환 확장":
        ed = {"BASELINE": ("record_date", "기록일"), "EXAM": ("exam_date", "검사일"), "EVENT": ("event_date", "사건 발생일"), "ASSESSMENT": ("assessment_date", "평가일"), "SURGERY_DETAIL": (None, None)}[name.split("_", 1)[1]]
    if ed and ed[0]:
        if ed[0] in T["fields"]: T["fields"][ed[0]]["required"] = True; T["fields"][ed[0]]["event_date"] = True
        else: fields[ed[0]] = dict(name=ed[0], kor=ed[1], type="date", value_kind="날짜", tier="필수", required=True, event_date=True, cohorts=set(T["cohorts"]), sources=[], legacy=[], codelist=None, unit=None, standard=None, desc="행의 기준 사건일")
    for k, v in T["fields"].items():
        if k not in fields: fields[k] = v
    T["fields"] = fields

# 코어·유지 테이블: v1 필드 그대로
for t in CORE:
    if t == "DEATH":
        T = tables["DEATH"]
        for n, k, ty, d in [("person_id", "환자 ID", "integer", "PERSON 외래키·고유키"), ("death_date", "사망일", "date", "v1 PERSON.death_date 를 이관"), ("death_type_concept_id", "사망 정보 출처", "integer", "OMOP type concept"), ("cause_concept_id", "사망 원인 concept", "integer", "SNOMED"), ("cause_source_value", "사망 원인 원천값", "varchar", "KCD 등")]:
            T["fields"][n] = dict(name=n, kor=k, type=ty, value_kind="키" if n == "person_id" else ("날짜" if ty == "date" else "열린 표준 코드"), tier="필수" if n in ("person_id", "death_date") else "권고", required=n in ("person_id", "death_date"), cohorts=set(COHORT_OF.values()), sources=[], legacy=["PERSON.death_date"] if n == "death_date" else [], codelist=None, unit=None, standard="OMOP DEATH", desc=d)
        T["cohorts"] = set(COHORT_OF.values()); continue
    T = tables[t]; T["cohorts"] = set(COHORT_OF.values())
    for f in V1[t]["fields"]:
        if t == "PERSON" and f["name"] == "death_date": notes.append("PERSON.death_date → DEATH 테이블로 이관"); continue
        T["fields"][f["name"]] = dict(name=f["name"], kor=f.get("kor") or f["name"], type=f.get("type", "varchar"), value_kind="코어", tier="필수" if f.get("required") else "권고", required=bool(f.get("required")), key=f.get("key"), ref=f.get("ref"), codelist=f.get("codelist"), unit=None, standard="OMOP", cohorts=set(COHORT_OF.values()), sources=[], legacy=[], desc=(f.get("desc") or "").replace("\n", " ")[:160], range=f.get("range"), pattern=f.get("pattern"))
    if t == "VISIT_OCCURRENCE":
        T["fields"]["discharge_to_concept_id"] = dict(name="discharge_to_concept_id", kor="퇴원 시 상태", type="integer", value_kind="닫힌 범주", tier="권고", required=False, codelist="DISCHARGE_STATUS", unit=None, standard="OMOP discharge_to", cohorts=set(COHORT_OF.values()), sources=["퇴원 시 환자 상태"], legacy=[], desc="자문 항목 '퇴원 시 환자 상태'")
for t in KEEP_V1:
    T = tables[t]
    for f in V1[t]["fields"]:
        if f["name"] in T["fields"]: continue
        T["fields"][f["name"]] = dict(name=f["name"], kor=f.get("kor") or f["name"], type=f.get("type", "varchar"), value_kind="v1 유지", tier="필수" if f.get("required") else "권고", required=bool(f.get("required")), key=f.get("key"), ref=f.get("ref"), codelist=f.get("codelist"), unit=None, standard=None, cohorts=set(), sources=[], legacy=[f"{t}.{f['name']}"], desc=(f.get("desc") or "").replace("\n", " ")[:160])
    T["cohorts"] |= set(c for c, prof in [(c, None) for c in COHORT_OF.values()]) if t == "ADVERSE_EVENT" else {"LUNG_CANCER", "BREAST_CANCER", "COLORECTAL_CANCER", "LYMPHOMA"}
    for f in T["fields"].values():
        if not f["cohorts"]: f["cohorts"] = set(T["cohorts"])
tables["ADVERSE_EVENT"]["desc"] += " · 코드체계: adverse_event_concept_id = MedDRA PT(또는 CTCAE 용어), severity = CTCAE 등급 1~5"

# 빈 질환 원본 표(LUNG_CRF 등)는 행 단위별 표로 대체되었으므로 제거
for d in list(DISEASE_CRF):
    if d in tables and not tables[d]["fields"]: del tables[d]
for T in list(tables.values()):
    if T["layer"] == "코어" and T["name"] != "DEATH": continue
    structural(T)

# ---------------------------------------------------------------- v1 이동 필드(합쳐지지 않은 것) → legacy
merged_legacy = {l for T in tables.values() for f in T["fields"].values() for l in f["legacy"]}
legacy = collections.defaultdict(list)
for r in V1FIELDS:
    key = f"{r['테이블']}.{r['필드']}"
    if r["처리"] in ("이동", "이관→코어") and key not in merged_legacy:
        legacy[r["목적지 테이블"]].append(dict(v1=key, kor=r.get("한글명") or "", desc=(r.get("설명") or "")[:120], type=r.get("타입"), group=r.get("현 그룹"), action=r["처리"]))

# ---------------------------------------------------------------- 코드표
codelists = collections.OrderedDict()
for c in CODES:
    cid = c["코드표"]
    cl = codelists.setdefault(cid, dict(kor=c["한글"], standard=None, note=None, values=[]))
    if c.get("표준 매핑 후보(코드표 단위)"): cl["standard"] = c["표준 매핑 후보(코드표 단위)"]
    if c.get("비고"): cl["note"] = c["비고"]
    val = str(c["값(코드·라벨)"]).strip(); code, _, label = val.partition(" ")
    if not label: code, label = val, val
    elif not re.match(r"^[A-Za-z0-9+\-/.]+$", code): code, label = str(c["순번"]), val
    cl["values"].append(dict(code=code, label=label, snomed=c.get("SNOMED/표준 ID") or None))
# v1 내장 코드표: 유지 테이블 것만 재키
for k, v in V1_CODES.get("embedded", {}).items():
    t, f = k.split(".", 1)
    if t in KEEP_V1: codelists[f"{t}.{f}"] = dict(kor=f, standard=None, note="v1 내장 코드표", values=[dict(code=str(a), label=str(b), snomed=None) for a, b in v.items()])
codelists["common"] = V1_CODES.get("common"); codelists["omop"] = V1_CODES.get("omop")
placeholder = sorted({f["codelist"] for T in tables.values() for f in T["fields"].values() if f.get("codelist") and str(f["codelist"]).startswith("CL_")})
for p in placeholder: codelists[p] = dict(kor=p, standard=None, note="값 집합 미정의 · 2.1 에서 채움", values=[])

# ---------------------------------------------------------------- 코호트 구성
profiles = collections.OrderedDict()
for c in COHORT_OF.values():
    profiles[c] = dict(kor=COHORT_KOR[c], tables=[t for t, T in tables.items() if T["layer"] == "코어" or c in T["cohorts"]])

# ---------------------------------------------------------------- YAML 출력
def ser_field(f):
    o = collections.OrderedDict()
    for k in ("name", "kor", "type", "value_kind", "tier", "required", "key", "ref", "event_date", "codelist", "vocabulary", "unit", "standard", "range", "pattern", "derived_score", "desc"):
        v = f.get(k)
        if v not in (None, False, "", []): o[k] = v
    o["cohorts"] = sorted(f["cohorts"])
    if f.get("sources"): o["also"] = f["sources"]
    if f.get("legacy"): o["v1_hint"] = f["legacy"]
    return dict(o)
spec = collections.OrderedDict(meta=dict(name="K-AI 질환별 코호트 CDM 명세", version="2.0.0-draft", source=os.path.basename(XLSX), generated_by="spec/build_spec_v2.py", generated_at=datetime.date.today().isoformat(),
    principles=["한 테이블 = 행 단위 하나", "코어 8개(+DEATH)가 검사·약물·시술·진단·방문·사망의 유일한 원천", "확장 표에 코어 컬럼 복사 금지, FK 로만 연결", "닫힌 범주는 사업단 코드표에서 선택, 명세가 표준 매핑 보유", "tier 는 완전성 규칙의 근거, required 는 키·사건일에만"]),
    layers=dict(core=[t for t, T in tables.items() if T["layer"] == "코어"], common=[t for t, T in tables.items() if T["layer"] == "공통 확장"], disease=[t for t, T in tables.items() if T["layer"] == "질환 확장"]),
    tables=collections.OrderedDict())
for name, T in tables.items():
    spec["tables"][name] = dict(name=name, layer=T["layer"], kor=T["kor"], grain=T["grain"], pk=T["pk"], parent=T.get("parent") or None, desc=T["desc"], cohorts=sorted(T["cohorts"]), fields=[ser_field(f) for f in T["fields"].values()])
class D(yaml.SafeDumper):
    pass
D.add_representer(collections.OrderedDict, lambda d, data: d.represent_dict(data.items()))
def dump(obj, fn):
    with open(os.path.join(OUT, fn), "w", encoding="utf-8") as fh: yaml.dump(json.loads(json.dumps(obj, ensure_ascii=False)), fh, Dumper=D, allow_unicode=True, sort_keys=False, width=140)
dump(spec, "kai_cdm_spec_v2.yaml")
dump(dict(codelists=codelists), "codelists_v2.yaml")
dump(dict(cohorts=profiles), "cohort_profiles_v2.yaml")
dump(dict(derived=derived, derived_scores=scores), "derived_v2.yaml")
dump(dict(legacy=dict(legacy)), "legacy_fields_v2.yaml")

# ---------------------------------------------------------------- 팀 배포용 사전 (엑셀)
xw = Workbook(); H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="003B73"); WRAP = Alignment(wrap_text=True, vertical="top")
def sheet(ws, header, rows, widths):
    ws.append(header)
    for c in ws[1]: c.font = H; c.fill = HF; c.alignment = WRAP
    for r in rows: ws.append(r)
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
ws = xw.active; ws.title = "테이블"
sheet(ws, ["테이블", "층", "한글", "행 단위", "고유키", "상위", "적용 코호트", "필드 수", "설명"], [[n, T["layer"], T["kor"], T["grain"], T["pk"], T.get("parent") or "", ", ".join(COHORT_KOR[c] for c in sorted(T["cohorts"])), len(T["fields"]), T["desc"]] for n, T in tables.items()], [22, 9, 18, 24, 22, 22, 30, 7, 70])
allf = []
for n, T in tables.items():
    for f in T["fields"].values():
        allf.append([n, f["name"], f["kor"], f["type"], f.get("unit") or "", f["value_kind"], f["tier"], "Y" if f.get("required") else "", f.get("codelist") or "", f.get("vocabulary") or "", f.get("standard") or "", ", ".join(COHORT_KOR[c] for c in sorted(f["cohorts"])), "; ".join(f.get("sources") or []), "; ".join(f.get("legacy") or []), f.get("desc") or ""])
sheet(xw.create_sheet("필드"), ["테이블", "필드", "한글", "타입", "단위", "값 종류", "등급", "행 필수", "코드표", "참조 어휘", "표준 매핑 후보", "적용 코호트", "같은 뜻 항목", "v1 대응", "설명"], allf, [22, 30, 30, 8, 8, 12, 6, 6, 22, 18, 30, 28, 30, 30, 50])
crow = []
for cid, cl in codelists.items():
    if not isinstance(cl, dict) or "values" not in cl: continue
    for v in cl["values"]: crow.append([cid, cl["kor"], v["code"], v["label"], v.get("snomed") or "", cl.get("standard") or "", cl.get("note") or ""])
sheet(xw.create_sheet("코드표"), ["코드표", "한글", "코드", "라벨", "SNOMED/표준 ID", "표준 매핑 후보", "비고"], crow, [24, 22, 10, 30, 16, 44, 36])
sheet(xw.create_sheet("파생변수"), ["변수", "한글", "코호트", "원천 테이블", "값 종류", "등급", "concept set", "표준", "메모"], [[d["name"], d["kor"], COHORT_KOR[d["cohort"]], d["source_table"], d["value_kind"], d["tier"], d.get("concept_set") or "", d.get("standard") or "", d.get("note") or ""] for d in derived], [28, 32, 10, 22, 14, 6, 20, 26, 40])
sheet(xw.create_sheet("코호트구성"), ["코호트", "테이블"], [[COHORT_KOR[c], ", ".join(p["tables"])] for c, p in profiles.items()], [14, 160])
lrow = [[dest, e["v1"], e["kor"], e["type"], e["group"], e["action"], e["desc"]] for dest, es in legacy.items() for e in es]
sheet(xw.create_sheet("v1 미승격 필드"), ["목적지", "v1 필드", "한글", "타입", "v1 그룹", "처리", "설명"], lrow, [22, 40, 28, 8, 10, 12, 60])
xw.save(os.path.join(OUT, "dictionary_v2.xlsx"))

# ---------------------------------------------------------------- 보고서
nf = sum(len(T["fields"]) for T in tables.values())
by_layer = collections.Counter(T["layer"] for T in tables.values())
tiers = collections.Counter(f["tier"] for T in tables.values() for f in T["fields"].values())
L = [f"# 사전 v2 변환 보고서 ({datetime.date.today().isoformat()})", "", f"입력: `{os.path.relpath(XLSX, ROOT)}` · 출력: `spec/v2/`", "",
     "## 규모", "", "| 구분 | 수 |", "|---|---|", f"| 테이블 | {len(tables)} (코어 {by_layer['코어']}, 공통 확장 {by_layer['공통 확장']}, 질환 확장 {by_layer['질환 확장']}) |",
     f"| 필드 | {nf} (필수 {tiers['필수']}, 권고 {tiers['권고']}, 보류 {tiers['보류']}) |", f"| 코어 파생 변수 | {len(derived)} |", f"| 파생 점수 | {len(scores)} |",
     f"| 코드표 | {sum(1 for v in codelists.values() if isinstance(v, dict) and 'values' in v)} (값 미정의 자리 {len(placeholder)}) |", f"| v1 미승격 필드 | {sum(len(v) for v in legacy.values())} |", "",
     "## 테이블", "", "| 테이블 | 층 | 행 단위 | 필드 | 코호트 |", "|---|---|---|---|---|"]
for n, T in tables.items(): L.append(f"| {n} | {T['layer']} | {T['grain']} | {len(T['fields'])} | {', '.join(COHORT_KOR[c] for c in sorted(T['cohorts']))} |")
L += ["", "## v1 미승격 필드 (목적지별)", "", "자문 항목과 이름이 합쳐지지 않은 v1 '이동'·'이관' 필드입니다. 필드의 `v1_hint` 는 배치표의 휴리스틱 대응이므로 참고용입니다. 승격(필드 추가)·폐기 여부를 정합니다. 상세는 `legacy_fields_v2.yaml`, 사전 엑셀 'v1 미승격 필드' 시트.", ""]
for dest, es in sorted(legacy.items(), key=lambda x: -len(x[1])): L.append(f"- {dest}: {len(es)}개")
L += ["", "## 값 집합이 비어 있는 코드표 (2.1 에서 채움)", "", ", ".join(placeholder) or "없음", "", "## 경고", ""] + [f"- {w}" for w in warnings] + ["", "## 메모", ""] + [f"- {n}" for n in notes]
open(os.path.join(OUT, "spec_v2_report.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L[:14])); print(f"... 경고 {len(warnings)}건, 출력 → {OUT}")
