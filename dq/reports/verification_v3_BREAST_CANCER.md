# 검출 성능 검증: BREAST_CANCER

- clean 데이터: 규칙 287개 실행, 위반 0건 (오탐)
- dirty 데이터: 주입 오류 272건 중 272건 검출, 재현율 1.0
- 오류 유형 28종 중 전부 검출 28종
- 주입 오류의 부수 효과로 함께 발화한 규칙: 없음

| 오류 유형 | 분류 | 주입 | 검출 | 재현율 |
|---|---|---|---|---|
| AE_AFTER_DEATH | Plausibility | 1 | 1 | 1.0 |
| CODELIST | Conformance | 23 | 23 | 1.0 |
| COLUMN_MISSING | Conformance | 2 | 2 | 1.0 |
| DAYS_SUPPLY_MISMATCH | Plausibility | 2 | 2 | 1.0 |
| DISEASE_VISIT_PERSON_MISMATCH | Conformance | 1 | 1 | 1.0 |
| DRUG_END_BEFORE_START | Plausibility | 1 | 1 | 1.0 |
| DRUG_SACT_PERSON_MISMATCH | Conformance | 1 | 1 | 1.0 |
| EVENT_AFTER_DEATH | Plausibility | 1 | 1 | 1.0 |
| EVENT_VISIT_PERSON_MISMATCH | Conformance | 2 | 2 | 1.0 |
| FK_BROKEN | Conformance | 19 | 19 | 1.0 |
| FREQ_WITHOUT_DAYS_SUPPLY | Completeness | 1 | 1 | 1.0 |
| FUTURE_DATE | Plausibility | 16 | 16 | 1.0 |
| INTERVAL_WITHOUT_NUMBER | Completeness | 1 | 1 | 1.0 |
| L01_WITHOUT_SACT | Completeness | 2 | 2 | 1.0 |
| L02_WITHOUT_SACT | Completeness | 1 | 1 | 1.0 |
| PERSON_WITHOUT_DISEASE_ROW | Completeness | 1 | 1 | 1.0 |
| PK_DUP | Conformance | 12 | 12 | 1.0 |
| PK_NULL | Completeness | 12 | 12 | 1.0 |
| PROGRESSION_BEFORE_START | Plausibility | 1 | 1 | 1.0 |
| RANGE | Plausibility | 16 | 16 | 1.0 |
| RANGE_LOW_GT_HIGH | Plausibility | 2 | 2 | 1.0 |
| REQUIRED_NULL | Completeness | 53 | 53 | 1.0 |
| SACT_END_BEFORE_START | Plausibility | 1 | 1 | 1.0 |
| SACT_LINE_MISMATCH | Plausibility | 1 | 1 | 1.0 |
| SACT_START_NE_DRUG_MIN | Plausibility | 1 | 1 | 1.0 |
| TYPE_BAD | Conformance | 95 | 95 | 1.0 |
| VISIT_BEFORE_BIRTH | Plausibility | 1 | 1 | 1.0 |
| VISIT_END_BEFORE_START | Plausibility | 2 | 2 | 1.0 |
