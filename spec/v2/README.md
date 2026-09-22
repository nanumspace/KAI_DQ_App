# 사전 v2 · OMOP 구조 + K-AI 어휘

전문가 자문(필수항목 조사)과 v1 사전을 합쳐 재설계한 데이터 모델입니다. **앱 v0.2.0 부터 기본 명세**이며(`meta.version: 2.0.0`), v1(`spec/kai_cdm_spec.yaml`)은 옛 제출본을 다시 볼 때만 씁니다.

이 폴더의 파일은 모두 `spec/build_spec_v2.py` 가 만듭니다(README 제외). 손으로 고치지 말고 원천(배치표·`spec/v2_*.py`)을 고친 뒤 다시 만듭니다. 등록부(`vocab/concept_registry.json`)를 두고 다시 만들면 바이트까지 같은 결과가 나옵니다.

**아직 열려 있는 것**(모델은 쓰되 답이 오면 고칠 자리): 병리 보고서 컬럼 10개의 조건부 필수(`spec/v2_row_kinds.py` `NEEDS_REVIEW`), SNOMED 미매핑 값 132건(사유는 `spec/v2_codelists_v21.py` 주석), 실데이터 파일럿 결과.

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
- **SNOMED CT**: snowstorm 용어 서버(MCP, `snomedct`/`MAIN`)에서 항목을 검색해 FSN·활성 여부를 눈으로 확인한 코드만 `SNOMED_CODES` 에 넣었습니다. `(코드표, 코드) → concept_id` 를 넣으면 그 값의 `vocabulary_id` 가 KAI → SNOMED 로 승격됩니다. 현재 **155개**(과거력 진단 20종 + 값 집합 135개)이며, 척도 8종과 참조표까지 합쳐 SNOMED 코드를 가진 concept 은 176개입니다(`spec_v2_report.md`).
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

## 2.3 · 표준 용어 확대 (2026-09-22)

CONCEPT 1,107개 중 `vocabulary_id = KAI` 가 892개였습니다. 값 하나하나를 snowstorm(MAIN 2026-09)과 로컬 LOINC 2.80 에서 대조해 **149개를 표준으로 올렸습니다** — SNOMED 176 → 277, LOINC 11 → 59, KAI 892 → 743.

배치표에서 온 코드표(병기군·ECOG·CKD 병기·예/아니오 …)는 2.1 의 `SNOMED_CODES` 가 닿지 않아 전부 KAI 로 남아 있던 것이 컸습니다. 이제 생성기가 모든 코드표에 `SNOMED_CODES` 를 적용하고, 서식 필드 개념에도 `SNOMED_FIELD_CODES`(observable entity)를 붙입니다.

**올린 것**

| 코드표 | SNOMED | 비고 |
|---|---|---|
| STAGE_GROUP_AJCC8 (15) | AJCC 병기군 한정자 (`1222724007` IA …) | clinical·pathological·yp 부모를 함께 가져 c/p 를 가리지 않는다 → 1:1 |
| STAGE_CONTEXT c/p/yc/yp/r | AJCC 접두 한정자 | |
| STAGE_EDITION 7·8, STAGE_SYSTEM Ann Arbor | tumor staging 체계 개념 | Lugano·FIGO 체계 개념은 없음 |
| ECOG 0~5 | finding | 필드에는 observable 423740007 |
| CHILD_PUGH A/B/C, RESPONSE CR/PR/SD | finding | PD·NE 는 대응 없음 |
| CKD_STAGE G1~G5, DR_SEVERITY, DM_TYPE, LYMPHOMA_SUBTYPE 8종 | disorder | CLL/SLL 은 disorder 층에 합친 개념이 없어 KAI |
| SMOKING_STATUS, FAMILY_RELATION 7종, YN 예/아니오/모름 | finding · person · qualifier | |
| BIOMARKER_METHOD NGS·PCR·FISH·IHC·FLOW·KARYOTYPE | technique (qualifier value) | RT-PCR·Sanger·array 는 기법 층에 개념 없음 |
| 수술·방사선·항암 의도 (근치·고식·진단·예방·보조·선행) | intent (qualifier value) | 재건·이식·유지·구제는 의도 개념이 아님 |
| AJCC R 분류 R0/R1/R2/RX (절제연 두 코드표) | qualifier value | 2.1 에서 KAI 로 뒀던 것을 AJCC 한정자 가족에서 찾음 |
| SCT_TYPE 자가·제대혈, SURG_APPROACH 개복 | procedure · access | 동종 3종은 한 개념으로 뭉치고, 복강경·로봇 등은 접근 한정자가 없음 |

