# 데이터 품질 검증 보고서: DIABETES (당뇨병)

검증일 2026-09-07 / 테이블 17개 / 규칙 339개 (실패 36, 건너뜀 7, 오류 0)

위반 138건 (error 101, warning 37)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 198 | 18 | 49 |
| Completeness | 108 | 7 | 27 |
| Plausibility | 33 | 11 | 62 |

## 테이블 행수

- PERSON: 60
- OBSERVATION_PERIOD: 60
- DEATH: 1
- VISIT_OCCURRENCE: 1061
- CONDITION_OCCURRENCE: 176
- PROCEDURE_OCCURRENCE: 301
- DRUG_EXPOSURE: 3007
- MEASUREMENT: 7817
- OBSERVATION: 60
- NOTE: 982
- SPECIMEN: 0
- COHORT: 60
- EPISODE: 60
- EPISODE_EVENT: 98
- BIOMARKER: 15
- DIABETES_BASELINE: 60
- DIABETES_EVENT: 241

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0015 OBSERVATION_PERIOD.observation_period_id PK 유일성 | Conformance | error | OBSERVATION_PERIOD | 2 | PK 중복: 500041 / PK 중복: 500041 |
| SV-0052 VISIT_OCCURRENCE.visit_end_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date=2099-01-01 미래 날짜 / visit_end_date=2099-01-01 미래 날짜 |
| SV-0058 CONDITION_OCCURRENCE 컬럼 구성 | Conformance | error | CONDITION_OCCURRENCE | 1 | 컬럼 누락: condition_type_concept_id |
| SV-0076 PROCEDURE_OCCURRENCE.procedure_occurrence_id PK 유일성 | Conformance | error | PROCEDURE_OCCURRENCE | 2 | PK 중복: 500210 / PK 중복: 500210 |
| SV-0097 DRUG_EXPOSURE.person_id 필수 | Completeness | error | DRUG_EXPOSURE | 3 | person_id NULL / person_id NULL |
| SV-0103 DRUG_EXPOSURE.drug_exposure_start_date 미래 날짜 금지 | Plausibility | error | DRUG_EXPOSURE | 3 | drug_exposure_start_date=2099-01-01 미래 날짜 / drug_exposure_start_date=2099-01-01 미래 날짜 |
| SV-0105 DRUG_EXPOSURE.drug_type_concept_id 필수 | Completeness | error | DRUG_EXPOSURE | 3 | drug_type_concept_id NULL / drug_type_concept_id NULL |
| SV-0147 OBSERVATION.observation_type_concept_id 타입(bigint) | Conformance | error | OBSERVATION | 3 | observation_type_concept_id='NOT_A_NUMBER' 은 integer 아님 / observation_type_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0164 NOTE.note_date 미래 날짜 금지 | Plausibility | error | NOTE | 3 | note_date=2099-01-01 미래 날짜 / note_date=2099-01-01 미래 날짜 |
| SV-0170 NOTE.encoding_concept_id 필수 | Completeness | error | NOTE | 3 | encoding_concept_id NULL / encoding_concept_id NULL |
| SV-0199 COHORT.cohort_definition_id 타입(bigint) | Conformance | error | COHORT | 3 | cohort_definition_id='NOT_A_NUMBER' 은 integer 아님 / cohort_definition_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0209 EPISODE.episode_id PK 유일성 | Conformance | error | EPISODE | 3 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0211 EPISODE.episode_id 타입(bigint) | Conformance | error | EPISODE | 3 | episode_id='NOT_A_NUMBER' 은 integer 아님 / episode_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0218 EPISODE.episode_start_date 미래 날짜 금지 | Plausibility | error | EPISODE | 3 | episode_start_date=2099-01-01 미래 날짜 / episode_start_date=2099-01-01 미래 날짜 |
| SV-0402 BIOMARKER.biomarker_id PK 유일성 | Conformance | error | BIOMARKER | 2 | PK 중복: 500005 / PK 중복: 500005 |
| SV-0406 BIOMARKER.person_id -> PERSON.person_id 참조무결성 | Conformance | error | BIOMARKER | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0411 BIOMARKER.test_date 필수 | Completeness | error | BIOMARKER | 3 | test_date NULL / test_date NULL |
| SV-0573 BIOMARKER 사건 날짜 필수 | Completeness | error | BIOMARKER | 3 | ['gad_antibody_result_concept_id', 'gad_antibody_result_source_value'] 값 있으나 anchor test_date NULL / ['gad_antibody_result_concept_id', 'gad_antibody_ |
| SV-0861 DIABETES_BASELINE.person_id -> PERSON.person_id 참조무결성 | Conformance | error | DIABETES_BASELINE | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0863 DIABETES_BASELINE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | DIABETES_BASELINE | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0869 DIABETES_BASELINE.cgm_use_yn 값 집합(YN) 코드 | Conformance | error | DIABETES_BASELINE | 3 | cgm_use_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / cgm_use_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0881 DIABETES_EVENT.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | DIABETES_EVENT | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0882 DIABETES_EVENT.event_date 필수 | Completeness | error | DIABETES_EVENT | 6 | event_date NULL / event_date NULL |
| SV-0895 DIABETES_EVENT.ckd_stage_concept_id 값 집합(CKD_STAGE) | Conformance | error | DIABETES_EVENT | 3 | ckd_stage_concept_id=10000099999 는 값 집합(CKD_STAGE) 의 concept_id 가 아니다 / ckd_stage_concept_id=10000099999 는 값 집합(CKD_STAGE) 의 concept_id 가 아니다 |
| SV-0901 DIABETES_EVENT.retinopathy_severity_concept_id 값 집합(DR_SEVERITY) | Conformance | error | DIABETES_EVENT | 3 | retinopathy_severity_concept_id=10000099999 는 값 집합(DR_SEVERITY) 의 concept_id 가 아니다 / retinopathy_severity_concept_id=10000099999 는 값 집합(DR_SEVERITY) 의 |
| SV-0904 DIABETES_EVENT.macular_edema_yn 값 집합(YN) 코드 | Conformance | error | DIABETES_EVENT | 3 | macular_edema_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / macular_edema_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0907 DIABETES_EVENT.peripheral_neuropathy_yn 값 집합(YN) 코드 | Conformance | error | DIABETES_EVENT | 3 | peripheral_neuropathy_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / peripheral_neuropathy_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0915 DIABETES_EVENT.cardiac_autonomic_neuropathy_yn 값 집합(YN) 코드 | Conformance | error | DIABETES_EVENT | 3 | cardiac_autonomic_neuropathy_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / cardiac_autonomic_neuropathy_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1',  |
| SV-0918 DIABETES_EVENT 사건 날짜 필수 | Completeness | error | DIABETES_EVENT | 6 | ['hba1c_target_met_yn', 'severe_hypoglycemia_count', 'hypoglycemia_unawareness_yn'] 값 있으나 anchor event_date NULL / ['hba1c_target_met_yn', 'severe_hyp |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2021-02-14 < visit_start_date 2021-02-15 / visit_end_date 2023-11-12 < visit_start_date 2023-11-13 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1961 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1958 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DEATH,DRUG_EXPOSURE,MEASUREMENT,OBSERVATION,PROCEDURE_OCCURRENCE,SPECIMEN,VISIT_OCCURRENCE | 2 | 사건일 2025-11-12 가 사망일 2025-11-05 보다 뒤다 / 사건일 2025-11-12 가 사망일 2025-11-05 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 관찰기간 [2019-12-04, 2026-09-01] 밖이다 / visit_start_date 1890-01-01 가 관찰기간 [2019-02-26, 2026-09-01] 밖이다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 34 | 사건일 2021-02-15 가 방문 [2021-02-15, 2021-02-14] 밖이다 / 사건일 2021-02-15 가 방문 [2021-02-15, 2021-02-14] 밖이다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 6 | days_supply 99 가 기간(91일) 과 다르다 / 종료일 2019-10-18 < 시작일 2099-01-01 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 1 |  |
