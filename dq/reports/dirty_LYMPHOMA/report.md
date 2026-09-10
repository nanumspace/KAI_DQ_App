# 데이터 품질 검증 보고서: LYMPHOMA (림프종)

검증일 2026-09-07 / 테이블 11개 / 규칙 463개 (실패 49, 건너뜀 0, 오류 0)

위반 132건 (error 87, warning 45)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 290 | 20 | 54 |
| Completeness | 74 | 12 | 26 |
| Plausibility | 99 | 17 | 52 |

## 테이블 행수

- PERSON: 100
- VISIT_OCCURRENCE: 2163
- PROCEDURE_OCCURRENCE: 1396
- DRUG_EXPOSURE: 2855
- CONDITION_OCCURRENCE: 441
- MEASUREMENT: 7802
- OBSERVATION: 100
- NOTE: 520
- LYMPHOMA: 2305
- ADVERSE_EVENT: 291
- ANTP_THERAPY: 133

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
| ST-0121 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 6 | PK 중복: 603865 / PK 중복: 605743 |
| ST-0136 MEASUREMENT.value_as_number 타입(float) | Conformance | error | MEASUREMENT | 3 | value_as_number='N/A' 은 float 아님 / value_as_number='N/A' 은 float 아님 |
| ST-0146 OBSERVATION 컬럼 구성 | Conformance | error | OBSERVATION | 1 | 컬럼 누락: value_as_string |
| ST-0177 NOTE.note_date 미래 날짜 금지 | Plausibility | error | NOTE | 3 | note_date=2030-01-01 미래 날짜 / note_date=2030-01-01 미래 날짜 |
| ST-0885 LYMPHOMA.person_id -> PERSON.person_id 참조무결성 | Conformance | error | LYMPHOMA | 3 | person_id=888888888 가 PERSON.person_id 에 없음 / person_id=888888888 가 PERSON.person_id 에 없음 |
| ST-0889 LYMPHOMA.condition_occurrence_id -> CONDITION_OCCURRENCE.condition_occurrence_id 참조무결성 | Conformance | error | LYMPHOMA | 2 | condition_occurrence_id=600001 가 CONDITION_OCCURRENCE.condition_occurrence_id 에 없음 / condition_occurrence_id=600005 가 CONDITION_OCCURRENCE.condition_o |
| ST-0915 LYMPHOMA.ann_arbor_lugano_stage 패턴 | Conformance | warning | LYMPHOMA | 2 | ann_arbor_lugano_stage='Stage 4?' 패턴 불일치 / ann_arbor_lugano_stage='Stage 4?' 패턴 불일치 |
| ST-0916 LYMPHOMA.stage_suffix 패턴 | Conformance | warning | LYMPHOMA | 2 | stage_suffix='Stage 4?' 패턴 불일치 / stage_suffix='Stage 4?' 패턴 불일치 |
| ST-0918 LYMPHOMA.nodal_regions_involved_count 범위 | Plausibility | warning | LYMPHOMA | 2 | nodal_regions_involved_count=1200 범위 [0,20] 밖 / nodal_regions_involved_count=1200 범위 [0,20] 밖 |
| ST-0922 LYMPHOMA.extranodal_site_count 범위 | Plausibility | warning | LYMPHOMA | 2 | extranodal_site_count=1200 범위 [0,20] 밖 / extranodal_site_count=1200 범위 [0,20] 밖 |
| ST-1037 LYMPHOMA 그룹 'dx' anchor 날짜 | Completeness | error | LYMPHOMA | 1 | ['diagnosis_status', 'lymphoma_group', 'cell_lineage'] 값 있으나 anchor diagnosis_date NULL |
| ST-1038 LYMPHOMA 그룹 'biopsy' anchor 날짜 | Completeness | error | LYMPHOMA | 1 | ['biopsy_method', 'biopsy_site', 'biopsy_specimen_adequacy'] 값 있으나 anchor biopsy_date NULL |
| ST-1040 LYMPHOMA 그룹 'stage' anchor 날짜 | Completeness | error | LYMPHOMA | 1 | ['stage_system', 'ann_arbor_lugano_stage', 'stage_suffix'] 값 있으나 anchor stage_assessment_date NULL |
| ST-1041 LYMPHOMA 그룹 'pet' anchor 날짜 | Completeness | error | LYMPHOMA | 1 | ['pet_suvmax', 'metabolic_tumor_volume', 'total_lesion_glycolysis'] 값 있으나 anchor pet_ct_assessment_date NULL |
| ST-1042 LYMPHOMA 그룹 'ihc' anchor 날짜 | Completeness | error | LYMPHOMA | 1 | ['cd3_result', 'cd5_result', 'cd10_result'] 값 있으나 anchor ihc_test_date NULL |
| ST-1051 LYMPHOMA 환자 불변 필드 일관성 | Plausibility | warning | LYMPHOMA | 3 | hbv_status 값이 환자 내에서 다름: ['HBsAg negative, anti-HBc negative', 'HBsAg negative, anti-HBc negative_X'] / hbv_status 값이 환자 내에서 다름: ['HBsAg negative, ant |
| ST-1054 ADVERSE_EVENT 컬럼 구성 | Conformance | error | ADVERSE_EVENT | 1 | 별칭 컬럼 antp_therapy_id 를 antp_id 로 해석함 (경고) |
| ST-1084 ADVERSE_EVENT.severity_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 3 | severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 / severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 |
| SEM-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2000-01-01 < visit_start_date 2021-02-14 / visit_end_date 2000-01-01 < visit_start_date 2020-10-06 |
| SEM-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | PERSON | 3 | 이벤트일 2026-08-30 > death_date 2022-08-03 / 이벤트일 2026-08-30 > death_date 2025-01-07 |
| SEM-COM-005 이벤트-방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 600250 의 person_id=600011 / visit 600349 의 person_id=600015 |
| SEM-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | VISIT_OCCURRENCE | 10 | 이벤트일 2021-02-14 가 방문기간 2021-02-14~2000-01-01 밖 / 이벤트일 2020-10-06 가 방문기간 2020-10-06~2000-01-01 밖 |
| SEM-COM-007 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | end < start / end < start |
| SEM-COM-008 투여 빈도/간격 조건부 필수 | Completeness | warning | DRUG_EXPOSURE | 3 | frequency_per_day 있음, days_supply 없음 / frequency_per_day 있음, days_supply 없음 |
| SEM-COM-009 검사 결과값 존재 | Completeness | error | MEASUREMENT | 6 | value_as_number, value_as_concept_id 모두 NULL / value_as_number, value_as_concept_id 모두 NULL |
| SEM-COM-011 검사항목별 타당 범위 | Plausibility | warning | MEASUREMENT | 3 | Platelet count=99999.0 (타당범위 1.0~2000.0) / C-reactive protein=99999.0 (타당범위 0.0~600.0) |
| SEM-COM-012 age_at_index 와 index date 일치 | Plausibility | error | CONDITION_OCCURRENCE,PERSON | 3 | age_at_index=62, index_date=2021-01-16, year_of_birth=1973 / age_at_index=77, index_date=2022-09-03, year_of_birth=1960 |
| SEM-COM-013 코호트 포함 조건 | Completeness | error | CONDITION_OCCURRENCE,PERSON,VISIT_OCCURRENCE | 2 | 코호트 정의 진단 없음 / 코호트 정의 진단 없음 |
| SEM-COM-015 특화 테이블 고아 환자 | Conformance | error | PERSON | 1 | PERSON 에 없는 person_id |
| SEM-COM-016 이상사례 발생일 >= 항암 시작일 | Plausibility | error | ADVERSE_EVENT,ANTP_THERAPY | 3 | AE 2015-01-01 < antp_start_date 2021-03-31 / AE 2015-01-01 < antp_start_date 2021-06-16 |
| SEM-COM-017 중대한 이상사례 조건부 필수 / 치명 결과와 사망 일치 | Completeness | error | ADVERSE_EVENT,PERSON | 3 | is_serious=1 인데 seriousness_concept_id 없음 / is_serious=1 인데 seriousness_concept_id 없음 |
| SEM-COM-018 항암요법 기간 및 line 번호 | Plausibility | error | ANTP_THERAPY | 3 | line=5 이나 시작일 순서=1 / line=5 이나 시작일 순서=1 |
| SEM-COM-023 중복 이벤트 레코드 | Plausibility | warning | MEASUREMENT | 3 | 2건 중복 / 2건 중복 |
| SEM-COM-029 특화 테이블 death_date 와 PERSON 일치 | Conformance | error | PERSON | 3 | LYMPHOMA.death_date=2024-01-01 <> PERSON.death_date=NULL / LYMPHOMA.death_date=2024-01-01 <> PERSON.death_date=NULL |
| SEM-COM-030 특화 테이블 방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 600362 의 person_id=600015 / visit 601356 의 person_id=600063 |
| SEM-LY-001 진단 그룹 존재 및 진단일 일치 | Completeness | error | CONDITION_OCCURRENCE,PERSON | 1 | dx 그룹 행 없음 |
| SEM-LY-002 B 증상과 병기 수식자 일치 | Plausibility | warning | LYMPHOMA | 3 | B 증상 있음인데 suffix=Stage 4? / B 증상 없음인데 suffix 에 B |
| SEM-LY-003 결절외/골수/bulky 침범 논리 | Plausibility | warning | LYMPHOMA | 1 | 결절외 침범 0 인데 count/E 있음 |
| SEM-LY-005 IPI 점수와 위험군 일치 | Conformance | warning | LYMPHOMA | 3 | ipi_score=4, ipi_risk_group=low / ipi_score=1, ipi_risk_group=high |
| SEM-LY-006 치료 line 논리 및 항암 테이블 일치 | Conformance | error | ANTP_THERAPY | 5 | line 1 <> ANTP line 5 / current_line 9 <> prior+1 |
| SEM-LY-008 반응평가 논리 | Plausibility | warning | LYMPHOMA | 2 | Deauville 3 인데 PMD / Deauville 1 인데 PMD |
| SEM-LY-009 추적/생존 상태 일관성 | Plausibility | error | PERSON | 2 | dead 인데 death_date 불일치/누락 / dead 인데 death_date 불일치/누락 |
