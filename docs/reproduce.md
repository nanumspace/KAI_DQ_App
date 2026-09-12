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

## 사전 v2 (재설계 초안)

`spec/v2/` 는 전문가 자문을 반영해 재설계한 데이터 모델 초안입니다(한 테이블 = 행 단위 하나, 코어 단일 원천, 코드표 + 표준 매핑). 원천은 비공개 배치표와 `spec/v2_field_names.py` 이며, `spec/build_spec_v2.py` 가 명세·코드표·파생 변수·팀 배포용 사전·보고서를 재생성합니다. 자세한 구조는 `spec/v2/README.md` 에 있습니다. 규칙·가상데이터·앱은 아직 v1 명세를 읽습니다.

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
- 앱 아이콘은 `app/build/icon.svg`(원본)와 `app/build/icon.png`(1024×1024)입니다. electron-builder가 PNG를 macOS icns와 Windows ico로 변환합니다. SVG를 고치면 `qlmanage -t -s 1024 -o app/build app/build/icon.svg && mv app/build/icon.svg.png app/build/icon.png`으로 다시 만듭니다.

## CI

`.github/workflows/ci.yml`은 push와 pull request마다 TypeScript 엔진의 회귀 시험(`dq-ts`의 `npm test`)과 앱의 타입 검사·빌드를 실행합니다.

## 소개 페이지 (GitHub Pages)

`docs/index.html` 한 파일(인라인 CSS·JS, 한/영 전환, 라이트/다크)과 `docs/img/` 캡처가 소개 페이지입니다. `docs/` 아래가 바뀌어 main 에 push 되면 `.github/workflows/deploy-pages.yml` 이 https://nanumspace.github.io/KAI_DQ_App/ 에 배포합니다. 다운로드 단추는 GitHub 의 최신 Release 를 읽어 파일 이름과 링크를 스스로 갱신하므로, 새 버전을 릴리스해도 페이지를 고칠 필요가 없습니다. 캡처는 `internal/presentations/img/` 원본을 1600px JPEG 로 줄인 것입니다.

## 릴리스 (`release.sh`)

서명에 USB 토큰과 키체인이 필요하므로 릴리스는 GitHub Actions 가 아니라 개발자의 macOS 에서 `release.sh` 로 합니다. 사용법은 루트 README 의 릴리스 절에 있습니다. 스크립트가 하는 일은 다음 순서입니다.

| 단계 | 내용 |
|---|---|
| 사전 점검 | 토큰 인식과 PIN 로그인, Developer ID 인증서, 공증 프로필, GitHub 로그인, main 브랜치, 커밋되지 않은 변경 없음, 같은 태그 없음 |
| 버전 | 인자로 버전을 주면 `app/package.json`(과 `dq-ts`)의 버전을 올리고 커밋 |
| 빌드 준비 | 타입 검사, `electron-vite build`. 빌드 대상 플랫폼의 DuckDB 바이너리만 `node_modules/@duckdb/` 에 남기고 나머지는 잠시 치움 (Windows 바이너리는 npm 레지스트리에서 받아 `~/Library/Caches/kai-release/` 에 보관) |
| macOS | `electron-builder --mac --arm64`. hardened runtime 으로 Developer ID 서명, 앱 공증과 staple 은 electron-builder 가 `APPLE_KEYCHAIN_PROFILE` 로 수행. 이어서 DMG 자체를 `notarytool` 로 공증하고 staple (오프라인 PC 에서도 경고 없이 열리도록) |
| Windows | x64, arm64 각각 `electron-builder --win`. exe 마다 `app/build/sign-win.cjs` 훅이 `osslsigncode` 로 토큰 서명 (PKCS#11 은 OpenSC 모듈, 중간 인증서 `app/build/globalsign-ev-codesigning-ca-2020.pem` 첨부, RFC 3161 타임스탬프) |
| 견본 데이터 | `app/build/pack-samples.cjs` 가 `synth/output/` 의 clean/dirty 를 코호트별 zip 12개와 전체 묶음 1개로 만듦. 각 zip 에 CSV, 시트당 테이블 엑셀, (dirty) `fault_manifest.csv`, 기대 결과를 적은 README.txt |
| 검증 | `osslsigncode verify`, `spctl -a -t open`, `xcrun stapler validate`, `SHA256SUMS.txt` (설치 파일과 견본 zip) |
| 게시 | 태그 `v<버전>` 생성과 push, `gh release create` 로 DMG·exe·SHA256SUMS 첨부. `--replace` 를 주면 같은 버전의 기존 Release 와 태그를 지우고 다시 게시 |

Windows 32비트(x86)는 만들지 않습니다. DuckDB Node 바인딩이 Windows 는 x64 와 arm64 만 제공하고, Windows 11 은 64비트 전용입니다.

환경 변수로 바꿀 수 있는 값: `KAI_NOTARY_PROFILE`(기본 kai-notary), `KAI_PIN_SERVICE`(기본 kai-safenet-pin), `KAI_PKCS11_MODULE`(기본 `/opt/homebrew/lib/opensc-pkcs11.so`), `KAI_TSA_URL`(기본 `http://timestamp.digicert.com`).
