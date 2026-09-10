# -*- coding: utf-8 -*-
"""
단계 0: 데이터 사전(xlsx) -> 기계 판독 명세(YAML) 변환기

입력 : internal/dictionary/raw_dictionary.json  (매뉴얼 초안_20260813.xlsx 를 그대로 파싱한 것)
출력 : spec/kai_cdm_spec.yaml      테이블/필드 명세 (타입, 필수, 키, 코드표, 이벤트 그룹, 범위)
       spec/codelists.yaml         설명문에 박혀 있던 코드값을 분리한 코드표 + OMOP 표준 concept 허용집합
       spec/cohort_profiles.yaml   질환별 코호트 DB 의 테이블 구성
       internal/decisions/dictionary_issues.md   자동 검출된 사전 결함 목록

설계 결정(internal/decisions/DECISIONS.md 참조)을 코드로 강제한다.
"""
import json, re, sys, io, yaml
from collections import OrderedDict, Counter

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAW = json.load(open("internal/dictionary/raw_dictionary.json", encoding="utf-8"))

CORE = ["PERSON", "VISIT_OCCURRENCE", "PROCEDURE_OCCURRENCE", "DRUG_EXPOSURE",
        "CONDITION_OCCURRENCE", "MEASUREMENT", "OBSERVATION", "NOTE"]
DISEASE = ["LUNG_CANCER", "BREAST_CANCER", "COLORECTAL_CANCER", "MASLD", "DIABETES", "LYMPHOMA"]
COMMON_EXT = ["ADVERSE_EVENT", "ANTP_THERAPY"]

# ----------------------------------------------------------------------------
# 결정 D-11: 코호트별 테이블 구성
# ----------------------------------------------------------------------------
COHORTS = OrderedDict([
    ("LUNG_CANCER",       dict(kor="폐암",         tables=CORE + ["LUNG_CANCER", "ADVERSE_EVENT", "ANTP_THERAPY"])),
    ("BREAST_CANCER",     dict(kor="유방암",       tables=CORE + ["BREAST_CANCER", "ADVERSE_EVENT", "ANTP_THERAPY"])),
    ("COLORECTAL_CANCER", dict(kor="대장암",       tables=CORE + ["COLORECTAL_CANCER", "ADVERSE_EVENT", "ANTP_THERAPY"])),
    ("MASLD",             dict(kor="대사이상지방간", tables=CORE + ["MASLD", "ADVERSE_EVENT"])),
    ("DIABETES",          dict(kor="당뇨병",       tables=CORE + ["DIABETES", "ADVERSE_EVENT"])),
    ("LYMPHOMA",          dict(kor="림프종",       tables=CORE + ["LYMPHOMA", "ADVERSE_EVENT", "ANTP_THERAPY"])),
])

# ----------------------------------------------------------------------------
# 타입 정규화
# ----------------------------------------------------------------------------
def norm_type(t, name, desc):
    t0 = (t or "").strip().lower()
    if t0 in ("int", "integer"): return "integer"
    if t0 in ("float", "double", "numeric", "decimal"): return "float"
    if t0 == "date": return "date"
    if t0 in ("timestamp", "datetime"): return "timestamp"
    if t0.startswith("varchar") or t0 == "string": return "varchar"
    if "text" in t0: return "text"
    if t0 == "":
        return None
    return t0

# ----------------------------------------------------------------------------
# 결정 D-06: 이름/설명으로 보아 날짜인데 varchar 로 선언된 필드 -> date 로 교정
# 결정 D-03: 중복 컬럼 제거
# 결정 D-02: FK 이름 통일 (antp_therapy_id -> antp_id)
# ----------------------------------------------------------------------------
FORCE_TYPE = {
    ("BREAST_CANCER", "first_menstrual_period_date_after_treatment"): "date",
    ("BREAST_CANCER", "pregnancy_attempt_start_date"): "date",
    ("ANTP_THERAPY", "days_to_progression"): "date",     # 이름은 일수, 타입은 DATE. 값은 PD 발생일. (개명 권고: progression_date)
    ("NOTE", "note_text"): "text",
    ("OBSERVATION", "visit_occurrence_id"): "integer",
    ("LUNG_CANCER", "nsmk_strt_yr"): "integer",          # 연도
}
RENAME = {"antp_therapy_id": "antp_id"}

# ----------------------------------------------------------------------------
# 결정 D-04: 필수 여부. 핵심 테이블은 사전의 '필수' 열, 특화 테이블은 PK/person_id 만 필수.
# 사전에서 비어 있던 필수 여부 교정
# ----------------------------------------------------------------------------
FORCE_REQUIRED = {
    ("MEASUREMENT", "measurement_date"): True,
    ("MEASUREMENT", "measurement_type_concept_id"): True,
    ("OBSERVATION", "visit_occurrence_id"): False,
    ("ANTP_THERAPY", "antp_start_date"): True,
    ("ANTP_THERAPY", "regimen_or_line_of_therapy"): True,
    ("ADVERSE_EVENT", "adverse_event_concept_id"): True,
    ("ADVERSE_EVENT", "adverse_event_start_date"): True,
    # DRUG_EXPOSURE.antp_id / note_id 는 사전에 필수(Y)이나 비항암제/비항암 코호트에서는 채울 수 없음 -> 조건부 필수
    ("DRUG_EXPOSURE", "antp_id"): False,
    ("DRUG_EXPOSURE", "note_id"): False,
    ("DRUG_EXPOSURE", "visit_occurrence_id"): False,
}

