# 재현과 빌드

## 환경

| 구성 | 요구 사항 |
|---|---|
| Python 파이프라인 (`spec/`, `rules/`, `synth/`, `dq/`) | Python 3.10 이상, `pandas`, `numpy`, `pyyaml`, `duckdb`, `openpyxl` |
| TypeScript 엔진 (`dq-ts/`) | Node.js 20 이상 |
| 데스크톱 앱 (`app/`) | Node.js 20 이상. Windows 설치 파일은 Windows에서, macOS DMG는 macOS에서 빌드 |

```bash
pip install pandas numpy pyyaml duckdb openpyxl
```

Windows에서는 `PYTHONIOENCODING=utf-8`을 권장합니다.

## 전체 파이프라인 재현

```bash
python rules/generate_structural_rules.py    # 명세 → 구조 규칙
python dq/run_all.py                         # 6개 코호트: 생성 → 검증(clean) → 오류 주입 → 검증(dirty) → 성능 평가
```

`run_all.py`는 코호트마다 시드를 고정하므로(20260907 + 코호트 순번) 결과가 재현됩니다. 실행 후 `synth/output/`과 `dq/reports/`가 저장소에 든 것과 같은 내용으로 다시 만들어집니다.

명세 자체를 다시 만드는 `spec/build_spec.py`는 원본 데이터 사전(엑셀)을 파싱한 JSON을 입력으로 받습니다. 원본 사전은 공개 저장소에 포함되지 않으므로, 공개 저장소에서는 생성된 `spec/*.yaml`을 그대로 사용합니다.

### 개별 실행

```bash
python synth/generate.py --cohort LUNG_CANCER --n 100 --seed 20260907
python dq/engine.py --cohort LUNG_CANCER --data synth/output/clean/LUNG_CANCER --out dq/reports/clean_LUNG_CANCER --today 2026-09-07
python synth/inject_faults.py --cohort LUNG_CANCER --k 3
python dq/engine.py --cohort LUNG_CANCER --data synth/output/dirty/LUNG_CANCER --out dq/reports/dirty_LUNG_CANCER --today 2026-09-07
python dq/verify.py --cohort LUNG_CANCER
```

## TypeScript 엔진

```bash
cd dq-ts
npm install
npm run engine -- --cohort LUNG_CANCER --data ../synth/output/clean/LUNG_CANCER --out output/reports/clean_LUNG_CANCER --today 2026-09-07
npm run run-all      # 12회 실행 → 검출 성능 평가 → Python 참조와 비교
npm test             # 단위 시험 + 위 전체 실행
```

`npm test`는 저장소에 포함된 `synth/output/`과 `dq/reports/`를 읽습니다. Python 파이프라인을 다시 돌린 뒤라면 두 구현이 같은 데이터를 보고 있는지 확인하세요.

## 데스크톱 앱

```bash
cd app
npm install                      # Electron 바이너리가 안 풀리면: node node_modules/electron/install.js
npm run dev                      # 개발 모드 (핫 리로드)
npm run typecheck
npm run build && npm run smoke   # 빌드 후 자동 점검 (KAI_SMOKE_OUT 으로 캡처 위치 지정)
npm run dist:mac                 # macOS DMG (macOS 에서)
npm run dist:win                 # Windows 설치 파일 (Windows 에서)
```

- 개발 모드에서는 명세 위치가 저장소 루트이고, 실행 이력은 OS의 앱 데이터 폴더(`~/Library/Application Support/kai-quality-validator` 또는 `%APPDATA%`)에 저장됩니다.
- 설치본은 `spec/`, `rules/` YAML과 `synth/output/clean` 견본 데이터를 `resources/kai/`에 내장합니다.
- DuckDB는 네이티브 모듈이라 `asarUnpack`으로 풀어 둡니다.

## CI와 릴리스

`.github/workflows/ci.yml`은 push와 pull request마다 TypeScript 엔진의 회귀 시험(`dq-ts`의 `npm test`)과 앱의 타입 검사·빌드를 실행합니다.

`.github/workflows/release.yml`은 `v*` 태그를 push하면 Windows 러너에서 설치 파일(.exe), macOS 러너에서 DMG를 빌드해 GitHub Release에 첨부합니다.

```bash
git tag v0.1.0 && git push origin v0.1.0
```

코드 서명(Windows 인증서, Apple 공증)은 아직 설정하지 않았습니다. 서명 없이 배포하면 Windows SmartScreen과 macOS Gatekeeper 경고가 뜨며, 사용자 설명서의 설치 절에 우회 방법을 안내합니다. 서명을 넣으려면 인증서를 GitHub Secrets에 등록하고 `release.yml`의 환경 변수(`CSC_LINK`, `CSC_KEY_PASSWORD`, Apple의 `APPLE_ID`, `APPLE_APP_SPECIFIC_PASSWORD`, `APPLE_TEAM_ID`)를 채웁니다.
