# 서식 → 레코드 예시 (폐암 환자 100001)

`crf_forms_v2.yaml` 의 매핑 규칙을 `build_spec_v2.py` 가 실제로 적용해 만든 결과입니다. concept_id 는 `vocab/CONCEPT.csv` 의 K-AI 어휘이며, `<concept: …>` 는 아직 값 집합에 없는 값(2.1 에서 채움), `<…>` 는 다른 서식이 만든 레코드 참조입니다.

## COHORT_INDEX · 코호트 인덱스 서식

입력 (서식 한 행):

```
person_id=100001, index_date=2022-03-25, diagnosis_registered_date=2022-03-25, diagnosis_name=C34.1, last_followup_date=2023-06-30, last_vital_status=생존
```

생성 레코드:

- **COHORT** cohort_definition_id=10000000024, subject_id=100001, cohort_start_date=2022-03-25, cohort_end_date=2023-06-30
- **OBSERVATION_PERIOD** observation_period_id=1001, person_id=100001, observation_period_start_date=2022-03-25, observation_period_end_date=2023-06-30, period_type_concept_id=10000000001
- **CONDITION_OCCURRENCE** condition_occurrence_id=5001, person_id=100001, condition_concept_id=10000000030, condition_start_date=2022-03-25, condition_type_concept_id=10000000001, condition_source_value=C34.1
- **EPISODE** episode_id=7001, person_id=100001, episode_concept_id=10000000004, episode_start_date=2022-03-25, episode_end_date=2023-06-30, episode_number=1, episode_object_concept_id=10000000030, episode_type_concept_id=10000000001
- **EPISODE_EVENT** episode_id=7001, event_id=5001, episode_event_field_concept_id=10000000010
- **OBSERVATION** observation_id=8001, person_id=100001, observation_concept_id=10000000386, observation_date=2022-03-25, observation_type_concept_id=10000000001, value_as_concept_id=<concept: 생존>, value_source_value=생존, observation_event_id=5001, obs_event_field_concept_id=10000000010

## STAGING · 진단·병기 평가 서식

입력 (서식 한 행):

```
person_id=100001, staging_date=2022-03-27, initial_clinical_stage=IV, clinical_tnm=cT2aN2M1b, imaging_distant_metastasis_yn=1, distant_metastasis_site=Adrenal gland, distant_metastasis_date=2022-03-25
```

생성 레코드:

- **MEASUREMENT** measurement_id=9001, person_id=100001, measurement_concept_id=10000000387, measurement_date=2022-03-27, measurement_type_concept_id=10000000001, value_as_concept_id=10000000087, value_source_value=IV, measurement_event_id=5001, meas_event_field_concept_id=10000000010
- **MEASUREMENT** measurement_id=9002, person_id=100001, measurement_concept_id=10000000390, measurement_date=2022-03-27, measurement_type_concept_id=10000000001, value_source_value=cT2aN2M1b, measurement_event_id=5001, meas_event_field_concept_id=10000000010
- **MEASUREMENT** measurement_id=9003, person_id=100001, measurement_concept_id=10000000393, measurement_date=2022-03-27, measurement_type_concept_id=10000000001, value_as_concept_id=10000000190, value_source_value=1, measurement_event_id=5001, meas_event_field_concept_id=10000000010
- **OBSERVATION** observation_id=8002, person_id=100001, observation_concept_id=10000000394, observation_date=2022-03-27, observation_type_concept_id=10000000001, value_as_string=2022-03-25, observation_event_id=5001, obs_event_field_concept_id=10000000010
- **MEASUREMENT** measurement_id=9004, person_id=100001, measurement_concept_id=10000000395, measurement_date=2022-03-27, measurement_type_concept_id=10000000001, value_as_concept_id=<concept: Adrenal gland>, value_source_value=Adrenal gland, measurement_event_id=5001, meas_event_field_concept_id=10000000010

## ANTP_THERAPY · 항암·전신치료 서식

입력 (서식 한 행):

```
person_id=100001, antp_id=1, regimen_or_line_of_therapy=1, regimen=osimertinib, antp_start_date=2022-04-10, antp_end_date=2023-01-15, number_of_cycles=9, treatment_intent_type=고식
```

생성 레코드:

- **EPISODE** episode_id=7002, person_id=100001, episode_concept_id=10000000008, episode_start_date=2022-04-10, episode_end_date=2023-01-15, episode_parent_id=7001, episode_number=1, episode_object_concept_id=<concept: osimertinib>, episode_type_concept_id=10000000001, episode_source_value=osimertinib
- **OBSERVATION** observation_id=8003, person_id=100001, observation_concept_id=10000000554, observation_date=2022-04-10, observation_type_concept_id=10000000001, value_as_number=9, observation_event_id=7002, obs_event_field_concept_id=10000000014
- **OBSERVATION** observation_id=8004, person_id=100001, observation_concept_id=10000000557, observation_date=2022-04-10, observation_type_concept_id=10000000001, value_as_concept_id=<concept: 고식>, value_source_value=고식, observation_event_id=7002, obs_event_field_concept_id=10000000014
- **EPISODE_EVENT** episode_id=7002, event_id=DRUG_EXPOSURE.drug_exposure_id where antp_id = $antp_id, episode_event_field_concept_id=10000000012

