# -*- coding: utf-8 -*-
"""사전 v2.2 · 열린 표준 코드가 가리키는 참조표 등록부.

값이 미리 정해진 필드는 값 집합(코드표)으로 받지만, 수술명·레지멘·이상사례 용어처럼
값이 수천~수십만 개인 필드는 값을 열거하지 않고 "어느 표준 표를 쓰는가"만 정한다.
그 등록 내용이 이 파일이다.

저장소에는 표의 **내용을 넣지 않는다.** MedDRA·SNOMED·ATC 는 재배포가 제한된
라이선스이고, 심평원 마스터는 공개 데이터지만 원본이 수십 MB라 저장소에 둘 것이 아니다.
대신 `spec/load_reference_tables.py` 가 각 기관에서 받은 로컬 원본을 읽어
`spec/v2/vocab/ref/`(gitignore) 에 표를 만든다. 병원은 자기 원본으로 같은 표를 만든다.

각 항목의 뜻:
  kor/vocabulary/version  어휘 이름과 판
  license                 재배포 조건. '공개'가 아니면 저장소에 내용을 넣지 않는다.
  obtain                  어디서 받는가
  source                  로컬 원본의 상대 경로(REF_ROOT 기준). 없으면 로더가 건너뛴다.
  code/label              그 표에서 코드·표기에 해당하는 열
  note                    적용 범위나 주의점
"""

# 로컬 원본 뿌리. 환경변수 KAI_REF_ROOT 로 덮어쓸 수 있다(병원마다 다르다).
DEFAULT_REF_ROOT = "/Users/min/Research/standard_terminology"

REFERENCE_TABLES = {
    "REF_MEDDRA_PT": dict(
        kor="이상사례 용어(MedDRA PT)", vocabulary="MedDRA", version="28.0",
        license="MSSO 구독 계약 필요 · 재배포 금지",
        obtain="meddra.org 구독 후 내려받기(영문·한글 판 별도)",
        source="MedDRA/MedDRA_28_0_ENglish_unlock.zip",
        source_ko="MedDRA/MedDRA_28_0_Korean_unlock.zip",
        code="PT 코드(8자리)", label="PT 용어",
        note="LLT 가 아니라 PT 수준으로 받는다. 한글 표기는 한글 판의 같은 코드에서 온다."),
    "REF_EDI_PROCEDURE": dict(
        kor="건강보험 행위(수술·처치) 코드", vocabulary="EDI", version="2025 고시",
        license="공개(공공데이터)",
        obtain="심평원 요양급여비용 마스터(data.go.kr)",
        source="EDI/hira_edi_ultimate_codemaster/data/processed/current/csv/procedures_의치과_급여.csv",
        code="code", label="name_kr",
        note="원본의 수술여부 열(surgery_flag)은 0/9 두 값만 쓰는데 9 가 전체의 76%%라 '수술=9' 로 읽으면 안 된다 — 심평원 서식 설명서와 대조해 뜻을 확정한 뒤 수술명 필드에서 거를 것. 비급여·한방 파일은 같은 자리에 따로 있다."),
    "REF_EDI_DRUG": dict(
        kor="건강보험 약제 코드", vocabulary="EDI", version="2025-10-31",
        license="공개(공공데이터)",
        obtain="심평원 약가마스터(data.go.kr)",
        source="EDI/hira_edi_ultimate_codemaster/data/processed/current/csv/drugs.csv",
        code="full_kd_code", label="product_name_kr",
        note="DRUG_EXPOSURE.drug_concept_id 가 가리키는 표. atc_code 열로 ATC 와 이어진다."),
    "REF_KCD": dict(
        kor="한국표준질병사인분류(KCD)", vocabulary="KCD", version="8차",
        license="공개",
        obtain="통계청 KOSIS · 심평원 상병마스터",
        source="EDI/hira_edi_ultimate_codemaster/data/processed/current/csv/diseases.csv",
        code="sick_code", label="name_kr",
        note="가족력 등 KCD 로 받는 진단명에 쓴다."),
    "REF_SNOMED_PROCEDURE": dict(
        kor="SNOMED CT 시술", vocabulary="SNOMED", version="2026-09-01",
        license="SNOMED International 회원국 라이선스 · 재배포 제한",
        obtain="KOSTOM/보건의료정보원 배포본 또는 MLDS",
        source=None, ecl="<<71388002",
        code="concept_id", label="FSN",
        note="EDI 행위코드와 함께 쓴다(청구는 EDI, 의미는 SNOMED). 로컬 원본이 없으면 "
             "용어 서버(snowstorm MCP)로 ECL 을 펼쳐 만든다."),
    "REF_SNOMED_MORPHOLOGY": dict(
        kor="SNOMED CT 조직형", vocabulary="SNOMED", version="2026-09-01",
        license="SNOMED International 회원국 라이선스 · 재배포 제한",
        obtain="위와 같음", source=None, ecl="<<108369006",
        code="concept_id", label="FSN",
        note="조직학적 진단명 계열 필드가 가리킨다. 2.1 에서 값 집합으로 올린 조직형도 이 하위다."),
    "REF_SNOMED_NEOPLASM": dict(
        kor="SNOMED CT 신생물 진단", vocabulary="SNOMED", version="2026-09-01",
        license="SNOMED International 회원국 라이선스 · 재배포 제한",
        obtain="위와 같음", source=None, ecl="<<363346000",
        code="concept_id", label="FSN", note="가족력의 암종처럼 진단명으로 받는 필드가 가리킨다."),
    "REF_SNOMED_DISORDER": dict(
        kor="SNOMED CT 질환", vocabulary="SNOMED", version="2026-09-01",
        license="SNOMED International 회원국 라이선스 · 재배포 제한",
        obtain="위와 같음", source=None, ecl="<<64572001",
        code="concept_id", label="FSN", note="암종 외 가족 질환처럼 범위가 넓은 진단명 필드가 가리킨다."),
    "REF_LOINC": dict(
        kor="LOINC 검사 항목", vocabulary="LOINC", version="2.80",
        license="무료(사용자 등록 필요)", obtain="loinc.org 등록 후 내려받기",
        source="LOINC/Loinc_2.80/LoincTableCore/LoincTableCore.csv",
        code="LOINC_NUM", label="LONG_COMMON_NAME",
        note="2.1 에서 개별 검사값에 부여한 LOINC 코드와 같은 표다."),
    "REF_HGNC_GENE": dict(
        kor="HGNC 유전자 기호", vocabulary="HGNC", version="수시 갱신",
        license="공개(EMBL-EBI, 자유 이용)",
        obtain="genenames.org 의 complete set(tsv)",
        source=None, url="https://storage.googleapis.com/public-download-files/hgnc/tsv/tsv/hgnc_complete_set.txt",
        code="hgnc_id", label="symbol",
        note="변이검사 유전자 종류 필드가 가리킨다. 변이 표기 자체는 HGVS 문법을 따르며 표가 아니다."),
    "REF_HEMONC_REGIMEN": dict(
        kor="HemOnc 항암요법 레지멘", vocabulary="HemOnc", version="수시 갱신",
        license="공개(CC BY 4.0)", obtain="hemonc.org 내려받기 또는 OHDSI HemOnc 어휘",
        source=None,
        code="concept_code", label="regimen name",
        note="국내에서만 쓰는 레지멘은 HemOnc 에 없어 자체 어휘로 받는다(regimen_source_value 에 원문 보관)."),
}