# ----------------------------------------------------------------------------
# FK 참조 정의
# ----------------------------------------------------------------------------
FK_REF = {
    "person_id": "PERSON.person_id",
    "visit_occurrence_id": "VISIT_OCCURRENCE.visit_occurrence_id",
    "procedure_occurrence_id": "PROCEDURE_OCCURRENCE.procedure_occurrence_id",
    "drug_exposure_id": "DRUG_EXPOSURE.drug_exposure_id",
    "condition_occurrence_id": "CONDITION_OCCURRENCE.condition_occurrence_id",
    "measurement_id": "MEASUREMENT.measurement_id",
    "observation_id": "OBSERVATION.observation_id",
    "note_id": "NOTE.note_id",
    "adverse_event_id": "ADVERSE_EVENT.adverse_event_id",
    "antp_id": "ANTP_THERAPY.antp_id",
    "preceding_visit_occurrence_id": "VISIT_OCCURRENCE.visit_occurrence_id",
}
# 외부 테이블(사전에 정의되지 않음) 참조 -> 존재만 기록, 참조무결성 검사는 하지 않음
EXTERNAL_REF = {"care_site_id": "CARE_SITE", "file_id": "FILE", "location_id": "LOCATION",
                "provider_id": "PROVIDER", "visit_detail_id": "VISIT_DETAIL"}

# ----------------------------------------------------------------------------
# 결정 D-01: 특화 테이블 이벤트 그룹 정의. (anchor 날짜, 접두어/필드 목록)
# 접두어는 필드명 시작 문자열로 매칭. 'patient' 는 환자 수준(불변) 그룹.
# ----------------------------------------------------------------------------
CANCER_GROUPS = OrderedDict([
    ("gmt",  ("gmt_ymd",  ["gmt_"])),
    ("gmvx", ("gmvx_ymd", ["gmvx_", "gmte_", "pavr_", "uncl_varnt", "dna_vainf", "amsn_vainf", "ref_seq"])),
    ("gnrx", ("gnrx_ymd", ["gnrx_"])),
    ("plex", ("plex_ymd", ["plex_"])),
    ("brex", ("brex_ymd", ["brex_"])),
    ("imem", ("imem_ymd", ["imem_", "impt_read_ymd"])),
    ("mlem", ("mlem_ymd", ["mlem_", "mlpt_read_ymd"])),
    ("oprt", ("oprt_ymd", ["oprt_", "opls_", "repr_", "obst_trtm", "lapr_conv", "ostm_frmt", "ostm_frsn", "ima_ligt",
                           "inap_dsnt", "spfl_mobl", "curdg_", "ansc_loca", "anes_", "ebl_", "afoc_trtm", "afop_asmt"])),
    ("ostm_reop", ("ostm_reop_ymd", ["ostm_reop", "etc_ostm_rest"])),
    ("sgpt", ("srgc_ptem_ymd", ["srgc_ptem", "sgpt_", "tumr_wdth", "tumr_lgtd", "tumr_hght", "tumr_max_diam",
                                "afop_path", "htlg_diag_cd_po", "htlg_diag_nm_po", "htlg_diag_etc_cont", "htlg_gr",
                                "lvin_ex", "sgpt_micf", "incn_asso", "srmg_rlct", "resi_tumr", "slnd_", "pstv_slnd",
                                "totl_ln_cnt", "pstv_ln_cnt", "gros_tp", "lymp_inva", "vasc_inva", "nerv_prex",
                                "inva_dgre", "radi_rsmg", "tme_qlt"])),
    ("drug", ("drug_prsc_ymd", ["drug_", "drin_", "amount_"])),
    ("rdt",  ("rdt_prsc_ymd", ["rdt_", "rd_"])),
    ("rlps", ("rldg_ymd", ["rlps_"])),
    ("fmht", ("fmht_rcrd_ymd", ["fmht_", "fmhs_", "pt_fm", "pt_fmrl"])),
    ("anth", ("anth_rcrd_ymd", ["ht_msrm", "wt_msrm", "bmi_vl"])),
    ("diag", ("diag_rgst_ymd", ["diag_cd", "diag_nm", "diag_kcd", "diag_smct"])),
    ("mtst", ("mtdg_ymd", ["mtst_site", "mtst_site_etc"])),
    ("stag", ("diag_stag_rcrd_ymd", ["clnc_"])),
    ("cexm", ("cexm_ymd", ["cexm_"])),
    ("imex", ("imex_ymd", ["imex_", "brst_dens", "micf_yn", "boms_yn", "rtcn_loca", "t4b_", "frnt_prtm", "tumr_msfc",
                           "tumr_rspn", "tumr_emvi", "tumr_msrt", "tumr_exms", "lstm_", "tumr_circ", "tmin_mxdp",
                           "tumr_ansp"])),
    ("bpsy", ("bpsy_ymd", ["bpsy_", "htlg_diag_cd", "htlg_diag_nm", "htlg_dfgd", "htlg_grad_etc", "bpsy_read_ymd"])),
    ("cc",   ("cc_rcrd_ymd", ["cc_cont", "cc_src"])),
    ("obtr", ("obtr_rcrd_ymd", ["menopause_status", "pregnant_at", "history_of_live", "postpartum_at", "fertility_",
                                "marital_status", "menstruation_", "first_menstrual", "menstrual_reg", "pregnancy_",
                                "method_of_conception", "delivery", "marg_", "hrpr_", "hrt_impl", "mena_age", "delv_",
                                "bfpr_", "meno_"])),
    ("hist", ("rcrd_ymd", ["cur_smok", "shis_", "smok_", "nsmk_", "mhis_", "etc_mhis", "ohad_hstr", "dsch_st", "ecog_"])),
    ("note", ("note_date", ["note_"])),
    ("dsch", ("dsch_ymd", [])),       # 퇴원일: 방문 단위 (환자 불변 아님)
])
CANCER_PATIENT = ["histologic_diagnosis", "clinical_stage", "stage_iv_diagnosis_date", "lucn_diag", "brcn_diag",
                  "clcn_diag", "lung_tumr", "otog_mtst", "care_site_id", "death_date", "bwpf_yn", "inob_yn",
                  "fmht_here_clcn", "antp_id", "file_id"]

