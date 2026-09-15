# 데이터 품질 검증 보고서: MASLD (대사이상지방간)

검증일 2026-09-07 / 테이블 18개 / 규칙 385개 (실패 41, 건너뜀 2, 오류 0)

위반 144건 (error 113, warning 31)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 223 | 19 | 54 |
| Completeness | 125 | 13 | 39 |
| Plausibility | 37 | 9 | 51 |

## 테이블 행수

- PERSON: 100
- OBSERVATION_PERIOD: 100
- DEATH: 0
- VISIT_OCCURRENCE: 764
- CONDITION_OCCURRENCE: 372
- PROCEDURE_OCCURRENCE: 131
- DRUG_EXPOSURE: 0
- MEASUREMENT: 3464
- OBSERVATION: 0
- NOTE: 0
- SPECIMEN: 31
- COHORT: 100
- EPISODE: 100
- EPISODE_EVENT: 100
- PATHOLOGY_REPORT: 31
- MASLD_EXAM: 100
- MASLD_ASSESSMENT: 541
- MASLD_EVENT: 541

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0049 VISIT_OCCURRENCE.visit_start_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_start_date=… 미래 날짜 / visit_start_date=… 미래 날짜 |
| SV-0052 VISIT_OCCURRENCE.visit_end_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date=… 미래 날짜 / visit_end_date=… 미래 날짜 |
| SV-0067 CONDITION_OCCURRENCE.condition_start_date 타입(date) | Conformance | error | CONDITION_OCCURRENCE | 3 | condition_start_date=… 은 date 아님 / condition_start_date=… 은 date 아님 |
| SV-0068 CONDITION_OCCURRENCE.condition_start_date 미래 날짜 금지 | Plausibility | error | CONDITION_OCCURRENCE | 3 | condition_start_date=… 미래 날짜 / condition_start_date=… 미래 날짜 |
| SV-0116 MEASUREMENT.person_id 필수 | Completeness | error | MEASUREMENT | 3 | person_id NULL / person_id NULL |
| SV-0120 MEASUREMENT.measurement_date 필수 | Completeness | error | MEASUREMENT | 3 | measurement_date NULL / measurement_date NULL |
| SV-0208 EPISODE 컬럼 구성 | Conformance | error | EPISODE | 1 | 컬럼 누락: episode_parent_id |
| SV-0224 EPISODE.episode_type_concept_id 필수 | Completeness | error | EPISODE | 3 | episode_type_concept_id NULL / episode_type_concept_id NULL |
| SV-0225 EPISODE.episode_type_concept_id 타입(bigint) | Conformance | error | EPISODE | 3 | episode_type_concept_id=… 은 integer 아님 / episode_type_concept_id=… 은 integer 아님 |
| SV-0228 EPISODE_EVENT.episode_id+event_id+episode_event_field_concept_id PK 유일성 | Conformance | error | EPISODE_EVENT | 2 | PK 중복: …+…+… / PK 중복: …+…+… |
| SV-0237 PATHOLOGY_REPORT.pathology_report_id PK 유일성 | Conformance | error | PATHOLOGY_REPORT | 2 | PK 중복: … / PK 중복: … |
| SV-0240 PATHOLOGY_REPORT.report_type_concept_id 값 집합(CL_PATHOLOGY_REPORT_TYPE) | Conformance | error | PATHOLOGY_REPORT | 3 | report_type_concept_id=… 는 값 집합(CL_PATHOLOGY_REPORT_TYPE) 의 concept_id 가 아니다 / report_type_concept_id=… 는 값 집합(CL_PATHOLOGY_REPORT_TYPE) 의 concept_id  |
| SV-0244 PATHOLOGY_REPORT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_id=… 가 SPECIMEN.specimen_id 에 없음 / specimen_id=… 가 SPECIMEN.specimen_id 에 없음 |
| SV-0366 PATHOLOGY_REPORT.biopsy_adequacy_concept_id 값 집합(CL_BIOPSY_ADEQUACY) | Conformance | error | PATHOLOGY_REPORT | 2 | biopsy_adequacy_concept_id=… 는 값 집합(CL_BIOPSY_ADEQUACY) 의 concept_id 가 아니다 / biopsy_adequacy_concept_id=… 는 값 집합(CL_BIOPSY_ADEQUACY) 의 concept_id 가 아니 |
| SV-0367 PATHOLOGY_REPORT.liver_fibrosis_grade_name_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | liver_fibrosis_grade_name_concept_id 와 liver_fibrosis_grade_name_source_value 가 모두 비어 있다 / liver_fibrosis_grade_name_concept_id 와 liver_fibrosis_grade |
| SV-0371 PATHOLOGY_REPORT.steatosis_grade_concept_id 값 집합(NAS_STEATOSIS) | Conformance | error | PATHOLOGY_REPORT | 3 | steatosis_grade_concept_id=… 는 값 집합(NAS_STEATOSIS) 의 concept_id 가 아니다 / steatosis_grade_concept_id=… 는 값 집합(NAS_STEATOSIS) 의 concept_id 가 아니다 |
| SV-0372 PATHOLOGY_REPORT.lobular_inflammation_grade_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 lobular_inflammation_grade_concept_id 가 비어 있다 / BIOPSY 행 인데 lobular_inflammation_grade_concept_id 가 비어 있다 |
| SV-0375 PATHOLOGY_REPORT.ballooning_grade_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 ballooning_grade_concept_id 가 비어 있다 / BIOPSY 행 인데 ballooning_grade_concept_id 가 비어 있다 |
| SV-0378 PATHOLOGY_REPORT.fibrosis_stage_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 fibrosis_stage_concept_id 가 비어 있다 / BIOPSY 행 인데 fibrosis_stage_concept_id 가 비어 있다 |
| SV-0381 PATHOLOGY_REPORT.nas_score 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 nas_score 가 비어 있다 / BIOPSY 행 인데 nas_score 가 비어 있다 |
| SV-0769 MASLD_EXAM.masld_exam_id PK 유일성 | Conformance | error | MASLD_EXAM | 2 | PK 중복: … / PK 중복: … |
| SV-0772 MASLD_EXAM.person_id 타입(bigint) | Conformance | error | MASLD_EXAM | 3 | person_id=… 은 integer 아님 / person_id=… 은 integer 아님 |
| SV-0773 MASLD_EXAM.person_id -> PERSON.person_id 참조무결성 | Conformance | error | MASLD_EXAM | 6 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| SV-0776 MASLD_EXAM.exam_date 필수 | Completeness | error | MASLD_EXAM | 3 | exam_date NULL / exam_date NULL |
| SV-0787 MASLD_EXAM.cap_db_m 타입(float) | Conformance | error | MASLD_EXAM | 3 | cap_db_m=… 은 float 아님 / cap_db_m=… 은 float 아님 |
| SV-0792 MASLD_EXAM 사건 날짜 필수 | Completeness | error | MASLD_EXAM | 3 | ['…', '…', '…'] 값 있으나 anchor exam_date NULL / ['…', '…', '…'] 값 있으나 anchor exam_date NULL |
| SV-0801 MASLD_ASSESSMENT.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | MASLD_ASSESSMENT | 3 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0811 MASLD_ASSESSMENT.fib4_index 필수 | Completeness | error | MASLD_ASSESSMENT | 3 | fib4_index NULL / fib4_index NULL |
| SV-0821 MASLD_ASSESSMENT.child_pugh_class_concept_id 값 집합(CHILD_PUGH) | Conformance | error | MASLD_ASSESSMENT | 3 | child_pugh_class_concept_id=… 는 값 집합(CHILD_PUGH) 의 concept_id 가 아니다 / child_pugh_class_concept_id=… 는 값 집합(CHILD_PUGH) 의 concept_id 가 아니다 |
| SV-0832 MASLD_EVENT.event_date 필수 | Completeness | error | MASLD_EVENT | 3 | event_date NULL / event_date NULL |
| SV-0834 MASLD_EVENT.event_date 미래 날짜 금지 | Plausibility | error | MASLD_EVENT | 3 | event_date=… 미래 날짜 / event_date=… 미래 날짜 |
| SV-0837 MASLD_EVENT.mash_resolution_yn 값 집합(YN) 코드 | Conformance | error | MASLD_EVENT | 3 | mash_resolution_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) / mash_resolution_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) |
| SV-0840 MASLD_EVENT.fibrosis_improvement_yn 값 집합(YN) 코드 | Conformance | error | MASLD_EVENT | 3 | fibrosis_improvement_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) / fibrosis_improvement_yn=… 는 값 집합(YN) 의 코드가 아니다 (허용: ['…', '…', '…']) |
| SV-0854 MASLD_EVENT 사건 날짜 필수 | Completeness | error | MASLD_EVENT | 3 | ['…', '…', '…'] 값 있으나 anchor event_date NULL / ['…', '…', '…'] 값 있으나 anchor event_date NULL |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 6 | visit_end_date … < visit_start_date … / visit_end_date … < visit_start_date … |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date … 가 출생연도 … 보다 이르다 / visit_start_date … 가 출생연도 … 보다 이르다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 5 | visit_start_date … 가 관찰기간 […, …] 밖이다 / visit_start_date … 가 관찰기간 […, …] 밖이다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 24 | 사건일 … 가 방문 […, …] 밖이다 / 사건일 … 가 방문 […, …] 밖이다 |
| SEMV-COM-007 이벤트-방문 환자 일치 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 3 | 사건의 person_id … 와 방문의 person_id … 가 다르다 / 사건의 person_id … 와 방문의 person_id … 가 다르다 |
| SEMV-MA-002 심장대사 위험인자가 하나 이상 | Plausibility | warning | CONDITION_OCCURRENCE,MASLD_EXAM,MEASUREMENT | 2 | 심장대사 위험인자(당뇨·고혈압·이상지질혈증·비만 진단 또는 BMI>=… 하나도 없다 / 심장대사 위험인자(당뇨·고혈압·이상지질혈증·비만 진단 또는 BMI>=… 하나도 없다 |
