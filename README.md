# K-AI 코호트 데이터 품질검증 (Quality Validator)

폐암, 유방암, 대장암, 대사이상지방간(MASLD), 당뇨병, 림프종 6개 질환 코호트 데이터베이스의 **데이터 품질검증 프로그램**입니다. 병원 담당자가 자기 병원의 코호트 테이블 파일을 넣고 실행하면, 명세 적합성·완전성·타당성 규칙 1,196개를 검사해 보고서와 중앙 제출용 집계를 만듭니다. 병원 DB에 접속하지 않고 네트워크 통신도 하지 않습니다.

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
