# K-AI 코호트 데이터 품질검증 (Quality Validator)

폐암, 유방암, 대장암, 대사이상지방간(MASLD), 당뇨병, 림프종 6개 질환 코호트 데이터베이스의 **데이터 품질검증 프로그램**입니다. 병원 담당자가 자기 병원의 코호트 테이블 파일을 넣고 실행하면, 명세 적합성·완전성·타당성 규칙 1,196개를 검사해 보고서와 중앙 제출용 집계를 만듭니다. 병원 DB에 접속하지 않고 네트워크 통신도 하지 않습니다.

소개 페이지: **https://nanumspace.github.io/KAI_DQ_App/** (기능, 사용 흐름, 화면, 다운로드)

저장소에는 병원 데이터가 없습니다. 검증 프로그램의 개발과 시험에는 같은 명세에서 만든 **가상데이터**만 사용했습니다.

## 무엇이 들어 있나

| 구성 | 위치 | 내용 |
|---|---|---|
| 데스크톱 앱 | `app/` | Electron + React. 병원 담당자가 쓰는 프로그램. Windows 11과 macOS |
| 검증 엔진 (TypeScript) | `dq-ts/` | 앱에 내장되는 엔진. Python 참조 구현과 동등성이 회귀 시험으로 고정됨 |
| 검증 엔진 (Python 참조 구현) | `dq/` | 규칙 의미의 기준. 검출 성능 평가 도구 포함 |
| 기계 판독 명세 | `spec/` | 16 테이블 · 1,105 필드 명세, 코드표, 코호트 구성, 대표 concept |
| 검증 규칙 카탈로그 | `rules/` | 구조 규칙 1,121개(명세에서 자동 생성) + 교차 테이블 SQL 규칙 75개 |
| 가상데이터 생성기 | `synth/` | 질환별 환자 여정 시나리오, 오류 주입기, 생성된 clean/dirty 데이터 |
| 문서 | `docs/` | 설계 원칙, 명세와 규칙, 가상데이터, 엔진과 검출 성능, 재현 방법 |
| 사용자 설명서 | `manual/` | 병원 담당자용 설치·입력·실행·출력물 안내 |

## 빠른 시작

**병원 담당자**는 [Releases](../../releases)에서 설치 파일을 받아 [사용자 설명서](manual/README.md)를 따릅니다.

**개발자**는 다음으로 앱을 개발 모드로 띄웁니다.

```bash
cd app && npm install && npm run dev
```

엔진만 명령줄로 실행하려면 코호트 테이블을 `<TABLE>.csv`로 한 폴더에 두고 다음을 실행합니다.

```bash
cd dq-ts && npm install
npm run engine -- --cohort LUNG_CANCER --data <csv 폴더> --out <출력 폴더>
```

전체 파이프라인(명세 → 규칙 → 가상데이터 → 검증 → 성능 평가)을 재현하는 방법은 [docs/reproduce.md](docs/reproduce.md)에 있습니다.

## 검출 성능

가상데이터 6개 코호트(질환당 100명)에서 clean 데이터 오탐 0건, 오류를 주입한 dirty 데이터의 주입 오류 622건 전부 검출(재현율 1.00)입니다. 이 값은 프로그램이 규칙을 정확히 구현했다는 증거이며, 실제 병원 데이터의 품질이나 오탐률에 대한 예측이 아닙니다. 자세한 표와 해석의 한계는 [docs/engine.md](docs/engine.md)에 있습니다.

## 릴리스 (빌드 · 서명 · 공증 · 배포)

저장소 루트의 `release.sh` 하나로 macOS DMG 와 Windows 설치 파일을 빌드하고, 코드 서명과 Apple 공증을 거쳐 GitHub Release 에 올립니다. macOS 에서 실행하며, Windows 서명은 SafeNet USB 토큰(GlobalSign EV 인증서)을, macOS 서명은 키체인의 Developer ID 인증서를 씁니다.

**한 번만 준비할 것**

```bash
brew install osslsigncode opensc gh
security add-generic-password -a "$USER" -s kai-safenet-pin -w          # 토큰 PIN (대화식 입력)
xcrun notarytool store-credentials kai-notary --apple-id <Apple ID> --team-id <Team ID>   # 앱 암호 입력
gh auth login
```

**릴리스할 때**

```bash
./release.sh 0.2.0            # 버전을 올리고(커밋) 빌드 → 서명 → 공증 → 검증 → 태그 → GitHub Release
./release.sh                  # package.json 의 현재 버전으로 릴리스
./release.sh --no-publish     # 빌드·서명·공증·검증까지만 (app/release/ 에 산출물)
./release.sh --publish-only   # 위 산출물로 태그와 Release 만
./release.sh --skip-win       # macOS 만 (또는 --skip-mac)
./release.sh --unsigned       # 서명·공증 없는 시험 빌드. 배포 금지
./release.sh --replace        # 같은 버전을 다시 게시 (기존 Release 와 태그 삭제 후)
```

USB 토큰을 꽂고, 변경 사항을 모두 커밋한 뒤 main 브랜치에서 실행합니다. 산출물은 `QualityValidator-<버전>-mac-arm64.dmg`, `QualityValidator-<버전>-win-x64.exe`, `QualityValidator-<버전>-win-arm64.exe`, `SHA256SUMS.txt` 입니다. 자세한 동작은 [docs/reproduce.md](docs/reproduce.md)에 있습니다.

## 문서

- [docs/overview.md](docs/overview.md) 배경, 코호트 DB 구조, 설계 원칙, 5단계 계획
- [docs/spec-and-rules.md](docs/spec-and-rules.md) 명세 속성, 이벤트 그룹 행 단위, 규칙 카탈로그
- [docs/synthetic-data.md](docs/synthetic-data.md) 생성 프레임워크, 시나리오, 오류 주입
- [docs/engine.md](docs/engine.md) 엔진 세 층, 검출 성능, 앱 구조
- [docs/reproduce.md](docs/reproduce.md) 환경, 파이프라인 재현, 앱 빌드와 배포
- [manual/README.md](manual/README.md) 사용자 설명서
- [CONTRIBUTING.md](CONTRIBUTING.md) 규칙 추가와 시험 방법

## 라이선스

Apache License 2.0. [LICENSE](LICENSE)를 보세요.
