# Quality Validator · K-AI 코호트 데이터 품질검증 앱

Electron + React + TypeScript 데스크톱 앱입니다. 검증 엔진은 `../dq-ts`(TypeScript, DuckDB)를 그대로 번들하며, 명세·규칙은 저장소의 `spec/`, `rules/` YAML 을 읽습니다. Windows 11 과 macOS 양쪽에서 같은 소스로 빌드합니다.

## 명세 판

기본은 **v2** 입니다. 환자·방문·검사는 OMOP CDM 5.4 표준 표에 앉고, 서식으로 받는 항목만 K-AI 확장 표에 둡니다 (`spec/v2/`, `rules/*_v2.yaml`, 규칙 1,078개, 코호트당 표 17~19개).

v1(질환별 단일 표, 규칙 1,196개)도 **설정 → 명세 판**에서 고를 수 있습니다. 이미 v1 로 낸 제출본을 다시 볼 때를 위한 것입니다. 판을 바꾸면 코호트·규칙·양식·견본 데이터가 함께 바뀌고 화면이 다시 그려집니다. 검증이 도는 중에는 바꿀 수 없습니다.

v2 에서 병원이 채우는 것은 저장 테이블이 아니라 **서식**입니다. '서식 변환' 화면이 서식 CSV 폴더를 저장 레코드로 바꿔 주며, 서식으로 만들 수 없는 표(환자·방문·약물·사망·검체·기록)는 EHR 추출본으로 따로 받아야 한다고 그 화면에서 알려 줍니다.

## 입력과 출력

**입력**은 코호트 테이블 파일입니다. 세 가지 형태를 받습니다.

| 형태 | 설명 |
|---|---|
| CSV 여러 개 | 파일 하나가 테이블 하나. UTF-8 또는 EUC-KR(자동 변환). 탭 구분(.tsv)도 됨 |
| 엑셀 한 파일 | 시트 하나가 테이블 하나. 날짜 셀은 자동으로 YYYY-MM-DD 로 변환 |
| 폴더 | 위 파일들이 든 폴더를 통째로. **여러 개 넣어도 됩니다** — 서식을 바꾼 폴더와 EHR 추출본 폴더가 따로여도 그대로. 폴더에 파일이 직접 없으면 바로 아래 폴더까지 찾습니다 |

폴더를 여럿 넣으면 파일 목록에 어느 폴더에서 왔는지가 함께 나오고, 폴더 하나에서 온 파일을 한꺼번에 뺄 수 있습니다. 같은 이름의 파일이 두 폴더에 있으면 어느 것을 쓰는지 사전 점검이 알려 주며, 대응표에서 다른 것으로 바꿀 수 있습니다.

**입력 정규화.** 병원 내보내기 도구가 남긴 흔적은 검증 전에 걷어 내고, 무엇을 얼마나 걷어 냈는지 보고서(`report.md` 의 '입력 정규화')와 `submission.json` 에 적습니다. 데이터를 고치는 것이 아니라 표기를 되돌리는 것이라 **뜻이 하나로 정해지는 경우만** 손댑니다.

| 흔적 | 처리 |
|---|---|
| UTF-8 BOM, CRLF, EUC-KR | UTF-8 로 |
| 세미콜론·탭·파이프 구분자 | 첫 줄에서 알아채 쉼표로 |
| 대문자 컬럼명 (`PERSON_ID`) | 소문자 명세 이름으로 |
| 이름 없는 끝 컬럼 (엑셀의 `,,,`) | 버림 |
| 값의 양끝 공백 | 걷음 |
| `NULL` `null` `NA` `N/A` `#N/A` `None` `nan` `NaN` | 빈 값으로 |
| 정수 컬럼의 `100001.0` (pandas·엑셀) | `100001` 로 |
| 날짜 컬럼의 `2022-01-01 00:00:00` (SQL 내보내기) | `2022-01-01` 로 |

`1,234` 같은 천 단위 쉼표, `2022/01/01` 같은 다른 날짜 형식, 엑셀 일련번호 날짜(`45000`)는 손대지 않고 규칙 위반으로 보고합니다. 이 때문에 같은 파일을 명령줄 엔진(`dq-ts`)에 바로 넣었을 때와 위반 수가 다를 수 있습니다 — 예컨대 v1 가상데이터의 주입 오류 중 `N/A` 를 숫자 자리에 넣은 3건은 앱에서는 빈 값이 되어 타입 위반이 아닙니다(필수 자리였다면 필수값 위반으로 잡힙니다). 시험은 `app/test/realworld.test.ts` 에 있습니다(`npm test`).