MASLD_GROUPS = OrderedDict([
    ("score", ("exam_gnrx_ymd", ["fib4_", "apri_", "bard_", "safe_", "lrs_", "exam_gnrx", "age"])),
    ("imex",  ("imex_ymd", ["imex_", "lver_fbrs"])),
    ("hist",  ("rcrd_ymd", ["drnk_", "shis_", "smok_", "exercise_"])),
    ("anth",  ("anth_rcrd_ymd", ["ht_msrm", "wt_msrm", "bmi_vl"])),
    ("oprt",  ("oprt_ymd", ["oprt_"])),
    ("drug",  ("drug_prsc_ymd", ["drug_"])),
    ("proc",  ("procedure_occurrence_crtn_dt", ["procedure_occurrence_id", "care_site_id"])),
    ("note",  ("note_date", ["note_"])),
])
MASLD_PATIENT = ["date_of_birth", "death_date", "file_id"]

LYMPHOMA_GROUPS = OrderedDict([
    ("dx",     ("diagnosis_date", ["diagnosis_status", "lymphoma_group", "cell_lineage", "histologic_", "classification_version", "primary_disease_site"])),
    ("biopsy", ("biopsy_date", ["biopsy_"])),
    ("transf", ("transformation_date", ["transformation_"])),
    ("stage",  ("stage_assessment_date", ["stage_", "ann_arbor", "staging_method", "nodal_", "extranodal_", "spleen_", "bone_marrow_involvement",
                                          "cns_", "bulky_", "largest_lesion", "b_symptom", "unexplained_fever", "drenching_", "weight_loss",
                                          "ecog_", "measurable_", "target_lesion", "sum_product"])),
    ("pet",    ("pet_ct_assessment_date", ["pet_suvmax", "metabolic_tumor", "total_lesion"])),
    ("ihc",    ("ihc_test_date", ["cd3_", "cd5_", "cd10_", "cd15_", "cd19_", "cd20_", "cd22_", "cd23_", "cd30_", "cd79a", "pax5", "bcl2_expr",
                                  "bcl6_expr", "mum1", "myc_expr", "cyclin_d1", "sox11", "alk_", "pd_l1", "ki67", "ebv_", "cell_of_origin",
                                  "double_expressor", "flow_cytometry"])),
    ("mol",    ("molecular_test_date", ["molecular_test", "myc_rearr", "bcl2_rearr", "bcl6_rearr", "double_hit", "t_14_18", "t_11_14",
                                        "tp53_", "complex_karyotype", "clonality"])),
    ("prog",   ("prognostic_score_date", ["ipi_", "aaipi", "nccn_ipi", "flipi", "mipi", "hodgkin_ips", "pit_score"])),
    ("tx",     ("treatment_start_date", ["disease_course", "primary_refractory", "prior_lines", "current_line", "treatment_", "prior_anti",
                                         "prior_anthra", "prior_btk", "prior_checkpoint", "radiotherapy_"])),
    ("sct",    ("stem_cell_transplant_date", ["stem_cell_"])),
    ("cart",   ("car_t_infusion_date", ["car_t_", "leukapheresis", "lymphodepletion"])),
    ("resp",   ("response_assessment_date", ["response_", "deauville", "anatomic_response", "metabolic_response", "best_overall",
                                             "bone_marrow_response", "minimal_residual", "ctdna"])),
    ("outcome",("progression_date", ["relapse_"])),
    ("fu",     ("last_followup_date", ["disease_status_at", "vital_status", "cause_of_death"])),
])
LYMPHOMA_PATIENT = ["hbv_status", "hcv_status", "hiv_status", "death_date", "antp_id", "file_id"]

