# 사전 v2 변환 보고서 (2026-09-12)

입력: `internal/decisions/배치표_v0_20260912.xlsx` · 출력: `spec/v2/`

## 규모

| 구분 | 수 |
|---|---|
| 테이블 | 33 (코어 9, 공통 확장 11, 질환 확장 13) |
| 필드 | 548 (필수 388, 권고 128, 보류 32) |
| 코어 파생 변수 | 120 |
| 파생 점수 | 29 |
| 코드표 | 91 (값 미정의 자리 54) |
| v1 미승격 필드 | 575 |

## 테이블

| 테이블 | 층 | 행 단위 | 필드 | 코호트 |
|---|---|---|---|---|
| PERSON | 코어 | 환자 1 | 8 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| DEATH | 코어 | 환자 1 | 5 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| VISIT_OCCURRENCE | 코어 | 방문 1 | 7 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| CONDITION_OCCURRENCE | 코어 | 진단 1 | 6 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| PROCEDURE_OCCURRENCE | 코어 | 시술 1 | 6 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| DRUG_EXPOSURE | 코어 | 처방 1 | 19 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| MEASUREMENT | 코어 | 검사 × 시점 | 13 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| OBSERVATION | 코어 | 관찰 1 | 9 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| NOTE | 코어 | 기록 1 | 7 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| COHORT_INDEX | 공통 확장 | 환자 1 | 18 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| STAGING | 공통 확장 | 환자 × 판정 시점 × 체계 | 33 | 유방암, 대장암, 폐암, 림프종 |
| PATHOLOGY_REPORT | 공통 확장 | 검체(보고서) 1 | 54 | 유방암, 대장암, 폐암, 림프종, 대사이상지방간 |
| PATHOLOGY_TUMOR | 공통 확장 | 종양 1 | 8 | 유방암, 대장암, 폐암 |
| BIOMARKER | 공통 확장 | 검사 × 마커 | 67 | 유방암, 대장암, 당뇨병, 폐암, 림프종 |
| SURGERY | 공통 확장 | 수술 1 | 16 | 유방암, 대장암, 폐암, 대사이상지방간 |
| RADIOTHERAPY | 공통 확장 | 치료 코스 1 | 13 | 유방암, 대장암, 폐암, 림프종 |
| ANTP_THERAPY | 공통 확장 | 요법 에피소드 1 | 20 | 유방암, 대장암, 폐암, 림프종 |
| RESPONSE_ASSESSMENT | 공통 확장 | 평가 1 | 24 | 유방암, 대장암, 폐암, 림프종 |
| ADVERSE_EVENT | 공통 확장 | 사건 1 | 22 | 유방암, 대장암, 당뇨병, 폐암, 림프종, 대사이상지방간 |
| FAMILY_HISTORY | 공통 확장 | 환자 × 관계 × 질환 | 8 | 유방암, 대장암, 당뇨병, 폐암, 대사이상지방간 |
| LUNG_EXAM | 질환 확장 | 검사 1 | 9 | 폐암 |
| BREAST_BASELINE | 질환 확장 | 환자 1 | 30 | 유방암 |
| BREAST_EXAM | 질환 확장 | 검사 1 | 7 | 유방암 |
| COLORECTAL_EXAM | 질환 확장 | 검사 1 | 18 | 대장암 |
| COLORECTAL_SURGERY_DETAIL | 질환 확장 | 수술 1 (SURGERY 자식) | 17 | 대장암 |
| MASLD_EXAM | 질환 확장 | 검사 1 | 12 | 대사이상지방간 |
| MASLD_ASSESSMENT | 질환 확장 | 평가 1 | 14 | 대사이상지방간 |
| MASLD_EVENT | 질환 확장 | 사건 1 | 11 | 대사이상지방간 |
| DIABETES_BASELINE | 질환 확장 | 환자 1 | 6 | 당뇨병 |
| DIABETES_EVENT | 질환 확장 | 사건 1 | 16 | 당뇨병 |
| LYMPHOMA_ASSESSMENT | 질환 확장 | 평가 1 | 20 | 림프종 |
| LYMPHOMA_EVENT | 질환 확장 | 사건 1 | 16 | 림프종 |
| LYMPHOMA_EXAM | 질환 확장 | 검사 1 | 9 | 림프종 |

