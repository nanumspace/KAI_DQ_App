# Good Sample · 유방암 (BREAST_CANCER)

명세 v3의 가상 환자 1명에서 나온 **연결된 모든 행**입니다. 실제 환자 자료가 아닙니다. 코호트별 진단·검사·진료·처방·기록·추적 경과를 여러 테이블로 제출할 때의 구조 예시입니다. 한 질환의 모든 환자에게 필요한 검사나 치료를 뜻하지 않습니다.

- 환자: 1명 (가상 ID 200004)
- 첫 방문 ~ 마지막 방문: 2023-02-27 ~ 2026-05-09
- 방문 38건, 검사 108건, 약물 40건, 문서 5건, 요법 3건
- 사망일: 기록 없음

## 이 환자에게 실제로 기록된 내용

- 질환 표: `diag_rgst_ymd=2023-02-27`, `menopause_status=2`, `pregnant_at_diagnosis=2`, `history_of_live_birth=1`, `postpartum_at_diagnosis=2`, `fertility_history=2`
- 요법: Docetaxel + Carboplatin + Trastuzumab (TCH) (2023-03-23 ~ 2023-07-06, line 1)
- 요법: Trastuzumab (2023-09-02 ~ 2024-03-30, line 2)
- 요법: Letrozole (2024-04-13 ~ 2026-07-31, line 3)
- 기록 (2023-02-27): Bilateral digital mammography with tomosynthesis. Right breast: 4.9 cm irregular hypoechoic mass at the upper outer quadrant. Axilla: no abnormal lymph node. Contralateral breast: no suspicious finding. Impression: BI-RADS 4C. Recommend ultrasound-guided core needle biopsy.
- 기록 (2023-08-09): Breast, right, total mastectomy with sentinel lymph node biopsy: Invasive ductal carcinoma, NOS. Tumor size 1.7 cm. Lymphovascular invasion: absent. Resection margins: negative margin (>= 2 mm). Lymph nodes: 0/5 positive. Pathologic stage yT1cyN0M0. Miller-Payne grade 4 (partial response).

## 테이블별 행 수

| 테이블 | 행 수 |
|---|---:|
| PERSON | 1 |
| VISIT_OCCURRENCE | 38 |
| PROCEDURE_OCCURRENCE | 10 |
| DRUG_EXPOSURE | 40 |
| CONDITION_OCCURRENCE | 4 |
| MEASUREMENT | 108 |
| OBSERVATION | 1 |
| NOTE | 5 |
| BREAST_CANCER | 1 |
| ADVERSE_EVENT | 3 |
| SACT | 3 |
| DRUG_INGREDIENT_STRUCTURE | 3 |

DRUG_INGREDIENT_STRUCTURE는 환자별 표가 아니라 해당 환자 약물의 성분 참조표입니다. 원천 시스템 코드·파일 ID 등은 원본이 없는 가상데이터이므로 임의로 꾸며 넣지 않았습니다. 빈 선택 컬럼은 실제 제출 시 해당 자료가 있으면 원천 값을 채우고, 없으면 비워 두어야 합니다. OMOP concept_id의 기관별 Athena 매핑도 확정되지 않았습니다. CSV는 UTF-8, 날짜는 YYYY-MM-DD입니다. 검증 실행일은 2026-09-07로 맞추세요.
