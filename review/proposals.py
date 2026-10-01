"""9월 30일 매뉴얼에 대한 수정 제안(CHANGES)과 의뢰사 확인 질문(QUESTIONS).

제안의 `requires`는 대안 목록이다. 하나라도 만족하면 그 제안이 필요하다.
각 대안은 {질문 id: [답 id, ...]} 이며 모든 질문이 해당 답이어야 만족한다.
`requires`가 None이면 질문 답과 무관하게 권장한다.
`fields`는 워크북에서 현재 정의를 찾아 화면에 보여줄 (시트, 필드명) 목록이다.
"""

OBS = "관찰(OBSERVATION)"
MEAS = "검사(MEASUREMENT)"
DRUG = "약물 노출(DRUG_EXPOSURE)"
COND = "질환 발생(CONDITION_OCCURRENCE)"

QUESTIONS = [
    {
        "id": "Q01", "title": "concept ID를 어느 Athena 어휘 판본 기준으로 정할까요?",
        "why": "같은 숫자 ID라도 판본에 따라 표준 여부·domain이 바뀔 수 있습니다. 판본이 정해져야 concept ID의 존재·표준성 DQ를 재현할 수 있습니다.",
        "options": [
            {"id": "client", "label": "의뢰사가 판본(다운로드 일자)을 지정", "effect": "지정 판본으로 매핑하고 검증합니다."},
            {"id": "developer", "label": "개발 측이 현재 판본을 고정해 공유", "effect": "고정한 판본 정보를 매뉴얼 부록에 기록합니다."},
        ],
        "recommended": "developer",
        "legacy": ["issue:vocabulary-edition"],
    },
    {
        "id": "Q02", "title": "범주형 결과값(예/아니오, 폐경 상태 등)도 concept ID로 저장할까요?",
        "why": "현재 OBSERVATION에는 결과용 concept 열이 없어 결과는 숫자 코드나 문자열로만 남습니다. concept ID로 저장해야 '임신 여부=예'처럼 기관 간 같은 의미로 비교·검증할 수 있습니다.",
        "options": [
            {"id": "yes", "label": "예, 결과도 concept ID로 저장", "effect": "OBSERVATION에 value_as_concept_id 열을 추가합니다(제안 C08)."},
            {"id": "no", "label": "아니오, 항목만 concept ID로 저장", "effect": "결과는 문자열로만 보존하며 결과 의미의 DQ는 하지 않습니다."},
        ],
        "recommended": "yes",
        "legacy": ["issue:concept-scope"],
    },
    {
        "id": "Q03", "title": "diag_rgst_ymd(진단정보 등록일)는 실제 진단일과 같은가요?",
        "why": "폐암·유방암·대장암 표에는 '등록일'만 있습니다. 등록이 진단보다 늦으면 '진단 전 치료' 같은 시간 순서 오류를 잘못 판정합니다.",
        "options": [
            {"id": "same", "label": "같다 (등록일 = 진단일)", "effect": "현재 열을 진단일로 사용합니다. 설명 문구만 정정합니다."},
            {"id": "different_available", "label": "다르며, 실제 진단일 데이터가 있다", "effect": "진단일 열을 추가합니다(제안 C07)."},
            {"id": "different_unavailable", "label": "다르지만 실제 진단일 데이터는 없다", "effect": "등록일을 근사값으로만 쓰고 날짜 순서 DQ는 경고 수준으로 낮춥니다."},
        ],
        "recommended": None,
        "legacy": [],
    },
    {
        "id": "Q04", "title": "폐암 clinical_stage의 AJCC 판수를 알 수 있나요?",
        "why": "OMOP 병기 개념은 판수(6·7·8판)별로 다릅니다. 판수가 없으면 'IIA'를 표준 병기 개념에 대응시킬 수 없습니다.",
        "options": [
            {"id": "per_patient", "label": "환자마다 판수가 원천에 기록되어 있다", "effect": "판수 열을 추가합니다(제안 C04)."},
            {"id": "single", "label": "모두 같은 판수(예: 8판)로 기록한다", "effect": "설명에 판수를 명시합니다(제안 C05)."},
            {"id": "unknown", "label": "알 수 없다", "effect": "병기는 원천 문자열로만 보존하고 표준 병기 매핑·DQ를 하지 않습니다."},
        ],
        "recommended": None,
        "legacy": [],
    },
    {
        "id": "Q05", "title": "폐암 조직형의 ICD-O-3 형태 코드(예: 8140/3)와 원발 부위 코드(예: C34.1)가 원천에 있나요?",
        "why": "OMOP 종양 관례는 암 진단을 ICD-O-3 조직형+부위 개념으로 CONDITION에 기록합니다. 현재 1~7 범주(예: '기타', 'Carcinoma tumor 계열')로는 표준 개념에 1:1로 대응시킬 수 없습니다.",
        "options": [
            {"id": "yes", "label": "있다", "effect": "ICD-O-3 코드 열을 추가합니다(제안 C06)."},
            {"id": "no", "label": "없다, 1~7 범주만 있다", "effect": "범주별로 가장 가까운 표준 진단 개념에 매핑하고 '기타'는 일반 폐암 개념으로 둡니다."},
        ],
        "recommended": None,
        "legacy": [],
    },
    {
        "id": "Q06", "title": "비항암 약물(예: 가임력 보존용 GnRHa)도 DRUG_EXPOSURE에 넣나요?",
        "why": "현재 sact_id와 note_id가 모두 필수(Y)라서 항암요법·노트가 없는 약물은 저장할 수 없습니다.",
        "options": [
            {"id": "include", "label": "넣는다", "effect": "sact_id·note_id를 조건부 필수로 바꿉니다(제안 C02·C03)."},
            {"id": "exclude", "label": "넣지 않는다 (항암 약물만)", "effect": "현재 필수 조건을 유지합니다. 비항암 약물은 수집 범위에서 빠집니다."},
        ],
        "recommended": "include",
        "legacy": ["issue:drug-sact-note-required"],
    },
    {
        "id": "Q07", "title": "항암요법(SACT) 정보를 어떤 구조로 둘까요?",
        "why": "OMOP CDM 5.4는 레지멘·치료 line을 EPISODE/EPISODE_EVENT 표준 테이블로 표현합니다. 전환하면 DRUG_EXPOSURE.sact_id 같은 비표준 연결이 필요 없고 표준 도구와 호환됩니다.",
        "options": [
            {"id": "keep", "label": "현재 SACT 특화 테이블 유지", "effect": "DRUG_EXPOSURE.sact_id 연결을 유지합니다."},
            {"id": "episode", "label": "EPISODE/EPISODE_EVENT로 전환", "effect": "SACT 시트를 EPISODE 매핑으로 바꿉니다(제안 C12)."},
        ],
        "recommended": "episode",
        "legacy": ["issue:extension-table-scope"],
    },
    {
        "id": "Q08", "title": "검사·관찰 값이 '어느 수술/진단'에 속하는지까지 검증해야 하나요?",
        "why": "같은 방문에 수술이 두 번 있으면 지금 구조로는 TME 완전도가 어느 수술의 평가인지 알 수 없습니다. CDM 5.4는 이를 위한 표준 연결 열을 제공합니다.",
        "options": [
            {"id": "event", "label": "예, 사건 단위로 검증", "effect": "표준 사건 연결 열을 추가합니다(제안 C11)."},
            {"id": "patient", "label": "아니오, 환자·방문 단위로 충분", "effect": "연결 열 없이 진행합니다. 사건 간 값 뒤바뀜은 검출하지 못합니다."},
        ],
        "recommended": None,
        "legacy": ["issue:event-linkage"],
    },
    {
        "id": "Q09", "title": "병원 고유(로컬) 코드의 concept ID도 보존해야 하나요?",
        "why": "표준 개념이 없거나 나중에 매핑이 바뀌어도 원래 병원 항목으로 되돌아가려면 로컬 concept ID를 별도 열에 둬야 합니다.",
        "options": [
            {"id": "yes", "label": "예", "effect": "*_source_concept_id 열을 추가합니다(제안 C10)."},
            {"id": "no", "label": "아니오, 원천 코드 문자열로 충분", "effect": "제안 C09의 원천 코드 문자열만 보존합니다."},
        ],
        "recommended": "no",
        "legacy": ["issue:missing-observation-columns"],
    },
    {
        "id": "Q10", "title": "질환별 특화 테이블(DIABETES 등)을 계속 제출하나요?",
        "why": "특화 테이블을 없애고 공통 테이블만 쓰려면, 그 테이블에만 있는 정보(예: 당뇨 진단 종료일)를 담을 열이 공통 테이블에 있어야 합니다.",
        "options": [
            {"id": "keep", "label": "계속 제출", "effect": "공통 테이블 열 추가가 필요 없습니다."},
            {"id": "drop", "label": "없애고 공통 테이블로 이전", "effect": "CONDITION_OCCURRENCE 종료일 등 열을 추가합니다(제안 C13)."},
        ],
        "recommended": "keep",
        "legacy": ["issue:extension-table-scope", "issue:diabetes-end-date"],
    },
    {
        "id": "Q11", "title": "약물의 SMILES 구조식은 투약 기록마다 필요한가요?",
        "why": "구조식은 환자 투약이 아니라 약물 자체의 속성입니다. 투약마다 NOTE를 연결하면 같은 구조식이 수천 번 중복되고 note_id 필수 오류가 생깁니다.",
        "options": [
            {"id": "per_drug", "label": "성분별 참조표 한 번이면 된다", "effect": "성분별 참조표를 두고 DRUG_EXPOSURE.note_id를 없앱니다(제안 C14)."},
            {"id": "per_exposure", "label": "투약 기록마다 연결해야 한다", "effect": "현재 note_id 구조를 유지합니다."},
        ],
        "recommended": "per_drug",
        "legacy": [],
    },
    {
        "id": "Q12", "rev": "2", "title": "소세포폐암 병기를 어떤 체계로 기록하나요?",
        "why": "소세포폐암(조직형 4)은 AJCC 대신 제한기/확장기(VALSG)로 기록하는 경우가 많습니다. AJCC 칸에 제한기/확장기가 들어오면 표준 매핑과 DQ가 모두 실패합니다.",
        "options": [
            {"id": "ajcc", "label": "AJCC 병기로만 기록", "effect": "현재 규칙(판수별 AJCC 병기)을 그대로 적용합니다."},
            {"id": "valsg", "label": "제한기/확장기로만 기록", "effect": "소세포폐암에 LD/ED 값을 허용합니다(제안 C21)."},
            {"id": "both", "label": "병원·환자에 따라 둘 다 있음", "effect": "AJCC와 LD/ED를 모두 허용하고 판수 유무로 구분합니다(제안 C21)."},
        ],
        "recommended": None,
        "legacy": [],
    },
]

