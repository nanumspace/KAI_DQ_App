# 매뉴얼 수정 제안 · 의뢰사 확인 질문 웹서비스

`raw/매뉴얼_질환별 데이터 테이블_20260930.xlsx`를 DQ가 가능한 구조로 만들기 위한 **매뉴얼 수정 제안**과, 그 제안이 필요한지 정하는 **의뢰사 확인 질문**을 결정하는 로컬 웹서비스입니다. 제안과 질문의 정의는 `review/proposals.py`에 있으며, 서버가 시작할 때 각 제안의 현재 매뉴얼 행을 엑셀에서 다시 읽어 대조합니다(불일치 시 화면 상단 경고).

## 실행

Python 3와 `openpyxl`이 필요합니다. 저장소 루트에서:

```bash
python3 -m pip install -r spec/requirements.txt
python3 review/server.py
```

`http://127.0.0.1:8765/`를 엽니다. 포트·DB 지정: `python3 review/server.py --port 8766 --db /path/to/reviews.sqlite`. 기본 DB는 사용자 홈의 앱 데이터 폴더(macOS: `~/Library/Application Support/KAI_DQ_Review/review.db`)에 저장됩니다. 서버는 로컬 주소에만 바인딩됩니다. 환자 데이터는 입력하지 않습니다.

## 사용 방법

1. **의뢰사 확인 질문(Q01–Q11)에 답합니다.** 질문마다 왜 필요한지와 각 답의 결과가 적혀 있습니다. 모르면 ‘아직 모름(보류)’을 고르고 의뢰사에 확인합니다. 이전 검토 화면에서 남긴 답이 있으면 참고로 표시되지만 자동 반영하지 않습니다.
2. **답에 따라 각 수정 제안(C01–C18)의 필요 여부가 자동 표시됩니다.** `필요` / `불필요` / `질문 답 대기` / `항상 권장`.
3. **제안마다 채택·채택 안 함·보류를 정합니다.** 화면에 현재 매뉴얼 행(원본 그대로), 제안 문구, 이유, 예시가 나란히 표시됩니다.
4. 질문 답과 어긋나는 결정(필요 없는 제안 채택, 필요한 제안 미채택)은 **모순**으로 표시되고 요약·목록·내보내기에 남습니다. 질문 답을 바꾸면 모든 제안의 필요 여부와 모순이 다시 계산됩니다.
5. **‘수정 제안서(.md)’**를 내려받아 의뢰사에 전달합니다. 질문·답, 제안별 현재/제안 문구·이유·예시·결정·모순이 들어 있습니다. CSV·JSON은 같은 내용을 표 형태로 담습니다.

## 제안의 근거

- 종양 항목은 [OHDSI Oncology Conventions](https://ohdsi.github.io/OncologyWG/conventions.html)를 따릅니다: 조직형은 진단 CONDITION의 ICD-O-3 개념, 병기는 AJCC 판수가 포함된 Cancer Modifier 개념.
- 사건 연결(`*_event_id`)과 항암요법(`EPISODE`/`EPISODE_EVENT`)은 [OMOP CDM 5.4 표준](https://ohdsi.github.io/CommonDataModel/cdm54Changes.html) 구조를 씁니다. 새 연결표를 설계하지 않습니다.
- 제안 속 OMOP concept ID 예시(예: 방문 9202)는 Q01의 Athena 판본에서 최종 확인해야 합니다. 저장소에는 Athena 어휘가 없어 숫자를 검증하지 않았습니다(`spec/v2/vocab/CONCEPT.csv`는 프로젝트 자체 어휘).

이 서비스는 결정을 기록할 뿐 **원본 엑셀이나 DQ 규칙을 자동으로 바꾸지 않습니다.** 공개 네트워크에 포트를 열지 마세요.
