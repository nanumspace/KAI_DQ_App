# 명세 v3 — 의뢰사 9/30 매뉴얼 수정안

의뢰사의 2026-09-30 매뉴얼(`매뉴얼_질환별 데이터 테이블_20260930.xlsx`)에 2026-10-01 검토 결정을 반영한 명세입니다. 앱의 기본 판입니다. 질환마다 본표 하나를 두고 코드는 문자열 코드표로 받는 **v1 과 같은 모양**이라, 엔진은 v1 경로를 파일만 바꿔 그대로 씁니다.

| 항목 | 규모 |
|---|---|
| 표 | 17개 (core 8 · disease 6 · extension 2(SACT, ADVERSE_EVENT) · reference 1(DRUG_INGREDIENT_STRUCTURE)) |
| 필드 | 169개 |
| 구조 규칙 | 367개 (`rules/rules_structural_v3.yaml`, 명세에서 자동 생성, id `ST-NNNN`) |
| 교차 규칙 | 22개 (`rules/rules_semantic_v3.yaml`, 손으로 작성, id `SEM3-*`) |
| 코호트 | 6개 (폐암·유방암·대장암·MASLD·당뇨·림프종). 모든 코호트에 DRUG_INGREDIENT_STRUCTURE 포함, SACT 는 MASLD·당뇨 제외 |

## 출처와 결정

- 입력: `spec/client_v1/매뉴얼_질환별 데이터 테이블_20260930_수정안.xlsx`. 원본 엑셀에 채택 결정을 표시한 파일이며, **빨간 취소선 행은 삭제 결정이므로 명세에서 뺍니다.** 첫 시트 `수정 이력`은 읽지 않습니다.
- 결정 기록: `spec/client_v1/매뉴얼_수정_제안서_20261001.md` (제안 21건 중 14건 채택).
- 채택: C01 `cell_of_origin` 필수 해제(DLBCL일 때만) · C02 `sact_id` 조건부 필수 · C04 폐암 AJCC 판수 열 · C06 폐암 ICD-O-3 조직형·부위 열 · C08 OBSERVATION `value_as_concept_id` · C09 원천 코드 열 · C14 SMILES 를 성분별 참조표로 이동, `DRUG_EXPOSURE.note_id` 삭제 · C15·C16 필수 여부 빈칸 채움 · C17 방문 concept 예시 · C18 시트 번호 · C19 림프종 ICD-O-3 열 · C20 `diag_rgst_ymd` 는 진단일 · C21 소세포폐암 제한기/확장기 병기 허용.
- 채택 안 함: C03, C05, C07, C10, C11, C12(SACT 는 EPISODE 로 바꾸지 않고 `SACT` 표 유지), C13.
- 치료 표 이름은 `SACT`, 키는 `sact_id` 입니다(v1 의 ANTP_THERAPY/antp_id 가 아님).
- `clinical_stage_ajcc_edition` 은 C04(판수 열)와 C21(소세포폐암 LD/ED면 비움)을 함께 따르려고 **필수 N** 으로 두고, "AJCC 병기면 판수 필수"는 교차 규칙 `SEM3-LC-001` 이 검사합니다.

## 파일

| 파일 | 내용 |
|---|---|
| `kai_cdm_spec_v3.yaml` | 표·필드 (v1 과 같은 스키마) |
| `codelists_v3.yaml` | 설명의 `N=라벨` 코드표(embedded) + OMOP 집합(omop) |
| `cohort_profiles_v3.yaml` | 코호트별 표 구성 |

범위(range)·OMOP 코드표·외부 키는 v1 명세에 같은 표·같은 이름의 필드가 있을 때 빌려 오고, 수정안이 새로 정한 형식(ICD-O-3 코드, AJCC 판수)은 `build_spec_v3.py` 의 `EXTRA` 에 적습니다.

## 다시 만들기

```bash
python spec/build_spec_v3.py                              # 명세·코드표·코호트 구성
python rules/generate_structural_rules.py --spec v3       # rules/rules_structural_v3.yaml
python dq/engine.py --spec v3 --cohort LUNG_CANCER --data synth/output/clean_v3/LUNG_CANCER --out dq/reports/clean_v3_LUNG_CANCER
cd dq-ts && npm run engine -- --spec v3 --cohort LUNG_CANCER --data ../synth/output/clean_v3/LUNG_CANCER --out <출력 폴더>
```

교차 규칙 `rules/rules_semantic_v3.yaml` 은 손으로 고칩니다. 가상데이터는 `synth/output/{clean,dirty}_v3/<COHORT>/` 입니다.

## 알려진 한계

- **Athena 어휘가 없습니다.** concept_id 의 존재·표준 여부·domain 은 검증할 수 없습니다. 의뢰사가 사용할 Athena 판본이 아직 확정되지 않았습니다.
- OMOP 코드표는 로컬 후보 자료에서 온 것이라 **경고 수준**입니다.
- `SEM3-SACT-005`(항종양제 ATC L01 이면 `sact_id` 필수, 오류)와 `SEM3-SACT-006`(내분비 L02 이면 목적 확인, 경고)은 앱 내장 항암제 목록(`spec/concepts.yaml`, 23종 + 스테로이드 2종은 판정 제외)을 씁니다. 목록 밖 항암제는 잡지 못합니다.
- ICD-O-3 형태 코드 ↔ 조직형 범주 대조는 범주 1·2·3·4·6 만 다룹니다.
- 병기·결과 값의 원천 코드 → 결과 concept 대응표, 사건별 귀속(Q08)은 아직 정해지지 않아 검증하지 않습니다.

## 확인된 것 (2026-10-01)

- `python dq/run_all.py --spec v3`: 6개 코호트 clean 위반 0·규칙 오류 0, dirty 주입 오류(코호트당 212~275건) 검출률 100%.
- `dq-ts` 동등성 시험(v1·v2·v3): TS 와 Python 의 `report.md` 바이트 일치·findings 일치.
- 앱 스모크(`KAI_SMOKE_SPEC=v3`): 폐암 clean 287규칙 위반 0, 당뇨 dirty 위반 1,539, 폐암 dirty 엑셀 위반 936 — CLI 와 같은 수. v2 스모크도 이전과 같은 수(0 / 185 / 221).
