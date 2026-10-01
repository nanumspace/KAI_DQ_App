# Good Sample · 폐암 (LUNG_CANCER)

명세 v3의 가상 환자 1명에서 나온 **연결된 모든 행**입니다. 실제 환자 자료가 아닙니다. 코호트별 진단·검사·진료·처방·기록·추적 경과를 여러 테이블로 제출할 때의 구조 예시입니다. 한 질환의 모든 환자에게 필요한 검사나 치료를 뜻하지 않습니다.

- 환자: 1명 (가상 ID 100003)
- 첫 방문 ~ 마지막 방문: 2022-05-09 ~ 2026-01-23
- 방문 37건, 검사 171건, 약물 26건, 문서 5건, 요법 2건
- 사망일: 기록 없음

## 이 환자에게 실제로 기록된 내용

- 질환 표: `diag_rgst_ymd=2022-05-09`, `histologic_diagnosis=1`, `histology_icdo3_code=8140/3`, `primary_site_icdo3_code=C34.3`, `histologic_diagnosis_source_value=Adenocarcinoma`, `clinical_stage=IIIA`, `clinical_stage_ajcc_edition=8`, `stage_iv_diagnosis_date=2024-04-09`
- 요법: Cisplatin + Pemetrexed (2022-08-10 ~ 2022-10-12, line 1)
- 요법: Osimertinib (2024-04-23 ~ 2025-07-14, line 2)
- 기록 (2022-05-09): Chest CT (contrast). 우하엽 에 spiculated mass. Mediastinal lymphadenopathy. No distant metastasis. Impression: Lung cancer, 우하엽, cT2aN2M0. Recommend tissue confirmation.
- 기록 (2024-04-09): Chest CT: new Brain lesion suspicious for recurrence.
- clinical_stage는 최초 진단 시 병기이며 stage_iv_diagnosis_date는 추적 중 IV기 진단일일 수 있습니다.

## 테이블별 행 수

| 테이블 | 행 수 |
|---|---:|
| PERSON | 1 |
| VISIT_OCCURRENCE | 37 |
| PROCEDURE_OCCURRENCE | 12 |
| DRUG_EXPOSURE | 26 |
| CONDITION_OCCURRENCE | 9 |
| MEASUREMENT | 171 |
| OBSERVATION | 2 |
| NOTE | 5 |
| LUNG_CANCER | 1 |
| ADVERSE_EVENT | 7 |
| SACT | 2 |
| DRUG_INGREDIENT_STRUCTURE | 4 |

DRUG_INGREDIENT_STRUCTURE는 환자별 표가 아니라 해당 환자 약물의 성분 참조표입니다. 원천 시스템 코드·파일 ID 등은 원본이 없는 가상데이터이므로 임의로 꾸며 넣지 않았습니다. 빈 선택 컬럼은 실제 제출 시 해당 자료가 있으면 원천 값을 채우고, 없으면 비워 두어야 합니다. OMOP concept_id의 기관별 Athena 매핑도 확정되지 않았습니다. CSV는 UTF-8, 날짜는 YYYY-MM-DD입니다. 검증 실행일은 2026-09-07로 맞추세요.
