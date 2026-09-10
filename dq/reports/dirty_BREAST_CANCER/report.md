# 데이터 품질 검증 보고서: BREAST_CANCER (유방암)

검증일 2026-09-07 / 테이블 11개 / 규칙 463개 (실패 52, 건너뜀 0, 오류 0)

위반 154건 (error 88, warning 66)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 276 | 19 | 54 |
| Completeness | 79 | 13 | 29 |
| Plausibility | 108 | 20 | 71 |

## 테이블 행수

- PERSON: 100
- VISIT_OCCURRENCE: 3366
- PROCEDURE_OCCURRENCE: 1326
- DRUG_EXPOSURE: 2354
- CONDITION_OCCURRENCE: 388
- MEASUREMENT: 8348
- OBSERVATION: 100
- NOTE: 560
- BREAST_CANCER: 5121
- ADVERSE_EVENT: 247
- ANTP_THERAPY: 177

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| ST-0002 PERSON 컬럼 구성 | Conformance | error | PERSON | 1 | 명세에 없는 컬럼: extra_col (경고) |
| ST-0005 PERSON.gender_concept_id 필수 | Completeness | error | PERSON | 3 | gender_concept_id NULL / gender_concept_id NULL |
| ST-0007 PERSON.gender_concept_id 코드표 | Conformance | warning | PERSON | 3 | gender_concept_id=9999 코드표(OMOP.gender_concept_id) 밖 / gender_concept_id=9999 코드표(OMOP.gender_concept_id) 밖 |
| ST-0034 VISIT_OCCURRENCE.visit_start_date 필수 | Completeness | error | VISIT_OCCURRENCE | 3 | visit_start_date NULL / visit_start_date NULL |
| ST-0035 VISIT_OCCURRENCE.visit_start_date 타입(date) | Conformance | error | VISIT_OCCURRENCE | 3 | visit_start_date='2024/13/40' 은 date 아님 / visit_start_date='2024/13/40' 은 date 아님 |
| ST-0065 DRUG_EXPOSURE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | DRUG_EXPOSURE | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0114 CONDITION_OCCURRENCE.condition_start_date 타입(date) | Conformance | error | CONDITION_OCCURRENCE | 3 | condition_start_date='2023-02-30' 은 date 아님 / condition_start_date='2023-02-30' 은 date 아님 |
| ST-0121 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 6 | PK 중복: 204135 / PK 중복: 206145 |
| ST-0136 MEASUREMENT.value_as_number 타입(float) | Conformance | error | MEASUREMENT | 3 | value_as_number='N/A' 은 float 아님 / value_as_number='N/A' 은 float 아님 |
| ST-0146 OBSERVATION 컬럼 구성 | Conformance | error | OBSERVATION | 1 | 컬럼 누락: value_as_string |
| ST-0177 NOTE.note_date 미래 날짜 금지 | Plausibility | error | NOTE | 3 | note_date=2030-01-01 미래 날짜 / note_date=2030-01-01 미래 날짜 |
| ST-0327 BREAST_CANCER.person_id -> PERSON.person_id 참조무결성 | Conformance | error | BREAST_CANCER | 3 | person_id=888888888 가 PERSON.person_id 에 없음 / person_id=888888888 가 PERSON.person_id 에 없음 |
| ST-0334 BREAST_CANCER.menopause_status 코드표 | Conformance | error | BREAST_CANCER | 3 | menopause_status=99 코드표(BREAST_CANCER.menopause_status) 밖 / menopause_status=99 코드표(BREAST_CANCER.menopause_status) 밖 |
| ST-0368 BREAST_CANCER.hrt_impl_mcnt 범위 | Plausibility | warning | BREAST_CANCER | 2 | hrt_impl_mcnt=7000 범위 [0,600] 밖 / hrt_impl_mcnt=7000 범위 [0,600] 밖 |
| ST-0370 BREAST_CANCER.mena_age_vl 범위 | Plausibility | warning | BREAST_CANCER | 2 | mena_age_vl=1200 범위 [8,20] 밖 / mena_age_vl=1200 범위 [8,20] 밖 |
| ST-0377 BREAST_CANCER.brcn_diag_kncd 패턴 | Conformance | warning | BREAST_CANCER | 5 | brcn_diag_kncd='C50.1_X' 패턴 불일치 / brcn_diag_kncd='Stage 4?' 패턴 불일치 |
| ST-0404 BREAST_CANCER.afop_path_t_stag_vl 패턴 | Conformance | warning | BREAST_CANCER | 2 | afop_path_t_stag_vl='Stage 4?' 패턴 불일치 / afop_path_t_stag_vl='Stage 4?' 패턴 불일치 |
| ST-0471 BREAST_CANCER 그룹 'gmvx' anchor 날짜 | Completeness | error | BREAST_CANCER | 1 | ['gmvx_mtcd', 'gmvx_mtnm', 'gmvx_gene_kncd'] 값 있으나 anchor gmvx_ymd NULL |
| ST-0472 BREAST_CANCER 그룹 'gnrx' anchor 날짜 | Completeness | error | BREAST_CANCER | 1 | ['gnrx_kncd', 'gnrx_knnm', 'gnrx_rslt_kncd'] 값 있으나 anchor gnrx_ymd NULL |
| ST-0474 BREAST_CANCER 그룹 'mlem' anchor 날짜 | Completeness | error | BREAST_CANCER | 1 | ['mlem_rslt_kncd', 'mlem_rslt_knnm', 'mlem_rslt_vl'] 값 있으나 anchor mlem_ymd NULL |
| ST-0486 BREAST_CANCER 그룹 'imex' anchor 날짜 | Completeness | error | BREAST_CANCER | 1 | ['brst_dens_clcd', 'brst_dens_clnm', 'imex_rslt_diag_clcd'] 값 있으나 anchor imex_ymd NULL |
| ST-0487 BREAST_CANCER 그룹 'bpsy' anchor 날짜 | Completeness | error | BREAST_CANCER | 1 | ['bpsy_site_cd', 'bpsy_site_nm', 'bpsy_site_latr_cd'] 값 있으나 anchor bpsy_ymd NULL |
| ST-0488 BREAST_CANCER 그룹 'obtr' anchor 날짜 | Completeness | error | BREAST_CANCER | 1 | ['menopause_status', 'pregnant_at_diagnosis', 'history_of_live_birth'] 값 있으나 anchor obtr_rcrd_ymd NULL |
| ST-0491 BREAST_CANCER 환자 불변 필드 일관성 | Plausibility | warning | BREAST_CANCER | 5 | brcn_diag_kncd 값이 환자 내에서 다름: ['C50.1', 'C50.1_X'] / brcn_diag_kncd 값이 환자 내에서 다름: ['C50.1', 'Stage 4?'] |
| ST-1054 ADVERSE_EVENT 컬럼 구성 | Conformance | error | ADVERSE_EVENT | 1 | 별칭 컬럼 antp_therapy_id 를 antp_id 로 해석함 (경고) |
| ST-1084 ADVERSE_EVENT.severity_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 3 | severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 / severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 |
| SEM-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2000-01-01 < visit_start_date 2024-09-05 / visit_end_date 2000-01-01 < visit_start_date 2021-02-16 |
| SEM-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | PERSON | 3 | 이벤트일 2026-08-30 > death_date 2025-09-23 / 이벤트일 2026-08-30 > death_date 2021-03-07 |
| SEM-COM-005 이벤트-방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 200393 의 person_id=200013 / visit 200575 의 person_id=200019 |
| SEM-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | VISIT_OCCURRENCE | 18 | 이벤트일 2024-09-05 가 방문기간 2024-09-05~2000-01-01 밖 / 이벤트일 2024-09-05 가 방문기간 2024-09-05~2000-01-01 밖 |
| SEM-COM-007 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | end < start / end < start |
| SEM-COM-008 투여 빈도/간격 조건부 필수 | Completeness | warning | DRUG_EXPOSURE | 3 | frequency_per_day 있음, days_supply 없음 / frequency_per_day 있음, days_supply 없음 |
| SEM-COM-009 검사 결과값 존재 | Completeness | error | MEASUREMENT | 6 | value_as_number, value_as_concept_id 모두 NULL / value_as_number, value_as_concept_id 모두 NULL |
| SEM-COM-011 검사항목별 타당 범위 | Plausibility | warning | MEASUREMENT | 3 | Leukocytes=99999.0 (타당범위 0.1~500.0) / Platelet count=99999.0 (타당범위 1.0~2000.0) |
| SEM-COM-012 age_at_index 와 index date 일치 | Plausibility | error | CONDITION_OCCURRENCE,PERSON | 3 | age_at_index=68, index_date=2020-06-20, year_of_birth=1967 / age_at_index=47, index_date=2019-07-29, year_of_birth=1987 |
| SEM-COM-013 코호트 포함 조건 | Completeness | error | CONDITION_OCCURRENCE,PERSON,VISIT_OCCURRENCE | 2 | 코호트 정의 진단 없음 / 코호트 정의 진단 없음 |
| SEM-COM-015 특화 테이블 고아 환자 | Conformance | error | PERSON | 1 | PERSON 에 없는 person_id |
| SEM-COM-016 이상사례 발생일 >= 항암 시작일 | Plausibility | error | ADVERSE_EVENT,ANTP_THERAPY | 3 | AE 2015-01-01 < antp_start_date 2020-12-24 / AE 2015-01-01 < antp_start_date 2025-01-08 |
| SEM-COM-017 중대한 이상사례 조건부 필수 / 치명 결과와 사망 일치 | Completeness | error | ADVERSE_EVENT,PERSON | 3 | is_serious=1 인데 seriousness_concept_id 없음 / is_serious=1 인데 seriousness_concept_id 없음 |
| SEM-COM-018 항암요법 기간 및 line 번호 | Plausibility | error | ANTP_THERAPY | 3 | line=5 이나 시작일 순서=1 / line=5 이나 시작일 순서=1 |
| SEM-COM-023 중복 이벤트 레코드 | Plausibility | warning | MEASUREMENT | 3 | 2건 중복 / 2건 중복 |
| SEM-COM-024 코호트 인구학적 분포 | Plausibility | warning | PERSON | 1 | female_ratio=0.93 (기대 0.95~1.0), median_age=51.0 (기대 40~65) |
| SEM-COM-028 처방 약물 이벤트의 핵심 테이블 존재 | Completeness | warning | DRUG_EXPOSURE | 3 | drug_prsc_ymd 2023-05-05 에 해당하는 DRUG_EXPOSURE 없음 / drug_prsc_ymd 2019-10-21 에 해당하는 DRUG_EXPOSURE 없음 |
| SEM-COM-029 특화 테이블 death_date 와 PERSON 일치 | Conformance | error | PERSON | 3 | BREAST_CANCER.death_date=2024-01-01 <> PERSON.death_date=NULL / BREAST_CANCER.death_date=2024-01-01 <> PERSON.death_date=NULL |
| SEM-COM-030 특화 테이블 방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 200538 의 person_id=200018 / visit 202094 의 person_id=200063 |
| SEM-CA-001 수술 후 외과병리일 >= 수술일 | Plausibility | error | BREAST_CANCER | 2 | srgc_ptem_ymd 2010-01-01 에 대응하는 수술(0~60일 전) 없음 / srgc_ptem_ymd 2010-01-01 에 대응하는 수술(0~60일 전) 없음 |
| SEM-CA-002 병리 TNM 조합 일치 | Conformance | warning | BREAST_CANCER | 4 | path TNM T4bN1M0 <> Stage 4?N1M0 / path TNM T1N0M1 <> T1bN0M0 |
| SEM-CA-003 방사선 총선량 = 1회 선량 x 횟수 | Plausibility | warning | BREAST_CANCER | 2 | rd_totl_gy=12.5 vs 2.0x25 / rd_totl_gy=12.5 vs 2.67x16 |
| SEM-CA-004 BMI = 체중 / 신장^2 | Plausibility | warning | BREAST_CANCER | 3 | bmi_vl=19.9 vs 계산값 24.7 / bmi_vl=19.9 vs 계산값 20.5 |
| SEM-CA-007 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | BREAST_CANCER | 2 | pstv_ln_cnt 22 > totl_ln_cnt 17 / pstv_ln_cnt 18 > totl_ln_cnt 13 |
| SEM-BC-001 유방암 코호트 성별 | Plausibility | error | PERSON | 3 | 산과 필드 있음, gender_concept_id=9999 / 산과 필드 있음, gender_concept_id=9999 |
| SEM-BC-002 폐경 상태 논리 | Plausibility | warning | BREAST_CANCER | 4 | 폐경 전인데 meno_age_vl 있음 / 첫 출산 나이 < 초경 나이 |
