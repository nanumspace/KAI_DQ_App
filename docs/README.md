# 문서 목차

이 폴더는 프로젝트의 공개 설계 문서입니다. 병원 담당자용 사용 안내는 [`../manual/`](../manual/README.md)에 따로 있습니다.

| 문서 | 내용 |
|---|---|
| [overview.md](overview.md) | 배경, 코호트 DB 구조, 설계 원칙 세 가지, 5단계 계획과 현재 상태 |
| [spec-and-rules.md](spec-and-rules.md) | 기계 판독 명세의 속성, 특화 테이블의 이벤트 그룹 행 단위, 규칙 카탈로그 1,196개 |
| [synthetic-data.md](synthetic-data.md) | 가상데이터 생성 프레임워크, 질환별 환자 여정 시나리오, 오류 주입과 정답 manifest |
| [engine.md](engine.md) | 검증 엔진 세 층(Python · TypeScript · 앱), 검출 성능과 해석의 한계, 앱 구조 |
| [reproduce.md](reproduce.md) | 환경 준비, 전체 파이프라인 재현, 앱 개발·빌드·배포, CI |

각 하위 폴더의 README(`app/README.md`, `dq-ts/README.md`)는 그 구성 요소의 세부 사항을 다룹니다.