서식 필드 48개에 LOINC 를 붙였습니다 — 림프절 개수 4종, 초경·폐경 나이, 출산 수, FIB-4, ELF, 실혈량, 림프종 IHC 마커 12종(CD3~PAX5, BCL2·BCL6·MYC·cyclin D1·SOX11·EBER), 재배열·전좌 5종, 세포기원, ctDNA, 침윤 4종(림프관·혈관·림프혈관·신경주위), 잔존종양 분류, 조직 등급, 원발·전이·재발 부위, 재발일, 임상 병기군, 방사선 총선량, PAM50 ROR, 당뇨 가족력. 우리 필드가 LOINC 보다 넓거나(ALK 발현 '또는' 재배열, TP53 변이 '또는' 17p 결실, IG/TCR 클론성, MRD 방법 불문) 좁은 것(Child-Pugh 등급 vs 총점)은 붙이지 않았습니다.

**남은 KAI 743개의 얼굴**

| 종류 | 수 | 왜 KAI 인가 |
|---|---|---|
| 값 집합 자체·씨앗(Type·Episode·Field·Cohort·Visit·Relationship) | 127 | 우리 모델의 구조 개념. 표준으로 바꿀 대상이 아닙니다 |
| 서식 필드 개념(Attribute) | 309 | "이 필드가 무엇인가"를 가리키는 개념. LOINC·observable 이 있는 것만 올렸고, 나머지(병기 수식자·장루 이유·MRI 소견 …)는 표준에 대응 개념이 없습니다 |
| 값(Value) | 307 | 아래 셋 |
| ↳ 설계상 KAI | 30 | TNM T/N/M. SNOMED 는 cT1·pT1 처럼 접두를 값에 붙이는데 우리는 STAGE_CONTEXT 로 따로 받습니다 |
| ↳ 출판 척도인데 SNOMED 에 값 개념이 없음 | ~150 | RECIST 기준·BI-RADS·Deauville·CTCAE·METAVIR·Wagner·NAS·Borrmann·ITBCC·mrTRG·VPI·ICH E2B(조치·결과·인과성·중대성)·IPI 위험군·Lugano 병기·수식자 |
| ↳ 대응 개념이 없거나 뜻이 어긋남 | ~120 | 2.1 에서 사유를 적은 132건 + 이번에 확인한 것(RT-PCR·Sanger·복강경·동종 3종·CLL/SLL·PD/NE·FIGO·Lugano 체계 …) |

즉 남은 것은 대부분 **표준에 자리가 없는 것**이지 매핑을 안 한 것이 아닙니다. 사유는 `spec/v2_codelists_v21.py` 의 해당 줄 주석에 있습니다.

**사전 xlsx 의 '저장컬럼' 시트**도 같은 날 채웠습니다. OMOP 14개 표 128개 컬럼에 한글 이름·설명·참조를 새로 적었고(`spec/v2_omop_columns_ko.py`), 확장 표 컬럼은 서식 필드가 가진 것(값 집합의 값 예시·단위·조건부 필수 조건·자문 등급)으로 설명을 지었습니다. 배치표의 '메모'는 설명이 아니라 설계 메모라 '비고' 열로 옮겼습니다. 한글·설명 100%, 참조는 키 컬럼 55개, 값 집합은 값이 정해진 컬럼 202개에 있습니다.

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

