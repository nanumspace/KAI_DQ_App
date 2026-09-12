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

필요한 외부 패키지는 `spec/requirements.txt` 에 있습니다(openpyxl, PyYAML 둘뿐).

```bash
uv run --with-requirements spec/requirements.txt python spec/build_spec_v2.py [배치표.xlsx] [--out spec/v2]
```

uv 가 없으면 가상환경을 만들어 씁니다.

```bash
python3 -m venv .venv && .venv/bin/pip install -r spec/requirements.txt
.venv/bin/python spec/build_spec_v2.py [배치표.xlsx] [--out spec/v2]
```

## 2.1 · 값 집합 채우기 (완료분)

`spec/v2_codelists_v21.py` 가 값 집합과 표준 매핑의 원천입니다.

- **값 집합 58개**를 임상 표준(AJCC 8판, WHO/ICC, RECIST 1.1, Lugano/Cheson, ITBCC 2016 종양출아, MERCURY mrTRG, EASL-EASD-EASO 2023 MASLD, NASH CRN, ICH E2B 등) 근거로 채웠습니다. 근거는 파일 안 주석에 항목별로 적었습니다.
- **LOINC**: 로컬 파일(`/Users/min/Research/standard_terminology/LOINC/Loinc_2.80/LoincTableCore/LoincTableCore.csv`, 2.80판)에서 직접 확인한 코드만 썼습니다 — HbA1c, 공복/식후/OGTT 혈당, C-peptide, 공복 인슐린, HOMA, 프룩토사민, UACR, GAD 항체, Ki-67, PD-L1(개별 검사값), 그리고 PFT_ITEM(FEV1·FVC·FEV1/FVC·DLCO)·ALCOHOL(AUDIT 총점 등) 두 항목 목록.
- **DRUG_CLASS_SET**(약물 계열 9종)은 WHO ATC 분류로 채웠습니다. ATC 는 안정된 국제 표준이라 용어 서버 확인 없이 적용했습니다.
- **SNOMED CT**: snowstorm 용어 서버(MCP, `snomedct`/`MAIN`)에서 항목을 검색해 FSN·활성 여부를 눈으로 확인한 코드만 `SNOMED_CODES` 에 넣었습니다. `(코드표, 코드) → concept_id` 를 넣으면 그 값의 `vocabulary_id` 가 KAI → SNOMED 로 승격됩니다. 현재 **155개**(과거력 진단 20종 + 값 집합 135개)이며, SNOMED 코드를 가진 concept 은 164개입니다.
- 매핑하지 **않은** 값도 이유를 파일 주석에 적었습니다. 크게 네 갈래입니다. ① 대응 개념이 아예 없음(Borrmann 육안형, ITBCC 종양출아, mrTRG, VPI, NASH CRN, BI-RADS 범주, ICH E2B 조치·결과 — 모두 코드 자체가 출판된 표준이라 교환에 지장이 없습니다), ② 시술 개념만 있고 값 개념이 없음(병기 방법, TME 질, IMA 결찰 수준), ③ 부위별 개념만 있고 일반 개념이 없음(경피적 배액, 복강 세척액 세포검사, 영상유도 생검), ④ 후보가 우리 값보다 넓거나 좁음(NHL B/T 계열, 별거).
- **원칙 하나**: 한 코드표 안에서 값들의 의미 층(finding·procedure·qualifier·disorder)이 섞이면 승격하지 않았습니다. 다만 임상 종양 소견처럼 코드표 자체가 여러 종류의 임상 양상을 모은 것이면 섞이는 것이 값의 성격이므로 예외로 두었습니다.
- 한 코드표 안에서 두 값이 같은 SNOMED 코드로 매핑되면 그 둘을 데이터에서 구분할 수 없으므로, `build_spec_v2.py` 가 이를 경고로 잡습니다.
- 값 293개 기준: 매핑 135, 행정값(기타·해당없음·평가 불가 등) 28, 사유를 적고 남긴 미매핑 132.

## 2.2 · domain 재지정 (완료분)

값의 OMOP `domain_id` 는 그 값이 **무엇인가**에 따라 정해집니다. 그런데 이전에는 코드표 단위로 domain 을 주고 값이 그것을 물려받아서, 폐엽·생검 방법 같은 값까지 코드표의 domain(대개 `Meas Value`)을 달고 있었습니다 — SNOMED 매핑 155개 중 134개가 그랬습니다.

그래서 `SNOMED_CODES` 의 값을 `(concept_id, SNOMED 계층)` 으로 바꾸고, `build_spec_v2.py` 의 `SNOMED_TAG_DOMAIN` 이 계층에서 domain 을 유도하도록 했습니다. 계층을 빠뜨리거나 모르는 값을 쓰면 빌드가 경고합니다.

| SNOMED 계층 | domain | 수 |
|---|---|---|
| body structure | `Spec Anatomic Site` | 49 |
| disorder | `Condition` | 18 |
| situation | `Observation` | 2 |
| qualifier value | `Meas Value` | 19 |
| morphologic abnormality | `Condition` | 19 |
| finding | `Observation` (질환·증상을 가리키면 `Condition`) | 17 |
| procedure · regime/therapy | `Procedure` | 16 |
| cell | `Observation` | 4 |

결과적으로 SNOMED concept 의 domain 은 `Condition` 51, `Spec Anatomic Site` 49, `Observation` 25, `Meas Value` 19, `Procedure` 16 입니다.

판단이 들어간 곳은 세 군데이며, OMOP 어휘(Athena)를 내려받아 적재할 때 대조해 확인할 값입니다.

- **조직형(morphologic abnormality) → `Condition`**: OMOP Oncology 가 조직형을 진단 개념과 함께 쓰는 것에 맞췄습니다.
- **finding 중 질환·증상은 `Condition`**: 불규칙 월경(80182007)·무월경(14302001)·촉지되는 종괴(443607001) 셋입니다. 검체 적정성·혼인 상태처럼 질환이 아닌 상태를 가리키는 finding 은 `Observation` 으로 두었습니다.
- **폐경 상태**는 `Observation` 으로 두었습니다. 생리적 상태이지 질환이 아니라고 보았으나, `Condition` 으로 보는 견해도 있습니다.

## 다음 단계 (2.2)

- **(완료) domain 재지정**: 아래 2.2 절 참고.
- **필드 수준 척도 메타**: BI-RADS 는 범주(0~6) 값 concept 이 없는 대신 척도 concept(1348266008)이 있습니다. 값이 아니라 "이 필드가 무슨 척도인가"를 말하므로 값 집합이 아닌 필드 메타 자리에 붙여야 합니다.
- 열린 표준 코드(수술명·레지멘·MedDRA 용어·약제)의 참조표를 어휘에 적재.
- v1 미승격 필드 575개 중 승격할 것 고르기.
- 3단계: 규칙 생성기·가상데이터·엔진·앱을 v2 로 전환. 앱에 서식→레코드 변환 단계를 추가.
