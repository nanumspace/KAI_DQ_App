# 데이터 품질 검증 보고서: LUNG_CANCER (폐암)

검증일 2026-09-07 / 테이블 11개 / 규칙 427개 (실패 49, 건너뜀 0, 오류 0)

위반 172건 (error 85, warning 87)

| 분류 | 규칙 수 | 실패 규칙 | 위반 건수 |
|---|---|---|---|
| Conformance | 248 | 20 | 56 |
| Completeness | 78 | 11 | 25 |
| Plausibility | 101 | 18 | 91 |

## 테이블 행수

- PERSON: 100
- VISIT_OCCURRENCE: 1867
- PROCEDURE_OCCURRENCE: 1000
- DRUG_EXPOSURE: 1361
- CONDITION_OCCURRENCE: 513
- MEASUREMENT: 7363
- OBSERVATION: 200
- NOTE: 414
- LUNG_CANCER: 2082
- ADVERSE_EVENT: 255
- ANTP_THERAPY: 130

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
| ST-0121 MEASUREMENT.measurement_id PK 유일성 | Conformance | error | MEASUREMENT | 6 | PK 중복: 103648 / PK 중복: 105420 |
| ST-0136 MEASUREMENT.value_as_number 타입(float) | Conformance | error | MEASUREMENT | 3 | value_as_number='N/A' 은 float 아님 / value_as_number='N/A' 은 float 아님 |
| ST-0146 OBSERVATION 컬럼 구성 | Conformance | error | OBSERVATION | 1 | 컬럼 누락: value_as_string |
| ST-0177 NOTE.note_date 미래 날짜 금지 | Plausibility | error | NOTE | 3 | note_date=2030-01-01 미래 날짜 / note_date=2030-01-01 미래 날짜 |
| ST-0190 LUNG_CANCER.person_id -> PERSON.person_id 참조무결성 | Conformance | error | LUNG_CANCER | 3 | person_id=888888888 가 PERSON.person_id 에 없음 / person_id=888888888 가 PERSON.person_id 에 없음 |
| ST-0197 LUNG_CANCER.histologic_diagnosis 코드표 | Conformance | error | LUNG_CANCER | 3 | histologic_diagnosis=99 코드표(LUNG_CANCER.histologic_diagnosis) 밖 / histologic_diagnosis=99 코드표(LUNG_CANCER.histologic_diagnosis) 밖 |
| ST-0198 LUNG_CANCER.clinical_stage 패턴 | Conformance | warning | LUNG_CANCER | 2 | clinical_stage='Stage 4?' 패턴 불일치 / clinical_stage='Stage 4?' 패턴 불일치 |
| ST-0202 LUNG_CANCER.smok_qty 범위 | Plausibility | warning | LUNG_CANCER | 2 | smok_qty=1100 범위 [0,10] 밖 / smok_qty=1100 범위 [0,10] 밖 |
| ST-0204 LUNG_CANCER.smok_dtrn_ycnt 범위 | Plausibility | warning | LUNG_CANCER | 2 | smok_dtrn_ycnt=1900 범위 [0,90] 밖 / smok_dtrn_ycnt=1900 범위 [0,90] 밖 |
| ST-0207 LUNG_CANCER.lucn_diag_kncd 패턴 | Conformance | warning | LUNG_CANCER | 2 | lucn_diag_kncd='Stage 4?' 패턴 불일치 / lucn_diag_kncd='Stage 4?' 패턴 불일치 |
| ST-0300 LUNG_CANCER 그룹 'gmt' anchor 날짜 | Completeness | error | LUNG_CANCER | 1 | ['gmt_mtcd', 'gmt_mtnm', 'gmt_gene_kncd'] 값 있으나 anchor gmt_ymd NULL |
| ST-0301 LUNG_CANCER 그룹 'plex' anchor 날짜 | Completeness | error | LUNG_CANCER | 1 | ['plex_spcd', 'plex_spnm', 'plex_kncd'] 값 있으나 anchor plex_ymd NULL |
| ST-0305 LUNG_CANCER 그룹 'oprt' anchor 날짜 | Completeness | error | LUNG_CANCER | 1 | ['opls_detl_loca_cd', 'oprt_kncd', 'oprt_knnm'] 값 있으나 anchor oprt_ymd NULL |
| ST-0306 LUNG_CANCER 그룹 'sgpt' anchor 날짜 | Completeness | error | LUNG_CANCER | 1 | ['htlg_diag_cd_po', 'htlg_diag_nm_po', 'sgpt_hvst_site_cd'] 값 있으나 anchor srgc_ptem_ymd NULL |
| ST-0317 LUNG_CANCER 그룹 'bpsy' anchor 날짜 | Completeness | error | LUNG_CANCER | 1 | ['bpsy_lung_site_dtlc_cd', 'bpsy_lung_site_dtlc_nm', 'bpsy_mthd_kncd'] 값 있으나 anchor bpsy_ymd NULL |
| ST-0319 LUNG_CANCER 환자 불변 필드 일관성 | Plausibility | warning | LUNG_CANCER | 16 | histologic_diagnosis 값이 환자 내에서 다름: ['2', '3'] / histologic_diagnosis 값이 환자 내에서 다름: ['1', '2'] |
| ST-1054 ADVERSE_EVENT 컬럼 구성 | Conformance | error | ADVERSE_EVENT | 1 | 별칭 컬럼 antp_therapy_id 를 antp_id 로 해석함 (경고) |
| ST-1084 ADVERSE_EVENT.severity_concept_id 코드표 | Conformance | warning | ADVERSE_EVENT | 3 | severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 / severity_concept_id=7 코드표(OMOP.severity_concept_id) 밖 |
| SEM-COM-001 방문 종료일 >= 시작일 | Plausibility | error | VISIT_OCCURRENCE | 3 | visit_end_date 2000-01-01 < visit_start_date 2020-07-21 / visit_end_date 2000-01-01 < visit_start_date 2023-03-08 |
| SEM-COM-003 사망 이후 임상 이벤트 금지 | Plausibility | error | PERSON | 5 | 이벤트일 2026-08-30 > death_date 2022-09-09 / 이벤트일 2026-08-30 > death_date 2020-09-25 |
| SEM-COM-005 이벤트-방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 100330 의 person_id=100019 / visit 100431 의 person_id=100024 |
| SEM-COM-006 이벤트일이 방문 기간 안에 있음 | Plausibility | warning | VISIT_OCCURRENCE | 30 | 이벤트일 2026-08-30 가 방문기간 2022-03-05~2022-03-08 밖 / 이벤트일 2026-08-30 가 방문기간 2019-10-13~2019-10-16 밖 |
| SEM-COM-007 약물 종료일 >= 시작일, days_supply 일치 | Plausibility | error | DRUG_EXPOSURE | 3 | end < start / end < start |
| SEM-COM-008 투여 빈도/간격 조건부 필수 | Completeness | warning | DRUG_EXPOSURE | 3 | frequency_per_day 있음, days_supply 없음 / frequency_per_day 있음, days_supply 없음 |
| SEM-COM-009 검사 결과값 존재 | Completeness | error | MEASUREMENT | 6 | value_as_number, value_as_concept_id 모두 NULL / value_as_number, value_as_concept_id 모두 NULL |
| SEM-COM-011 검사항목별 타당 범위 | Plausibility | warning | MEASUREMENT | 3 | Platelet count=99999.0 (타당범위 1.0~2000.0) / CEA=99999.0 (타당범위 0.0~10000.0) |
| SEM-COM-012 age_at_index 와 index date 일치 | Plausibility | error | CONDITION_OCCURRENCE,PERSON | 3 | age_at_index=94, index_date=2019-02-28, year_of_birth=1940 / age_at_index=80, index_date=2022-02-17, year_of_birth=1957 |
| SEM-COM-013 코호트 포함 조건 | Completeness | error | CONDITION_OCCURRENCE,PERSON,VISIT_OCCURRENCE | 2 | 코호트 정의 진단 없음 / 코호트 정의 진단 없음 |
| SEM-COM-015 특화 테이블 고아 환자 | Conformance | error | PERSON | 1 | PERSON 에 없는 person_id |
| SEM-COM-016 이상사례 발생일 >= 항암 시작일 | Plausibility | error | ADVERSE_EVENT,ANTP_THERAPY | 3 | AE 2015-01-01 < antp_start_date 2023-04-17 / AE 2015-01-01 < antp_start_date 2021-03-01 |
| SEM-COM-017 중대한 이상사례 조건부 필수 / 치명 결과와 사망 일치 | Completeness | error | ADVERSE_EVENT,PERSON | 3 | is_serious=1 인데 seriousness_concept_id 없음 / is_serious=1 인데 seriousness_concept_id 없음 |
| SEM-COM-018 항암요법 기간 및 line 번호 | Plausibility | error | ANTP_THERAPY | 3 | line=5 이나 시작일 순서=1 / line=5 이나 시작일 순서=1 |
| SEM-COM-023 중복 이벤트 레코드 | Plausibility | warning | MEASUREMENT | 3 | 2건 중복 / 2건 중복 |
| SEM-COM-029 특화 테이블 death_date 와 PERSON 일치 | Conformance | error | PERSON | 3 | LUNG_CANCER.death_date=2024-01-01 <> PERSON.death_date=NULL / LUNG_CANCER.death_date=2024-01-01 <> PERSON.death_date=NULL |
| SEM-COM-030 특화 테이블 방문 환자 일치 | Conformance | error | VISIT_OCCURRENCE | 3 | visit 100304 의 person_id=100016 / visit 101210 의 person_id=100064 |
| SEM-CA-001 수술 후 외과병리일 >= 수술일 | Plausibility | error | LUNG_CANCER | 3 | srgc_ptem_ymd 2010-01-01 에 대응하는 수술(0~60일 전) 없음 / srgc_ptem_ymd 2010-01-01 에 대응하는 수술(0~60일 전) 없음 |
| SEM-CA-002 병리 TNM 조합 일치 | Conformance | warning | LUNG_CANCER | 2 | path TNM T1N0M1 <> T3N2M0 / path TNM T1N0M1 <> T2aN0M0 |
| SEM-CA-003 방사선 총선량 = 1회 선량 x 횟수 | Plausibility | warning | LUNG_CANCER | 2 | rd_totl_gy=12.5 vs 2.0x30 / rd_totl_gy=12.5 vs 2.0x30 |
| SEM-CA-004 BMI = 체중 / 신장^2 | Plausibility | warning | LUNG_CANCER | 3 | bmi_vl=19.9 vs 계산값 29.1 / bmi_vl=19.9 vs 계산값 20.9 |
| SEM-LC-002 흡연력 논리 | Plausibility | warning | LUNG_CANCER | 2 | 흡연력 N 인데 smok_qty/smok_dtrn_ycnt 있음 / 흡연력 N 인데 smok_qty/smok_dtrn_ycnt 있음 |
| SEM-LC-003 종양 크기와 T 병기 일치 | Plausibility | warning | LUNG_CANCER | 2 | T=T1b 인데 최대직경 8.5cm / T=T1b 인데 최대직경 8.5cm |
| SEM-LC-005 조직형 코드와 원천명 일치 | Conformance | warning | LUNG_CANCER | 7 | 2개의 조직형 코드 / 2개의 조직형 코드 |