배치표가 옮기라고 한 v1 컬럼 575개 중 어떤 v2 항목도 `현 명세 대응 필드`로 지목하지 않은 것이 미승격으로 남습니다. **"v2 에서 빠진 항목"이 아니라 "연결 고리가 안 적힌 항목"** 입니다. `spec/v2_legacy_triage.py` 가 나누고, 2026-09-21 에 232개를 하나하나 v2 와 대조해 결과를 그 파일에 적었습니다(`RESOLVED`·`DROPPED`·`PENDING`).

| 묶음 | 수 | 뜻 |
|---|---|---|
| 키·외래키 | 4 | 데이터 항목이 아닙니다 |
| 코드·명칭 쌍의 명칭쪽 | 129 | v1 은 코드·명칭 두 컬럼, v2 는 `concept_id` 하나 — 구조가 흡수했습니다 |
| v2 에 이미 대응 있음 | 198 | 낱말 겹침으로 찾은 것. 서식·파생변수·값집합에 같은 뜻이 있습니다 |
| 대응 확인(검토 완료) | 234 | 어림이 놓쳤으나 사람이 대조해 v2 자리를 적었습니다 |
| 제외(사유 기록) | 10 | v2 에 두지 않기로 한 것 — `file_id`(영상 파일 참조, 4개 코호트: 코호트 DB 는 영상 파일을 담지 않는다), 레코드 생성 일시, 기록지 출처, 병리 판독일 3종, 타병원 전원 여부 |
| 부분 일치 | 0 | |
| 대응 없음 | 0 | |

어림 분류가 232개를 놓친 이유는 둘입니다. **OMOP 코어 컬럼**(처방일·투여경로·단위·퇴원일·진단코드…)은 서식 필드가 아니라 비교 대상에 없었고, **영문 표기**(Residual Tumor, Gross type)가 한글 라벨과 어긋났습니다. 대조 결과 232개 중 임상 판단이 필요한 것은 없었습니다 — 모두 OMOP 코어 컬럼, 서식 필드, 파생 변수 중 하나에 이미 자리가 있었습니다. 목록은 `legacy_fields_v2.yaml` 의 `triage` 와 사전의 **`v1 미승격 분류`** 시트에 있습니다.

### 행 종류(조건부 필수)

`PATHOLOGY_REPORT` 는 생검 병리와 수술 병리를 **같은 표에 각각 한 행**으로 받습니다(서식의 행 단위가 '검체(보고서) 1'). 그래서 생검 행에 수술 컬럼이 비어 있는 것이 정상인데, 배치표의 '필수'를 행마다 NULL 금지로 바꾸면 어느 쪽이든 반드시 어깁니다.

그래서 표에 **행 종류 컬럼**(`report_type_concept_id`, 값 집합 `CL_PATHOLOGY_REPORT_TYPE`)을 두고, 필수를 그 종류에 걸린 조건부로 만들었습니다. 분류는 `spec/v2_row_kinds.py` 한 파일에 있고, 빌드가 컬럼에 `applies_when` 을 붙이면 규칙 생성기가 `not_null_when` 규칙(현재 41개)으로 바꿉니다. 필수인데 종류를 정하지 않은 컬럼이 있으면 빌드가 경고합니다.

두 가지를 함께 손봤습니다.

- **열린 표준 코드**(MedDRA·SNOMED 참조표를 가리키는 `*_concept_id`)는 병원이 참조표를 싣기 전에는 채울 수 없습니다. 그래서 `concept_id` 를 곧바로 요구하지 않고 **코드나 원천값 중 하나는 반드시 남기도록**(`not_null_either` 7개) 바꿨습니다.
- **값 집합이 아직 비어 있는 컬럼**은 채울 근거가 없으므로 필수를 오류가 아니라 경고로 냅니다. 값 집합을 채우면 오류로 올라갑니다.

**당시 남았던 1건** — `adenocarcinoma_predominant_subtype` 은 수술 병리에서 보지만 **선암일 때만** 해당해, 필수 여부가 행 종류가 아니라 조직형에 걸렸습니다. 조건을 여러 종류로 넓혀(아래 '6개 코호트 전환 완료'의 `_contains`) 풀었습니다. 지금은 깨끗한 가상데이터에서 위반 0 입니다.

