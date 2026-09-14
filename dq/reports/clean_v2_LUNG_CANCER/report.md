# 데이터 품질 검증 보고서: LUNG_CANCER (폐암)

검증일 2026-09-07 / 테이블 18개 / 규칙 383개 (실패 1, 건너뜀 0, 오류 0)

위반 3건 (error 3, warning 0)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 219 | 0 | 0 |
| Completeness | 122 | 1 | 3 |
| Plausibility | 42 | 0 | 0 |

## 테이블 행수

- PERSON: 40
- OBSERVATION_PERIOD: 40
- DEATH: 13
- VISIT_OCCURRENCE: 638
- CONDITION_OCCURRENCE: 157
- PROCEDURE_OCCURRENCE: 491
- DRUG_EXPOSURE: 368
- MEASUREMENT: 1612
- OBSERVATION: 159
- NOTE: 131
- SPECIMEN: 57
- COHORT: 40
- EPISODE: 83
- EPISODE_EVENT: 466
- PATHOLOGY_REPORT: 57
- PATHOLOGY_TUMOR: 57
- BIOMARKER: 136
- LUNG_EXAM: 351

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0280 PATHOLOGY_REPORT.adenocarcinoma_predominant_subtype_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행인데 adenocarcinoma_predominant_subtype_concept_id 가 비어 있다 / SURGICAL 행인데 adenocarcinoma_predominant_subtype_concept_id 가 비어 있다 |
