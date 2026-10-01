# 검출 성능 검증: LUNG_CANCER

- clean 데이터: 규칙 287개 실행, 위반 0건 (오탐)
- dirty 데이터: 주입 오류 275건 중 275건 검출, 재현율 1.0
- 오류 유형 34종 중 전부 검출 34종
- 주입 오류의 부수 효과로 함께 발화한 규칙: 없음

| 오류 유형 | 분류 | 주입 | 검출 | 재현율 |
|---|---|---|---|---|
| AE_AFTER_DEATH | Plausibility | 1 | 1 | 1.0 |
| CODELIST | Conformance | 19 | 19 | 1.0 |
| COLUMN_MISSING | Conformance | 2 | 2 | 1.0 |
| DAYS_SUPPLY_MISMATCH | Plausibility | 2 | 2 | 1.0 |
| DISEASE_VISIT_PERSON_MISMATCH | Conformance | 1 | 1 | 1.0 |
| DRUG_END_BEFORE_START | Plausibility | 1 | 1 | 1.0 |
| DRUG_SACT_PERSON_MISMATCH | Conformance | 1 | 1 | 1.0 |
| EVENT_AFTER_DEATH | Plausibility | 1 | 1 | 1.0 |
| EVENT_VISIT_PERSON_MISMATCH | Conformance | 2 | 2 | 1.0 |
| FK_BROKEN | Conformance | 19 | 19 | 1.0 |
| FREQ_WITHOUT_DAYS_SUPPLY | Completeness | 1 | 1 | 1.0 |
| FUTURE_DATE | Plausibility | 17 | 17 | 1.0 |
| HISTOLOGY_CODE_MISMATCH | Plausibility | 2 | 2 | 1.0 |
| INTERVAL_WITHOUT_NUMBER | Completeness | 1 | 1 | 1.0 |
| L01_WITHOUT_SACT | Completeness | 2 | 2 | 1.0 |
| LDED_NOT_SMALL_CELL | Conformance | 1 | 1 | 1.0 |
| LDED_WITH_EDITION | Conformance | 1 | 1 | 1.0 |
| PATTERN | Conformance | 2 | 2 | 1.0 |
| PERSON_WITHOUT_DISEASE_ROW | Completeness | 1 | 1 | 1.0 |
| PK_DUP | Conformance | 12 | 12 | 1.0 |
| PK_NULL | Completeness | 12 | 12 | 1.0 |
| PRIMARY_SITE_NOT_LUNG | Plausibility | 1 | 1 | 1.0 |
| PROGRESSION_BEFORE_START | Plausibility | 1 | 1 | 1.0 |
| RANGE | Plausibility | 16 | 16 | 1.0 |
| RANGE_LOW_GT_HIGH | Plausibility | 2 | 2 | 1.0 |
| REQUIRED_NULL | Completeness | 53 | 53 | 1.0 |
| SACT_END_BEFORE_START | Plausibility | 1 | 1 | 1.0 |
| SACT_LINE_MISMATCH | Plausibility | 1 | 1 | 1.0 |
| SACT_START_NE_DRUG_MIN | Plausibility | 1 | 1 | 1.0 |
| STAGE_NOT_IN_EDITION | Conformance | 2 | 2 | 1.0 |
| STAGE_WITHOUT_EDITION | Completeness | 1 | 1 | 1.0 |
| TYPE_BAD | Conformance | 92 | 92 | 1.0 |
| VISIT_BEFORE_BIRTH | Plausibility | 1 | 1 | 1.0 |
| VISIT_END_BEFORE_START | Plausibility | 2 | 2 | 1.0 |