`spec/v2_row_kinds.py` 의 `NEEDS_REVIEW` 에는 코어 생검에서도 볼 수 있어 일단 가장 엄격한 BOTH 로 둔 10개 컬럼(림프관·혈관 침윤, DCIS 핵등급, TIL 등)이 있습니다. 임상 검토로 고칠 자리는 그 파일 하나입니다.

### 의미 규칙 v2

v1 의미 규칙 75개를 그대로 옮길 수 없었습니다. v1 은 질환마다 큰 테이블 하나를 두고 수술일·생검일을 컬럼으로 갖고 있었지만, v2 는 같은 사실이 OMOP 테이블과 확장 테이블에 나뉘어 앉기 때문입니다. **'무엇을 보는 규칙인가'만 남기고 SQL 은 v2 구조로 다시 썼습니다** — `rules/rules_semantic_v2.yaml` 에 공통 23개, 코호트별 17개, 모두 40개.

| 묶음 | 수 | 내용 |
|---|---|---|
| 공통 · 시간 순서 | 8 | 방문 기간, 사망·관찰기간 밖 사건, 방문-사건 환자 일치, 입원 중첩 |
| 공통 · 값의 정합 | 6 | 약물 기간과 days_supply, 검사 결과값·참고범위·타당 범위, BMI 계산 |
| 치료 묶음(EPISODE) | 5 | 에피소드 기간, 매단 사건의 실재·환자 일치, 레지멘 기간과 약물 기간, 진단일 <= 첫 치료일 |
| 검체와 병리 | 4 | 검체일 일치, 림프절 수 정합, 수술 병리의 대응 시술, 종양 크기 정합 |
| 폐암 | 3 | 검사일 >= 검체일, 영상·병리 크기 정합, 흡연 기록 논리 |
| 유방암 | 3 | 생식 기록이 있는 환자는 여성, 폐경·출산 기록의 앞뒤 |
| 대장암 | 2 | 직장 MRI 거리 순서, 개복 전환과 사유의 맞물림 |
| MASLD | 2 | FIB-4 재계산, 심장대사 위험인자 1개 이상 |
| 당뇨병 | 2 | 해마다 HbA1c, 혈당강하제는 진단 뒤에 |
| 림프종 | 5 | B 증상 논리, IPI 와 위험군, 전환일 >= 진단일, CAR-T 날짜 순서, double-hit 판정 |

코호트별 규칙은 코호트를 옮길 때 함께 썼습니다. v1 에 있었으나 아직 옮기지 않은 것은 코호트 구성 조건·인구학적 분포입니다(v2 는 `COHORT` 테이블이 따로 있어 기준부터 정해야 합니다). v1 의 당뇨 규칙 중 넷은 특화 테이블이 코어의 평면화 사본인지 보는 것이라 v2 에서는 뜻이 없어 옮기지 않았습니다.

**코호트별 규칙이 가상데이터의 결함 여섯을 잡았습니다.** 모두 제가 값을 따로따로 뽑아 앞뒤가 어긋난 것들입니다 — FIB-4 를 기록한 검사값이 아닌 새 난수로 계산한 것, 개복 전환 여부와 사유를 따로 뽑은 것, IPI 점수와 위험군을 따로 정한 것, MASLD 인데 심장대사 위험인자가 하나도 없는 환자, B 증상이 있다면서 세부 증상이 다 없는 환자, 항문연 거리가 항문직장경계부보다 가까운 MRI 입니다.

**규칙을 돌려 보며 찾은 것**

- **`EPISODE_EVENT` 는 `episode_event_field_concept_id` 로 갈라 봐야 합니다.** 테이블마다 id 가 따로 매겨져 약물 100001 과 진단 100001 이 동시에 존재하므로, field concept 을 무시하고 id 로만 이으면 엉뚱한 행이 붙습니다. 처음 쓴 규칙이 이걸 놓쳐 91건의 가짜 위반을 냈고, field concept 으로 갈라 조인하도록 고쳤습니다.
- **검사 행의 '값'에는 원천값도 포함해야 합니다.** 병기·반응처럼 원천 표기만 남기는 항목이 있어, 수치·값 concept 만 보면 정상 데이터를 위반으로 잡습니다.
- 가상데이터 쪽 결함 둘도 이 규칙들이 잡았습니다 — 수술 병리의 검체일에 보고일을 넣은 것, 병리 종양 크기를 영상과 무관하게 뽑은 것.

