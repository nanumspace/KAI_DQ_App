# -*- coding: utf-8 -*-
"""대사이상지방간염(MASLD) 코호트 시나리오 (v2 저장 구조).

여정
  1) 진단 외래: MASLD 진단과 심장대사 위험인자, 간효소·지질·혈소판·HbA1c, 신체계측
  2) 비침습 검사: 섬유화스캔(LSM·CAP)과 일부 MRI-PDFF/MRE → MASLD_EXAM
  3) 일부 환자는 간생검 → SPECIMEN + PATHOLOGY_REPORT(지방증·소엽염증·풍선변성·섬유화 병기·NAS)
  4) 6~12개월 간격 추적: 비침습 점수(FIB-4·ELF·MELD·Child-Pugh) → MASLD_ASSESSMENT
  5) 경과 사건: MASH 해소·섬유화 호전·간경변·대상부전·간세포암 → MASLD_EVENT

간생검은 일부만 받는다. 그래서 PATHOLOGY_REPORT 의 MASLD 컬럼은 생검을 한 환자에게만 생긴다 —
행 종류(BIOPSY)에 걸린 조건부 필수가 이 코호트에서 어떻게 도는지 여기서 확인된다.
"""
import datetime as dt

from framework_v2 import D, FEMALE, MALE, OUTPATIENT, CtxV2

MASLD, MASH, CIRRHOSIS, HCC = 4059290, 4278234, 192680, 4246127
T2DM, HTN, DLP, OBESITY = 201826, 320128, 432867, 433736
AST, ALT, GGT, PLT, ALB, BILI, INR = 3013721, 3006923, 3026910, 3024929, 3024561, 3024128, 3022217
A1C, TG, HDL, HT, WT, BMI = 3004410, 3022192, 3007070, 3036277, 3025315, 3038553
FIBROSCAN, LIVER_BX = 4324124, 4056894
LIVER_SPEC = 4001271