# 필드 -> 참조표. 한 필드가 여러 표를 가리킬 수 있다(청구용·의미용을 함께 받는 경우).
FIELD_REFERENCES = {
    ("ADVERSE_EVENT", "adverse_event_concept_id"): ["REF_MEDDRA_PT"],
    ("SURGERY", "surgery_name"): ["REF_EDI_PROCEDURE", "REF_SNOMED_PROCEDURE"],
    ("SURGERY", "stoma_reversal_name"): ["REF_EDI_PROCEDURE", "REF_SNOMED_PROCEDURE"],
    ("RADIOTHERAPY", "rt_name"): ["REF_EDI_PROCEDURE", "REF_SNOMED_PROCEDURE"],
    ("ANTP_THERAPY", "regimen"): ["REF_HEMONC_REGIMEN"],
    ("PATHOLOGY_REPORT", "biopsy_histologic_diagnosis"): ["REF_SNOMED_MORPHOLOGY"],
    ("PATHOLOGY_REPORT", "surgical_histologic_diagnosis"): ["REF_SNOMED_MORPHOLOGY"],
    ("PATHOLOGY_REPORT", "primary_histology"): ["REF_SNOMED_MORPHOLOGY"],
    ("PATHOLOGY_REPORT", "liver_fibrosis_grade_name"): ["REF_SNOMED_DISORDER"],
    ("FAMILY_HISTORY", "family_cancer_type"): ["REF_SNOMED_NEOPLASM"],
    ("FAMILY_HISTORY", "family_disease"): ["REF_SNOMED_DISORDER", "REF_KCD"],
    ("BIOMARKER", "mutation_test_gene"): ["REF_HGNC_GENE"],
    ("BIOMARKER", "germline_test_gene"): ["REF_HGNC_GENE"],
    ("BIOMARKER", "flow_cytometry_summary"): ["REF_LOINC", "REF_SNOMED_DISORDER"],
}

# 필드는 아니지만 저장 테이블이 직접 가리키는 표.
TABLE_REFERENCES = {("DRUG_EXPOSURE", "drug_concept_id"): ["REF_EDI_DRUG"]}
