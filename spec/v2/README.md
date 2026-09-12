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

### 척도(assessment scale) 메타

BI-RADS 처럼 **범주 하나하나를 가리키는 SNOMED 개념은 없는데 "그 필드가 무슨 척도인가"를 가리키는 개념은 있는** 경우가 있습니다. 이런 개념은 값이 아니므로 값 집합의 항목이 아니라 **코드표 자신**에 붙였습니다. 코드표의 상위 concept 이 `concept_class_id=Scale` 로 그 코드를 달고, CRF 서식의 해당 필드에는 `scale:` 항목으로 드러납니다. 범주 값들은 그대로 KAI 코드입니다.

`SNOMED_SCALES`(`spec/v2_codelists_v21.py`)에 8개 코드표, 6종 척도를 넣었습니다 — BI-RADS(1348266008, 영상 판독 분류·유방 밀도 두 곳), ECOG(273437007), Deauville(708895006), CTCAE(711434002), Child-Pugh(3191000175106), 잔존암부담 지수(445050009), AJCC 8판 병기체계(897275008). `<<273249006 |Assessment scales|` 하위에서 확인했습니다.

붙이지 않은 것도 적어둡니다. **Clavien-Dindo 분류**(789278003)는 개념은 있으나 대응하는 코드표가 아직 없고(합병증 "등급" 필드가 없습니다), **Lugano 분류**는 SNOMED 것이 성인 호지킨·소아 호지킨처럼 질환별로 나뉘어 있어 호지킨·비호지킨을 함께 쓰는 `STAGE_LUGANO` 에 붙이면 범위가 좁아집니다. **RECIST·METAVIR·NAS·Wagner·당뇨망막병증 중증도·CKD 병기**는 척도 개념 자체가 없습니다.

코드표 없는 척도를 적어두면 조용히 사라지므로 빌드가 경고로 잡습니다.

### 참조표 등록 (열린 표준 코드)

값이 미리 정해진 필드는 값 집합으로 받지만, 수술명·레지멘·이상사례 용어처럼 값이 수천~수십만 개인 필드(**14개**)는 값을 열거하지 않고 **어느 표준 표를 쓰는가**만 정합니다. 그 등록 내용이 `spec/v2_reference_tables.py` 이고, 생성물은 `spec/v2/vocab/REFERENCE_TABLE.csv` 입니다. 서식에서는 필드의 `reference:` 항목으로 드러납니다.

**표의 내용은 저장소에 넣지 않습니다.** MedDRA·SNOMED 는 재배포가 제한된 라이선스이고, 심평원 마스터는 공개 데이터지만 원본이 수십 MB입니다. 대신 `spec/load_reference_tables.py` 가 각자 받은 로컬 원본을 읽어 `spec/v2/vocab/ref/`(gitignore)에 표를 만듭니다.

```bash
uv run --with-requirements spec/requirements.txt python spec/load_reference_tables.py
KAI_REF_ROOT=/경로/표준용어 python spec/load_reference_tables.py --only REF_MEDDRA_PT
```

원본이 없는 표는 건너뛰고 무엇이 없는지 알려줍니다. 만든 표마다 행 수와 sha256 을 `ref/manifest.json` 에 남겨 어느 판으로 만든 표인지 확인할 수 있습니다.

| 참조표 | 어휘 | 로더 | 비고 |
|---|---|---|---|
| `REF_MEDDRA_PT` | MedDRA 28.0 | ✅ 26,920행 | 이상사례 용어. LLT 가 아니라 PT 수준 |
| `REF_EDI_PROCEDURE` | EDI | ✅ 432,993행 | 수술명·장루복원술명·방사선치료명 |
| `REF_EDI_DRUG` | EDI | ✅ 22,307행 | `DRUG_EXPOSURE.drug_concept_id` |
| `REF_KCD` | KCD 8차 | ✅ 21,299행 | 가족 질환 |
| `REF_LOINC` | LOINC 2.80 | ✅ 104,672행 | 유세포검사 요약 |
| `REF_SNOMED_PROCEDURE/MORPHOLOGY/NEOPLASM/DISORDER` | SNOMED | ECL | 로컬 배포본 대신 용어 서버에서 받습니다 |
| `REF_HGNC_GENE` | HGNC | 미구현 | genenames.org complete set |
| `REF_HEMONC_REGIMEN` | HemOnc | 미구현 | 국내 전용 레지멘은 자체 어휘로 받습니다 |

열린 표준 코드인데 참조표가 등록되지 않은 필드가 있으면 빌드가 경고합니다.

### v1 미승격 필드 분류

배치표가 옮기라고 한 v1 컬럼 575개 중 어떤 v2 항목도 `현 명세 대응 필드`로 지목하지 않은 것이 미승격으로 남습니다. 그런데 **이 수는 실제 누락이 아니라 대부분 기록·연결의 문제**입니다. 575줄을 그대로 내놓으면 검토가 불가능하므로 `spec/v2_legacy_triage.py` 가 다섯으로 나눕니다.

| 묶음 | 수 | 뜻 |
|---|---|---|
| 키·외래키 | 7 | 데이터 항목이 아닙니다 |
| 코드·명칭 쌍의 명칭쪽 | 129 | v1 은 코드·명칭 두 컬럼, v2 는 `concept_id` 하나 — 구조가 흡수했습니다 |
| v2 에 이미 대응 있음 | 207 | 서식·파생변수·값집합에 같은 뜻이 있습니다. 배치표에 대응 필드를 적으면 이 목록에서 빠집니다 |
| 부분 일치 | 149 | 비슷한 것이 있으나 같은지 사람이 봐야 합니다 |
| 대응 없음 | 83 | 실제 승격 후보. 임상 판단이 필요한 것은 이것뿐입니다 |

목록은 `legacy_fields_v2.yaml` 의 `triage` 와 팀 배포용 사전의 **`v1 미승격 분류`** 시트에 있습니다.

분류는 낱말 겹침으로 하는 어림입니다. "수술을 시행한 연월일"과 "수술일"처럼 뜻은 같은데 낱말이 어긋나면 '대응 없음'으로 잘못 떨어지므로, **그 묶음은 승격할 목록이 아니라 사람이 볼 목록**으로 읽어야 합니다. 실제로 83개 안에 `oprt_ymd`(수술일 → `SURGERY.surgery_date`)처럼 이미 있는 것이 섞여 있습니다.

흡연량·흡연기간·금연연도, 과거력 진단 20종처럼 **코어 파생 변수와 값 집합이 받는 항목**은 서식 필드가 아니어서 눈에 띄지 않지만 이미 v2 에 들어와 있습니다. 분류가 파생 변수와 값 라벨까지 함께 보는 이유입니다.

## 다음 단계 (2.2)

- 3단계: 규칙 생성기·가상데이터·엔진·앱을 v2 로 전환. 앱에 서식→레코드 변환 단계를 추가.
