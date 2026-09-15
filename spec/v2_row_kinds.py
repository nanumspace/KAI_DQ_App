# -*- coding: utf-8 -*-
"""사전 v2.2 · 한 표에 여러 종류의 행이 앉는 경우의 '행 종류' 표시.

PATHOLOGY_REPORT 는 생검 병리와 수술 병리를 **같은 표에 각각 한 행**으로 받는다
(서식의 행 단위가 '검체(보고서) 1' 이다). 그래서 생검 행에는 수술 컬럼이 비어 있고
수술 행에는 생검 컬럼이 비어 있는 것이 정상이다. 배치표가 '필수'라고 한 항목을
행마다 NULL 금지로 바꾸면 어느 쪽이든 반드시 어긴다.

그래서 표에 행 종류 컬럼을 두고, 필수를 그 종류에 걸린 조건부로 만든다.
  - build_spec_v2.py 가 이 표시를 읽어 종류 컬럼과 값 집합을 만들고,
    각 컬럼에 `applies_when` 을 붙인다.
  - generate_structural_rules.py 가 그것을 조건부 필수 규칙으로 바꾼다.

필수 여부가 행 종류가 아니라 **다른 컬럼의 값**에 걸리는 것도 있다. 폐선암 우세 아형은
수술 병리이면서 조직형이 선암일 때만 해당하고, 직장 MRI 의 mrTRG 는 선행치료 뒤 재평가일
때만 잰다. 그래서 EXTRA_CONDITIONS 에 '어느 컬럼이 비어 있지 않을 때만 필수' 를 더 걸 수 있다.
조건은 모두 만족해야 필수가 된다.

APPLIES 의 분류는 '그 소견을 어느 검체에서 판정하는가'로 나눈 것이며, 임상적으로
다시 볼 필요가 있다. 확실하지 않은 것은 BOTH 로 두었다(양쪽 모두에서 요구한다는 뜻이라
가장 엄격하다). 팀 검토에서 고칠 자리는 이 파일 하나다.
"""

BIOPSY, SURGICAL, BOTH = "BIOPSY", "SURGICAL", "BOTH"

ROW_KINDS = {
    "PATHOLOGY_REPORT": dict(
        column="report_type_concept_id",
        codelist="CL_PATHOLOGY_REPORT_TYPE",
        kor="병리 보고서 종류",
        values=[("BIOPSY", "생검 병리", "Biopsy pathology report"),
                ("SURGICAL", "수술 병리", "Surgical pathology report")],
        applies={
            # ---- 생검 검체에서 판정하는 것
            "biopsy_method_concept_id": BIOPSY,
            "biopsy_site_concept_id": BIOPSY,
            "biopsy_site_detail_concept_id": BIOPSY,
            "biopsy_histologic_diagnosis_concept_id": BIOPSY,
            "biopsy_differentiation_concept_id": BIOPSY,
            "biopsy_laterality_concept_id": BIOPSY,
            "biopsy_adequacy_concept_id": BIOPSY,
            # 간 병리 등급은 간 생검에서 매긴다(MASLD)
            "liver_fibrosis_grade_name_concept_id": BIOPSY,
            "steatosis_grade_concept_id": BIOPSY,
            "lobular_inflammation_grade_concept_id": BIOPSY,
            "ballooning_grade_concept_id": BIOPSY,
            "fibrosis_stage_concept_id": BIOPSY,
            "nas_score": BIOPSY,
            # ---- 절제 검체에서 판정하는 것
            "surgical_specimen_site_concept_id": SURGICAL,
            "surgical_specimen_laterality_concept_id": SURGICAL,
            "surgical_histologic_diagnosis_concept_id": SURGICAL,
            "surgical_histologic_grade_concept_id": SURGICAL,
            "surgical_tumor_site_concept_id": SURGICAL,
            "resection_margin_status_concept_id": SURGICAL,
            "residual_tumor_r_class_concept_id": SURGICAL,
            "resection_completeness_concept_id": SURGICAL,
            "tme_quality_concept_id": SURGICAL,
            "sentinel_nodes_examined": SURGICAL,
            "sentinel_nodes_positive": SURGICAL,
            "lymph_nodes_examined": SURGICAL,
            "lymph_nodes_positive": SURGICAL,
            "invasion_depth_concept_id": SURGICAL,
            "tumor_deposits_yn": SURGICAL,
            "tumor_budding_grade_concept_id": SURGICAL,
            "gross_type_concept_id": SURGICAL,
            # 폐: 종양 전체를 봐야 판정할 수 있는 것들
            "stas_yn": SURGICAL,
            "vpi_grade_concept_id": SURGICAL,
            "obstructive_pneumonia_atelectasis_yn": SURGICAL,
            "adenocarcinoma_predominant_subtype_concept_id": SURGICAL,
            # ---- 어느 보고서에나 적는 것
            "primary_histology_concept_id": BOTH,
            # ---- 임상 검토 필요: 코어 생검에서도 볼 수 있어 일단 BOTH(가장 엄격) 로 둔다
            "lymphovascular_invasion_yn": BOTH,
            "lymphatic_invasion_yn": BOTH,
            "vascular_invasion_yn": BOTH,
            "perineural_invasion_yn": BOTH,
            "in_situ_component_yn": BOTH,
            "dcis_nuclear_grade_concept_id": BOTH,
            "til_percent": BOTH,
            "microcalcification_yn": BOTH,
            "mammographic_microcalcification_yn": BOTH,
            "inflammatory_breast_cancer_yn": BOTH,
        },
    ),
}

