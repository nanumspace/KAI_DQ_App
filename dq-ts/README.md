# dq-ts · 검증 엔진 TypeScript 이식

`dq/engine.py`(Python 참조 구현)를 TypeScript 로 옮긴 것입니다. Electron 데스크톱 앱에 넣기 위한 것으로, 명세·코드표·규칙 YAML 과 교차 테이블 SQL 규칙은 수정 없이 그대로 읽습니다.

## 동등성 (2026-09-10)

6개 코호트 × (clean, dirty) 12회 실행에서 Python 참조 구현과 **규칙 단위 상태·위반 수·위반 행 내용이 완전히 일치**합니다. clean 오탐 0건, dirty 주입 오류 622건 전부 검출(재현율 1.00)도 같습니다. 12회 실행에 약 4.5초가 걸립니다.

| 실행 | 규칙 | 위반 행 (py = ts) |
|---|---|---|
| LUNG_CANCER clean / dirty | 427 | 0 / 172 |
| BREAST_CANCER clean / dirty | 463 | 0 / 154 |
| COLORECTAL_CANCER clean / dirty | 450 | 0 / 155 |
| MASLD clean / dirty | 358 | 0 / 145 |
| DIABETES clean / dirty | 392 | 0 / 950 |
| LYMPHOMA clean / dirty | 463 | 0 / 132 |

## 실행

```bash
cd dq-ts
npm install

# 코호트 하나 검증 (출력: findings.csv, summary.json, report.md)
npm run engine -- --cohort LUNG_CANCER --data ../synth/output/clean/LUNG_CANCER --out output/reports/clean_LUNG_CANCER --today 2026-09-07

# 전체: 12회 실행 → 검출 성능 평가 → Python 참조와 비교
npm run run-all

# 회귀 시험 (단위 시험 + 위 전체 실행)
npm test
```

입력 형식은 Python 엔진과 같습니다. `<TABLE>.csv`(UTF-8, 헤더 포함, NULL 은 빈 문자열, 날짜 `YYYY-MM-DD`)를 한 디렉터리에 둡니다. `antp_therapy_id` 는 `antp_id` 별칭으로 해석하고 경고합니다.

## 구조

```
dq-ts/
├─ src/
│  ├─ types.ts        명세 · 규칙 · 결과 타입
│  ├─ load.ts         YAML 로더 (spec/, rules/ 를 저장소 루트에서 읽음)
│  ├─ csv.ts          CSV 읽기/쓰기 (pandas dtype=str, keep_default_na=False 와 같은 의미)
│  ├─ pyrepr.ts       Python repr 흉내 (detail 문자열을 참조 구현과 글자 단위로 맞춤)
│  ├─ structural.ts   구조 규칙 검사기 15종 (원본 문자열 위에서)
│  ├─ semantic.ts     교차 규칙: 명세 타입으로 변환해 DuckDB 적재 → SQL 실행
│  ├─ engine.ts       엔진 본체 (적재 → 구조 → 교차 → 요약 · 보고서)
│  ├─ cli.ts          명령줄 진입점
│  ├─ verify.ts       검출 성능 평가 (dq/verify.py 이식)
│  ├─ compare.ts      Python 참조 출력과의 동등성 비교
│  └─ run_all.ts      전체 실행기
├─ test/
│  ├─ structural.test.ts   보조 함수 단위 시험
│  └─ equivalence.test.ts  12회 실행 회귀 시험 (오탐 0 · 재현율 1.00 · Python 동등)
└─ output/            실행 결과 (git 제외)
```

## 참조 구현과 맞춘 세부 동작

- **타입 변환**: pandas `to_numeric / to_datetime(errors="coerce")` 는 DuckDB `TRY_CAST` 로 대응합니다. 정수 컬럼의 `"12.0"` 은 12 로, 무효한 날짜는 NULL 로 갑니다.
- **날짜 형식 검사**: 정규식 일치 뒤 실제 달력 날짜인지 확인합니다 (`2023-02-30` 은 형식은 맞지만 무효).
- **정규식 패턴**: Python `re.match` 는 문자열 시작에만 고정되므로 `^(?:...)` 로 감쌉니다.
- **detail 문자열의 수치 표기**: YAML 의 `1.0` 을 Python 은 `1.0`, JavaScript 는 `1` 로 출력하므로, 범위 경계와 코호트 정의 경계는 YAML 원문 표기를 그대로 씁니다.
- **findings 순서**: 규칙 순서 → 행 순서로 같습니다. 환자 불변 검사는 환자 ID 문자열 순입니다.

## 앱 연동 API (`src/index.ts`)

| 함수 | 용도 |
|---|---|
| `runEngine({ cohort, data, out, today, onProgress })` | 한 번 실행. `onProgress` 로 적재·구조·교차·쓰기 단계의 진행률을 받는다 |
| `setRoot(dir)` / `getRoot()` | 명세·규칙 디렉터리 지정. 앱은 설정값 또는 내장 리소스 경로를 넣는다 |
| `loadSpec()`, `loadProfiles()`, `loadStructuralRules()`, `loadSemanticRules()` | 명세와 규칙 읽기 (규칙 관리 화면, 입력 사전 점검에 사용) |
| `readCsv(path)`, `writeCsv(...)`, `csvCell(v)` | CSV 읽기·쓰기 (앱의 입력 정규화와 출력물 생성에 사용) |
| `verify(cohort, reportsDir)`, `compareRun(...)` | 검출 성능 평가와 Python 비교 (개발용) |

## Electron 앱으로 갈 때

`app/` 이 이 방식으로 구현되어 있습니다.

- 엔진은 `runEngine()` 한 함수로 호출됩니다. 앱은 Electron 유틸리티 프로세스(`app/src/main/worker.ts`)에서 실행하고 진행률을 IPC 로 보냅니다.
- 앱은 이 디렉터리를 빌드하지 않고 `../dq-ts/src` 를 `@engine` 별칭으로 직접 번들합니다. DuckDB 는 네이티브 모듈이라 앱의 의존성으로 두고 번들에서 제외합니다.
- 명세·규칙 위치는 `setRoot()` 로 넣습니다. 번들된 환경에서는 `import.meta.url` 이 없을 수 있어 `getRoot()` 가 지연 계산하고 실패 시 작업 디렉터리로 대체합니다.