**검사항목 타당 범위**는 v2 명세에 범위 정보가 없어 v1 의 `spec/concepts.yaml` 범위표를 빌려 씁니다. OMOP 검사 concept_id 는 v1·v2 가 같아 그대로 맞습니다.

### 오류 주입과 검출 평가 (v2)

규칙이 있다고 오류를 잡는다는 뜻은 아닙니다. 그래서 일부러 오류를 심고 규칙이 그것을 잡는지 잽니다.

v1 의 주입기는 오류를 하나하나 손으로 적었습니다. v2 는 구조 규칙이 1,038개(폐암에 적용되는 것만 340여 개)라 그 방식으로는 규칙과 주입이 금방 어긋납니다. 그래서 **규칙에서 거꾸로 오류를 만듭니다** — 규칙이 무엇을 금지하는지 읽고 바로 그것을 어기는 값을 넣습니다(`synth/inject_faults_v2.py`). 규칙을 늘리면 주입도 따라 늘고, 정답(`expected_rules`)이 어긋날 일이 없습니다. 여러 테이블이 얽히는 의미 규칙만 손으로 적었습니다.

```bash
python dq/run_all.py --spec v2          # 생성 → 검증 → 오류 주입 → 검증 → 검출 평가
```

폐암 기준 **오류 116건을 심어 116건 모두 검출(재현율 1.0)**, 깨끗한 데이터에서는 위반 0 입니다.

**평가를 돌려 찾은 것**은 모두 주입기 쪽 결함이었고, 규칙은 처음부터 제대로 울리고 있었습니다.

- 방문 종료일을 시작일과 **같게** 넣어 규칙(`<`)에 걸리지 않았습니다. 하루 앞으로 보내야 합니다.
- `COHORT` 처럼 환자 컬럼 이름이 `person_id` 가 아닌(`subject_id`) 표에서 정답을 맞추지 못했습니다.
- 심는 컬럼이 **복합 PK 의 일부**이면(`COHORT.cohort_start_date`) 주입 전 PK 로 적어 둬서, 엔진이 내는 `row_key` 와 달라 정답이 맞지 않았습니다. 값을 먼저 넣고 기록하도록 고쳤습니다.

### 서식 → 레코드 변환

v2 에서 병원이 채우는 것은 저장 테이블이 아니라 **서식**입니다. 한 서식의 한 행이 여러 저장 테이블의 여러 레코드가 됩니다. 그 변환기가 `dq-ts/src/crf.ts` 이고, 앱은 `crf:convert` 로 부릅니다.

**변환 규칙을 코드에 옮겨 적지 않았습니다.** 명세가 바뀌면 변환도 따라 바뀌어야 하므로, `crf_forms_v2.yaml` 에 실린 규칙을 그대로 읽어 씁니다. 그러려면 빌드가 규칙을 기계가 읽을 수 있게 내보내야 해서, 서식마다 `mapping`(사건 날짜 필드, 먼저 만들 레코드 `anchors`, 연결 `links`)을 새로 싣습니다. 필드별 `target` 은 전부터 실려 있었습니다.

서식은 두 종류이고 변환이 다릅니다.

| 종류 | 변환 |
|---|---|
| 확장 저장 (16개) | 서식 하나가 확장 테이블 하나. 필드가 그대로 컬럼이 됩니다. `*_concept_id` 컬럼에는 값 집합 코드를 concept_id 로 바꿔 넣고, 사람이 고른 코드는 언제나 `*_source_value` 에 남깁니다 |
| OMOP 투영 (8개) | 한 행이 여러 테이블로 흩어집니다. `anchors` 로 기준 레코드(COHORT·CONDITION·EPISODE…)를 먼저 만들고, 나머지 필드는 `target` 이 가리키는 자리(MEASUREMENT·OBSERVATION·EPISODE)에 앉힙니다 |

