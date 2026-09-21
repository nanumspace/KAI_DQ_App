# -*- coding: utf-8 -*-
"""사전 v2.2 · v1 미승격 필드 분류.

배치표가 '이동/이관→코어'라고 한 v1 컬럼 중, 어떤 v2 항목도 '현 명세 대응 필드'로
지목하지 않은 것이 미승격으로 남는다. 그런데 그 수(575)는 실제 누락이 아니라 대부분
기록·연결의 문제다. 그대로 575줄을 내놓으면 팀이 검토할 수 없으므로 다섯으로 나눈다.

  키·외래키                    데이터 항목이 아니다. 볼 것 없다.
  코드·명칭 쌍의 명칭쪽          v1 은 코드와 명칭을 두 컬럼으로 받았고 v2 는 concept_id
                              하나로 받는다. 구조가 흡수한 것이라 승격 대상이 아니다.
  v2 에 이미 대응 있음          서식 필드·코어 파생 변수·값 집합 중에 같은 뜻이 이미 있다.
                              배치표에 대응 필드를 적어 넣으면 이 목록에서 빠진다.
  부분 일치                    비슷한 것이 있으나 같은지 사람이 봐야 한다.
  대응 확인(검토 완료)          어림이 놓쳤으나 사람이 대조해 v2 자리를 적어 둔 것 (RESOLVED).
  제외(사유 기록)              v2 에 두지 않기로 한 것과 그 이유 (DROPPED).
  대응 없음                    남은 것. 팀이 정해야 한다 (PENDING 에 이유).

분류는 낱말 겹침으로 하는 어림이라 완벽하지 않다. 특히 '수술을 시행한 연월일'과
'수술일'처럼 같은 뜻인데 낱말이 어긋나면 '대응 없음'으로 잘못 떨어진다. 그래서
'대응 없음'은 승격해야 할 목록이 아니라 **사람이 볼 목록**으로 읽어야 한다.
"""
import re

PAIR_SUFFIX = [("_spnm", "_spcd"), ("_knnm", "_kncd"), ("_nm", "_cd")]
# 낱말 겹침을 셀 때 빼는 흔한 말 — 어느 설명에나 나와 변별력이 없다.
STOP = {"코드값", "명칭", "여부", "시행", "확인", "해당", "사용", "경우", "환자", "기록",
        "수집", "위한", "이다", "나타내는", "대한", "정보", "내용", "구분", "기타"}

BUCKETS = ["키·외래키", "코드·명칭 쌍의 명칭쪽", "v2 에 이미 대응 있음", "대응 확인(검토 완료)", "제외(사유 기록)", "부분 일치", "대응 없음"]