# 행 종류 말고 다른 컬럼의 값에도 걸리는 것들.
#   key: (테이블, 컬럼) -> 함께 채워져 있어야 필수가 되는 컬럼
# 뜻: '그 컬럼이 채워진 행에서만 이 컬럼이 필수다'. 행 종류 조건이 있으면 그것과 함께 만족해야 한다.
# 조건은 세 가지로 적는다.
#   ("표", "컬럼"): "다른컬럼"                      그 컬럼이 **채워져 있을 때만** 필수
#   ("표", "컬럼"): ("다른컬럼", "들어갈 글자")        그 컬럼 값에 그 글자가 **들어 있을 때만** 필수
#   ("표", "컬럼"): ("다른컬럼", "=", "값")           그 컬럼이 그 값일 때만 필수 (예/아니오 칸에 쓴다)
EXTRA_CONDITIONS = {
    # 폐선암 우세 아형은 조직형이 선암일 때만 매긴다. 진단명은 조직형이 무엇이든 적히므로
    # '채워졌는가'로는 가릴 수 없고 값에 'Adenocarcinoma' 가 들어 있는지를 봐야 한다.
    ("PATHOLOGY_REPORT", "adenocarcinoma_predominant_subtype_concept_id"):
        ("surgical_histologic_diagnosis_source_value", "Adenocarcinoma"),
    # mrTRG(치료 반응 등급)는 선행치료를 한 뒤 재평가 MRI 에서만 잰다.
    # 재평가 MRI 에서는 침윤 깊이를 다시 재므로 그 값이 있는 행에서만 요구한다.
    ("COLORECTAL_EXAM", "mri_tumor_regression_grade_concept_id"): "mri_invasion_depth_mm",
    # 림프종: 일어나지 않은 사건의 날짜·종류를 요구할 수 없다.
    ("LYMPHOMA_EVENT", "transformation_date"): ("transformation_yn", "=", "1"),
    ("LYMPHOMA_EVENT", "transformation_from_subtype_concept_id"): ("transformation_yn", "=", "1"),
    ("LYMPHOMA_EVENT", "transformation_to_subtype_concept_id"): ("transformation_yn", "=", "1"),
    ("LYMPHOMA_EVENT", "sct_date"): ("sct_yn", "=", "1"),
    ("LYMPHOMA_EVENT", "sct_type_concept_id"): ("sct_yn", "=", "1"),
    ("LYMPHOMA_EVENT", "car_t_infusion_date"): ("car_t_yn", "=", "1"),
    ("LYMPHOMA_EVENT", "car_t_target_concept_id"): ("car_t_yn", "=", "1"),
    ("LYMPHOMA_EVENT", "apheresis_date"): ("car_t_yn", "=", "1"),
    ("LYMPHOMA_EVENT", "lymphodepletion_start_date"): ("car_t_yn", "=", "1"),
}

# 위 applies 에서 BOTH 로 둔 것 중 임상 검토가 필요하다고 표시한 것. 보고서에 그대로 싣는다.
NEEDS_REVIEW = {
    "PATHOLOGY_REPORT": ["lymphovascular_invasion_yn", "lymphatic_invasion_yn", "vascular_invasion_yn",
                         "perineural_invasion_yn", "in_situ_component_yn", "dcis_nuclear_grade_concept_id",
                         "til_percent", "microcalcification_yn", "mammographic_microcalcification_yn",
                         "inflammatory_breast_cancer_yn"],
}
