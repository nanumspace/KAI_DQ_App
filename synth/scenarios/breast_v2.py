# -*- coding: utf-8 -*-
"""유방암 코호트 시나리오 (v2 저장 구조).

여정
  1) 진단: 유방촬영·초음파(BREAST_EXAM) → 총생검(병리: ER/PR/HER2·Ki-67), 생식·산과력(BREAST_BASELINE)
  2) 수술(유방보존 또는 전절제) + 감시림프절 → 수술 병리
  3) 보조 요법: 항암(AC-T 등)·항HER2·내분비요법 → EPISODE + 약물
  4) 추적: 유방촬영, 일부 재발·사망

BREAST_BASELINE 은 생식·산과력을 받는 자리라 EHR 에서 그대로 나오지 않는다. v2 가 서식으로
새로 받는 항목이 가장 많은 표이고, 폐경 여부·출산력처럼 서로 얽힌 값들이 앞뒤가 맞아야 한다.
"""
import datetime as dt

from framework_v2 import D, FEMALE, INPATIENT, MALE, OUTPATIENT, CtxV2

BC = 4112853
MAMMO, US, BREAST_MRI = 4324124, 4047494, 4013636
CORE_BX, LUMPECTOMY, MASTECTOMY, SLNB = 4047494, 4030450, 4001938, 4213297
HB, WBC, PLT, ALB, CREA, CA153 = 3000963, 3010813, 3024929, 3024561, 3016723, 3021044
BREAST_SPEC = 4001320
AC_T = [1338512, 1315286, 1378382]          # doxorubicin·cyclophosphamide·paclitaxel 자리
TRASTUZUMAB, TAMOXIFEN, LETROZOLE = 1314924, 1436678, 1398937
SIDE = ["RIGHT", "LEFT"]


