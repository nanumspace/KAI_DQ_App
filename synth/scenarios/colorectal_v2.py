# -*- coding: utf-8 -*-
"""대장암 코호트 시나리오 (v2 저장 구조).

여정
  1) 진단: 대장내시경 + 조직검사(생검 병리), CEA, 복부·흉부 CT, 직장암이면 골반 MRI(COLORECTAL_EXAM)
  2) 직장암 III 기 전후: 선행 항암방사선 → 재평가 MRI(mrTRG)
  3) 수술: 절제 + 수술 병리(침윤 깊이·림프절·종양출아·TME 완전도) + 수술 상세(문합·장루·전환)
  4) 보조 항암요법(FOLFOX 등) → EPISODE + 약물
  5) 추적: CEA·CT, 일부 재발·사망

우측·좌측·직장은 서로 다른 길을 간다. 직장암만 MRI 와 TME·CRM 을 받는다.
"""
import datetime as dt

from framework_v2 import D, FEMALE, INPATIENT, MALE, OUTPATIENT, CtxV2

CRC, RECTAL = 443381, 4247719
COLONOSCOPY, ABD_CT, CHEST_CT, PELVIC_MRI = 4249893, 4021967, 4059400, 4013636
COLECTOMY, LAR = 4176797, 4056894
CEA, HB, ALB, CREA, WBC, PLT = 4197971, 3000963, 3024561, 3016723, 3010813, 3024929
COLON_SPEC = 4002054
FOLFOX = [1397141, 955632, 1344905]        # oxaliplatin·5-FU·leucovorin 자리
CAPOX = [1397141, 1337620]

SITE = [("CECUM", "맹장", "RIGHT"), ("ASC_COLON", "상행결장", "RIGHT"), ("TRANS_COLON", "횡행결장", "RIGHT"),
        ("DESC_COLON", "하행결장", "LEFT"), ("SIGMOID", "S상결장", "LEFT"), ("RECTUM", "직장", "RECTUM")]
DEPTH = {"I": "T1", "II": "T3", "III": "T3", "IV": "T4A"}
PATH_REPORT = ("Colon/Rectum, {site}, {method}: Adenocarcinoma. Invasion depth {depth}. "
               "Lymph nodes {pos}/{tot} positive. Tumor budding {bd}. TME {tme}.")