파일·시트 이름이 테이블 이름과 다르면 이름 포함 여부와 헤더 유사도(명세 컬럼의 60% 이상)로 자동 대응하고, 화면의 대응표에서 직접 바꿀 수 있습니다. 실행 전 사전 점검이 기본키·person_id 누락, 컬럼 불일치, 별칭, 날짜 형식 표본을 알려 주며, 오류가 있으면 실행 단추가 잠깁니다. 넣은 파일은 실행 폴더의 `input/` 에 `<TABLE>.csv` (UTF-8) 로 정규화되어 보관됩니다.

입력 양식은 앱에서 내려받습니다: 엑셀 양식(시트당 테이블 + 명세 시트), CSV 양식 묶음(헤더만), 컬럼 명세서(xlsx), 견본 데이터(100명 가상 코호트), 그리고 v2 에서는 서식 양식(병원이 채울 빈 서식 CSV).

사전 점검에서 **없으면 실행을 막는 표**는 v1 이 환자와 질환 본표 둘, v2 는 환자 하나입니다. v2 의 나머지 표는 없어도 실행되지만 엔진이 '테이블 없음' 오류로 보고하므로, 해당 사례가 없더라도 헤더만 있는 빈 파일을 넣는 편이 낫습니다.

**출력**은 실행마다 다섯 파일입니다.

| 파일 | 내용 | 외부 제출 |
|---|---|---|
| report.md | 검증 보고서 (요약, 분류별 집계, 실패 규칙과 예시) | 가능 |
| findings.csv | 위반 행 목록 (규칙, 테이블, 행 키, 환자 ID, 상세) | 금지 (환자 단위) |
| rule_results.csv | 규칙 1,196개의 통과·실패·건너뜀과 위반 수 | 가능 |
| submission.json | 중앙 제출용 집계 (환자 단위 정보 없음) | 가능 · 중앙에 보내는 유일한 파일 |
| summary.json | 엔진 원본 요약 | 가능 |

"결과 폴더로 내보내기" 가 다섯 파일과 README 를 폴더 하나에 담습니다.

## 화면

| 메뉴 | 내용 |
|---|---|
| 대시보드 | ① 오류 유형별 통계(도넛, 심각도표) ② 질환별 검증 결과(최신 실행, 오류율 신호등) ③ 적용 검증 규칙 ④ 후속 조치 가이드 ⑤ 실행 이력 추이와 상태 요약 |
| 검증 실행 (첫 화면) | ① 코호트와 파일(드래그 앤 드롭·파일·폴더, 양식 내려받기) ② 테이블 대응표와 사전 점검, 미리보기 ③ 실행과 진행률 ④ 결과와 출력물 5종 |
| 검증 규칙 관리 | 규칙 조회·필터·검색 (v2 1,078개 · v1 1,196개), 규칙 상세(설명, SQL, 조치 안내) |
| 오류 현황 조회 | 실행별 위반 행 조회, 규칙·테이블·심각도·검색 필터, 쪽 넘김, CSV 내보내기 |
| 결과 보고서 | 실행 요약, 실패 규칙, Kahn 분류별 집계, 테이블 행 수, 보고서 원문, 다운로드(.md/.csv/.json) |
| 통계 모니터링 | 실행 이력 목록과 위반 건수·오류율 추이, 실행 기록 삭제 |
| 서식 변환 (v2) | 서식 CSV 폴더 → 저장 레코드, 변환 결과와 EHR 추출이 필요한 표 안내 |
| 설정 | 명세 판, 명세·규칙 위치, 검증 실행일 기본값, 데이터 위치 |

## 구조

