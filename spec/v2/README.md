# 사전 v2 (초안) · OMOP 구조 + K-AI 어휘

전문가 자문(필수항목 조사)과 v1 사전을 합쳐 재설계한 데이터 모델입니다. v1(`spec/kai_cdm_spec.yaml`)과 나란히 두고, 규칙·가상데이터·검증 앱을 v2 로 옮기는 동안 v1 파이프라인은 그대로 동작합니다.

## 설계 원칙

1. **저장 테이블은 OMOP CDM 5.4 + Oncology 확장의 이름과 컬럼을 그대로 씁니다.** PERSON, OBSERVATION_PERIOD, DEATH, VISIT_OCCURRENCE, CONDITION_OCCURRENCE, PROCEDURE_OCCURRENCE, DRUG_EXPOSURE, MEASUREMENT, OBSERVATION, NOTE, SPECIMEN, COHORT, EPISODE, EPISODE_EVENT.
2. **concept_id 는 OMOP 이 아니라 K-AI 어휘입니다.** 64비트 정수, 10,000,000,000 부터 순번. 표준 코드(SNOMED CT, LOINC, MedDRA, KCD, EDI, UCUM)는 `CONCEPT.concept_code` 에 보관하고 `vocabulary_id` 로 출처를 남깁니다. 표준이 없는 용어만 `vocabulary_id = KAI`.
3. **병원은 CRF 서식을 채우고, 앱이 서식→레코드 규칙으로 저장 테이블을 만듭니다.** 서식 한 행이 기준 레코드(예: EPISODE) 하나와 속성 레코드(MEASUREMENT/OBSERVATION, `*_event_id` 로 연결) 여럿이 됩니다.
4. **OMOP 에 자리가 없는 병리 세부·바이오마커 변이·질환 항목은 K-AI 확장 테이블**로 저장합니다. OMOP 관례를 따라 닫힌 범주는 `<필드>_concept_id` + `<필드>_source_value` 쌍, 예/아니오는 값 집합 `YN` 의 정수입니다.
5. **한 테이블 = 행 단위 하나.** 질환 표는 `_BASELINE`(환자 1), `_EXAM`(검사 1), `_EVENT`(사건 1), `_ASSESSMENT`(평가 1), `_SURGERY_DETAIL`(수술 1)로 나뉩니다.
6. **등급(tier)과 필수(required)를 구분합니다.** `tier` 는 자문의 필수·권고·보류로 완전성 규칙의 근거이고, `required` 는 키와 사건일에만 겁니다.

## 서식과 저장 위치

| 서식 | 행 단위 | 저장 |
|---|---|---|
| COHORT_INDEX | 환자 1 | COHORT, OBSERVATION_PERIOD, CONDITION_OCCURRENCE(코호트 정의 진단), EPISODE(질환 에피소드) + OBSERVATION 속성 |
| STAGING | 환자 × 판정 시점 × 체계 | MEASUREMENT(병기·TNM·전이, 진단 레코드에 연결). 4기 진단일은 EPISODE(재발·진행) |
| ANTP_THERAPY | 요법 에피소드 1 | EPISODE(치료 레지멘, 질환 에피소드의 자식) + OBSERVATION 속성 + EPISODE_EVENT → DRUG_EXPOSURE |
| RESPONSE_ASSESSMENT | 평가 1 | MEASUREMENT(반응·병변, 치료 에피소드에 연결). 재발일은 EPISODE(재발) |
| SURGERY, RADIOTHERAPY | 수술 1 · 코스 1 | PROCEDURE_OCCURRENCE + EPISODE_EVENT + 속성(선량은 MEASUREMENT, 목적·부위는 OBSERVATION) |
| ADVERSE_EVENT | 사건 1 | CONDITION_OCCURRENCE(MedDRA 용어) + MEASUREMENT(CTCAE 등급) + OBSERVATION(인과성·중대성) + EPISODE_EVENT → 치료 에피소드 |
| FAMILY_HISTORY | 환자 × 관계 × 질환 | OBSERVATION(가족력 concept, value = 질환, qualifier = 관계, number = 진단 나이) |
| PATHOLOGY_REPORT, PATHOLOGY_TUMOR, BIOMARKER | 검체 1 · 종양 1 · 검사 × 마커 | K-AI 확장 테이블 그대로 (SPECIMEN 에 연결) |
| 질환 표 13개 | 표별 행 단위 | K-AI 확장 테이블 그대로 |

구체적인 레코드 예시는 `crf_to_omop_examples.md` 에 있습니다. 변환기가 규칙을 실제로 적용해 만든 결과라 규칙과 예시가 어긋날 수 없습니다.

## 파일

| 파일 | 내용 |
|---|---|
| `kai_cdm_spec_v2.yaml` | 저장 테이블 30개(OMOP 14 + 확장 16)와 컬럼 |
| `crf_forms_v2.yaml` | 서식 24개와 필드별 `target`(어느 테이블의 어느 컬럼·레코드가 되는지) |
| `crf_to_omop_examples.md` | 폐암 환자 한 명의 서식 8장 → 레코드 |
| `vocab/CONCEPT.csv` | K-AI 어휘. concept_id, 한글·영문 이름, domain, vocabulary, class, concept_code(표준 코드), standard_concept, 표준 매핑 후보, 유효 기간 |
| `vocab/VOCABULARY.csv` | 원천 어휘와 라이선스 |
| `vocab/CONCEPT_RELATIONSHIP.csv` | 값 → 값 집합 `Is a`, 표준 코드 보유 concept 의 `Maps to` |
| `vocab/CONCEPT_SET.csv`, `CONCEPT_SET_ITEM.csv` | 값 집합(옛 코드표)과 소속 concept. 검증기는 "값이 집합 안에 있는가"를 본다 |
| `vocab/concept_registry.json` | key → concept_id 등록부. 재생성해도 ID 가 바뀌지 않는다. **삭제 금지** |
| `derived_v2.yaml` | 코어에서 파생하는 변수 120개(입력 항목 아님)와 파생 점수 29개 |
| `legacy_fields_v2.yaml` | v1 필드 중 서식 항목과 합쳐지지 않은 575개 (승격·폐기 검토용) |
| `dictionary_v2.xlsx` | 팀 배포용 사전: 저장테이블, 저장컬럼, 서식, CONCEPT, CONCEPT_SET, 파생변수, v1 미승격 필드 |
| `spec_v2_report.md` | 통계, 비어 있는 값 집합, 경고 |

## 만들기

원천은 1단계 배치표(`internal/decisions/배치표_v0_YYYYMMDD.xlsx`, 비공개), `spec/v2_field_names.py`(항목 → 영문 필드명·단위·코드표·타입), `spec/v2_omop_map.py`(OMOP 테이블 정의, 어휘 씨앗, 서식→레코드 규칙)입니다.

```bash
uv run --with openpyxl --with pyyaml python spec/build_spec_v2.py [배치표.xlsx] [--out spec/v2]
```

## 다음 단계 (2.1)

- 비어 있는 값 집합의 값 채우기, 값마다 SNOMED/LOINC 코드를 용어 서버로 확인해 `concept_code` 에 기록.
- 열린 표준 코드(수술명·레지멘·MedDRA 용어·약제)의 참조표를 어휘에 적재.
- 파생 변수의 concept set(과거력 진단 목록, 약물 계열 목록) 채우기.
- v1 미승격 필드 575개 중 승격할 것 고르기.
- 3단계: 규칙 생성기·가상데이터·엔진·앱을 v2 로 전환. 앱에 서식→레코드 변환 단계를 추가.
