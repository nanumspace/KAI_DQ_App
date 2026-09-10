# 검증 엔진과 앱

## Python 참조 구현 (`dq/`)

```
python dq/engine.py --cohort <COHORT> --data <csv 디렉터리> --out <보고서 디렉터리> [--today YYYY-MM-DD]
```

1. 코호트 구성(`spec/cohort_profiles.yaml`)에 따라 `<TABLE>.csv`를 문자열 그대로 읽습니다. `antp_therapy_id`는 `antp_id` 별칭으로 해석하고 경고합니다.
2. **구조 규칙**은 원본 문자열 위에서 검사합니다 (타입 오류를 잡기 위해).
3. **교차 테이블 규칙**은 명세 타입으로 변환한 뒤 DuckDB에 적재해 SQL로 실행합니다. 보조 테이블 `_MEASUREMENT_CONCEPTS`(검사 타당 범위), `_ANTICANCER_DRUGS`를 함께 등록합니다.
4. 출력: `findings.csv`(위반 행 단위), `summary.json`(규칙 단위 상태와 위반 수), `report.md`(사람용 요약).

### 검출 성능 평가 (`dq/verify.py`)

clean 실행에서 오탐(위반) 수, dirty 실행에서 manifest의 오류별 검출 여부를 판정합니다. 검출 판정은 "기대 규칙 중 하나가 같은 person_id 또는 같은 pk로 findings에 있음"입니다. 주입 오류의 부수 효과로 함께 발화한 규칙(collateral)은 별도로 기록합니다.

### 결과 (2026-09-07, `dq/reports/verification_summary.md`)

| 코호트 | 실행 규칙 | clean 오탐 | 주입 오류 | 검출 | 재현율 | 오류 유형 (전부 검출 / 전체) |
|---|---|---|---|---|---|---|
| LUNG_CANCER | 427 | 0 | 109 | 109 | 1.00 | 34 / 34 |
| BREAST_CANCER | 463 | 0 | 110 | 110 | 1.00 | 34 / 34 |
| COLORECTAL_CANCER | 450 | 0 | 109 | 109 | 1.00 | 35 / 35 |
| MASLD | 358 | 0 | 96 | 96 | 1.00 | 30 / 30 |
| DIABETES | 392 | 0 | 94 | 94 | 1.00 | 29 / 29 |
| LYMPHOMA | 463 | 0 | 104 | 104 | 1.00 | 33 / 33 |
| **합계** | | **0** | **622** | **622** | **1.00** | |

MASLD와 DIABETES에서 건너뛴 규칙 9개는 ANTP_THERAPY가 코호트에 없어 실행 대상이 아닌 규칙입니다.

**해석의 한계.** 재현율 1.00과 오탐 0은 가상데이터가 규칙을 만족하도록 만들어졌기 때문에 나온 값입니다. 프로그램이 규칙을 정확히 구현했다는 증거이지 병원 데이터 품질에 대한 예측이 아닙니다. 실제 병원 데이터의 오탐률과 새 오류 유형은 파일럿에서 측정해 규칙과 주입 카탈로그에 추가하고, 같은 방식으로 회귀 시험합니다.

## TypeScript 엔진 (`dq-ts/`)

Electron 앱에 넣기 위해 엔진을 TypeScript로 옮겼습니다. 명세·규칙 YAML과 SQL 규칙은 그대로 읽고, 구조 규칙 검사기 15종은 TypeScript로 다시 썼으며, 교차 규칙은 DuckDB Node 바인딩으로 실행합니다.

12회 실행(6개 코호트 × clean/dirty)에서 Python 참조 구현과 규칙 단위 상태·위반 수·위반 행 내용이 완전히 일치합니다(정렬 후 바이트 단위 동일). `npm test`가 단위 시험과 이 동등성 시험을 회귀 시험으로 고정합니다. 이식 중 맞춰야 했던 세부 동작(Python repr의 수치 표기, 정규식 시작 고정, pandas coerce와 DuckDB TRY_CAST 대응)은 `dq-ts/README.md`에 있습니다.

```bash
cd dq-ts && npm install && npm run run-all    # 12회 실행 → 검출 성능 → Python 비교
```

## 데스크톱 앱 Quality Validator (`app/`)

Electron + React + TypeScript로 만든 검증 프로그램입니다. Windows 11과 macOS에서 같은 소스로 빌드하며, 병원 DB에 접속하지 않고 네트워크 통신도 없습니다.

**입력.** 코호트 테이블 파일을 세 가지 형태로 받습니다: CSV 여러 개(UTF-8 또는 EUC-KR, EUC-KR은 자동 변환), 시트당 테이블 하나인 엑셀 한 파일(날짜 셀은 YYYY-MM-DD로 변환), 또는 파일들이 든 폴더. 파일·시트 이름이 테이블 이름과 달라도 이름 포함 여부와 헤더 유사도(명세 컬럼의 60% 이상)로 자동 대응하고, 대응표에서 직접 바꿀 수 있습니다. 실행 전 사전 점검이 기본키·person_id 누락(오류, 실행 차단), 명세 컬럼 불일치, 별칭, 날짜 형식 표본(주의)을 알려 줍니다.

**출력.** 실행마다 다섯 파일이 실행 폴더에 생깁니다.

| 파일 | 내용 | 외부 제출 |
|---|---|---|
| `report.md` | 검증 보고서 | 가능 |
| `findings.csv` | 위반 행 목록 (규칙, 테이블, 행 키, 환자 ID, 상세) | 금지 (환자 단위) |
| `rule_results.csv` | 규칙 1,196개의 통과·실패·건너뜀과 위반 수 | 가능 |
| `submission.json` | 중앙 제출용 집계 (환자 단위 정보 없음), `schema: kai-dq-submission/1` | 가능, 중앙에 보내는 유일한 파일 |
| `summary.json` | 엔진 원본 요약 | 가능 |

**구조.** 화면(React, 샌드박스)은 preload가 노출한 좁은 API로만 메인 프로세스에 요청합니다. 메인이 파일을 인식·정규화하고 엔진을 Electron 유틸리티 프로세스(워커)에서 실행해 진행률을 전달하며, 실행마다 요약·규칙별 결과·위반 행을 사용자 컴퓨터의 DuckDB 이력 DB에 적재합니다. 화면은 검증 실행(첫 화면, 4단계 마법사), 결과 보고서, 오류 현황 조회, 대시보드, 통계 모니터링, 검증 규칙 관리, 설정 7개입니다.

**자동 점검.** `npm run smoke`가 가상데이터로 검증 3회(폐암 clean CSV, 당뇨 dirty CSV, 폐암 dirty 엑셀 한 파일)를 자동 실행하고 화면 7개를 PNG로 캡처합니다.

세부 구조와 개발 방법은 `app/README.md`에 있습니다.
