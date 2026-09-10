# 가상데이터

검증 프로그램의 개발과 시험에 쓰는 데이터는 모두 가상데이터입니다. 저장소의 `synth/output/`에 들어 있는 CSV는 실제 환자와 무관하며, 같은 시드로 다시 생성하면 같은 내용이 나옵니다.

## 생성 프레임워크 (`synth/framework.py`)

- 명세에서 테이블과 컬럼을 읽어 코호트별 `<TABLE>.csv`를 씁니다 (UTF-8, 헤더 포함, NULL은 빈 문자열, 날짜 ISO 8601).
- numpy 시드 기반이라 같은 시드면 같은 데이터가 나옵니다.
- `Ctx` 헬퍼(person, visit, condition, procedure, measure, labs, observation, note, drug, antp, ae, disease_row 등)가 규칙을 **구성상** 만족하도록 강제합니다. 모든 이벤트는 방문 안에서 발생하고, 사망 이후 이벤트는 만들어지지 않으며, 약물 종료일은 시작일 + days_supply − 1, 항암요법 시작/종료일은 연결 약물의 최소/최대, 특화 테이블은 이벤트 그룹 단위 1행이며 환자 불변 필드는 자동 복사됩니다.
- 대표 concept(진단, 약물, 검사, 처치, 이상사례)은 `spec/concepts.yaml`에서 가져옵니다. concept id는 OMOP 대표값이며 병원 적용 전 Athena 대조가 필요합니다.

## 질환별 환자 여정 시나리오 (`synth/scenarios/`)

| 시나리오 | 여정 개요 |
|---|---|
| lung.py | 진단 입원(CT, 기관지내시경 생검, PET, NGS/PD-L1) → 병기별 치료(I~II 폐엽절제 + 보조항암, III 동시항암방사선 60 Gy/30 fx, IV EGFR+ osimertinib 또는 pembrolizumab 병용, 진행 시 docetaxel) → 사이클별 CBC/신장/간기능과 CTCAE 이상사례 → 3개월 추적 CT, 재발, 사망 |
| breast.py | 유방촬영(밀도, BI-RADS), 코어 생검, IHC(ER/PR/HER2/Ki-67), FISH, 산과력, BRCA, Oncotype → 아형별 치료(DCIS, HR+, HER2+ TCH 선행, TNBC AC-T) → 수술(BCS/유방절제, 감시림프절), 외과병리(ypTNM), 방사선 50 Gy/25 fx, 내분비 치료 line → 전이/재발, 치료 후 월경·임신 |
| colorectal.py | 대장내시경 생검, CT, 직장암 MRI(MRF 거리, EMVI, 항문연 거리), CEA, MMR IHC, KRAS/NRAS/BRAF/MSI → 직장암 II~III 선행 CCRT 50.4 Gy + capecitabine → 결장절제/LAR/APR(장루, 개복 전환, IMA 결찰, 문합, EBL), 외과병리(TME 등급, 림프절), 장루 복원 → FOLFOX/CAPOX 보조, 전이 FOLFOX/FOLFIRI + bevacizumab → 6개월 추적 |
| masld.py | 복부초음파, 진단, 심장대사 동반질환, 체성분, 생활습관(음주 임계 미만) → FIB-4/APRI/BARD 점수(같은 날 AST/ALT/혈소판 MEASUREMENT와 일치), 간탄성도(F0~F4), 간생검 → 약물(metformin, SGLT2, pioglitazone, semaglutide, statin) 반복 처방과 이상사례 → 6개월 추적, 간경변 진행, 간이식, 사망 |
| diabetes.py | T2DM 진단, 동반질환, HbA1c/혈당/지질/신장기능/혈압/체성분, 안저검사 → 분기별 외래(HbA1c 매 방문), 단계적 약물 강화, 90일 리필 → CKD/IHD 합병증, 저혈당 이상사례(응급실) → DIABETES 특화 테이블은 핵심 이벤트를 1:1로 미러링 |
| lymphoma.py | 림프절 절제 생검, 아형별 IHC, FISH(double-hit), PET-CT 병기(Lugano, B 증상, bulky), 골수검사, IPI/FLIPI/MIPI/IPS → R-CHOP/ABVD/R-CVP/CHOP, 중간·종료 PET(Deauville), 방사선 → 재발/불응 30%: R-GDP 구제, 자가이식, CAR-T(성분채집 ≤ 전처치 ≤ 주입), 전환, 사망 → 최종 추적 행 |