# DIABETES: 핵심 테이블의 평면 복사본. 그룹 = 원천 OMOP 테이블
DIABETES_GROUPS = OrderedDict([
    ("person",    (None, ["gender_", "year_of_birth", "month_of_birth", "day_of_birth", "birth_datetime", "location_id", "person_source"])),
    ("care_site", (None, ["care_site", "place_of_service"])),
    ("visit",     ("visit_start_date", ["visit_", "admitting_", "discharge_to", "preceding_visit", "provider_id"])),
    ("condition", ("condition_start_date", ["condition_", "stop_reason"])),
    ("measurement", ("measurement_date", ["measurement_", "operator_concept", "value_as", "unit_", "range_", "value_source"])),
    ("drug",      ("drug_exposure_start_date", ["drug_", "verbatim_end", "refills", "amount_", "quantity", "days_supply", "sig",
                                                "route_", "lot_number", "dose_unit"])),
    ("death",     ("death_date", ["death_", "cause_"])),
    ("note",      ("note_date", ["note_"])),
    ("org",       (None, ["medical_dept", "ward_cd", "hsp_tp_cd"])),
])
DIABETES_PATIENT = ["antp_id", "file_id"]

GROUP_DEFS = {
    "LUNG_CANCER": (CANCER_GROUPS, CANCER_PATIENT),
    "BREAST_CANCER": (CANCER_GROUPS, CANCER_PATIENT),
    "COLORECTAL_CANCER": (CANCER_GROUPS, CANCER_PATIENT),
    "MASLD": (MASLD_GROUPS, MASLD_PATIENT),
    "LYMPHOMA": (LYMPHOMA_GROUPS, LYMPHOMA_PATIENT),
    "DIABETES": (DIABETES_GROUPS, DIABETES_PATIENT),
}
KEY_FIELDS = set(FK_REF) | {"lc_id", "bc_id", "cc_id", "masld_id", "dm_id", "lym_id"}

def assign_group(table, name):
    groups, patient = GROUP_DEFS[table]
    if name in KEY_FIELDS and name not in ("antp_id",):
        return "key", None
    for g, (anchor, prefixes) in groups.items():
        if name == anchor:
            return g, anchor
    # 긴 접두어 우선 매칭
    best = None
    for g, (anchor, prefixes) in groups.items():
        for p in prefixes:
            if name.startswith(p) and (best is None or len(p) > best[2]):
                best = (g, anchor, len(p))
    if best:
        return best[0], best[1]
    for p in patient:
        if name.startswith(p):
            return "patient", None
    return "patient", None

