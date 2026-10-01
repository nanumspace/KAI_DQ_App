# K-AI 코호트 데이터 품질검증 (Quality Validator)

폐암, 유방암, 대장암, 대사이상지방간(MASLD), 당뇨병, 림프종 6개 질환 코호트 데이터베이스의 **데이터 품질검증 프로그램**입니다. 병원 담당자가 EHR 추출본과 채운 서식을 넣고 실행하면, 명세 적합성·완전성·타당성 규칙 1,078개(코호트마다 341~531개 적용)를 검사해 보고서와 중앙 제출용 집계를 만듭니다. 병원 DB에 접속하지 않고 네트워크 통신도 하지 않습니다.

소개 페이지: **https://nanumspace.github.io/KAI_DQ_App/** (기능, 사용 흐름, 화면, 다운로드)

저장소에는 병원 데이터가 없습니다. 검증 프로그램의 개발과 시험에는 같은 명세에서 만든 **가상데이터**만 사용했습니다.

## 데이터 모델 (v2)

저장 구조는 **OMOP CDM 5.4 + Oncology 확장(EPISODE)** 표 14개에 **K-AI 확장 표** 16개를 더한 것입니다(표 30개, 필드 547개). concept_id 는 K-AI 자체 어휘(`spec/v2/vocab/`)를 쓰며 SNOMED CT·LOINC·MedDRA·EDI·KCD 등 표준과의 대응을 함께 적습니다.

병원이 준비하는 것은 두 가지입니다. **EHR 추출본**(환자·방문·진단·처치·약물·검사·관찰·기록·검체·사망)은 정보시스템에서 그대로 뽑고, **서식** 24종(병리 보고서·바이오마커·병기·수술·항암·이상사례·가족력과 질환별 검사·평가)은 담당자가 채웁니다. 앱이 서식을 저장 레코드로 바꾸고, 둘을 합쳐 검증합니다.

이전 명세 **v1**(질환별 단일 표 16개, 규칙 1,196개)은 앱의 설정에서 고를 수 있으며 이미 낸 제출본을 다시 볼 때 씁니다. 재설계의 근거와 전환 기록은 [`spec/v2/README.md`](spec/v2/README.md)에 있습니다.

현재 앱의 기본은 의뢰사 2026-09-30 매뉴얼에 10/1 검토 결정을 반영한 **v3**(표 17개 · 필드 169개 · 구조 규칙 367개 + 교차 규칙 22개)입니다. 질환별 단일 표 모양이라 엔진은 v1 경로를 파일만 바꿔 씁니다. 내용과 한계는 [`spec/v3/README.md`](spec/v3/README.md)에 있습니다. 위 v2 모델은 설정에서 고를 수 있고, 앱의 `v1`은 구 명세입니다. 매뉴얼 수정 제안과 의뢰사 질문은 [검토 웹서비스](review/README.md)에서 결정합니다.

## 무엇이 들어 있나

| 구성 | 위치 | 내용 |
|---|---|---|
| 데스크톱 앱 | `app/` | Electron + React. 병원 담당자가 쓰는 프로그램. Windows 11과 macOS |
| 검증 엔진 (TypeScript) | `dq-ts/` | 앱에 내장되는 엔진과 서식→레코드 변환기. Python 참조 구현과 동등성이 회귀 시험으로 고정됨 |
| 검증 엔진 (Python 참조 구현) | `dq/` | 규칙 의미의 기준. 검출 성능 평가 도구 포함 |
| 기계 판독 명세 | `spec/v2/` | 표 30개 · 필드 547개 명세, 서식 24종, 값 집합·어휘, 코호트 구성. `spec/` 에는 v1 |
| 기계 판독 명세 (v3, 기본) | `spec/v3/` | 의뢰사 9/30 매뉴얼 수정안: 표 17개 · 필드 169개, 구조 규칙 367개 + 교차 규칙 22개(`rules/*_v3.yaml`) |
| 검증 규칙 카탈로그 | `rules/` | 구조 규칙 1,038개(명세에서 자동 생성) + 교차 테이블 SQL 규칙 40개. `*_v2.yaml` |
| 가상데이터 생성기 | `synth/` | 질환별 환자 여정 시나리오, 규칙에서 오류 유형을 뽑는 주입기, 생성된 clean/dirty 데이터 |
| 문서 | `docs/` | 설계 원칙, 명세와 규칙, 가상데이터, 엔진과 검출 성능, 재현 방법 |
| 사용자 설명서 | `manual/` | 병원 담당자용 설치·입력·서식 변환·실행·출력물 안내 |
| 파일럿 키트 | `pilot/` | 파일럿 안내서, 피드백 양식, 중앙용 submission 집계 도구 |
| 매뉴얼 수정 제안·의뢰사 질문 검토 서비스 | `review/`, `spec/client_v1/` | 9월 30일 매뉴얼의 수정 제안과 의뢰사 확인 질문을 브라우저에서 결정하고 수정 제안서(.md)를 내보내는 로컬 서비스. 결정 결과가 v3 명세의 입력이다 |