def generate(ctx: CtxV2, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.99) else MALE
        age = int(ctx.normal(53, 11, 25, 88, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 4))
        p = ctx.person(gender, age, index)
        side = ctx.choice(SIDE)
        stage = ctx.choice(["I", "II", "III", "IV"], p=[0.3, 0.38, 0.22, 0.1])
        er = ctx.bern(0.72)
        her2 = ctx.bern(0.18)
        if stage == "IV" and ctx.bern(0.3):
            d = ctx.days(index, ctx.randint(400, 1500))
            if d <= ctx.today:
                ctx.set_death(p, d)

        # ---- 1) 진단
        vid = ctx.visit(p, index, OUTPATIENT)
        dx = ctx.condition(p, index, BC, vid=vid, source="C50.9")
        ep = ctx.episode(p, index, None, ctx.seeds["episode_disease"], BC)
        ctx.episode_event(ep, dx, ctx.seeds["field_condition"])
        ctx.procedure(p, index, MAMMO, vid=vid, source="MAMMOGRAPHY")
        ctx.procedure(p, index, US, vid=vid, source="BREAST-US")
        ctx.ext("BREAST_EXAM", p, vid=vid, exam_date=index,
                imaging_diagnostic_classification_concept_id=ctx.cs("CL_IMAGING_DIAGNOSTIC_CLASSIFICATION",
                                                                    ctx.choice(["4A", "4B", "4C", "5"],
                                                                               p=[0.15, 0.25, 0.3, 0.3])),
                mammographic_density_concept_id=ctx.cs("BIRADS_DENSITY", ctx.choice(["A", "B", "C", "D"],
                                                                                    p=[0.1, 0.3, 0.4, 0.2])))
        for concept, val in ((HB, ctx.normal(12.5, 1.5, 7.0, 16.5)), (WBC, ctx.normal(6.5, 2.0, 2.0, 15.0, 1)),
                             (PLT, ctx.normal(250, 65, 60, 500, 0)), (ALB, ctx.normal(4.2, 0.4, 2.5, 5.2, 1)),
                             (CREA, ctx.normal(0.8, 0.2, 0.4, 2.5, 2)), (CA153, ctx.normal(18, 12, 2, 200, 1))):
            ctx.measure(p, index, concept, val, vid=vid)
        _baseline_row(ctx, p, vid, index, age)

        # ---- 생검과 병리
        bx_day = ctx.days(index, ctx.randint(1, 10))
        bv = ctx.visit_on(p, bx_day)
        ctx.procedure(p, bx_day, CORE_BX, vid=bv, source="CORE-BX")
        spec = ctx.specimen(p, bx_day, BREAST_SPEC, vid=bv, source=f"BREAST-{side}")
        diff = ctx.choice(["well", "moderately", "poorly"], p=[0.2, 0.5, 0.3])
        ctx.ext("PATHOLOGY_REPORT", p, vid=bv, specimen_id=spec, specimen_date=bx_day,
                report_type_concept_id=ctx.cs("CL_PATHOLOGY_REPORT_TYPE", "BIOPSY"), report_type_source_value="BIOPSY",
                biopsy_method_concept_id=ctx.cs("CL_BIOPSY_METHOD", "CORE"),
                biopsy_site_concept_id=ctx.cs("CL_BIOPSY_SITE", "PRIMARY"),
                biopsy_adequacy_concept_id=ctx.cs("CL_BIOPSY_ADEQUACY", "ADEQUATE"),
                biopsy_laterality_concept_id=ctx.cs("CL_BIOPSY_LATERALITY", side),
                biopsy_differentiation_concept_id=ctx.cs("CL_BIOPSY_DIFFERENTIATION",
                                                         {"well": "WD", "moderately": "MD", "poorly": "PD"}[diff]),
                biopsy_histologic_diagnosis_source_value="Invasive ductal carcinoma",
                primary_histology_source_value="8500/3",
                lymphatic_invasion_yn=0, vascular_invasion_yn=0, perineural_invasion_yn=0,
                lymphovascular_invasion_yn=1 if ctx.bern(0.2) else 0,
                in_situ_component_yn=1 if ctx.bern(0.4) else 0,
                dcis_nuclear_grade_concept_id=ctx.cs("CL_DCIS_NUCLEAR_GRADE",
                                                     ctx.choice(["LOW", "INTERMEDIATE", "HIGH"], p=[0.2, 0.5, 0.3])),
                til_percent=ctx.randint(1, 60),
                microcalcification_yn=1 if ctx.bern(0.3) else 0,
                mammographic_microcalcification_yn=1 if ctx.bern(0.35) else 0,
                inflammatory_breast_cancer_yn=1 if ctx.bern(0.03) else 0)
        _biomarker_row(ctx, p, bv, bx_day, spec, er, her2)

        # ---- 2) 수술
        surgery_day = ctx.days(index, ctx.randint(21, 50))
        if not (p.death_date and surgery_day > p.death_date) and (stage != "IV" or ctx.bern(0.5)):
            sv = ctx.visit(p, surgery_day, INPATIENT, los=ctx.randint(3, 8))
            breast_conserving = ctx.bern(0.55)
            proc = ctx.procedure(p, surgery_day, LUMPECTOMY if breast_conserving else MASTECTOMY, vid=sv,
                                 source="유방보존술" if breast_conserving else "유방전절제술")
            ctx.episode_event(ep, proc, ctx.seeds["field_procedure"])
            ctx.procedure(p, surgery_day, SLNB, vid=sv, source="SLNB")
            op_spec = ctx.specimen(p, surgery_day, BREAST_SPEC, vid=sv, source=f"RESECTION-{side}")
            sn_tot = ctx.randint(1, 6)
            sn_pos = 0 if stage == "I" else ctx.randint(0, sn_tot)
            tot_ln = sn_tot + (ctx.randint(5, 25) if sn_pos else 0)
            pos_ln = sn_pos + (ctx.randint(0, 6) if sn_pos else 0)
            ctx.ext("PATHOLOGY_REPORT", p, vid=sv, specimen_id=op_spec, specimen_date=surgery_day,
                    report_type_concept_id=ctx.cs("CL_PATHOLOGY_REPORT_TYPE", "SURGICAL"),
                    report_type_source_value="SURGICAL",
                    surgical_specimen_site_concept_id=ctx.cs("CL_SURGICAL_SPECIMEN_SITE", "PRIMARY"),
                    surgical_specimen_laterality_concept_id=ctx.cs("CL_SURGICAL_SPECIMEN_LATERALITY", side),
                    surgical_histologic_diagnosis_source_value="Invasive ductal carcinoma",
                    primary_histology_source_value="8500/3",
                    surgical_histologic_grade_concept_id=ctx.cs("CL_SURGICAL_HISTOLOGIC_GRADE",
                                                                {"well": "G1", "moderately": "G2", "poorly": "G3"}[diff]),
                    sentinel_nodes_examined=sn_tot, sentinel_nodes_positive=sn_pos,
                    lymph_nodes_examined=tot_ln, lymph_nodes_positive=pos_ln,
                    resection_margin_status_concept_id=ctx.cs("CL_RESECTION_MARGIN_STATUS",
                                                              ctx.choice(["R0", "R1"], p=[0.92, 0.08])),
                    residual_tumor_r_class_concept_id=ctx.cs("CL_RESIDUAL_TUMOR_R_CLASS", "R0"),
                    lymphatic_invasion_yn=1 if ctx.bern(0.25) else 0,
                    vascular_invasion_yn=1 if ctx.bern(0.15) else 0,
                    perineural_invasion_yn=1 if ctx.bern(0.1) else 0,
                    lymphovascular_invasion_yn=1 if ctx.bern(0.25) else 0,
                    in_situ_component_yn=1 if ctx.bern(0.45) else 0,
                    dcis_nuclear_grade_concept_id=ctx.cs("CL_DCIS_NUCLEAR_GRADE", "INTERMEDIATE"),
                    til_percent=ctx.randint(1, 60),
                    microcalcification_yn=1 if ctx.bern(0.3) else 0,
                    mammographic_microcalcification_yn=1 if ctx.bern(0.3) else 0,
                    inflammatory_breast_cancer_yn=0)

        # ---- 3) 보조 요법
        tx_start = ctx.days(surgery_day, ctx.randint(21, 45))
        if stage in ("II", "III", "IV") and not (p.death_date and tx_start > p.death_date):
            cycles = 8
            tx = ctx.episode(p, tx_start, ctx.days(tx_start, 21 * (cycles - 1) + 20),
                             ctx.seeds["episode_regimen"], BC, number=1, parent=ep)
            for c in range(cycles):
                day = ctx.days(tx_start, 21 * c)
                if day > ctx.today or (p.death_date and day > p.death_date):
                    break
                cv = ctx.visit_on(p, day)
                for drug in AC_T:
                    did = ctx.drug(p, day, drug, days=1, vid=cv, source="AC-T")
                    ctx.episode_event(tx, did, ctx.seeds["field_drug"])
                if her2:
                    did = ctx.drug(p, day, TRASTUZUMAB, days=1, vid=cv, source="trastuzumab")
                    ctx.episode_event(tx, did, ctx.seeds["field_drug"])
                ctx.measure(p, day, WBC, ctx.normal(3.4, 1.7, 0.3, 13.0, 1), vid=cv)
                if ctx.bern(0.2):
                    ae = ctx.condition(p, day, ctx.choice([4160887, 378253, 440674]), vid=cv,
                                       source=f"CTCAE grade {ctx.randint(1, 3)}")
                    ctx.episode_event(tx, ae, ctx.seeds["field_condition"])
        if er:
            endo_start = ctx.days(surgery_day, ctx.randint(30, 90))
            for m in range(0, 60, 3):
                day = ctx.days(endo_start, 30 * m)
                if day > ctx.today or (p.death_date and day > p.death_date):
                    break
                ev = ctx.visit_on(p, day)
                ctx.drug(p, day, TAMOXIFEN if age < 50 else LETROZOLE, days=90, vid=ev, source="내분비요법")

        # ---- 4) 추적
        for k in range(1, 7):
            day = ctx.days(index, 180 * k)
            if day > ctx.today or (p.death_date and day > p.death_date):
                break
            fv = ctx.visit(p, day, OUTPATIENT)
            ctx.procedure(p, day, MAMMO, vid=fv, source="MAMMOGRAPHY")
            ctx.ext("BREAST_EXAM", p, vid=fv, exam_date=day,
                    imaging_diagnostic_classification_concept_id=ctx.cs("CL_IMAGING_DIAGNOSTIC_CLASSIFICATION", "2"),
                    mammographic_density_concept_id=ctx.cs("BIRADS_DENSITY", "C"))
            ctx.measure(p, day, CA153, ctx.normal(16, 9, 2, 150, 1), vid=fv)
        ctx.finalize_person(p)