def generate(ctx: CtxV2, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.42) else MALE
        age = int(ctx.normal(64, 11, 30, 90, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 4))
        p = ctx.person(gender, age, index)
        site_cd, site_nm, side = ctx.choice(SITE)
        rectum = side == "RECTUM"
        stage = ctx.choice(["I", "II", "III", "IV"], p=[0.2, 0.27, 0.35, 0.18])
        depth = DEPTH[stage]
        # 사망일은 여정을 그리기 전에 정한다. 끝에 정하면 앞서 만든 사건을 자를 수 없다.
        if stage == "IV" and ctx.bern(0.4):
            d = ctx.days(index, ctx.randint(400, 1400))
            if d <= ctx.today:
                ctx.set_death(p, d)

        # ---- 1) 진단
        vid = ctx.visit(p, index, OUTPATIENT)
        dx = ctx.condition(p, index, RECTAL if rectum else CRC, vid=vid,
                           source="C20" if rectum else "C18.9")
        ep = ctx.episode(p, index, None, ctx.seeds["episode_disease"], CRC)
        ctx.episode_event(ep, dx, ctx.seeds["field_condition"])
        ctx.procedure(p, index, COLONOSCOPY, vid=vid, source="COLONOSCOPY")
        ctx.procedure(p, index, ABD_CT, vid=vid, source="ABD-CT")
        ctx.procedure(p, index, CHEST_CT, vid=vid, source="CHEST-CT")
        for concept, val in ((CEA, ctx.normal(9 if stage in ("III", "IV") else 3.2, 6, 0.4, 120, 1)),
                             (HB, ctx.normal(11.8 if side == "RIGHT" else 13.2, 1.8, 6.5, 17.0)),
                             (ALB, ctx.normal(4.0, 0.4, 2.2, 5.2, 1)), (CREA, ctx.normal(0.9, 0.25, 0.4, 3.0, 2)),
                             (WBC, ctx.normal(7.0, 2.0, 2.0, 18.0, 1)), (PLT, ctx.normal(265, 70, 60, 550, 0))):
            ctx.measure(p, index, concept, val, vid=vid)

        bx_day = ctx.days(index, 1)
        bx_spec = ctx.specimen(p, bx_day, COLON_SPEC, vid=vid, source=f"COLON-{site_cd}")
        diff = ctx.choice(["well", "moderately", "poorly"], p=[0.2, 0.6, 0.2])
        ctx.ext("PATHOLOGY_REPORT", p, vid=vid, specimen_id=bx_spec, specimen_date=bx_day,
                report_type_concept_id=ctx.cs("CL_PATHOLOGY_REPORT_TYPE", "BIOPSY"), report_type_source_value="BIOPSY",
                biopsy_method_concept_id=ctx.cs("CL_BIOPSY_METHOD", "ENDOSCOPIC"),
                biopsy_site_concept_id=ctx.cs("CL_BIOPSY_SITE", "PRIMARY"),
                biopsy_adequacy_concept_id=ctx.cs("CL_BIOPSY_ADEQUACY", "ADEQUATE"),
                biopsy_site_detail_concept_id=ctx.cs("CL_BIOPSY_SITE_DETAIL", site_cd),
                biopsy_site_detail_source_value=site_nm,
                biopsy_differentiation_concept_id=ctx.cs("CL_BIOPSY_DIFFERENTIATION",
                                                         {"well": "WD", "moderately": "MD", "poorly": "PD"}[diff]),
                biopsy_histologic_diagnosis_source_value="Adenocarcinoma, NOS",
                primary_histology_source_value="8140/3",
                # 침윤 여부는 코어 생검에서도 본다(spec/v2_row_kinds.py 가 BOTH 로 둔 항목)
                lymphatic_invasion_yn=1 if ctx.bern(0.15) else 0,
                vascular_invasion_yn=1 if ctx.bern(0.1) else 0,
                perineural_invasion_yn=1 if ctx.bern(0.12) else 0)

        # ---- 2) 직장암이면 골반 MRI
        if rectum and not (p.death_date and ctx.days(index, 10) > p.death_date):
            mri_day = ctx.days(index, ctx.randint(3, 10))
            mv = ctx.visit_on(p, mri_day)
            ctx.procedure(p, mri_day, PELVIC_MRI, vid=mv, source="PELVIC-MRI")
            _mri_row(ctx, p, mv, mri_day, stage, first=True)

        # ---- 3) 선행 항암방사선(직장암 II~III)
        surgery_day = ctx.days(index, ctx.randint(21, 45))
        if rectum and stage in ("II", "III") and ctx.bern(0.6) and not (p.death_date and surgery_day > p.death_date):
            crt_start = ctx.days(index, ctx.randint(14, 28))
            # 마지막 주 투여가 5일치이므로 에피소드는 그 종료일(+39)까지 덮어야 한다
            crt_ep = ctx.episode(p, crt_start, ctx.days(crt_start, 39), ctx.seeds["episode_regimen"], CRC,
                                 number=0, parent=ep)
            for w in range(6):
                d = ctx.days(crt_start, 7 * w)
                cv = ctx.visit_on(p, d)
                did = ctx.drug(p, d, 1337620, days=5, vid=cv, source="capecitabine + RT")
                ctx.episode_event(crt_ep, did, ctx.seeds["field_drug"])
            re_day = ctx.days(crt_start, ctx.randint(45, 70))
            rv = ctx.visit_on(p, re_day)
            ctx.procedure(p, re_day, PELVIC_MRI, vid=rv, source="PELVIC-MRI")
            _mri_row(ctx, p, rv, re_day, stage, first=False)
            surgery_day = ctx.days(re_day, ctx.randint(14, 35))

        # ---- 4) 수술과 수술 병리
        if (stage != "IV" or ctx.bern(0.4)) and not (p.death_date and surgery_day > p.death_date):
            sv = ctx.visit(p, surgery_day, INPATIENT, los=ctx.randint(7, 14))
            proc = ctx.procedure(p, surgery_day, LAR if rectum else COLECTOMY, vid=sv,
                                 source="저위전방절제술" if rectum else "결장절제술")
            ctx.episode_event(ep, proc, ctx.seeds["field_procedure"])
            op_spec = ctx.specimen(p, surgery_day, COLON_SPEC, vid=sv, source=f"RESECTION-{site_cd}")
            tot_ln = ctx.randint(12, 40)
            pos_ln = 0 if stage in ("I", "II") else ctx.randint(1, min(9, tot_ln))
            bd = ctx.choice(["BD1", "BD2", "BD3"], p=[0.5, 0.3, 0.2])
            tme = ctx.choice(["COMPLETE", "NEARLY_COMPLETE", "INCOMPLETE"], p=[0.7, 0.22, 0.08])
            path_day = ctx.days(surgery_day, ctx.randint(3, 7))
            ctx.ext("PATHOLOGY_REPORT", p, vid=sv, specimen_id=op_spec, specimen_date=surgery_day,
                    report_type_concept_id=ctx.cs("CL_PATHOLOGY_REPORT_TYPE", "SURGICAL"),
                    report_type_source_value="SURGICAL",
                    surgical_specimen_site_concept_id=ctx.cs("CL_SURGICAL_SPECIMEN_SITE", "PRIMARY"),
                    surgical_specimen_site_source_value=site_nm,
                    surgical_histologic_diagnosis_source_value="Adenocarcinoma, NOS",
                    primary_histology_source_value="8140/3",
                    surgical_histologic_grade_concept_id=ctx.cs("CL_SURGICAL_HISTOLOGIC_GRADE",
                                                                {"well": "G1", "moderately": "G2", "poorly": "G3"}[diff]),
                    lymph_nodes_examined=tot_ln, lymph_nodes_positive=pos_ln,
                    invasion_depth_concept_id=ctx.cs("CL_INVASION_DEPTH", depth),
                    invasion_depth_source_value=depth,
                    gross_type_concept_id=ctx.cs("CL_GROSS_TYPE", ctx.choice(["TYPE1", "TYPE2", "TYPE3", "TYPE4"],
                                                                             p=[0.1, 0.5, 0.3, 0.1])),
                    tumor_budding_grade_concept_id=ctx.cs("CL_TUMOR_BUDDING_GRADE", bd),
                    tumor_deposits_yn=1 if (pos_ln and ctx.bern(0.2)) else 0,
                    resection_completeness_concept_id=ctx.cs("CL_RESECTION_COMPLETENESS",
                                                             "CURATIVE" if stage != "IV" else "NONCURATIVE"),
                    resection_margin_status_concept_id=ctx.cs("CL_RESECTION_MARGIN_STATUS",
                                                              "R0" if stage != "IV" else ctx.choice(["R0", "R1"])),
                    residual_tumor_r_class_concept_id=ctx.cs("CL_RESIDUAL_TUMOR_R_CLASS",
                                                             "R0" if stage != "IV" else "R2"),
                    lymphatic_invasion_yn=1 if ctx.bern(0.3) else 0,
                    vascular_invasion_yn=1 if ctx.bern(0.2) else 0,
                    perineural_invasion_yn=1 if ctx.bern(0.25) else 0,
                    tme_quality_concept_id=ctx.cs("CL_TME_QUALITY", tme),
                    surgical_tumor_site_concept_id=ctx.cs("TUMOR_SITE", "PRIMARY"),
                    surgical_tumor_site_source_value=site_nm)
            ctx.note(p, path_day, PATH_REPORT.format(site=site_nm, method="resection", depth=depth,
                                                      pos=pos_ln, tot=tot_ln, bd=bd, tme=tme),
                     note_type=44814640, note_class=36716165, vid=sv)
            stoma = rectum and ctx.bern(0.45)
            converted = ctx.bern(0.08)      # 전환 여부와 사유는 한 번에 정해야 앞뒤가 맞는다
            ctx.ext("COLORECTAL_SURGERY_DETAIL", p, vid=sv, procedure_occurrence_id=proc,
                    preop_obstruction_treatment_yn=1 if ctx.bern(0.1) else 0,
                    stoma_yn=1 if stoma else 0,
                    stoma_reason_concept_id=ctx.cs("CL_STOMA_REASON", "DIVERTING" if stoma else "OTHER"),
                    stoma_reason_source_value="보호 장루" if stoma else "해당없음",
                    anastomosis_method_concept_id=ctx.cs("CL_ANASTOMOSIS_METHOD",
                                                         ctx.choice(["STAPLED", "HAND_SEWN"], p=[0.8, 0.2])),
                    anastomosis_height_cm=round(ctx.rand(2.0, 12.0), 1) if rectum else None,
                    splenic_flexure_mobilization_yn=1 if ctx.bern(0.3) else 0,
                    hipec_yn=1 if (stage == "IV" and ctx.bern(0.1)) else 0,
                    conversion_to_open_yn=1 if converted else 0,
                    conversion_reason="유착" if converted else "해당없음")

        # ---- 5) 보조 항암요법
        if stage in ("III", "IV"):
            start = ctx.days(surgery_day, ctx.randint(21, 45))
            cycles = 8 if stage == "III" else 12
            regimen, drugs = ("FOLFOX", FOLFOX) if ctx.bern(0.6) else ("CAPOX", CAPOX)
            tx = ctx.episode(p, start, ctx.days(start, 14 * (cycles - 1) + 13), ctx.seeds["episode_regimen"],
                             CRC, number=1, parent=ep)
            for c in range(cycles):
                d = ctx.days(start, 14 * c)
                if d > ctx.today or (p.death_date and d > p.death_date):
                    break
                cv = ctx.visit_on(p, d)
                for drug in drugs:
                    did = ctx.drug(p, d, drug, days=2, vid=cv, source=regimen)
                    ctx.episode_event(tx, did, ctx.seeds["field_drug"])
                ctx.measure(p, d, WBC, ctx.normal(4.5, 1.6, 1.0, 14.0, 1), vid=cv)
                if ctx.bern(0.2):
                    ae = ctx.condition(p, d, ctx.choice([378253, 4160887]), vid=cv,
                                       source=f"CTCAE grade {ctx.randint(1, 3)}")
                    ctx.episode_event(tx, ae, ctx.seeds["field_condition"])

        # ---- 6) 추적
        for k in range(1, 9):
            day = ctx.days(index, 120 * k)
            if day > ctx.today or (p.death_date and day > p.death_date):
                break
            fv = ctx.visit(p, day, OUTPATIENT)
            ctx.measure(p, day, CEA, ctx.normal(3.0, 2.2, 0.3, 60, 1), vid=fv)
            if k % 3 == 0:
                ctx.procedure(p, day, ABD_CT, vid=fv, source="ABD-CT")
        ctx.finalize_person(p)


