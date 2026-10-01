# 의뢰사 v1: 질환 항목 → OMOP-style 레코드 개념 작업표

**기준 자료:** `raw/매뉴얼_질환별 데이터 테이블_20260930.xlsx`의 질환별 여섯 시트. `disease_record_catalog.csv`는 질환별 PK·`person_id`·`visit_occurrence_id`를 제외한 39개 원천 항목의 저장 위치와 필요한 개념을 기록한 **작업표**다. `source_value_catalog.csv`는 설명에 코드표가 명시된 32개 원천 값을 따로 대조한다. `standard_concept_id`가 비어 있으면 아직 병원에 배포할 숫자가 없다. 빈 칸을 임의의 정수·원천 코드·v2 K-AI concept_id로 채우지 않는다. 이 파일은 승인된 CONCEPT 배포본이 아니다.

## 개념 식별자의 종류

- **항목 개념:** `measurement_concept_id`/`observation_concept_id` 등에 들어가는 *무엇을 측정·관찰했는가*의 OMOP 표준 개념.
- **결과 개념:** 예/아니오·폐경 상태처럼 범주형 결과를 가리키는 `value_as_concept_id`. 엑셀 설명의 `1=Yes` 같은 정수는 원천 코드이지 OMOP concept_id가 아니다. `3=Unknown` 또는 `4=Not Applicable` 등을 NULL/No로 치환하지 않는다.
- **종양 관례 예외:** OHDSI 종양 관례에 따라 폐암 조직형은 결과값이 아니라 진단 `CONDITION_OCCURRENCE`의 ICD-O-3 조직형-부위 개념으로, 병기는 Cancer Modifier 병기 개념 자체를 `measurement_concept_id`로 기록하고 진단 행에 `measurement_event_id`로 연결한다. [OHDSI Oncology Conventions](https://ohdsi.github.io/OncologyWG/conventions.html)
- **원천 개념:** OMOP 표준에 정확히 대응하는 항목이 없을 때 로컬 어휘에 등록할 수 있지만 **표준 concept_id 열에 넣으면 안 된다**. OMOP 규약상 로컬 concept은 20억 초과·비표준(`standard_concept=NULL`)으로 만들고 `*_source_concept_id`에만 저장하며 가능하면 표준 개념으로 `Maps to`한다. [OHDSI Custom Concepts](https://ohdsi.github.io/CommonDataModel/customConcepts.html). 기존 `spec/v2/vocab/CONCEPT.csv`의 100억 번대 ID는 이 프로젝트 자체 어휘로 공식 OMOP concept_id가 아니다.

## 원본 유지와 검증 범위

매뉴얼 자체의 수정 제안과 의뢰사에 확인할 질문은 `review/proposals.py`에 정리되어 있고 검토 웹서비스(`review/`)에서 결정한다. 이 작업표의 `NEEDS_SCHEMA_*`는 해당 제안이 채택되어야 저장 가능한 항목이다. 제안을 채택하지 않으면 그 범위(결과 concept ID 검증·사건별 귀속 검증 등)를 달성했다고 주장하지 않는다.

**2026-10-01 결정 결과:** `매뉴얼_수정_제안서_20261001.md`(질문 12개 답·제안 21개 결정, 모순 0건)와 `매뉴얼_질환별 데이터 테이블_20260930_수정안.xlsx`(채택 14건 반영 표시본: 노란색 수정 칸·메모에 수정 전 값, 초록색 추가 행·시트, 빨간 취소선 삭제 행, 첫 시트 `수정 이력`). 원본 엑셀은 수정하지 않았다. 제안 속 concept ID 숫자(방문 9202 등)는 고정할 Athena 판본에서 확인 전이다.

## 계약을 확정해야 할 부분

1. **개념 사전 판본과 출처:** 의뢰사가 사용하는 Athena `CONCEPT`, `VOCABULARY`, `CONCEPT_RELATIONSHIP`, `CONCEPT_ANCESTOR`의 판본을 고정하고 각 숫자의 명칭·domain·표준 여부·유효일·매핑을 확인한다. `raw/smc_omop_concept_id_catalog.xlsx`는 일부 후보 숫자만 담은 로컬 자료다. 예: 유방암 진단 4112853, 난자 동결 4234919, 배아 동결 2213355, 결과 Yes/No 4188539/4188540. 해당 판본의 Athena 검증과 문맥 검토 전에는 공식 배포값으로 취급하지 않는다. 기존 v2의 LOINC `21908-9`(초진 임상 병기)와 `93783-9`(DLBCL 세포기원)는 **LOINC 코드**이며 숫자 OMOP concept_id가 아니다.
2. **실제 파일 스키마와 요구 수준의 차이:** 9월 30일 매뉴얼의 `MEASUREMENT`·`OBSERVATION`에는 `*_source_concept_id`가 없고, `OBSERVATION`에는 `value_as_concept_id`도 없다. **항목 개념만** 사용한다면 기존 `observation_concept_id`와 결과 원천값(`value_as_number`/`value_as_string`)으로 범위를 제한할 수 있다. **결과 개념까지** 요구하면 대상 열 또는 대체 저장 계약이 필요하다. `CONDITION_OCCURRENCE`에는 당뇨 시트의 `condition_end_date`가 없다. 당뇨 특화 표에 남기거나, 특화 표를 없애려면 종료일 저장 위치를 추가로 합의한다. `DRUG_EXPOSURE.sact_id`와 `note_id`가 모두 필수(Y)인 상태에서 비항암 약물을 포함한다면 조건부 필수 규약이 필요하다. 원본 엑셀 자체를 바꾸기보다 범위와 필요한 최소 부속 변경을 먼저 승인받는다.
3. **코호트·사건 연결:** 환자당 단일 진단/복수 진단, 동일 방문의 여러 수술·평가·검사 중 어느 사건에 관찰값이 속하는지 결정해야 한다. `person_id`와 `visit_occurrence_id`만으로는 사건-항목 연결이 유일하지 않다. 질환별 PK나 `sact_id`를 없앨 경우 별도 에피소드/이벤트 ID와 연결 방식이 필요하다. 특히 9월 30일 매뉴얼에는 질환별 표 외에 `SACT`, `ADVERSE_EVENT` 시트가 그대로 남아 있어 이 두 표를 보존할지 레코드로 바꿀지도 결정해야 한다.
4. **필수의 적용 조건:** `LYMPHOMA.cell_of_origin`의 Y는 설명상 DLBCL 분류인데 모든 림프종 환자에게 강제하면 오탐이다. 항목의 적용 질환·조직형·사건 시점·결측 허용 조건을 정한 다음에만 존재 규칙을 생성한다. `diag_rgst_ymd`가 실제 진단일인지 단순 등록일인지도 확정한다.

## 항목 존재 검사 계약(예시)

- 분모: 코호트 정의에 따라 **대상 환자/해당 사건**을 먼저 확정한다. `PERSON` 전체를 질환 환자로 간주하지 않는다.
- 대상 테이블에 같은 `person_id`의 행이 있고, 확정된 **항목 표준 concept_id**로 구분되며, 합의한 진단·방문·사건에 연결되고, 결과(`value_as_number`/`value_as_concept_id`/`value_as_string` 또는 날짜)가 유효할 때만 해당 항목을 수집한 것으로 센다. 단순 테이블 존재나 같은 환자의 임의 관찰 행으로 통과시키지 않는다.
- `required=Y`는 확정된 적용 조건에서 누락을 오류로, `N`은 수집된 레코드의 형식·개념·결과만 검사한다. 원천 코드 1~7/1~4 및 기타는 **별도의 값 개념 대응표**가 확정되기 전에는 숫자 동일성을 가정하지 않는다.
- 예: 폐암 `clinical_stage`는 해당 진단 시점의 병기 MEASUREMENT 행과 유효한 병기 결과가 있어야 통과한다. `stage_iv_diagnosis_date`는 진단 IV기와 나중 재발이라는 서로 다른 사건을 먼저 구분한다.

**현재 상태:** 질환별 항목의 대상 테이블·값 열은 검토 초안이다. 39개 항목의 숫자 **표준 concept_id는 아직 0개 확정**이다. 원천 값 32개 중 10개의 숫자는 로컬 카탈로그의 후보일 뿐이고 22개는 미확인이다. Athena 판본의 개념 조회가 불가능하여 후보의 유효성·표준 여부를 검증하지 못했다. 원천 값→결과 개념 대응, 에피소드 연결, 적용 조건 역시 미확정이다. 이 대응표로 앱에서 환자별 존재 위반을 확정 판정하거나 병원에 최종 입력 지침을 배포하면 안 된다.
