# 기여 안내

## 저장소 구성

| 폴더 | 내용 | 바꿀 때 다시 해야 하는 것 |
|---|---|---|
| `spec/` | 명세, 코드표, 코호트 구성, concept | 구조 규칙 재생성 → 가상데이터 재생성 → 검증 |
| `rules/` | 구조 규칙(자동 생성), 교차 테이블 SQL 규칙(수동) | 가상데이터로 검증, 필요하면 오류 주입 유형 추가 |
| `synth/` | 생성 프레임워크, 시나리오, 오류 주입기 | 전체 파이프라인 재실행 |
| `dq/` | Python 참조 엔진, 검출 성능 평가 | `dq-ts` 동등성 시험 |
| `dq-ts/` | TypeScript 엔진 | `npm test` |
| `app/` | 데스크톱 앱 | `npm run typecheck`, `npm run build`, `npm run smoke` |
| `docs/`, `manual/` | 공개 문서, 사용자 설명서 | 화면이나 출력물이 바뀌면 설명서를 같이 고침 |

## 규칙을 추가하거나 고치기

**구조 규칙**은 직접 편집하지 않습니다. `spec/kai_cdm_spec.yaml`의 필드 속성(`required`, `range`, `pattern`, `codelist`, `group`, `anchor`, `level`)을 고친 뒤 생성기를 다시 돌립니다.

```bash
python rules/generate_structural_rules.py
```

**교차 테이블 규칙**은 `rules/rules_semantic.yaml`에 DuckDB SQL로 추가합니다. 규칙 하나는 id(`SEM-<그룹>-<번호>`), 이름, Kahn 분류, 심각도, 적용 코호트, 설명, SQL을 가집니다. SQL은 위반 행을 `person_id`, `row_key`, `detail` 세 컬럼으로 반환해야 하며, 코호트별 치환자(`{COHORT_CONDITION_IDS}`, `{DISEASE}`, `{DISEASE_PK}` 등)를 쓸 수 있습니다. 기존 규칙을 본떠 작성하면 됩니다.

규칙을 추가했으면 다음 순서로 확인합니다.

1. clean 가상데이터에서 새 규칙의 위반이 0건인지 봅니다. 위반이 있으면 규칙이 틀렸거나 시나리오가 사전과 다른 것이므로 어느 쪽인지 판단합니다.
2. `synth/inject_faults.py`에 그 규칙이 잡아야 할 오류 주입 유형을 추가하고 `expected_rules`에 규칙 id를 적습니다.
3. 전체 파이프라인을 다시 돌려 재현율이 유지되는지 봅니다.

```bash
python dq/run_all.py
cd dq-ts && npm test
```

Python과 TypeScript 엔진은 같은 YAML을 읽으므로 규칙 YAML만 고치면 두 엔진에 같이 반영됩니다. 구조 규칙의 검사 유형을 새로 만드는 경우에만 `dq/engine.py`와 `dq-ts/src/structural.ts` 양쪽을 고치고 동등성 시험을 통과시켜야 합니다.

## 사전 v2

`spec/v2/` 의 재설계 명세는 `spec/build_spec_v2.py` 가 배치표(비공개)와 `spec/v2_field_names.py` 에서 생성합니다. 필드 이름·단위·코드표 지정을 바꾸려면 `v2_field_names.py` 를 고치고 다시 생성합니다. 생성물을 직접 편집하지 마세요.

## 명세 자체를 바꾸기

명세를 만드는 `spec/build_spec.py`는 원본 데이터 사전을 파싱한 JSON을 입력으로 받습니다. 원본 사전은 공개 저장소에 포함되지 않으므로, 외부 기여자는 생성된 `spec/*.yaml`을 직접 고치고 그 변경을 pull request로 제안합니다. 유지 관리자가 사전과 대조해 반영합니다.

## 코드 규약

- Python은 3.10 이상, TypeScript는 strict 모드입니다.
- 커밋 전에 `cd dq-ts && npm test`와 `cd app && npm run typecheck`가 통과해야 합니다. CI가 같은 것을 실행합니다.
- 병원 데이터나 환자 정보를 절대 저장소에 넣지 않습니다. 시험 데이터는 `synth/`의 가상데이터만 씁니다.

## 문제 보고

GitHub Issues에 다음을 적어 주세요.

- 코호트, 사용한 파일 형태(CSV/엑셀/폴더), 운영체제
- 기대한 결과와 실제 결과
- 가능하면 `summary.json` 또는 `rule_results.csv`. `findings.csv`는 환자 단위 정보이므로 첨부하지 않습니다.
