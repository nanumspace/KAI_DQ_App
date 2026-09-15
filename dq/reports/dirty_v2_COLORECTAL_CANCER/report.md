# 데이터 품질 검증 보고서: COLORECTAL_CANCER (대장암)

검증일 2026-09-07 / 테이블 19개 / 규칙 461개 (실패 52, 건너뜀 2, 오류 0)

위반 158건 (error 142, warning 16)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 284 | 23 | 67 |
| Completeness | 143 | 13 | 39 |
| Plausibility | 34 | 16 | 52 |

## 테이블 행수

- PERSON: 100
- OBSERVATION_PERIOD: 100
- DEATH: 2
- VISIT_OCCURRENCE: 1496
- CONDITION_OCCURRENCE: 194
- PROCEDURE_OCCURRENCE: 613
- DRUG_EXPOSURE: 1170
- MEASUREMENT: 1852
- OBSERVATION: 0
- NOTE: 95
- SPECIMEN: 195
- COHORT: 100
- EPISODE: 155
- EPISODE_EVENT: 1459
- PATHOLOGY_REPORT: 195
- PATHOLOGY_TUMOR: 0
- BIOMARKER: 0
- COLORECTAL_EXAM: 19
- COLORECTAL_SURGERY_DETAIL: 95

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0034 DEATH.death_date 미래 날짜 금지 | Plausibility | error | DEATH | 2 | death_date=2099-01-01 미래 날짜 / death_date=2099-01-01 미래 날짜 |
| SV-0059 CONDITION_OCCURRENCE.condition_occurrence_id PK 유일성 | Conformance | error | CONDITION_OCCURRENCE | 2 | PK 중복: 300155 / PK 중복: 300155 |
| SV-0101 DRUG_EXPOSURE.drug_exposure_start_date 필수 | Completeness | error | DRUG_EXPOSURE | 3 | drug_exposure_start_date NULL / drug_exposure_start_date NULL |
| SV-0103 DRUG_EXPOSURE.drug_exposure_start_date 미래 날짜 금지 | Plausibility | error | DRUG_EXPOSURE | 3 | drug_exposure_start_date=2099-01-01 미래 날짜 / drug_exposure_start_date=2099-01-01 미래 날짜 |
| SV-0116 MEASUREMENT.person_id 필수 | Completeness | error | MEASUREMENT | 3 | person_id NULL / person_id NULL |
| SV-0122 MEASUREMENT.measurement_date 미래 날짜 금지 | Plausibility | error | MEASUREMENT | 2 | measurement_date=2099-01-08 미래 날짜 / measurement_date=2099-01-08 미래 날짜 |
| SV-0156 NOTE 컬럼 구성 | Conformance | error | NOTE | 1 | 컬럼 누락: encoding_concept_id |
| SV-0197 COHORT.cohort_definition_id+subject_id+cohort_start_date PK 유일성 | Conformance | error | COHORT | 5 | PK NULL / PK NULL |
| SV-0200 COHORT.subject_id 필수 | Completeness | error | COHORT | 3 | subject_id NULL / subject_id NULL |
| SV-0220 EPISODE.episode_parent_id 타입(bigint) | Conformance | error | EPISODE | 3 | episode_parent_id='NOT_A_NUMBER' 은 integer 아님 / episode_parent_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0237 PATHOLOGY_REPORT.pathology_report_id PK 유일성 | Conformance | error | PATHOLOGY_REPORT | 2 | PK 중복: 300004 / PK 중복: 300004 |
| SV-0244 PATHOLOGY_REPORT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0250 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0252 PATHOLOGY_REPORT.specimen_date 미래 날짜 금지 | Plausibility | error | PATHOLOGY_REPORT | 3 | specimen_date=2099-01-01 미래 날짜 / specimen_date=2099-01-01 미래 날짜 |
| SV-0265 PATHOLOGY_REPORT.biopsy_histologic_diagnosis_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | biopsy_histologic_diagnosis_concept_id 와 biopsy_histologic_diagnosis_source_value 가 모두 비어 있다 / biopsy_histologic_diagnosis_concept_id 와 biopsy_histolo |
| SV-0270 PATHOLOGY_REPORT.surgical_histologic_diagnosis_concept_id 필수(SURGICAL 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | surgical_histologic_diagnosis_concept_id 와 surgical_histologic_diagnosis_source_value 가 모두 비어 있다 / surgical_histologic_diagnosis_concept_id 와 surgical |
| SV-0292 PATHOLOGY_REPORT.lymph_nodes_positive 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 / SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 |
| SV-0332 PATHOLOGY_REPORT.gross_type_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 gross_type_concept_id 가 비어 있다 / SURGICAL 행 인데 gross_type_concept_id 가 비어 있다 |
| SV-0333 PATHOLOGY_REPORT.gross_type_concept_id 타입(bigint) | Conformance | error | PATHOLOGY_REPORT | 3 | gross_type_concept_id='NOT_A_NUMBER' 은 integer 아님 / gross_type_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0334 PATHOLOGY_REPORT.gross_type_concept_id 값 집합(CL_GROSS_TYPE) | Conformance | error | PATHOLOGY_REPORT | 3 | gross_type_concept_id=NOT_A_NUMBER 는 값 집합(CL_GROSS_TYPE) 의 concept_id 가 아니다 / gross_type_concept_id=NOT_A_NUMBER 는 값 집합(CL_GROSS_TYPE) 의 concept_id 가  |
| SV-0338 PATHOLOGY_REPORT.tumor_deposits_yn 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 tumor_deposits_yn 가 비어 있다 / SURGICAL 행 인데 tumor_deposits_yn 가 비어 있다 |
| SV-0343 PATHOLOGY_REPORT.tumor_budding_grade_concept_id 값 집합(CL_TUMOR_BUDDING_GRADE) | Conformance | error | PATHOLOGY_REPORT | 3 | tumor_budding_grade_concept_id=10000099999 는 값 집합(CL_TUMOR_BUDDING_GRADE) 의 concept_id 가 아니다 / tumor_budding_grade_concept_id=10000099999 는 값 집합(CL_TU |
| SV-0352 PATHOLOGY_REPORT.vascular_invasion_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | vascular_invasion_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / vascular_invasion_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0354 PATHOLOGY_REPORT.perineural_invasion_yn 타입(integer) | Conformance | error | PATHOLOGY_REPORT | 3 | perineural_invasion_yn='NOT_A_NUMBER' 은 integer 아님 / perineural_invasion_yn='NOT_A_NUMBER' 은 integer 아님 |
| SV-0355 PATHOLOGY_REPORT.perineural_invasion_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | perineural_invasion_yn=NOT_A_NUMBER 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / perineural_invasion_yn=NOT_A_NUMBER 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', ' |
| SV-0358 PATHOLOGY_REPORT.invasion_depth_concept_id 값 집합(CL_INVASION_DEPTH) | Conformance | error | PATHOLOGY_REPORT | 3 | invasion_depth_concept_id=10000099999 는 값 집합(CL_INVASION_DEPTH) 의 concept_id 가 아니다 / invasion_depth_concept_id=10000099999 는 값 집합(CL_INVASION_DEPTH) 의 |
| SV-0363 PATHOLOGY_REPORT.tme_quality_concept_id 값 집합(CL_TME_QUALITY) | Conformance | error | PATHOLOGY_REPORT | 3 | tme_quality_concept_id=10000099999 는 값 집합(CL_TME_QUALITY) 의 concept_id 가 아니다 / tme_quality_concept_id=10000099999 는 값 집합(CL_TME_QUALITY) 의 concept_id  |
| SV-0383 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['report_type_concept_id', 'report_type_source_value', 'surgical_specimen_site_concept_id'] 값 있으나 anchor specimen_date NULL / ['report_type_concept_id |
| SV-0696 COLORECTAL_EXAM.exam_date 필수 | Completeness | error | COLORECTAL_EXAM | 3 | exam_date NULL / exam_date NULL |
| SV-0698 COLORECTAL_EXAM.exam_date 미래 날짜 금지 | Plausibility | error | COLORECTAL_EXAM | 3 | exam_date=2099-01-01 미래 날짜 / exam_date=2099-01-01 미래 날짜 |
| SV-0710 COLORECTAL_EXAM.mri_distance_anorectal_junction_cm 필수 | Completeness | error | COLORECTAL_EXAM | 3 | mri_distance_anorectal_junction_cm NULL / mri_distance_anorectal_junction_cm NULL |
| SV-0728 COLORECTAL_EXAM 사건 날짜 필수 | Completeness | error | COLORECTAL_EXAM | 3 | ['rectal_tumor_height_cm', 'mri_t4b_invaded_organ_concept_id', 'mri_anterior_peritoneal_relation_concept_id'] 값 있으나 anchor exam_date NULL / ['rectal_t |
| SV-0735 COLORECTAL_SURGERY_DETAIL.person_id -> PERSON.person_id 참조무결성 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0738 COLORECTAL_SURGERY_DETAIL.procedure_occurrence_id -> PROCEDURE_OCCURRENCE.procedure_occurrence_id 참조무결성 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | procedure_occurrence_id=999999999 가 PROCEDURE_OCCURRENCE.procedure_occurrence_id 에 없음 / procedure_occurrence_id=999999999 가 PROCEDURE_OCCURRENCE.proce |
| SV-0743 COLORECTAL_SURGERY_DETAIL.preop_obstruction_treatment_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | preop_obstruction_treatment_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / preop_obstruction_treatment_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9 |
| SV-0746 COLORECTAL_SURGERY_DETAIL.stoma_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | stoma_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / stoma_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0765 COLORECTAL_SURGERY_DETAIL.conversion_to_open_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | conversion_to_open_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / conversion_to_open_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2022-04-21 < visit_start_date 2022-04-22 / visit_end_date 2019-07-03 < visit_start_date 2019-07-04 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1971 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1943 보다 이르다 |
| SEMV-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DEATH,DRUG_EXPOSURE,MEASUREMENT,OBSERVATION,PROCEDURE_OCCURRENCE,SPECIMEN,VISIT_OCCURRENCE | 2 | 사건일 2099-01-08 가 사망일 2099-01-01 보다 뒤다 / 사건일 2099-01-08 가 사망일 2099-01-01 보다 뒤다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 관찰기간 [2018-07-04, 2026-09-01] 밖이다 / visit_start_date 1890-01-01 가 관찰기간 [2019-03-24, 2026-09-01] 밖이다 |
| SEMV-COM-005 관찰기간 자체의 정합 | Plausibility | error | DEATH,OBSERVATION_PERIOD | 2 | 사망일 2099-01-01 과 관찰기간 종료 2024-07-17 가 다르다 / 사망일 2099-01-01 과 관찰기간 종료 2023-12-25 가 다르다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 12 | 사건일 2022-04-22 가 방문 [2022-04-22, 2022-04-21] 밖이다 / 사건일 2019-07-04 가 방문 [2019-07-04, 2019-07-03] 밖이다 |
| SEMV-COM-007 이벤트-방문 환자 일치 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 3 | 사건의 person_id 999999999 와 방문의 person_id 300007 가 다르다 / 사건의 person_id 999999999 와 방문의 person_id 300046 가 다르다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 6 | 종료일 2023-04-30 < 시작일 2099-01-01 / 종료일 2020-11-14 < 시작일 2099-01-01 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 2 | episode_end_date 2000-01-01 < episode_start_date 2021-11-17 / episode_end_date 2000-01-01 < episode_start_date 2020-05-18 |
| SEMV-EP-002 에피소드에 매단 사건이 실제로 있음 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,EPISODE,EPISODE_EVENT,PROCEDURE_OCCURRENCE | 1 | F_CONDITION 가 가리킨 사건 300124 이 대상 테이블에 없다 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 2 | 레지멘 기간 [2021-11-17, 2000-01-01] 이 연결 약물 기간 [2021-11-17, 2022-02-24] 을 담지 못한다 / 레지멘 기간 [2020-05-18, 2000-01-01] 이 연결 약물 기간 [2020-05-18, 2020-08-25] 을 담 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 5 | 병리 보고서의 검체일 2099-01-01 가 SPECIMEN 의 2020-11-24 와 다르다 / 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2022-10-10 와 다르다 |
| SEMV-PA-002 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | PATHOLOGY_REPORT | 2 | 침윤 999.0 > 절제 36.0 / 침윤 999.0 > 절제 37.0 |
| SEMV-PA-003 수술 병리 검체일 >= 수술일 | Plausibility | error | PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE | 4 | 수술 병리 검체일 2099-01-01 앞 60일 안에 시술 기록이 없다 / 수술 병리 검체일 2001-01-01 앞 60일 안에 시술 기록이 없다 |