# ---------------------------------------------------------------------------------------------
# 2026-09-21 검토 결과. 낱말 겹침이 '대응 없음'·'부분 일치'로 떨어뜨린 232개를 하나하나 v2 와 대조했다.
# 어림 분류가 놓친 이유는 둘이다 — (1) OMOP 코어 컬럼(처방일·투여경로·단위·퇴원일·진단코드…)은
# 서식 필드가 아니라 라벨 풀에 없었다, (2) 영문 표기(Residual Tumor, Gross type)와 한글 표기가 어긋났다.
# 아래는 v1 필드명(테이블 무관) → v2 자리. 테이블까지 특정해야 하면 'TABLE.field' 키를 쓴다.
RESOLVED = {
    # ---- OMOP 코어 컬럼으로 흡수 (EHR 추출본에서 그대로 온다)
    "diag_cd": "CONDITION_OCCURRENCE.condition_source_value",
    "diag_kcd_cd": "CONDITION_OCCURRENCE.condition_concept_id (KCD) · COHORT_INDEX.세부 진단명",
    "diag_smct_cd": "CONDITION_OCCURRENCE.condition_concept_id · COHORT_INDEX.세부 진단명",
    "cexm_ymd": "MEASUREMENT.measurement_date",
    "cexm_kncd": "MEASUREMENT.measurement_source_value",
    "cexm_loinc_cd": "MEASUREMENT.measurement_concept_id (LOINC)",
    "cexm_rslt_cont": "MEASUREMENT.value_as_number · value_source_value",
    "cexm_rslt_unit_cont": "MEASUREMENT.unit_concept_id · unit_source_value",
    "imex_ymd": "PROCEDURE_OCCURRENCE.procedure_date · *_EXAM.검사일",
    "imex_kncd": "PROCEDURE_OCCURRENCE.procedure_source_value",
    "imex_smct_cd": "PROCEDURE_OCCURRENCE.procedure_concept_id (SNOMED)",
    "brex_ymd": "파생 변수 · 기관지내시경 검사 시행일 (PROCEDURE_OCCURRENCE)",
    "plex_ymd": "MEASUREMENT.measurement_date (PFT_ITEM)",
    "plex_spcd": "파생 변수 · 폐기능검사 항목",
    "plex_kncd": "파생 변수 · 폐기능검사 항목 (MEASUREMENT.measurement_concept_id)",
    "plex_rslt_vl": "파생 변수 · 폐기능검사 결과값",
    "anth_rcrd_ymd": "MEASUREMENT.measurement_date (신장·체중)",
    "ht_msrm_vl": "MEASUREMENT (LOINC 신장 3036277)",
    "wt_msrm_vl": "MEASUREMENT (LOINC 체중 3025315)",
    "bmi_vl": "MEASUREMENT (LOINC BMI 3038553) · 의미 규칙이 신장·체중과 대조",
    "drug_prsc_ymd": "DRUG_EXPOSURE.drug_exposure_start_date",
    "drug_prsc_dcnt": "DRUG_EXPOSURE.days_supply",
    "drug_prsc_capa": "DRUG_EXPOSURE.quantity",
    "drug_prsc_capa_unit_cd": "DRUG_EXPOSURE.dose_unit_source_value",
    "drug_mdct_dtrn_mcnt": "DRUG_EXPOSURE.drug_exposure_start_date ~ end_date",
    "drin_cd": "DRUG_EXPOSURE.drug_concept_id (성분)",
    "drug_rxnm_cd": "DRUG_EXPOSURE.drug_source_concept_id (RxNorm)",
    "drug_injc_pth_cd": "DRUG_EXPOSURE.route_concept_id",
    "drug_clcd": "값 집합 DRUG_CLASS_SET (ATC) · 파생 변수",
    "drug_clnm": "값 집합 DRUG_CLASS_SET (ATC) 라벨",
    "dsch_ymd": "VISIT_OCCURRENCE.visit_end_date",
    "cc_rcrd_ymd": "OBSERVATION.observation_date (주증상)",
    "cc_cont": "OBSERVATION.value_as_string · NOTE",
    "rcrd_ymd": "OBSERVATION.observation_date (흡연·음주·운동 파생 변수의 기록일)",
    "fmht_rcrd_ymd": "FAMILY_HISTORY.기록일",
    "cause_of_death": "DEATH.cause_concept_id · cause_source_value (파생 변수 사망 원인)",
    # ---- 서식 필드에 이미 있음 (표기가 달라 놓친 것)
    "bpsy_ymd": "PATHOLOGY_REPORT.검체 채취일 · SPECIMEN.specimen_date",
    "biopsy_date": "PATHOLOGY_REPORT.검체 채취일",
    "bpsy_mthd_kncd": "PATHOLOGY_REPORT.생체검사 시행 방법",
    "biopsy_method": "PATHOLOGY_REPORT.생체검사 시행 방법",
    "bpsy_site_cd": "PATHOLOGY_REPORT.생체검사 대상 부위 or 검체",
    "bpsy_site_latr_cd": "PATHOLOGY_REPORT.생체검사 부위 편측성",
    "bpsy_rslt_cont": "PATHOLOGY_REPORT.생체검사에 따른 조직학적 진단명 · 전문은 NOTE",
    "resi_tumr_cd": "PATHOLOGY_REPORT.잔존종양(Residual Tumor) 분류",
    "gros_tpcd": "PATHOLOGY_REPORT.Gross type 분류 명칭",
    "inva_dgre_cd": "PATHOLOGY_REPORT.종양 침윤 깊이 정도",
    "sgpt_micf_ex_yn_spcd": "PATHOLOGY_REPORT.미세석회화 여부",
    "micf_yn_unid_spcd": "PATHOLOGY_REPORT.유방촬영술상 미세석회화 여부",
    "lver_fbrs_grnm": "PATHOLOGY_REPORT.간실질 섬유화 등급명",
    "tumr_hght_vl": "PATHOLOGY_TUMOR (종양 크기 치수)",
    "imem_ymd": "BIOMARKER.검사일", "mlem_ymd": "BIOMARKER.검사일", "gmt_ymd": "BIOMARKER.검사일",
    "gmvx_ymd": "BIOMARKER.검사일", "ihc_test_date": "BIOMARKER.검사일",
    "imem_opn_cd": "BIOMARKER.면역조직화학병리 검사 (마커별 결과 컬럼)",
    "mlem_opn_cd": "BIOMARKER.분자병리 검사 (마커별 결과 컬럼)",
    "imem_rslt_cont": "BIOMARKER 마커별 결과 컬럼 · 결론 전문은 NOTE",
    "mlem_rslt_cont": "BIOMARKER 마커별 결과 컬럼 · 결론 전문은 NOTE",
    "pavr_detect_yn_spcd": "BIOMARKER.Pathogenic 검출 여부",
    "uncl_varnt_detect_yn_spcd": "BIOMARKER.Unclassified Variant 검출 여부",
    "dna_vainf_b_cd": "BIOMARKER.DNA 변이 정보 B 값", "dna_vainf_c_cd": "BIOMARKER.DNA 변이 정보 C 값",
    "hodgkin_ips_score": "LYMPHOMA_ASSESSMENT.호지킨림프종 IPS 총점",
    "ipi_risk_group": "LYMPHOMA_ASSESSMENT.IPI 위험군", "mipi_c_risk_group": "LYMPHOMA_ASSESSMENT.MIPI-c 위험군",
    "pit_score": "LYMPHOMA_ASSESSMENT.말초T세포림프종 PIT 총점",
    "unexplained_fever_yn": "LYMPHOMA_ASSESSMENT.원인불명 발열 여부",
    "b_symptom_yn": "LYMPHOMA_ASSESSMENT.B 증상 여부",
    "ann_arbor_lugano_stage": "STAGING.Ann Arbor/Lugano 병기",
    "stage_assessment_date": "STAGING.병기 평가일", "stage_suffix": "STAGING.병기 수식자",
    "staging_method": "STAGING.병기 결정 방법",
    "mtdg_ymd": "STAGING.원격 전이 진단일", "mtst_site_etc_cont": "STAGING.원격 전이 부위 (원천값)",
    "clnc_tumr_prty_cd": "STAGING.임상 종양 특성",
    "afop_asmt_item_cd": "STAGING.수술치료 후 평가 내용", "afop_asmt_item_etc_cont": "STAGING.수술치료 후 평가 내용 (원천값)",
    "oprt_ymd": "SURGERY.수술 시행일", "oprt_kncd": "SURGERY.수술명 (EDI 참조표)",
    "oprt_prps_cd": "SURGERY.수술 목적", "oprt_mtcd": "SURGERY.수술 방법",
    "anes_mthd_detl_spcd": "COLORECTAL_SURGERY_DETAIL.문합 방법 세부 내용",
    "anes_mthd_detl_clsf_etc_cont": "COLORECTAL_SURGERY_DETAIL.문합 방법 세부 내용 (원천값)",
    "anes_mthd_etc_cont": "COLORECTAL_SURGERY_DETAIL.문합 방법 (원천값)",
    "ima_ligt_loca_spcd": "COLORECTAL_SURGERY_DETAIL.IMA ligation 위치",
    "afoc_trtm_mtcd": "ADVERSE_EVENT.합병증 치료방법",
    "bwpf_yn_unid_spcd": "ADVERSE_EVENT.장천공 여부", "inob_yn_unid_spcd": "ADVERSE_EVENT.장폐색 여부",
    "stem_cell_transplant_type": "LYMPHOMA_EVENT.조혈모세포이식 유형",
    "transformation_date": "LYMPHOMA_EVENT.조직학적 전환 확정일",
    "leukapheresis_date": "LYMPHOMA_EVENT.백혈구성분채집일",
    "car_t_product_source_value": "LYMPHOMA_EVENT.CAR-T 표적 항원 (제품명은 원천값)",
    "pet_suvmax": "LYMPHOMA_EXAM.PET 최고 SUVmax",
    "deauville_score": "RESPONSE_ASSESSMENT.Deauville 5점 척도",
    "response_criteria": "RESPONSE_ASSESSMENT.적용 반응평가 기준",
    "response_assessment_timepoint": "RESPONSE_ASSESSMENT.반응평가 시점",
    "anatomic_response": "RESPONSE_ASSESSMENT.해부학적 반응",
    "progression_date": "RESPONSE_ASSESSMENT.질환 경과 상태 + 기준일 · ANTP_THERAPY.days_to_progression",
    "rldg_ymd": "RESPONSE_ASSESSMENT.암 재발 진단일", "rlps_site_cd": "RESPONSE_ASSESSMENT.암 재발 부위",
    "rdt_prsc_ymd": "RADIOTHERAPY.방사선치료 처방일", "rdt_kncd": "RADIOTHERAPY.방사선치료명",
    "treatment_end_date": "ANTP_THERAPY.antp_end_date",
    "diagnosis_date": "COHORT_INDEX.최초 림프종 진단일", "diagnosis_status": "COHORT_INDEX.진단 상태",
    "lymphoma_group": "COHORT_INDEX.림프종 대분류", "last_followup_date": "COHORT_INDEX.최종 추적관찰일",
    "classification_version": "COHORT_INDEX.WHO/ICC 기준 조직학적 아형 (분류 판은 원천값에)",
    "fmht_yn_noans_spcd": "FAMILY_HISTORY.가족력 여부", "pt_fm_rlnm": "FAMILY_HISTORY.가족력 대상자와의 관계",
    "pt_fmrl_etc_cont": "FAMILY_HISTORY.가족력 대상자와의 관계 (원천값)",
    "fmhs_etc_yn_noans_spcd": "FAMILY_HISTORY.가족 질환(암종 외)",
    "fmht_here_clcn_clsf_etc_cont": "파생 변수 · 유전성 대장암 여부 (원천값)",
    "obtr_rcrd_ymd": "BREAST_BASELINE.기록일", "marg_yn_noans_spcd": "BREAST_BASELINE.결혼 여부",
    "marg_detl_cd": "BREAST_BASELINE.결혼상태 상세 구분", "meno_yn_noans_spcd": "BREAST_BASELINE.폐경 여부",
    "method_of_conception": "BREAST_BASELINE.임신 방법", "pregnancy_outcome": "BREAST_BASELINE.임신 결과",
    "fertility_treatment_type_other": "BREAST_BASELINE.가임력 보존 치료 기타 내용",
    "brst_dens_clcd": "BREAST_EXAM.유방촬영술상 유방 밀도", "brst_dens_clnm": "BREAST_EXAM.유방촬영술상 유방 밀도 (라벨)",
    # ---- 파생 변수(코어에서 계산)로 흡수
    "shis_yn_noans_spcd": "파생 변수 · 흡연력 여부", "smok_dtrn_ycnt": "파생 변수 · 총 흡연기간",
    "drnk_dtrn_ycnt": "파생 변수 · 총 음주기간", "exercise_ycnt": "파생 변수 · 총 운동기간",
    "mhis_etc_rptd_cont_cd": "파생 변수 · 과거 기타 호흡기질환 내용",
    "etc_mhis_yn_noans_spcd": "파생 변수 · 과거 병력 여부",
    "mhis_dbt_yn_noans_spcd": "파생 변수 · 과거 당뇨병 여부", "mhis_cncr_yn_noans_spcd": "파생 변수 · 과거 암 병력 여부",
}