```
app/
├─ src/main/
│  ├─ index.ts     창 · IPC · 엔진 워커 실행 · 스모크 모드
│  ├─ input.ts     파일 인식(CSV·엑셀) · 인코딩 감지 · 자동 대응 · 사전 점검 · 정규화 · 양식 생성
│  ├─ outputs.ts   출력물 5종 정의 · rule_results.csv · submission.json · 묶음 내보내기
│  ├─ worker.ts    utilityProcess 에서 엔진 실행 (화면이 멈추지 않음), 진행률 전송
│  ├─ db.ts        실행 이력 DuckDB (runs · rule_results · findings)
│  └─ config.ts    userData/config.json
├─ src/preload/index.ts   contextBridge 로 window.api 노출
├─ src/shared/            types.ts (IPC 계약) · labels.ts (검사 유형·심각도 이름표, 조치 안내)
├─ src/renderer/src/      React 화면 (pages/ 7개, components/ui.tsx, styles.css)
└─ electron.vite.config.ts  @engine → ../dq-ts/src 별칭
```

데이터 흐름: 화면 → IPC → 메인이 워커를 fork → 워커가 `runEngine()` 실행, 진행률 postMessage → 완료 시 `userData/runs/<실행 ID>/` 에 findings.csv · summary.json · report.md 저장 → 메인이 DB 에 적재 → 화면 갱신.

## 개발

```bash
cd app
npm install            # electron 바이너리가 안 풀리면: node node_modules/electron/install.js
npm run dev            # 개발 모드 (핫 리로드)
npm run typecheck
npm run build          # out/ 생성
npm run smoke          # 빌드 후 자동 점검: 폐암 clean(CSV) · 당뇨 dirty(CSV) · 폐암 dirty(엑셀 한 파일) 실행, 서식 변환, 화면 8개 PNG 캡처
                       # KAI_SMOKE_OUT 로 결과 위치, KAI_SMOKE_SPEC=v1|v2 로 명세 판 지정
                       # 설치본에서도 돈다: KAI_SMOKE=1 "release/mac-arm64/Quality Validator.app/Contents/MacOS/Quality Validator"
                       # (설치본에는 synth/ 가 없어 내장 견본으로 돌고 dirty 단계는 건너뛴다)
```

개발 모드에서는 명세 위치가 저장소 루트(`app/..`)이고, 실행 이력은 OS 의 앱 데이터 폴더(`~/Library/Application Support/kai-quality-validator` 또는 `%APPDATA%`)에 저장됩니다.

## 배포 빌드와 릴리스

배포용 빌드는 저장소 루트의 `release.sh` 가 합니다 (macOS 에서 실행, Windows 는 SafeNet 토큰 서명, macOS 는 Developer ID 서명과 공증). 사용법은 루트 README 의 릴리스 절, 단계별 동작은 `docs/reproduce.md` 에 있습니다.

```bash
../release.sh --no-publish   # 빌드·서명·공증·검증 (release/ 에 산출물)
npm run dist:mac             # 서명·공증 포함 macOS 빌드만 (APPLE_KEYCHAIN_PROFILE 필요)
npm run dist:win             # Windows 빌드만 (토큰 서명 훅 build/sign-win.cjs 가 동작)
```

- `build/icon.svg` 가 앱 아이콘 원본이고 `build/icon.png`(1024×1024)를 electron-builder 가 macOS icns 와 Windows ico 로 변환합니다. SVG 를 고치면 `qlmanage -t -s 1024 -o build build/icon.svg && mv build/icon.svg.png build/icon.png` 으로 다시 만듭니다. 색은 K-AIPA 브랜드(남색 `#003B73`, 파랑 `#275BAB`, 청록 `#00C2D1`)를 따릅니다.
- `build/sign-win.cjs` 는 Windows exe 서명 훅, `build/globalsign-*.pem` 은 서명에 첨부하는 중간 인증서와 검증용 루트 인증서입니다.
- `package.json > build.extraResources` 가 `../spec/*.yaml`, `../spec/v2/`(명세 YAML 과 `vocab/*.csv`), `../rules/*.yaml`, 견본 데이터(v1·v2)를 `resources/kai/` 로 복사하므로 설치본은 명세를 내장합니다. `spec/v2/vocab/ref/`(MedDRA·LOINC 등 외부 표)는 각 기관이 자기 라이선스로 받는 것이라 넣지 않습니다.
- DuckDB 는 네이티브 모듈이라 `asarUnpack` 으로 풀어 둡니다. 설치본에는 대상 플랫폼의 바이너리만 들어가며(`release.sh` 가 교체), Windows 32비트는 바이너리가 없어 만들지 않습니다.

## 확인된 것 (2026-09-15 · v2 전환)