## 빠른 시작

**병원 담당자**는 [Releases](../../releases)에서 설치 파일을 받아 [사용자 설명서](manual/README.md)를 따릅니다. 같은 페이지의 견본 데이터 zip(가상데이터, clean/dirty)으로 앱 동작을 먼저 확인할 수 있습니다.

**개발자**는 다음으로 앱을 개발 모드로 띄웁니다.

```bash
cd app && npm install && npm run dev
```

엔진만 명령줄로 실행하려면 표를 `<TABLE>.csv`로 한 폴더에 두고 다음을 실행합니다.

```bash
cd dq-ts && npm install
npm run engine -- --spec v2 --cohort LUNG_CANCER --data <csv 폴더> --out <출력 폴더>
```

전체 파이프라인(명세 → 규칙 → 가상데이터 → 검증 → 성능 평가)을 재현하는 방법은 [docs/reproduce.md](docs/reproduce.md)에 있습니다(`--spec v2`).

## 검출 성능

가상데이터 6개 코호트(질환당 100명)에서 clean 데이터 오탐 0건, 오류를 주입한 dirty 데이터의 주입 오류 601건 전부 검출(재현율 1.00)입니다. 질환당 2,000명(행 50만) 규모에서도 오탐 0건이며 코호트당 3초 안팎이 걸립니다. 이 값은 프로그램이 규칙을 정확히 구현했다는 증거이며, 실제 병원 데이터의 품질이나 오탐률에 대한 예측이 아닙니다. 실데이터에서 규칙이 어떻게 우는지는 파일럿이 답합니다.

앱은 병원 내보내기 도구의 흔적(BOM, EUC-KR, 대문자 컬럼명, `NULL` 글자, `100001.0`, `2022-01-01 00:00:00`, 세미콜론 구분자, 빈 끝 컬럼)을 검증 전에 걷어 내고 무엇을 걷어 냈는지 보고서에 적습니다. 그 시험은 `app/test/realworld.test.ts` 에 있습니다.

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

USB 토큰을 꽂고, 변경 사항을 모두 커밋한 뒤 main 브랜치에서 실행합니다. 산출물은 `QualityValidator-<버전>-mac-arm64.dmg`, `QualityValidator-<버전>-win-x64.exe`, `QualityValidator-<버전>-win-arm64.exe`, 견본 데이터 `SampleData-<버전>-*.zip`(13개, v2), `SHA256SUMS.txt` 입니다. 자세한 동작은 [docs/reproduce.md](docs/reproduce.md)에 있습니다.

## 문서

- [spec/v2/README.md](spec/v2/README.md) v2 데이터 모델, 값 집합과 표준 대응, 전환 기록
- [docs/overview.md](docs/overview.md) 배경, 설계 원칙, 5단계 계획
- [docs/spec-and-rules.md](docs/spec-and-rules.md) 명세 속성, 규칙 카탈로그
- [docs/synthetic-data.md](docs/synthetic-data.md) 생성 프레임워크, 시나리오, 오류 주입
- [docs/engine.md](docs/engine.md) 엔진 세 층, 검출 성능, 앱 구조
- [docs/reproduce.md](docs/reproduce.md) 환경, 파이프라인 재현, 앱 빌드와 배포
- [manual/README.md](manual/README.md) 사용자 설명서
- [pilot/README.md](pilot/README.md) 파일럿 키트
- [review/README.md](review/README.md) 매뉴얼 수정 제안·의뢰사 질문 검토 서비스 사용법
- [CONTRIBUTING.md](CONTRIBUTING.md) 규칙 추가와 시험 방법