**확장 저장 서식은 왕복으로 확인합니다**(`dq-ts/test/crf.test.ts`). 생성된 저장 CSV 에서 concept_id 를 코드로 되돌려 서식을 만들고, 그 서식을 다시 변환해 원래 값이 나오는지 봅니다. 코드↔concept_id 짝이 어긋나면 여기서 걸립니다. OMOP 투영은 되돌릴 수 없어 만들어진 레코드의 모양만 봅니다.

이 과정에서 **행 종류 컬럼이 서식에 없다는 것**이 드러났습니다. `report_type_concept_id` 를 저장 컬럼으로만 만들어 두어 병원이 채울 길이 없었습니다. 서식에도 필드로 넣어 사람이 고르게 했습니다.

### 서식은 EHR 을 대신하지 않는다

전 구간을 돌려 보고 알게 된 것이 있습니다. **6개 표는 어느 서식도 만들지 않습니다** — `PERSON`·`VISIT_OCCURRENCE`·`DRUG_EXPOSURE`·`DEATH`·`NOTE`·`SPECIMEN`.

서식은 EHR 에 구조화되어 있지 않은 것(병리 소견, 병기, 바이오마커…)을 받는 자리입니다. 환자·방문·약물처럼 EHR 에서 그대로 뽑는 표는 **추출본으로 따로** 받아야 하고, 검증할 때 변환 결과와 합쳐야 합니다. 모르고 넘어가면 검증에서 '테이블 없음'만 잔뜩 나옵니다.

그래서 변환기가 `tablesFromEhr` 로 그 목록을 돌려주고, 앱의 **서식 변환** 화면이 그 사실을 먼저 알립니다.

전 구간 확인은 이렇게 했습니다 — 생성된 저장 데이터를 되돌려 서식 12개(601행)를 만들고, 투영 서식 2개를 사람이 채우는 모양으로 더해, 변환한 뒤 엔진에 넣었습니다. 남은 위반은 변환하지 않은 서식 때문에 비는 표뿐입니다.

**이 과정에서 두 가지를 고쳤습니다.**

- 변환기가 **값이 있는 컬럼만 쓰고 있었습니다.** 명세의 컬럼을 다 갖춰야 '컬럼 구성' 검사를 지나므로, 빈 칸이라도 모두 씁니다.
- 의미 규칙 6개의 **`requires` 가 SQL 이 쓰는 표를 다 적지 않았습니다.** 표가 없으면 건너뛰어야 하는데 SQL 이 실행돼 오류가 났습니다. 당시 26개를 전부 감사해 맞췄고, 이후 더한 규칙도 같은 검사를 거칩니다.

### 6개 코호트 전환 완료

폐암에 이어 당뇨·MASLD·대장암·림프종·유방암을 v2 로 옮겼습니다. 여정은 v1 과 같고 적는 자리만 바뀝니다.

```
코호트              깨끗한 데이터   주입 오류    검출   재현율
LUNG_CANCER            0 위반        116건      116    1.0
DIABETES               0 위반         83건       83    1.0
MASLD                  0 위반         95건       95    1.0
COLORECTAL_CANCER      0 위반        106건      106    1.0
LYMPHOMA               0 위반        100건      100    1.0
BREAST_CANCER          0 위반        101건      101    1.0
```
(2026-09-16 · `python dq/run_all.py --spec v2`. 환자 2,000명 규모에서도 6개 모두 위반 0.)


**조건부 필수를 넓혔습니다.** 코호트를 옮기면서 '필수 여부가 행 종류가 아니라 다른 조건에 걸리는' 항목이 계속 나왔습니다 — 폐선암 우세 아형은 조직형이 선암일 때만, 직장 MRI 의 mrTRG 는 선행치료 뒤 재평가일 때만, 림프종의 이식일·CAR-T 주입일은 그 일이 실제로 있었을 때만 해당합니다. 그래서 `applies_when` 에 조건 세 가지를 둡니다.