def _baseline_row(ctx, p, vid, index, age):
    """생식·산과력. 값들이 서로 앞뒤가 맞아야 한다 — 출산한 적이 없으면 첫 출산 나이도 없다."""
    menopause = age >= ctx.randint(48, 54)
    parity = ctx.bern(0.8)
    children = ctx.randint(1, 4) if parity else 0
    first_birth = ctx.randint(22, min(40, age - 1)) if parity else 0
    fert = (not menopause) and ctx.bern(0.12)
    status = "POST" if menopause else ("PERI" if age >= 45 and ctx.bern(0.3) else "PRE")
    ctx.ext("BREAST_BASELINE", p, vid=vid, record_date=index,
            married_yn=1 if ctx.bern(0.75) else 0,
            menarche_age=ctx.randint(11, 16),
            fertility_preservation_yn=1 if fert else 0,
            fertility_preservation_type_concept_id=ctx.cs("CL_FERTILITY_PRESERVATION_TYPE",
                                                          ctx.choice(["OOCYTE", "EMBRYO", "GNRH_AGONIST"]))
            if fert else None,
            parity_yn=1 if parity else 0, first_birth_age=first_birth, number_of_children=children,
            breastfeeding_yn=1 if (parity and ctx.bern(0.7)) else 0,
            menopause_yn=1 if menopause else 0,
            menopause_age=ctx.randint(45, 55) if menopause else 0,
            hrt_yn=1 if (menopause and ctx.bern(0.15)) else 0,
            hrt_duration_months=round(ctx.rand(6, 60), 0) if (menopause and ctx.bern(0.15)) else 0.0,
            pregnant_at_diagnosis_yn=1 if (not menopause and ctx.bern(0.02)) else 0,
            menopausal_status_at_diagnosis_concept_id=ctx.cs("CL_MENOPAUSAL_STATUS_AT_DIAGNOSIS", status),
            menopausal_status_at_diagnosis_source_value=status,
            menses_resumed_1y_yn=1 if (not menopause and ctx.bern(0.4)) else 0)


