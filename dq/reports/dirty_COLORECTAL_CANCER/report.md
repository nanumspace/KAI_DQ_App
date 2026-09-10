# 데이터 품질 검증 보고서: COLORECTAL_CANCER (대장암)

검증일 2026-09-07 / 테이블 11개 / 규칙 450개 (실패 50, 건너뜀 0, 오류 0)

위반 155건 (error 85, warning 70)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 264 | 18 | 51 |
| Completeness | 79 | 14 | 30 |
| Plausibility | 107 | 18 | 74 |

## 테이블 행수

- PERSON: 100
- VISIT_OCCURRENCE: 2603
- PROCEDURE_OCCURRENCE: 1129
- DRUG_EXPOSURE: 2030
- CONDITION_OCCURRENCE: 500
- MEASUREMENT: 7813
- OBSERVATION: 111
- NOTE: 847
- COLORECTAL_CANCER: 5924
- ADVERSE_EVENT: 324
- ANTP_THERAPY: 97

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
| ST-0121 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 6 | PK 중복: 303870 / PK 중복: 305751 |
| ST-0136 MEASUREMENT.value_as_number 타입(float) | Conformance | error | MEASUREMENT | 3 | value_as_number='N/A' 은 float 아님 / value_as_number='N/A' 은 float 아님 |
| ST-0146 OBSERVATION 컬럼 구성 | Conformance | error | OBSERVATION | 1 | 컬럼 누락: value_as_string |
| ST-0177 NOTE.note_date 미래 날짜 금지 | Plausibility | error | NOTE | 3 | note_date=2030-01-01 미래 날짜 / note_date=2030-01-01 미래 날짜 |
| ST-0499 COLORECTAL_CANCER.person_id -> PERSON.person_id 참조무결성 | Conformance | error | COLORECTAL_CANCER | 3 | person_id=888888888 가 PERSON.person_id 에 없음 / person_id=888888888 가 PERSON.person_id 에 없음 |
| ST-0525 COLORECTAL_CANCER.drug_mdct_dtrn_mcnt 범위 | Plausibility | warning | COLORECTAL_CANCER | 2 | drug_mdct_dtrn_mcnt=3400 범위 [0,240] 밖 / drug_mdct_dtrn_mcnt=3400 범위 [0,240] 밖 |
| ST-0528 COLORECTAL_CANCER.clcn_diag_kncd 패턴 | Conformance | warning | COLORECTAL_CANCER | 5 | clcn_diag_kncd='C18.2_X' 패턴 불일치 / clcn_diag_kncd='C20_X' 패턴 불일치 |
| ST-0530 COLORECTAL_CANCER.rtcn_loca_dst_vl 범위 | Plausibility | warning | COLORECTAL_CANCER | 2 | rtcn_loca_dst_vl=1200 범위 [0,20] 밖 / rtcn_loca_dst_vl=1200 범위 [0,20] 밖 |
| ST-0563 COLORECTAL_CANCER.afop_path_t_stag_vl 패턴 | Conformance | warning | COLORECTAL_CANCER | 2 | afop_path_t_stag_vl='Stage 4?' 패턴 불일치 / afop_path_t_stag_vl='Stage 4?' 패턴 불일치 |
| ST-0631 COLORECTAL_CANCER 그룹 'imem' anchor 날짜 | Completeness | error | COLORECTAL_CANCER | 1 | ['imem_rslt_cont', 'impt_read_ymd', 'imem_kncd'] 값 있으나 anchor imem_ymd NULL |
| ST-0632 COLORECTAL_CANCER 그룹 'mlem' anchor 날짜 | Completeness | error | COLORECTAL_CANCER | 1 | ['mlem_rslt_cont', 'mlpt_read_ymd', 'mlem_opn_cd'] 값 있으나 anchor mlem_ymd NULL |
| ST-0639 COLORECTAL_CANCER 그룹 'fmht' anchor 날짜 | Completeness | error | COLORECTAL_CANCER | 1 | ['fmht_here_clcn_spcd', 'fmht_here_clcn_spnm', 'fmht_yn_noans_spcd'] 값 있으나 anchor fmht_rcrd_ymd NULL |
| ST-0645 COLORECTAL_CANCER 그룹 'imex' anchor 날짜 | Completeness | error | COLORECTAL_CANCER | 1 | ['imex_rslt_cont', 'imex_kncd', 'imex_knnm'] 값 있으나 anchor imex_ymd NULL |
| ST-0646 COLORECTAL_CANCER 그룹 'bpsy' anchor 날짜 | Completeness | error | COLORECTAL_CANCER | 1 | ['bpsy_rslt_cont', 'bpsy_read_ymd', 'bpsy_site_cd'] 값 있으나 anchor bpsy_ymd NULL |
| ST-0648 COLORECTAL_CANCER 그룹 'hist' anchor 날짜 | Completeness | error | COLORECTAL_CANCER | 1 | ['mhis_clrc_diss_spcd', 'mhis_clrc_diss_spnm', 'mhis_absg_yn_noans_spcd'] 값 있으나 anchor rcrd_ymd NULL |
| ST-0650 COLORECTAL_CANCER 환자 불변 필드 일관성 | Plausibility | warning | COLORECTAL_CANCER | 7 | clcn_diag_kncd 값이 환자 내에서 다름: ['C18.2', 'C18.2_X'] / clcn_diag_kncd 값이 환자 내에서 다름: ['C20', 'C20_X'] |
| ST-1054 ADVERSE_EVENT 컬럼 구성 | Conformance | error | ADVERSE_EVENT | 1 | 별칭 컬럼 antp_therapy_id 를 antp_id 로 해석함 (경고) |
| ST-1084 ADVERSE_EVENT.severity_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 3 | severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 / severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 |
| SEM-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2000-01-01 < visit_start_date 2026-04-24 / visit_end_date 2000-01-01 < visit_start_date 2020-09-10 |
| SEM-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | PERSON | 4 | 이벤트일 2026-08-30 > death_date 2025-04-10 / 이벤트일 2026-08-30 > death_date 2025-04-09 |
| SEM-COM-005 이벤트-방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 300297 의 person_id=300012 / visit 300386 의 person_id=300014 |
| SEM-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | VISIT_OCCURRENCE | 24 | 이벤트일 2026-08-30 가 방문기간 2022-03-24~2022-03-24 밖 / 이벤트일 2026-08-30 가 방문기간 2022-09-13~2022-09-13 밖 |
| SEM-COM-007 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | end < start / end < start |
| SEM-COM-008 투여 빈도/간격 조건부 필수 | Completeness | warning | DRUG_EXPOSURE | 3 | frequency_per_day 있음, days_supply 없음 / frequency_per_day 있음, days_supply 없음 |
| SEM-COM-009 검사 결과값 존재 | Completeness | error | MEASUREMENT | 6 | value_as_number, value_as_concept_id 모두 NULL / value_as_number, value_as_concept_id 모두 NULL |
| SEM-COM-011 검사항목별 타당 범위 | Plausibility | warning | MEASUREMENT | 3 | Hemoglobin=99999.0 (타당범위 2.0~25.0) / Creatinine=99999.0 (타당범위 0.1~30.0) |
| SEM-COM-012 age_at_index 와 index date 일치 | Plausibility | error | CONDITION_OCCURRENCE,PERSON | 3 | age_at_index=92, index_date=2022-03-18, year_of_birth=1944 / age_at_index=77, index_date=2021-10-12, year_of_birth=1959 |
| SEM-COM-013 코호트 포함 조건 | Completeness | error | CONDITION_OCCURRENCE,PERSON,VISIT_OCCURRENCE | 2 | 코호트 정의 진단 없음 / 코호트 정의 진단 없음 |
| SEM-COM-015 특화 테이블 고아 환자 | Conformance | error | PERSON | 1 | PERSON 에 없는 person_id |
| SEM-COM-016 이상사례 발생일 >= 항암 시작일 | Plausibility | error | ADVERSE_EVENT,ANTP_THERAPY | 3 | AE 2015-01-01 < antp_start_date 2024-08-04 / AE 2015-01-01 < antp_start_date 2023-02-16 |
| SEM-COM-017 중대한 이상사례 조건부 필수 / 치명 결과와 사망 일치 | Completeness | error | ADVERSE_EVENT,PERSON | 3 | is_serious=1 인데 seriousness_concept_id 없음 / is_serious=1 인데 seriousness_concept_id 없음 |
| SEM-COM-018 항암요법 기간 및 line 번호 | Plausibility | error | ANTP_THERAPY | 3 | line=5 이나 시작일 순서=1 / line=5 이나 시작일 순서=1 |
| SEM-COM-023 중복 이벤트 레코드 | Plausibility | warning | MEASUREMENT | 3 | 2건 중복 / 2건 중복 |
| SEM-COM-028 처방 약물 이벤트의 핵심 테이블 존재 | Completeness | warning | DRUG_EXPOSURE | 2 | drug_prsc_ymd 2021-08-26 에 해당하는 DRUG_EXPOSURE 없음 / drug_prsc_ymd 2024-02-16 에 해당하는 DRUG_EXPOSURE 없음 |
| SEM-COM-029 특화 테이블 death_date 와 PERSON 일치 | Conformance | error | PERSON | 3 | COLORECTAL_CANCER.death_date=2024-01-01 <> PERSON.death_date=NULL / COLORECTAL_CANCER.death_date=2024-01-01 <> PERSON.death_date=NULL |
| SEM-COM-030 특화 테이블 방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 300437 의 person_id=300016 / visit 301652 의 person_id=300062 |
| SEM-CA-001 수술 후 외과병리일 >= 수술일 | Plausibility | error | COLORECTAL_CANCER | 2 | srgc_ptem_ymd 2010-01-01 에 대응하는 수술(0~60일 전) 없음 / srgc_ptem_ymd 2010-01-01 에 대응하는 수술(0~60일 전) 없음 |
| SEM-CA-002 병리 TNM 조합 일치 | Conformance | warning | COLORECTAL_CANCER | 4 | path TNM pT1N0M0 <> Stage 4?N0M0 / path TNM pT4aN2aM0 <> Stage 4?N2aM0 |
| SEM-CA-003 방사선 총선량 = 1회 선량 x 횟수 | Plausibility | warning | COLORECTAL_CANCER | 2 | rd_totl_gy=12.5 vs 1.8x28 / rd_totl_gy=12.5 vs 1.8x28 |
| SEM-CA-004 BMI = 체중 / 신장^2 | Plausibility | warning | COLORECTAL_CANCER | 3 | bmi_vl=19.9 vs 계산값 25.3 / bmi_vl=19.9 vs 계산값 29.6 |
| SEM-CA-007 침윤 림프절 수 <= 절제 림프절 수 | Plausibility | error | COLORECTAL_CANCER | 2 | pstv_ln_cnt 20 > totl_ln_cnt 15 / pstv_ln_cnt 37 > totl_ln_cnt 32 |
| SEM-CA-008 병리 판독일 >= 검사 시행일 | Plausibility | error | COLORECTAL_CANCER | 2 | impt_read_ymd < imem_ymd / impt_read_ymd < imem_ymd |
| SEM-CC-002 개복 전환 사유 조건부 필수 | Completeness | warning | COLORECTAL_CANCER | 2 | 개복 전환 Y 인데 사유 없음 / 개복 전환 Y 인데 사유 없음 |
