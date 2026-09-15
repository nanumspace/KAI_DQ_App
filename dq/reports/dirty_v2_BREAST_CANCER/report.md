# 데이터 품질 검증 보고서: BREAST_CANCER (유방암)

검증일 2026-09-07 / 테이블 19개 / 규칙 498개 (실패 48, 건너뜀 3, 오류 0)

위반 150건 (error 131, warning 19)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 304 | 19 | 61 |
| Completeness | 155 | 15 | 45 |
| Plausibility | 39 | 14 | 44 |

## 테이블 행수

- PERSON: 100
- OBSERVATION_PERIOD: 100
- DEATH: 1
- VISIT_OCCURRENCE: 2991
- CONDITION_OCCURRENCE: 224
- PROCEDURE_OCCURRENCE: 1088
- DRUG_EXPOSURE: 3374
- MEASUREMENT: 1784
- OBSERVATION: 0
- NOTE: 0
- SPECIMEN: 194
- COHORT: 100
- EPISODE: 173
- EPISODE_EVENT: 2174
- PATHOLOGY_REPORT: 194
- PATHOLOGY_TUMOR: 0
- BIOMARKER: 100
- BREAST_BASELINE: 100
- BREAST_EXAM: 700

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0052 VISIT_OCCURRENCE.visit_end_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date=2099-01-01 미래 날짜 / visit_end_date=2099-01-01 미래 날짜 |
| SV-0059 CONDITION_OCCURRENCE.condition_occurrence_id PK 유일성 | Conformance | error | CONDITION_OCCURRENCE | 3 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0061 CONDITION_OCCURRENCE.condition_occurrence_id 타입(bigint) | Conformance | error | CONDITION_OCCURRENCE | 3 | condition_occurrence_id='NOT_A_NUMBER' 은 integer 아님 / condition_occurrence_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0068 CONDITION_OCCURRENCE.condition_start_date 미래 날짜 금지 | Plausibility | error | CONDITION_OCCURRENCE | 3 | condition_start_date=2099-01-01 미래 날짜 / condition_start_date=2099-01-01 미래 날짜 |
| SV-0085 PROCEDURE_OCCURRENCE.procedure_date 미래 날짜 금지 | Plausibility | error | PROCEDURE_OCCURRENCE | 3 | procedure_date=2099-01-01 미래 날짜 / procedure_date=2099-01-01 미래 날짜 |
| SV-0118 MEASUREMENT.measurement_concept_id 필수 | Completeness | error | MEASUREMENT | 3 | measurement_concept_id NULL / measurement_concept_id NULL |
| SV-0121 MEASUREMENT.measurement_date 타입(date) | Conformance | error | MEASUREMENT | 3 | measurement_date='2026-13-45' 은 date 아님 / measurement_date='2026-13-45' 은 date 아님 |
| SV-0179 SPECIMEN.specimen_id PK 유일성 | Conformance | error | SPECIMEN | 5 | PK NULL / PK NULL |
| SV-0180 SPECIMEN.specimen_id 필수 | Completeness | error | SPECIMEN | 3 | specimen_id NULL / specimen_id NULL |
| SV-0197 COHORT.cohort_definition_id+subject_id+cohort_start_date PK 유일성 | Conformance | error | COHORT | 2 | PK 중복: 2+200040+2020-02-12 / PK 중복: 2+200040+2020-02-12 |
| SV-0237 PATHOLOGY_REPORT.pathology_report_id PK 유일성 | Conformance | error | PATHOLOGY_REPORT | 2 | PK 중복: 200168 / PK 중복: 200168 |
| SV-0240 PATHOLOGY_REPORT.report_type_concept_id 값 집합(CL_PATHOLOGY_REPORT_TYPE) | Conformance | error | PATHOLOGY_REPORT | 3 | report_type_concept_id=10000099999 는 값 집합(CL_PATHOLOGY_REPORT_TYPE) 의 concept_id 가 아니다 / report_type_concept_id=10000099999 는 값 집합(CL_PATHOLOGY_REPORT |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 7 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=200067 가 SPECIMEN.specimen_id 에 없음 |
| SV-0250 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0265 PATHOLOGY_REPORT.biopsy_histologic_diagnosis_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | biopsy_histologic_diagnosis_concept_id 와 biopsy_histologic_diagnosis_source_value 가 모두 비어 있다 / biopsy_histologic_diagnosis_concept_id 와 biopsy_histolo |
| SV-0270 PATHOLOGY_REPORT.surgical_histologic_diagnosis_concept_id 필수(SURGICAL 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | surgical_histologic_diagnosis_concept_id 와 surgical_histologic_diagnosis_source_value 가 모두 비어 있다 / surgical_histologic_diagnosis_concept_id 와 surgical |
| SV-0290 PATHOLOGY_REPORT.lymph_nodes_examined 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 lymph_nodes_examined 가 비어 있다 / SURGICAL 행 인데 lymph_nodes_examined 가 비어 있다 |
| SV-0292 PATHOLOGY_REPORT.lymph_nodes_positive 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 / SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 |
| SV-0294 PATHOLOGY_REPORT.biopsy_laterality_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 biopsy_laterality_concept_id 가 비어 있다 / BIOPSY 행 인데 biopsy_laterality_concept_id 가 비어 있다 |
| SV-0300 PATHOLOGY_REPORT.microcalcification_yn 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | microcalcification_yn NULL / microcalcification_yn NULL |
| SV-0319 PATHOLOGY_REPORT.lymphovascular_invasion_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | lymphovascular_invasion_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / lymphovascular_invasion_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0323 PATHOLOGY_REPORT.residual_tumor_r_class_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 residual_tumor_r_class_concept_id 가 비어 있다 / SURGICAL 행 인데 residual_tumor_r_class_concept_id 가 비어 있다 |
| SV-0328 PATHOLOGY_REPORT.mammographic_microcalcification_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | mammographic_microcalcification_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / mammographic_microcalcification_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', |
| SV-0383 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['report_type_concept_id', 'report_type_source_value', 'surgical_specimen_site_concept_id'] 값 있으나 anchor specimen_date NULL / ['report_type_concept_id |
| SV-0406 BIOMARKER.person_id -> PERSON.person_id 참조무결성 | Conformance | error | BIOMARKER | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0408 BIOMARKER.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | BIOMARKER | 5 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=200082 가 SPECIMEN.specimen_id 에 없음 |
| SV-0445 BIOMARKER.germline_test_gene_concept_id 필수(코드 또는 원천값) | Completeness | error | BIOMARKER | 3 | germline_test_gene_concept_id 와 germline_test_gene_source_value 가 모두 비어 있다 / germline_test_gene_concept_id 와 germline_test_gene_source_value 가 모두 비어 있 |
| SV-0605 BREAST_BASELINE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | BREAST_BASELINE | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0631 BREAST_BASELINE.breastfeeding_yn 필수 | Completeness | error | BREAST_BASELINE | 3 | breastfeeding_yn NULL / breastfeeding_yn NULL |
| SV-0636 BREAST_BASELINE.menopause_yn 값 집합(YN) 코드 | Conformance | error | BREAST_BASELINE | 3 | menopause_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / menopause_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0669 BREAST_EXAM 컬럼 구성 | Conformance | error | BREAST_EXAM | 1 | 컬럼 누락: mammographic_density_concept_id |
| SV-0675 BREAST_EXAM.visit_occurrence_id 타입(bigint) | Conformance | error | BREAST_EXAM | 3 | visit_occurrence_id='NOT_A_NUMBER' 은 integer 아님 / visit_occurrence_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0676 BREAST_EXAM.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | BREAST_EXAM | 3 | visit_occurrence_id=NOT_A_NUMBER 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=NOT_A_NUMBER 가 VISIT_OCCURRENCE.visit_occurrence_id |
| SV-0677 BREAST_EXAM.exam_date 필수 | Completeness | error | BREAST_EXAM | 3 | exam_date NULL / exam_date NULL |
| SV-0686 BREAST_EXAM 사건 날짜 필수 | Completeness | error | BREAST_EXAM | 3 | ['imaging_diagnostic_classification_concept_id'] 값 있으나 anchor exam_date NULL / ['imaging_diagnostic_classification_concept_id'] 값 있으나 anchor exam_date |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2020-03-29 < visit_start_date 2020-03-30 / visit_end_date 2022-04-12 < visit_start_date 2022-04-13 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1967 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1965 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DEATH,DRUG_EXPOSURE,MEASUREMENT,OBSERVATION,PROCEDURE_OCCURRENCE,SPECIMEN,VISIT_OCCURRENCE | 2 | 사건일 2023-12-01 가 사망일 2023-11-24 보다 뒤다 / 사건일 2023-12-01 가 사망일 2023-11-24 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 관찰기간 [2019-12-10, 2026-09-01] 밖이다 / visit_start_date 1890-01-01 가 관찰기간 [2020-09-10, 2026-09-01] 밖이다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 15 | 사건일 2020-03-30 가 방문 [2020-03-30, 2020-03-29] 밖이다 / 사건일 2022-04-13 가 방문 [2022-04-13, 2022-04-12] 밖이다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | days_supply 99 가 기간(90일) 과 다르다 / days_supply 99 가 기간(1일) 과 다르다 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 2 | episode_end_date 2000-01-01 < episode_start_date 2021-09-08 / episode_end_date 2000-01-01 < episode_start_date 2019-10-11 |
| SEMV-EP-002 에피소드에 매단 사건이 실제로 있음 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,EPISODE,EPISODE_EVENT,PROCEDURE_OCCURRENCE | 3 | F_CONDITION 가 가리킨 사건 200025 이 대상 테이블에 없다 / F_CONDITION 가 가리킨 사건 200035 이 대상 테이블에 없다 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 2 | 레지멘 기간 [2021-09-08, 2000-01-01] 이 연결 약물 기간 [2021-09-08, 2022-02-02] 을 담지 못한다 / 레지멘 기간 [2019-10-11, 2000-01-01] 이 연결 약물 기간 [2019-10-11, 2020-03-06] 을 담 |
| SEMV-EP-005 진단일 <= 첫 치료 시작일 | Plausibility | error | CONDITION_OCCURRENCE,EPISODE | 1 | 첫 치료 시작 2020-04-09 가 첫 진단 2020-07-10 보다 이르다 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 3 | 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2022-05-04 와 다르다 / 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2021-09-21 와 다르다 |
| SEMV-PA-002 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | PATHOLOGY_REPORT | 2 | 침윤 999.0 > 절제 3.0 / 침윤 999.0 > 절제 4.0 |
| SEMV-PA-003 수술 병리 검체일 >= 수술일 | Plausibility | error | PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE | 1 | 수술 병리 검체일 2001-01-01 앞 60일 안에 시술 기록이 없다 |