# ----------------------------------------------------------------------------
# 수치 범위(타당성) 정의. 필드명 -> [min, max]  (경계 포함)
# ----------------------------------------------------------------------------
RANGES = {
    "year_of_birth": [1900, 2026], "month_of_birth": [1, 12], "day_of_birth": [1, 31], "age_at_index": [0, 110],
    "age": [0, 110], "days_supply": [0, 400], "frequency_per_day": [1, 24], "dosing_interval_day": [1, 180],
    "dosing_number": [1, 500], "amount_value": [0, 100000], "quantity": [0, 100000],
    "smok_qty": [0, 10], "smok_dtrn_ycnt": [0, 90], "nsmk_strt_yr": [1900, 2026],
    "ht_msrm_vl": [100, 230], "wt_msrm_vl": [20, 250], "bmi_vl": [10, 70],
    "lung_tumr_size_vl": [0, 30], "tumr_max_diam_vl": [0, 50], "tumr_wdth_lnth_vl": [0, 50], "tumr_lgtd_lnth_vl": [0, 50],
    "tumr_hght_vl": [0, 50], "srgc_ptem_rslt_tumr_cnt": [0, 20], "plex_rslt_vl": [0, 200], "imem_rslt_vl": [0, 100],
    "rd_gy": [0, 30], "rd_impl_nt": [1, 60], "rd_totl_gy": [0, 100], "rdt_total_dose_gy": [0, 100],
    "radiotherapy_total_dose_gy": [0, 100],
    "totl_ln_cnt": [0, 200], "pstv_ln_cnt": [0, 200], "slnd_totl_cnt": [0, 30], "pstv_slnd_cnt": [0, 30],
    "hrt_impl_mcnt": [0, 600], "mena_age_vl": [8, 20], "delv_age_vl": [12, 55], "delv_chld_cnt": [0, 15], "meno_age_vl": [30, 65],
    "mlem_rslt_vl": [0, 100], "amsn_vainf_b_vl": [0, 100000],
    "rtcn_loca_dst_vl": [0, 20], "tumr_msfc_shrt_dst_vl": [0, 100], "lstm_anvg_dst_vl": [0, 20], "lstm_anju_dst_vl": [0, 20],
    "tmin_mxdp_vl": [0, 50], "ansc_loca_dst_vl": [0, 30], "ebl_qty": [0, 10000], "drug_mdct_dtrn_mcnt": [0, 240],
    "drug_prsc_capa": [0, 100000], "drug_prsc_dcnt": [0, 400],
    "fib4_score": [0, 50], "apri_score": [0, 30], "bard_score": [0, 4], "safe_score": [-50, 300], "lrs_score": [0, 30],
    "drnk_dtrn_ycnt": [0, 90], "drnk_nt": [0, 31], "drnk_qty": [0, 20], "exercise_ycnt": [0, 90], "exercise_nt": [0, 14],
    "exercise_tm": [0, 600], "exam_gnrx_rslt_vl": [-100, 1000], "exam_gnrx_input_nm_vl": [0, 100000],
    "nodal_regions_involved_count": [0, 20], "extranodal_site_count": [0, 20], "bone_marrow_involvement_pct": [0, 100],
    "bulky_disease_threshold_cm": [5, 15], "largest_lesion_diameter_cm": [0, 40], "weight_loss_6mo_pct": [0, 100],
    "ecog_performance_status": [0, 5], "target_lesion_count": [0, 10], "sum_product_diameters": [0, 100000],
    "pet_suvmax": [0, 100], "metabolic_tumor_volume": [0, 10000], "total_lesion_glycolysis": [0, 100000],
    "ki67_proliferation_index_pct": [0, 100], "ipi_score": [0, 5], "aaipi_score": [0, 3], "nccn_ipi_score": [0, 8],
    "flipi_score": [0, 5], "flipi2_score": [0, 5], "mipi_score": [0, 15], "hodgkin_ips_score": [0, 7], "pit_score": [0, 4],
    "prior_lines_of_therapy_count": [0, 15], "current_line_of_therapy": [1, 15], "treatment_cycle_count": [0, 50],
    "deauville_score": [1, 5], "regimen_or_line_of_therapy": [1, 15], "number_of_cycles": [0, 60],
    "refills": [0, 50], "value_as_number": [-1000000, 1000000], "range_low": [-1000000, 1000000], "range_high": [-1000000, 1000000],
}
# 문자열 패턴(적합성)
PATTERNS = {
    "clinical_stage": r"^(0|IA[1-3]?|IB|IIA|IIB|IIIA|IIIB|IIIC|IVA|IVB|IV|I|II|III)$",
    "ann_arbor_lugano_stage": r"^(I|II|III|IV)$",
    "stage_suffix": r"^[ABES]{1,3}$",
    "afop_path_t_stag_vl": r"^(y?p?)(T(is|0|X|1[abc]?(mi)?|2[ab]?|3|4[abcd]?))$",
    "afop_path_n_stag_vl": r"^(y?p?)(N(X|0|1[abc]?|2[abc]?|3[abc]?))$",
    "afop_path_m_stag_vl": r"^(y?p?)(M(X|0|1[abc]?))$",
    "clnc_t_stag_vl": r"^(c?)(T(is|0|X|1[abc]?(mi)?|2[ab]?|3|4[abcd]?))$",
    "clnc_n_stag_vl": r"^(c?)(N(X|0|1[abc]?|2[abc]?|3[abc]?))$",
    "clnc_m_stag_vl": r"^(c?)(M(X|0|1[abc]?))$",
    "lucn_diag_kncd": r"^C34\.?[0-9]?$|^C[0-9]{2}\.?[0-9]?$|^[A-Z][0-9]{2}\.?[0-9]?$",
    "brcn_diag_kncd": r"^(C50|D05)\.?[0-9]?$|^[A-Z][0-9]{2}\.?[0-9]?$",
    "clcn_diag_kncd": r"^(C1[89]|C20|C21)\.?[0-9]?$|^[A-Z][0-9]{2}\.?[0-9]?$",
    "diag_kcd_cd": r"^[A-Z][0-9]{2}\.?[0-9]{0,2}$",
    "cexm_loinc_cd": r"^[0-9]{1,6}-[0-9]$",
    "ecog_cd": r"^[0-5]$",
}

# ----------------------------------------------------------------------------
# 코드표 추출: 설명문의 "1=..., 2=..." 패턴
# ----------------------------------------------------------------------------
CODE_RE = re.compile(r"(?<![\w.])(\d{1,2})\s*[=:]\s*([^/,\n;]+?)(?=\s*(?:[/,;\n]|$|\d{1,2}\s*[=:]))")
def extract_codes(desc):
    if "=" not in desc: return None
    found = CODE_RE.findall(desc)
    if len(found) < 2: return None
    codes = OrderedDict()
    for k, v in found:
        v = v.strip().rstrip(".)").strip()
        if k not in codes: codes[k] = v
    return codes

EX_RE = re.compile(r"예[:：]\s*([^.\n]+)")
def extract_examples(desc):
    m = EX_RE.search(desc)
    if not m: return None
    vals = [v.strip().rstrip(".") for v in re.split(r",|、", m.group(1)) if v.strip()]
    return vals if len(vals) >= 2 else None

