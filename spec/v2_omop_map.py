# -*- coding: utf-8 -*-
"""사전 v2 · 저장 모델(OMOP CDM 5.4 + Oncology 구조), K-AI 어휘 씨앗, CRF 서식 → 레코드 매핑 규칙.

- 저장 테이블은 OMOP 5.4 의 이름과 컬럼을 그대로 쓴다. 단 concept_id 는 K-AI 어휘(64비트, 10,000,000,000~)다.
- CRF 서식은 병원이 채우는 입력 단위이고, 앱이 FORM_MAP 규칙으로 저장 테이블 레코드를 만든다.
"""

CONCEPT_ID_BASE = 10_000_000_000

# ---------------------------------------------------------------- OMOP 5.4 저장 테이블 (필수 컬럼 부분집합)
# (컬럼, 타입, 필수, 설명)
OMOP_TABLES = {
    "PERSON": ("환자", "환자 1", "person_id", [
        ("person_id", "bigint", True, "환자 고유키(가명)"), ("gender_concept_id", "bigint", True, "성별 concept"), ("year_of_birth", "integer", True, "출생 연도"),
        ("month_of_birth", "integer", False, ""), ("day_of_birth", "integer", False, ""), ("care_site_id", "bigint", False, "기관"),
        ("gender_source_value", "varchar", False, "원천 성별값")]),
    "OBSERVATION_PERIOD": ("관찰 기간", "환자 × 기간", "observation_period_id", [
        ("observation_period_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("observation_period_start_date", "date", True, "관찰 시작(코호트 진입일 또는 첫 방문)"),
        ("observation_period_end_date", "date", True, "관찰 종료(최종 추적일·사망일)"), ("period_type_concept_id", "bigint", True, "출처 type")]),
    "DEATH": ("사망", "환자 1", "person_id", [
        ("person_id", "bigint", True, ""), ("death_date", "date", True, "사망일"), ("death_type_concept_id", "bigint", True, "출처 type"),
        ("cause_concept_id", "bigint", False, "사망 원인 concept"), ("cause_source_value", "varchar", False, "원천 사망 원인(KCD 등)")]),
    "VISIT_OCCURRENCE": ("방문", "방문 1", "visit_occurrence_id", [
        ("visit_occurrence_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("visit_concept_id", "bigint", True, "입원/외래/응급"),
        ("visit_start_date", "date", True, "입원일·방문일"), ("visit_end_date", "date", True, "퇴원일·방문일"), ("visit_type_concept_id", "bigint", True, ""),
        ("discharge_to_concept_id", "bigint", False, "퇴원 시 상태"), ("visit_source_value", "varchar", False, "")]),
    "CONDITION_OCCURRENCE": ("진단", "진단 1", "condition_occurrence_id", [
        ("condition_occurrence_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("condition_concept_id", "bigint", True, "진단 concept(SNOMED/KCD 매핑)"),
        ("condition_start_date", "date", True, ""), ("condition_end_date", "date", False, ""), ("condition_type_concept_id", "bigint", True, "EHR/Registry"),
        ("condition_status_concept_id", "bigint", False, "주진단·과거력·합병증 등"), ("visit_occurrence_id", "bigint", False, ""), ("condition_source_value", "varchar", False, "원천 코드(KCD·MedDRA)")]),
    "PROCEDURE_OCCURRENCE": ("시술·검사 시행", "시술 1", "procedure_occurrence_id", [
        ("procedure_occurrence_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("procedure_concept_id", "bigint", True, "시술 concept(EDI/SNOMED 매핑)"),
        ("procedure_date", "date", True, ""), ("procedure_end_date", "date", False, "방사선 코스 종료일 등"), ("procedure_type_concept_id", "bigint", True, ""),
        ("modifier_concept_id", "bigint", False, "접근법(개복/복강경/로봇) 등"), ("quantity", "integer", False, "횟수(방사선 분할 등)"),
        ("visit_occurrence_id", "bigint", False, ""), ("procedure_source_value", "varchar", False, "원천 코드")]),
    "DRUG_EXPOSURE": ("약물", "처방 1", "drug_exposure_id", [
        ("drug_exposure_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("drug_concept_id", "bigint", True, "약제 concept(국내 약물코드 매핑)"),
        ("drug_exposure_start_date", "date", True, ""), ("drug_exposure_end_date", "date", False, ""), ("drug_type_concept_id", "bigint", True, ""),
        ("quantity", "float", False, ""), ("days_supply", "integer", False, ""), ("dose_unit_source_value", "varchar", False, ""), ("route_concept_id", "bigint", False, ""),
        ("visit_occurrence_id", "bigint", False, ""), ("drug_source_value", "varchar", False, "")]),
    "MEASUREMENT": ("검사값·수식자", "검사 × 시점", "measurement_id", [
        ("measurement_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("measurement_concept_id", "bigint", True, "검사·수식자 concept(LOINC/Cancer Modifier/K-AI)"),
        ("measurement_date", "date", True, ""), ("measurement_type_concept_id", "bigint", True, ""), ("operator_concept_id", "bigint", False, ""),
        ("value_as_number", "float", False, "수치"), ("value_as_concept_id", "bigint", False, "범주값 concept(병기군·등급·반응 등)"), ("unit_concept_id", "bigint", False, "UCUM"),
        ("range_low", "float", False, ""), ("range_high", "float", False, ""), ("visit_occurrence_id", "bigint", False, ""),
        ("measurement_source_value", "varchar", False, "원천 검사명"), ("value_source_value", "varchar", False, "원천 값(라벨·코드)"),
        ("measurement_event_id", "bigint", False, "수식 대상 레코드(진단·에피소드·시술)"), ("meas_event_field_concept_id", "bigint", False, "수식 대상 테이블·컬럼 concept")]),
    "OBSERVATION": ("관찰", "관찰 1", "observation_id", [
        ("observation_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("observation_concept_id", "bigint", True, "관찰 항목 concept"),
        ("observation_date", "date", True, ""), ("observation_type_concept_id", "bigint", True, ""), ("value_as_number", "float", False, ""),
        ("value_as_string", "varchar", False, ""), ("value_as_concept_id", "bigint", False, ""), ("qualifier_concept_id", "bigint", False, "가족 관계 등 한정자"),
        ("unit_concept_id", "bigint", False, ""), ("visit_occurrence_id", "bigint", False, ""), ("observation_source_value", "varchar", False, ""),
        ("value_source_value", "varchar", False, ""), ("observation_event_id", "bigint", False, "관련 레코드"), ("obs_event_field_concept_id", "bigint", False, "")]),
    "NOTE": ("판독문·기록", "기록 1", "note_id", [
        ("note_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("note_date", "date", True, ""), ("note_type_concept_id", "bigint", True, ""),
        ("note_class_concept_id", "bigint", True, "판독문·병리·경과기록"), ("note_title", "varchar", False, ""), ("note_text", "text", True, ""),
        ("encoding_concept_id", "bigint", True, ""), ("language_concept_id", "bigint", True, ""), ("visit_occurrence_id", "bigint", False, ""),
        ("note_event_id", "bigint", False, "관련 레코드(검체·시술)"), ("note_event_field_concept_id", "bigint", False, "")]),
    "SPECIMEN": ("검체", "검체 1", "specimen_id", [
        ("specimen_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("specimen_concept_id", "bigint", True, "검체 종류(생검·절제)"),
        ("specimen_type_concept_id", "bigint", True, ""), ("specimen_date", "date", True, "채취일"), ("quantity", "float", False, ""), ("unit_concept_id", "bigint", False, ""),
        ("anatomic_site_concept_id", "bigint", False, "채취 부위"), ("disease_status_concept_id", "bigint", False, ""), ("specimen_source_id", "varchar", False, "병리 번호"),
        ("specimen_source_value", "varchar", False, ""), ("anatomic_site_source_value", "varchar", False, "")]),
    "COHORT": ("코호트 진입", "환자 × 코호트", "cohort_definition_id+subject_id+cohort_start_date", [
        ("cohort_definition_id", "bigint", True, "코호트 concept(폐암 코호트 등)"), ("subject_id", "bigint", True, "person_id"),
        ("cohort_start_date", "date", True, "코호트 진입일(index date)"), ("cohort_end_date", "date", True, "종료일(최종 추적·사망), 미정이면 진입일")]),
    "EPISODE": ("에피소드", "에피소드 1", "episode_id", [
        ("episode_id", "bigint", True, ""), ("person_id", "bigint", True, ""), ("episode_concept_id", "bigint", True, "질환 에피소드/재발/관해/치료 레지멘/치료 사이클"),
        ("episode_start_date", "date", True, ""), ("episode_end_date", "date", False, ""), ("episode_parent_id", "bigint", False, "상위 에피소드(질환 ← 레지멘 ← 사이클)"),
        ("episode_number", "integer", False, "line 번호·사이클 번호"), ("episode_object_concept_id", "bigint", True, "대상(질환 concept·레지멘 concept·재발 부위)"),
        ("episode_type_concept_id", "bigint", True, ""), ("episode_source_value", "varchar", False, "원천 레지멘명 등")]),
    "EPISODE_EVENT": ("에피소드 연결", "에피소드 × 레코드", "episode_id+event_id+episode_event_field_concept_id", [
        ("episode_id", "bigint", True, ""), ("event_id", "bigint", True, "연결 레코드 id"), ("episode_event_field_concept_id", "bigint", True, "연결 레코드의 테이블·컬럼 concept")]),
}

# ---------------------------------------------------------------- 어휘 씨앗 (K-AI 메타 concept)
# key → (한글, 영문, domain, vocabulary, class, code, standard)
SEED_CONCEPTS = {
    # type concept
    "TYPE_REGISTRY": ("등록 서식 입력", "Registry (CRF entry)", "Type Concept", "KAI", "Type", "KAI-TYPE-REG", "S"),
    "TYPE_EHR": ("전자의무기록", "EHR", "Type Concept", "KAI", "Type", "KAI-TYPE-EHR", "S"),
    "TYPE_DERIVED": ("파생", "Derived", "Type Concept", "KAI", "Type", "KAI-TYPE-DRV", "S"),
    # episode concept
    "EP_DISEASE": ("질환 에피소드", "Disease Episode", "Episode", "KAI", "Episode", "KAI-EP-DIS", "S"),
    "EP_FIRST": ("질환 최초 발생", "Disease First Occurrence", "Episode", "KAI", "Episode", "KAI-EP-FIRST", "S"),
    "EP_RECURRENCE": ("질환 재발·진행", "Disease Recurrence/Progression", "Episode", "KAI", "Episode", "KAI-EP-REC", "S"),
    "EP_REMISSION": ("관해", "Disease Remission", "Episode", "KAI", "Episode", "KAI-EP-REM", "S"),
    "EP_REGIMEN": ("치료 레지멘", "Treatment Regimen", "Episode", "KAI", "Episode", "KAI-EP-REG", "S"),
    "EP_CYCLE": ("치료 사이클", "Treatment Cycle", "Episode", "KAI", "Episode", "KAI-EP-CYC", "S"),
    # 연결 대상 테이블·컬럼 (field concept)
    "F_CONDITION": ("CONDITION_OCCURRENCE.condition_occurrence_id", "condition_occurrence.condition_occurrence_id", "Metadata", "KAI", "Field", "KAI-F-COND", "S"),
    "F_PROCEDURE": ("PROCEDURE_OCCURRENCE.procedure_occurrence_id", "procedure_occurrence.procedure_occurrence_id", "Metadata", "KAI", "Field", "KAI-F-PROC", "S"),
    "F_DRUG": ("DRUG_EXPOSURE.drug_exposure_id", "drug_exposure.drug_exposure_id", "Metadata", "KAI", "Field", "KAI-F-DRUG", "S"),
    "F_MEASUREMENT": ("MEASUREMENT.measurement_id", "measurement.measurement_id", "Metadata", "KAI", "Field", "KAI-F-MEAS", "S"),
    "F_EPISODE": ("EPISODE.episode_id", "episode.episode_id", "Metadata", "KAI", "Field", "KAI-F-EPI", "S"),
    "F_SPECIMEN": ("SPECIMEN.specimen_id", "specimen.specimen_id", "Metadata", "KAI", "Field", "KAI-F-SPEC", "S"),
    "F_OBSERVATION": ("OBSERVATION.observation_id", "observation.observation_id", "Metadata", "KAI", "Field", "KAI-F-OBS", "S"),
    # 방문·성별·검체 등 최소 표준값 (SNOMED/OMOP 코드 보관)
    "GENDER_M": ("남성", "Male", "Gender", "SNOMED", "Gender", "248153007", "S"), "GENDER_F": ("여성", "Female", "Gender", "SNOMED", "Gender", "248152002", "S"),
    "VISIT_INPATIENT": ("입원", "Inpatient visit", "Visit", "KAI", "Visit", "KAI-VISIT-IP", "S"), "VISIT_OUTPATIENT": ("외래", "Outpatient visit", "Visit", "KAI", "Visit", "KAI-VISIT-OP", "S"),
    "VISIT_ER": ("응급", "Emergency room visit", "Visit", "KAI", "Visit", "KAI-VISIT-ER", "S"),
    "SPEC_BIOPSY": ("생검 검체", "Biopsy specimen", "Specimen", "SNOMED", "Specimen", "258415003", "S"), "SPEC_RESECTION": ("절제 검체", "Resection specimen", "Specimen", "KAI", "Specimen", "KAI-SPEC-RES", "S"),
    # 코호트 정의
    "COHORT_LUNG_CANCER": ("폐암 코호트", "K-AI lung cancer cohort", "Cohort", "KAI", "Cohort", "KAI-COH-LC", "S"), "COHORT_BREAST_CANCER": ("유방암 코호트", "K-AI breast cancer cohort", "Cohort", "KAI", "Cohort", "KAI-COH-BC", "S"),
    "COHORT_COLORECTAL_CANCER": ("대장암 코호트", "K-AI colorectal cancer cohort", "Cohort", "KAI", "Cohort", "KAI-COH-CRC", "S"), "COHORT_MASLD": ("대사이상지방간 코호트", "K-AI MASLD cohort", "Cohort", "KAI", "Cohort", "KAI-COH-MASLD", "S"),
    "COHORT_DIABETES": ("당뇨병 코호트", "K-AI diabetes cohort", "Cohort", "KAI", "Cohort", "KAI-COH-DM", "S"), "COHORT_LYMPHOMA": ("림프종 코호트", "K-AI lymphoma cohort", "Cohort", "KAI", "Cohort", "KAI-COH-LY", "S"),
    # 코호트 정의 진단 (v1 concepts.yaml 의 대표 concept 을 대체)
    "DX_LUNG_CANCER": ("폐의 악성 신생물", "Malignant neoplasm of lung", "Condition", "SNOMED", "Disorder", "363358000", "S"),
    "DX_BREAST_CANCER": ("유방의 악성 신생물", "Malignant neoplasm of breast", "Condition", "SNOMED", "Disorder", "254837009", "S"),
    "DX_COLORECTAL_CANCER": ("대장·직장의 악성 신생물", "Malignant neoplasm of colorectum", "Condition", "SNOMED", "Disorder", "781382000", "S"),
    "DX_MASLD": ("대사이상 관련 지방간질환", "Metabolic dysfunction-associated steatotic liver disease", "Condition", "KAI", "Disorder", "KAI-DX-MASLD", "S"),
    "DX_DIABETES": ("제2형 당뇨병", "Type 2 diabetes mellitus", "Condition", "SNOMED", "Disorder", "44054006", "S"),
    "DX_LYMPHOMA": ("악성 림프종", "Malignant lymphoma", "Condition", "SNOMED", "Disorder", "118600007", "S"),
    # 관계
    "REL_MAPS_TO": ("표준 매핑", "Maps to", "Relationship", "KAI", "Relationship", "KAI-REL-MAPS", "S"),
    "REL_IS_A": ("상위 개념", "Is a", "Relationship", "KAI", "Relationship", "KAI-REL-ISA", "S"),
    "REL_HAS_UNIT": ("단위", "Has unit", "Relationship", "KAI", "Relationship", "KAI-REL-UNIT", "S"),
    "REL_MEMBER_OF": ("값 집합 소속", "Member of concept set", "Relationship", "KAI", "Relationship", "KAI-REL-MEMBER", "S"),
}
COHORT_DX = {"LUNG_CANCER": "DX_LUNG_CANCER", "BREAST_CANCER": "DX_BREAST_CANCER", "COLORECTAL_CANCER": "DX_COLORECTAL_CANCER", "MASLD": "DX_MASLD", "DIABETES": "DX_DIABETES", "LYMPHOMA": "DX_LYMPHOMA"}

# ---------------------------------------------------------------- CRF 서식 → 레코드 매핑 규칙
# anchor: 서식 한 행이 만드는 기준 레코드. columns 의 값은 "$필드" (서식 값), "@KEY" (씨앗 concept), "#ref" (같은 행의 다른 레코드 id), 상수.
# attr_default: 나머지 필드가 만드는 속성 레코드의 기본 테이블. 속성 레코드는 concept = 필드 concept, 값은 종류에 따라 value_as_number / value_as_concept_id / value_as_string,
#               날짜 = date_field, *_event_id = anchor ref, *_event_field_concept_id = anchor 테이블의 field concept.
# overrides: 필드별 예외. table, role(anchor_column | attr | skip | episode), 추가 컬럼.
FORM_MAP = {
    "COHORT_INDEX": dict(
        kor="코호트 인덱스 서식", date_field="index_date",
        anchors=[
            dict(ref="COHORT", table="COHORT", columns={"cohort_definition_id": "@COHORT_{cohort}", "subject_id": "$person_id", "cohort_start_date": "$index_date", "cohort_end_date": "$last_followup_date|$index_date"}),
            dict(ref="OP", table="OBSERVATION_PERIOD", columns={"person_id": "$person_id", "observation_period_start_date": "$index_date", "observation_period_end_date": "$last_followup_date|$index_date", "period_type_concept_id": "@TYPE_REGISTRY"}),
            dict(ref="DX", table="CONDITION_OCCURRENCE", columns={"person_id": "$person_id", "condition_concept_id": "@DX_{cohort}", "condition_start_date": "$diagnosis_registered_date|$first_diagnosis_date|$index_date", "condition_type_concept_id": "@TYPE_REGISTRY", "condition_source_value": "$diagnosis_name"}),
            dict(ref="EP", table="EPISODE", columns={"person_id": "$person_id", "episode_concept_id": "@EP_DISEASE", "episode_start_date": "$first_diagnosis_date|$index_date", "episode_end_date": "$last_followup_date", "episode_number": 1, "episode_object_concept_id": "@DX_{cohort}", "episode_type_concept_id": "@TYPE_REGISTRY"}),
            dict(ref="EPEV", table="EPISODE_EVENT", columns={"episode_id": "#EP", "event_id": "#DX", "episode_event_field_concept_id": "@F_CONDITION"}),
        ],
        attr_default="OBSERVATION", link=("DX", "F_CONDITION"),
        skip=["person_id", "index_date", "diagnosis_registered_date", "diagnosis_name", "first_diagnosis_date"],
    ),
    "STAGING": dict(
        kor="진단·병기 평가 서식", date_field="staging_date", anchors=[], attr_default="MEASUREMENT", link=("DX", "F_CONDITION"),
        skip=["person_id", "staging_date", "staging_id", "visit_occurrence_id"],
        overrides={"distant_metastasis_date": dict(role="attr", table="OBSERVATION"), "stage_iv_diagnosis_date": dict(role="episode", concept="EP_RECURRENCE", start="$stage_iv_diagnosis_date", parent="#EP", object="@DX_{cohort}")},
    ),
    "ANTP_THERAPY": dict(
        kor="항암·전신치료 서식", date_field="antp_start_date",
        anchors=[dict(ref="REG", table="EPISODE", columns={"person_id": "$person_id", "episode_concept_id": "@EP_REGIMEN", "episode_start_date": "$antp_start_date", "episode_end_date": "$antp_end_date", "episode_parent_id": "#EP", "episode_number": "$regimen_or_line_of_therapy", "episode_object_concept_id": "$regimen:concept", "episode_type_concept_id": "@TYPE_REGISTRY", "episode_source_value": "$regimen_source_value|$regimen"})],
        attr_default="OBSERVATION", link=("REG", "F_EPISODE"),
        skip=["person_id", "antp_id", "antp_start_date", "antp_end_date", "regimen", "regimen_source_value", "regimen_or_line_of_therapy"],
        links=[dict(table="EPISODE_EVENT", columns={"episode_id": "#REG", "event_id": "DRUG_EXPOSURE.drug_exposure_id where antp_id = $antp_id", "episode_event_field_concept_id": "@F_DRUG"}, note="연결된 약물마다 한 행")],
    ),
    "RESPONSE_ASSESSMENT": dict(
        kor="반응·경과 평가 서식", date_field="response_assessment_date", anchors=[], attr_default="MEASUREMENT", link=("REG|EP", "F_EPISODE"),
        skip=["person_id", "response_id", "response_assessment_date", "visit_occurrence_id"],
        overrides={"recurrence_date": dict(role="episode", concept="EP_RECURRENCE", start="$recurrence_date", parent="#EP", object="$recurrence_site:concept|@DX_{cohort}"), "recurrence_site": dict(role="skip")},
    ),
    "SURGERY": dict(
        kor="수술 서식", date_field="surgery_date",
        anchors=[dict(ref="PROC", table="PROCEDURE_OCCURRENCE", columns={"person_id": "$person_id", "procedure_concept_id": "$surgery_name:concept", "procedure_date": "$surgery_date", "procedure_type_concept_id": "@TYPE_REGISTRY", "modifier_concept_id": "$surgery_approach:concept", "visit_occurrence_id": "$visit_occurrence_id", "procedure_source_value": "$surgery_name"}),
                 dict(ref="EPEV", table="EPISODE_EVENT", columns={"episode_id": "#EP", "event_id": "#PROC", "episode_event_field_concept_id": "@F_PROCEDURE"})],
        attr_default="OBSERVATION", link=("PROC", "F_PROCEDURE"),
        skip=["person_id", "surgery_id", "surgery_date", "surgery_name", "surgery_approach", "visit_occurrence_id", "procedure_occurrence_id"],
        overrides={"ebl_ml": dict(role="attr", table="MEASUREMENT")},
    ),
    "RADIOTHERAPY": dict(
        kor="방사선치료 서식", date_field="rt_start_date",
        anchors=[dict(ref="PROC", table="PROCEDURE_OCCURRENCE", columns={"person_id": "$person_id", "procedure_concept_id": "$rt_name:concept", "procedure_date": "$rt_start_date", "procedure_end_date": "$rt_end_date", "procedure_type_concept_id": "@TYPE_REGISTRY", "quantity": "$rt_fractions", "procedure_source_value": "$rt_name"}),
                 dict(ref="EPEV", table="EPISODE_EVENT", columns={"episode_id": "#EP", "event_id": "#PROC", "episode_event_field_concept_id": "@F_PROCEDURE"})],
        attr_default="MEASUREMENT", link=("PROC", "F_PROCEDURE"),
        skip=["person_id", "radiotherapy_id", "rt_start_date", "rt_end_date", "rt_name", "rt_fractions", "visit_occurrence_id", "procedure_occurrence_id"],
        overrides={"rt_purpose": dict(role="attr", table="OBSERVATION"), "rt_site": dict(role="attr", table="OBSERVATION"), "rt_yn": dict(role="skip"), "rt_prescription_date": dict(role="attr", table="OBSERVATION")},
    ),
    "ADVERSE_EVENT": dict(
        kor="이상사례 서식", date_field="adverse_event_start_date",
        anchors=[dict(ref="AE", table="CONDITION_OCCURRENCE", columns={"person_id": "$person_id", "condition_concept_id": "$adverse_event_concept_id:concept", "condition_start_date": "$adverse_event_start_date", "condition_type_concept_id": "@TYPE_REGISTRY", "condition_status_concept_id": "@AE_STATUS", "visit_occurrence_id": "$visit_occurrence_id", "condition_source_value": "$adverse_event_source_value"}),
                 dict(ref="EPEV", table="EPISODE_EVENT", columns={"episode_id": "#REG(antp_id)", "event_id": "#AE", "episode_event_field_concept_id": "@F_CONDITION"})],
        attr_default="OBSERVATION", link=("AE", "F_CONDITION"),
        skip=["person_id", "adverse_event_id", "adverse_event_start_date", "adverse_event_concept_id", "adverse_event_type_concept_id", "visit_occurrence_id", "antp_id", "observation_id", "condition_occurrence_id", "measurement_id", "procedure_occurrence_id", "drug_exposure_id", "note_id"],
        overrides={"severity_concept_id": dict(role="attr", table="MEASUREMENT", concept="CTCAE_GRADE")},
    ),
    "FAMILY_HISTORY": dict(
        kor="가족력 서식", date_field="index_date",
        anchors=[dict(ref="FH", table="OBSERVATION", columns={"person_id": "$person_id", "observation_concept_id": "@FAMILY_HISTORY_OF", "observation_date": "$record_date|$index_date", "observation_type_concept_id": "@TYPE_REGISTRY", "value_as_concept_id": "$family_cancer_type:concept|$family_disease:concept", "qualifier_concept_id": "$family_relation:concept", "value_as_number": "$family_member_age_at_diagnosis", "value_source_value": "$family_cancer_type"})],
        attr_default="OBSERVATION", link=("FH", "F_OBSERVATION"),
        skip=["person_id", "family_history_id", "family_relation", "family_cancer_type", "family_history_yn", "family_cancer_yn", "family_liver_disease_yn", "family_diabetes_yn"],
    ),
}
EXTRA_SEEDS = {
    "AE_STATUS": ("이상사례", "Adverse event (condition status)", "Condition Status", "KAI", "Status", "KAI-STAT-AE", "S"),
    "FAMILY_HISTORY_OF": ("가족력", "Family history of disorder", "Observation", "SNOMED", "Finding", "281666001", "S"),
    "CTCAE_GRADE": ("CTCAE 등급", "CTCAE grade", "Measurement", "KAI", "Grade scale", "KAI-CTCAE-GRADE", "S"),
}
SEED_CONCEPTS.update(EXTRA_SEEDS)

# 확장 테이블(K-AI 고유)에서 그대로 저장되는 서식 (서식 = 테이블). 닫힌 범주 필드는 <name>_concept_id + <name>_source_value 쌍으로 저장.
EXTENSION_FORMS = ["PATHOLOGY_REPORT", "PATHOLOGY_TUMOR", "BIOMARKER"]