폐암 시나리오를 먼저 작성해 프레임워크를 확정하고, 나머지 5개는 같은 규격으로 작성한 뒤 각각 엔진에서 위반 0건을 확인했습니다.

## clean 데이터 (질환당 100명)

| 코호트 | 방문 | 처치 | 약물 | 진단 | 검사 | 관찰 | 노트 | 특화 | 이상사례 | 항암 |
|---|---|---|---|---|---|---|---|---|---|---|
| LUNG_CANCER | 1,867 | 1,000 | 1,361 | 514 | 7,363 | 200 | 414 | 2,082 | 255 | 130 |
| BREAST_CANCER | 3,366 | 1,326 | 2,354 | 387 | 8,348 | 100 | 560 | 5,121 | 247 | 177 |
| COLORECTAL_CANCER | 2,603 | 1,129 | 2,030 | 499 | 7,813 | 111 | 847 | 5,924 | 324 | 97 |
| MASLD | 1,386 | 301 | 2,422 | 320 | 10,742 | 894 | 446 | 8,324 | 15 | — |
| DIABETES | 1,684 | 450 | 4,293 | 276 | 13,235 | 100 | 1,822 | 21,875 | 19 | — |
| LYMPHOMA | 2,163 | 1,396 | 2,855 | 440 | 7,802 | 100 | 520 | 2,305 | 291 | 133 |

## dirty 데이터와 정답 manifest (`synth/inject_faults.py`)

clean 데이터에 오류 유형 30여 종을 각 2~3건씩 주입하고, 오류마다 잡아야 할 규칙 id를 `fault_manifest.csv`(fault_id, fault_type, category, table, pk, person_id, field, original, injected, expected_rules)에 기록합니다.

| 분류 | 주입 유형 |
|---|---|
| 구조 | 필수값 NULL, PK 중복, FK 고아, 날짜/숫자 형식 오류, 코드표 밖 값, 범위 밖 값, 패턴 불일치, 그룹 anchor 누락, 환자 불변 필드 불일치, 미래 날짜, 컬럼 누락/추가/별칭 |
| 의미 (공통) | 방문 종료일 < 시작일, 사망 후 이벤트, 이벤트-방문 환자 불일치, 약물 종료 < 시작, 검사값 모두 NULL, age_at_index 불일치, 이상사례가 항암 시작 전, line 번호 건너뜀, 검사값 타당 범위 밖, 특화 death_date 불일치, 중복 진단, 코호트 정의 진단 삭제, 중대 AE 불완전, 투여빈도 있으나 days_supply 없음, 비항암 코호트 antp_id |
| 질환별 | BMI·방사선 총선량·TNM 조합·외과병리일 불일치, 폐암 종양 크기 vs T 병기와 흡연 논리, 유방암/대장암 양성 림프절 > 절제, 폐경 논리, 개복 전환 사유, 판독일 < 검사일, MASLD FIB-4·나이·음주, 당뇨 특화-핵심 불일치·방문 유형·약물 불일치, 림프종 IPI·B 증상·생존 상태·치료 line·Deauville |

## 저장소에 포함된 데이터

`synth/output/clean/`과 `synth/output/dirty/`를 모두 저장소에 포함합니다. clean은 앱 설치본의 견본 데이터로 빌드에 필요하고, dirty와 manifest는 TypeScript 엔진의 회귀 시험(`dq-ts`의 `npm test`)이 읽습니다. 다시 만들려면 [reproduce.md](reproduce.md)를 보세요.