# ----------------------------------------------------------------------------
# OMOP 표준 concept 허용집합 (결정 D-08). 병원은 config 로 확장 가능.
# ----------------------------------------------------------------------------
OMOP_SETS = OrderedDict([
    ("gender_concept_id", {"8507": "MALE", "8532": "FEMALE"}),
    ("visit_concept_id", {"9201": "Inpatient Visit", "9202": "Outpatient Visit", "9203": "Emergency Room Visit",
                          "262": "Emergency Room and Inpatient Visit"}),
    ("visit_type_concept_id", {"32817": "EHR", "32879": "Registry", "32810": "Claim"}),
    ("procedure_type_concept_id", {"32817": "EHR", "32879": "Registry", "32810": "Claim"}),
    ("condition_type_concept_id", {"32817": "EHR", "32879": "Registry", "32810": "Claim", "32840": "EHR problem list"}),
    ("measurement_type_concept_id", {"32817": "EHR", "32856": "Lab", "32879": "Registry"}),
    ("observation_type_concept_id", {"32817": "EHR", "32879": "Registry"}),
    ("note_type_concept_id", {"32817": "EHR", "44814637": "Radiology report", "44814640": "Pathology report",
                              "44814641": "Discharge summary", "44814645": "Outpatient note", "32831": "EHR note"}),
    ("note_class_concept_id", {"36716164": "Radiology note", "36716165": "Pathology note", "36716213": "Discharge summary",
                               "36716177": "Progress note", "44814641": "Discharge summary", "3040218": "Oncology note"}),
    ("adverse_event_type_concept_id", {"32817": "EHR", "32879": "Registry"}),
    ("amount_unit_concept_id", {"8576": "mg", "8587": "mL", "9655": "ug", "8510": "unit", "8718": "IU", "9551": "mg/m2",
                                "8504": "mg/kg", "8573": "mmol"}),
    ("unit_concept_id", {"8576": "mg", "8587": "mL", "8840": "mg/dL", "8753": "mmol/L", "8554": "%", "8645": "U/L",
                         "8848": "10^3/uL", "8961": "10^3/mm3", "8582": "cm", "9529": "kg", "9531": "kg/m2",
                         "8876": "mmHg", "8713": "g/dL", "8555": "ng/mL", "8847": "10^6/uL", "8629": "ug/L", "8749": "umol/L",
                         "9550": "mL/min/1.73m2", "8636": "ng/mL", "8859": "mg/L", "9435": "ug/dL", "8641": "mIU/mL"}),
    ("numerator_unit_concept_id", {"8576": "mg", "9655": "ug", "8718": "IU", "8510": "unit"}),
    ("denominator_unit_concept_id", {"8587": "mL", "8576": "mg", "8582": "cm", "9529": "kg"}),
    ("severity_concept_id", {"1": "CTCAE Grade 1", "2": "CTCAE Grade 2", "3": "CTCAE Grade 3", "4": "CTCAE Grade 4", "5": "CTCAE Grade 5"}),
    ("causality_concept_id", {"1": "Certain", "2": "Probable", "3": "Possible", "4": "Unlikely", "5": "Unrelated", "6": "Unassessable"}),
    ("seriousness_concept_id", {"1": "Death", "2": "Life-threatening", "3": "Hospitalization", "4": "Disability", "5": "Congenital anomaly", "6": "Other medically important"}),
    ("outcome_concept_id", {"1": "Recovered", "2": "Recovering", "3": "Not recovered", "4": "Recovered with sequelae", "5": "Fatal", "6": "Unknown"}),
    ("action_taken_concept_id", {"1": "None", "2": "Dose reduced", "3": "Interrupted", "4": "Withdrawn", "5": "Not applicable", "6": "Unknown"}),
])
# 이상사례 코드는 사전에 정의가 없어 임시 코드표(1~6)로 둔다. 결정 D-05 / 이슈 I-13 참조.

# ----------------------------------------------------------------------------
# 빌드
# ----------------------------------------------------------------------------
issues = []
def issue(code, table, field, text, sev="major"):
    issues.append(dict(id=f"I-{len(issues)+1:02d}", code=code, table=table, field=field, severity=sev, text=text))

codelists = OrderedDict()
tables = OrderedDict()

