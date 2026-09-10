# 명세와 규칙 카탈로그

## 기계 판독 명세 (`spec/`)

데이터 사전(엑셀 16개 시트)을 `spec/build_spec.py`가 파싱해 필드마다 다음 속성을 부여한 YAML 명세를 만듭니다. 원본 사전 파일은 공개 저장소에 포함되지 않으며, 생성된 명세 YAML이 공개 산출물입니다.

| 속성 | 내용 |
|---|---|
| `type` | integer / float / varchar / text / date / timestamp 로 정규화 |
| `required` | 핵심 테이블은 사전의 '필수' 열, 특화 테이블은 PK와 person_id만 필수 |
| `key`, `ref` | PK / FK와 참조 대상 (예: `VISIT_OCCURRENCE.visit_occurrence_id`) |
| `codelist` | 설명문에서 분리한 코드표 또는 OMOP 허용집합 참조 |
| `group`, `anchor` | 특화 테이블의 이벤트 그룹과 그룹의 기준 날짜 필드 |
| `level` | person(환자 불변) / event / key |
| `range`, `pattern` | 수치 타당 범위, 문자열 정규식 (병기, KCD, LOINC 등) |

| 파일 | 내용 |
|---|---|
| `kai_cdm_spec.yaml` | 16 테이블 · 1,105 필드 명세 |
| `codelists.yaml` | 분리된 코드표 22개 + 공통 코드표 + OMOP 허용집합 |
| `cohort_profiles.yaml` | 코호트별 테이블 구성 |
| `concepts.yaml` | 규칙과 생성기가 공유하는 대표 concept 목록 (OMOP 대표값, 병원 적용 전 Athena 대조 필요) |

### 특화 테이블의 행 단위: 이벤트 그룹

특화 테이블 한 시트에는 유전자검사일, 폐기능검사일, 수술일, 메모일처럼 서로 다른 시점의 필드가 함께 있습니다. 환자당 1행으로는 반복 검사를 담을 수 없고, 방문당 1행은 한 방문의 여러 검사에서 깨집니다.

그래서 날짜 필드(anchor)를 기준으로 필드를 묶은 **이벤트 그룹**을 행 단위로 정했습니다. 한 행은 (person_id, visit_occurrence_id, 그룹) 하나의 이벤트를 담고, 다른 그룹의 필드는 NULL입니다. 흡연력처럼 환자 수준에서 불변인 필드는 같은 환자의 모든 행에서 값이 같아야 합니다. 이 정의에서 "그룹 필드가 있으면 anchor 날짜 필수"(완전성)와 "환자 내 불변"(타당성) 규칙이 자동으로 따라옵니다.

| 특화 테이블 | 그룹 수 | 대표 그룹 (anchor) |
|---|---|---|
| LUNG_CANCER | 21 | gmt(유전자검사), plex(폐기능), bpsy(생검), oprt(수술), sgpt(외과병리), drug, rdt(방사선), rlps(재발), imex, cexm |
| BREAST_CANCER | 22 | obtr(산과력), gmvx(생식세포변이), gnrx(유전자발현), imem(면역조직화학), oprt, sgpt, rdt |
| COLORECTAL_CANCER | 20 | imex(MRI), oprt(44필드), ostm_reop(장루복원), sgpt(35필드), mlem(분자병리) |
| MASLD | 8 | score(FIB-4 등 예후척도), imex, hist(음주·흡연·운동), anth, oprt(간이식) |
| DIABETES | 9 | person, visit, condition, measurement, drug, death (핵심 테이블 파생 뷰) |
| LYMPHOMA | 15 | dx, stage, ihc, mol(FISH), prog(IPI), tx, sct, cart, resp(Deauville), fu |

### 명세에 반영된 주요 정의

- 외래키 이름은 `antp_id`로 통일하고, `antp_therapy_id`는 별칭으로 받아 경고 후 처리합니다.
- 설명문 안에 "1=…, 2=…" 형태로 있던 코드값은 `codelists.yaml`로 분리했습니다. 병원 LOCAL/EDI 코드는 중앙에서 검증할 수 없으므로 코드-명칭 1:1 일관성만 검증합니다.
- DIABETES 특화 테이블은 핵심 테이블의 파생 뷰로 취급해 값 일치를 교차검증합니다.
- OMOP 표준 concept은 최소 허용집합(gender, visit, type concept, 단위)만 `codelists.yaml`의 `omop` 절에 두고, 병원은 설정으로 확장할 수 있습니다. 전체 OMOP vocabulary 검증은 병원 DB에서 OHDSI DataQualityDashboard로 수행합니다.
- index date는 코호트 정의 진단의 최초 condition_start_date이며, `age_at_index`는 이 날짜 기준 만 나이입니다.
- 날짜는 ISO 8601(YYYY-MM-DD), 타임스탬프는 YYYY-MM-DD HH:MM:SS, CSV는 UTF-8·헤더 포함·NULL은 빈 문자열입니다.
- 수치 범위와 문자열 패턴은 임상 상식 범위(BMI 10~70, ECOG 0~5, Deauville 1~5, 방사선 1회 선량 0~30 Gy 등)이며 파일럿 병원 집계로 보정합니다.

