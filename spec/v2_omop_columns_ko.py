# -*- coding: utf-8 -*-
"""OMOP CDM 5.4 저장 컬럼의 한글 이름·설명·참조.

`spec/v2_omop_map.py` 의 OMOP_TABLES 는 컬럼 이름·타입·필수만 적고 설명은 드문드문 있었다.
사전(dictionary_v2.xlsx)의 '저장컬럼' 시트에서 OMOP 14개 표 128개 컬럼이 한글 없이 나오던 것을
여기서 채운다. 뜻은 OMOP CDM 5.4 규약을 따르되, K-AI 에서 어떻게 쓰는지(어느 어휘, 어느 서식이 채우는지)를 덧붙였다.

모양: (테이블, 컬럼) → dict(kor=한글 이름, desc=설명, ref=참조 'TABLE.column' 또는 None, vocab=값이 오는 어휘·값 집합 힌트 또는 None)
"""

# 여러 표에 같은 뜻으로 되풀이되는 컬럼
_PERSON_FK = dict(kor="환자 ID", desc="PERSON.person_id 참조. 같은 환자는 모든 표에서 같은 값", ref="PERSON.person_id", vocab=None)
_VISIT_FK = dict(kor="방문 ID", desc="이 사건이 일어난 방문. VISIT_OCCURRENCE.visit_occurrence_id 참조. 방문에 매달 수 없으면 비움", ref="VISIT_OCCURRENCE.visit_occurrence_id", vocab=None)
_TYPE = dict(kor="레코드 출처 type", desc="레코드가 어디서 왔는지. K-AI Type concept: 등록 서식 입력·전자의무기록·파생 중 하나", ref=None, vocab="K-AI Type (TYPE_REGISTRY · TYPE_EHR · TYPE_DERIVED)")
_UNIT = dict(kor="단위 concept", desc="값의 단위. UCUM 단위 concept", ref=None, vocab="UCUM")

