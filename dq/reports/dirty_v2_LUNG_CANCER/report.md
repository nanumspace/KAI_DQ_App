# 데이터 품질 검증 보고서: LUNG_CANCER (폐암)

검증일 2026-09-07 / 테이블 18개 / 규칙 383개 (실패 55, 건너뜀 1, 오류 0)

위반 162건 (error 149, warning 13)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 219 | 25 | 71 |
| Completeness | 122 | 16 | 51 |
| Plausibility | 42 | 14 | 40 |

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
| SV-0015 OBSERVATION_PERIOD.observation_period_id PK 유일성 | Conformance | error | OBSERVATION_PERIOD | 3 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0017 OBSERVATION_PERIOD.observation_period_id 타입(bigint) | Conformance | error | OBSERVATION_PERIOD | 3 | observation_period_id='NOT_A_NUMBER' 은 integer 아님 / observation_period_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0041 VISIT_OCCURRENCE.visit_occurrence_id PK 유일성 | Conformance | error | VISIT_OCCURRENCE | 3 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0043 VISIT_OCCURRENCE.visit_occurrence_id 타입(bigint) | Conformance | error | VISIT_OCCURRENCE | 3 | visit_occurrence_id='NOT_A_NUMBER' 은 integer 아님 / visit_occurrence_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0053 VISIT_OCCURRENCE.visit_end_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date=2099-01-01 미래 날짜 / visit_end_date=2099-01-01 미래 날짜 |
| SV-0060 CONDITION_OCCURRENCE.condition_occurrence_id PK 유일성 | Conformance | error | CONDITION_OCCURRENCE | 2 | PK 중복: 100097 / PK 중복: 100097 |
| SV-0087 PROCEDURE_OCCURRENCE.procedure_date 미래 날짜 금지 | Plausibility | error | PROCEDURE_OCCURRENCE | 3 | procedure_date=2099-01-01 미래 날짜 / procedure_date=2099-01-01 미래 날짜 |
| SV-0097 DRUG_EXPOSURE.drug_exposure_id PK 유일성 | Conformance | error | DRUG_EXPOSURE | 2 | PK 중복: 100284 / PK 중복: 100284 |
| SV-0102 DRUG_EXPOSURE.drug_concept_id 필수 | Completeness | error | DRUG_EXPOSURE | 3 | drug_concept_id NULL / drug_concept_id NULL |
| SV-0117 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 3 | PK NULL / PK NULL |
| SV-0118 MEASUREMENT.measurement_id 필수 | Completeness | error | MEASUREMENT | 3 | measurement_id NULL / measurement_id NULL |
| SV-0128 MEASUREMENT.measurement_type_concept_id 타입(bigint) | Conformance | error | MEASUREMENT | 3 | measurement_type_concept_id='NOT_A_NUMBER' 은 integer 아님 / measurement_type_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0139 OBSERVATION 컬럼 구성 | Conformance | error | OBSERVATION | 1 | 컬럼 누락: qualifier_concept_id |
| SV-0161 NOTE.note_id PK 유일성 | Conformance | error | NOTE | 2 | PK 중복: 100116 / PK 중복: 100116 |
| SV-0186 SPECIMEN.person_id 필수 | Completeness | error | SPECIMEN | 3 | person_id NULL / person_id NULL |
| SV-0208 COHORT.cohort_start_date 미래 날짜 금지 | Plausibility | error | COHORT | 3 | cohort_start_date=2099-01-01 미래 날짜 / cohort_start_date=2099-01-01 미래 날짜 |
| SV-0211 COHORT.cohort_end_date 미래 날짜 금지 | Plausibility | error | COHORT | 3 | cohort_end_date=2099-01-01 미래 날짜 / cohort_end_date=2099-01-01 미래 날짜 |
| SV-0250 PATHOLOGY_REPORT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0256 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0263 PATHOLOGY_REPORT.biopsy_site_concept_id 타입(bigint) | Conformance | error | PATHOLOGY_REPORT | 3 | biopsy_site_concept_id='NOT_A_NUMBER' 은 integer 아님 / biopsy_site_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0264 PATHOLOGY_REPORT.biopsy_site_concept_id 값 집합(CL_BIOPSY_SITE) | Conformance | error | PATHOLOGY_REPORT | 6 | biopsy_site_concept_id=NOT_A_NUMBER 는 값 집합(CL_BIOPSY_SITE) 의 concept_id 가 아니다 / biopsy_site_concept_id=10000099999 는 값 집합(CL_BIOPSY_SITE) 의 concept_id |
| SV-0268 PATHOLOGY_REPORT.surgical_specimen_site_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행인데 surgical_specimen_site_concept_id 가 비어 있다 / SURGICAL 행인데 surgical_specimen_site_concept_id 가 비어 있다 |
| SV-0271 PATHOLOGY_REPORT.biopsy_histologic_diagnosis_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | biopsy_histologic_diagnosis_concept_id 와 biopsy_histologic_diagnosis_source_value 가 모두 비어 있다 / biopsy_histologic_diagnosis_concept_id 와 biopsy_histolo |
| SV-0273 PATHOLOGY_REPORT.biopsy_differentiation_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행인데 biopsy_differentiation_concept_id 가 비어 있다 / BIOPSY 행인데 biopsy_differentiation_concept_id 가 비어 있다 |
| SV-0276 PATHOLOGY_REPORT.surgical_histologic_diagnosis_concept_id 필수(SURGICAL 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | surgical_histologic_diagnosis_concept_id 와 surgical_histologic_diagnosis_source_value 가 모두 비어 있다 / surgical_histologic_diagnosis_concept_id 와 surgical |
| SV-0278 PATHOLOGY_REPORT.primary_histology_concept_id 필수(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | primary_histology_concept_id 와 primary_histology_source_value 가 모두 비어 있다 / primary_histology_concept_id 와 primary_histology_source_value 가 모두 비어 있다 |
| SV-0280 PATHOLOGY_REPORT.adenocarcinoma_predominant_subtype_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 6 | SURGICAL 행인데 adenocarcinoma_predominant_subtype_concept_id 가 비어 있다 / SURGICAL 행인데 adenocarcinoma_predominant_subtype_concept_id 가 비어 있다 |
| SV-0285 PATHOLOGY_REPORT.stas_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | stas_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / stas_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0289 PATHOLOGY_REPORT.obstructive_pneumonia_atelectasis_yn 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행인데 obstructive_pneumonia_atelectasis_yn 가 비어 있다 / SURGICAL 행인데 obstructive_pneumonia_atelectasis_yn 가 비어 있다 |
| SV-0291 PATHOLOGY_REPORT.obstructive_pneumonia_atelectasis_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | obstructive_pneumonia_atelectasis_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / obstructive_pneumonia_atelectasis_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: [ |
| SV-0389 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['report_type_concept_id', 'surgical_specimen_site_concept_id', 'surgical_specimen_site_source_value'] 값 있으나 anchor specimen_date NULL / ['report_type |
| SV-0399 PATHOLOGY_TUMOR.pathology_report_id -> PATHOLOGY_REPORT.pathology_report_id 참조무결성 | Conformance | error | PATHOLOGY_TUMOR | 3 | pathology_report_id=999999999 가 PATHOLOGY_REPORT.pathology_report_id 에 없음 / pathology_report_id=999999999 가 PATHOLOGY_REPORT.pathology_report_id 에 없음 |
| SV-0410 BIOMARKER.person_id 필수 | Completeness | error | BIOMARKER | 3 | person_id NULL / person_id NULL |
| SV-0414 BIOMARKER.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | BIOMARKER | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0416 BIOMARKER.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | BIOMARKER | 7 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=100485 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0417 BIOMARKER.test_date 필수 | Completeness | error | BIOMARKER | 3 | test_date NULL / test_date NULL |
| SV-0422 BIOMARKER.ihc_test_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | ihc_test_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / ihc_test_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가  |
| SV-0425 BIOMARKER.molecular_pathology_test_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | molecular_pathology_test_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / molecular_pathology_test_concept_id=10000099999 는 값 집합(B |
| SV-0429 BIOMARKER.mutation_test_gene_concept_id 필수(코드 또는 원천값) | Completeness | error | BIOMARKER | 3 | mutation_test_gene_concept_id 와 mutation_test_gene_source_value 가 모두 비어 있다 / mutation_test_gene_concept_id 와 mutation_test_gene_source_value 가 모두 비어 있 |
| SV-0583 BIOMARKER 사건 날짜 필수 | Completeness | error | BIOMARKER | 3 | ['ihc_test_concept_id', 'ihc_test_source_value', 'molecular_pathology_test_concept_id'] 값 있으나 anchor test_date NULL / ['ihc_test_concept_id', 'ihc_tes |
| SV-0592 LUNG_EXAM.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | LUNG_EXAM | 1 | visit_occurrence_id=100099 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2024-01-15 < visit_start_date 2024-01-16 / visit_end_date 2023-12-21 < visit_start_date 2023-12-22 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1975 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1954 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | DEATH | 2 | 사건일 2026-08-31 가 사망일 2025-01-17 보다 뒤다 / 사건일 2026-08-31 가 사망일 2021-11-18 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD | 2 | visit_start_date 1890-01-01 가 관찰기간 [2019-12-28, 2026-02-02] 밖이다 / visit_start_date 1890-01-01 가 관찰기간 [2019-11-09, 2021-11-18] 밖이다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | VISIT_OCCURRENCE | 8 | 사건일 2099-01-01 가 방문 [2020-10-22, 2020-10-22] 밖이다 / 사건일 2099-01-01 가 방문 [2022-01-20, 2022-01-20] 밖이다 |
| SEMV-COM-007 이벤트-방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | 사건의 person_id 999999999 와 방문의 person_id 100013 가 다르다 / 사건의 person_id 999999999 와 방문의 person_id 100031 가 다르다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | days_supply 99 가 기간(7일) 과 다르다 / days_supply 99 가 기간(1일) 과 다르다 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 2 | episode_end_date 2000-01-01 < episode_start_date 2021-10-03 / episode_end_date 2000-01-01 < episode_start_date 2021-03-11 |
| SEMV-EP-002 에피소드에 매단 사건이 실제로 있음 | Conformance | error | EPISODE,EPISODE_EVENT | 2 | F_DRUG 가 가리킨 사건 100316 이 대상 테이블에 없다 / F_CONDITION 가 가리킨 사건 100083 이 대상 테이블에 없다 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 3 | 레지멘 기간 [2021-10-03, 2000-01-01] 이 연결 약물 기간 [2021-10-03, 2021-12-05] 을 담지 못한다 / 레지멘 기간 [2022-03-27, 2022-06-18] 이 연결 약물 기간 [2019-05-03, 2022-05-29] 을 담 |
| SEMV-EP-004 에피소드와 연결 사건의 환자 일치 | Conformance | error | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 1 | 에피소드 환자 100029 와 약물 환자 100034 가 다르다 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 2 | 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2022-03-06 와 다르다 / 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2021-04-27 와 다르다 |
| SEMV-PA-002 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | PATHOLOGY_REPORT | 2 | 침윤 999.0 > 절제 8.0 / 침윤 999.0 > 절제 26.0 |
| SEMV-PA-003 수술 병리 검체일 >= 수술일 | Plausibility | error | PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE | 1 | 수술 병리 검체일 2023-12-03 앞 60일 안에 시술 기록이 없다 |
