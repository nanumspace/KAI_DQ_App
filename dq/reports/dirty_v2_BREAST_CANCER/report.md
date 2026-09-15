# 데이터 품질 검증 보고서: BREAST_CANCER (유방암)

검증일 2026-09-07 / 테이블 19개 / 규칙 498개 (실패 46, 건너뜀 1, 오류 1)

위반 136건 (error 119, warning 17)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 304 | 17 | 47 |
| Completeness | 155 | 16 | 48 |
| Plausibility | 39 | 13 | 41 |

## 테이블 행수

- PERSON: 60
- OBSERVATION_PERIOD: 60
- DEATH: 0
- VISIT_OCCURRENCE: 1841
- CONDITION_OCCURRENCE: 129
- PROCEDURE_OCCURRENCE: 654
- DRUG_EXPOSURE: 2042
- MEASUREMENT: 1056
- OBSERVATION: 0
- NOTE: 0
- SPECIMEN: 117
- COHORT: 60
- EPISODE: 102
- EPISODE_EVENT: 1258
- PATHOLOGY_REPORT: 117
- PATHOLOGY_TUMOR: 0
- BIOMARKER: 60
- BREAST_BASELINE: 60
- BREAST_EXAM: 420

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0068 CONDITION_OCCURRENCE.condition_start_date 미래 날짜 금지 | Plausibility | error | CONDITION_OCCURRENCE | 3 | condition_start_date=2099-01-01 미래 날짜 / condition_start_date=2099-01-01 미래 날짜 |
| SV-0085 PROCEDURE_OCCURRENCE.procedure_date 미래 날짜 금지 | Plausibility | error | PROCEDURE_OCCURRENCE | 3 | procedure_date=2099-01-01 미래 날짜 / procedure_date=2099-01-01 미래 날짜 |
| SV-0112 MEASUREMENT 컬럼 구성 | Conformance | error | MEASUREMENT | 1 | 컬럼 누락: range_high |
| SV-0123 MEASUREMENT.measurement_type_concept_id 필수 | Completeness | error | MEASUREMENT | 3 | measurement_type_concept_id NULL / measurement_type_concept_id NULL |
| SV-0126 MEASUREMENT.value_as_number 타입(float) | Conformance | error | MEASUREMENT | 3 | value_as_number='NOT_A_NUMBER' 은 float 아님 / value_as_number='NOT_A_NUMBER' 은 float 아님 |
| SV-0179 SPECIMEN.specimen_id PK 유일성 | Conformance | error | SPECIMEN | 2 | PK 중복: 200077 / PK 중복: 200077 |
| SV-0184 SPECIMEN.specimen_concept_id 필수 | Completeness | error | SPECIMEN | 3 | specimen_concept_id NULL / specimen_concept_id NULL |
| SV-0185 SPECIMEN.specimen_concept_id 타입(bigint) | Conformance | error | SPECIMEN | 3 | specimen_concept_id='NOT_A_NUMBER' 은 integer 아님 / specimen_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0197 COHORT.cohort_definition_id+subject_id+cohort_start_date PK 유일성 | Conformance | error | COHORT | 2 | PK 중복: 2+200024+2019-12-13 / PK 중복: 2+200024+2019-12-13 |
| SV-0237 PATHOLOGY_REPORT.pathology_report_id PK 유일성 | Conformance | error | PATHOLOGY_REPORT | 2 | PK 중복: 200102 / PK 중복: 200102 |
| SV-0240 PATHOLOGY_REPORT.report_type_concept_id 값 집합(CL_PATHOLOGY_REPORT_TYPE) | Conformance | error | PATHOLOGY_REPORT | 3 | report_type_concept_id=10000099999 는 값 집합(CL_PATHOLOGY_REPORT_TYPE) 의 concept_id 가 아니다 / report_type_concept_id=10000099999 는 값 집합(CL_PATHOLOGY_REPORT |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 4 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0250 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0265 PATHOLOGY_REPORT.biopsy_histologic_diagnosis_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | biopsy_histologic_diagnosis_concept_id 와 biopsy_histologic_diagnosis_source_value 가 모두 비어 있다 / biopsy_histologic_diagnosis_concept_id 와 biopsy_histolo |
| SV-0270 PATHOLOGY_REPORT.surgical_histologic_diagnosis_concept_id 필수(SURGICAL 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | surgical_histologic_diagnosis_concept_id 와 surgical_histologic_diagnosis_source_value 가 모두 비어 있다 / surgical_histologic_diagnosis_concept_id 와 surgical |
| SV-0290 PATHOLOGY_REPORT.lymph_nodes_examined 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 lymph_nodes_examined 가 비어 있다 / SURGICAL 행 인데 lymph_nodes_examined 가 비어 있다 |
| SV-0292 PATHOLOGY_REPORT.lymph_nodes_positive 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 / SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 |
| SV-0294 PATHOLOGY_REPORT.biopsy_laterality_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 biopsy_laterality_concept_id 가 비어 있다 / BIOPSY 행 인데 biopsy_laterality_concept_id 가 비어 있다 |
| SV-0306 PATHOLOGY_REPORT.dcis_nuclear_grade_concept_id 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | dcis_nuclear_grade_concept_id NULL / dcis_nuclear_grade_concept_id NULL |
| SV-0319 PATHOLOGY_REPORT.lymphovascular_invasion_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | lymphovascular_invasion_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / lymphovascular_invasion_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0323 PATHOLOGY_REPORT.residual_tumor_r_class_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 residual_tumor_r_class_concept_id 가 비어 있다 / SURGICAL 행 인데 residual_tumor_r_class_concept_id 가 비어 있다 |
| SV-0328 PATHOLOGY_REPORT.mammographic_microcalcification_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | mammographic_microcalcification_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / mammographic_microcalcification_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', |
| SV-0383 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['report_type_concept_id', 'report_type_source_value', 'surgical_specimen_site_concept_id'] 값 있으나 anchor specimen_date NULL / ['report_type_concept_id |
| SV-0406 BIOMARKER.person_id -> PERSON.person_id 참조무결성 | Conformance | error | BIOMARKER | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0408 BIOMARKER.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | BIOMARKER | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0445 BIOMARKER.germline_test_gene_concept_id 필수(코드 또는 원천값) | Completeness | error | BIOMARKER | 3 | germline_test_gene_concept_id 와 germline_test_gene_source_value 가 모두 비어 있다 / germline_test_gene_concept_id 와 germline_test_gene_source_value 가 모두 비어 있 |
| SV-0605 BREAST_BASELINE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | BREAST_BASELINE | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0631 BREAST_BASELINE.breastfeeding_yn 필수 | Completeness | error | BREAST_BASELINE | 3 | breastfeeding_yn NULL / breastfeeding_yn NULL |
| SV-0636 BREAST_BASELINE.menopause_yn 값 집합(YN) 코드 | Conformance | error | BREAST_BASELINE | 3 | menopause_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / menopause_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0675 BREAST_EXAM.visit_occurrence_id 타입(bigint) | Conformance | error | BREAST_EXAM | 3 | visit_occurrence_id='NOT_A_NUMBER' 은 integer 아님 / visit_occurrence_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0676 BREAST_EXAM.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | BREAST_EXAM | 3 | visit_occurrence_id=NOT_A_NUMBER 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=NOT_A_NUMBER 가 VISIT_OCCURRENCE.visit_occurrence_id |
| SV-0677 BREAST_EXAM.exam_date 필수 | Completeness | error | BREAST_EXAM | 3 | exam_date NULL / exam_date NULL |
| SV-0679 BREAST_EXAM.exam_date 미래 날짜 금지 | Plausibility | error | BREAST_EXAM | 3 | exam_date=2099-01-01 미래 날짜 / exam_date=2099-01-01 미래 날짜 |
| SV-0686 BREAST_EXAM 사건 날짜 필수 | Completeness | error | BREAST_EXAM | 3 | ['imaging_diagnostic_classification_concept_id', 'mammographic_density_concept_id'] 값 있으나 anchor exam_date NULL / ['imaging_diagnostic_classification_ |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2024-05-02 < visit_start_date 2024-05-03 / visit_end_date 2021-12-25 < visit_start_date 2021-12-26 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1958 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1960 보다 이르다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 관찰기간 [2018-02-09, 2026-09-01] 밖이다 / visit_start_date 1890-01-01 가 관찰기간 [2020-06-29, 2026-09-01] 밖이다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 13 | 사건일 2024-05-03 가 방문 [2024-05-03, 2024-05-02] 밖이다 / 사건일 2021-12-26 가 방문 [2021-12-26, 2021-12-25] 밖이다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | days_supply 99 가 기간(90일) 과 다르다 / days_supply 99 가 기간(1일) 과 다르다 |
| SEMV-COM-010 검사 결과값 존재 | Completeness | error | MEASUREMENT | 3 | value_as_number 와 value_as_concept_id 가 모두 비어 있다 / value_as_number 와 value_as_concept_id 가 모두 비어 있다 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 2 | episode_end_date 2000-01-01 < episode_start_date 2020-04-13 / episode_end_date 2000-01-01 < episode_start_date 2020-03-23 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 2 | 레지멘 기간 [2020-04-13, 2000-01-01] 이 연결 약물 기간 [2020-04-13, 2020-09-07] 을 담지 못한다 / 레지멘 기간 [2020-03-23, 2000-01-01] 이 연결 약물 기간 [2020-03-23, 2020-08-17] 을 담 |
| SEMV-EP-005 진단일 <= 첫 치료 시작일 | Plausibility | error | CONDITION_OCCURRENCE,EPISODE | 2 | 첫 치료 시작 2020-12-15 가 첫 진단 2021-04-03 보다 이르다 / 첫 치료 시작 2020-11-09 가 첫 진단 2099-01-01 보다 이르다 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 3 | 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2020-01-10 와 다르다 / 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2019-11-13 와 다르다 |
| SEMV-PA-002 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | PATHOLOGY_REPORT | 2 | 침윤 999.0 > 절제 3.0 / 침윤 999.0 > 절제 3.0 |
| SEMV-PA-003 수술 병리 검체일 >= 수술일 | Plausibility | error | PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE | 1 | 수술 병리 검체일 2001-01-01 앞 60일 안에 시술 기록이 없다 |

## 규칙 실행 오류

- SEMV-COM-011: SQL 오류: Binder Error: Referenced column "range_high" not found in FROM clause!
Candidate bindings: "range_low", "person_id", "measurement_id", "measurement_date", "measurement_event_id"

LINE 4: WHERE range_l
