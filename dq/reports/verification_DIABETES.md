# 검출 성능 검증: DIABETES

- clean 데이터: 규칙 392개 실행, 위반 0건 (오탐)
- dirty 데이터: 주입 오류 94건 중 94건 검출, 재현율 1.0
- 오류 유형 29종 중 전부 검출 29종
- 주입 오류의 부수 효과로 함께 발화한 규칙: SEM-COM-006, SEM-COM-015, SEM-COM-030, SEM-DM-005, SEM-DM-006, ST-0758, ST-0760

| 오류 유형 | 분류 | 주입 | 검출 | 재현율 |
|---|---|---|---|---|
| AGE_AT_INDEX_MISMATCH | Plausibility | 3 | 3 | 1.0 |
| ALIAS_COLUMN | Conformance | 1 | 1 | 1.0 |
| ANTP_IN_NONCANCER | Conformance | 3 | 3 | 1.0 |
| CODELIST | Conformance | 6 | 6 | 1.0 |
| COHORT_CONDITION_MISSING | Completeness | 2 | 2 | 1.0 |
| DEATH_DATE_MISMATCH | Conformance | 3 | 3 | 1.0 |
| DM_DRUG_MISMATCH | Conformance | 2 | 2 | 1.0 |
| DM_MEASUREMENT_MISMATCH | Conformance | 3 | 3 | 1.0 |
| DM_VISIT_MISMATCH | Conformance | 3 | 3 | 1.0 |
| DM_VISIT_NOT_OUTPATIENT | Conformance | 2 | 2 | 1.0 |
| DRUG_END_BEFORE_START | Plausibility | 3 | 3 | 1.0 |
| DUPLICATE_RECORD | Plausibility | 3 | 3 | 1.0 |
| EVENT_AFTER_DEATH | Plausibility | 3 | 3 | 1.0 |
| FK_ORPHAN | Conformance | 6 | 6 | 1.0 |
| FREQ_WITHOUT_DAYS | Completeness | 3 | 3 | 1.0 |
| FUTURE_DATE | Plausibility | 3 | 3 | 1.0 |
| GROUP_ANCHOR_NULL | Completeness | 6 | 6 | 1.0 |
| MEASUREMENT_IMPLAUSIBLE | Plausibility | 3 | 3 | 1.0 |
| MEASUREMENT_NO_VALUE | Completeness | 3 | 3 | 1.0 |
| MISSING_COLUMN | Conformance | 1 | 1 | 1.0 |
| PK_DUPLICATE | Conformance | 3 | 3 | 1.0 |
| RANGE | Plausibility | 4 | 4 | 1.0 |
| REQUIRED_NULL | Completeness | 6 | 6 | 1.0 |
| SERIOUS_AE_INCOMPLETE | Completeness | 3 | 3 | 1.0 |
| TYPE_DATE | Conformance | 6 | 6 | 1.0 |
| TYPE_NUMBER | Conformance | 3 | 3 | 1.0 |
| UNKNOWN_COLUMN | Conformance | 1 | 1 | 1.0 |
| VISIT_END_BEFORE_START | Plausibility | 3 | 3 | 1.0 |
| VISIT_PERSON_MISMATCH | Conformance | 3 | 3 | 1.0 |