for tname, tinfo in RAW.items():
    has_req_col = "필수" in tinfo["header"]
    if not has_req_col:
        issue("NO_REQUIRED_COLUMN", tname, "", "특화 테이블 시트에 '필수' 열이 없어 완전성 규칙을 정의할 수 없음. 명세에서는 PK/person_id 만 필수로 지정하고, 나머지는 이벤트 그룹 규칙(anchor 날짜 조건부 필수)으로 대체함.")
    seen = Counter(f["필드명"] for f in tinfo["fields"])
    for fname, c in seen.items():
        if c > 1:
            issue("DUPLICATE_FIELD", tname, fname, f"동일 필드가 {c}회 정의됨. 첫 정의만 유지.")
    fields = OrderedDict()
    pk = None
    for f in tinfo["fields"]:
        name = f["필드명"].strip()
        if name in fields:
            continue
        raw_type = f.get("데이터 타입", "")
        desc = f.get("설명", "")
        key = f.get("PK/FK", "").strip().upper()
        t = norm_type(raw_type, name, desc)
        if t is None:
            issue("MISSING_TYPE", tname, name, "데이터 타입이 비어 있음.")
        if (tname, name) in FORCE_TYPE:
            nt = FORCE_TYPE[(tname, name)]
            if t != nt:
                issue("TYPE_CORRECTED", tname, name, f"타입 '{raw_type}' -> '{nt}' 로 교정 (이름/설명상 {nt}).", "minor")
            t = nt
        if t == "varchar" and re.search(r"_date$|_ymd$", name):
            issue("DATE_AS_VARCHAR", tname, name, "날짜 필드가 varchar 로 선언됨.")
        if t == "date" and name.startswith("days_"):
            issue("NAME_TYPE_MISMATCH", tname, name, "이름은 일수(days_)인데 타입은 DATE. 값은 PD 발생일로 해석하고 progression_date 로 개명 권고.")
        if "RBDMS" in raw_type or "RDBMS" in raw_type:
            issue("VENDOR_TYPE", tname, name, f"타입 '{raw_type}' 은 DBMS 종속 표기. 'text' 로 정규화.", "minor")

        new_name = RENAME.get(name, name)
        if new_name != name:
            issue("FK_NAME_INCONSISTENT", tname, name, f"외래키 이름 '{name}' 을 '{new_name}' 으로 통일 (ANTP_THERAPY.antp_id, DRUG_EXPOSURE.antp_id 와 일치).")

        # 필수
        if has_req_col:
            req_raw = f.get("필수", "").strip().upper()
            required = (req_raw == "Y")
            if req_raw == "" and key != "PK":
                issue("MISSING_REQUIRED_FLAG", tname, name, "필수 여부가 비어 있음. 기본값 N 적용.", "minor")
        else:
            required = key == "PK" or new_name == "person_id"
        if (tname, new_name) in FORCE_REQUIRED:
            fr = FORCE_REQUIRED[(tname, new_name)]
            if has_req_col and fr != required:
                issue("REQUIRED_CORRECTED", tname, new_name, f"필수 여부 {'Y' if required else 'N'} -> {'Y' if fr else 'N'} 로 교정.", "minor")
            required = fr
        if key == "PK":
            required = True
            pk = new_name

        fd = OrderedDict(name=new_name, type=t or "varchar", required=required, desc=desc)
        if key == "PK": fd["key"] = "PK"
        if new_name in FK_REF and new_name != pk:
            fd["key"] = "FK"; fd["ref"] = FK_REF[new_name]
            if key != "FK" and tname not in ("PERSON",):
                issue("FK_NOT_MARKED", tname, new_name, f"참조 필드인데 PK/FK 열에 FK 표시가 없음 -> FK({FK_REF[new_name]}) 로 지정.", "minor")
        elif new_name in EXTERNAL_REF:
            fd["key"] = "FK_EXTERNAL"; fd["ref"] = EXTERNAL_REF[new_name]
            if new_name != "care_site_id" or tname == "PERSON":
                issue("EXTERNAL_TABLE_REF", tname, new_name, f"사전에 정의되지 않은 테이블({EXTERNAL_REF[new_name]}) 참조. 참조무결성 검사 제외.", "minor")
        # 코드표
        codes = extract_codes(desc)
        if codes:
            cl_name = f"{tname}.{new_name}"
            codelists[cl_name] = codes
            fd["codelist"] = cl_name
            issue("CODES_IN_DESCRIPTION", tname, new_name, f"코드값 {len(codes)}개가 설명문에 텍스트로 포함됨 -> codelists.yaml 로 분리.", "minor")
        elif new_name in OMOP_SETS:
            fd["codelist"] = f"OMOP.{new_name}"
        elif (new_name.endswith("_yn") or new_name == "is_serious") and t == "integer":
            fd["codelist"] = "COMMON.yn01"
        ex = extract_examples(desc)
        if ex and not codes:
            fd["suggested_values"] = ex
        # 범위/패턴
        if new_name in RANGES and t in ("integer", "float"):
            fd["range"] = RANGES[new_name]
        if new_name in PATTERNS:
            fd["pattern"] = PATTERNS[new_name]
        if re.search(r"구분자|\"_\"", desc):
            fd["multivalued"] = True
            issue("MULTIVALUED_FIELD", tname, new_name, "한 필드에 여러 값을 구분자로 연결하도록 정의됨. 반복 행(long) 적재 권고.", "minor")
        # 그룹
        if tname in GROUP_DEFS:
            g, anchor = assign_group(tname, new_name)
            fd["group"] = g
            if anchor and anchor != new_name:
                fd["anchor"] = anchor
            fd["level"] = "person" if g == "patient" else ("key" if g == "key" else "event")
        fields[new_name] = fd

    tables[tname] = OrderedDict(name=tname, kor=tinfo["kor"], section=tinfo["section"],
                                category=("core" if tname in CORE else "disease" if tname in DISEASE else "common_ext"),
                                pk=pk, fields=list(fields.values()))

# ----------------------------------------------------------------------------
# 테이블 수준 결정/그룹 메타
# ----------------------------------------------------------------------------
for tname, (groups, patient) in GROUP_DEFS.items():
    present = {f["name"] for f in tables[tname]["fields"]}
    for f in tables[tname]["fields"]:
        if f.get("anchor") and f["anchor"] not in present:
            issue("GROUP_WITHOUT_ANCHOR", tname, f["name"], f"그룹 '{f['group']}' 의 anchor 날짜 {f['anchor']} 가 이 테이블에 없음. 기록일 필드 추가 권고. anchor 규칙 생략.", "minor")
            del f["anchor"]
    tables[tname]["grain"] = ("1행 = 1 이벤트 그룹 인스턴스 (person_id, visit_occurrence_id, group). "
                              "group='patient' 필드는 동일 person_id 의 모든 행에서 값이 동일해야 한다.")
    tables[tname]["groups"] = OrderedDict((g, dict(anchor=a if a in present else None)) for g, (a, _) in groups.items())
    tables[tname]["groups"]["patient"] = dict(anchor=None)