| 조건 | 뜻 | 쓰는 곳 |
|---|---|---|
| `{컬럼: 코드}` | 그 컬럼이 그 코드일 때 | 행 종류(생검/수술 병리) |
| `_filled: 컬럼` | 그 컬럼이 채워져 있을 때 | 재평가 MRI 의 mrTRG |
| `_contains: [컬럼, 글자]` | 그 컬럼 값에 그 글자가 들어 있을 때 | 선암일 때만 매기는 우세 아형 |
| `_equals: [컬럼, 값]` | 그 컬럼이 그 값일 때 | 이식·CAR-T 를 했을 때만 있는 날짜 |

조건은 `spec/v2_row_kinds.py` 한 파일에 적고, 빌드·규칙 생성기·두 엔진·오류 주입기가 모두 그것을 따릅니다.

**빈 값 집합 3종을 채웠습니다.** `TUMOR_SITE`·`BIOMARKER_METHOD`·`LYMPHOMA_SUBTYPE` 은 저장 컬럼이 가리키는데 만들어지지 않아 빌드 경고로 남아 있던 것입니다. 이제 **빌드 경고 0** 입니다.

**코호트를 옮기며 찾은 결함들**

- **미래 날짜 규칙이 과했습니다.** 오늘 90일치를 처방하면 종료일은 당연히 미래인데 모든 날짜를 막고 있었습니다. 이미 일어난 일을 적는 날짜만 막고, 진행 중인 것의 종료 예정일은 허용합니다(퇴원일은 예외로 계속 막습니다).
- **염기서열·변이 표기가 `float` 로 선언돼 있었습니다.** `reference_sequence`("GRCh38")와 HGVS 표기는 글자입니다. 배치표에서 수치로 잡힌 것을 바로잡았습니다.
- **오류 주입기가 한 행에 둘을 심고 있었습니다.** 참조를 끊어 놓으면 그 행의 날짜 불일치는 JOIN 이 안 돼 드러나지 않아 '못 잡았다'로 보입니다. 이제 행을 겹치지 않게 고르고, 자리가 모자라면 덜 심습니다.
- **위반이 0일 때 파이썬 엔진이 머리글조차 쓰지 않았습니다.** 컬럼 없는 CSV 가 되어 읽는 쪽이 형식 오류로 봅니다. 깨끗한 실행이 처음으로 위반 0이 되면서 드러났고, TypeScript 동등성 시험이 잡았습니다.

## 전환 기록과 남은 일

