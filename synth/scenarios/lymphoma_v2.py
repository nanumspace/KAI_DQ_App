# -*- coding: utf-8 -*-
"""림프종 코호트 시나리오 (v2 저장 구조).

여정
  1) 진단: 림프절 절제생검 → 병리(조직형)와 면역표현형(BIOMARKER), PET-CT(LYMPHOMA_EXAM), 골수검사
  2) 병기·예후: B 증상과 예후지수(IPI 계열) → LYMPHOMA_ASSESSMENT
  3) 1차 항암(R-CHOP 등) → EPISODE + 약물, 중간·말기 PET 로 반응 평가(Deauville)
  4) 일부에서 형질전환·자가조혈모세포이식·CAR-T → LYMPHOMA_EVENT
  5) 추적과 일부 사망

LYMPHOMA_EVENT 는 '일어나지 않은 사건'의 날짜까지 필수로 적혀 있다. 그래서 이 코호트가
조건부 필수(_equals)를 실제로 쓰는 자리다 — 이식을 안 했으면 이식일이 없는 것이 정상이다.
"""
import datetime as dt

from framework_v2 import D, FEMALE, INPATIENT, MALE, OUTPATIENT, CtxV2

DLBCL, FL, HL = 4245079, 4180791, 4179356
LN_BIOPSY, PET, BM_BIOPSY = 4054746, 4305790, 4148124
LDH, HB, WBC, PLT, ALB, CREA, B2M = 3002385, 3000963, 3010813, 3024929, 3024561, 3016723, 3020630
LN_SPEC = 4001225
RCHOP = [1314924, 1338512, 1344905, 1354118]     # rituximab·doxorubicin·vincristine·prednisone 자리
ABVD = [1338512, 1315286, 1367268, 1315942]
SUBTYPE = [("DLBCL", "미만성 거대B세포림프종", DLBCL), ("FL", "여포림프종", FL), ("CHL", "고전적 호지킨림프종", HL)]
RISK = ["저위험", "저중간", "고중간", "고위험"]


