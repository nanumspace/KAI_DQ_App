# 데이터 품질 검증 보고서: LUNG_CANCER (폐암)

검증일 2026-09-07 / 테이블 18개 / 규칙 377개 (실패 55, 건너뜀 1, 오류 0)

위반 159건 (error 142, warning 17)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 219 | 24 | 67 |
| Completeness | 122 | 16 | 48 |
| Plausibility | 36 | 15 | 44 |

## 테이블 행수

- PERSON: 60
- OBSERVATION_PERIOD: 60
- DEATH: 16
- VISIT_OCCURRENCE: 957
- CONDITION_OCCURRENCE: 227
- PROCEDURE_OCCURRENCE: 737
- DRUG_EXPOSURE: 548
- MEASUREMENT: 2398
- OBSERVATION: 237
- NOTE: 201
- SPECIMEN: 89
- COHORT: 60
- EPISODE: 125
- EPISODE_EVENT: 699
- PATHOLOGY_REPORT: 89
- PATHOLOGY_TUMOR: 89
- BIOMARKER: 208
- LUNG_EXAM: 523

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0015 OBSERVATION_PERIOD.observation_period_id PK 유일성 | Conformance | error | OBSERVATION_PERIOD | 3 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0017 OBSERVATION_PERIOD.observation_period_id 타입(bigint) | Conformance | error | OBSERVATION_PERIOD | 3 | observation_period_id='NOT_A_NUMBER' 은 integer 아님 / observation_period_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0040 VISIT_OCCURRENCE.visit_occurrence_id PK 유일성 | Conformance | error | VISIT_OCCURRENCE | 3 | PK 중복: NOT_A_NUMBER / PK 중복: NOT_A_NUMBER |
| SV-0042 VISIT_OCCURRENCE.visit_occurrence_id 타입(bigint) | Conformance | error | VISIT_OCCURRENCE | 3 | visit_occurrence_id='NOT_A_NUMBER' 은 integer 아님 / visit_occurrence_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0052 VISIT_OCCURRENCE.visit_end_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date=2099-01-01 미래 날짜 / visit_end_date=2099-01-01 미래 날짜 |
| SV-0059 CONDITION_OCCURRENCE.condition_occurrence_id PK 유일성 | Conformance | error | CONDITION_OCCURRENCE | 2 | PK 중복: 100139 / PK 중복: 100139 |
| SV-0085 PROCEDURE_OCCURRENCE.procedure_date 미래 날짜 금지 | Plausibility | error | PROCEDURE_OCCURRENCE | 3 | procedure_date=2099-01-01 미래 날짜 / procedure_date=2099-01-01 미래 날짜 |
| SV-0094 DRUG_EXPOSURE.drug_exposure_id PK 유일성 | Conformance | error | DRUG_EXPOSURE | 2 | PK 중복: 100423 / PK 중복: 100423 |
| SV-0099 DRUG_EXPOSURE.drug_concept_id 필수 | Completeness | error | DRUG_EXPOSURE | 3 | drug_concept_id NULL / drug_concept_id NULL |
| SV-0113 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 3 | PK NULL / PK NULL |
| SV-0114 MEASUREMENT.measurement_id 필수 | Completeness | error | MEASUREMENT | 3 | measurement_id NULL / measurement_id NULL |
| SV-0124 MEASUREMENT.measurement_type_concept_id 타입(bigint) | Conformance | error | MEASUREMENT | 3 | measurement_type_concept_id='NOT_A_NUMBER' 은 integer 아님 / measurement_type_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0135 OBSERVATION 컬럼 구성 | Conformance | error | OBSERVATION | 1 | 컬럼 누락: qualifier_concept_id |
| SV-0157 NOTE.note_id PK 유일성 | Conformance | error | NOTE | 2 | PK 중복: 100177 / PK 중복: 100177 |
| SV-0182 SPECIMEN.person_id 필수 | Completeness | error | SPECIMEN | 3 | person_id NULL / person_id NULL |
| SV-0190 SPECIMEN.specimen_date 미래 날짜 금지 | Plausibility | error | SPECIMEN | 3 | specimen_date=2099-01-01 미래 날짜 / specimen_date=2099-01-01 미래 날짜 |
| SV-0204 COHORT.cohort_start_date 미래 날짜 금지 | Plausibility | error | COHORT | 3 | cohort_start_date=2099-01-01 미래 날짜 / cohort_start_date=2099-01-01 미래 날짜 |
| SV-0244 PATHOLOGY_REPORT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0250 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0257 PATHOLOGY_REPORT.biopsy_site_concept_id 타입(bigint) | Conformance | error | PATHOLOGY_REPORT | 3 | biopsy_site_concept_id='NOT_A_NUMBER' 은 integer 아님 / biopsy_site_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0258 PATHOLOGY_REPORT.biopsy_site_concept_id 값 집합(CL_BIOPSY_SITE) | Conformance | error | PATHOLOGY_REPORT | 6 | biopsy_site_concept_id=NOT_A_NUMBER 는 값 집합(CL_BIOPSY_SITE) 의 concept_id 가 아니다 / biopsy_site_concept_id=10000099999 는 값 집합(CL_BIOPSY_SITE) 의 concept_id |
| SV-0262 PATHOLOGY_REPORT.surgical_specimen_site_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 surgical_specimen_site_concept_id 가 비어 있다 / SURGICAL 행 인데 surgical_specimen_site_concept_id 가 비어 있다 |
| SV-0265 PATHOLOGY_REPORT.biopsy_histologic_diagnosis_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | biopsy_histologic_diagnosis_concept_id 와 biopsy_histologic_diagnosis_source_value 가 모두 비어 있다 / biopsy_histologic_diagnosis_concept_id 와 biopsy_histolo |
| SV-0267 PATHOLOGY_REPORT.biopsy_differentiation_concept_id 필수(BIOPSY 행) | Completeness | error | PATHOLOGY_REPORT | 3 | BIOPSY 행 인데 biopsy_differentiation_concept_id 가 비어 있다 / BIOPSY 행 인데 biopsy_differentiation_concept_id 가 비어 있다 |
| SV-0270 PATHOLOGY_REPORT.surgical_histologic_diagnosis_concept_id 필수(SURGICAL 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | surgical_histologic_diagnosis_concept_id 와 surgical_histologic_diagnosis_source_value 가 모두 비어 있다 / surgical_histologic_diagnosis_concept_id 와 surgical |
| SV-0272 PATHOLOGY_REPORT.primary_histology_concept_id 필수(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | primary_histology_concept_id 와 primary_histology_source_value 가 모두 비어 있다 / primary_histology_concept_id 와 primary_histology_source_value 가 모두 비어 있다 |
| SV-0274 PATHOLOGY_REPORT.adenocarcinoma_predominant_subtype_concept_id 필수(SURGICAL 행)(surgical_histologic_diagnosis_source_value 에 'Adenocarcinoma' 일 때) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 이고 surgical_histologic_diagnosis_source_value 에 'Adenocarcinoma' 가 든 행 인데 adenocarcinoma_predominant_subtype_concept_id 가 비어 있다 / SURGICAL  |
| SV-0279 PATHOLOGY_REPORT.stas_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | stas_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / stas_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0283 PATHOLOGY_REPORT.obstructive_pneumonia_atelectasis_yn 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 obstructive_pneumonia_atelectasis_yn 가 비어 있다 / SURGICAL 행 인데 obstructive_pneumonia_atelectasis_yn 가 비어 있다 |
| SV-0285 PATHOLOGY_REPORT.obstructive_pneumonia_atelectasis_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | obstructive_pneumonia_atelectasis_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / obstructive_pneumonia_atelectasis_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: [ |
| SV-0383 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['report_type_concept_id', 'biopsy_method_concept_id', 'biopsy_method_source_value'] 값 있으나 anchor specimen_date NULL / ['report_type_concept_id', 'bio |
| SV-0393 PATHOLOGY_TUMOR.pathology_report_id -> PATHOLOGY_REPORT.pathology_report_id 참조무결성 | Conformance | error | PATHOLOGY_TUMOR | 3 | pathology_report_id=999999999 가 PATHOLOGY_REPORT.pathology_report_id 에 없음 / pathology_report_id=999999999 가 PATHOLOGY_REPORT.pathology_report_id 에 없음 |
| SV-0404 BIOMARKER.person_id 필수 | Completeness | error | BIOMARKER | 3 | person_id NULL / person_id NULL |
| SV-0408 BIOMARKER.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | BIOMARKER | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0410 BIOMARKER.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | BIOMARKER | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| SV-0411 BIOMARKER.test_date 필수 | Completeness | error | BIOMARKER | 3 | test_date NULL / test_date NULL |
| SV-0416 BIOMARKER.ihc_test_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | ihc_test_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / ihc_test_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가  |
| SV-0419 BIOMARKER.molecular_pathology_test_concept_id 값 집합(BIOMARKER_RESULT) | Conformance | error | BIOMARKER | 3 | molecular_pathology_test_concept_id=10000099999 는 값 집합(BIOMARKER_RESULT) 의 concept_id 가 아니다 / molecular_pathology_test_concept_id=10000099999 는 값 집합(B |
| SV-0423 BIOMARKER.mutation_test_gene_concept_id 필수(코드 또는 원천값) | Completeness | error | BIOMARKER | 3 | mutation_test_gene_concept_id 와 mutation_test_gene_source_value 가 모두 비어 있다 / mutation_test_gene_concept_id 와 mutation_test_gene_source_value 가 모두 비어 있 |
| SV-0573 BIOMARKER 사건 날짜 필수 | Completeness | error | BIOMARKER | 3 | ['ihc_test_concept_id', 'ihc_test_source_value', 'molecular_pathology_test_concept_id'] 값 있으나 anchor test_date NULL / ['ihc_test_concept_id', 'ihc_tes |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2023-02-14 < visit_start_date 2023-02-15 / visit_end_date 2023-07-23 < visit_start_date 2023-07-24 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1966 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1969 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DEATH,DRUG_EXPOSURE,MEASUREMENT,OBSERVATION,PROCEDURE_OCCURRENCE,SPECIMEN,VISIT_OCCURRENCE | 2 | 사건일 2025-01-24 가 사망일 2025-01-17 보다 뒤다 / 사건일 2022-08-05 가 사망일 2022-07-29 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 관찰기간 [2022-06-08, 2026-09-01] 밖이다 / visit_start_date 1890-01-01 가 관찰기간 [2018-07-22, 2026-09-01] 밖이다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 9 | 사건일 2099-01-01 가 방문 [2023-01-27, 2023-01-27] 밖이다 / 사건일 2099-01-01 가 방문 [2024-01-16, 2024-01-16] 밖이다 |
| SEMV-COM-007 이벤트-방문 환자 일치 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 3 | 사건의 person_id 999999999 와 방문의 person_id 100021 가 다르다 / 사건의 person_id 999999999 와 방문의 person_id 100047 가 다르다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | days_supply 99 가 기간(1일) 과 다르다 / days_supply 99 가 기간(1일) 과 다르다 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 2 | episode_end_date 2000-01-01 < episode_start_date 2021-12-26 / episode_end_date 2000-01-01 < episode_start_date 2019-11-01 |
| SEMV-EP-002 에피소드에 매단 사건이 실제로 있음 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,EPISODE,EPISODE_EVENT,PROCEDURE_OCCURRENCE | 1 | F_DRUG 가 가리킨 사건 100470 이 대상 테이블에 없다 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 3 | 레지멘 기간 [2021-12-26, 2000-01-01] 이 연결 약물 기간 [2021-12-26, 2022-02-27] 을 담지 못한다 / 레지멘 기간 [2020-08-07, 2020-10-29] 이 연결 약물 기간 [2019-08-21, 2020-10-09] 을 담 |
| SEMV-EP-004 에피소드와 연결 사건의 환자 일치 | Conformance | error | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 1 | 에피소드 환자 100045 와 약물 환자 100052 가 다르다 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 4 | 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2022-03-06 와 다르다 / 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2023-06-30 와 다르다 |
| SEMV-PA-002 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | PATHOLOGY_REPORT | 2 | 침윤 999.0 > 절제 26.0 / 침윤 999.0 > 절제 15.0 |
| SEMV-PA-003 수술 병리 검체일 >= 수술일 | Plausibility | error | PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE | 1 | 수술 병리 검체일 2020-01-11 앞 60일 안에 시술 기록이 없다 |
| SEMV-LC-001 유전자검사일 >= 검체 채취일 | Plausibility | warning | BIOMARKER,SPECIMEN | 3 | 검사일 2021-12-31 가 검체 채취일 2099-01-01 보다 이르다 / 검사일 2021-12-31 가 검체 채취일 2099-01-01 보다 이르다 |
