# 데이터 품질 검증 보고서: LYMPHOMA (림프종)

검증일 2026-09-07 / 테이블 19개 / 규칙 526개 (실패 48, 건너뜀 3, 오류 0)

위반 156건 (error 131, warning 25)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 310 | 23 | 62 |
| Completeness | 174 | 12 | 36 |
| Plausibility | 42 | 13 | 58 |

## 테이블 행수

- PERSON: 60
- OBSERVATION_PERIOD: 60
- DEATH: 3
- VISIT_OCCURRENCE: 1177
- CONDITION_OCCURRENCE: 133
- PROCEDURE_OCCURRENCE: 300
- DRUG_EXPOSURE: 1368
- MEASUREMENT: 1362
- OBSERVATION: 0
- NOTE: 0
- SPECIMEN: 60
- COHORT: 60
- EPISODE: 120
- EPISODE_EVENT: 1501
- PATHOLOGY_REPORT: 60
- BIOMARKER: 60
- LYMPHOMA_ASSESSMENT: 60
- LYMPHOMA_EVENT: 60
- LYMPHOMA_EXAM: 180

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0034 DEATH.death_date 미래 날짜 금지 | Plausibility | error | DEATH | 3 | death_date=2099-01-01 미래 날짜 / death_date=2099-01-01 미래 날짜 |
| SV-0049 VISIT_OCCURRENCE.visit_start_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_start_date=2099-01-01 미래 날짜 / visit_start_date=2099-01-01 미래 날짜 |
| SV-0076 PROCEDURE_OCCURRENCE.procedure_occurrence_id PK 유일성 | Conformance | error | PROCEDURE_OCCURRENCE | 5 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0078 PROCEDURE_OCCURRENCE.procedure_occurrence_id 타입(bigint) | Conformance | error | PROCEDURE_OCCURRENCE | 3 | procedure_occurrence_id='NOT_A_NUMBER' 은 integer 아님 / procedure_occurrence_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0094 DRUG_EXPOSURE.drug_exposure_id PK 유일성 | Conformance | error | DRUG_EXPOSURE | 2 | PK 중복: 601101 / PK 중복: 601101 |
| SV-0122 MEASUREMENT.measurement_date 미래 날짜 금지 | Plausibility | error | MEASUREMENT | 5 | measurement_date=2099-01-01 미래 날짜 / measurement_date=2099-01-01 미래 날짜 |
| SV-0197 COHORT.cohort_definition_id+subject_id+cohort_start_date PK 유일성 | Conformance | error | COHORT | 3 | PK NULL / PK NULL |
| SV-0198 COHORT.cohort_definition_id 필수 | Completeness | error | COHORT | 3 | cohort_definition_id NULL / cohort_definition_id NULL |
| SV-0209 EPISODE.episode_id PK 유일성 | Conformance | error | EPISODE | 3 | PK NULL / PK NULL |
| SV-0210 EPISODE.episode_id 필수 | Completeness | error | EPISODE | 3 | episode_id NULL / episode_id NULL |
| SV-0218 EPISODE.episode_start_date 미래 날짜 금지 | Plausibility | error | EPISODE | 3 | episode_start_date=2099-01-01 미래 날짜 / episode_start_date=2099-01-01 미래 날짜 |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0250 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0251 PATHOLOGY_REPORT.specimen_date 타입(date) | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_date='2026-13-45' 은 date 아님 / specimen_date='2026-13-45' 은 date 아님 |
| SV-0383 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['report_type_concept_id', 'report_type_source_value', 'biopsy_method_concept_id'] 값 있으나 anchor specimen_date NULL / ['report_type_concept_id', 'repor |
| SV-0408 BIOMARKER.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | BIOMARKER | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0411 BIOMARKER.test_date 필수 | Completeness | error | BIOMARKER | 3 | test_date NULL / test_date NULL |
| SV-0505 BIOMARKER.mum1_result_concept_id 필수 | Completeness | error | BIOMARKER | 3 | mum1_result_concept_id NULL / mum1_result_concept_id NULL |
| SV-0507 BIOMARKER.mum1_result_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | mum1_result_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / mum1_result_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept |
| SV-0526 BIOMARKER.ebv_eber_result_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | ebv_eber_result_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / ebv_eber_result_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 |
| SV-0533 BIOMARKER.flow_cytometry_summary_concept_id 필수(코드 또는 원천값) | Completeness | error | BIOMARKER | 3 | flow_cytometry_summary_concept_id 와 flow_cytometry_summary_source_value 가 모두 비어 있다 / flow_cytometry_summary_concept_id 와 flow_cytometry_summary_source |
| SV-0555 BIOMARKER.t14_18_result_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | t14_18_result_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / t14_18_result_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 con |
| SV-0564 BIOMARKER.complex_karyotype_yn 값 집합(YN) 코드 | Conformance | error | BIOMARKER | 3 | complex_karyotype_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / complex_karyotype_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0567 BIOMARKER.ig_tcr_clonality_result_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | ig_tcr_clonality_result_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / ig_tcr_clonality_result_concept_id=10000099999 는 값 집합(BIO |
| SV-0573 BIOMARKER 사건 날짜 필수 | Completeness | error | BIOMARKER | 3 | ['cd3_result_concept_id', 'cd5_result_concept_id', 'cd10_result_concept_id'] 값 있으나 anchor test_date NULL / ['cd3_result_concept_id', 'cd5_result_conce |
| SV-0939 LYMPHOMA_ASSESSMENT.night_sweats_yn 값 집합(YN) 코드 | Conformance | error | LYMPHOMA_ASSESSMENT | 3 | night_sweats_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / night_sweats_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0959 LYMPHOMA_ASSESSMENT.mipi_c_risk_group_concept_id 필수 | Completeness | error | LYMPHOMA_ASSESSMENT | 3 | mipi_c_risk_group_concept_id NULL / mipi_c_risk_group_concept_id NULL |
| SV-0971 LYMPHOMA_EVENT.lymphoma_event_id PK 유일성 | Conformance | error | LYMPHOMA_EVENT | 2 | PK 중복: 600042 / PK 중복: 600042 |
| SV-0975 LYMPHOMA_EVENT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | LYMPHOMA_EVENT | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0990 LYMPHOMA_EVENT.transformation_to_subtype_concept_id 필수(transformation_yn=1 일 때) | Completeness | error | LYMPHOMA_EVENT | 3 | transformation_yn 이 1 인 행 인데 transformation_to_subtype_concept_id 가 비어 있다 / transformation_yn 이 1 인 행 인데 transformation_to_subtype_concept_id 가 비어 있다 |
| SV-0995 LYMPHOMA_EVENT.sct_yn 값 집합(YN) 코드 | Conformance | error | LYMPHOMA_EVENT | 3 | sct_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / sct_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0996 LYMPHOMA_EVENT.sct_date 필수(sct_yn=1 일 때) | Completeness | error | LYMPHOMA_EVENT | 3 | sct_yn 이 1 인 행 인데 sct_date 가 비어 있다 / sct_yn 이 1 인 행 인데 sct_date 가 비어 있다 |
| SV-0999 LYMPHOMA_EVENT.sct_type_concept_id 필수(sct_yn=1 일 때) | Completeness | error | LYMPHOMA_EVENT | 3 | sct_yn 이 1 인 행 인데 sct_type_concept_id 가 비어 있다 / sct_yn 이 1 인 행 인데 sct_type_concept_id 가 비어 있다 |
| SV-1004 LYMPHOMA_EVENT.car_t_yn 값 집합(YN) 코드 | Conformance | error | LYMPHOMA_EVENT | 3 | car_t_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / car_t_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-1019 LYMPHOMA_EXAM 컬럼 구성 | Conformance | error | LYMPHOMA_EXAM | 1 | 컬럼 누락: metabolic_tumor_volume_ml |
| SV-1026 LYMPHOMA_EXAM.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | LYMPHOMA_EXAM | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 6 | visit_end_date 2022-12-20 < visit_start_date 2099-01-01 / visit_end_date 2020-04-06 < visit_start_date 2099-01-01 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1953 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1960 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DEATH,DRUG_EXPOSURE,MEASUREMENT,OBSERVATION,PROCEDURE_OCCURRENCE,SPECIMEN,VISIT_OCCURRENCE | 2 | 사건일 2099-01-08 가 사망일 2099-01-01 보다 뒤다 / 사건일 2099-01-08 가 사망일 2099-01-01 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 5 | visit_start_date 1890-01-01 가 관찰기간 [2017-03-04, 2026-09-01] 밖이다 / visit_start_date 2099-01-01 가 관찰기간 [2022-05-31, 2026-09-01] 밖이다 |
| SEMV-COM-005 관찰기간 자체의 정합 | Plausibility | error | DEATH,OBSERVATION_PERIOD | 3 | 사망일 2099-01-01 과 관찰기간 종료 2024-08-09 가 다르다 / 사망일 2099-01-01 과 관찰기간 종료 2025-05-14 가 다르다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 16 | 사건일 2022-12-20 가 방문 [2099-01-01, 2022-12-20] 밖이다 / 사건일 2020-04-06 가 방문 [2099-01-01, 2020-04-06] 밖이다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | days_supply 99 가 기간(1일) 과 다르다 / days_supply 99 가 기간(1일) 과 다르다 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 3 | episode_end_date 2000-01-01 < episode_start_date 2019-12-29 / episode_end_date 2021-12-12 < episode_start_date 2099-01-01 |
| SEMV-EP-002 에피소드에 매단 사건이 실제로 있음 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,EPISODE,EPISODE_EVENT,PROCEDURE_OCCURRENCE | 1 | F_DRUG 가 가리킨 사건 600386 이 대상 테이블에 없다 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 4 | 레지멘 기간 [2019-12-29, 2000-01-01] 이 연결 약물 기간 [2019-12-29, 2020-04-12] 을 담지 못한다 / 레지멘 기간 [2099-01-01, 2021-12-12] 이 연결 약물 기간 [2021-08-09, 2021-11-22] 을 담 |
| SEMV-EP-004 에피소드와 연결 사건의 환자 일치 | Conformance | error | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 1 | 에피소드 환자 600049 와 약물 환자 600018 가 다르다 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 2 | 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2021-05-14 와 다르다 / 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2022-04-02 와 다르다 |
