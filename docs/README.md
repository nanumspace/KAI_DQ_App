# 문서 목차

이 폴더는 프로젝트의 공개 설계 문서입니다. 병원 담당자용 사용 안내는 [`../manual/`](../manual/README.md)에 따로 있습니다.

| 문서 | 내용 |
|---|---|
| [overview.md](overview.md) | 배경, 코호트 DB 구조, 설계 원칙 세 가지, 5단계 계획과 현재 상태 |
| [spec-and-rules.md](spec-and-rules.md) | 기계 판독 명세의 속성, 특화 테이블의 이벤트 그룹 행 단위, 규칙 카탈로그. 기본 판 v3(규칙 389개)과 이전 판 v2(1,078개)·v1(1,196개) |
| [synthetic-data.md](synthetic-data.md) | 가상데이터 생성 프레임워크, 질환별 환자 여정 시나리오, 오류 주입과 정답 manifest |
| [engine.md](engine.md) | 검증 엔진 세 층(Python · TypeScript · 앱), 검출 성능과 해석의 한계, 앱 구조 |
| [reproduce.md](reproduce.md) | 환경 준비, 전체 파이프라인 재현(v3 기본, v2·v1 은 `--spec`), 앱 개발·빌드·배포, CI |
| [`../spec/v3/README.md`](../spec/v3/README.md) | 기본 판 v3 명세의 출처·결정, 파일, 알려진 한계, 확인된 것 |
| [`../review/README.md`](../review/README.md) | 매뉴얼 수정 제안과 의뢰사 확인 질문을 정하는 검토 웹서비스. 결과가 v3 에 반영됩니다 |

`index.html`과 `img/`는 GitHub Pages 소개 페이지(https://nanumspace.github.io/KAI_DQ_App/)의 원본입니다. `docs/` 가 바뀌면 `.github/workflows/deploy-pages.yml` 이 자동으로 배포합니다.

`resources.html`은 자료실 페이지입니다. 코호트별 입력 양식(엑셀·CSV), 컬럼 명세서, 검증 규칙 목록, 견본 데이터 기대 결과를 담습니다. 이 페이지가 읽는 `docs/resources/` 는 저장소에 넣지 않습니다. 배포할 때 `python docs/build_resources.py` 가 기본 명세(`spec/v3/`)와 규칙(`rules/*_v3.yaml`), 견본 보고서 요약(`dq/reports/*_v3_*/summary.json`)에서 만듭니다. 그래서 명세나 규칙을 고치면 다음 배포에 저절로 반영됩니다. 생성기는 엔진과 같은 기준으로 코호트별 규칙 수를 세고, 그 수가 견본 보고서와 다르면 실패합니다. 의뢰사 원본 자료(`raw/`, `spec/client_v1/`)는 싣지 않습니다. 로컬에서 미리 보려면 `python docs/build_resources.py` 를 실행한 뒤 `python -m http.server --directory docs` 를 띄웁니다.

각 하위 폴더의 README(`app/README.md`, `dq-ts/README.md`)는 그 구성 요소의 세부 사항을 다룹니다.
