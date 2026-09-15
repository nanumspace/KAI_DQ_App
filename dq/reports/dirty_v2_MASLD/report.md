# 데이터 품질 검증 보고서: MASLD (대사이상지방간)

검증일 2026-09-07 / 테이블 18개 / 규칙 385개 (실패 39, 건너뜀 4, 오류 0)

위반 204건 (error 109, warning 95)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 223 | 16 | 47 |
| Completeness | 125 | 13 | 39 |
| Plausibility | 37 | 10 | 118 |

## 테이블 행수

- PERSON: 60
- OBSERVATION_PERIOD: 60
- DEATH: 0
- VISIT_OCCURRENCE: 465
- CONDITION_OCCURRENCE: 226
- PROCEDURE_OCCURRENCE: 82
- DRUG_EXPOSURE: 0
- MEASUREMENT: 2080
- OBSERVATION: 0
- NOTE: 0
- SPECIMEN: 22
- COHORT: 60
- EPISODE: 60
- EPISODE_EVENT: 60
- PATHOLOGY_REPORT: 22
- MASLD_EXAM: 60
- MASLD_ASSESSMENT: 325
- MASLD_EVENT: 325

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0022 OBSERVATION_PERIOD.observation_period_start_date 미래 날짜 금지 | Plausibility | error | OBSERVATION_PERIOD | 3 | observation_period_start_date=2099-01-01 미래 날짜 / observation_period_start_date=2099-01-01 미래 날짜 |
| SV-0049 VISIT_OCCURRENCE.visit_start_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_start_date=2099-01-01 미래 날짜 / visit_start_date=2099-01-01 미래 날짜 |
| SV-0067 CONDITION_OCCURRENCE.condition_start_date 타입(date) | Conformance | error | CONDITION_OCCURRENCE | 3 | condition_start_date='2026-13-45' 은 date 아님 / condition_start_date='2026-13-45' 은 date 아님 |
| SV-0085 PROCEDURE_OCCURRENCE.procedure_date 미래 날짜 금지 | Plausibility | error | PROCEDURE_OCCURRENCE | 3 | procedure_date=2099-01-01 미래 날짜 / procedure_date=2099-01-01 미래 날짜 |
| SV-0116 MEASUREMENT.person_id 필수 | Completeness | error | MEASUREMENT | 3 | person_id NULL / person_id NULL |
| SV-0120 MEASUREMENT.measurement_date 필수 | Completeness | error | MEASUREMENT | 3 | measurement_date NULL / measurement_date NULL |
| SV-0224 EPISODE.episode_type_concept_id 필수 | Completeness | error | EPISODE | 3 | episode_type_concept_id NULL / episode_type_concept_id NULL |
| SV-0225 EPISODE.episode_type_concept_id 타입(bigint) | Conformance | error | EPISODE | 3 | episode_type_concept_id='NOT_A_NUMBER' 은 integer 아님 / episode_type_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0228 EPISODE_EVENT.episode_id+event_id+episode_event_field_concept_id PK 유일성 | Conformance | error | EPISODE_EVENT | 2 | PK 중복: 400027+400095+10000000010 / PK 중복: 400027+400095+10000000010 |
| SV-0244 PATHOLOGY_REPORT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0367 PATHOLOGY_REPORT.liver_fibrosis_grade_name_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | liver_fibrosis_grade_name_concept_id 와 liver_fibrosis_grade_name_source_value 가 모두 비어 있다 / liver_fibrosis_grade_name_concept_id 와 liver_fibrosis_grade |
| SV-0372 PATHOLOGY_REPORT.lobular_inflammation_grade_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 lobular_inflammation_grade_concept_id 가 비어 있다 / BIOPSY 행 인데 lobular_inflammation_grade_concept_id 가 비어 있다 |
| SV-0375 PATHOLOGY_REPORT.ballooning_grade_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 ballooning_grade_concept_id 가 비어 있다 / BIOPSY 행 인데 ballooning_grade_concept_id 가 비어 있다 |
| SV-0378 PATHOLOGY_REPORT.fibrosis_stage_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 fibrosis_stage_concept_id 가 비어 있다 / BIOPSY 행 인데 fibrosis_stage_concept_id 가 비어 있다 |
| SV-0381 PATHOLOGY_REPORT.nas_score 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 nas_score 가 비어 있다 / BIOPSY 행 인데 nas_score 가 비어 있다 |
| SV-0769 MASLD_EXAM.masld_exam_id PK 유일성 | Conformance | error | MASLD_EXAM | 2 | PK 중복: 400035 / PK 중복: 400035 |
| SV-0772 MASLD_EXAM.person_id 타입(bigint) | Conformance | error | MASLD_EXAM | 3 | person_id='NOT_A_NUMBER' 은 integer 아님 / person_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0773 MASLD_EXAM.person_id -> PERSON.person_id 참조무결성 | Conformance | error | MASLD_EXAM | 6 | person_id=NOT_A_NUMBER 가 PERSON.person_id 에 없음 / person_id=NOT_A_NUMBER 가 PERSON.person_id 에 없음 |
| SV-0776 MASLD_EXAM.exam_date 필수 | Completeness | error | MASLD_EXAM | 3 | exam_date NULL / exam_date NULL |
| SV-0778 MASLD_EXAM.exam_date 미래 날짜 금지 | Plausibility | error | MASLD_EXAM | 3 | exam_date=2099-01-01 미래 날짜 / exam_date=2099-01-01 미래 날짜 |
| SV-0787 MASLD_EXAM.cap_db_m 타입(float) | Conformance | error | MASLD_EXAM | 3 | cap_db_m='NOT_A_NUMBER' 은 float 아님 / cap_db_m='NOT_A_NUMBER' 은 float 아님 |
| SV-0792 MASLD_EXAM 사건 날짜 필수 | Completeness | error | MASLD_EXAM | 3 | ['elastography_date', 'mri_pdff_percent', 'mre_kpa'] 값 있으나 anchor exam_date NULL / ['elastography_date', 'mri_pdff_percent', 'mre_kpa'] 값 있으나 anchor e |
| SV-0801 MASLD_ASSESSMENT.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | MASLD_ASSESSMENT | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0802 MASLD_ASSESSMENT.assessment_date 필수 | Completeness | error | MASLD_ASSESSMENT | 3 | assessment_date NULL / assessment_date NULL |
| SV-0811 MASLD_ASSESSMENT.fib4_index 필수 | Completeness | error | MASLD_ASSESSMENT | 3 | fib4_index NULL / fib4_index NULL |
| SV-0821 MASLD_ASSESSMENT.child_pugh_class_concept_id 값 집합(CHILD_PUGH) | Conformance | error | MASLD_ASSESSMENT | 3 | child_pugh_class_concept_id=10000099999 는 값 집합(CHILD_PUGH) 의 concept_id 가 아니다 / child_pugh_class_concept_id=10000099999 는 값 집합(CHILD_PUGH) 의 concept_i |
| SV-0822 MASLD_ASSESSMENT 사건 날짜 필수 | Completeness | error | MASLD_ASSESSMENT | 3 | ['prognostic_score_type', 'prognostic_score_value', 'elf_score'] 값 있으나 anchor assessment_date NULL / ['prognostic_score_type', 'prognostic_score_value |
| SV-0824 MASLD_EVENT 컬럼 구성 | Conformance | error | MASLD_EVENT | 1 | 컬럼 누락: cirrhosis_yn |
| SV-0837 MASLD_EVENT.mash_resolution_yn 값 집합(YN) 코드 | Conformance | error | MASLD_EVENT | 3 | mash_resolution_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / mash_resolution_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0846 MASLD_EVENT.decompensation_event_yn 값 집합(YN) 코드 | Conformance | error | MASLD_EVENT | 3 | decompensation_event_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / decompensation_event_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0853 MASLD_EVENT.hcc_yn 값 집합(YN) 코드 | Conformance | error | MASLD_EVENT | 3 | hcc_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / hcc_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 6 | visit_end_date 2022-01-25 < visit_start_date 2022-01-26 / visit_end_date 2022-05-01 < visit_start_date 2099-01-01 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1968 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1957 보다 이르다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 29 | visit_start_date 2020-07-15 가 관찰기간 [2099-01-01, 2026-09-01] 밖이다 / visit_start_date 2020-07-20 가 관찰기간 [2099-01-01, 2026-09-01] 밖이다 |
| SEMV-COM-005 관찰기간 자체의 정합 | Plausibility | error | DEATH,OBSERVATION_PERIOD | 3 | 관찰기간 종료 2026-09-01 < 시작 2099-01-01 / 관찰기간 종료 2026-09-01 < 시작 2099-01-01 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 64 | 사건일 2020-11-04 가 방문 [2099-01-01, 2020-11-04] 밖이다 / 사건일 2020-11-04 가 방문 [2099-01-01, 2020-11-04] 밖이다 |
| SEMV-COM-007 이벤트-방문 환자 일치 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 3 | 사건의 person_id 999999999 와 방문의 person_id 400009 가 다르다 / 사건의 person_id 999999999 와 방문의 person_id 400035 가 다르다 |
| SEMV-MA-002 심장대사 위험인자가 하나 이상 | Plausibility | warning | CONDITION_OCCURRENCE,MASLD_EXAM,MEASUREMENT | 2 | 심장대사 위험인자(당뇨·고혈압·이상지질혈증·비만 진단 또는 BMI>=23)가 하나도 없다 / 심장대사 위험인자(당뇨·고혈압·이상지질혈증·비만 진단 또는 BMI>=23)가 하나도 없다 |
