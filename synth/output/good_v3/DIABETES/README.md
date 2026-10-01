# Good Sample · 당뇨병 (DIABETES)

명세 v3의 가상 환자 1명에서 나온 **연결된 모든 행**입니다. 실제 환자 자료가 아닙니다. 코호트별 진단·검사·진료·처방·기록·추적 경과를 여러 테이블로 제출할 때의 구조 예시입니다. 한 질환의 모든 환자에게 필요한 검사나 치료를 뜻하지 않습니다.

- 환자: 1명 (가상 ID 500020)
- 첫 방문 ~ 마지막 방문: 2022-12-03 ~ 2026-08-11
- 방문 17건, 검사 126건, 약물 64건, 문서 17건
- 사망일: 기록 없음

## 이 환자에게 실제로 기록된 내용

- 질환 표: `condition_start_date=2022-12-03`
- 기록 (2022-12-03): Endocrinology initial visit. Newly diagnosed type 2 diabetes mellitus. HbA1c 8.7%, FBS 165.0 mg/dL, BP 122.0/79.0 mmHg, BMI 28.8 kg/m2, never smoker. Comorbidity: hypertension, dyslipidemia. Labs: LDL 123.6, HDL 39.0, TG 156.0 mg/dL; AST/ALT 30.9/25.4 U/L; Cr 0.58 mg/dL, eGFR 105.0. Fundoscopy done. Plan: continue metformin 500 mg bid, atorvastatin 20 mg qhs, lisinopril 10 mg qd. Lifestyle counseling, f/u 3 months.
- 기록 (2026-08-11): Endocrinology follow-up (visit 16). T2DM, glycemic control suboptimal: HbA1c 7.2%, FBS 114.0 mg/dL. BP 141.0/91.0 mmHg, BMI 28.7 kg/m2. Plan: continue metformin 500 mg bid, atorvastatin 20 mg qhs, lisinopril 10 mg qd, sitagliptin 100 mg qd. Lifestyle counseling, f/u 3 months.

## 테이블별 행 수

| 테이블 | 행 수 |
|---|---:|
| PERSON | 1 |
| VISIT_OCCURRENCE | 17 |
| PROCEDURE_OCCURRENCE | 4 |
| DRUG_EXPOSURE | 64 |
| CONDITION_OCCURRENCE | 4 |
| MEASUREMENT | 126 |
| OBSERVATION | 1 |
| NOTE | 17 |
| DIABETES | 1 |
| ADVERSE_EVENT | 1 |
| DRUG_INGREDIENT_STRUCTURE | 5 |

DRUG_INGREDIENT_STRUCTURE는 환자별 표가 아니라 해당 환자 약물의 성분 참조표입니다. 원천 시스템 코드·파일 ID 등은 원본이 없는 가상데이터이므로 임의로 꾸며 넣지 않았습니다. 빈 선택 컬럼은 실제 제출 시 해당 자료가 있으면 원천 값을 채우고, 없으면 비워 두어야 합니다. OMOP concept_id의 기관별 Athena 매핑도 확정되지 않았습니다. CSV는 UTF-8, 날짜는 YYYY-MM-DD입니다. 검증 실행일은 2026-09-07로 맞추세요.