def generate(ctx: CtxV2, n=100):
    for _ in range(n):
        gender = FEMALE if ctx.bern(0.45) else MALE
        age = int(ctx.normal(54, 12, 20, 85, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 4))
        p = ctx.person(gender, age, index)
        # 섬유화가 진행한 환자일수록 검사 수치와 경과가 함께 나빠진다
        stage = ctx.choice(["F0", "F1", "F2", "F3", "F4"], p=[0.22, 0.3, 0.24, 0.16, 0.08])
        advanced = stage in ("F3", "F4")
        nas = ctx.randint(3, 8) if ctx.bern(0.6) else ctx.randint(0, 3)
        # 사망은 여정을 적기 전에 정한다. 뒤에서 정하면 앞서 적은 사건이 사망일 뒤에 남는다.
        # 추적 중에 간경변으로 진행한 환자는 이 창 안에서는 죽지 않는다 — 처음부터 F4 인 환자만 본다.
        if stage == "F4" and ctx.bern(0.12):
            d = ctx.days(index, ctx.randint(700, 365 * 6))
            if d <= ctx.today:
                ctx.set_death(p, d)

        # ---- 1) 진단 외래
        vid = ctx.visit(p, index, OUTPATIENT)
        dx = ctx.condition(p, index, MASLD, vid=vid, source="K76.0")
        ep = ctx.episode(p, index, None, ctx.seeds["episode_disease"], MASLD)
        ctx.episode_event(ep, dx, ctx.seeds["field_condition"])
        if nas >= 4:
            ctx.condition(p, index, MASH, vid=vid, source="K75.8")
        # MASLD 는 정의상 심장대사 위험인자를 하나 이상 동반한다. 하나도 없는 환자는 그 정의에 맞지 않는다.
        risks = [(c, src) for c, src, prob in
                 ((T2DM, "E11.9", 0.45), (HTN, "I10", 0.5), (DLP, "E78.5", 0.6), (OBESITY, "E66.9", 0.55))
                 if ctx.bern(prob)]
        if not risks:
            risks = [ctx.choice([(T2DM, "E11.9"), (HTN, "I10"), (DLP, "E78.5"), (OBESITY, "E66.9")])]
        for c, src in risks:
            ctx.condition(p, index, c, vid=vid, source=src)

        ht = ctx.normal(170 if gender == MALE else 157, 6, 145, 190)
        wt = ctx.normal(82 if gender == MALE else 72, 14, 45, 140)
        for concept, val in ((HT, ht), (WT, wt), (BMI, round(wt / (ht / 100) ** 2, 1)),
                             (AST, ctx.normal(48 if advanced else 36, 18, 12, 200, 0)),
                             (ALT, ctx.normal(58 if advanced else 44, 24, 10, 260, 0)),
                             (GGT, ctx.normal(70, 40, 10, 400, 0)),
                             (PLT, ctx.normal(160 if advanced else 240, 55, 40, 420, 0)),
                             (ALB, ctx.normal(4.0 if advanced else 4.4, 0.4, 2.2, 5.2, 1)),
                             (BILI, ctx.normal(1.1 if advanced else 0.7, 0.4, 0.2, 6.0, 1)),
                             (INR, ctx.normal(1.15 if advanced else 1.02, 0.12, 0.9, 2.4, 2)),
                             (A1C, ctx.normal(6.4, 1.0, 4.8, 12.0)),
                             (TG, ctx.normal(190, 80, 50, 600, 0)), (HDL, ctx.normal(44, 11, 20, 90, 0))):
            ctx.measure(p, index, concept, val, vid=vid)

        # ---- 2) 비침습 검사
        ex_day = ctx.days(index, ctx.randint(0, 14))
        ev = ctx.visit_on(p, ex_day)
        ctx.procedure(p, ex_day, FIBROSCAN, vid=ev, source="FIBROSCAN")
        lsm = {"F0": 4.5, "F1": 6.5, "F2": 8.5, "F3": 11.5, "F4": 18.0}[stage]
        ctx.ext("MASLD_EXAM", p, vid=ev, exam_date=ex_day, elastography_date=ex_day,
                lsm_kpa=round(ctx.normal(lsm, 1.6, 2.0, 40.0, 1), 1),
                cap_db_m=round(ctx.normal(290, 40, 180, 400, 0), 0),
                mri_pdff_percent=round(ctx.normal(14, 6, 2, 40, 1), 1),
                mre_kpa=round(ctx.normal(lsm / 4 + 1.6, 0.5, 1.5, 9.0, 1), 1),
                hvpg_mmhg=round(ctx.normal(12, 3, 4, 24, 0), 0) if advanced and ctx.bern(0.3) else None,
                spleen_stiffness_kpa=round(ctx.normal(35, 10, 12, 75, 0), 0) if advanced and ctx.bern(0.3) else None)

        # ---- 3) 일부는 간생검
        if ctx.bern(0.35):
            bx_day = ctx.days(index, ctx.randint(14, 60))
            bv = ctx.visit_on(p, bx_day)
            ctx.procedure(p, bx_day, LIVER_BX, vid=bv, source="LIVER-BX")
            spec = ctx.specimen(p, bx_day, LIVER_SPEC, vid=bv, source="LIVER")
            ctx.ext("PATHOLOGY_REPORT", p, vid=bv, specimen_id=spec, specimen_date=bx_day,
                    report_type_concept_id=ctx.cs("CL_PATHOLOGY_REPORT_TYPE", "BIOPSY"),
                    report_type_source_value="BIOPSY",
                    biopsy_method_concept_id=ctx.cs("CL_BIOPSY_METHOD", "CORE"),
                    biopsy_site_concept_id=ctx.cs("CL_BIOPSY_SITE", "PRIMARY"),
                    biopsy_adequacy_concept_id=ctx.cs("CL_BIOPSY_ADEQUACY", "ADEQUATE"),
                    biopsy_histologic_diagnosis_source_value="Steatohepatitis",
                    primary_histology_source_value="Steatohepatitis",
                    steatosis_grade_concept_id=ctx.cs("NAS_STEATOSIS", str(min(3, max(0, nas // 3)))),
                    lobular_inflammation_grade_concept_id=ctx.cs("CL_LOBULAR_INFLAMMATION_GRADE", str(min(3, nas // 3))),
                    ballooning_grade_concept_id=ctx.cs("CL_BALLOONING_GRADE", str(min(2, nas // 4))),
                    fibrosis_stage_concept_id=ctx.cs("FIBROSIS_STAGE", stage),
                    fibrosis_stage_source_value=stage,
                    liver_fibrosis_grade_name_source_value=f"NASH CRN {stage}",
                    nas_score=nas)

        # ---- 4) 추적: 비침습 점수와 경과 사건
        cirrhosis = stage == "F4"
        for k in range(1, ctx.randint(3, 8) + 1):
            day = ctx.days(index, 182 * k)
            if day > ctx.today or (p.death_date and day > p.death_date):
                break
            v = ctx.visit(p, day, OUTPATIENT)
            # FIB-4 는 기록한 검사값에서 바로 계산한다. 따로 뽑으면 점수와 검사값이 어긋난다.
            ast_v = ctx.normal(44, 16, 12, 200, 0)
            alt_v = ctx.normal(52, 22, 10, 250, 0)
            plt = ctx.normal(150 if advanced else 235, 50, 40, 420, 0)
            for concept, val in ((AST, ast_v), (ALT, alt_v), (PLT, plt), (ALB, ctx.normal(4.1, 0.4, 2.2, 5.2, 1))):
                ctx.measure(p, day, concept, val, vid=v)
            age_now = day.year - p.birth.year
            fib4 = round((age_now * ast_v) / (plt * (alt_v ** 0.5)), 2)
            child = "A" if not cirrhosis else ctx.choice(["A", "B", "C"], p=[0.6, 0.3, 0.1])
            ctx.ext("MASLD_ASSESSMENT", p, vid=v, assessment_date=day,
                    prognostic_score_type=1, prognostic_score_value=fib4,
                    fib4_index=fib4, elf_score=round(ctx.normal(9.5, 1.2, 6.0, 14.0, 1)),
                    meld_score=ctx.randint(6, 20) if cirrhosis else ctx.randint(6, 10),
                    child_pugh_class_concept_id=ctx.cs("CHILD_PUGH", child), child_pugh_class_source_value=child,
                    apri_score=round(ctx.normal(0.8, 0.5, 0.1, 4.0, 1)),
                    pro_c3_ng_ml=round(ctx.normal(14, 5, 3, 40, 1), 1))

            became = (not cirrhosis) and advanced and ctx.bern(0.06)
            if became:
                cirrhosis = True
                ctx.condition(p, day, CIRRHOSIS, vid=v, source="K74.6")
            hcc = cirrhosis and ctx.bern(0.02)
            if hcc:
                ctx.condition(p, day, HCC, vid=v, source="C22.0")
            ctx.ext("MASLD_EVENT", p, vid=v, event_date=day,
                    mash_resolution_yn=1 if (nas >= 4 and ctx.bern(0.12)) else 0,
                    fibrosis_improvement_yn=1 if ctx.bern(0.15) else 0,
                    cirrhosis_yn=1 if cirrhosis else 0,
                    decompensation_event_yn=1 if (cirrhosis and ctx.bern(0.08)) else 0,
                    hcc_yn=1 if hcc else 0)

        ctx.finalize_person(p)