## v1 미승격 필드 (목적지별)

자문 항목과 이름이 합쳐지지 않은 v1 '이동'·'이관' 필드입니다. 필드의 `v1_hint` 는 배치표의 휴리스틱 대응이므로 참고용입니다. 승격(필드 추가)·폐기 여부를 정합니다. 상세는 `legacy_fields_v2.yaml`, 사전 엑셀 'v1 미승격 필드' 시트.

- PATHOLOGY_REPORT: 172개
- SURGERY: 91개
- BIOMARKER: 77개
- CONDITION_OCCURRENCE: 45개
- MEASUREMENT: 32개
- FAMILY_HISTORY: 28개
- DRUG_EXPOSURE: 25개
- STAGING: 21개
- BREAST_CRF: 17개
- RADIOTHERAPY: 14개
- RESPONSE_ASSESSMENT: 12개
- ANTP_THERAPY: 10개
- LYMPHOMA_CRF: 7개
- OBSERVATION: 5개
- LUNG_CRF: 4개
- PROCEDURE_OCCURRENCE: 3개
- VISIT_OCCURRENCE: 3개
- ADVERSE_EVENT: 3개
- COLORECTAL_CRF: 3개
- MASLD_CRF: 2개
- DEATH: 1개

## 값 집합이 비어 있는 코드표 (2.1 에서 채움)

CL_ADENOCARCINOMA_PREDOMINANT_SUBTYPE, CL_ANASTOMOSIS_METHOD, CL_BALLOONING_GRADE, CL_BIOPSY_ADEQUACY, CL_BIOPSY_DIFFERENTIATION, CL_BIOPSY_LATERALITY, CL_BIOPSY_METHOD, CL_BIOPSY_SITE, CL_BIOPSY_SITE_DETAIL, CL_CELL_LINEAGE, CL_CLINICAL_TUMOR_FEATURE, CL_COMPLICATION_TREATMENT, CL_CONCEPTION_METHOD, CL_CRM_STATUS, CL_DCIS_NUCLEAR_GRADE, CL_DIAGNOSIS_STATUS, CL_DIAGNOSIS_SUBTYPE, CL_DISTANT_METASTASIS_SITE, CL_EXTRANODAL_SITES, CL_FERTILITY_PRESERVATION_TYPE, CL_GROSS_TYPE, CL_HISTOLOGIC_SUBTYPE, CL_IMAGING_DIAGNOSTIC_CLASSIFICATION, CL_IMA_LIGATION_LEVEL, CL_INVASION_DEPTH, CL_LOBULAR_INFLAMMATION_GRADE, CL_LYMPHOMA_CATEGORY, CL_MARITAL_STATUS_DETAIL, CL_MASLD_DIAGNOSIS_BASIS, CL_MENOPAUSAL_STATUS_AT_DIAGNOSIS, CL_MENSES_REGULARITY_AFTER_CHEMO, CL_MRI_ANTERIOR_PERITONEAL_RELATION, CL_MRI_CIRCUMFERENTIAL_EXTENT, CL_MRI_CIRCUMFERENTIAL_LOCATION, CL_MRI_T4B_INVADED_ORGAN, CL_MRI_TUMOR_REGRESSION_GRADE, CL_NODULE_RADIOLOGIC_TYPE, CL_PERITONEAL_CYTOLOGY_RESULT, CL_PREGNANCY_OUTCOME, CL_PRIMARY_INVOLVED_SITE, CL_PRIMARY_SIDEDNESS, CL_PRIMARY_SITE, CL_RESECTION_COMPLETENESS, CL_RESECTION_MARGIN_STATUS, CL_RESIDUAL_TUMOR_R_CLASS, CL_STAGING_METHOD, CL_STOMA_REASON, CL_SURGICAL_HISTOLOGIC_GRADE, CL_SURGICAL_SPECIMEN_LATERALITY, CL_SURGICAL_SPECIMEN_SITE, CL_TME_QUALITY, CL_TUMOR_BUDDING_GRADE, CL_VPI_GRADE, CL_WATCH_AND_WAIT_STATUS

## 경고


## 메모

- PERSON.death_date → DEATH 테이블로 이관
