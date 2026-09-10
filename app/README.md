# Quality Validator · K-AI 코호트 데이터 품질검증 앱

Electron + React + TypeScript 데스크톱 앱입니다. 검증 엔진은 `../dq-ts`(TypeScript, DuckDB)를 그대로 번들하며, 명세·규칙은 저장소의 `spec/`, `rules/` YAML 을 읽습니다. Windows 11 과 macOS 양쪽에서 같은 소스로 빌드합니다.

## 입력과 출력

**입력**은 코호트 테이블 파일입니다. 세 가지 형태를 받습니다.

| 형태 | 설명 |
|---|---|
| CSV 여러 개 | 파일 하나가 테이블 하나. UTF-8 또는 EUC-KR(자동 변환). 탭 구분(.tsv)도 됨 |
| 엑셀 한 파일 | 시트 하나가 테이블 하나. 날짜 셀은 자동으로 YYYY-MM-DD 로 변환 |
| 폴더 | 위 파일들이 든 폴더를 통째로 |

파일·시트 이름이 테이블 이름과 다르면 이름 포함 여부와 헤더 유사도(명세 컬럼의 60% 이상)로 자동 대응하고, 화면의 대응표에서 직접 바꿀 수 있습니다. 실행 전 사전 점검이 기본키·person_id 누락, 컬럼 불일치, 별칭, 날짜 형식 표본을 알려 주며, 오류가 있으면 실행 단추가 잠깁니다. 넣은 파일은 실행 폴더의 `input/` 에 `<TABLE>.csv` (UTF-8) 로 정규화되어 보관됩니다.

입력 양식은 앱에서 내려받습니다: 엑셀 양식(시트당 테이블 + 명세 시트), CSV 양식 묶음(헤더만), 컬럼 명세서(xlsx), 견본 데이터(100명 가상 코호트).

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
| 검증 규칙 관리 | 규칙 1,196개 조회·필터·검색, 규칙 상세(설명, SQL, 조치 안내) |
| 오류 현황 조회 | 실행별 위반 행 조회, 규칙·테이블·심각도·검색 필터, 쪽 넘김, CSV 내보내기 |
| 결과 보고서 | 실행 요약, 실패 규칙, Kahn 분류별 집계, 테이블 행 수, 보고서 원문, 다운로드(.md/.csv/.json) |
| 통계 모니터링 | 실행 이력 목록과 위반 건수·오류율 추이, 실행 기록 삭제 |
| 설정 | 명세·규칙 위치, 검증 실행일 기본값, 데이터 위치 |

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
npm run smoke          # 빌드 후 자동 점검: 폐암 clean(CSV) · 당뇨 dirty(CSV) · 폐암 dirty(엑셀 한 파일) 실행, 화면 7개 PNG 캡처 (KAI_SMOKE_OUT 로 위치 지정)
```

개발 모드에서는 명세 위치가 저장소 루트(`app/..`)이고, 실행 이력은 OS 의 앱 데이터 폴더(`~/Library/Application Support/kai-quality-validator` 또는 `%APPDATA%`)에 저장됩니다.

## 배포 빌드

```bash
npm run dist:mac       # release/*.dmg (macOS 에서)
npm run dist:win       # release/*.exe (Windows 에서, 또는 GitHub Actions windows 러너)
```

- `package.json > build.extraResources` 가 `../spec/*.yaml`, `../rules/*.yaml` 을 `resources/kai/` 로 복사하므로 설치본은 명세를 내장합니다.
- DuckDB 는 네이티브 모듈이라 `asarUnpack` 으로 풀어 둡니다. Windows x64, macOS arm64, macOS x64 는 각각 해당 OS 에서 빌드합니다.
- 코드 서명(Windows 인증서, Apple 공증)은 아직 설정하지 않았습니다. 서명 없이 배포하면 SmartScreen · Gatekeeper 경고가 뜹니다.

## 확인된 것 (2026-09-10)

- 타입 검사와 빌드 통과. 스모크 시험: 폐암 clean(CSV), 당뇨 dirty(CSV), 폐암 dirty(엑셀 한 파일) 3회 실행, 화면 7개 캡처. 엑셀 입력은 시트 11개가 자동 대응되고 CSV 입력과 같은 위반 172건.
- 이름을 바꾼 CSV(한글 파일명, EUC-KR 포함)를 넣었을 때 자동 대응과 UTF-8 변환 확인.
- 설계 결정은 내부 문서 `internal/decisions/DECISIONS.md` 의 D-15~D-18 (공개 저장소에는 포함되지 않음).

## 이후 할 일

- Windows 러너에서 설치 파일 빌드와 Windows 11 실행 확인 (한글 경로·폰트 포함)
- 코드 서명(Windows 인증서, Apple 공증)과 자동 업데이트
- 규칙 심각도 3단계(정보 등급)와 규칙별 조치 안내를 `rules/*.yaml` 에 추가하고, 규칙 관리 화면에서 활성화 여부를 편집
- 파일럿에서 회수한 submission.json 을 모아 보는 중앙용 화면
