# 데이터 품질 검증 보고서: DIABETES (당뇨병)

검증일 2026-09-07 / 테이블 17개 / 규칙 341개 (실패 37, 건너뜀 6, 오류 1)

위반 198건 (error 101, warning 97)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 198 | 18 | 49 |
| Completeness | 109 | 8 | 29 |
| Plausibility | 34 | 11 | 120 |

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
| SV-0015 OBSERVATION_PERIOD.observation_period_id PK 유일성 | Conformance | error | OBSERVATION_PERIOD | 2 | PK 중복: 500028 / PK 중복: 500028 |
| SV-0022 OBSERVATION_PERIOD.observation_period_start_date 미래 날짜 금지 | Plausibility | error | OBSERVATION_PERIOD | 3 | observation_period_start_date=2099-01-01 미래 날짜 / observation_period_start_date=2099-01-01 미래 날짜 |
| SV-0076 PROCEDURE_OCCURRENCE.procedure_occurrence_id PK 유일성 | Conformance | error | PROCEDURE_OCCURRENCE | 2 | PK 중복: 500069 / PK 중복: 500069 |
| SV-0097 DRUG_EXPOSURE.person_id 필수 | Completeness | error | DRUG_EXPOSURE | 3 | person_id NULL / person_id NULL |
| SV-0105 DRUG_EXPOSURE.drug_type_concept_id 필수 | Completeness | error | DRUG_EXPOSURE | 3 | drug_type_concept_id NULL / drug_type_concept_id NULL |
| SV-0147 OBSERVATION.observation_type_concept_id 타입(bigint) | Conformance | error | OBSERVATION | 3 | observation_type_concept_id='NOT_A_NUMBER' 은 integer 아님 / observation_type_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0156 NOTE 컬럼 구성 | Conformance | error | NOTE | 1 | 컬럼 누락: note_text |
| SV-0170 NOTE.encoding_concept_id 필수 | Completeness | error | NOTE | 3 | encoding_concept_id NULL / encoding_concept_id NULL |
| SV-0199 COHORT.cohort_definition_id 타입(bigint) | Conformance | error | COHORT | 3 | cohort_definition_id='NOT_A_NUMBER' 은 integer 아님 / cohort_definition_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0209 EPISODE.episode_id PK 유일성 | Conformance | error | EPISODE | 3 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0211 EPISODE.episode_id 타입(bigint) | Conformance | error | EPISODE | 3 | episode_id='NOT_A_NUMBER' 은 integer 아님 / episode_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0402 BIOMARKER.biomarker_id PK 유일성 | Conformance | error | BIOMARKER | 2 | PK 중복: 500002 / PK 중복: 500002 |
| SV-0406 BIOMARKER.person_id -> PERSON.person_id 참조무결성 | Conformance | error | BIOMARKER | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0411 BIOMARKER.test_date 필수 | Completeness | error | BIOMARKER | 3 | test_date NULL / test_date NULL |
| SV-0413 BIOMARKER.test_date 미래 날짜 금지 | Plausibility | error | BIOMARKER | 3 | test_date=2099-01-01 미래 날짜 / test_date=2099-01-01 미래 날짜 |
| SV-0573 BIOMARKER 사건 날짜 필수 | Completeness | error | BIOMARKER | 3 | ['gad_antibody_result_concept_id', 'gad_antibody_result_source_value'] 값 있으나 anchor test_date NULL / ['gad_antibody_result_concept_id', 'gad_antibody_ |
| SV-0861 DIABETES_BASELINE.person_id -> PERSON.person_id 참조무결성 | Conformance | error | DIABETES_BASELINE | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0863 DIABETES_BASELINE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | DIABETES_BASELINE | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0866 DIABETES_BASELINE.record_date 미래 날짜 금지 | Plausibility | error | DIABETES_BASELINE | 3 | record_date=2099-01-01 미래 날짜 / record_date=2099-01-01 미래 날짜 |
| SV-0881 DIABETES_EVENT.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | DIABETES_EVENT | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0882 DIABETES_EVENT.event_date 필수 | Completeness | error | DIABETES_EVENT | 6 | event_date NULL / event_date NULL |
| SV-0884 DIABETES_EVENT.event_date 미래 날짜 금지 | Plausibility | error | DIABETES_EVENT | 3 | event_date=2099-01-01 미래 날짜 / event_date=2099-01-01 미래 날짜 |
| SV-0887 DIABETES_EVENT.hba1c_target_met_yn 값 집합(YN) 코드 | Conformance | error | DIABETES_EVENT | 3 | hba1c_target_met_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / hba1c_target_met_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0895 DIABETES_EVENT.ckd_stage_concept_id 값 집합(CKD_STAGE) | Conformance | error | DIABETES_EVENT | 3 | ckd_stage_concept_id=10000099999 는 값 집합(CKD_STAGE) 의 concept_id 가 아니다 / ckd_stage_concept_id=10000099999 는 값 집합(CKD_STAGE) 의 concept_id 가 아니다 |
| SV-0901 DIABETES_EVENT.retinopathy_severity_concept_id 값 집합(DR_SEVERITY) | Conformance | error | DIABETES_EVENT | 3 | retinopathy_severity_concept_id=10000099999 는 값 집합(DR_SEVERITY) 의 concept_id 가 아니다 / retinopathy_severity_concept_id=10000099999 는 값 집합(DR_SEVERITY) 의 |
| SV-0904 DIABETES_EVENT.macular_edema_yn 값 집합(YN) 코드 | Conformance | error | DIABETES_EVENT | 3 | macular_edema_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / macular_edema_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0907 DIABETES_EVENT.peripheral_neuropathy_yn 값 집합(YN) 코드 | Conformance | error | DIABETES_EVENT | 3 | peripheral_neuropathy_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / peripheral_neuropathy_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0915 DIABETES_EVENT.cardiac_autonomic_neuropathy_yn 값 집합(YN) 코드 | Conformance | error | DIABETES_EVENT | 3 | cardiac_autonomic_neuropathy_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / cardiac_autonomic_neuropathy_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1',  |
| SV-0918 DIABETES_EVENT 사건 날짜 필수 | Completeness | error | DIABETES_EVENT | 6 | ['hba1c_target_met_yn', 'severe_hypoglycemia_count', 'hypoglycemia_unawareness_yn'] 값 있으나 anchor event_date NULL / ['hba1c_target_met_yn', 'severe_hyp |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2019-01-13 < visit_start_date 2019-01-14 / visit_end_date 2019-04-14 < visit_start_date 2019-04-15 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1965 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1956 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DEATH,DRUG_EXPOSURE,MEASUREMENT,OBSERVATION,PROCEDURE_OCCURRENCE,SPECIMEN,VISIT_OCCURRENCE | 2 | 사건일 2025-11-12 가 사망일 2025-11-05 보다 뒤다 / 사건일 2025-11-12 가 사망일 2025-11-05 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 51 | visit_start_date 1890-01-01 가 관찰기간 [2017-08-19, 2026-09-01] 밖이다 / visit_start_date 2021-02-25 가 관찰기간 [2099-01-01, 2026-09-01] 밖이다 |
| SEMV-COM-005 관찰기간 자체의 정합 | Plausibility | error | DEATH,OBSERVATION_PERIOD | 3 | 관찰기간 종료 2026-09-01 < 시작 2099-01-01 / 관찰기간 종료 2026-09-01 < 시작 2099-01-01 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 44 | 사건일 2019-01-14 가 방문 [2019-01-14, 2019-01-13] 밖이다 / 사건일 2019-01-14 가 방문 [2019-01-14, 2019-01-13] 밖이다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | days_supply 99 가 기간(91일) 과 다르다 / days_supply 99 가 기간(91일) 과 다르다 |
| SEMV-DM-001 해마다 HbA1c 를 잰다 | Completeness | warning | MEASUREMENT,VISIT_OCCURRENCE | 2 | 1890년에 방문은 있는데 HbA1c 가 없다 / 1890년에 방문은 있는데 HbA1c 가 없다 |

## 규칙 실행 오류

- SEMV-COM-013: SQL 오류: Binder Error: Referenced column "note_text" not found in FROM clause!
Candidate bindings: "note_title", "note_date", "note_type_concept_id", "note_id", "note_event_id"

LINE 2: FROM NOTE WHERE note_te