- v2 로 스모크 시험: 폐암 clean 377규칙 위반 0, 당뇨 dirty 341규칙 위반 198, 폐암 dirty 엑셀(시트 18개) 위반 236 — CLI(`dq-ts`, `dq/`)와 같은 수.
- 서식 경로: 빈 양식 12개 생성, 서식 4개 80행 → 레코드 80건(확인할 점 0건), 화면 8개 캡처.
- 실데이터 흉내 입력 18종(`app/test/realworld.test.ts`): BOM·CRLF·EUC-KR·대문자 헤더·공백·NULL 글자·`.0`·`00:00:00`·세미콜론·빈 끝 컬럼·다른 파일명·따옴표 안 줄바꿈은 원본과 같은 결과(위반 0), 엑셀 일련번호 날짜·천 단위 쉼표는 규칙 위반으로 보고, 중복 헤더·빈 파일·UTF-16 은 죽지 않고 사전 점검에서 막음.
- 개인정보: 병원 밖으로 나갈 수 있는 파일(`report.md`, `rule_results.csv`, `submission.json`, `summary.json`)에 환자 단위 값이 없는지 v2 표 기준으로 훑었다. `report.md` 의 '예시'가 실제 셀 값(ID·날짜·수치·원천 문자열)을 싣고 있어 두 엔진 모두에서 값을 `…` 로 가리게 했고, 두 엔진의 `report.md` 가 바이트까지 같은지 동등성 시험에 넣었다. 환자 단위 값은 `findings.csv` 에만 있다.
- 규모 시험(`KAI_SCALE_DATA=<폴더> npx vitest run test/scale.test.ts`): 코호트당 환자 2,000명(행 13만~48만, 7~33MB)에서 인식·정규화 0.3~1.3초, 엔진 0.6~2.4초, RSS 1GB 미만, 위반 0. 이 크기에서 처음 드러난 시나리오 결함 5건(사망 뒤 사건, 남성의 산과력, 침윤>절제 림프절, double-hit 판정, 부분 연도의 HbA1c)을 고쳤다.
- 설치본(`electron-builder --mac dir`)을 직접 띄워 확인: 내장 명세만으로 v2 규칙 1,078개를 읽고 견본 데이터로 377규칙 위반 0, 폴더 2곳 입력·서식 변환·화면 8개 모두 동작. 번들에 `spec/v2/`(어휘 CSV 포함)와 v1·v2 견본이 들어가고 `vocab/ref/` 는 빠진다(29MB).
- 폴더 여러 개 입력: 폐암 clean 을 두 폴더로 쪼개 넣어 18개 표 전부 자동 대응, 위반 0 (한 폴더로 넣었을 때와 같음). 그 둘을 담은 상위 폴더 하나만 넣어도 같은 결과. 같은 이름이 두 폴더에 있으면 어느 것을 쓰는지 안내 1건.
- `KAI_SMOKE_SPEC=v1 npm run smoke` 로 v1 경로도 동작 (427규칙 위반 0/168, 392규칙 위반 946 — 입력 정규화가 `N/A` 주입 오류 3건과 별칭 컬럼 경고 1건을 걷어 내어 명령줄의 172/950 보다 4건 적다).

## 확인된 것 (2026-09-10)

- 타입 검사와 빌드 통과. 스모크 시험: 폐암 clean(CSV), 당뇨 dirty(CSV), 폐암 dirty(엑셀 한 파일) 3회 실행, 화면 7개 캡처. 엑셀 입력은 시트 11개가 자동 대응되고 CSV 입력과 같은 위반 172건.
- 이름을 바꾼 CSV(한글 파일명, EUC-KR 포함)를 넣었을 때 자동 대응과 UTF-8 변환 확인.
- 설계 결정은 내부 문서 `internal/decisions/DECISIONS.md` 의 D-15~D-18 (공개 저장소에는 포함되지 않음).

## 이후 할 일

- 실제 Windows 11 PC 에서 설치·실행 확인 (한글 경로·폰트 포함)
- 자동 업데이트
- 규칙 심각도 3단계(정보 등급)와 규칙별 조치 안내를 `rules/*.yaml` 에 추가하고, 규칙 관리 화면에서 활성화 여부를 편집
- 파일럿에서 회수한 submission.json 을 모아 보는 중앙용 화면