def generate(ctx: CtxV2, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.45) else MALE
        sub_cd, sub_nm, concept = ctx.choice(SUBTYPE, p=[0.5, 0.28, 0.22])
        hodgkin = sub_cd == "CHL"
        age = int(ctx.normal(34 if hodgkin else 62, 12, 18, 88, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 4))
        p = ctx.person(gender, age, index)
        stage = ctx.choice(["I", "II", "III", "IV"], p=[0.15, 0.3, 0.3, 0.25])
        advanced = stage in ("III", "IV")
        ipi = min(5, (1 if age > 60 else 0) + (1 if advanced else 0) + ctx.randint(0, 2))
        # 사망은 여정을 그리기 전에 정한다
        if advanced and ctx.bern(0.22):
            d = ctx.days(index, ctx.randint(300, 1500))
            if d <= ctx.today:
                ctx.set_death(p, d)

        # ---- 1) 진단
        vid = ctx.visit(p, index, OUTPATIENT)
        dx = ctx.condition(p, index, concept, vid=vid, source="C83.3" if sub_cd == "DLBCL" else ("C82.9" if sub_cd == "FL" else "C81.9"))
        ep = ctx.episode(p, index, None, ctx.seeds["episode_disease"], concept)
        ctx.episode_event(ep, dx, ctx.seeds["field_condition"])
        bx_day = ctx.days(index, ctx.randint(1, 7))
        bv = ctx.visit_on(p, bx_day)
        ctx.procedure(p, bx_day, LN_BIOPSY, vid=bv, source="LN-EXCISION")
        spec = ctx.specimen(p, bx_day, LN_SPEC, vid=bv, source="LYMPH-NODE")
        ctx.ext("PATHOLOGY_REPORT", p, vid=bv, specimen_id=spec, specimen_date=bx_day,
                report_type_concept_id=ctx.cs("CL_PATHOLOGY_REPORT_TYPE", "BIOPSY"), report_type_source_value="BIOPSY",
                biopsy_method_concept_id=ctx.cs("CL_BIOPSY_METHOD", "EXCISION"),
                biopsy_site_concept_id=ctx.cs("CL_BIOPSY_SITE", "REGIONAL_NODE"),
                biopsy_adequacy_concept_id=ctx.cs("CL_BIOPSY_ADEQUACY", "ADEQUATE"),
                biopsy_histologic_diagnosis_source_value=sub_nm,
                primary_histology_source_value=sub_nm,
                lymphatic_invasion_yn=0, vascular_invasion_yn=0, perineural_invasion_yn=0)
        # 면역표현형과 분자검사. 표지자마다 컬럼이 따로 있으므로 **한 행에 모두** 적는다.
        # (표지자 하나당 한 행으로 적으면 나머지 컬럼이 전부 빈 채로 남아 필수 검사에 걸린다.)
        b_cell = not hodgkin
        markers = {
            "cd3_result": not b_cell and not hodgkin, "cd5_result": sub_cd == "MCL",
            "cd10_result": sub_cd == "FL", "cd19_result": b_cell, "cd20_result": b_cell,
            "cd22_result": b_cell, "cd23_result": False, "cd30_result": hodgkin,
            "cd79a_result": b_cell, "pax5_result": b_cell or hodgkin,
            "bcl2_protein_result": sub_cd == "FL", "bcl6_protein_result": sub_cd in ("FL", "DLBCL"),
            "mum1_result": sub_cd == "DLBCL", "myc_protein_result": sub_cd == "DLBCL" and ctx.bern(0.3),
            "cyclin_d1_result": False, "sox11_result": False, "alk_result": False,
            "ebv_eber_result": hodgkin and ctx.bern(0.4),
            "myc_rearrangement_result": sub_cd == "DLBCL" and ctx.bern(0.1),
            "bcl2_rearrangement_result": sub_cd == "FL" and ctx.bern(0.8),
            "bcl6_rearrangement_result": ctx.bern(0.1),
            "t14_18_result": sub_cd == "FL" and ctx.bern(0.8), "t11_14_result": False,
            "tp53_abnormality_result": ctx.bern(0.12), "ig_tcr_clonality_result": b_cell,
            "mrd_result": False,
        }
        row = {f"{k}_concept_id": ctx.cs("BIOMARKER_RESULT", "양성" if v else "음성") for k, v in markers.items()}
        row["dlbcl_cell_of_origin_concept_id"] = ctx.cs("BIOMARKER_RESULT", "불명확" if sub_cd != "DLBCL" else "양성")
        row["double_hit_status_concept_id"] = ctx.cs("BIOMARKER_RESULT", "음성")
        ctx.ext("BIOMARKER", p, vid=bv, specimen_id=spec, test_date=bx_day,
                ki67_percent=ctx.randint(10, 95), molecular_test_date=bx_day,
                molecular_test_method_concept_id=ctx.cs("BIOMARKER_METHOD", ctx.choice(["NGS", "FISH", "PCR"])),
                double_expressor_yn=0, complex_karyotype_yn=1 if ctx.bern(0.1) else 0,
                flow_cytometry_summary_source_value="B-cell phenotype" if b_cell else "T-cell phenotype",
                **row)
        ctx.procedure(p, bx_day, BM_BIOPSY, vid=bv, source="BM-BIOPSY")
        for concept_id, val in ((LDH, ctx.normal(320 if advanced else 210, 120, 90, 1200, 0)),
                                (HB, ctx.normal(11.5 if advanced else 13.2, 1.8, 6.0, 17.0)),
                                (WBC, ctx.normal(7.5, 3.0, 1.0, 30.0, 1)), (PLT, ctx.normal(240, 80, 30, 600, 0)),
                                (ALB, ctx.normal(3.9, 0.5, 2.0, 5.2, 1)), (CREA, ctx.normal(0.9, 0.25, 0.4, 3.0, 2)),
                                (B2M, ctx.normal(3.0, 1.4, 0.8, 12.0, 1))):
            ctx.measure(p, index, concept_id, val, vid=vid)

        # PET-CT
        pet_day = ctx.days(index, ctx.randint(3, 12))
        pv = ctx.visit_on(p, pet_day)
        ctx.procedure(p, pet_day, PET, vid=pv, source="PET-CT")
        ctx.ext("LYMPHOMA_EXAM", p, vid=pv, exam_date=pet_day,
                pet_suvmax=round(ctx.normal(14 if advanced else 9, 5, 2, 40, 1), 1),
                metabolic_tumor_volume_ml=round(ctx.normal(320 if advanced else 90, 150, 5, 2000, 0), 0),
                total_lesion_glycolysis=round(ctx.normal(2200 if advanced else 600, 1200, 20, 15000, 0), 0),
                mediastinal_mass_ratio=round(ctx.rand(0.1, 0.45), 2))

        # ---- 2) 예후지수
        risk = RISK[min(3, ipi if not hodgkin else ctx.randint(0, 3))]
        b_sym = ctx.bern(0.35 if advanced else 0.12)
        ctx.ext("LYMPHOMA_ASSESSMENT", p, vid=vid, assessment_date=index,
                b_symptoms_yn=1 if b_sym else 0,
                fever_yn=1 if (b_sym and ctx.bern(0.6)) else 0,
                night_sweats_yn=1 if (b_sym and ctx.bern(0.7)) else 0,
                weight_loss_percent_6m=round(ctx.rand(5.0, 15.0), 1) if b_sym else 0.0,
                prognostic_index_date=index, ipi_score=ipi,
                ipi_risk_group_concept_id=ctx.cs("RISK_GROUP", risk), ipi_risk_group_source_value=risk,
                aaipi_score=min(3, ipi), nccn_ipi_score=min(8, ipi + ctx.randint(0, 3)),
                flipi_score=ctx.randint(0, 5), flipi2_score=ctx.randint(0, 5),
                mipi_score=ctx.randint(0, 11),
                mipi_c_risk_group_concept_id=ctx.cs("RISK_GROUP", risk), mipi_c_risk_group_source_value=risk,
                ips_score=ctx.randint(0, 7), pit_score=ctx.randint(0, 4),
                gelf_high_burden_yn=1.0 if (advanced and ctx.bern(0.4)) else 0.0)

        # ---- 3) 1차 항암
        start = ctx.days(index, ctx.randint(10, 28))
        cycles = 6 if not hodgkin else 4
        regimen, drugs = ("R-CHOP", RCHOP) if not hodgkin else ("ABVD", ABVD)
        tx = ctx.episode(p, start, ctx.days(start, 21 * (cycles - 1) + 20), ctx.seeds["episode_regimen"],
                         concept, number=1, parent=ep)
        for c in range(cycles):
            day = ctx.days(start, 21 * c)
            if day > ctx.today or (p.death_date and day > p.death_date):
                break
            cv = ctx.visit_on(p, day)
            for drug in drugs:
                did = ctx.drug(p, day, drug, days=1, vid=cv, source=regimen)
                ctx.episode_event(tx, did, ctx.seeds["field_drug"])
            ctx.measure(p, day, WBC, ctx.normal(3.6, 1.8, 0.4, 14.0, 1), vid=cv)
            if ctx.bern(0.22):
                ae = ctx.condition(p, day, ctx.choice([4160887, 440674, 378253]), vid=cv,
                                   source=f"CTCAE grade {ctx.randint(1, 4)}")
                ctx.episode_event(tx, ae, ctx.seeds["field_condition"])
            if c in (1, cycles - 1):          # 중간·말기 PET
                rday = ctx.days(day, 18)
                if rday <= ctx.today and not (p.death_date and rday > p.death_date):
                    rv = ctx.visit_on(p, rday)
                    ctx.procedure(p, rday, PET, vid=rv, source="PET-CT")
                    ctx.measure(p, rday, 36769180, vid=rv,
                                source=f"Deauville {ctx.choice([1, 2, 3, 4, 5], p=[0.3, 0.3, 0.2, 0.15, 0.05])}")
                    ctx.ext("LYMPHOMA_EXAM", p, vid=rv, exam_date=rday,
                            pet_suvmax=round(ctx.normal(4, 3, 0.5, 20, 1), 1),
                            metabolic_tumor_volume_ml=round(ctx.normal(40, 40, 0, 500, 0), 0),
                            total_lesion_glycolysis=round(ctx.normal(150, 150, 0, 2000, 0), 0),
                            mediastinal_mass_ratio=round(ctx.rand(0.05, 0.3), 2))

        # ---- 4) 경과 사건: 형질전환·이식·CAR-T
        ev_day = ctx.days(start, 21 * cycles + ctx.randint(30, 200))
        if ev_day <= ctx.today and not (p.death_date and ev_day > p.death_date):
            transform = sub_cd == "FL" and ctx.bern(0.12)
            sct = advanced and ctx.bern(0.15)
            car_t = (not hodgkin) and advanced and ctx.bern(0.08)
            ev = ctx.visit_on(p, ev_day)
            row = dict(event_date=ev_day,
                       transformation_yn=1 if transform else 0,
                       sct_yn=1 if sct else 0,
                       car_t_yn=1 if car_t else 0)
            # 일어난 사건만 날짜와 종류를 적는다. 안 일어난 것은 비워 둔다(조건부 필수).
            if transform:
                row.update(transformation_date=ev_day,
                           transformation_from_subtype_concept_id=ctx.cs("LYMPHOMA_SUBTYPE", "FL"),
                           transformation_from_subtype_source_value="여포림프종",
                           transformation_to_subtype_concept_id=ctx.cs("LYMPHOMA_SUBTYPE", "DLBCL"),
                           transformation_to_subtype_source_value="미만성 거대B세포림프종")
            if sct:
                row.update(sct_date=ctx.days(ev_day, 30),
                           sct_type_concept_id=ctx.cs("SCT_TYPE", "자가"), sct_type_source_value="자가")
            if car_t:
                row.update(apheresis_date=ctx.days(ev_day, 7),
                           lymphodepletion_start_date=ctx.days(ev_day, 25),
                           car_t_infusion_date=ctx.days(ev_day, 30),
                           car_t_target_concept_id=ctx.cs("SCT_TYPE", "자가"), car_t_target_source_value="CD19")
            ctx.ext("LYMPHOMA_EVENT", p, vid=ev, **row)

        # ---- 5) 추적
        for k in range(1, 9):
            day = ctx.days(index, 120 * k)
            if day > ctx.today or (p.death_date and day > p.death_date):
                break
            fv = ctx.visit(p, day, OUTPATIENT)
            ctx.measure(p, day, LDH, ctx.normal(200, 60, 90, 800, 0), vid=fv)
        ctx.finalize_person(p)