## 규칙 카탈로그 (`rules/`)

규칙은 OHDSI DataQualityDashboard와 같은 **Kahn 프레임워크** 세 축(Conformance 적합성, Completeness 완전성, Plausibility 타당성)으로 분류하고, 심각도 error(적재 거부 수준)와 warning(검토 필요)을 둡니다.

### 구조 규칙 1,121개 (명세에서 자동 생성)

`rules/generate_structural_rules.py`가 명세에서 생성하므로 사전이 바뀌면 다시 생성하면 됩니다.

| 검사 유형 | 규칙 수 | 내용 |
|---|---|---|
| type | 478 | integer / float / date(YYYY-MM-DD) / timestamp 형식 |
| range | 139 | BMI 10~70, ECOG 0~5, Deauville 1~5, 방사선 1회 선량 0~30 Gy 등 |
| not_future | 136 | 검증 실행일 이후 날짜 금지 |
| group_anchor | 86 | 그룹 필드가 있으면 anchor 날짜 필수 |
| codelist | 73 | 코드표 / OMOP 허용집합 (OMOP은 병원 설정으로 확장 가능하므로 warning) |
| fk | 72 | 참조무결성 (참조 테이블이 코호트에 없으면 건너뜀) |
| not_null | 45 | 필수 필드 |
| pattern | 32 | TNM 병기 `^(y?p?)T(is|0|X|1[abc]?…)$`, KCD, LOINC, ECOG 등 |
| table_present, columns, pk_unique | 48 | 테이블 존재, 컬럼 구성(별칭 antp_therapy_id 수용), PK 유일성 |
| must_be_null | 8 | 비항암 코호트에서 antp_id는 NULL |
| person_invariant | 5 | 환자 수준 필드는 환자 내 동일 |

### 교차 테이블 규칙 75개 (수동 작성, `rules_semantic.yaml`)

DuckDB SQL로 작성되어 있어 병원 DBMS로 옮기기 쉽습니다. 각 규칙은 위반 행(person_id, row_key, detail)을 반환합니다. 치환자(`{COHORT_CONDITION_IDS}`, `{DISEASE}`, `{DISEASE_PK}` 등)로 코호트별로 실행됩니다.

| 그룹 | 수 | 예 |
|---|---|---|
| 공통 SEM-COM | 30 | 방문 종료일 ≥ 시작일, 사망 이후 이벤트 금지, 이벤트-방문 환자 일치, 이벤트일이 방문 기간 안, 약물 종료일 = 시작일 + days_supply − 1, 검사 결과값 존재, 검사항목별 타당 범위, age_at_index 재계산, 코호트 포함 조건, 이상사례 ≥ 항암 시작일, 중대 AE 논리, line 번호 연속, 항암 시작일 = 연결 약물 최소 시작일, 진단일 ≤ 첫 항암, 중복 레코드, 성비·나이 분포, 단위 일관성, 입원 중첩, 특화 테이블 death_date = PERSON |
| 암 공통 SEM-CA | 8 | 외과병리일은 수술 후 60일 이내, TNM 조합 일치, 방사선 총선량 = 1회 선량 × 횟수, BMI 재계산, 재발일 > 수술일, KCD 비율 ≥ 90%, 양성 림프절 ≤ 절제 림프절, 판독일 ≥ 검사일 |
| 폐암 SEM-LC | 5 | Stage IV 진단일, 흡연력 논리, 종양 크기 vs T 병기, 유전자검사 ≥ 생검, 조직형 일관성 |
| 유방암 SEM-BC | 5 | 산과 필드는 여성, 폐경 논리, 임신·출산 조건부 논리, 감시림프절 수, 월경 재개일 > 세포독성 항암 종료 |
| 대장암 SEM-CC | 4 | 장루 논리, 개복 전환 사유, 직장암 MRI 거리, 추정실혈량 구분 |
| MASLD SEM-MA | 6 | FIB-4 재계산(MEASUREMENT의 AST/ALT/혈소판 ±7일), 지표 나이, 음주 임계, 예후 척도 명칭, 심장대사 위험인자, 간이식일 |
| 당뇨병 SEM-DM | 6 | DIABETES 방문·검사·약물·진단·환자 필드가 핵심 테이블과 일치, 방문 유형 외래, 연 1회 HbA1c, 당뇨약 ≥ 진단일 |
| 림프종 SEM-LY | 11 | dx 그룹 1행과 진단일 일치, B 증상 ↔ 병기 수식자, 결절외/골수/bulky 논리, 전환, IPI 위험군, 치료 line ↔ ANTP, 이식/CAR-T 날짜 순서, Deauville ↔ 대사 반응, 추적/생존 일관성, double-hit, 대분류 ↔ 아형 |

규칙을 추가하거나 고치는 방법은 [CONTRIBUTING.md](../CONTRIBUTING.md)에 있습니다.