# DIABETES 특수 이슈
issue("DENORMALIZED_COPY", "DIABETES", "", "특화 테이블이 PERSON/CARE_SITE/VISIT/CONDITION/MEASUREMENT/DRUG/DEATH/NOTE 의 평면 복사본이며 당뇨병 고유 항목이 거의 없음. 명세에서는 핵심 테이블과의 값 일치 규칙(교차검증)으로 처리하고, 구조 재설계 권고.")
issue("GRAIN_UNDEFINED", "LUNG_CANCER,BREAST_CANCER,COLORECTAL_CANCER,MASLD,LYMPHOMA,DIABETES", "",
      "특화 테이블의 행 단위(환자당/방문당/검사당)가 정의되지 않음. 결정 D-01 로 '이벤트 그룹' 단위를 부여.", "critical")
issue("LOCAL_CODE_UNVERIFIABLE", "LUNG_CANCER,BREAST_CANCER,COLORECTAL_CANCER,MASLD", "*_kncd, *_cd",
      "LOCAL/EDI 코드는 중앙에서 검증 불가. 병원별 코드 매핑표(코드, 명칭, 표준코드) 제출을 요구하고, 검증은 코드-명칭 1:1 일관성만 수행.")
issue("AE_CODES_UNDEFINED", "ADVERSE_EVENT", "severity/causality/seriousness/outcome/action_taken_concept_id",
      "코드체계가 정의되지 않음. 임시로 CTCAE grade(1-5) 및 WHO-UMC 인과성 등 1~6 코드표를 부여. 팀 확정 필요.")
issue("INDEX_DATE_UNDEFINED", "PERSON", "age_at_index", "index date 의 정의가 없음. 결정 D-12: 코호트 정의 진단의 최초 condition_start_date.")
issue("ANTP_IN_NONCANCER", "MASLD,DIABETES", "antp_id",
      "항암 테이블이 없는 코호트의 특화 테이블에 antp_id 외래키가 존재. 해당 코호트에서는 항상 NULL 이어야 함.", "minor")
issue("DRUG_CONDITIONAL_FK", "DRUG_EXPOSURE", "antp_id, note_id",
      "필수(Y)로 지정되었으나 비항암제/비항암 코호트에서는 채울 수 없음. 조건부 필수(항암제이면 antp_id 필수)로 교정.")

# ----------------------------------------------------------------------------
# 저장
# ----------------------------------------------------------------------------
def dump(obj, path):
    class D(yaml.SafeDumper): pass
    D.add_representer(OrderedDict, lambda d, data: d.represent_dict(data.items()))
    with open(path, "w", encoding="utf-8") as fh:
        yaml.dump(obj, fh, Dumper=D, allow_unicode=True, sort_keys=False, width=140)

spec = OrderedDict(
    meta=OrderedDict(name="K-AI 질환별 코호트 CDM 명세", version="0.1.0", source="매뉴얼 초안_20260813.xlsx",
                     generated_by="spec/build_spec.py", decisions="internal/decisions/DECISIONS.md"),
    tables=tables,
)
dump(spec, "spec/kai_cdm_spec.yaml")
codelists_common = OrderedDict([("COMMON.yn01", OrderedDict([("1", "Yes"), ("0", "No")]))])
dump(OrderedDict(embedded=codelists, common=codelists_common, omop=OrderedDict((f"OMOP.{k}", v) for k, v in OMOP_SETS.items())), "spec/codelists.yaml")
dump(OrderedDict(cohorts=COHORTS), "spec/cohort_profiles.yaml")

sev_order = {"critical": 0, "major": 1, "minor": 2}
issues.sort(key=lambda x: (sev_order[x["severity"]], x["code"], x["table"]))
for i, it in enumerate(issues): it["id"] = f"I-{i+1:02d}"
with open("internal/decisions/dictionary_issues.md", "w", encoding="utf-8") as fh:
    fh.write("# 데이터 사전 결함 목록 (자동 검출 + 수동 검토)\n\n")
    fh.write(f"원본: 매뉴얼 초안_20260813.xlsx / 생성: build_spec.py / 총 {len(issues)}건\n\n")
    fh.write("| ID | 심각도 | 코드 | 테이블 | 필드 | 내용 |\n|---|---|---|---|---|---|\n")
    for it in issues:
        fh.write(f"| {it['id']} | {it['severity']} | {it['code']} | {it['table']} | {it['field']} | {it['text']} |\n")
json.dump(issues, open("internal/decisions/dictionary_issues.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

nf = sum(len(t["fields"]) for t in tables.values())
print(f"tables={len(tables)} fields={nf} codelists={len(codelists)} issues={len(issues)}")
for t in tables.values():
    if "groups" in t:
        c = Counter(f["group"] for f in t["fields"])
        print(t["name"], dict(c))