# v2 에 자리를 두지 않기로 한 것. 데이터가 아니라 기록 체계의 메타데이터거나, 서식의 원천값이 대신한다.
DROPPED = {
    "procedure_occurrence_crtn_dt": "행위처방 레코드의 생성 일시. 임상 값이 아니라 원천 시스템의 감사 정보",
    "cc_src_spcd": "주증상을 어느 기록지에서 옮겼는지. OBSERVATION.observation_type_concept_id 가 출처 종류를 맡는다",
    "impt_read_ymd": "병리 판독일. v2 는 검체 채취일만 둔다 — 판독 소요일이 필요해지면 PATHOLOGY_REPORT 에 report_date 를 더한다",
    "mlpt_read_ymd": "병리 판독일. 위와 같다",
    "bpsy_read_ymd": "병리 판독일. 위와 같다",
    "ohad_hstr_yn_noans_spcd": "타병원 진단 후 전원 여부. 코호트 정의 항목이 아니며 필요하면 OBSERVATION 한 개념으로 받는다",
    "file_id": "영상·이미지 파일 참조. 코호트 DB 는 영상 파일을 담지 않는다 (2026-09-21 결정). 담게 되면 IMAGE 확장 표를 둔다",
}

# v2 에 자리가 없고 팀이 정해야 하는 것. 지금은 비어 있다.
PENDING = {}