def _biomarker_row(ctx, p, vid, day, spec, er, her2):
    """유방암 바이오마커 한 행. 표지자마다 컬럼이 따로 있으므로 한 행에 모두 적는다."""
    res = lambda v: ctx.cs("BIOMARKER_RESULT", "양성" if v else "음성")   # noqa: E731
    ctx.ext("BIOMARKER", p, vid=vid, specimen_id=spec, test_date=day,
            ihc_test_concept_id=res(True), ihc_test_source_value=f"ER {'+' if er else '-'} / HER2 {'+' if her2 else '-'}",
            molecular_pathology_test_concept_id=res(False),
            molecular_subtype_concept_id=res(er),
            reference_sequence="GRCh38", dna_variant_a="NM_007294.4:c.68_69del" if ctx.bern(0.05) else "-",
            prognostic_gene_assay_type_concept_id=res(True),
            prognostic_gene_assay_result_concept_id=res(er),
            germline_test_method_concept_id=res(True),
            germline_test_gene_source_value="BRCA1/2",
            germline_test_result="pathogenic variant" if ctx.bern(0.05) else "no pathogenic variant",
            pathogenic_variant_yn=1 if ctx.bern(0.05) else 0,
            oncotype_rs=ctx.randint(0, 60),
            mammaprint_result_concept_id=res(er),
            ki67_percent=ctx.randint(2, 80))
