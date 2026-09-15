# 데이터 품질 검증 보고서: LYMPHOMA (림프종)

검증일 2026-09-07 / 테이블 19개 / 규칙 531개 (실패 47, 건너뜀 2, 오류 0)

위반 143건 (error 121, warning 22)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 312 | 23 | 62 |
| Completeness | 174 | 13 | 37 |
| Plausibility | 45 | 11 | 44 |

## 테이블 행수

- PERSON: 100
- OBSERVATION_PERIOD: 100
- DEATH: 17
- VISIT_OCCURRENCE: 1902
- CONDITION_OCCURRENCE: 207
- PROCEDURE_OCCURRENCE: 500
- DRUG_EXPOSURE: 2160
- MEASUREMENT: 2215
- OBSERVATION: 0
- NOTE: 0
- SPECIMEN: 100
- COHORT: 100
- EPISODE: 200
- EPISODE_EVENT: 2367
- PATHOLOGY_REPORT: 100
- BIOMARKER: 100
- LYMPHOMA_ASSESSMENT: 100
- LYMPHOMA_EVENT: 100
- LYMPHOMA_EXAM: 300

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0068 CONDITION_OCCURRENCE.condition_start_date 미래 날짜 금지 | Plausibility | error | CONDITION_OCCURRENCE | 3 | condition_start_date=… 미래 날짜 / condition_start_date=… 미래 날짜 |
| SV-0076 PROCEDURE_OCCURRENCE.procedure_occurrence_id PK 유일성 | Conformance | error | PROCEDURE_OCCURRENCE | 5 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0078 PROCEDURE_OCCURRENCE.procedure_occurrence_id 타입(bigint) | Conformance | error | PROCEDURE_OCCURRENCE | 3 | procedure_occurrence_id=… 은 integer 아님 / procedure_occurrence_id=… 은 integer 아님 |
| SV-0093 DRUG_EXPOSURE 컬럼 구성 | Conformance | error | DRUG_EXPOSURE | 1 | 컬럼 누락: quantity |
| SV-0094 DRUG_EXPOSURE.drug_exposure_id PK 유일성 | Conformance | error | DRUG_EXPOSURE | 2 | PK 중복: … / PK 중복: … |
| SV-0122 MEASUREMENT.measurement_date 미래 날짜 금지 | Plausibility | error | MEASUREMENT | 3 | measurement_date=… 미래 날짜 / measurement_date=… 미래 날짜 |
| SV-0197 COHORT.cohort_definition_id+subject_id+cohort_start_date PK 유일성 | Conformance | error | COHORT | 3 | PK NULL / PK NULL |
| SV-0198 COHORT.cohort_definition_id 필수 | Completeness | error | COHORT | 3 | cohort_definition_id NULL / cohort_definition_id NULL |
| SV-0204 COHORT.cohort_start_date 미래 날짜 금지 | Plausibility | error | COHORT | 3 | cohort_start_date=… 미래 날짜 / cohort_start_date=… 미래 날짜 |
| SV-0209 EPISODE.episode_id PK 유일성 | Conformance | error | EPISODE | 3 | PK NULL / PK NULL |
| SV-0210 EPISODE.episode_id 필수 | Completeness | error | EPISODE | 3 | episode_id NULL / episode_id NULL |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_id=… 가 SPECIMEN.specimen_id 에 없음 / specimen_id=… 가 SPECIMEN.specimen_id 에 없음 |
| SV-0250 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0251 PATHOLOGY_REPORT.specimen_date 타입(date) | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_date=… 은 date 아님 / specimen_date=… 은 date 아님 |
| SV-0383 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['…', '…', '…'] 값 있으나 anchor specimen_date NULL / ['…', '…', '…'] 값 있으나 anchor specimen_date NULL |
| SV-0408 BIOMARKER.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | BIOMARKER | 3 | specimen_id=… 가 SPECIMEN.specimen_id 에 없음 / specimen_id=… 가 SPECIMEN.specimen_id 에 없음 |
| SV-0505 BIOMARKER.mum1_result_concept_id 필수 | Completeness | error | BIOMARKER | 3 | mum1_result_concept_id NULL / mum1_result_concept_id NULL |
| SV-0532 BIOMARKER.double_expressor_yn 값 집합(YN) 코드 | Conformance | error | BIOMARKER | 3 | double_expressor_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) / double_expressor_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) |
| SV-0533 BIOMARKER.flow_cytometry_summary_concept_id 필수(코드 또는 원천값) | Completeness | error | BIOMARKER | 3 | flow_cytometry_summary_concept_id 와 flow_cytometry_summary_source_value 가 모두 비어 있다 / flow_cytometry_summary_concept_id 와 flow_cytometry_summary_source |
| SV-0546 BIOMARKER.bcl2_rearrangement_result_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | bcl2_rearrangement_result_concept_id=… 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / bcl2_rearrangement_result_concept_id=… 는 값 집합(BIOMARKER_RESULT) 의 |
| SV-0555 BIOMARKER.t14_18_result_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | t14_18_result_concept_id=… 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / t14_18_result_concept_id=… 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 |
| SV-0558 BIOMARKER.t11_14_result_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | t11_14_result_concept_id=… 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / t11_14_result_concept_id=… 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 |
| SV-0564 BIOMARKER.complex_karyotype_yn 값 집합(YN) 코드 | Conformance | error | BIOMARKER | 3 | complex_karyotype_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) / complex_karyotype_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) |
| SV-0570 BIOMARKER.mrd_result_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | mrd_result_concept_id=… 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / mrd_result_concept_id=… 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 |
| SV-0928 LYMPHOMA_ASSESSMENT.assessment_date 필수 | Completeness | error | LYMPHOMA_ASSESSMENT | 3 | assessment_date NULL / assessment_date NULL |
| SV-0936 LYMPHOMA_ASSESSMENT.fever_yn 값 집합(YN) 코드 | Conformance | error | LYMPHOMA_ASSESSMENT | 3 | fever_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) / fever_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) |
| SV-0959 LYMPHOMA_ASSESSMENT.mipi_c_risk_group_concept_id 필수 | Completeness | error | LYMPHOMA_ASSESSMENT | 3 | mipi_c_risk_group_concept_id NULL / mipi_c_risk_group_concept_id NULL |
| SV-0968 LYMPHOMA_ASSESSMENT 사건 날짜 필수 | Completeness | error | LYMPHOMA_ASSESSMENT | 3 | ['…', '…', '…'] 값 있으나 anchor assessment_date NULL / ['…', '…', '…'] 값 있으나 anchor assessment_date NULL |
| SV-0971 LYMPHOMA_EVENT.lymphoma_event_id PK 유일성 | Conformance | error | LYMPHOMA_EVENT | 2 | PK 중복: … / PK 중복: … |
| SV-0975 LYMPHOMA_EVENT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | LYMPHOMA_EVENT | 3 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| SV-0983 LYMPHOMA_EVENT.transformation_yn 값 집합(YN) 코드 | Conformance | error | LYMPHOMA_EVENT | 3 | transformation_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) / transformation_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) |
| SV-0990 LYMPHOMA_EVENT.transformation_to_subtype_concept_id 필수(transformation_yn=1 일 때) | Completeness | error | LYMPHOMA_EVENT | 1 | transformation_yn 이 … 인 행 인데 transformation_to_subtype_concept_id 가 비어 있다 |
| SV-0996 LYMPHOMA_EVENT.sct_date 필수(sct_yn=1 일 때) | Completeness | error | LYMPHOMA_EVENT | 3 | sct_yn 이 … 인 행 인데 sct_date 가 비어 있다 / sct_yn 이 … 인 행 인데 sct_date 가 비어 있다 |
| SV-0999 LYMPHOMA_EVENT.sct_type_concept_id 필수(sct_yn=1 일 때) | Completeness | error | LYMPHOMA_EVENT | 3 | sct_yn 이 … 인 행 인데 sct_type_concept_id 가 비어 있다 / sct_yn 이 … 인 행 인데 sct_type_concept_id 가 비어 있다 |
| SV-1014 LYMPHOMA_EVENT.lymphodepletion_start_date 필수(car_t_yn=1 일 때) | Completeness | error | LYMPHOMA_EVENT | 3 | car_t_yn 이 … 인 행 인데 lymphodepletion_start_date 가 비어 있다 / car_t_yn 이 … 인 행 인데 lymphodepletion_start_date 가 비어 있다 |
| SV-1026 LYMPHOMA_EXAM.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | LYMPHOMA_EXAM | 3 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date … < visit_start_date … / visit_end_date … < visit_start_date … |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date … 가 출생연도 … 보다 이르다 / visit_start_date … 가 출생연도 … 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DEATH,DRUG_EXPOSURE,MEASUREMENT,OBSERVATION,PROCEDURE_OCCURRENCE,SPECIMEN,VISIT_OCCURRENCE | 3 | 사건일 … 가 사망일 … 보다 뒤다 / 사건일 … 가 사망일 … 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 2 | visit_start_date … 가 관찰기간 […, …] 밖이다 / visit_start_date … 가 관찰기간 […, …] 밖이다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 17 | 사건일 … 가 방문 […, …] 밖이다 / 사건일 … 가 방문 […, …] 밖이다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | days_supply … 가 기간(…일) 과 다르다 / days_supply … 가 기간(…일) 과 다르다 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 2 | episode_end_date … < episode_start_date … / episode_end_date … < episode_start_date … |
| SEMV-EP-002 에피소드에 매단 사건이 실제로 있음 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,EPISODE,EPISODE_EVENT,PROCEDURE_OCCURRENCE | 1 | F_DRUG 가 가리킨 사건 … 이 대상 테이블에 없다 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 3 | 레지멘 기간 […, …] 이 연결 약물 기간 […, …] 을 담지 못한다 / 레지멘 기간 […, …] 이 연결 약물 기간 […, …] 을 담지 못한다 |
| SEMV-EP-004 에피소드와 연결 사건의 환자 일치 | Conformance | error | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 1 | 에피소드 환자 … 와 약물 환자 … 가 다르다 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 2 | 병리 보고서의 검체일 … 가 SPECIMEN 의 … 와 다르다 / 병리 보고서의 검체일 … 가 SPECIMEN 의 … 와 다르다 |