- **3단계 (진행 중): v1 과 병행하며 v2 경로를 만든다.** 병원이 쓰던 v1 을 끊지 않고 둘을 견주어 보기 위해서다. v2 가 안정되면 v1 을 재단한다.
  - ✅ 규칙 생성기: `python rules/generate_structural_rules.py --spec v2` → `rules/rules_structural_v2.yaml` (1,038개)
  - ✅ 가상데이터: **6개 코호트 전부** 옮겼다 — `python synth/generate.py --spec v2 --all`
    - `synth/framework_v2.py` 가 v2 저장 테이블에 적고, `scenarios/lung_v2.py` 가 여정을 기술한다. 여정 자체는 v1 과 같다.
    - 명세에 없는 컬럼을 쓰거나 값 집합에 없는 코드를 쓰면 생성이 그 자리에서 멈춘다.
    - 6개 코호트 모두 깨끗한 데이터에서 **위반 0**, 오류를 심으면 **재현율 1.0**.
  - ✅ 엔진: `python dq/engine.py --spec v2 --cohort LUNG_CANCER --data synth/output/clean_v2/LUNG_CANCER --out dq/reports/v2_LUNG_CANCER`
    - v2 명세·프로필·값 집합을 읽고, v2 전용 검사 5종(`concept_set`·`concept_code`·`not_null_when`·`not_null_either`·복합 PK)을 더했다.
    - 6개 코호트 전부 깨끗한 데이터에서 **위반 0**. v1 경로는 규칙 427개·위반 0으로 그대로다.
    - 의미 규칙은 `rules/rules_semantic_v2.yaml` 에 **40개**(공통 23 · 코호트별 17)를 새로 썼다. 코호트가 실제로 도는 규칙 수는 341~531개다.
    - TypeScript 엔진도 `--spec v2` 로 같은 규칙을 돌린다: `npm run engine -- --spec v2 --cohort LUNG_CANCER --data ... --out ...`
      **6개 코호트 전부** clean·dirty 두 실행에서 위반 행까지 완전히 같다(`dq-ts/test/equivalence.test.ts`, 시험 26개).
  - ✅ 오류 주입·검출 평가: `python dq/run_all.py --spec v2` 로 생성→검증→주입→검증→평가를 한 번에 돈다.
    - **6개 코호트 전부 오탐 0 · 재현율 1.0** (주입 83~113건/코호트).
  - ✅ 앱: 서식→레코드 변환기(`dq-ts/src/crf.ts`), `crf:convert` IPC, **서식 변환** 화면, 빈 서식 양식 내려받기.
  - ✅ 앱 엔진 v2 전환: 앱의 기본 명세가 **v2** 가 됐다 (설정 → 명세 판에서 v1 도 고를 수 있다).
    - 명세·코호트 프로필·규칙·견본 데이터·입력 양식이 모두 판에 따라 갈린다. 판을 바꾸면 화면이 다시 그려지고, 검증이 도는 중에는 바꿀 수 없다.
    - 사전 점검의 '없으면 못 도는 표'는 v2 에서 PERSON 하나다. v2 에는 질환 본표가 없기 때문이다.
    - `npm run smoke` 로 확인: 폐암 clean 377규칙 위반 0, 당뇨 dirty 341규칙 위반 198, 폐암 dirty 엑셀(시트 18개) 위반 236 — CLI 와 같은 수.
      `KAI_SMOKE_SPEC=v1 npm run smoke` 로 v1 회귀 없음(427규칙 위반 0/172, 392규칙 위반 950).
    - 설치본에도 `spec/v2/` 와 v2 견본을 넣는다. `spec/v2/vocab/ref/`(MedDRA·LOINC 등)는 기관이 자기 라이선스로 받는 것이라 넣지 않는다.
    - 규모: 환자 2,000명 × 6개 코호트에서도 위반 0, 코호트당 3초 안팎, 메모리 1GB 미만 (`app/test/scale.test.ts`).
      100명에서는 안 보이던 시나리오 결함 5건이 이 크기에서 드러나 고쳤다. 사망은 여정 앞에서 정하도록 틀에 걸쇠를 달았다(`framework_v2.set_death`).
    - 검증 실행 화면이 **폴더 여러 개**를 받는다. v2 는 서식을 바꾼 폴더와 EHR 추출본 폴더가 따로 오기 때문이다.
      그 둘을 담은 상위 폴더 하나만 넣어도 바로 아래 폴더까지 찾고, 같은 이름의 파일이 겹치면 어느 것을 쓰는지 사전 점검이 알려 준다.
  - ✅ 파일럿 준비 (2026-09-16): 실데이터 흉내 입력 18종과 입력 정규화(`app/test/realworld.test.ts`), 규모 시험 2,000명×6 위반 0,
    보고서 예시의 값 가리기, 같은 이름의 표 합쳐 읽기(서식 변환 ID 는 9,000,000,000부터), 병원용 자료 v2 전환(설명서·README·Pages·견본 zip),
    파일럿 키트(`pilot/`: 안내서·피드백 양식·중앙 집계 도구·임상 검토 표 2종), v0.2.0 unsigned 빌드.
  - ⬜ 파일럿: 실제 병원 데이터. 규칙이 실데이터에서 어떻게 우는지는 여기서 처음 안다.
  - ⬜ Windows 11 실기 확인, 서명 릴리스(USB 토큰), 임상 검토 회신 반영(`NEEDS_REVIEW` 10건, 미승격 필드), v1 재단.
