# 데이터 품질 검증 보고서: COLORECTAL_CANCER (대장암)

검증일 2026-09-07 / 테이블 19개 / 규칙 461개 (실패 47, 건너뜀 2, 오류 0)

위반 172건 (error 139, warning 33)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 284 | 21 | 66 |
| Completeness | 143 | 13 | 39 |
| Plausibility | 34 | 13 | 67 |

## 테이블 행수

- PERSON: 60
- OBSERVATION_PERIOD: 60
- DEATH: 0
- VISIT_OCCURRENCE: 933
- CONDITION_OCCURRENCE: 120
- PROCEDURE_OCCURRENCE: 369
- DRUG_EXPOSURE: 776
- MEASUREMENT: 1140
- OBSERVATION: 0
- NOTE: 57
- SPECIMEN: 117
- COHORT: 60
- EPISODE: 97
- EPISODE_EVENT: 953
- PATHOLOGY_REPORT: 117
- PATHOLOGY_TUMOR: 0
- BIOMARKER: 0
- COLORECTAL_EXAM: 12
- COLORECTAL_SURGERY_DETAIL: 57

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| SV-0049 VISIT_OCCURRENCE.visit_start_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_start_date=2099-01-01 미래 날짜 / visit_start_date=2099-01-01 미래 날짜 |
| SV-0076 PROCEDURE_OCCURRENCE.procedure_occurrence_id PK 유일성 | Conformance | error | PROCEDURE_OCCURRENCE | 2 | PK 중복: 300295 / PK 중복: 300295 |
| SV-0080 PROCEDURE_OCCURRENCE.person_id 타입(bigint) | Conformance | error | PROCEDURE_OCCURRENCE | 3 | person_id='NOT_A_NUMBER' 은 integer 아님 / person_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0103 DRUG_EXPOSURE.drug_exposure_start_date 미래 날짜 금지 | Plausibility | error | DRUG_EXPOSURE | 3 | drug_exposure_start_date=2099-01-01 미래 날짜 / drug_exposure_start_date=2099-01-01 미래 날짜 |
| SV-0113 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 3 | PK NULL / PK NULL |
| SV-0114 MEASUREMENT.measurement_id 필수 | Completeness | error | MEASUREMENT | 3 | measurement_id NULL / measurement_id NULL |
| SV-0120 MEASUREMENT.measurement_date 필수 | Completeness | error | MEASUREMENT | 3 | measurement_date NULL / measurement_date NULL |
| SV-0156 NOTE 컬럼 구성 | Conformance | error | NOTE | 1 | 컬럼 누락: encoding_concept_id |
| SV-0205 COHORT.cohort_end_date 필수 | Completeness | error | COHORT | 3 | cohort_end_date NULL / cohort_end_date NULL |
| SV-0209 EPISODE.episode_id PK 유일성 | Conformance | error | EPISODE | 2 | PK 중복: 300074 / PK 중복: 300074 |
| SV-0221 EPISODE.episode_number 타입(integer) | Conformance | error | EPISODE | 3 | episode_number='NOT_A_NUMBER' 은 integer 아님 / episode_number='NOT_A_NUMBER' 은 integer 아님 |
| SV-0237 PATHOLOGY_REPORT.pathology_report_id PK 유일성 | Conformance | error | PATHOLOGY_REPORT | 2 | PK 중복: 300003 / PK 중복: 300003 |
| SV-0244 PATHOLOGY_REPORT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0247 PATHOLOGY_REPORT.specimen_id -> SPECIMEN.specimen_id 참조무결성 | Conformance | error | PATHOLOGY_REPORT | 3 | specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 / specimen_id=999999999 가 SPECIMEN.specimen_id 에 없음 |
| SV-0250 PATHOLOGY_REPORT.specimen_date 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | specimen_date NULL / specimen_date NULL |
| SV-0252 PATHOLOGY_REPORT.specimen_date 미래 날짜 금지 | Plausibility | error | PATHOLOGY_REPORT | 3 | specimen_date=2099-01-01 미래 날짜 / specimen_date=2099-01-01 미래 날짜 |
| SV-0265 PATHOLOGY_REPORT.biopsy_histologic_diagnosis_concept_id 필수(BIOPSY 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | biopsy_histologic_diagnosis_concept_id 와 biopsy_histologic_diagnosis_source_value 가 모두 비어 있다 / biopsy_histologic_diagnosis_concept_id 와 biopsy_histolo |
| SV-0270 PATHOLOGY_REPORT.surgical_histologic_diagnosis_concept_id 필수(SURGICAL 행)(코드 또는 원천값) | Completeness | error | PATHOLOGY_REPORT | 3 | surgical_histologic_diagnosis_concept_id 와 surgical_histologic_diagnosis_source_value 가 모두 비어 있다 / surgical_histologic_diagnosis_concept_id 와 surgical |
| SV-0292 PATHOLOGY_REPORT.lymph_nodes_positive 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 / SURGICAL 행 인데 lymph_nodes_positive 가 비어 있다 |
| SV-0332 PATHOLOGY_REPORT.gross_type_concept_id 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 gross_type_concept_id 가 비어 있다 / SURGICAL 행 인데 gross_type_concept_id 가 비어 있다 |
| SV-0338 PATHOLOGY_REPORT.tumor_deposits_yn 필수(SURGICAL 행) | Completeness | error | PATHOLOGY_REPORT | 3 | SURGICAL 행 인데 tumor_deposits_yn 가 비어 있다 / SURGICAL 행 인데 tumor_deposits_yn 가 비어 있다 |
| SV-0343 PATHOLOGY_REPORT.tumor_budding_grade_concept_id 값 집합(CL_TUMOR_BUDDING_GRADE) | Conformance | error | PATHOLOGY_REPORT | 3 | tumor_budding_grade_concept_id=10000099999 는 값 집합(CL_TUMOR_BUDDING_GRADE) 의 concept_id 가 아니다 / tumor_budding_grade_concept_id=10000099999 는 값 집합(CL_TU |
| SV-0352 PATHOLOGY_REPORT.vascular_invasion_yn 값 집합(YN) 코드 | Conformance | error | PATHOLOGY_REPORT | 3 | vascular_invasion_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / vascular_invasion_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0357 PATHOLOGY_REPORT.invasion_depth_concept_id 타입(bigint) | Conformance | error | PATHOLOGY_REPORT | 3 | invasion_depth_concept_id='NOT_A_NUMBER' 은 integer 아님 / invasion_depth_concept_id='NOT_A_NUMBER' 은 integer 아님 |
| SV-0358 PATHOLOGY_REPORT.invasion_depth_concept_id 값 집합(CL_INVASION_DEPTH) | Conformance | error | PATHOLOGY_REPORT | 6 | invasion_depth_concept_id=NOT_A_NUMBER 는 값 집합(CL_INVASION_DEPTH) 의 concept_id 가 아니다 / invasion_depth_concept_id=10000099999 는 값 집합(CL_INVASION_DEPTH)  |
| SV-0363 PATHOLOGY_REPORT.tme_quality_concept_id 값 집합(CL_TME_QUALITY) | Conformance | error | PATHOLOGY_REPORT | 3 | tme_quality_concept_id=10000099999 는 값 집합(CL_TME_QUALITY) 의 concept_id 가 아니다 / tme_quality_concept_id=10000099999 는 값 집합(CL_TME_QUALITY) 의 concept_id  |
| SV-0383 PATHOLOGY_REPORT 사건 날짜 필수 | Completeness | error | PATHOLOGY_REPORT | 3 | ['report_type_concept_id', 'report_type_source_value', 'biopsy_method_concept_id'] 값 있으나 anchor specimen_date NULL / ['report_type_concept_id', 'repor |
| SV-0696 COLORECTAL_EXAM.exam_date 필수 | Completeness | error | COLORECTAL_EXAM | 3 | exam_date NULL / exam_date NULL |
| SV-0698 COLORECTAL_EXAM.exam_date 미래 날짜 금지 | Plausibility | error | COLORECTAL_EXAM | 3 | exam_date=2099-01-01 미래 날짜 / exam_date=2099-01-01 미래 날짜 |
| SV-0710 COLORECTAL_EXAM.mri_distance_anorectal_junction_cm 필수 | Completeness | error | COLORECTAL_EXAM | 3 | mri_distance_anorectal_junction_cm NULL / mri_distance_anorectal_junction_cm NULL |
| SV-0728 COLORECTAL_EXAM 사건 날짜 필수 | Completeness | error | COLORECTAL_EXAM | 3 | ['rectal_tumor_height_cm', 'mri_t4b_invaded_organ_concept_id', 'mri_anterior_peritoneal_relation_concept_id'] 값 있으나 anchor exam_date NULL / ['rectal_t |
| SV-0735 COLORECTAL_SURGERY_DETAIL.person_id -> PERSON.person_id 참조무결성 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | person_id=999999999 가 PERSON.person_id 에 없음 / person_id=999999999 가 PERSON.person_id 에 없음 |
| SV-0738 COLORECTAL_SURGERY_DETAIL.procedure_occurrence_id -> PROCEDURE_OCCURRENCE.procedure_occurrence_id 참조무결성 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | procedure_occurrence_id=999999999 가 PROCEDURE_OCCURRENCE.procedure_occurrence_id 에 없음 / procedure_occurrence_id=999999999 가 PROCEDURE_OCCURRENCE.proce |
| SV-0743 COLORECTAL_SURGERY_DETAIL.preop_obstruction_treatment_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | preop_obstruction_treatment_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / preop_obstruction_treatment_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9 |
| SV-0746 COLORECTAL_SURGERY_DETAIL.stoma_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | stoma_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / stoma_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SV-0765 COLORECTAL_SURGERY_DETAIL.conversion_to_open_yn 값 집합(YN) 코드 | Conformance | error | COLORECTAL_SURGERY_DETAIL | 3 | conversion_to_open_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) / conversion_to_open_yn=7 는 값 집합(YN) 의 코드가 아니다 (허용: ['0', '1', '9']) |
| SEMV-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 6 | visit_end_date 2020-10-24 < visit_start_date 2099-01-01 / visit_end_date 2021-10-24 < visit_start_date 2021-10-25 |
| SEMV-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 2 | visit_start_date 1890-01-01 가 출생연도 1973 보다 이르다 / visit_start_date 1890-01-01 가 출생연도 1943 보다 이르다 |
| SEMV-COM-004 관찰기간 밖 이벤트 금지 | Plausibility | warning | OBSERVATION_PERIOD,VISIT_OCCURRENCE | 5 | visit_start_date 2099-01-01 가 관찰기간 [2016-03-24, 2026-09-01] 밖이다 / visit_start_date 2099-01-01 가 관찰기간 [2022-03-03, 2026-09-01] 밖이다 |
| SEMV-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 26 | 사건일 2020-10-24 가 방문 [2099-01-01, 2020-10-24] 밖이다 / 사건일 2021-10-25 가 방문 [2021-10-25, 2021-10-24] 밖이다 |
| SEMV-COM-007 이벤트-방문 환자 일치 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 6 | 사건의 person_id NOT_A_NUMBER 와 방문의 person_id 300010 가 다르다 / 사건의 person_id NOT_A_NUMBER 와 방문의 person_id 300022 가 다르다 |
| SEMV-COM-009 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 6 | 종료일 2022-01-18 < 시작일 2099-01-01 / 종료일 2023-01-19 < 시작일 2099-01-01 |
| SEMV-EP-001 에피소드 종료일 >= 시작일 | Plausibility | error | EPISODE | 2 | episode_end_date 2000-01-01 < episode_start_date 2021-02-14 / episode_end_date 2000-01-01 < episode_start_date 2020-05-03 |
| SEMV-EP-003 레지멘 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,EPISODE,EPISODE_EVENT | 2 | 레지멘 기간 [2021-02-14, 2000-01-01] 이 연결 약물 기간 [2021-02-14, 2021-07-19] 을 담지 못한다 / 레지멘 기간 [2020-05-03, 2000-01-01] 이 연결 약물 기간 [2020-05-03, 2020-10-05] 을 담 |
| SEMV-PA-001 병리 보고서의 검체일이 SPECIMEN 과 일치 | Conformance | error | PATHOLOGY_REPORT,SPECIMEN | 5 | 병리 보고서의 검체일 2099-01-01 가 SPECIMEN 의 2022-05-29 와 다르다 / 병리 보고서의 검체일 2001-01-01 가 SPECIMEN 의 2022-08-01 와 다르다 |
| SEMV-PA-002 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | PATHOLOGY_REPORT | 2 | 침윤 999.0 > 절제 32.0 / 침윤 999.0 > 절제 21.0 |
| SEMV-PA-003 수술 병리 검체일 >= 수술일 | Plausibility | error | PATHOLOGY_REPORT,PROCEDURE_OCCURRENCE | 4 | 수술 병리 검체일 2021-09-27 앞 60일 안에 시술 기록이 없다 / 수술 병리 검체일 2001-01-01 앞 60일 안에 시술 기록이 없다 |
