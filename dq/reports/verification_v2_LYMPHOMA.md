# 검출 성능 검증: LYMPHOMA

- clean 데이터: 규칙 531개 실행, 위반 0건 (오탐)
- dirty 데이터: 주입 오류 100건 중 100건 검출, 재현율 1.0
- 오류 유형 17종 중 전부 검출 17종
- 주입 오류의 부수 효과로 함께 발화한 규칙: SEMV-COM-004, SEMV-COM-006, SEMV-EP-002, SEMV-EP-003, SEMV-EP-004, SV-0197, SV-0209, SV-0250, SV-0928

| 오류 유형 | 분류 | 주입 | 검출 | 재현율 |
|---|---|---|---|---|
| ANCHOR_MISSING | Completeness | 6 | 6 | 1.0 |
| CODE_OUT_OF_SET | Conformance | 12 | 12 | 1.0 |
| COLUMN_MISSING | Conformance | 1 | 1 | 1.0 |
| CONCEPT_OUT_OF_SET | Conformance | 12 | 12 | 1.0 |
| DAYS_SUPPLY_MISMATCH | Plausibility | 3 | 3 | 1.0 |
| EPISODE_END_BEFORE_START | Plausibility | 2 | 2 | 1.0 |
| EVENT_AFTER_DEATH | Plausibility | 2 | 2 | 1.0 |
| FK_BROKEN | Conformance | 12 | 12 | 1.0 |
| FUTURE_DATE | Plausibility | 9 | 9 | 1.0 |
| PK_DUP | Conformance | 3 | 3 | 1.0 |
| REQUIRED_EITHER_NULL | Completeness | 3 | 3 | 1.0 |
| REQUIRED_NULL | Completeness | 12 | 12 | 1.0 |
| REQUIRED_NULL_WHEN | Completeness | 10 | 10 | 1.0 |
| SPECIMEN_DATE_MISMATCH | Conformance | 2 | 2 | 1.0 |
| TYPE_BAD | Conformance | 6 | 6 | 1.0 |
| VISIT_BEFORE_BIRTH | Plausibility | 2 | 2 | 1.0 |
| VISIT_END_BEFORE_START | Plausibility | 3 | 3 | 1.0 |
