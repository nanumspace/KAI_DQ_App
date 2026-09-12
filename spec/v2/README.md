# 사전 v2 (초안)

질환별 임상 전문가 자문(필수항목 조사)과 v1 사전을 합쳐 재설계한 데이터 모델입니다. v1(`spec/kai_cdm_spec.yaml`)과 나란히 두고, 규칙·가상데이터·검증 앱을 v2 로 옮기는 동안 v1 파이프라인은 그대로 동작합니다.

## 설계 원칙

1. **한 테이블 = 행 단위 하나.** 테이블마다 `grain`, 고유키 `pk`, 상위 FK `parent` 가 명세에 있다. 환자 요약은 저장하지 않고 파생한다.
2. **코어 9개 테이블이 검사·약물·시술·진단·방문·사망의 유일한 원천.** 확장 표에는 코어로 담을 수 없는 등록(CRF) 항목만 있고, 코어 컬럼 복사는 없다. 과거력·약물 사용 여부·입퇴원일·사망일 같은 항목은 `derived_v2.yaml` 의 파생 변수다.
3. **닫힌 범주는 사업단 코드표에서 고른다.** 병원은 한글 라벨과 짧은 코드를 보고, 명세가 SNOMED CT·LOINC·OMOP 매핑을 가진다(`codelists_v2.yaml`).
4. **등급(tier)과 필수(required)를 구분한다.** `tier` 는 전문가 자문의 필수·권고·보류로 완전성 규칙의 근거이고, `required` 는 키와 사건일에만 건다.

## 층과 테이블

| 층 | 테이블 |
|---|---|
| 코어 (9) | PERSON, DEATH, VISIT_OCCURRENCE, CONDITION_OCCURRENCE, PROCEDURE_OCCURRENCE, DRUG_EXPOSURE, MEASUREMENT, OBSERVATION, NOTE |
| 공통 확장 (11) | COHORT_INDEX(환자 1), STAGING(환자 × 판정 시점 × 체계), PATHOLOGY_REPORT(검체 1), PATHOLOGY_TUMOR(종양 1), BIOMARKER(검사 × 마커), SURGERY(수술 1), RADIOTHERAPY(치료 코스 1), ANTP_THERAPY(요법 에피소드 1), RESPONSE_ASSESSMENT(평가 1), ADVERSE_EVENT(사건 1), FAMILY_HISTORY(환자 × 관계 × 질환) |
| 질환 확장 (13) | 질환별로 행 단위에 따라 `_BASELINE`(환자 1), `_EXAM`(검사 1), `_EVENT`(사건 1), `_ASSESSMENT`(평가 1), `_SURGERY_DETAIL`(수술 1) 로 나뉨. 예: MASLD_EXAM, DIABETES_EVENT, LYMPHOMA_ASSESSMENT, COLORECTAL_SURGERY_DETAIL |

코호트별 구성은 `cohort_profiles_v2.yaml` 에 있습니다.

## 파일

| 파일 | 내용 |
|---|---|
| `kai_cdm_spec_v2.yaml` | 테이블과 필드. 필드 속성: `type`, `value_kind`, `tier`, `required`, `codelist`, `vocabulary`, `unit`(UCUM), `pattern`, `standard`(매핑 후보), `cohorts`, `also`(같은 뜻 자문 항목), `v1_hint`(배치표의 휴리스틱 v1 대응, 참고용) |
| `codelists_v2.yaml` | 코드표. 값마다 `code`, `label`, `snomed`(2.1 에서 채움). `CL_*` 는 값 집합이 아직 비어 있는 자리 |
| `derived_v2.yaml` | 코어에서 파생하는 변수 120개(입력 항목 아님)와 파생 점수 29개 |
| `legacy_fields_v2.yaml` | v1 필드 중 자문 항목과 합쳐지지 않은 것 575개. 승격·폐기 검토용 |
| `dictionary_v2.xlsx` | 팀 배포용 사전(테이블, 필드, 코드표, 파생변수, 코호트구성, v1 미승격 필드) |
| `spec_v2_report.md` | 변환 통계, 빈 코드표 목록, 경고 |

## 만들기

원천은 1단계 배치표(`internal/decisions/배치표_v0_YYYYMMDD.xlsx`, 비공개)와 `spec/v2_field_names.py`(자문 항목 → 영문 필드명, 단위, 코드표·타입 지정)입니다. 배치표나 이름 사전을 고친 뒤 다시 돌리면 모든 파일이 재생성됩니다.

```bash
uv run --with openpyxl --with pyyaml python spec/build_spec_v2.py [배치표.xlsx] [--out spec/v2]
```

## 다음 단계 (2.1)

- 빈 코드표 55개의 값 집합 채우기, 값마다 SNOMED/LOINC ID 를 용어 서버로 확인.
- v1 미승격 필드 575개 중 승격할 것 고르기.
- 파생 변수의 concept set(과거력 진단 목록, 약물 계열 목록) 정의.
- 질환별 예측 과제·기준일·관찰창을 `COHORT_INDEX` 와 마트 파생 규칙에 반영.
- 3단계: 규칙 생성기·가상데이터·엔진·앱을 v2 로 전환.
