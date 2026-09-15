# 데이터 품질 검증 보고서: COLORECTAL_CANCER (대장암)

검증일 2026-09-07 / 테이블 19개 / 규칙 459개 (실패 49, 건너뜀 1, 오류 0)

위반 143건 (error 128, warning 15)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 283 | 21 | 61 |
| Completeness | 143 | 13 | 35 |
| Plausibility | 33 | 15 | 47 |

## 테이블 행수

- PERSON: 60
- OBSERVATION_PERIOD: 60
- DEATH: 4
- VISIT_OCCURRENCE: 905
- CONDITION_OCCURRENCE: 111
- PROCEDURE_OCCURRENCE: 360
- DRUG_EXPOSURE: 772
- MEASUREMENT: 1132
- OBSERVATION: 0
- NOTE: 54
- SPECIMEN: 114
- COHORT: 60
- EPISODE: 94
- EPISODE_EVENT: 937
- PATHOLOGY_REPORT: 114
- PATHOLOGY_TUMOR: 0
- BIOMARKER: 0
- COLORECTAL_EXAM: 7
- COLORECTAL_SURGERY_DETAIL: 54

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0002 PERSON 컬럼 구성 | Conformance | error | PERSON | 1 | 컬럼 누락: day_of_birth |
| SV-0034 DEATH.death_date 미래 날짜 금지 | Plausibility | error | DEATH | 3 | death_date=2099-01-01 미래 날짜 / death_date=2099-01-01 미래 날짜 |
| SV-0052 VISIT_OCCURRENCE.visit_end_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date=2099-01-01 미래 날짜 / visit_end_date=2099-01-01 미래 날짜 |
| SV-0059 CONDITION_OCCURRENCE.condition_occurrence_id PK 유일성 | Conformance | error | CONDITION_OCCURRENCE | 2 | PK 중복: 300044 / PK 중복: 300044 |
| SV-0085 PROCEDURE_OCCURRENCE.procedure_date 미래 날짜 금지 | Plausibility | error | PROCEDURE_OCCURRENCE | 3 | procedure_date=2099-01-01 미래 날짜 / procedure_date=2099-01-01 미래 날짜 |
| SV-0101 DRUG_EXPOSURE.drug_exposure_start_date 필수 | Completeness | error | DRUG_EXPOSURE | 3 | drug_exposure_start_date NULL / drug_exposure_start_date NULL |
| SV-0116 MEASUREMENT.person_id 필수 | Completeness | error | MEASUREMENT | 3 | person_id NULL / person_id NULL |
| SV-0122 MEASUREMENT.measurement_date 미래 날짜 금지 | Plausibility | error | MEASUREMENT | 4 | measurement_date=2099-01-01 미래 날짜 / measurement_date=2099-01-01 미래 날짜 |
| SV-0197 COHORT.cohort_definition_id+subject_id+cohort_start_date PK 유일성 | Conformance | error | COHORT | 5 | PK NULL / PK NULL |
| SV-0200 COHORT.subject_id 필수 | Completeness | error | COHORT | 3 | subject_id NULL / subject_id NULL |
| SV-0220 EPISODE.episode_parent_id 타입(bigint) | Conformance | error | EPISODE | 3 | episode_parent_id='NOT_A_NUMBER' 은 integer 아님 / episode_parent_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0237 PATHOLOGY_REPORT.pathology_report_id PK 유일성 | Conformance | error | PATHOLOGY_REPORT | 2 | PK 중복: 300067 / PK 중복: 300067 |
| SV-0244 PATHOLOGY_REPORT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0250 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0265 PATHOLOGY_REPORT.biopsy_histologic_diagnosis_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | biopsy_histologic_diagnosis_concept_id 와 biopsy_histologic_diagnosis_source_value 가 모두 비어 있다 / biopsy_histologic_diagnosis_concept_id 와 biopsy_histolo |
| SV-0270 PATHOLOGY_REPORT.surgical_histologic_diagnosis_concept_id 필수(SURGICAL 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | surgical_histologic_diagnosis_concept_id 와 surgical_histologic_diagnosis_source_value 가 모두 비어 있다 / surgical_histologic_diagnosis_concept_id 와 surgical |
| SV-0292 PATHOLOGY_REPORT.lymph_nodes_positive 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 / SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 |
| SV-0332 PATHOLOGY_REPORT.gross_type_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 gross_type_concept_id 가 비어 있다 / SURGICAL 행 인데 gross_type_concept_id 가 비어 있다 |
| SV-0333 PATHOLOGY_REPORT.gross_type_concept_id 타입(bigint) | Conformance | error | PATHOLOGY_REPORT | 3 | gross_type_concept_id='NOT_A_NUMBER' 은 integer 아님 / gross_type_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0334 PATHOLOGY_REPORT.gross_type_concept_id 값 집합(CL_GROSS_TYPE) | Conformance | error | PATHOLOGY_REPORT | 3 | gross_type_concept_id=NOT_A_NUMBER 는 값 집합(CL_GROSS_TYPE) 의 concept_id 가 아니다 / gross_type_concept_id=NOT_A_NUMBER 는 값 집합(CL_GROSS_TYPE) 의 concept_id 가  |
| SV-0338 PATHOLOGY_REPORT.tumor_deposits_yn 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 tumor_deposits_yn 가 비어 있다 / SURGICAL 행 인데 tumor_deposits_yn 가 비어 있다 |
| SV-0346 PATHOLOGY_REPORT.resection_completeness_concept_id 값 집합(CL_RESECTION_COMPLETENESS) | Conformance | error | PATHOLOGY_REPORT | 3 | resection_completeness_concept_id=10000099999 는 값 집합(CL_RESECTION_COMPLETENESS) 의 concept_id 가 아니다 / resection_completeness_concept_id=10000099999 는 값 |
| SV-0354 PATHOLOGY_REPORT.perineural_invasion_yn 타입(integer) | Conformance | error | PATHOLOGY_REPORT | 3 | perineural_invasion_yn='NOT_A_NUMBER' 은 integer 아님 / perineural_invasion_yn='NOT_A_NUMBER' 은 integer 아님 |
| SV-0355 PATHOLOGY_REPORT.perineural_invasion_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 6 | perineural_invasion_yn=NOT_A_NUMBER 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / perineural_invasion_yn=NOT_A_NUMBER 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', ' |
| SV-0383 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['report_type_concept_id', 'report_type_source_value', 'surgical_specimen_site_concept_id'] 값 있으나 anchor specimen_date NULL / ['report_type_concept_id |
| SV-0696 COLORECTAL_EXAM.exam_date 필수 | Completeness | error | COLORECTAL_EXAM | 1 | exam_date NULL |
| SV-0710 COLORECTAL_EXAM.mri_distance_anorectal_junction_cm 필수 | Completeness | error | COLORECTAL_EXAM | 3 | mri_distance_anorectal_junction_cm NULL / mri_distance_anorectal_junction_cm NULL |
| SV-0722 COLORECTAL_EXAM.mri_extramesorectal_node_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_EXAM | 3 | mri_extramesorectal_node_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / mri_extramesorectal_node_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0728 COLORECTAL_EXAM 사건 날짜 필수 | Completeness | error | COLORECTAL_EXAM | 1 | ['rectal_tumor_height_cm', 'mri_t4b_invaded_organ_concept_id', 'mri_anterior_peritoneal_relation_concept_id'] 값 있으나 anchor exam_date NULL |
| SV-0735 COLORECTAL_SURGERY_DETAIL.person_id -> PERSON.person_id 참조무결성 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0738 COLORECTAL_SURGERY_DETAIL.procedure_occurrence_id -> PROCEDURE_OCCURRENCE.procedure_occurrence_id 참조무결성 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | procedure_occurrence_id=999999999 가 PROCEDURE_OCCURRENCE.procedure_occurrence_id 에 없음 / procedure_occurrence_id=999999999 가 PROCEDURE_OCCURRENCE.proce |
| SV-0746 COLORECTAL_SURGERY_DETAIL.stoma_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | stoma_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / stoma_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0756 COLORECTAL_SURGERY_DETAIL.anastomosis_method_concept_id 값 집합(CL_ANASTOMOSIS_METHOD) | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | anastomosis_method_concept_id=10000099999 는 값 집합(CL_ANASTOMOSIS_METHOD) 의 concept_id 가 아니다 / anastomosis_method_concept_id=10000099999 는 값 집합(CL_ANAST |
| SV-0762 COLORECTAL_SURGERY_DETAIL.hipec_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | hipec_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / hipec_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2022-03-10 < visit_start_date 2022-03-11 / visit_end_date 2023-02-15 < visit_start_date 2023-02-16 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1957 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1951 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DEATH,DRUG_EXPOSURE,MEASUREMENT,OBSERVATION,PROCEDURE_OCCURRENCE,SPECIMEN,VISIT_OCCURRENCE | 2 | 사건일 2022-09-15 가 사망일 2022-09-08 보다 뒤다 / 사건일 2099-01-08 가 사망일 2099-01-01 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 관찰기간 [2018-04-05, 2026-09-01] 밖이다 / visit_start_date 1890-01-01 가 관찰기간 [2017-05-06, 2026-09-01] 밖이다 |
| SEMV-COM-005 관찰기간 자체의 정합 | Plausibility | error | DEATH,OBSERVATION_PERIOD | 3 | 사망일 2099-01-01 과 관찰기간 종료 2023-11-19 가 다르다 / 사망일 2099-01-01 과 관찰기간 종료 2023-06-23 가 다르다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 11 | 사건일 2099-01-01 가 방문 [2020-06-20, 2020-06-20] 밖이다 / 사건일 2022-03-11 가 방문 [2022-03-11, 2022-03-10] 밖이다 |
| SEMV-COM-007 이벤트-방문 환자 일치 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 3 | 사건의 person_id 999999999 와 방문의 person_id 300004 가 다르다 / 사건의 person_id 999999999 와 방문의 person_id 300027 가 다르다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | days_supply 99 가 기간(2일) 과 다르다 / days_supply 99 가 기간(2일) 과 다르다 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 2 | episode_end_date 2000-01-01 < episode_start_date 2022-02-14 / episode_end_date 2000-01-01 < episode_start_date 2021-03-04 |
| SEMV-EP-002 에피소드에 매단 사건이 실제로 있음 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,EPISODE,EPISODE_EVENT,PROCEDURE_OCCURRENCE | 1 | F_CONDITION 가 가리킨 사건 300066 이 대상 테이블에 없다 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 2 | 레지멘 기간 [2022-02-14, 2000-01-01] 이 연결 약물 기간 [2022-02-14, 2022-05-24] 을 담지 못한다 / 레지멘 기간 [2021-03-04, 2000-01-01] 이 연결 약물 기간 [2021-03-04, 2021-06-11] 을 담 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 2 | 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2021-12-23 와 다르다 / 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2019-04-29 와 다르다 |
| SEMV-PA-002 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | PATHOLOGY_REPORT | 2 | 침윤 999.0 > 절제 15.0 / 침윤 999.0 > 절제 19.0 |
| SEMV-PA-003 수술 병리 검체일 >= 수술일 | Plausibility | error | PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE | 2 | 수술 병리 검체일 2019-05-19 앞 60일 안에 시술 기록이 없다 / 수술 병리 검체일 2001-01-01 앞 60일 안에 시술 기록이 없다 |