def _mri_row(ctx, p, vid, day, stage, first):
    """직장 MRI 한 행. 재평가일 때만 mrTRG 를 적는다(치료 전에는 잴 것이 없다)."""
    ctx.ext("COLORECTAL_EXAM", p, vid=vid, exam_date=day,
            rectal_tumor_height_cm=round(ctx.rand(2.0, 14.0), 1),
            # 항문연이 항문직장경계부보다 바깥이므로 거리도 더 멀다. 따로 뽑으면 앞뒤가 어긋난다.
            mri_distance_anal_verge_cm=(verge := round(ctx.rand(3.0, 15.0), 1)),
            mri_distance_anorectal_junction_cm=round(max(0.5, verge - ctx.rand(1.0, 3.0)), 1),
            mri_t4b_invaded_organ_concept_id=ctx.cs("CL_MRI_T4B_INVADED_ORGAN",
                                                    ctx.choice(["PROSTATE", "VAGINA", "BLADDER", "OTHER"])
                                                    if stage == "IV" else "OTHER"),
            mri_anterior_peritoneal_relation_concept_id=ctx.cs("CL_MRI_ANTERIOR_PERITONEAL_RELATION",
                                                               ctx.choice(["ABOVE", "AT", "BELOW"])),
            mri_mesorectal_node_yn=1 if stage in ("III", "IV") else 0,
            mri_extramesorectal_node_yn=1 if (stage == "IV" and ctx.bern(0.3)) else 0,
            mri_tumor_regression_grade_concept_id=ctx.cs("CL_MRI_TUMOR_REGRESSION_GRADE",
                                                         ctx.choice(["MRTRG1", "MRTRG2", "MRTRG3", "MRTRG4", "MRTRG5"],
                                                                    p=[0.1, 0.25, 0.35, 0.2, 0.1]))
            if not first else None)