CHANGES = [
    {
        "id": "C01", "priority": "필수", "title": "LYMPHOMA.cell_of_origin 필수 Y → N (DLBCL일 때만 입력)",
        "sheet": "림프종(LYMPHOMA)", "fields": [("림프종(LYMPHOMA)", "cell_of_origin")],
        "proposed": "필수: N\n설명: DLBCL 세포기원 분류이다. DLBCL 환자인 경우에만 입력한다. 예: GCB, ABC/non-GCB, unclassifiable.",
        "reason": "세포기원은 DLBCL에만 존재하는 분류입니다. Y로 두면 다른 림프종 환자 전원이 결측 오류로 판정됩니다.",
        "example": "호지킨 림프종 환자의 cell_of_origin이 비어 있음 → 현재: 필수 결측 오류 / 수정 후: 정상. DLBCL 환자인데 비어 있으면 DQ 규칙이 별도로 경고합니다.",
        "requires": None,
    },
    {
        "id": "C02", "rev": "2", "priority": "필수", "title": "DRUG_EXPOSURE.sact_id 필수 Y → N (항암제 투여일 때만 필수)",
        "sheet": DRUG, "fields": [(DRUG, "sact_id")],
        "proposed": "필수: N (조건부)\n설명: SACT 테이블과 연결되는 외래키이다. 항종양제(ATC L01)는 항암요법으로 투여되므로 필수이다. 내분비 치료제(ATC L02, 예: GnRHa·타목시펜)는 항암요법으로 투여한 경우에만 입력한다. 그 외 약물은 비워 둔다.",
        "reason": "비항암 약물에는 연결할 항암요법이 없습니다. 또한 '항암요법일 때만 필수'를 DQ로 검사하려면 무엇이 항암제인지 판정 기준이 있어야 합니다. ATC L01은 항상 항암 목적이라 필수로 검사할 수 있고, L02는 가임력 보존처럼 비항암 목적에도 쓰여 강제할 수 없으므로 구분합니다.",
        "example": "옥살리플라틴(L01) 투여, sact_id 비어 있음 → 필수 결측 오류. GnRHa(L02, 가임력 보존) 투여, sact_id 비어 있음 → 정상(DQ는 '목적 확인' 안내만). 메트포르민(A10), sact_id 비어 있음 → 정상.",
        "requires": [{"Q06": ["include"], "Q07": ["keep"]}],
    },
    {
        "id": "C03", "priority": "필수", "title": "DRUG_EXPOSURE.note_id 필수 Y → N",
        "sheet": DRUG, "fields": [(DRUG, "note_id")],
        "proposed": "필수: N\n설명: 해당 투약과 연결되는 노트가 있는 경우에만 입력한다.",
        "reason": "SMILES 노트가 없는 약물(비항암제 등)은 저장할 수 없게 됩니다.",
        "example": "구조식 노트가 없는 GnRHa 투여 기록: note_id = 비움(정상).",
        "requires": [{"Q06": ["include"], "Q11": ["per_exposure"]}],
    },
    {
        "id": "C04", "rev": "2", "priority": "필수", "title": "LUNG_CANCER에 clinical_stage_ajcc_edition 열 추가, 병기 값은 판수별로",
        "sheet": "폐암(LUNG_CANCER)", "fields": [("폐암(LUNG_CANCER)", "clinical_stage")],
        "proposed": "신규 열 (clinical_stage 다음)\n필드명: clinical_stage_ajcc_edition | integer | 필수 Y\n설명: clinical_stage 판정에 사용한 AJCC 판수이다. 6, 7, 8 중 하나로 기입한다.\n\nclinical_stage 설명 변경: 초진 시 AJCC 임상 병기이다. clinical_stage_ajcc_edition 판수의 병기군으로 기입한다. 8판: 0, IA1, IA2, IA3, IB, IIA, IIB, IIIA, IIIB, IIIC, IVA, IVB / 7판: 0, IA, IB, IIA, IIB, IIIA, IIIB, IV",
        "reason": "OMOP 표준 병기 개념(Cancer Modifier)은 판수별로 다른 개념입니다(예: c-8th_AJCC/UICC-Stage-2A). 판수 없이는 표준 매핑이 불가능합니다. 기존 설명의 예시(IA, IB … IV)는 7판 값이라 8판 환자에게 맞지 않으므로 판수별 허용 값을 함께 고칩니다.",
        "example": "clinical_stage = IA2, 판수 8 → 정상. clinical_stage = IA2, 판수 7 → 7판에 없는 값이므로 DQ 오류. clinical_stage = IIA, 판수 8 → '임상 AJCC 8판 IIA' 개념으로 매핑.",
        "requires": [{"Q04": ["per_patient"]}],
    },
    {
        "id": "C05", "priority": "필수", "title": "LUNG_CANCER.clinical_stage 설명에 AJCC 판수 명시",
        "sheet": "폐암(LUNG_CANCER)", "fields": [("폐암(LUNG_CANCER)", "clinical_stage")],
        "proposed": "설명: 초진 시 AJCC 8판 기준 임상 병기를 나타내는 값이다. IA1, IA2, IA3, IB, IIA, IIB, IIIA, IIIB, IIIC, IVA, IVB 등으로 기입한다.",
        "reason": "판수가 하나로 고정되면 열 추가 없이 설명만으로 표준 매핑이 가능합니다. 8판을 쓰면 IA1~IA3, IIIC, IVA/IVB 같은 세분 값도 허용해야 합니다.",
        "example": "clinical_stage = IA2 → 8판 IA2 개념. 8판에 없는 값(예: 단독 'IA')은 DQ에서 판수 불일치로 경고합니다.",
        "requires": [{"Q04": ["single"]}],
    },
    {
        "id": "C06", "rev": "2", "priority": "필수", "title": "LUNG_CANCER에 ICD-O-3 조직형·부위 코드 열 추가 (필수)",
        "sheet": "폐암(LUNG_CANCER)", "fields": [("폐암(LUNG_CANCER)", "histologic_diagnosis")],
        "proposed": "신규 열 2개 (histologic_diagnosis 다음)\nhistology_icdo3_code | varchar | 필수 Y | ICD-O-3 형태 코드 (예: 8140/3)\nprimary_site_icdo3_code | varchar | 필수 Y | ICD-O-3 부위 코드 (예: C34.1)",
        "reason": "OHDSI 종양 관례는 암 진단을 ICD-O-3 '조직형-부위' 개념으로 CONDITION_OCCURRENCE에 기록합니다. 1~7 범주는 표준 개념과 1:1로 대응하지 않습니다(특히 5 'Carcinoma tumor 계열', 7 '기타'). 원천에 코드가 있으므로(Q05) 필수로 두어 누락을 잡고, 1~7 범주와 코드의 일치 여부도 검사합니다.",
        "example": "histologic_diagnosis = 1(Adenocarcinoma), histology_icdo3_code = 8140/3, primary_site_icdo3_code = C34.1 → '8140/3-C34.1' 진단 개념으로 매핑. histologic_diagnosis = 4(Small cell)인데 코드 = 8140/3 → 범주·코드 불일치 DQ 오류.",
        "requires": [{"Q05": ["yes"]}],
    },
    {
        "id": "C07", "priority": "필수", "title": "폐암·유방암·대장암에 diagnosis_date 열 추가, diag_rgst_ymd는 N",
        "sheet": "폐암·유방암·대장암", "fields": [("폐암(LUNG_CANCER)", "diag_rgst_ymd"), ("유방암(BREAST_CANCER)", "diag_rgst_ymd"), ("대장암(COLORECTAL_CANCER)", "diag_rgst_ymd")],
        "proposed": "세 시트 공통 신규 열 (diag_rgst_ymd 앞)\ndiagnosis_date | date | 필수 Y | 해당 암을 최초로 진단(조직학적 확진)한 날짜이다.\n기존 diag_rgst_ymd: 필수 Y → N",
        "reason": "진단일과 등록일이 다르면 등록일을 진단일로 쓰는 순간 날짜 순서 DQ가 틀립니다. 림프종 시트는 이미 diagnosis_date를 쓰므로 시트 간 일관성도 맞춰집니다.",
        "example": "진단 2024-02-01, 등록 2024-03-01, 수술 2024-02-20 → 등록일 기준이면 '진단 전 수술' 오류(오탐) / 진단일 기준이면 정상.",
        "requires": [{"Q03": ["different_available"]}],
    },
    {
        "id": "C08", "priority": "필수", "title": "OBSERVATION에 value_as_concept_id 열 추가",
        "sheet": OBS, "fields": [(OBS, "value_as_string")],
        "proposed": "신규 열 (value_as_string 다음)\nvalue_as_concept_id | integer | 필수 N\n설명: 관찰 결과가 범주형인 경우 해당 결과를 나타내는 표준 Concept 식별자이다.",
        "reason": "MEASUREMENT에는 이미 같은 열(10행)이 있지만 OBSERVATION에는 없습니다. 결과를 concept ID로 저장하기로 하면 담을 곳이 필요합니다. OMOP CDM 표준 열입니다.",
        "example": "pregnant_at_diagnosis = 1(Yes) → observation_concept_id = '진단 시 임신' 항목 ID, value_as_concept_id = 표준 'Yes' ID. 원천 숫자 1을 그대로 넣지 않습니다.",
        "requires": [{"Q02": ["yes"]}],
    },
    {
        "id": "C09", "rev": "2", "priority": "권장", "title": "MEASUREMENT·OBSERVATION·CONDITION·PROCEDURE·DRUG에 원천 코드 열 추가",
        "sheet": "검사·관찰·질환·처치·약물", "fields": [(MEAS, "measurement_concept_id"), (OBS, "observation_concept_id"), (COND, "condition_concept_id"), ("시술 및 처치(PROCEDURE_OCCURRENCE)", "procedure_concept_id"), (DRUG, "drug_concept_id")],
        "proposed": "MEASUREMENT: measurement_source_value | varchar | 필수 N | 원천의 검사 항목 코드·명칭\nOBSERVATION: observation_source_value | varchar | 필수 N | 원천의 관찰 항목 코드·명칭\nOBSERVATION: value_source_value | varchar | 필수 N | 변환 전 원천 결과값\nCONDITION_OCCURRENCE: condition_source_value | varchar | 필수 N | 원천 진단 코드(예: KCD, ICD-O-3)\nPROCEDURE_OCCURRENCE: procedure_source_value | varchar | 필수 N | 원천 처치·수가 코드\nDRUG_EXPOSURE: drug_source_value | varchar | 필수 N | 원천 약품 코드(예: EDI, 원내 코드)",
        "reason": "현재는 항목이 concept ID로만 남아, 잘못 매핑돼도 원래 무엇이었는지 확인할 수 없습니다. 원천 코드를 남겨야 '매핑 정확성' DQ가 가능합니다. 처음에는 검사·관찰만 제안했으나 진단·처치·약물도 같은 문제가 있어 범위를 넓혔습니다. 모두 OMOP CDM 표준 열입니다.",
        "example": "condition_concept_id = 0(매핑 실패), condition_source_value = 'C34.1' → 매핑되지 않은 원천 코드를 DQ 보고서에 표시. drug_source_value = 'EDI 642102570'인데 drug_concept_id가 다른 성분 → 매핑 오류 검출.",
        "requires": None,
    },
    {
        "id": "C10", "priority": "선택", "title": "MEASUREMENT·OBSERVATION에 *_source_concept_id 열 추가",
        "sheet": "검사·관찰", "fields": [(MEAS, "measurement_concept_id"), (OBS, "observation_concept_id")],
        "proposed": "MEASUREMENT 신규 열: measurement_source_concept_id | integer | 필수 N\nOBSERVATION 신규 열: observation_source_concept_id | integer | 필수 N\n설명: 원천(로컬) 항목을 나타내는 Concept 식별자이다. 표준 여부와 무관하다.",
        "reason": "로컬 concept ID를 표준 열에 넣으면 표준성 DQ가 깨집니다. 별도 열에 두면 표준·로컬 역할이 분리됩니다.",
        "example": "measurement_concept_id = 표준 FIB-4 ID, measurement_source_concept_id = 병원 로컬 FIB-4 ID.",
        "requires": [{"Q09": ["yes"]}],
    },
    {
        "id": "C11", "priority": "필수", "title": "MEASUREMENT·OBSERVATION에 사건 연결 열 추가 (CDM 5.4 표준)",
        "sheet": "검사·관찰", "fields": [(MEAS, "visit_occurrence_id"), (OBS, "visit_occurrence_id")],
        "proposed": "MEASUREMENT 신규 열: measurement_event_id | integer | 필수 N, meas_event_field_concept_id | integer | 필수 N\nOBSERVATION 신규 열: observation_event_id | integer | 필수 N, obs_event_field_concept_id | integer | 필수 N\n설명: 이 기록이 가리키는 다른 테이블의 행 ID와, 그 테이블·열을 나타내는 concept 식별자이다.",
        "reason": "같은 방문 안의 여러 수술·진단 중 어느 것에 대한 값인지 연결합니다. 별도 연결표를 새로 설계하지 않고 OMOP CDM 5.4 표준 열을 씁니다.",
        "example": "같은 방문에 수술 A(procedure_occurrence_id=101), B(102). TME 완전도 관찰 행: observation_event_id = 102, obs_event_field_concept_id = 'procedure_occurrence.procedure_occurrence_id' 개념 → 수술 B의 평가로 확정됩니다.",
        "requires": [{"Q08": ["event"]}],
    },
    {
        "id": "C12", "priority": "필수", "title": "SACT를 EPISODE/EPISODE_EVENT로 전환, DRUG_EXPOSURE.sact_id 삭제",
        "sheet": "항암(SACT)", "fields": [("항암(SACT)", "sact_id"), ("항암(SACT)", "regimen_concept_id"), ("항암(SACT)", "line_of_therapy"), (DRUG, "sact_id")],
        "proposed": "SACT → EPISODE: sact_id→episode_id, regimen_concept_id→episode_object_concept_id, regimen_start/end_date→episode_start/end_date, line_of_therapy→episode_number, episode_concept_id='Treatment Regimen'\n약물 연결: EPISODE_EVENT(episode_id, event_id=drug_exposure_id, episode_event_field_concept_id)\nDRUG_EXPOSURE.sact_id 삭제\nSACT의 나머지 항목(치료 목적, ECOG, 반응, 진행일 등)은 해당 EPISODE에 연결된 OBSERVATION/MEASUREMENT로 이동",
        "reason": "OMOP CDM 5.4의 표준 항암요법 표현입니다. 비표준 sact_id FK가 없어지므로 비항암 약물 저장 문제(C02)도 함께 해소됩니다.",
        "example": "2차 FOLFOX 요법(sact_id 42)에 옥살리플라틴·5-FU 투여 6건 → EPISODE 1행(episode_number=2) + EPISODE_EVENT 6행.",
        "requires": [{"Q07": ["episode"]}],
    },
    {
        "id": "C13", "priority": "필수", "title": "CONDITION_OCCURRENCE에 condition_end_date 열 추가",
        "sheet": COND, "fields": [(COND, "condition_start_date"), ("당뇨병(DIABETES)", "condition_end_date")],
        "proposed": "신규 열 (condition_start_date 다음)\ncondition_end_date | date | 필수 N | 질환 상태의 종료 날짜이다.",
        "reason": "DIABETES 표를 없애면 진단 종료일을 담을 곳이 사라집니다. OMOP CDM 표준 열입니다.",
        "example": "당뇨 진단 2024-01-10 ~ 2024-06-30 → 두 날짜를 모두 보존하고 '종료일 ≥ 시작일' DQ를 수행합니다.",
        "requires": [{"Q10": ["drop"]}],
    },
    {
        "id": "C14", "rev": "2", "priority": "권장", "title": "SMILES를 성분별 참조표로 이동, DRUG_EXPOSURE.note_id 삭제",
        "sheet": DRUG, "fields": [(DRUG, "note_id")],
        "proposed": "신규 참조표 DRUG_INGREDIENT_STRUCTURE\ningredient_concept_id | integer | 필수 Y (PK) | 성분(RxNorm Ingredient 등) 표준 Concept 식별자\nsmiles | varchar | 필수 Y | 해당 성분의 SMILES 구조식\n투약과의 연결: DRUG_EXPOSURE.drug_concept_id → 표준 어휘의 성분 관계(CONCEPT_ANCESTOR) → ingredient_concept_id\nDRUG_EXPOSURE.note_id 삭제",
        "reason": "구조식은 제품이 아니라 성분의 속성입니다. 제품(drug_concept_id) 기준으로 두면 같은 성분의 용량·제형마다 중복되고, 복합제는 구조식이 2개 이상이라 한 행에 담을 수 없습니다. 성분 단위로 두면 중복과 note_id 필수 오류가 모두 없어지고 '구조식 누락 성분' DQ를 할 수 있습니다.",
        "example": "메트포르민 500mg·1000mg 정제 투여 1,000건 → 참조표에는 메트포르민 성분 1행. 메트포르민+시타글립틴 복합제 → 두 성분 행에 각각 연결.",
        "requires": [{"Q11": ["per_drug"]}],
    },
    {
        "id": "C15", "priority": "권장", "title": "MEASUREMENT 필수 여부 빈칸 채우기",
        "sheet": MEAS, "fields": [(MEAS, "measurement_date"), (MEAS, "measurement_type_concept_id"), (MEAS, "value_as_number"), (MEAS, "value_as_concept_id")],
        "proposed": "measurement_date: (빈칸) → Y\nmeasurement_type_concept_id: (빈칸) → Y\n9~15행(value_as_number ~ value_source_value): (빈칸) → N",
        "reason": "필수 여부가 비어 있으면 DQ에서 결측을 오류로 볼지 정할 수 없습니다. 측정일과 출처 유형은 OMOP CDM에서도 필수입니다.",
        "example": "measurement_date가 비어 있는 행 → 현재: 판정 불가 / 수정 후: 필수 결측 오류.",
        "requires": None,
    },
    {
        "id": "C16", "priority": "권장", "title": "DRUG_EXPOSURE 15~21행 필수 여부 빈칸 → N",
        "sheet": DRUG, "fields": [(DRUG, "numerator_value"), (DRUG, "dosing_number")],
        "proposed": "numerator_value, numerator_unit_concept_id, denominator_value, denominator_unit_concept_id, frequency_per_day, dosing_interval_day, dosing_number: (빈칸) → N\n(조건부 규칙은 설명대로 유지: 매일 투여 시 days_supply 필수, 간격 1일 초과 시 dosing_number 필수)",
        "reason": "필수 여부를 명시해야 결측 DQ와 설명 속 조건부 규칙을 구분해 적용할 수 있습니다.",
        "example": "frequency_per_day = 1, days_supply 비어 있음 → 조건부 규칙 위반으로 판정.",
        "requires": None,
    },
    {
        "id": "C17", "priority": "권장", "title": "VISIT_OCCURRENCE.visit_concept_id 예시를 실제 concept ID로 교체",
        "sheet": "방문(VISIT_OCCURRENCE)", "fields": [("방문(VISIT_OCCURRENCE)", "visit_concept_id")],
        "proposed": "예) 외래 = 9202 (Outpatient Visit), 입원 = 9201 (Inpatient Visit), 응급 = 9203 (Emergency Room Visit)\n※ Q01 판본에서 최종 확인 후 기재",
        "reason": "'00000000'은 자리표시자라 병원이 실제 값을 알 수 없습니다. 방문 유형은 OMOP 표준 Visit 개념이 널리 고정되어 있습니다.",
        "example": "외래 방문 행: visit_concept_id = 9202.",
        "requires": None,
    },
    {
        "id": "C18", "priority": "선택", "title": "ADVERSE_EVENT 시트 번호 5.1 → 5.2",
        "sheet": "이상사례(ADVERSE_EVENT)", "fields": [],
        "current": "시트 제목: 5.1 이상사례(ADVERSE_EVENT) — SACT 시트와 번호 중복",
        "proposed": "5.2 이상사례(ADVERSE_EVENT)",
        "reason": "문서 번호 중복 정정입니다. DQ와 무관합니다.",
        "example": "",
        "requires": None,
    },
    {
        "id": "C19", "rev": "2", "priority": "필수", "title": "LYMPHOMA에 ICD-O-3 조직형 코드 열 추가 (아형 판별)",
        "sheet": "림프종(LYMPHOMA)", "fields": [("림프종(LYMPHOMA)", "diagnosis_date"), ("림프종(LYMPHOMA)", "cell_of_origin")],
        "proposed": "신규 열 (diagnosis_date 다음)\nhistology_icdo3_code | varchar | 필수 Y | 림프종 ICD-O-3 형태 코드 (예: DLBCL 9680/3, 외투세포 9673/3, 고전적 호지킨 9650/3, 말초 T세포 NOS 9702/3)",
        "reason": "현재 LYMPHOMA 표에는 아형 정보가 없어 cell_of_origin(DLBCL), mipi_score(외투세포), hodgkin_ips_score(호지킨), pit_score(T세포)가 누구에게 해당하는지 DQ가 알 수 없습니다. C01(cell_of_origin Y→N)의 'DLBCL이면 입력' 규칙도 이 열이 있어야 검사할 수 있습니다. 진단 CONDITION 매핑(ICD-O-3 관례)에도 필요합니다.",
        "example": "histology_icdo3_code = 9680/3(DLBCL), cell_of_origin 비어 있음 → 조건부 필수 결측 경고. 9650/3(호지킨), cell_of_origin 비어 있음 → 정상. 9673/3(외투세포), mipi_score 비어 있음 → 권장 항목 결측 안내.",
        "requires": None,
    },
    {
        "id": "C20", "rev": "2", "priority": "필수", "title": "diag_rgst_ymd 설명을 '진단일'로 정정 (폐암·유방암·대장암)",
        "sheet": "폐암·유방암·대장암", "fields": [("폐암(LUNG_CANCER)", "diag_rgst_ymd"), ("유방암(BREAST_CANCER)", "diag_rgst_ymd"), ("대장암(COLORECTAL_CANCER)", "diag_rgst_ymd")],
        "proposed": "설명: 해당 암을 최초로 진단(조직학적 확진)한 날짜이다. 진단정보 등록일과 동일하다.",
        "reason": "현재 설명 '진단정보 등록 연월일'만 보면 병원마다 실제 등록 작업일을 넣을 수 있습니다. 진단일과 같다고 확인했으므로(Q03) 의미를 문구로 고정해야 날짜 순서 DQ가 맞습니다.",
        "example": "병원 A는 진단일, 병원 B는 전산 등록일을 입력 → 같은 열의 의미가 달라 '진단 전 수술' 판정이 병원마다 틀어짐. 문구 정정 후에는 진단일로 통일.",
        "requires": [{"Q03": ["same"]}],
    },
    {
        "id": "C21", "rev": "2", "priority": "필수", "title": "소세포폐암의 제한기/확장기 병기 허용",
        "sheet": "폐암(LUNG_CANCER)", "fields": [("폐암(LUNG_CANCER)", "clinical_stage")],
        "proposed": "clinical_stage 설명에 추가: 소세포폐암(histologic_diagnosis = 4)에서 AJCC 병기 대신 VALSG 병기를 쓰는 경우 LD(제한기) 또는 ED(확장기)로 기입하고, clinical_stage_ajcc_edition은 비워 둔다.",
        "reason": "소세포폐암은 제한기/확장기로 병기를 기록하는 경우가 많습니다. 이를 AJCC 칸에 억지로 넣거나 결측으로 처리하면 DQ 오류가 납니다. 값과 판수 규칙을 명시해 두 체계를 구분합니다.",
        "example": "histologic_diagnosis = 4, clinical_stage = ED, 판수 비어 있음 → 정상. histologic_diagnosis = 1(선암), clinical_stage = ED → 오류.",
        "requires": [{"Q12": ["valsg", "both"]}],
    },
]

# 이전 검토 화면의 선택 라벨. 새 질문 옆에 '이전 답'을 참고로 보여주기 위한 것이다.
LEGACY_LABELS = {
    "freeze_athena": "Athena 판본 지정 후 대조", "defer_ids": "판본 확정 전 ID 판정 보류",
    "item_only": "항목 concept ID만", "item_and_result": "항목과 결과 모두 concept ID",
    "unchanged": "원본 열 유지", "targeted_extension": "필요한 열만 추가",
    "keep_extension": "DIABETES 표에 종료일 보존", "add_condition_end": "CONDITION_OCCURRENCE 종료일 추가",
    "exclude_end": "종료일 제외", "anticancer_only": "항암 약물만", "conditional_links": "sact_id·note_id 조건부 필수",
    "patient_level": "환자·방문 단위", "event_level": "사건 단위",
    "retain": "특화 시트 유지", "move_all": "특화 시트 폐지 후 이동",
    "literal": "원본 Y 그대로", "conditional": "조건부 필수",
}
