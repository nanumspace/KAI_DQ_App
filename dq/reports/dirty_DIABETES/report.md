# 데이터 품질 검증 보고서: DIABETES (당뇨병)

검증일 2026-09-07 / 테이블 10개 / 규칙 392개 (실패 46, 건너뜀 9, 오류 0)

위반 950건 (error 885, warning 65)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 259 | 22 | 855 |
| Completeness | 60 | 13 | 32 |
| Plausibility | 73 | 11 | 63 |

## 테이블 행수

- PERSON: 100
- VISIT_OCCURRENCE: 1684
- PROCEDURE_OCCURRENCE: 450
- DRUG_EXPOSURE: 4293
- CONDITION_OCCURRENCE: 277
- MEASUREMENT: 13235
- OBSERVATION: 100
- NOTE: 1822
- DIABETES: 21875
- ADVERSE_EVENT: 19

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
| ST-0121 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 6 | PK 중복: 506556 / PK 중복: 509742 |
| ST-0136 MEASUREMENT.value_as_number 타입(float) | Conformance | error | MEASUREMENT | 3 | value_as_number='N/A' 은 float 아님 / value_as_number='N/A' 은 float 아님 |
| ST-0146 OBSERVATION 컬럼 구성 | Conformance | error | OBSERVATION | 1 | 컬럼 누락: value_as_string |
| ST-0177 NOTE.note_date 미래 날짜 금지 | Plausibility | error | NOTE | 3 | note_date=2030-01-01 미래 날짜 / note_date=2030-01-01 미래 날짜 |
| ST-0754 DIABETES.person_id -> PERSON.person_id 참조무결성 | Conformance | error | DIABETES | 3 | person_id=888888888 가 PERSON.person_id 에 없음 / person_id=888888888 가 PERSON.person_id 에 없음 |
| ST-0758 DIABETES.condition_occurrence_id -> CONDITION_OCCURRENCE.condition_occurrence_id 참조무결성 | Conformance | error | DIABETES | 2 | condition_occurrence_id=500001 가 CONDITION_OCCURRENCE.condition_occurrence_id 에 없음 / condition_occurrence_id=500003 가 CONDITION_OCCURRENCE.condition_o |
| ST-0760 DIABETES.measurement_id -> MEASUREMENT.measurement_id 참조무결성 | Conformance | error | DIABETES | 3 | measurement_id=504158 가 MEASUREMENT.measurement_id 에 없음 / measurement_id=504461 가 MEASUREMENT.measurement_id 에 없음 |
| ST-0776 DIABETES.year_of_birth 범위 | Plausibility | warning | DIABETES | 2 | year_of_birth=21260 범위 [1900,2026] 밖 / year_of_birth=21260 범위 [1900,2026] 밖 |
| ST-0778 DIABETES.month_of_birth 범위 | Plausibility | warning | DIABETES | 2 | month_of_birth=1120 범위 [1,12] 밖 / month_of_birth=1120 범위 [1,12] 밖 |
| ST-0872 DIABETES 그룹 'visit' anchor 날짜 | Completeness | error | DIABETES | 1 | ['provider_id', 'visit_concept_id', 'visit_start_datetime'] 값 있으나 anchor visit_start_date NULL |
| ST-0873 DIABETES 그룹 'condition' anchor 날짜 | Completeness | error | DIABETES | 1 | ['condition_concept_id', 'condition_start_datetime', 'condition_type_concept_id'] 값 있으나 anchor condition_start_date NULL |
| ST-0874 DIABETES 그룹 'measurement' anchor 날짜 | Completeness | error | DIABETES | 1 | ['measurement_concept_id', 'measurement_datetime', 'measurement_time'] 값 있으나 anchor measurement_date NULL |
| ST-0875 DIABETES 그룹 'drug' anchor 날짜 | Completeness | error | DIABETES | 1 | ['drug_concept_id', 'drug_exposure_start_datetime', 'drug_exposure_end_date'] 값 있으나 anchor drug_exposure_start_date NULL |
| ST-0876 DIABETES 그룹 'death' anchor 날짜 | Completeness | error | DIABETES | 1 | ['death_datetime', 'death_type_concept_id', 'cause_concept_id'] 값 있으나 anchor death_date NULL |
| ST-0877 DIABETES 그룹 'note' anchor 날짜 | Completeness | error | DIABETES | 1 | ['note_type_concept_id', 'note_text'] 값 있으나 anchor note_date NULL |
| ST-1054 ADVERSE_EVENT 컬럼 구성 | Conformance | error | ADVERSE_EVENT | 1 | 별칭 컬럼 antp_therapy_id 를 antp_id 로 해석함 (경고) |
| ST-1084 ADVERSE_EVENT.severity_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 3 | severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 / severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 |
| SEM-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2000-01-01 < visit_start_date 2023-05-21 / visit_end_date 2000-01-01 < visit_start_date 2021-02-08 |
| SEM-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | PERSON | 3 | 이벤트일 2026-08-30 > death_date 2022-06-21 / 이벤트일 2026-08-30 > death_date 2024-12-31 |
| SEM-COM-005 이벤트-방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 500223 의 person_id=500015 / visit 500613 의 person_id=500037 |
| SEM-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | VISIT_OCCURRENCE | 36 | 이벤트일 2023-05-12 가 방문기간 2023-05-12~2000-01-01 밖 / 이벤트일 2026-08-30 가 방문기간 2018-12-05~2018-12-05 밖 |
| SEM-COM-007 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | end < start / end < start |
| SEM-COM-008 투여 빈도/간격 조건부 필수 | Completeness | warning | DRUG_EXPOSURE | 3 | frequency_per_day 있음, days_supply 없음 / frequency_per_day 있음, days_supply 없음 |
| SEM-COM-009 검사 결과값 존재 | Completeness | error | MEASUREMENT | 6 | value_as_number, value_as_concept_id 모두 NULL / value_as_number, value_as_concept_id 모두 NULL |
| SEM-COM-011 검사항목별 타당 범위 | Plausibility | warning | MEASUREMENT | 3 | Diastolic blood pressure=99999.0 (타당범위 20.0~200.0) / Creatinine=99999.0 (타당범위 0.1~30.0) |
| SEM-COM-012 age_at_index 와 index date 일치 | Plausibility | error | CONDITION_OCCURRENCE,PERSON | 3 | age_at_index=79, index_date=2021-04-28, year_of_birth=1956 / age_at_index=84, index_date=2022-08-17, year_of_birth=1952 |
| SEM-COM-013 코호트 포함 조건 | Completeness | error | CONDITION_OCCURRENCE,PERSON,VISIT_OCCURRENCE | 2 | 코호트 정의 진단 없음 / 코호트 정의 진단 없음 |
| SEM-COM-015 특화 테이블 고아 환자 | Conformance | error | PERSON | 1 | PERSON 에 없는 person_id |
| SEM-COM-017 중대한 이상사례 조건부 필수 / 치명 결과와 사망 일치 | Completeness | error | ADVERSE_EVENT,PERSON | 3 | is_serious=1 인데 seriousness_concept_id 없음 / is_serious=1 인데 seriousness_concept_id 없음 |
| SEM-COM-023 중복 이벤트 레코드 | Plausibility | warning | MEASUREMENT | 3 | 2건 중복 / 2건 중복 |
| SEM-COM-029 특화 테이블 death_date 와 PERSON 일치 | Conformance | error | PERSON | 3 | DIABETES.death_date=2024-01-01 <> PERSON.death_date=NULL / DIABETES.death_date=2024-01-01 <> PERSON.death_date=NULL |
| SEM-COM-030 특화 테이블 방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 500269 의 person_id=500017 / visit 501060 의 person_id=500063 |
| SEM-DM-001 DIABETES 방문 필드가 VISIT_OCCURRENCE 와 일치 | Conformance | error | VISIT_OCCURRENCE | 8 | visit_end_date 불일치 / visit_end_date 불일치 |
| SEM-DM-002 DIABETES 검사 필드가 MEASUREMENT 와 일치 | Conformance | error | MEASUREMENT | 18 | MEASUREMENT 500001 불일치: concept 3036277/3036277, value 173.3/173.3 / MEASUREMENT 500615 불일치: concept 3038553/3038553, value 27.4/NULL |
| SEM-DM-003 DIABETES 약물/진단/환자 필드가 핵심 테이블과 일치 | Conformance | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,PERSON | 779 | DRUG_EXPOSURE 500186 불일치 / DRUG_EXPOSURE 500426 불일치 |
| SEM-DM-004 당뇨 코호트 방문 유형 = 외래 | Conformance | warning | DIABETES | 2 | visit_concept_id=9201 / visit_concept_id=9201 |
| SEM-DM-005 연 1회 이상 HbA1c | Completeness | warning | MEASUREMENT,PERSON,VISIT_OCCURRENCE | 6 |  /  |
| SEM-DM-006 당뇨약 처방 환자의 진단 존재 | Plausibility | warning | CONDITION_OCCURRENCE,DRUG_EXPOSURE | 2 | 당뇨약 처방인데 T2DM 진단 없음 / 당뇨약 처방인데 T2DM 진단 없음 |