def _nouns(text):
    return {w for w in re.findall(r"[가-힣]{2,}", text or "")} - STOP


def _head(desc):
    """설명에서 뜻을 담은 앞부분만 남긴다 ('…를 나타내는 코드값이다' 같은 꼬리를 떼낸다)."""
    d = re.sub(r"\s*(이다|입니다)\.?\s*$", "", (desc or "").strip())
    d = re.sub(r"(을|를)?\s*나타내는\s*코드값$|코드값$|명칭$|여부$", "", d).strip()
    return d


def classify(legacy_rows, v1_field_names, v1_desc, v2_labels):
    """미승격 행을 다섯 묶음으로 나눈다.

    legacy_rows   : [(목적지, 'V1TABLE.field'), …]
    v1_field_names: {v1 테이블: {필드명, …}}  — 코드·명칭 쌍을 찾는 데 쓴다
    v1_desc       : {'V1TABLE.field': 설명}
    v2_labels     : v2 가 이미 가진 한글 이름 모음(서식 필드 kor + 파생 변수 kor + 값 라벨)
    """
    pool = [(lab, _nouns(lab)) for lab in v2_labels if lab]
    out = {b: [] for b in BUCKETS}
    for dest, key in legacy_rows:
        table, _, name = key.partition(".")
        desc = v1_desc.get(key, "")
        row = dict(dest=dest, v1=key, desc=desc[:120], match="")
        # 팀이 정해야 하는 것은 키 모양이어도 먼저 걸러 낸다 (file_id 는 외래키지만 '파일 표가 있는가'라는 결정이 남았다)
        why = PENDING.get(key) or PENDING.get(name)
        if why:
            row["match"] = why; out["대응 없음"].append(row); continue
        why = DROPPED.get(key) or DROPPED.get(name)
        if why:
            row["match"] = why; out["제외(사유 기록)"].append(row); continue
        if name.endswith("_id") and ("외래키" in desc or "식별자" in desc):
            out["키·외래키"].append(row); continue
        if any(name.endswith(s) and (name[: -len(s)] + c) in v1_field_names.get(table, ()) for s, c in PAIR_SUFFIX):
            out["코드·명칭 쌍의 명칭쪽"].append(row); continue
        # 사람이 대조해 적어 둔 결과가 어림보다 앞선다
        hit = RESOLVED.get(key) or RESOLVED.get(name)
        if hit:
            row["match"] = hit; out["대응 확인(검토 완료)"].append(row); continue
        why = DROPPED.get(key) or DROPPED.get(name)
        if why:
            row["match"] = why; out["제외(사유 기록)"].append(row); continue
        want = _nouns(_head(desc))
        best = max(((len(want & pn), lab) for lab, pn in pool), default=(0, ""))
        if best[0] >= 2:
            row["match"] = best[1]; out["v2 에 이미 대응 있음"].append(row)
        elif best[0] == 1:
            row["match"] = best[1]; out["부분 일치"].append(row)
        else:
            out["대응 없음"].append(row)
    return out
