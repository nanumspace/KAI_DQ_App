# Good Sample · 림프종 (LYMPHOMA)

명세 v3의 가상 환자 1명에서 나온 **연결된 모든 행**입니다. 실제 환자 자료가 아닙니다. 코호트별 진단·검사·진료·처방·기록·추적 경과를 여러 테이블로 제출할 때의 구조 예시입니다. 한 질환의 모든 환자에게 필요한 검사나 치료를 뜻하지 않습니다.

- 환자: 1명 (가상 ID 600001)
- 첫 방문 ~ 마지막 방문: 2022-07-04 ~ 2026-04-01
- 방문 26건, 검사 94건, 약물 43건, 문서 6건, 요법 2건
- 사망일: 기록 없음

## 이 환자에게 실제로 기록된 내용

- 질환 표: `diagnosis_date=2022-07-04`, `histology_icdo3_code=9680/3`, `cell_of_origin=GCB`, `double_expressor_yn=0`, `minimal_residual_disease_result=Positive (1e-4)`
- 요법: R-CHOP (2022-07-15 ~ 2022-11-01, line 1)
- 요법: R-GDP (2024-08-03 ~ 2024-09-17, line 2)
- 기록 (2022-07-06): Lymph node, inguinal lymph node, excisional biopsy: Diffuse large B-cell lymphoma. Immunohistochemistry: CD20 positive, CD10 positive, BCL6 positive, MUM1 negative. Cell of origin by Hans algorithm: GCB. MYC/BCL2 protein co-expression absent. Ki-67 74%. Specimen adequate for ancillary studies.
- 기록 (2024-10-03): FDG PET/CT (end of treatment). Deauville score 3. Complete metabolic response.

## 테이블별 행 수

| 테이블 | 행 수 |
|---|---:|
| PERSON | 1 |
| VISIT_OCCURRENCE | 26 |
| PROCEDURE_OCCURRENCE | 16 |
| DRUG_EXPOSURE | 43 |
| CONDITION_OCCURRENCE | 4 |
| MEASUREMENT | 94 |
| OBSERVATION | 1 |
| NOTE | 6 |
| LYMPHOMA | 1 |
| ADVERSE_EVENT | 3 |
| SACT | 2 |
| DRUG_INGREDIENT_STRUCTURE | 7 |

DRUG_INGREDIENT_STRUCTURE는 환자별 표가 아니라 해당 환자 약물의 성분 참조표입니다. 원천 시스템 코드·파일 ID 등은 원본이 없는 가상데이터이므로 임의로 꾸며 넣지 않았습니다. 빈 선택 컬럼은 실제 제출 시 해당 자료가 있으면 원천 값을 채우고, 없으면 비워 두어야 합니다. OMOP concept_id의 기관별 Athena 매핑도 확정되지 않았습니다. CSV는 UTF-8, 날짜는 YYYY-MM-DD입니다. 검증 실행일은 2026-09-07로 맞추세요.
