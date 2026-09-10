# 데이터 품질 검증 보고서: MASLD (대사이상지방간)

검증일 2026-09-07 / 테이블 10개 / 규칙 358개 (실패 44, 건너뜀 9, 오류 0)

위반 145건 (error 76, warning 69)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 219 | 17 | 50 |
| Completeness | 61 | 12 | 26 |
| Plausibility | 78 | 15 | 69 |

## 테이블 행수

- PERSON: 100
- VISIT_OCCURRENCE: 1386
- PROCEDURE_OCCURRENCE: 301
- DRUG_EXPOSURE: 2422
- CONDITION_OCCURRENCE: 321
- MEASUREMENT: 10742
- OBSERVATION: 894
- NOTE: 446
- MASLD: 8324
- ADVERSE_EVENT: 15

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| ST-0002 PERSON 컬럼 구성 | Conformance | error | PERSON | 1 | 명세에 없는 컬럼: extra_col (경고) |
| ST-0005 PERSON.gender_concept_id 필수 | Completeness | error | PERSON | 3 | gender_concept_id NULL / gender_concept_id NULL |
| ST-0007 PERSON.gender_concept_id 코드표 | Conformance | warning | PERSON | 3 | gender_concept_id=9999 코드표(OMOP.gender_concept_id) 밖 / gender_concept_id=9999 코드표(OMOP.gender_concept_id) 밖 |
| ST-0034 VISIT_OCCURRENCE.visit_start_date 필수 | Completeness | error | VISIT_OCCURRENCE | 3 | visit_start_date NULL / visit_start_date NULL |
| ST-0035 VISIT_OCCURRENCE.visit_start_date 타입(date) | Conformance | error | VISIT_OCCURRENCE | 3 | visit_start_date='2024/13/40' 은 date 아님 / visit_start_date='2024/13/40' 은 date 아님 |
| ST-0065 DRUG_EXPOSURE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | DRUG_EXPOSURE | 3 | visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=999999999 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0101 DRUG_EXPOSURE.antp_id 비항암 코호트 NULL | Conformance | error | DRUG_EXPOSURE | 3 | antp_id=1 (이 코호트에서는 NULL 이어야 함) / antp_id=1 (이 코호트에서는 NULL 이어야 함) |
| ST-0114 CONDITION_OCCURRENCE.condition_start_date 타입(date) | Conformance | error | CONDITION_OCCURRENCE | 3 | condition_start_date='2023-02-30' 은 date 아님 / condition_start_date='2023-02-30' 은 date 아님 |
| ST-0121 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 6 | PK 중복: 405321 / PK 중복: 407907 |
| ST-0136 MEASUREMENT.value_as_number 타입(float) | Conformance | error | MEASUREMENT | 3 | value_as_number='N/A' 은 float 아님 / value_as_number='N/A' 은 float 아님 |
| ST-0146 OBSERVATION 컬럼 구성 | Conformance | error | OBSERVATION | 1 | 컬럼 누락: value_as_string |
| ST-0177 NOTE.note_date 미래 날짜 금지 | Plausibility | error | NOTE | 3 | note_date=2030-01-01 미래 날짜 / note_date=2030-01-01 미래 날짜 |
| ST-0658 MASLD.person_id -> PERSON.person_id 참조무결성 | Conformance | error | MASLD | 3 | person_id=888888888 가 PERSON.person_id 에 없음 / person_id=888888888 가 PERSON.person_id 에 없음 |
| ST-0679 MASLD.fib4_score 범위 | Plausibility | warning | MASLD | 2 | fib4_score=1500 범위 [0,50] 밖 / fib4_score=1500 범위 [0,50] 밖 |
| ST-0681 MASLD.apri_score 범위 | Plausibility | warning | MASLD | 2 | apri_score=1300 범위 [0,30] 밖 / apri_score=1300 범위 [0,30] 밖 |
| ST-0739 MASLD 그룹 'score' anchor 날짜 | Completeness | error | MASLD | 1 | ['fib4_score', 'exam_gnrx_idx_nm', 'exam_gnrx_rslt_vl'] 값 있으나 anchor exam_gnrx_ymd NULL |
| ST-0740 MASLD 그룹 'imex' anchor 날짜 | Completeness | error | MASLD | 1 | ['imex_rslt_cont', 'lver_fbrs_grnm', 'imex_kncd'] 값 있으나 anchor imex_ymd NULL |
| ST-0741 MASLD 그룹 'hist' anchor 날짜 | Completeness | error | MASLD | 1 | ['drnk_dtrn_ycnt', 'drnk_nt', 'drnk_qty'] 값 있으나 anchor rcrd_ymd NULL |
| ST-0742 MASLD 그룹 'anth' anchor 날짜 | Completeness | error | MASLD | 1 | ['ht_msrm_vl', 'wt_msrm_vl', 'bmi_vl'] 값 있으나 anchor anth_rcrd_ymd NULL |
| ST-0743 MASLD 그룹 'oprt' anchor 날짜 | Completeness | error | MASLD | 1 | ['oprt_kncd', 'oprt_knnm'] 값 있으나 anchor oprt_ymd NULL |
| ST-0744 MASLD 그룹 'proc' anchor 날짜 | Completeness | error | MASLD | 1 | ['care_site_id'] 값 있으나 anchor procedure_occurrence_crtn_dt NULL |
| ST-0746 MASLD 환자 불변 필드 일관성 | Plausibility | warning | MASLD | 4 | date_of_birth 값이 환자 내에서 다름: ['1950-01-01', '1967-07-21'] / date_of_birth 값이 환자 내에서 다름: ['1950-01-01', '1973-06-11'] |
| ST-1054 ADVERSE_EVENT 컬럼 구성 | Conformance | error | ADVERSE_EVENT | 1 | 별칭 컬럼 antp_therapy_id 를 antp_id 로 해석함 (경고) |
| ST-1084 ADVERSE_EVENT.severity_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 3 | severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 / severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 |
| SEM-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2000-01-01 < visit_start_date 2026-05-09 / visit_end_date 2000-01-01 < visit_start_date 2021-05-04 |
| SEM-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | PERSON | 4 | 이벤트일 2026-08-30 > death_date 2025-07-29 / 이벤트일 2026-08-30 > death_date 2024-10-01 |
| SEM-COM-005 이벤트-방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 400056 의 person_id=400005 / visit 400128 의 person_id=400012 |
| SEM-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | VISIT_OCCURRENCE | 24 | 이벤트일 2021-05-04 가 방문기간 2021-05-04~2000-01-01 밖 / 이벤트일 2026-05-09 가 방문기간 2026-05-09~2000-01-01 밖 |
| SEM-COM-007 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | end < start / end < start |
| SEM-COM-008 투여 빈도/간격 조건부 필수 | Completeness | warning | DRUG_EXPOSURE | 3 | frequency_per_day 있음, days_supply 없음 / frequency_per_day 있음, days_supply 없음 |
| SEM-COM-009 검사 결과값 존재 | Completeness | error | MEASUREMENT | 6 | value_as_number, value_as_concept_id 모두 NULL / value_as_number, value_as_concept_id 모두 NULL |
| SEM-COM-011 검사항목별 타당 범위 | Plausibility | warning | MEASUREMENT | 3 | ALT=99999.0 (타당범위 0.0~5000.0) / Body weight=99999.0 (타당범위 20.0~250.0) |
| SEM-COM-012 age_at_index 와 index date 일치 | Plausibility | error | CONDITION_OCCURRENCE,PERSON | 3 | age_at_index=73, index_date=2024-07-13, year_of_birth=1966 / age_at_index=78, index_date=2019-03-29, year_of_birth=1956 |
| SEM-COM-013 코호트 포함 조건 | Completeness | error | CONDITION_OCCURRENCE,PERSON,VISIT_OCCURRENCE | 2 | 코호트 정의 진단 없음 / 코호트 정의 진단 없음 |
| SEM-COM-015 특화 테이블 고아 환자 | Conformance | error | PERSON | 1 | PERSON 에 없는 person_id |
| SEM-COM-017 중대한 이상사례 조건부 필수 / 치명 결과와 사망 일치 | Completeness | error | ADVERSE_EVENT,PERSON | 3 | is_serious=1 인데 seriousness_concept_id 없음 / is_serious=1 인데 seriousness_concept_id 없음 |
| SEM-COM-023 중복 이벤트 레코드 | Plausibility | warning | MEASUREMENT | 3 | 2건 중복 / 2건 중복 |
| SEM-COM-029 특화 테이블 death_date 와 PERSON 일치 | Conformance | error | PERSON | 3 | MASLD.death_date=2024-01-01 <> PERSON.death_date=NULL / MASLD.death_date=2024-01-01 <> PERSON.death_date=NULL |
| SEM-COM-030 특화 테이블 방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 400216 의 person_id=400018 / visit 400892 의 person_id=400065 |
| SEM-CA-004 BMI = 체중 / 신장^2 | Plausibility | warning | MASLD | 2 | bmi_vl=19.9 vs 계산값 22.2 / bmi_vl=19.9 vs 계산값 23.5 |
| SEM-MA-001 FIB-4 재계산 일치 | Plausibility | warning | MEASUREMENT,PERSON | 9 | fib4_score=1500.0 vs 재계산 1.39 / fib4_score=2.57 vs 재계산 0.07 |
| SEM-MA-002 지표 산출용 나이 = 검사일 기준 만 나이 | Plausibility | warning | PERSON | 2 | age=66, exam 2023-11-02, birth 1977 / age=81, exam 2024-10-04, birth 1963 |
| SEM-MA-003 음주량이 MASLD 정의 임계 미만 | Plausibility | warning | PERSON | 2 | 주당 알코올 4186.0g / 주당 알코올 4186.0g |
| SEM-MA-004 예후 척도 명칭과 점수 컬럼 일치 | Conformance | warning | MASLD | 7 | FIB-4 결과값 1.39 이 점수 컬럼과 불일치 / APRI 결과값 0.42 이 점수 컬럼과 불일치 |