## RESPONSE_ASSESSMENT · 반응·경과 평가 서식

입력 (서식 한 행):

```
person_id=100001, antp_id=1, response_assessment_date=2022-07-12, response_criteria=RECIST 1.1, response_timepoint=3개월, best_overall_response=PR, measurable_disease_yn=1, target_lesions_count=2, spd_mm2=820
```

생성 레코드:

- **MEASUREMENT** measurement_id=9005, person_id=100001, measurement_concept_id=10000000570, measurement_date=2022-07-12, measurement_type_concept_id=10000000001, value_as_concept_id=10000000190, value_source_value=1, measurement_event_id=7002, meas_event_field_concept_id=10000000014
- **MEASUREMENT** measurement_id=9006, person_id=100001, measurement_concept_id=10000000571, measurement_date=2022-07-12, measurement_type_concept_id=10000000001, value_as_number=2, measurement_event_id=7002, meas_event_field_concept_id=10000000014
- **MEASUREMENT** measurement_id=9007, person_id=100001, measurement_concept_id=10000000572, measurement_date=2022-07-12, measurement_type_concept_id=10000000001, value_as_number=820, unit_concept_id=10000000052, measurement_event_id=7002, meas_event_field_concept_id=10000000014
- **MEASUREMENT** measurement_id=9008, person_id=100001, measurement_concept_id=10000000575, measurement_date=2022-07-12, measurement_type_concept_id=10000000001, value_as_concept_id=<concept: 3개월>, value_source_value=3개월, measurement_event_id=7002, meas_event_field_concept_id=10000000014
- **MEASUREMENT** measurement_id=9009, person_id=100001, measurement_concept_id=10000000576, measurement_date=2022-07-12, measurement_type_concept_id=10000000001, value_as_concept_id=10000000142, value_source_value=RECIST 1.1, measurement_event_id=7002, meas_event_field_concept_id=10000000014
- **MEASUREMENT** measurement_id=9010, person_id=100001, measurement_concept_id=10000000581, measurement_date=2022-07-12, measurement_type_concept_id=10000000001, value_as_concept_id=10000000153, value_source_value=PR, measurement_event_id=7002, meas_event_field_concept_id=10000000014

## ADVERSE_EVENT · 이상사례 서식

입력 (서식 한 행):

```
person_id=100001, antp_id=1, adverse_event_start_date=2022-05-02, adverse_event_concept_id=10037844, adverse_event_source_value=Rash, severity_concept_id=2, causality_concept_id=가능, is_serious=0
```

생성 레코드:

- **CONDITION_OCCURRENCE** condition_occurrence_id=5002, person_id=100001, condition_concept_id=<concept: 10037844>, condition_start_date=2022-05-02, condition_type_concept_id=10000000001, condition_status_concept_id=10000000040, condition_source_value=Rash
- **EPISODE_EVENT** episode_id=7002, event_id=5002, episode_event_field_concept_id=10000000010
- **MEASUREMENT** measurement_id=9011, person_id=100001, measurement_concept_id=10000000589, measurement_date=2022-05-02, measurement_type_concept_id=10000000001, value_as_concept_id=10000000171, value_source_value=2, measurement_event_id=5002, meas_event_field_concept_id=10000000010
- **OBSERVATION** observation_id=8005, person_id=100001, observation_concept_id=10000000590, observation_date=2022-05-02, observation_type_concept_id=10000000001, value_as_concept_id=10000000178, value_source_value=가능, observation_event_id=5002, obs_event_field_concept_id=10000000010
- **OBSERVATION** observation_id=8006, person_id=100001, observation_concept_id=10000000591, observation_date=2022-05-02, observation_type_concept_id=10000000001, value_as_concept_id=<concept: 0>, value_source_value=0, observation_event_id=5002, obs_event_field_concept_id=10000000010

## FAMILY_HISTORY · 가족력 서식

입력 (서식 한 행):

```
person_id=100001, record_date=2022-03-25, family_relation=모, family_cancer_type=폐암, family_member_age_at_diagnosis=62
```

생성 레코드:

- **OBSERVATION** observation_id=8007, person_id=100001, observation_concept_id=10000000041, observation_date=2022-03-25, observation_type_concept_id=10000000001, value_as_concept_id=<concept: 폐암>, qualifier_concept_id=10000000195, value_as_number=62, value_source_value=폐암

## SURGERY · 수술 서식

입력 (서식 한 행):

```
person_id=100001, surgery_date=2022-05-20, surgery_name=흉강경 폐엽절제술, surgery_purpose=근치, surgery_approach=흉강경, surgery_site=우중엽, ebl_ml=150
```

생성 레코드:

- **PROCEDURE_OCCURRENCE** procedure_occurrence_id=4001, person_id=100001, procedure_concept_id=<concept: 흉강경 폐엽절제술>, procedure_date=2022-05-20, procedure_type_concept_id=10000000001, modifier_concept_id=10000000224, procedure_source_value=흉강경 폐엽절제술
- **EPISODE_EVENT** episode_id=7001, event_id=4001, episode_event_field_concept_id=10000000011
- **OBSERVATION** observation_id=8008, person_id=100001, observation_concept_id=10000000533, observation_date=2022-05-20, observation_type_concept_id=10000000001, value_as_concept_id=10000000214, value_source_value=근치, observation_event_id=4001, obs_event_field_concept_id=10000000011
- **OBSERVATION** observation_id=8009, person_id=100001, observation_concept_id=10000000534, observation_date=2022-05-20, observation_type_concept_id=10000000001, value_as_concept_id=<concept: 우중엽>, value_source_value=우중엽, observation_event_id=4001, obs_event_field_concept_id=10000000011
- **MEASUREMENT** measurement_id=9012, person_id=100001, measurement_concept_id=10000000539, measurement_date=2022-05-20, measurement_type_concept_id=10000000001, value_as_number=150, unit_concept_id=10000000050, measurement_event_id=4001, meas_event_field_concept_id=10000000011

## RADIOTHERAPY · 방사선치료 서식

입력 (서식 한 행):

```
person_id=100001, rt_start_date=2022-08-01, rt_name=흉부 방사선치료, rt_purpose=고식, rt_site=흉부, rt_dose_per_fraction_gy=3.0, rt_fractions=10, rt_total_dose_gy=30.0
```

생성 레코드:

- **PROCEDURE_OCCURRENCE** procedure_occurrence_id=4002, person_id=100001, procedure_concept_id=<concept: 흉부 방사선치료>, procedure_date=2022-08-01, procedure_type_concept_id=10000000001, quantity=10, procedure_source_value=흉부 방사선치료
- **EPISODE_EVENT** episode_id=7001, event_id=4002, episode_event_field_concept_id=10000000011
- **OBSERVATION** observation_id=8010, person_id=100001, observation_concept_id=10000000545, observation_date=2022-08-01, observation_type_concept_id=10000000001, value_as_concept_id=10000000231, value_source_value=고식, observation_event_id=4002, obs_event_field_concept_id=10000000011
- **OBSERVATION** observation_id=8011, person_id=100001, observation_concept_id=10000000546, observation_date=2022-08-01, observation_type_concept_id=10000000001, value_as_concept_id=<concept: 흉부>, value_source_value=흉부, observation_event_id=4002, obs_event_field_concept_id=10000000011
- **MEASUREMENT** measurement_id=9013, person_id=100001, measurement_concept_id=10000000547, measurement_date=2022-08-01, measurement_type_concept_id=10000000001, value_as_number=3.0, unit_concept_id=10000000045, measurement_event_id=4002, meas_event_field_concept_id=10000000011
- **MEASUREMENT** measurement_id=9014, person_id=100001, measurement_concept_id=10000000549, measurement_date=2022-08-01, measurement_type_concept_id=10000000001, value_as_number=30.0, unit_concept_id=10000000045, measurement_event_id=4002, meas_event_field_concept_id=10000000011

## 규칙 요약

| 서식 | 기준 레코드 | 속성 레코드 | 속성의 연결 대상 |
|---|---|---|---|
| COHORT_INDEX | COHORT, OBSERVATION_PERIOD, CONDITION_OCCURRENCE, EPISODE, EPISODE_EVENT | OBSERVATION (필드 concept + 값) | DX → F_CONDITION |
| STAGING | (없음 · 속성만) | MEASUREMENT (필드 concept + 값) | DX → F_CONDITION |
| ANTP_THERAPY | EPISODE | OBSERVATION (필드 concept + 값) | REG → F_EPISODE |
| RESPONSE_ASSESSMENT | (없음 · 속성만) | MEASUREMENT (필드 concept + 값) | REG|EP → F_EPISODE |
| SURGERY | PROCEDURE_OCCURRENCE, EPISODE_EVENT | OBSERVATION (필드 concept + 값) | PROC → F_PROCEDURE |
| RADIOTHERAPY | PROCEDURE_OCCURRENCE, EPISODE_EVENT | MEASUREMENT (필드 concept + 값) | PROC → F_PROCEDURE |
| ADVERSE_EVENT | CONDITION_OCCURRENCE, EPISODE_EVENT | OBSERVATION (필드 concept + 값) | AE → F_CONDITION |
| FAMILY_HISTORY | OBSERVATION | OBSERVATION (필드 concept + 값) | FH → F_OBSERVATION |

속성 레코드 규칙: 서식의 나머지 필드마다 레코드 하나. `*_concept_id` = 필드 concept(CONCEPT.csv 의 Attribute), 값은 수치 → `value_as_number`(+unit), 범주 → `value_as_concept_id`(+`value_source_value`), 텍스트 → `value_as_string`. 날짜는 서식의 기준일, `*_event_id` 는 기준 레코드 id, `*_event_field_concept_id` 는 그 테이블의 Field concept.