OMOP_COLUMNS_KO = {
    # ---------------------------------------------------------------- PERSON
    ("PERSON", "person_id"): dict(kor="환자 ID", desc="환자 고유키(가명). 코호트 안에서 유일하며 모든 표가 이 값으로 환자를 가리킨다", ref=None, vocab=None),
    ("PERSON", "gender_concept_id"): dict(kor="성별 concept", desc="성별. OMOP Gender concept(남 8507 · 여 8532)", ref=None, vocab="OMOP Gender"),
    ("PERSON", "year_of_birth"): dict(kor="출생 연도", desc="출생 연도(YYYY). 나이 계산의 기준", ref=None, vocab=None),
    ("PERSON", "month_of_birth"): dict(kor="출생 월", desc="출생 월(1~12). 모르면 비움", ref=None, vocab=None),
    ("PERSON", "day_of_birth"): dict(kor="출생 일", desc="출생 일(1~31). 모르면 비움", ref=None, vocab=None),
    ("PERSON", "care_site_id"): dict(kor="기관 ID", desc="환자가 속한 기관(병원) 식별자. 기관 코드는 중앙이 부여", ref=None, vocab=None),
    ("PERSON", "gender_source_value"): dict(kor="성별 원천값", desc="병원 원천의 성별 표기(M/F 등)", ref=None, vocab=None),
    # ---------------------------------------------------------------- OBSERVATION_PERIOD
    ("OBSERVATION_PERIOD", "observation_period_id"): dict(kor="관찰기간 ID", desc="행 고유키", ref=None, vocab=None),
    ("OBSERVATION_PERIOD", "person_id"): _PERSON_FK,
    ("OBSERVATION_PERIOD", "observation_period_start_date"): dict(kor="관찰 시작일", desc="이 환자의 기록이 신뢰되는 기간의 시작. 코호트 진입일 또는 첫 방문일. 코호트 인덱스 서식이 만든다", ref=None, vocab=None),
    ("OBSERVATION_PERIOD", "observation_period_end_date"): dict(kor="관찰 종료일", desc="기록이 신뢰되는 기간의 끝. 최종 추적일 또는 사망일. 이 뒤의 사건은 '관찰기간 밖'으로 보고된다", ref=None, vocab=None),
    ("OBSERVATION_PERIOD", "period_type_concept_id"): _TYPE,
    # ---------------------------------------------------------------- DEATH
    ("DEATH", "person_id"): dict(kor="환자 ID", desc="PERSON.person_id 참조. 환자당 한 행", ref="PERSON.person_id", vocab=None),
    ("DEATH", "death_date"): dict(kor="사망일", desc="사망 일자. 이 뒤의 임상 사건은 '사망 이후 사건'으로 보고된다", ref=None, vocab=None),
    ("DEATH", "death_type_concept_id"): _TYPE,
    ("DEATH", "cause_concept_id"): dict(kor="사망 원인 concept", desc="사망 원인 진단 concept(K-AI 어휘, KCD/SNOMED 매핑). 모르면 비움", ref=None, vocab="K-AI 진단 concept (KCD·SNOMED)"),
    ("DEATH", "cause_source_value"): dict(kor="사망 원인 원천값", desc="병원 원천의 사망 원인 코드(KCD 등)·표기", ref=None, vocab=None),
    # ---------------------------------------------------------------- VISIT_OCCURRENCE
    ("VISIT_OCCURRENCE", "visit_occurrence_id"): dict(kor="방문 ID", desc="행 고유키", ref=None, vocab=None),
    ("VISIT_OCCURRENCE", "person_id"): _PERSON_FK,
    ("VISIT_OCCURRENCE", "visit_concept_id"): dict(kor="방문 종류 concept", desc="입원·외래·응급 중 하나. K-AI Visit concept", ref=None, vocab="K-AI Visit (VISIT_INPATIENT · VISIT_OUTPATIENT · VISIT_ER)"),
    ("VISIT_OCCURRENCE", "visit_start_date"): dict(kor="방문 시작일", desc="입원일 또는 외래·응급 방문일", ref=None, vocab=None),
    ("VISIT_OCCURRENCE", "visit_end_date"): dict(kor="방문 종료일", desc="퇴원일. 외래·응급은 방문일과 같다. 시작일보다 앞설 수 없다", ref=None, vocab=None),
    ("VISIT_OCCURRENCE", "visit_type_concept_id"): _TYPE,
    ("VISIT_OCCURRENCE", "discharge_to_concept_id"): dict(kor="퇴원 시 상태 concept", desc="퇴원 시 상태(호전·미호전·사망·전원·자의 퇴원·기타). 값 집합 DISCHARGE_STATUS", ref=None, vocab="DISCHARGE_STATUS"),
    ("VISIT_OCCURRENCE", "visit_source_value"): dict(kor="방문 원천값", desc="병원 원천의 방문 구분 표기(IP/OP/ER 등)", ref=None, vocab=None),
    # ---------------------------------------------------------------- CONDITION_OCCURRENCE
    ("CONDITION_OCCURRENCE", "condition_occurrence_id"): dict(kor="진단 ID", desc="행 고유키", ref=None, vocab=None),
    ("CONDITION_OCCURRENCE", "person_id"): _PERSON_FK,
    ("CONDITION_OCCURRENCE", "condition_concept_id"): dict(kor="진단 concept", desc="진단 개념. K-AI 어휘(KCD·SNOMED 매핑). 코호트 정의 진단은 코호트 인덱스 서식이, 이상사례는 이상사례 서식(MedDRA)이 만든다", ref=None, vocab="K-AI 진단 concept (KCD·SNOMED·MedDRA)"),
    ("CONDITION_OCCURRENCE", "condition_start_date"): dict(kor="진단일", desc="진단(또는 사건 발생)이 기록된 날", ref=None, vocab=None),
    ("CONDITION_OCCURRENCE", "condition_end_date"): dict(kor="진단 종료일", desc="해소된 진단의 종료일. 진행 중이면 비움", ref=None, vocab=None),
    ("CONDITION_OCCURRENCE", "condition_type_concept_id"): _TYPE,
    ("CONDITION_OCCURRENCE", "condition_status_concept_id"): dict(kor="진단 상태 concept", desc="주진단·과거력·합병증·이상사례 같은 진단의 성격. 이상사례 행은 AE_STATUS", ref=None, vocab="K-AI Condition Status"),
    ("CONDITION_OCCURRENCE", "visit_occurrence_id"): _VISIT_FK,
    ("CONDITION_OCCURRENCE", "condition_source_value"): dict(kor="진단 원천값", desc="병원 원천의 진단 코드(KCD)·MedDRA 용어·표기", ref=None, vocab=None),
    # ---------------------------------------------------------------- PROCEDURE_OCCURRENCE
    ("PROCEDURE_OCCURRENCE", "procedure_occurrence_id"): dict(kor="시술 ID", desc="행 고유키", ref=None, vocab=None),
    ("PROCEDURE_OCCURRENCE", "person_id"): _PERSON_FK,
    ("PROCEDURE_OCCURRENCE", "procedure_concept_id"): dict(kor="시술 concept", desc="시술·검사 시행 개념. K-AI 어휘(EDI 행위·SNOMED 매핑). 수술·방사선 서식이 행을 보탠다", ref=None, vocab="K-AI 시술 concept (EDI 행위·SNOMED)"),
    ("PROCEDURE_OCCURRENCE", "procedure_date"): dict(kor="시술일", desc="시술·검사를 시행한 날. 방사선 코스는 시작일", ref=None, vocab=None),
    ("PROCEDURE_OCCURRENCE", "procedure_end_date"): dict(kor="시술 종료일", desc="여러 날에 걸친 시술의 종료일(방사선 코스 등). 하루짜리는 비움", ref=None, vocab=None),
    ("PROCEDURE_OCCURRENCE", "procedure_type_concept_id"): _TYPE,
    ("PROCEDURE_OCCURRENCE", "modifier_concept_id"): dict(kor="시술 수식자 concept", desc="접근법(개복·복강경·로봇 등) 같은 시술 수식자. 값 집합 SURG_APPROACH", ref=None, vocab="SURG_APPROACH"),
    ("PROCEDURE_OCCURRENCE", "quantity"): dict(kor="횟수", desc="시행 횟수. 방사선은 분할 횟수", ref=None, vocab=None),
    ("PROCEDURE_OCCURRENCE", "visit_occurrence_id"): _VISIT_FK,
    ("PROCEDURE_OCCURRENCE", "procedure_source_value"): dict(kor="시술 원천값", desc="병원 원천의 시술 코드(EDI·원내)·명칭", ref=None, vocab=None),
    # ---------------------------------------------------------------- DRUG_EXPOSURE
    ("DRUG_EXPOSURE", "drug_exposure_id"): dict(kor="약물 노출 ID", desc="행 고유키", ref=None, vocab=None),
    ("DRUG_EXPOSURE", "person_id"): _PERSON_FK,
    ("DRUG_EXPOSURE", "drug_concept_id"): dict(kor="약물 concept", desc="약제(성분) 개념. K-AI 어휘(국내 약물코드·ATC 매핑). 항암제는 항암요법 에피소드에 EPISODE_EVENT 로 매달린다", ref=None, vocab="K-AI 약물 concept (EDI 약제·ATC)"),
    ("DRUG_EXPOSURE", "drug_exposure_start_date"): dict(kor="투약 시작일", desc="처방·투여 시작일", ref=None, vocab=None),
    ("DRUG_EXPOSURE", "drug_exposure_end_date"): dict(kor="투약 종료일", desc="투약 종료(예정)일. 시작일 + 처방일수 - 1 과 맞아야 한다. 진행 중 처방은 미래여도 된다", ref=None, vocab=None),
    ("DRUG_EXPOSURE", "drug_type_concept_id"): _TYPE,
    ("DRUG_EXPOSURE", "quantity"): dict(kor="1회 투여 용량", desc="처방된 1회 투여 용량(수치). 단위는 dose_unit_source_value", ref=None, vocab=None),
    ("DRUG_EXPOSURE", "days_supply"): dict(kor="처방일수", desc="처방 일수. 시작일·종료일과 맞아야 한다", ref=None, vocab=None),
    ("DRUG_EXPOSURE", "dose_unit_source_value"): dict(kor="용량 단위 원천값", desc="1회 투여 용량의 단위 표기(mg, IU 등)", ref=None, vocab=None),
    ("DRUG_EXPOSURE", "route_concept_id"): dict(kor="투여 경로 concept", desc="투여 경로(경구·정맥·피하 등). OMOP Route concept", ref=None, vocab="OMOP Route"),
    ("DRUG_EXPOSURE", "visit_occurrence_id"): _VISIT_FK,
    ("DRUG_EXPOSURE", "drug_source_value"): dict(kor="약물 원천값", desc="병원 원천의 약제 코드(EDI·원내)·명칭", ref=None, vocab=None),
    # ---------------------------------------------------------------- MEASUREMENT
    ("MEASUREMENT", "measurement_id"): dict(kor="검사 ID", desc="행 고유키", ref=None, vocab=None),
    ("MEASUREMENT", "person_id"): _PERSON_FK,
    ("MEASUREMENT", "measurement_concept_id"): dict(kor="검사 항목 concept", desc="무엇을 쟀는가. 검사(LOINC)·병기·반응·등급 같은 수식자(K-AI Attribute) concept. 병기·반응평가·방사선 서식이 행을 보탠다", ref=None, vocab="LOINC · K-AI Attribute (서식 필드 개념)"),
    ("MEASUREMENT", "measurement_date"): dict(kor="검사일", desc="검사·평가한 날", ref=None, vocab=None),
    ("MEASUREMENT", "measurement_type_concept_id"): _TYPE,
    ("MEASUREMENT", "operator_concept_id"): dict(kor="비교 연산자 concept", desc="값 앞의 부등호(<, >, ≤, ≥). 대부분 비움", ref=None, vocab="OMOP Meas Value Operator"),
    ("MEASUREMENT", "value_as_number"): dict(kor="수치 결과", desc="검사 결과가 수치일 때의 값. 단위는 unit_concept_id", ref=None, vocab=None),
    ("MEASUREMENT", "value_as_concept_id"): dict(kor="범주 결과 concept", desc="결과가 범주일 때의 값 concept(병기군·등급·반응·양성/음성 등). 값 집합은 measurement_concept_id 가 정한다", ref=None, vocab="값 집합의 Value concept"),
    ("MEASUREMENT", "unit_concept_id"): _UNIT,
    ("MEASUREMENT", "range_low"): dict(kor="참고범위 하한", desc="검사 참고범위의 하한. 병원 기준", ref=None, vocab=None),
    ("MEASUREMENT", "range_high"): dict(kor="참고범위 상한", desc="검사 참고범위의 상한. 병원 기준", ref=None, vocab=None),
    ("MEASUREMENT", "visit_occurrence_id"): _VISIT_FK,
    ("MEASUREMENT", "measurement_source_value"): dict(kor="검사 원천값", desc="병원 원천의 검사 코드·명칭", ref=None, vocab=None),
    ("MEASUREMENT", "value_source_value"): dict(kor="결과 원천값", desc="결과의 원천 표기(라벨·코드·문자열). 병기 'cT2aN2M1b' 처럼 원천 표기만 남는 항목도 있다", ref=None, vocab=None),
    ("MEASUREMENT", "measurement_event_id"): dict(kor="수식 대상 레코드 ID", desc="이 값이 무엇을 수식하는지(진단·에피소드·시술 레코드의 id). 어느 표인지는 meas_event_field_concept_id", ref=None, vocab=None),
    ("MEASUREMENT", "meas_event_field_concept_id"): dict(kor="수식 대상 표 concept", desc="measurement_event_id 가 가리키는 표·컬럼. K-AI Field concept(F_CONDITION, F_EPISODE, F_PROCEDURE …)", ref=None, vocab="K-AI Field (F_*)"),
    # ---------------------------------------------------------------- OBSERVATION
    ("OBSERVATION", "observation_id"): dict(kor="관찰 ID", desc="행 고유키", ref=None, vocab=None),
    ("OBSERVATION", "person_id"): _PERSON_FK,
    ("OBSERVATION", "observation_concept_id"): dict(kor="관찰 항목 concept", desc="무엇을 관찰했는가. 가족력·수술 목적·항암 의도 같은 서식 필드 개념(K-AI Attribute)이나 흡연·음주 같은 파생 변수 개념", ref=None, vocab="K-AI Attribute (서식 필드 개념)"),
    ("OBSERVATION", "observation_date"): dict(kor="관찰일", desc="관찰·기록한 날. 서식의 기준일", ref=None, vocab=None),
    ("OBSERVATION", "observation_type_concept_id"): _TYPE,
    ("OBSERVATION", "value_as_number"): dict(kor="수치 값", desc="관찰 값이 수치일 때(가족 진단 나이, 흡연량 등)", ref=None, vocab=None),
    ("OBSERVATION", "value_as_string"): dict(kor="문자 값", desc="관찰 값이 자유 문자열일 때(레지멘명 원천 표기 등)", ref=None, vocab=None),
    ("OBSERVATION", "value_as_concept_id"): dict(kor="범주 값 concept", desc="관찰 값이 범주일 때의 값 concept(가족 질환·수술 목적·예/아니오 등)", ref=None, vocab="값 집합의 Value concept"),
    ("OBSERVATION", "qualifier_concept_id"): dict(kor="한정자 concept", desc="값을 한정하는 개념. 가족력에서는 가족 관계(값 집합 FAMILY_RELATION)", ref=None, vocab="FAMILY_RELATION 등"),
    ("OBSERVATION", "unit_concept_id"): _UNIT,
    ("OBSERVATION", "visit_occurrence_id"): _VISIT_FK,
    ("OBSERVATION", "observation_source_value"): dict(kor="관찰 원천값", desc="병원 원천의 항목 표기", ref=None, vocab=None),
    ("OBSERVATION", "value_source_value"): dict(kor="값 원천값", desc="값의 원천 표기(서식에서 고른 코드·라벨)", ref=None, vocab=None),
    ("OBSERVATION", "observation_event_id"): dict(kor="관련 레코드 ID", desc="이 관찰이 속한 기준 레코드(에피소드·시술·진단)의 id. 어느 표인지는 obs_event_field_concept_id", ref=None, vocab=None),
    ("OBSERVATION", "obs_event_field_concept_id"): dict(kor="관련 표 concept", desc="observation_event_id 가 가리키는 표·컬럼. K-AI Field concept(F_EPISODE, F_PROCEDURE …)", ref=None, vocab="K-AI Field (F_*)"),
    # ---------------------------------------------------------------- NOTE
    ("NOTE", "note_id"): dict(kor="기록 ID", desc="행 고유키", ref=None, vocab=None),
    ("NOTE", "person_id"): _PERSON_FK,
    ("NOTE", "note_date"): dict(kor="기록일", desc="기록·판독문이 작성된 날", ref=None, vocab=None),
    ("NOTE", "note_type_concept_id"): _TYPE,
    ("NOTE", "note_class_concept_id"): dict(kor="기록 종류 concept", desc="판독문·병리 보고서·경과기록 같은 기록의 종류", ref=None, vocab="OMOP Note class"),
    ("NOTE", "note_title"): dict(kor="기록 제목", desc="기록의 제목. 없으면 비움", ref=None, vocab=None),
    ("NOTE", "note_text"): dict(kor="기록 본문", desc="기록의 전문. 자유 문자열. 개인정보 마스킹은 병원 책임", ref=None, vocab=None),
    ("NOTE", "encoding_concept_id"): dict(kor="인코딩 concept", desc="본문 인코딩. UTF-8(32678)", ref=None, vocab="OMOP Encoding"),
    ("NOTE", "language_concept_id"): dict(kor="언어 concept", desc="본문 언어. 한국어(4175771)·영어(4180186)", ref=None, vocab="OMOP Language"),
    ("NOTE", "visit_occurrence_id"): _VISIT_FK,
    ("NOTE", "note_event_id"): dict(kor="관련 레코드 ID", desc="기록이 붙는 레코드(검체·시술)의 id. 어느 표인지는 note_event_field_concept_id", ref=None, vocab=None),
    ("NOTE", "note_event_field_concept_id"): dict(kor="관련 표 concept", desc="note_event_id 가 가리키는 표·컬럼. K-AI Field concept", ref=None, vocab="K-AI Field (F_*)"),
    # ---------------------------------------------------------------- SPECIMEN
    ("SPECIMEN", "specimen_id"): dict(kor="검체 ID", desc="행 고유키. 병리 보고서·바이오마커 표가 이 값을 참조한다", ref=None, vocab=None),
    ("SPECIMEN", "person_id"): _PERSON_FK,
    ("SPECIMEN", "specimen_concept_id"): dict(kor="검체 종류 concept", desc="생검·절제 같은 검체의 종류. K-AI Specimen concept(SNOMED 매핑)", ref=None, vocab="K-AI Specimen (SNOMED)"),
    ("SPECIMEN", "specimen_type_concept_id"): _TYPE,
    ("SPECIMEN", "specimen_date"): dict(kor="검체 채취일", desc="검체를 채취한 날. 병리 보고서의 검체 채취일과 같아야 한다", ref=None, vocab=None),
    ("SPECIMEN", "quantity"): dict(kor="검체 양", desc="검체의 양(수치). 단위는 unit_concept_id. 대부분 비움", ref=None, vocab=None),
    ("SPECIMEN", "unit_concept_id"): _UNIT,
    ("SPECIMEN", "anatomic_site_concept_id"): dict(kor="채취 부위 concept", desc="검체를 뗀 해부학적 부위(SNOMED body structure)", ref=None, vocab="SNOMED body structure"),
    ("SPECIMEN", "disease_status_concept_id"): dict(kor="검체 질환 상태 concept", desc="검체가 종양 조직인지 정상 조직인지 등. 대부분 비움", ref=None, vocab=None),
    ("SPECIMEN", "specimen_source_id"): dict(kor="병리 번호", desc="병원 병리과의 접수·검체 번호", ref=None, vocab=None),
    ("SPECIMEN", "specimen_source_value"): dict(kor="검체 원천값", desc="병원 원천의 검체 종류 표기", ref=None, vocab=None),
    ("SPECIMEN", "anatomic_site_source_value"): dict(kor="채취 부위 원천값", desc="병원 원천의 부위 표기", ref=None, vocab=None),
    # ---------------------------------------------------------------- COHORT
    ("COHORT", "cohort_definition_id"): dict(kor="코호트 concept", desc="어느 코호트인가. K-AI Cohort concept(COHORT_LUNG_CANCER …). subject_id·cohort_start_date 와 함께 고유키", ref=None, vocab="K-AI Cohort (COHORT_*)"),
    ("COHORT", "subject_id"): dict(kor="환자 ID", desc="PERSON.person_id 참조(OMOP 관례상 이름이 subject_id)", ref="PERSON.person_id", vocab=None),
    ("COHORT", "cohort_start_date"): dict(kor="코호트 진입일", desc="인덱스 날짜. 코호트 인덱스 서식의 진입일", ref=None, vocab=None),
    ("COHORT", "cohort_end_date"): dict(kor="코호트 종료일", desc="최종 추적일 또는 사망일. 미정이면 진입일과 같게 둔다", ref=None, vocab=None),
    # ---------------------------------------------------------------- EPISODE
    ("EPISODE", "episode_id"): dict(kor="에피소드 ID", desc="행 고유키. EPISODE_EVENT 가 이 값으로 사건을 매단다", ref=None, vocab=None),
    ("EPISODE", "person_id"): _PERSON_FK,
    ("EPISODE", "episode_concept_id"): dict(kor="에피소드 종류 concept", desc="질환 에피소드·최초 발생·재발/진행·관해·치료 레지멘·치료 사이클 중 하나. K-AI Episode concept", ref=None, vocab="K-AI Episode (EP_*)"),
    ("EPISODE", "episode_start_date"): dict(kor="에피소드 시작일", desc="질환 에피소드는 진단일, 레지멘은 첫 투여일", ref=None, vocab=None),
    ("EPISODE", "episode_end_date"): dict(kor="에피소드 종료일", desc="레지멘 종료일 등. 진행 중이면 비움. 매단 약물의 기간과 맞아야 한다", ref=None, vocab=None),
    ("EPISODE", "episode_parent_id"): dict(kor="상위 에피소드 ID", desc="질환 ← 레지멘 ← 사이클의 위 단계. EPISODE.episode_id 참조. 최상위는 비움", ref="EPISODE.episode_id", vocab=None),
    ("EPISODE", "episode_number"): dict(kor="에피소드 번호", desc="치료 line 번호 또는 사이클 번호", ref=None, vocab=None),
    ("EPISODE", "episode_object_concept_id"): dict(kor="에피소드 대상 concept", desc="무엇에 관한 에피소드인가. 질환 concept·레지멘 concept(HemOnc)·재발 부위 등", ref=None, vocab="K-AI 진단 concept · HemOnc 레지멘"),
    ("EPISODE", "episode_type_concept_id"): _TYPE,
    ("EPISODE", "episode_source_value"): dict(kor="에피소드 원천값", desc="원천 레지멘명 등 표기", ref=None, vocab=None),
    # ---------------------------------------------------------------- EPISODE_EVENT
    ("EPISODE_EVENT", "episode_id"): dict(kor="에피소드 ID", desc="EPISODE.episode_id 참조. (episode_id, event_id, episode_event_field_concept_id) 가 고유키", ref="EPISODE.episode_id", vocab=None),
    ("EPISODE_EVENT", "event_id"): dict(kor="연결 레코드 ID", desc="에피소드에 매단 레코드(약물·진단·시술·검사)의 id. 표마다 id 가 따로 매겨지므로 episode_event_field_concept_id 와 함께 읽어야 한다", ref=None, vocab=None),
    ("EPISODE_EVENT", "episode_event_field_concept_id"): dict(kor="연결 표 concept", desc="event_id 가 어느 표의 id 인지. K-AI Field concept(F_DRUG, F_CONDITION, F_PROCEDURE, F_MEASUREMENT …)", ref=None, vocab="K-AI Field (F_*)"),
}
