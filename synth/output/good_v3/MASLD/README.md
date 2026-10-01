# Good Sample · 대사이상지방간 (MASLD)

명세 v3의 가상 환자 1명에서 나온 **연결된 모든 행**입니다. 실제 환자 자료가 아닙니다. 코호트별 진단·검사·진료·처방·기록·추적 경과를 여러 테이블로 제출할 때의 구조 예시입니다. 한 질환의 모든 환자에게 필요한 검사나 치료를 뜻하지 않습니다.

- 환자: 1명 (가상 ID 400087)
- 첫 방문 ~ 마지막 방문: 2019-10-28 ~ 2022-02-26
- 방문 14건, 검사 76건, 약물 44건, 문서 6건
- 사망일: 기록 없음

## 이 환자에게 실제로 기록된 내용

- 질환 표: `fib4_score=0.5`, `apri_score=0.31`, `bard_score=1`, `safe_score=-45`, `liverrisk_score=4.88`
- 기록 (2019-10-28): Abdomen ultrasonography. Liver: diffusely increased parenchymal echogenicity with moderate posterior attenuation, compatible with moderate hepatic steatosis. Liver contour smooth. Spleen normal in size. No focal hepatic lesion. Gallbladder and bile ducts unremarkable. Impression: 중등도 지방간.
- 기록 (2021-11-28): Transient elastography (FibroScan). Liver stiffness measurement 6.7 kPa (IQR/median 11%, 10 valid measurements), CAP 289 dB/m. Interpretation: fibrosis stage F1, steatosis S2.

## 테이블별 행 수

| 테이블 | 행 수 |
|---|---:|
| PERSON | 1 |
| VISIT_OCCURRENCE | 14 |
| PROCEDURE_OCCURRENCE | 5 |
| DRUG_EXPOSURE | 44 |
| CONDITION_OCCURRENCE | 5 |
| MEASUREMENT | 76 |
| OBSERVATION | 7 |
| NOTE | 6 |
| MASLD | 1 |
| ADVERSE_EVENT | 1 |
| DRUG_INGREDIENT_STRUCTURE | 3 |

DRUG_INGREDIENT_STRUCTURE는 환자별 표가 아니라 해당 환자 약물의 성분 참조표입니다. 원천 시스템 코드·파일 ID 등은 원본이 없는 가상데이터이므로 임의로 꾸며 넣지 않았습니다. 빈 선택 컬럼은 실제 제출 시 해당 자료가 있으면 원천 값을 채우고, 없으면 비워 두어야 합니다. OMOP concept_id의 기관별 Athena 매핑도 확정되지 않았습니다. CSV는 UTF-8, 날짜는 YYYY-MM-DD입니다. 검증 실행일은 2026-09-07로 맞추세요.
