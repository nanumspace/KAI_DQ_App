# 데이터 품질 검증 보고서: BREAST_CANCER (유방암)

검증일 2026-09-07 / 테이블 12개 / 규칙 287개 (실패 252, 건너뜀 0, 오류 0)

위반 1177건 (error 1111, warning 66)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 176 | 154 | 771 |
| Completeness | 69 | 57 | 66 |
| Plausibility | 42 | 41 | 340 |

## 테이블 행수

- PERSON: 100
- VISIT_OCCURRENCE: 3594
- PROCEDURE_OCCURRENCE: 1300
- DRUG_EXPOSURE: 2643
- CONDITION_OCCURRENCE: 475
- MEASUREMENT: 10075
- OBSERVATION: 100
- NOTE: 449
- BREAST_CANCER: 99
- ADVERSE_EVENT: 332
- SACT: 184
- DRUG_INGREDIENT_STRUCTURE: 10

## 실패 규칙

| 규칙 | 분류 | 심각도 | 테이블 | 위반 | 예시 |
|---|---|---|---|---|---|
| ST-0003 PERSON.person_id PK 유일성 | Conformance | error | PERSON | 3 | PK NULL / PK 중복: … |
| ST-0004 PERSON.person_id 타입(integer) | Conformance | error | PERSON | 1 | person_id=… 은 integer 아님 |
| ST-0005 PERSON.gender_concept_id 필수 | Completeness | error | PERSON | 1 | gender_concept_id NULL |
| ST-0006 PERSON.gender_concept_id 타입(integer) | Conformance | error | PERSON | 1 | gender_concept_id=… 은 integer 아님 |
| ST-0007 PERSON.gender_concept_id 코드표 | Conformance | warning | PERSON | 2 | gender_concept_id=… 코드표(OMOP.gender_concept_id) 밖 / gender_concept_id=… 코드표(OMOP.gender_concept_id) 밖 |
| ST-0008 PERSON.year_of_birth 필수 | Completeness | error | PERSON | 1 | year_of_birth NULL |
| ST-0009 PERSON.year_of_birth 타입(integer) | Conformance | error | PERSON | 1 | year_of_birth=… 은 integer 아님 |
| ST-0010 PERSON.year_of_birth 범위 | Plausibility | warning | PERSON | 1 | year_of_birth=… 범위 […,…] 밖 |
| ST-0011 PERSON.month_of_birth 타입(integer) | Conformance | error | PERSON | 1 | month_of_birth=… 은 integer 아님 |
| ST-0012 PERSON.month_of_birth 범위 | Plausibility | warning | PERSON | 1 | month_of_birth=… 범위 […,…] 밖 |
| ST-0013 PERSON.day_of_birth 타입(integer) | Conformance | error | PERSON | 1 | day_of_birth=… 은 integer 아님 |
| ST-0014 PERSON.day_of_birth 범위 | Plausibility | warning | PERSON | 1 | day_of_birth=… 범위 […,…] 밖 |
| ST-0015 PERSON.age_at_index 필수 | Completeness | error | PERSON | 1 | age_at_index NULL |
| ST-0016 PERSON.age_at_index 타입(integer) | Conformance | error | PERSON | 1 | age_at_index=… 은 integer 아님 |
| ST-0017 PERSON.age_at_index 범위 | Plausibility | warning | PERSON | 1 | age_at_index=… 범위 […,…] 밖 |
| ST-0018 PERSON.care_site_id 필수 | Completeness | error | PERSON | 1 | care_site_id NULL |
| ST-0019 PERSON.care_site_id 타입(integer) | Conformance | error | PERSON | 1 | care_site_id=… 은 integer 아님 |
| ST-0020 PERSON.observation_period_start_date 타입(date) | Conformance | error | PERSON | 1 | observation_period_start_date=… 은 date 아님 |
| ST-0021 PERSON.observation_period_start_date 미래 날짜 금지 | Plausibility | error | PERSON | 1 | observation_period_start_date=… 미래 날짜 |
| ST-0022 PERSON.death_date 타입(date) | Conformance | error | PERSON | 1 | death_date=… 은 date 아님 |
| ST-0023 PERSON.death_date 미래 날짜 금지 | Plausibility | error | PERSON | 1 | death_date=… 미래 날짜 |
| ST-0026 VISIT_OCCURRENCE.visit_occurrence_id PK 유일성 | Conformance | error | VISIT_OCCURRENCE | 3 | PK NULL / PK 중복: … |
| ST-0027 VISIT_OCCURRENCE.visit_occurrence_id 타입(integer) | Conformance | error | VISIT_OCCURRENCE | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0028 VISIT_OCCURRENCE.person_id 필수 | Completeness | error | VISIT_OCCURRENCE | 1 | person_id NULL |
| ST-0029 VISIT_OCCURRENCE.person_id 타입(integer) | Conformance | error | VISIT_OCCURRENCE | 1 | person_id=… 은 integer 아님 |
| ST-0030 VISIT_OCCURRENCE.person_id -> PERSON.person_id 참조무결성 | Conformance | error | VISIT_OCCURRENCE | 84 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0031 VISIT_OCCURRENCE.visit_concept_id 필수 | Completeness | error | VISIT_OCCURRENCE | 1 | visit_concept_id NULL |
| ST-0032 VISIT_OCCURRENCE.visit_concept_id 타입(integer) | Conformance | error | VISIT_OCCURRENCE | 1 | visit_concept_id=… 은 integer 아님 |
| ST-0033 VISIT_OCCURRENCE.visit_concept_id 코드표 | Conformance | warning | VISIT_OCCURRENCE | 2 | visit_concept_id=… 코드표(OMOP.visit_concept_id) 밖 / visit_concept_id=… 코드표(OMOP.visit_concept_id) 밖 |
| ST-0034 VISIT_OCCURRENCE.visit_start_date 필수 | Completeness | error | VISIT_OCCURRENCE | 1 | visit_start_date NULL |
| ST-0035 VISIT_OCCURRENCE.visit_start_date 타입(date) | Conformance | error | VISIT_OCCURRENCE | 1 | visit_start_date=… 은 date 아님 |
| ST-0036 VISIT_OCCURRENCE.visit_start_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 1 | visit_start_date=… 미래 날짜 |
| ST-0037 VISIT_OCCURRENCE.visit_end_date 필수 | Completeness | error | VISIT_OCCURRENCE | 1 | visit_end_date NULL |
| ST-0038 VISIT_OCCURRENCE.visit_end_date 타입(date) | Conformance | error | VISIT_OCCURRENCE | 1 | visit_end_date=… 은 date 아님 |
| ST-0039 VISIT_OCCURRENCE.visit_end_date 미래 날짜 금지 | Plausibility | error | VISIT_OCCURRENCE | 1 | visit_end_date=… 미래 날짜 |
| ST-0040 VISIT_OCCURRENCE.visit_type_concept_id 필수 | Completeness | error | VISIT_OCCURRENCE | 1 | visit_type_concept_id NULL |
| ST-0041 VISIT_OCCURRENCE.visit_type_concept_id 타입(integer) | Conformance | error | VISIT_OCCURRENCE | 1 | visit_type_concept_id=… 은 integer 아님 |
| ST-0042 VISIT_OCCURRENCE.visit_type_concept_id 코드표 | Conformance | warning | VISIT_OCCURRENCE | 2 | visit_type_concept_id=… 코드표(OMOP.visit_type_concept_id) 밖 / visit_type_concept_id=… 코드표(OMOP.visit_type_concept_id) 밖 |
| ST-0044 PROCEDURE_OCCURRENCE 컬럼 구성 | Conformance | error | PROCEDURE_OCCURRENCE | 1 | 컬럼 누락: procedure_source_value |
| ST-0045 PROCEDURE_OCCURRENCE.procedure_occurrence_id PK 유일성 | Conformance | error | PROCEDURE_OCCURRENCE | 3 | PK NULL / PK 중복: … |
| ST-0046 PROCEDURE_OCCURRENCE.procedure_occurrence_id 타입(integer) | Conformance | error | PROCEDURE_OCCURRENCE | 1 | procedure_occurrence_id=… 은 integer 아님 |
| ST-0047 PROCEDURE_OCCURRENCE.visit_occurrence_id 타입(integer) | Conformance | error | PROCEDURE_OCCURRENCE | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0048 PROCEDURE_OCCURRENCE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | PROCEDURE_OCCURRENCE | 1 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0049 PROCEDURE_OCCURRENCE.person_id 필수 | Completeness | error | PROCEDURE_OCCURRENCE | 1 | person_id NULL |
| ST-0050 PROCEDURE_OCCURRENCE.person_id 타입(integer) | Conformance | error | PROCEDURE_OCCURRENCE | 1 | person_id=… 은 integer 아님 |
| ST-0051 PROCEDURE_OCCURRENCE.person_id -> PERSON.person_id 참조무결성 | Conformance | error | PROCEDURE_OCCURRENCE | 35 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0052 PROCEDURE_OCCURRENCE.procedure_concept_id 필수 | Completeness | error | PROCEDURE_OCCURRENCE | 1 | procedure_concept_id NULL |
| ST-0053 PROCEDURE_OCCURRENCE.procedure_concept_id 타입(integer) | Conformance | error | PROCEDURE_OCCURRENCE | 1 | procedure_concept_id=… 은 integer 아님 |
| ST-0054 PROCEDURE_OCCURRENCE.procedure_date 필수 | Completeness | error | PROCEDURE_OCCURRENCE | 1 | procedure_date NULL |
| ST-0055 PROCEDURE_OCCURRENCE.procedure_date 타입(date) | Conformance | error | PROCEDURE_OCCURRENCE | 1 | procedure_date=… 은 date 아님 |
| ST-0056 PROCEDURE_OCCURRENCE.procedure_date 미래 날짜 금지 | Plausibility | error | PROCEDURE_OCCURRENCE | 1 | procedure_date=… 미래 날짜 |
| ST-0057 PROCEDURE_OCCURRENCE.procedure_type_concept_id 필수 | Completeness | error | PROCEDURE_OCCURRENCE | 1 | procedure_type_concept_id NULL |
| ST-0058 PROCEDURE_OCCURRENCE.procedure_type_concept_id 타입(integer) | Conformance | error | PROCEDURE_OCCURRENCE | 1 | procedure_type_concept_id=… 은 integer 아님 |
| ST-0059 PROCEDURE_OCCURRENCE.procedure_type_concept_id 코드표 | Conformance | warning | PROCEDURE_OCCURRENCE | 2 | procedure_type_concept_id=… 코드표(OMOP.procedure_type_concept_id) 밖 / procedure_type_concept_id=… 코드표(OMOP.procedure_type_concept_id) 밖 |
| ST-0062 DRUG_EXPOSURE.drug_exposure_id PK 유일성 | Conformance | error | DRUG_EXPOSURE | 3 | PK NULL / PK 중복: … |
| ST-0063 DRUG_EXPOSURE.drug_exposure_id 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | drug_exposure_id=… 은 integer 아님 |
| ST-0064 DRUG_EXPOSURE.visit_occurrence_id 필수 | Completeness | error | DRUG_EXPOSURE | 1 | visit_occurrence_id NULL |
| ST-0065 DRUG_EXPOSURE.visit_occurrence_id 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0066 DRUG_EXPOSURE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | DRUG_EXPOSURE | 4 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0067 DRUG_EXPOSURE.person_id 필수 | Completeness | error | DRUG_EXPOSURE | 1 | person_id NULL |
| ST-0068 DRUG_EXPOSURE.person_id 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | person_id=… 은 integer 아님 |
| ST-0069 DRUG_EXPOSURE.person_id -> PERSON.person_id 참조무결성 | Conformance | error | DRUG_EXPOSURE | 57 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0070 DRUG_EXPOSURE.sact_id 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | sact_id=… 은 integer 아님 |
| ST-0071 DRUG_EXPOSURE.sact_id -> SACT.sact_id 참조무결성 | Conformance | error | DRUG_EXPOSURE | 45 | sact_id=… 가 SACT.sact_id 에 없음 / sact_id=… 가 SACT.sact_id 에 없음 |
| ST-0072 DRUG_EXPOSURE.drug_concept_id 필수 | Completeness | error | DRUG_EXPOSURE | 1 | drug_concept_id NULL |
| ST-0073 DRUG_EXPOSURE.drug_concept_id 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | drug_concept_id=… 은 integer 아님 |
| ST-0074 DRUG_EXPOSURE.drug_exposure_start_date 필수 | Completeness | error | DRUG_EXPOSURE | 1 | drug_exposure_start_date NULL |
| ST-0075 DRUG_EXPOSURE.drug_exposure_start_date 타입(date) | Conformance | error | DRUG_EXPOSURE | 1 | drug_exposure_start_date=… 은 date 아님 |
| ST-0076 DRUG_EXPOSURE.drug_exposure_start_date 미래 날짜 금지 | Plausibility | error | DRUG_EXPOSURE | 1 | drug_exposure_start_date=… 미래 날짜 |
| ST-0077 DRUG_EXPOSURE.drug_exposure_end_date 필수 | Completeness | error | DRUG_EXPOSURE | 1 | drug_exposure_end_date NULL |
| ST-0078 DRUG_EXPOSURE.drug_exposure_end_date 타입(date) | Conformance | error | DRUG_EXPOSURE | 1 | drug_exposure_end_date=… 은 date 아님 |
| ST-0079 DRUG_EXPOSURE.drug_exposure_end_date 미래 날짜 금지 | Plausibility | error | DRUG_EXPOSURE | 1 | drug_exposure_end_date=… 미래 날짜 |
| ST-0080 DRUG_EXPOSURE.days_supply 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | days_supply=… 은 integer 아님 |
| ST-0081 DRUG_EXPOSURE.days_supply 범위 | Plausibility | warning | DRUG_EXPOSURE | 1 | days_supply=… 범위 […,…] 밖 |
| ST-0082 DRUG_EXPOSURE.amount_unit_concept_id 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | amount_unit_concept_id=… 은 integer 아님 |
| ST-0083 DRUG_EXPOSURE.amount_unit_concept_id 코드표 | Conformance | warning | DRUG_EXPOSURE | 2 | amount_unit_concept_id=… 코드표(OMOP.amount_unit_concept_id) 밖 / amount_unit_concept_id=… 코드표(OMOP.amount_unit_concept_id) 밖 |
| ST-0084 DRUG_EXPOSURE.amount_value 타입(float) | Conformance | error | DRUG_EXPOSURE | 1 | amount_value=… 은 float 아님 |
| ST-0085 DRUG_EXPOSURE.amount_value 범위 | Plausibility | warning | DRUG_EXPOSURE | 1 | amount_value=… 범위 […,…] 밖 |
| ST-0094 DRUG_EXPOSURE.frequency_per_day 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | frequency_per_day=… 은 integer 아님 |
| ST-0095 DRUG_EXPOSURE.frequency_per_day 범위 | Plausibility | warning | DRUG_EXPOSURE | 1 | frequency_per_day=… 범위 […,…] 밖 |
| ST-0096 DRUG_EXPOSURE.dosing_interval_day 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | dosing_interval_day=… 은 integer 아님 |
| ST-0097 DRUG_EXPOSURE.dosing_interval_day 범위 | Plausibility | warning | DRUG_EXPOSURE | 1 | dosing_interval_day=… 범위 […,…] 밖 |
| ST-0098 DRUG_EXPOSURE.dosing_number 타입(integer) | Conformance | error | DRUG_EXPOSURE | 1 | dosing_number=… 은 integer 아님 |
| ST-0099 DRUG_EXPOSURE.dosing_number 범위 | Plausibility | warning | DRUG_EXPOSURE | 1 | dosing_number=… 범위 […,…] 밖 |
| ST-0103 CONDITION_OCCURRENCE.condition_occurrence_id PK 유일성 | Conformance | error | CONDITION_OCCURRENCE | 3 | PK NULL / PK 중복: … |
| ST-0104 CONDITION_OCCURRENCE.condition_occurrence_id 타입(integer) | Conformance | error | CONDITION_OCCURRENCE | 1 | condition_occurrence_id=… 은 integer 아님 |
| ST-0105 CONDITION_OCCURRENCE.visit_occurrence_id 타입(integer) | Conformance | error | CONDITION_OCCURRENCE | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0106 CONDITION_OCCURRENCE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | CONDITION_OCCURRENCE | 1 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0107 CONDITION_OCCURRENCE.person_id 필수 | Completeness | error | CONDITION_OCCURRENCE | 1 | person_id NULL |
| ST-0108 CONDITION_OCCURRENCE.person_id 타입(integer) | Conformance | error | CONDITION_OCCURRENCE | 1 | person_id=… 은 integer 아님 |
| ST-0109 CONDITION_OCCURRENCE.person_id -> PERSON.person_id 참조무결성 | Conformance | error | CONDITION_OCCURRENCE | 12 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0110 CONDITION_OCCURRENCE.condition_concept_id 필수 | Completeness | error | CONDITION_OCCURRENCE | 1 | condition_concept_id NULL |
| ST-0111 CONDITION_OCCURRENCE.condition_concept_id 타입(integer) | Conformance | error | CONDITION_OCCURRENCE | 1 | condition_concept_id=… 은 integer 아님 |
| ST-0112 CONDITION_OCCURRENCE.condition_start_date 필수 | Completeness | error | CONDITION_OCCURRENCE | 1 | condition_start_date NULL |
| ST-0113 CONDITION_OCCURRENCE.condition_start_date 타입(date) | Conformance | error | CONDITION_OCCURRENCE | 1 | condition_start_date=… 은 date 아님 |
| ST-0114 CONDITION_OCCURRENCE.condition_start_date 미래 날짜 금지 | Plausibility | error | CONDITION_OCCURRENCE | 1 | condition_start_date=… 미래 날짜 |
| ST-0115 CONDITION_OCCURRENCE.condition_type_concept_id 필수 | Completeness | error | CONDITION_OCCURRENCE | 1 | condition_type_concept_id NULL |
| ST-0116 CONDITION_OCCURRENCE.condition_type_concept_id 타입(integer) | Conformance | error | CONDITION_OCCURRENCE | 1 | condition_type_concept_id=… 은 integer 아님 |
| ST-0117 CONDITION_OCCURRENCE.condition_type_concept_id 코드표 | Conformance | warning | CONDITION_OCCURRENCE | 2 | condition_type_concept_id=… 코드표(OMOP.condition_type_concept_id) 밖 / condition_type_concept_id=… 코드표(OMOP.condition_type_concept_id) 밖 |
| ST-0119 MEASUREMENT 컬럼 구성 | Conformance | error | MEASUREMENT | 1 | 컬럼 누락: unit_source_value |
| ST-0120 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 3 | PK NULL / PK 중복: … |
| ST-0121 MEASUREMENT.measurement_id 타입(integer) | Conformance | error | MEASUREMENT | 1 | measurement_id=… 은 integer 아님 |
| ST-0122 MEASUREMENT.visit_occurrence_id 타입(integer) | Conformance | error | MEASUREMENT | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0123 MEASUREMENT.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | MEASUREMENT | 7 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 / visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0124 MEASUREMENT.person_id 필수 | Completeness | error | MEASUREMENT | 1 | person_id NULL |
| ST-0125 MEASUREMENT.person_id 타입(integer) | Conformance | error | MEASUREMENT | 1 | person_id=… 은 integer 아님 |
| ST-0126 MEASUREMENT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | MEASUREMENT | 248 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0127 MEASUREMENT.measurement_concept_id 필수 | Completeness | error | MEASUREMENT | 1 | measurement_concept_id NULL |
| ST-0128 MEASUREMENT.measurement_concept_id 타입(integer) | Conformance | error | MEASUREMENT | 1 | measurement_concept_id=… 은 integer 아님 |
| ST-0129 MEASUREMENT.measurement_date 필수 | Completeness | error | MEASUREMENT | 1 | measurement_date NULL |
| ST-0130 MEASUREMENT.measurement_date 타입(date) | Conformance | error | MEASUREMENT | 1 | measurement_date=… 은 date 아님 |
| ST-0131 MEASUREMENT.measurement_date 미래 날짜 금지 | Plausibility | error | MEASUREMENT | 1 | measurement_date=… 미래 날짜 |
| ST-0132 MEASUREMENT.measurement_type_concept_id 필수 | Completeness | error | MEASUREMENT | 1 | measurement_type_concept_id NULL |
| ST-0133 MEASUREMENT.measurement_type_concept_id 타입(integer) | Conformance | error | MEASUREMENT | 1 | measurement_type_concept_id=… 은 integer 아님 |
| ST-0134 MEASUREMENT.measurement_type_concept_id 코드표 | Conformance | warning | MEASUREMENT | 2 | measurement_type_concept_id=… 코드표(OMOP.measurement_type_concept_id) 밖 / measurement_type_concept_id=… 코드표(OMOP.measurement_type_concept_id) 밖 |
| ST-0135 MEASUREMENT.value_as_number 타입(float) | Conformance | error | MEASUREMENT | 1 | value_as_number=… 은 float 아님 |
| ST-0136 MEASUREMENT.value_as_number 범위 | Plausibility | warning | MEASUREMENT | 1 | value_as_number=… 범위 [-…,…] 밖 |
| ST-0138 MEASUREMENT.unit_concept_id 타입(integer) | Conformance | error | MEASUREMENT | 1 | unit_concept_id=… 은 integer 아님 |
| ST-0139 MEASUREMENT.unit_concept_id 코드표 | Conformance | warning | MEASUREMENT | 2 | unit_concept_id=… 코드표(OMOP.unit_concept_id) 밖 / unit_concept_id=… 코드표(OMOP.unit_concept_id) 밖 |
| ST-0140 MEASUREMENT.range_low 타입(float) | Conformance | error | MEASUREMENT | 1 | range_low=… 은 float 아님 |
| ST-0141 MEASUREMENT.range_low 범위 | Plausibility | warning | MEASUREMENT | 1 | range_low=… 범위 [-…,…] 밖 |
| ST-0142 MEASUREMENT.range_high 타입(float) | Conformance | error | MEASUREMENT | 1 | range_high=… 은 float 아님 |
| ST-0143 MEASUREMENT.range_high 범위 | Plausibility | warning | MEASUREMENT | 1 | range_high=… 범위 [-…,…] 밖 |
| ST-0146 OBSERVATION.observation_id PK 유일성 | Conformance | error | OBSERVATION | 3 | PK NULL / PK 중복: … |
| ST-0147 OBSERVATION.observation_id 타입(integer) | Conformance | error | OBSERVATION | 1 | observation_id=… 은 integer 아님 |
| ST-0148 OBSERVATION.visit_occurrence_id 필수 | Completeness | error | OBSERVATION | 1 | visit_occurrence_id NULL |
| ST-0149 OBSERVATION.visit_occurrence_id 타입(integer) | Conformance | error | OBSERVATION | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0150 OBSERVATION.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | OBSERVATION | 1 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0151 OBSERVATION.person_id 필수 | Completeness | error | OBSERVATION | 1 | person_id NULL |
| ST-0152 OBSERVATION.person_id 타입(integer) | Conformance | error | OBSERVATION | 1 | person_id=… 은 integer 아님 |
| ST-0153 OBSERVATION.person_id -> PERSON.person_id 참조무결성 | Conformance | error | OBSERVATION | 4 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0154 OBSERVATION.observation_concept_id 필수 | Completeness | error | OBSERVATION | 1 | observation_concept_id NULL |
| ST-0155 OBSERVATION.observation_concept_id 타입(integer) | Conformance | error | OBSERVATION | 1 | observation_concept_id=… 은 integer 아님 |
| ST-0156 OBSERVATION.observation_date 필수 | Completeness | error | OBSERVATION | 1 | observation_date NULL |
| ST-0157 OBSERVATION.observation_date 타입(date) | Conformance | error | OBSERVATION | 1 | observation_date=… 은 date 아님 |
| ST-0158 OBSERVATION.observation_date 미래 날짜 금지 | Plausibility | error | OBSERVATION | 1 | observation_date=… 미래 날짜 |
| ST-0159 OBSERVATION.observation_type_concept_id 필수 | Completeness | error | OBSERVATION | 1 | observation_type_concept_id NULL |
| ST-0160 OBSERVATION.observation_type_concept_id 타입(integer) | Conformance | error | OBSERVATION | 1 | observation_type_concept_id=… 은 integer 아님 |
| ST-0161 OBSERVATION.observation_type_concept_id 코드표 | Conformance | warning | OBSERVATION | 2 | observation_type_concept_id=… 코드표(OMOP.observation_type_concept_id) 밖 / observation_type_concept_id=… 코드표(OMOP.observation_type_concept_id) 밖 |
| ST-0162 OBSERVATION.value_as_number 타입(float) | Conformance | error | OBSERVATION | 1 | value_as_number=… 은 float 아님 |
| ST-0163 OBSERVATION.value_as_number 범위 | Plausibility | warning | OBSERVATION | 1 | value_as_number=… 범위 [-…,…] 밖 |
| ST-0169 NOTE.note_id PK 유일성 | Conformance | error | NOTE | 3 | PK NULL / PK 중복: … |
| ST-0170 NOTE.note_id 타입(integer) | Conformance | error | NOTE | 1 | note_id=… 은 integer 아님 |
| ST-0171 NOTE.visit_occurrence_id 타입(integer) | Conformance | error | NOTE | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0172 NOTE.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | NOTE | 1 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0173 NOTE.person_id 필수 | Completeness | error | NOTE | 1 | person_id NULL |
| ST-0174 NOTE.person_id 타입(integer) | Conformance | error | NOTE | 1 | person_id=… 은 integer 아님 |
| ST-0175 NOTE.person_id -> PERSON.person_id 참조무결성 | Conformance | error | NOTE | 14 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0176 NOTE.note_date 필수 | Completeness | error | NOTE | 1 | note_date NULL |
| ST-0177 NOTE.note_date 타입(date) | Conformance | error | NOTE | 1 | note_date=… 은 date 아님 |
| ST-0178 NOTE.note_date 미래 날짜 금지 | Plausibility | error | NOTE | 1 | note_date=… 미래 날짜 |
| ST-0179 NOTE.note_type_concept_id 필수 | Completeness | error | NOTE | 1 | note_type_concept_id NULL |
| ST-0180 NOTE.note_type_concept_id 타입(integer) | Conformance | error | NOTE | 1 | note_type_concept_id=… 은 integer 아님 |
| ST-0181 NOTE.note_type_concept_id 코드표 | Conformance | warning | NOTE | 2 | note_type_concept_id=… 코드표(OMOP.note_type_concept_id) 밖 / note_type_concept_id=… 코드표(OMOP.note_type_concept_id) 밖 |
| ST-0182 NOTE.note_class_concept_id 필수 | Completeness | error | NOTE | 1 | note_class_concept_id NULL |
| ST-0183 NOTE.note_class_concept_id 타입(integer) | Conformance | error | NOTE | 1 | note_class_concept_id=… 은 integer 아님 |
| ST-0184 NOTE.note_class_concept_id 코드표 | Conformance | warning | NOTE | 2 | note_class_concept_id=… 코드표(OMOP.note_class_concept_id) 밖 / note_class_concept_id=… 코드표(OMOP.note_class_concept_id) 밖 |
| ST-0188 DRUG_INGREDIENT_STRUCTURE.ingredient_concept_id PK 유일성 | Conformance | error | DRUG_INGREDIENT_STRUCTURE | 3 | PK NULL / PK 중복: … |
| ST-0189 DRUG_INGREDIENT_STRUCTURE.ingredient_concept_id 타입(integer) | Conformance | error | DRUG_INGREDIENT_STRUCTURE | 1 | ingredient_concept_id=… 은 integer 아님 |
| ST-0190 DRUG_INGREDIENT_STRUCTURE.smiles 필수 | Completeness | error | DRUG_INGREDIENT_STRUCTURE | 1 | smiles NULL |
| ST-0219 BREAST_CANCER.breast_cancer_id PK 유일성 | Conformance | error | BREAST_CANCER | 3 | PK NULL / PK 중복: … |
| ST-0220 BREAST_CANCER.breast_cancer_id 타입(integer) | Conformance | error | BREAST_CANCER | 1 | breast_cancer_id=… 은 integer 아님 |
| ST-0221 BREAST_CANCER.person_id 필수 | Completeness | error | BREAST_CANCER | 1 | person_id NULL |
| ST-0222 BREAST_CANCER.person_id 타입(integer) | Conformance | error | BREAST_CANCER | 1 | person_id=… 은 integer 아님 |
| ST-0223 BREAST_CANCER.person_id -> PERSON.person_id 참조무결성 | Conformance | error | BREAST_CANCER | 4 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0224 BREAST_CANCER.visit_occurrence_id 필수 | Completeness | error | BREAST_CANCER | 1 | visit_occurrence_id NULL |
| ST-0225 BREAST_CANCER.visit_occurrence_id 타입(integer) | Conformance | error | BREAST_CANCER | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0226 BREAST_CANCER.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | BREAST_CANCER | 1 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0227 BREAST_CANCER.diag_rgst_ymd 필수 | Completeness | error | BREAST_CANCER | 1 | diag_rgst_ymd NULL |
| ST-0228 BREAST_CANCER.diag_rgst_ymd 타입(date) | Conformance | error | BREAST_CANCER | 1 | diag_rgst_ymd=… 은 date 아님 |
| ST-0229 BREAST_CANCER.diag_rgst_ymd 미래 날짜 금지 | Plausibility | error | BREAST_CANCER | 1 | diag_rgst_ymd=… 미래 날짜 |
| ST-0230 BREAST_CANCER.menopause_status 필수 | Completeness | error | BREAST_CANCER | 1 | menopause_status NULL |
| ST-0231 BREAST_CANCER.menopause_status 타입(integer) | Conformance | error | BREAST_CANCER | 1 | menopause_status=… 은 integer 아님 |
| ST-0232 BREAST_CANCER.menopause_status 코드표 | Conformance | error | BREAST_CANCER | 2 | menopause_status=… 코드표(BREAST_CANCER.menopause_status) 밖 / menopause_status=… 코드표(BREAST_CANCER.menopause_status) 밖 |
| ST-0233 BREAST_CANCER.pregnant_at_diagnosis 필수 | Completeness | error | BREAST_CANCER | 1 | pregnant_at_diagnosis NULL |
| ST-0234 BREAST_CANCER.pregnant_at_diagnosis 타입(integer) | Conformance | error | BREAST_CANCER | 1 | pregnant_at_diagnosis=… 은 integer 아님 |
| ST-0235 BREAST_CANCER.pregnant_at_diagnosis 코드표 | Conformance | error | BREAST_CANCER | 2 | pregnant_at_diagnosis=… 코드표(BREAST_CANCER.pregnant_at_diagnosis) 밖 / pregnant_at_diagnosis=… 코드표(BREAST_CANCER.pregnant_at_diagnosis) 밖 |
| ST-0236 BREAST_CANCER.history_of_live_birth 필수 | Completeness | error | BREAST_CANCER | 1 | history_of_live_birth NULL |
| ST-0237 BREAST_CANCER.history_of_live_birth 타입(integer) | Conformance | error | BREAST_CANCER | 1 | history_of_live_birth=… 은 integer 아님 |
| ST-0238 BREAST_CANCER.history_of_live_birth 코드표 | Conformance | error | BREAST_CANCER | 2 | history_of_live_birth=… 코드표(BREAST_CANCER.history_of_live_birth) 밖 / history_of_live_birth=… 코드표(BREAST_CANCER.history_of_live_birth) 밖 |
| ST-0239 BREAST_CANCER.postpartum_at_diagnosis 필수 | Completeness | error | BREAST_CANCER | 1 | postpartum_at_diagnosis NULL |
| ST-0240 BREAST_CANCER.postpartum_at_diagnosis 타입(integer) | Conformance | error | BREAST_CANCER | 1 | postpartum_at_diagnosis=… 은 integer 아님 |
| ST-0241 BREAST_CANCER.postpartum_at_diagnosis 코드표 | Conformance | error | BREAST_CANCER | 2 | postpartum_at_diagnosis=… 코드표(BREAST_CANCER.postpartum_at_diagnosis) 밖 / postpartum_at_diagnosis=… 코드표(BREAST_CANCER.postpartum_at_diagnosis) 밖 |
| ST-0242 BREAST_CANCER.fertility_history 필수 | Completeness | error | BREAST_CANCER | 1 | fertility_history NULL |
| ST-0243 BREAST_CANCER.fertility_history 타입(integer) | Conformance | error | BREAST_CANCER | 1 | fertility_history=… 은 integer 아님 |
| ST-0244 BREAST_CANCER.fertility_history 코드표 | Conformance | error | BREAST_CANCER | 2 | fertility_history=… 코드표(BREAST_CANCER.fertility_history) 밖 / fertility_history=… 코드표(BREAST_CANCER.fertility_history) 밖 |
| ST-0245 BREAST_CANCER.fertility_treatment_type 타입(integer) | Conformance | error | BREAST_CANCER | 1 | fertility_treatment_type=… 은 integer 아님 |
| ST-0246 BREAST_CANCER.fertility_treatment_type 코드표 | Conformance | error | BREAST_CANCER | 2 | fertility_treatment_type=… 코드표(BREAST_CANCER.fertility_treatment_type) 밖 / fertility_treatment_type=… 코드표(BREAST_CANCER.fertility_treatment_type) 밖 |
| ST-0318 SACT.sact_id PK 유일성 | Conformance | error | SACT | 3 | PK NULL / PK 중복: … |
| ST-0319 SACT.sact_id 타입(integer) | Conformance | error | SACT | 1 | sact_id=… 은 integer 아님 |
| ST-0320 SACT.person_id 필수 | Completeness | error | SACT | 1 | person_id NULL |
| ST-0321 SACT.person_id 타입(integer) | Conformance | error | SACT | 1 | person_id=… 은 integer 아님 |
| ST-0322 SACT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | SACT | 5 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0323 SACT.regimen_concept_id 필수 | Completeness | error | SACT | 1 | regimen_concept_id NULL |
| ST-0324 SACT.regimen_concept_id 타입(integer) | Conformance | error | SACT | 1 | regimen_concept_id=… 은 integer 아님 |
| ST-0325 SACT.regimen_source_value 필수 | Completeness | error | SACT | 1 | regimen_source_value NULL |
| ST-0326 SACT.regimen_start_date 필수 | Completeness | error | SACT | 1 | regimen_start_date NULL |
| ST-0327 SACT.regimen_start_date 타입(date) | Conformance | error | SACT | 1 | regimen_start_date=… 은 date 아님 |
| ST-0328 SACT.regimen_start_date 미래 날짜 금지 | Plausibility | error | SACT | 1 | regimen_start_date=… 미래 날짜 |
| ST-0329 SACT.regimen_end_date 필수 | Completeness | error | SACT | 1 | regimen_end_date NULL |
| ST-0330 SACT.regimen_end_date 타입(date) | Conformance | error | SACT | 1 | regimen_end_date=… 은 date 아님 |
| ST-0331 SACT.regimen_end_date 미래 날짜 금지 | Plausibility | error | SACT | 1 | regimen_end_date=… 미래 날짜 |
| ST-0332 SACT.line_of_therapy 타입(integer) | Conformance | error | SACT | 1 | line_of_therapy=… 은 integer 아님 |
| ST-0333 SACT.line_of_therapy 범위 | Plausibility | warning | SACT | 1 | line_of_therapy=… 범위 […,…] 밖 |
| ST-0334 SACT.number_of_cycles 타입(integer) | Conformance | error | SACT | 1 | number_of_cycles=… 은 integer 아님 |
| ST-0335 SACT.number_of_cycles 범위 | Plausibility | warning | SACT | 1 | number_of_cycles=… 범위 […,…] 밖 |
| ST-0336 SACT.therapy_intent 타입(integer) | Conformance | error | SACT | 1 | therapy_intent=… 은 integer 아님 |
| ST-0337 SACT.therapy_intent 코드표 | Conformance | error | SACT | 2 | therapy_intent=… 코드표(SACT.therapy_intent) 밖 / therapy_intent=… 코드표(SACT.therapy_intent) 밖 |
| ST-0338 SACT.ecog_performance_status 타입(integer) | Conformance | error | SACT | 1 | ecog_performance_status=… 은 integer 아님 |
| ST-0339 SACT.ecog_performance_status 범위 | Plausibility | warning | SACT | 1 | ecog_performance_status=… 범위 […,…] 밖 |
| ST-0340 SACT.date_of_progression 타입(date) | Conformance | error | SACT | 1 | date_of_progression=… 은 date 아님 |
| ST-0341 SACT.date_of_progression 미래 날짜 금지 | Plausibility | error | SACT | 1 | date_of_progression=… 미래 날짜 |
| ST-0344 ADVERSE_EVENT.adverse_event_id PK 유일성 | Conformance | error | ADVERSE_EVENT | 3 | PK NULL / PK 중복: … |
| ST-0345 ADVERSE_EVENT.adverse_event_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | adverse_event_id=… 은 integer 아님 |
| ST-0346 ADVERSE_EVENT.person_id 필수 | Completeness | error | ADVERSE_EVENT | 1 | person_id NULL |
| ST-0347 ADVERSE_EVENT.person_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | person_id=… 은 integer 아님 |
| ST-0348 ADVERSE_EVENT.person_id -> PERSON.person_id 참조무결성 | Conformance | error | ADVERSE_EVENT | 8 | person_id=… 가 PERSON.person_id 에 없음 / person_id=… 가 PERSON.person_id 에 없음 |
| ST-0349 ADVERSE_EVENT.visit_occurrence_id 필수 | Completeness | error | ADVERSE_EVENT | 1 | visit_occurrence_id NULL |
| ST-0350 ADVERSE_EVENT.visit_occurrence_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | visit_occurrence_id=… 은 integer 아님 |
| ST-0351 ADVERSE_EVENT.visit_occurrence_id -> VISIT_OCCURRENCE.visit_occurrence_id 참조무결성 | Conformance | error | ADVERSE_EVENT | 1 | visit_occurrence_id=… 가 VISIT_OCCURRENCE.visit_occurrence_id 에 없음 |
| ST-0352 ADVERSE_EVENT.adverse_event_concept_id 필수 | Completeness | error | ADVERSE_EVENT | 1 | adverse_event_concept_id NULL |
| ST-0353 ADVERSE_EVENT.adverse_event_concept_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | adverse_event_concept_id=… 은 integer 아님 |
| ST-0354 ADVERSE_EVENT.adverse_event_start_date 필수 | Completeness | error | ADVERSE_EVENT | 1 | adverse_event_start_date NULL |
| ST-0355 ADVERSE_EVENT.adverse_event_start_date 타입(date) | Conformance | error | ADVERSE_EVENT | 1 | adverse_event_start_date=… 은 date 아님 |
| ST-0356 ADVERSE_EVENT.adverse_event_start_date 미래 날짜 금지 | Plausibility | error | ADVERSE_EVENT | 1 | adverse_event_start_date=… 미래 날짜 |
| ST-0357 ADVERSE_EVENT.severity_concept_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | severity_concept_id=… 은 integer 아님 |
| ST-0358 ADVERSE_EVENT.severity_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 2 | severity_concept_id=… 코드표(OMOP.severity_concept_id) 밖 / severity_concept_id=… 코드표(OMOP.severity_concept_id) 밖 |
| ST-0359 ADVERSE_EVENT.causality_concept_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | causality_concept_id=… 은 integer 아님 |
| ST-0360 ADVERSE_EVENT.causality_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 2 | causality_concept_id=… 코드표(OMOP.causality_concept_id) 밖 / causality_concept_id=… 코드표(OMOP.causality_concept_id) 밖 |
| ST-0361 ADVERSE_EVENT.is_serious_yn 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | is_serious_yn=… 은 integer 아님 |
| ST-0362 ADVERSE_EVENT.seriousness_concept_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | seriousness_concept_id=… 은 integer 아님 |
| ST-0363 ADVERSE_EVENT.seriousness_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 2 | seriousness_concept_id=… 코드표(OMOP.seriousness_concept_id) 밖 / seriousness_concept_id=… 코드표(OMOP.seriousness_concept_id) 밖 |
| ST-0364 ADVERSE_EVENT.outcome_concept_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | outcome_concept_id=… 은 integer 아님 |
| ST-0365 ADVERSE_EVENT.outcome_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 2 | outcome_concept_id=… 코드표(OMOP.outcome_concept_id) 밖 / outcome_concept_id=… 코드표(OMOP.outcome_concept_id) 밖 |
| ST-0366 ADVERSE_EVENT.action_taken_concept_id 타입(integer) | Conformance | error | ADVERSE_EVENT | 1 | action_taken_concept_id=… 은 integer 아님 |
| ST-0367 ADVERSE_EVENT.action_taken_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 2 | action_taken_concept_id=… 코드표(OMOP.action_taken_concept_id) 밖 / action_taken_concept_id=… 코드표(OMOP.action_taken_concept_id) 밖 |
| SEM3-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date … < visit_start_date … / visit_end_date … < visit_start_date … |
| SEM3-COM-002 방문일 >= 출생연도 | Plausibility | error | PERSON,VISIT_OCCURRENCE | 38 | visit_start_date … < year_of_birth … / visit_start_date … < year_of_birth … |
| SEM3-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,NOTE,OBSERVATION,PERSON,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 229 | 이벤트일 … > death_date … / 이벤트일 … > death_date … |
| SEM3-COM-004 이벤트-방문 환자 일치 | Conformance | error | ADVERSE_EVENT,CONDITION_OCCURRENCE,DRUG_EXPOSURE,MEASUREMENT,NOTE,OBSERVATION,PROCEDURE_OCCURRENCE,VISIT_OCCURRENCE | 39 | visit … 의 person_id=… / visit … 의 person_id=… |
| SEM3-COM-005 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 6 | end < start / days_supply=… 이나 기간=… |
| SEM3-COM-006 투여 빈도/간격 조건부 필수 | Completeness | warning | DRUG_EXPOSURE | 3 | dosing_interval_day>…, dosing_number 없음 / frequency_per_day 있음, days_supply 없음 |
| SEM3-COM-007 정상범위 하한 <= 상한 | Plausibility | error | MEASUREMENT | 3 | range_low … > range_high … / range_low … > range_high … |
| SEM3-COM-008 특화 테이블 누락 환자 | Completeness | warning | PERSON | 6 | BREAST_CANCER 에 행 없음 / BREAST_CANCER 에 행 없음 |
| SEM3-COM-009 특화 테이블 방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 2 | visit … 의 person_id=… / visit … 의 person_id=… |
| SEM3-COM-010 이상사례 발생일 사망 이후 금지 | Plausibility | error | ADVERSE_EVENT,PERSON | 4 | adverse_event_start_date … > death_date … / adverse_event_start_date … > death_date … |
| SEM3-SACT-001 항암요법 기간 및 line 번호 | Plausibility | error | SACT | 16 | line_of_therapy=… 이나 시작일 순서=… / line_of_therapy=… 이나 시작일 순서=… |
| SEM3-SACT-002 항암요법 기간이 연결 약물 기간과 일치 | Plausibility | warning | DRUG_EXPOSURE,SACT | 8 | regimen_start_date … <> MIN(drug start) … / regimen_start_date … <> MIN(drug start) … |
| SEM3-SACT-003 진행일 >= 항암 시작일 | Plausibility | error | SACT | 1 | date_of_progression … < regimen_start_date … |
| SEM3-SACT-004 약물-항암요법 환자 일치 | Conformance | error | DRUG_EXPOSURE,SACT | 18 | SACT … 의 person_id=… / SACT … 의 person_id=… |
| SEM3-SACT-005 항종양제(ATC L01) 투여는 sact_id 필수 | Completeness | error | DRUG_EXPOSURE,SACT | 3 | 항종양제(paclitaxel) 인데 sact_id 없음 / 항종양제(trastuzumab) 인데 sact_id 없음 |
| SEM3-SACT-006 내분비 치료제(ATC L02) 투여의 항암요법 연결 확인 | Completeness | warning | DRUG_EXPOSURE,SACT | 1 | 내분비 치료제(tamoxifen) sact_id 없음 — 항암 목적이면 연결 필요 |
