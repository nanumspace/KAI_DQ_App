# -*- coding: utf-8 -*-
"""
림프종 코호트 시나리오 (환자 여정 템플릿)

여정 개요
  1) 진단 입원(5일): 절제 림프절 생검 + 병리/IHC(아형별 표지자), DLBCL 은 FISH(MYC/BCL2/BCL6),
     PET-CT 병기(Lugano, B 증상/결절외/골수/bulky 논리), 골수 생검, 기본 혈액검사(LDH, β2M, CBC 등),
     HBV/HCV/HIV 상태(환자 불변), 예후지수(IPI/FLIPI/MIPI/IPS/PIT), dx 행 + 코호트 진단(같은 날짜)
  2) 1차 항암: DLBCL/MCL R-CHOP, Hodgkin ABVD(doxorubicin+bleomycin+dacarbazine), FL R-CVP 또는 경과관찰,
     PTCL CHOP. tx 행은 antp_id 로 ANTP_THERAPY 와 line/시작일/레지멘 일치.
     중간 PET(Deauville 일관), 종료 PET, 일부 방사선 공고, 사이클마다 검사 + CTCAE 이상사례
  3) 재발/불응(약 30%): outcome 행(재발일 > 1차 종료일), 2차 구제요법(R-GDP 등), 자가조혈모세포이식(입원 21일)
     또는 DLBCL CAR-T(성분채집 <= 림프구감소 <= 주입, CRS 이상사례), FL->DLBCL 전환, 일부 사망(5등급 AE 또는 질병)
  4) 3~6개월 추적 외래(CT), 환자당 마지막 fu 행(last_followup_date >= 모든 날짜, 생존상태/사망일 일치)
특화 테이블(LYMPHOMA)은 이벤트 그룹 단위로 행을 만든다. death_date 는 fu 그룹 필드이므로 fu 행에만 적는다.
"""
from framework import *

SUBTYPES = {
    "DLBCL": dict(concept=4300704, group="non-Hodgkin lymphoma", lineage="B-cell", kcd="C83.3", src="Diffuse large B-cell lymphoma, NOS"),
    "classical Hodgkin lymphoma": dict(concept=438090, group="Hodgkin lymphoma", lineage="B-cell", kcd="C81.9", src="Classical Hodgkin lymphoma, nodular sclerosis"),
    "follicular lymphoma": dict(concept=4147411, group="non-Hodgkin lymphoma", lineage="B-cell", kcd="C82.9", src="Follicular lymphoma, grade 1-2"),
    "mantle cell lymphoma": dict(concept=4038836, group="non-Hodgkin lymphoma", lineage="B-cell", kcd="C83.1", src="Mantle cell lymphoma, classic"),
    "peripheral T-cell lymphoma": dict(concept=4038838, group="non-Hodgkin lymphoma", lineage="T-cell", kcd="C84.4", src="Peripheral T-cell lymphoma, NOS"),
}
SUB_LIST = list(SUBTYPES)
SUB_P = [0.45, 0.20, 0.15, 0.10, 0.10]
NODAL_SITES = ["cervical lymph node", "axillary lymph node", "mediastinal lymph node", "inguinal lymph node", "retroperitoneal lymph node", "abdominal lymph node"]
EXTRANODAL = ["stomach", "bone", "liver", "lung", "skin", "tonsil", "small intestine", "kidney", "pleura"]
R_CHOP = [1314273, 1310317, 1338512, 1308290, 1551099]
CHOP = [1310317, 1338512, 1308290, 1551099]
R_CVP = [1314273, 1310317, 1308290, 1551099]
ABVD = [1338512, 1329033, 1319193]
R_GDP = [1314273, 1314924, 1518254, 1397141]
GDP = [1314924, 1518254, 1397141]
BASE_LABS = [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923, 3020491, 3024128, 3022250, 3006315]
IPI_GROUP = {0: "low", 1: "low", 2: "low-intermediate", 3: "high-intermediate", 4: "high", 5: "high"}
RESP_OF_DS = {1: ("CMR", "CR"), 2: ("CMR", "CR"), 3: ("CMR", "CR"), 4: ("PMR", "PR"), 5: ("PMD", "PD")}

PATH_REPORT = ("Lymph node, {site}, excisional biopsy: {hist}. {arch}. Immunohistochemistry: {ihc}. Ki-67 {ki67}%. "
               "EBER ISH {eber}. Specimen adequate for ancillary studies.")
PET_REPORT = ("FDG PET/CT (baseline). Hypermetabolic lymphadenopathy in {n} nodal regions, SUVmax {suv}. {extra} {spleen} "
              "Largest lesion {size} cm. Impression: Lymphoma, Lugano stage {stage}{suffix}.")
RESP_REPORT = "FDG PET/CT ({tp}). Deauville score {ds}. {resp}."


def generate(ctx: Ctx, n=100):
    for _ in range(n):
        sub = ctx.choice(SUB_LIST, p=SUB_P)
        S = SUBTYPES[sub]
        hl, dlbcl, fl, mcl, ptcl = (sub == "classical Hodgkin lymphoma"), (sub == "DLBCL"), (sub == "follicular lymphoma"), (sub == "mantle cell lymphoma"), (sub == "peripheral T-cell lymphoma")
        gender = FEMALE if ctx.bern(0.42) else MALE
        age = int(ctx.normal(34, 12, 18, 80, 0)) if hl else int(ctx.normal(63, 12, 20, 90, 0))
        index = D(2019, 1, 1) + dt.timedelta(days=ctx.randint(0, 365 * 6 - 5))
        p = ctx.person(gender, age, index)
        hbv = ctx.choice(["HBsAg negative, anti-HBc negative", "HBsAg negative, anti-HBc positive (resolved)", "HBsAg positive (chronic, on prophylaxis)"], p=[0.8, 0.15, 0.05])
        p.patient_fields = dict(hbv_status=hbv, hcv_status="anti-HCV negative" if ctx.bern(0.97) else "anti-HCV positive, HCV RNA detected",
                                hiv_status="HIV Ag/Ab negative" if ctx.bern(0.98) else "HIV positive, on ART")

        # ---- 1) 진단 입원 (5일)
        dx_vid = ctx.visit(p, index, INPATIENT, los=5)
        cid = ctx.condition(p, index, S["concept"], vid=dx_vid)
        if ctx.bern(0.3): ctx.condition(p, index, 320128, vid=dx_vid)      # HTN
        if ctx.bern(0.15): ctx.condition(p, index, 201826, vid=dx_vid)     # T2DM
        primary = ctx.choice(NODAL_SITES)
        # 병기
        stage = ctx.choice(["I", "II", "III", "IV"], p=[0.25, 0.35, 0.2, 0.2] if hl else ([0.1, 0.2, 0.3, 0.4] if (fl or mcl) else [0.15, 0.3, 0.25, 0.3]))
        adv = stage in ("III", "IV")
        ecog = ctx.choice([0, 1, 2, 3], p=[0.35, 0.45, 0.15, 0.05])
        labs = ctx.labs(p, index, BASE_LABS, vid=dx_vid, shifts={3022250: 150 if (adv and (dlbcl or ptcl)) else (40 if adv else 0), 3006315: 1.0 if adv else 0})
        ht = ctx.normal(171 if gender == MALE else 158, 6, 145, 190); wt = ctx.normal(67 if gender == MALE else 56, 9, 38, 110)
        ctx.measure(p, index, 3036277, ht, vid=dx_vid); ctx.measure(p, index, 3025315, wt, vid=dx_vid)
        ctx.observation(p, index, 4257895, vid=dx_vid, value_number=ecog, value_string=f"ECOG {ecog}")
        # 생검 (index 일), 병리 노트
        ctx.procedure(p, index, 4306780, vid=dx_vid)
        ihc = _ihc(ctx, sub)
        ihc_txt = ", ".join(f"{k.split('_')[0].upper()} {v}" for k, v in ihc.items() if isinstance(v, str) and k.endswith("_result") and k not in ("flow_cytometry_result", "ebv_eber_result", "pd_l1_result"))
        ctx.note(p, ctx.days(index, 2), PATH_REPORT.format(site=primary, hist=S["src"], arch="Diffuse growth pattern of large atypical lymphoid cells" if dlbcl else "Effaced nodal architecture",
                                                            ihc=ihc_txt, ki67=ihc.get("ki67_proliferation_index_pct") or "not assessed", eber=ihc["ebv_eber_result"]),
                 note_type=44814640, note_class=36716165, vid=dx_vid)
        # PET-CT 병기 (index+1), 골수 생검 (index+2)
        pet_day = ctx.days(index, 1); bm_day = ctx.days(index, 2)
        ctx.procedure(p, pet_day, 4305790, vid=dx_vid)
        ctx.procedure(p, bm_day, 4023083, vid=dx_vid)
        st = _stage_fields(ctx, stage, sub, ecog, wt)
        suv = ctx.normal(18 if (dlbcl or hl or ptcl) else 9, 5, 3, 40)
        ctx.note(p, pet_day, PET_REPORT.format(n=st["nodal_regions_involved_count"], suv=suv, extra=f"Extranodal involvement: {st['extranodal_sites']}." if st["extranodal_involvement_yn"] else "No extranodal involvement.",
                                               spleen="Splenic involvement." if st["spleen_involvement_yn"] else "", size=st["largest_lesion_diameter_cm"], stage=stage, suffix=st["stage_suffix"]), vid=dx_vid)
        stage_day = ctx.days(index, 3)
        # 특화 테이블 진단 시 그룹들
        ctx.disease_row(p, dx_vid, condition_occurrence_id=cid, diagnosis_date=index, diagnosis_status="newly diagnosed", lymphoma_group=S["group"], cell_lineage=S["lineage"],
                        histologic_subtype=sub, histologic_subtype_source_value=f"{S['kcd']} {S['src']}",
                        classification_version="WHO-HAEM5 (2022)" if index.year >= 2023 else "WHO 2017 (revised 4th edition)", primary_disease_site=primary)
        ctx.disease_row(p, dx_vid, biopsy_date=index, biopsy_method="excisional", biopsy_site=primary, biopsy_specimen_adequacy="adequate")
        ctx.disease_row(p, dx_vid, biopsy_date=bm_day, biopsy_method="bone marrow biopsy", biopsy_site="posterior iliac crest",
                        biopsy_specimen_adequacy="adequate" if ctx.bern(0.95) else "suboptimal (hemodilute aspirate)")
        ctx.disease_row(p, dx_vid, ihc_test_date=ctx.days(index, 2), **ihc)
        ctx.disease_row(p, dx_vid, stage_assessment_date=stage_day, **st)
        ctx.disease_row(p, dx_vid, pet_ct_assessment_date=pet_day, pet_suvmax=suv, metabolic_tumor_volume=round(ctx.rand(20, 600) * (2 if adv else 1), 1),
                        total_lesion_glycolysis=round(ctx.rand(100, 4000) * (2 if adv else 1), 1))
        mol = _molecular(ctx, sub)
        if mol:
            ctx.disease_row(p, dx_vid, molecular_test_date=ctx.days(index, 4), **mol)
        prog = _prognostic(ctx, sub, p.age_at_index, labs, ecog, stage, st, ihc, gender)
        ctx.disease_row(p, dx_vid, prognostic_score_date=stage_day, **prog)
        last_date = stage_day          # 특화 테이블에 기록된 마지막 날짜 (fu 행 산정용)

        # ---- 2) 치료 계획
        lines = []                     # antp_ids
        end1 = None
        outcome = ctx.choice(["cured", "relapse", "refractory"], p=[0.68, 0.22, 0.10] if not (fl or hl) else ([0.6, 0.35, 0.05] if fl else [0.8, 0.15, 0.05]))
        fatal_ae = ctx.bern(0.03)
        watch_wait = fl and stage in ("III", "IV") and ctx.bern(0.5) and not fatal_ae
        remission = False
        if not watch_wait:
            s1 = ctx.days(index, ctx.randint(10, 25))
            if hl:
                regimen, drugs, cyc_n, cd, cat, inp = "ABVD (doxorubicin + bleomycin + dacarbazine)", ABVD, (8 if not adv else 12), 14, 1, False
            elif fl:
                regimen, drugs, cyc_n, cd, cat, inp = "R-CVP", R_CVP, 6, 21, 2, False
            elif ptcl:
                regimen, drugs, cyc_n, cd, cat, inp = "CHOP", CHOP, 6, 21, 1, True
            else:
                regimen, drugs, cyc_n, cd, cat, inp = "R-CHOP", R_CHOP, (4 if (not adv and not st["bulky_disease_yn"] and dlbcl) else 6), 21, 2, True
            rt = (not adv and (hl or dlbcl) and ctx.bern(0.6)) or (st["bulky_disease_yn"] == 1 and ctx.bern(0.5))
            rt = rt and outcome != "refractory" and not fatal_ae
            fatal_cycle = ctx.randint(1, cyc_n - 1) if fatal_ae else None
            if outcome == "refractory": cyc_n = 2
            if fatal_ae: cyc_n = fatal_cycle + 1
            aid, e1, cyc = ctx.antp(p, 1, regimen, drugs, s1, cyc_n, 5, cat, ecog=ecog,
                                    response="PD" if outcome == "refractory" else ("CR" if not fatal_ae else "NE"), cycle_days=cd, inpatient_first=inp)
            lines.append(aid)
            ctx.disease_row(p, ctx.visit_on(p, s1), antp_id=aid, disease_course_status="treatment-naive", primary_refractory_yn=1 if outcome == "refractory" else 0,
                            prior_lines_of_therapy_count=0, current_line_of_therapy=1, treatment_regimen=regimen, treatment_start_date=s1, treatment_end_date=e1,
                            treatment_cycle_count=len(cyc), prior_anti_cd20_therapy_yn=0, prior_anthracycline_therapy_yn=0, prior_btk_inhibitor_therapy_yn=0,
                            prior_checkpoint_inhibitor_yn=0, radiotherapy_yn=1 if rt else 0, radiotherapy_site=primary if rt else None,
                            radiotherapy_total_dose_gy=(30.0 if hl else 36.0) if rt else None)
            end1 = e1; last_date = max(last_date, e1)
            dead = _chemo_monitoring(ctx, p, cyc, aid, drugs, fatal_cycle=fatal_cycle)
            if dead:
                _finish(ctx, p, last_date, "progressive" if outcome == "refractory" else "stable", cause="treatment-related infection (febrile neutropenia)")
                continue
            # 중간 PET
            if len(cyc) >= 3:
                interim = ctx.days(cyc[2], -1)
            else:
                interim = ctx.days(e1, 10)
            if outcome == "refractory":
                ds = 5
            else:
                ds = ctx.choice([1, 2, 3, 4], p=[0.2, 0.35, 0.3, 0.15])
            last_date = max(last_date, _response(ctx, p, interim, "interim PET2", ds, aid))
            if outcome == "refractory":
                pd_day = interim
                ctx.disease_row(p, ctx.visit_on(p, pd_day), progression_date=pd_day, relapse_sites=None)
                ctx.antp_update(aid, days_to_progression=pd_day, progression_or_recurrence_anatomic_site=primary)
                last_date = max(last_date, pd_day)
                last_date, dead = _salvage(ctx, p, sub, ecog, primary, pd_day, lines, last_date, refractory=True, prior_regimen=regimen)
                if dead:
                    continue
                remission = not dead and getattr(p, "_remission", False)
            else:
                # 방사선 공고 및 종료 PET
                eot_base = e1
                if rt:
                    rt_day = ctx.days(e1, ctx.randint(21, 35))
                    rvid = ctx.visit_on(p, rt_day)
                    ctx.procedure(p, rt_day, 4181206, vid=rvid)
                    ctx.note(p, rt_day, f"Involved-site radiotherapy to {primary}, {30 if hl else 36} Gy in {15 if hl else 18} fractions started.", note_type=32831, note_class=36716177, vid=rvid)
                    eot_base = ctx.days(rt_day, 21 if hl else 25)
                eot = ctx.days(eot_base, ctx.randint(21, 35))
                ds = ctx.choice([1, 2, 3], p=[0.3, 0.4, 0.3])
                last_date = max(last_date, _response(ctx, p, eot, "end of treatment", ds, aid))
                remission = True
        else:
            # 경과관찰 (FL)
            ctx.note(p, stage_day, "Low tumor burden follicular lymphoma (GELF criteria not met). Plan: watch and wait with 3-monthly follow-up.",
                     note_type=32831, note_class=36716177, vid=dx_vid)

        # ---- 3) 추적, 재발/전환, 구제
        status = "remission" if remission else ("stable" if watch_wait else "remission")
        fu_from = last_date
        dead = False
        if outcome == "relapse" and not watch_wait:
            rel = ctx.days(end1, ctx.randint(150, 900))
            if rel <= ctx.days(ctx.today, -240):
                fu_from = _followups(ctx, p, fu_from, rel, "CR")
                rvid = ctx.visit_on(p, rel)
                ctx.procedure(p, rel, 4305790, vid=rvid)
                sites = ctx.choice(NODAL_SITES) + ("; " + ctx.choice(EXTRANODAL) if ctx.bern(0.4) else "")
                ctx.note(p, rel, f"FDG PET/CT: new hypermetabolic lesions ({sites}). Relapsed lymphoma.", vid=rvid)
                ctx.disease_row(p, rvid, progression_date=rel, relapse_date=rel, relapse_sites=sites)
                ctx.antp_update(lines[0], days_to_progression=rel, progression_or_recurrence_anatomic_site=sites.split(";")[0])
                last_date = max(last_date, rel)
                last_date, dead = _salvage(ctx, p, sub, ecog, primary, rel, lines, last_date, refractory=False, prior_regimen=regimen)
                fu_from = last_date
                status = "remission" if getattr(p, "_remission", False) else "progressive"
        elif fl and ctx.bern(0.25):
            # 조직학적 전환 FL -> DLBCL
            tdate = ctx.days(last_date, ctx.randint(365, 1400))
            if tdate <= ctx.days(ctx.today, -240):
                fu_from = _followups(ctx, p, fu_from, tdate, "CR" if not watch_wait else "SD")
                tvid = ctx.visit(p, tdate, INPATIENT, los=3)
                ctx.condition(p, tdate, 4300704, vid=tvid)
                ctx.procedure(p, tdate, 4306780, vid=tvid)
                ctx.procedure(p, tdate, 4305790, vid=tvid)
                ihc2 = _ihc(ctx, "DLBCL"); ihc2.pop("cell_of_origin", None)
                ctx.note(p, ctx.days(tdate, 2), PATH_REPORT.format(site=ctx.choice(NODAL_SITES), hist="Diffuse large B-cell lymphoma, transformed from follicular lymphoma",
                                                                    arch="Sheets of large centroblastic cells", ihc="CD20 positive, CD10 positive, BCL2 positive", ki67=ihc2["ki67_proliferation_index_pct"], eber="negative"),
                         note_type=44814640, note_class=36716165, vid=tvid)
                ctx.disease_row(p, tvid, biopsy_date=tdate, biopsy_method="excisional", biopsy_site=ctx.choice(NODAL_SITES), biopsy_specimen_adequacy="adequate")
                ctx.disease_row(p, tvid, ihc_test_date=ctx.days(tdate, 2), **ihc2)
                ctx.disease_row(p, tvid, transformation_yn=1, transformation_from_subtype="follicular lymphoma", transformation_to_subtype="DLBCL", transformation_date=tdate)
                ctx.disease_row(p, tvid, progression_date=tdate, relapse_date=tdate if end1 else None, relapse_sites="transformed disease, " + primary)
                if lines:
                    ctx.antp_update(lines[0], days_to_progression=tdate, progression_or_recurrence_anatomic_site=primary)
                last_date = max(last_date, tdate)
                line = len(lines) + 1
                s2 = ctx.days(tdate, ctx.randint(7, 21))
                aid2, e2, cyc2 = ctx.antp(p, line, "R-CHOP", R_CHOP, s2, 6, 5 if line == 1 else 6, 2, ecog=ecog, response="CR", inpatient_first=True)
                lines.append(aid2)
                ctx.disease_row(p, ctx.visit_on(p, s2), antp_id=aid2, disease_course_status="relapsed" if line > 1 else "treatment-naive", primary_refractory_yn=0,
                                prior_lines_of_therapy_count=line - 1, current_line_of_therapy=line, treatment_regimen="R-CHOP", treatment_start_date=s2, treatment_end_date=e2,
                                treatment_cycle_count=len(cyc2), prior_anti_cd20_therapy_yn=1 if line > 1 else 0, prior_anthracycline_therapy_yn=0, prior_btk_inhibitor_therapy_yn=0,
                                prior_checkpoint_inhibitor_yn=0, radiotherapy_yn=0)
                _chemo_monitoring(ctx, p, cyc2, aid2, R_CHOP)
                last_date = max(last_date, e2)
                eot = ctx.days(e2, ctx.randint(21, 35))
                ds = ctx.choice([1, 2, 3, 4], p=[0.3, 0.35, 0.25, 0.1])
                last_date = max(last_date, _response(ctx, p, eot, "end of treatment", ds, aid2))
                fu_from = last_date
                status = "remission"
        if dead:
            continue
        # 정기 추적 후 마지막 fu 행
        last_fu = _followups(ctx, p, fu_from, ctx.today, "CR" if status == "remission" else "SD")
        _finish(ctx, p, max(last_date, last_fu), status)


# ----------------------------------------------------------------------------------------------- helpers
def _finish(ctx, p, last_date, status, cause=None):
    """마지막 fu 행 + PERSON 확정. 사망자는 last_followup_date = death_date."""
    if p.death_date is not None:
        d = p.death_date
        ctx.disease_row(p, ctx.visit_on(p, d), last_followup_date=d, disease_status_at_last_followup=status, vital_status="dead", death_date=d, cause_of_death=cause or "lymphoma progression")
    else:
        d = last_date
        if ctx.days(d, 14) <= ctx.today and not any(s == d for _, s, _, _ in p.visits):
            d = ctx.days(d, ctx.randint(14, 45))
            if d > ctx.today: d = last_date
        ctx.disease_row(p, ctx.visit_on(p, d), last_followup_date=d, disease_status_at_last_followup=status, vital_status="alive")
    ctx.finalize_person(p)


def _followups(ctx, p, start, until, anat):
    """3~6개월 간격 추적 외래 (CT + 검사 + follow-up 반응평가). 마지막 방문일을 반환."""
    fu = ctx.days(start, ctx.randint(80, 120)); last = start; k = 0
    while fu < ctx.days(until, -20) and fu <= ctx.today and k < 12:
        fvid = ctx.visit_on(p, fu)
        ctx.procedure(p, fu, 4207701, vid=fvid)
        ctx.labs(p, fu, [3000963, 3022250], vid=fvid)
        ctx.disease_row(p, fvid, response_assessment_date=fu, response_assessment_timepoint="follow-up", response_criteria="Lugano 2014",
                        response_assessment_modality="CT", anatomic_response=anat)
        last = fu
        fu = ctx.days(fu, ctx.randint(85, 185)); k += 1
    return last


def _response(ctx, p, day, timepoint, ds, aid):
    """PET 반응평가 (resp + pet 행, PET 처치, 판독 노트). Deauville 와 대사반응 일관."""
    vid = ctx.visit_on(p, day)
    ctx.procedure(p, day, 4305790, vid=vid)
    met, anat = RESP_OF_DS[ds]
    suv = ctx.normal(2.0, 0.5, 0.8, 3.0) if ds <= 3 else ctx.normal(8 if ds == 4 else 16, 3, 4, 40)
    ctx.note(p, day, RESP_REPORT.format(tp=timepoint, ds=ds, resp={"CMR": "Complete metabolic response", "PMR": "Partial metabolic response", "PMD": "Progressive metabolic disease"}[met]), vid=vid)
    ctx.disease_row(p, vid, antp_id=aid, response_assessment_date=day, response_assessment_timepoint=timepoint, response_criteria="Lugano 2014", response_assessment_modality="PET/CT",
                    deauville_score=ds, anatomic_response=anat, metabolic_response=met, best_overall_response=anat if timepoint != "interim PET2" else None)
    ctx.disease_row(p, vid, pet_ct_assessment_date=day, pet_suvmax=suv, metabolic_tumor_volume=round(ctx.rand(0, 5) if ds <= 3 else ctx.rand(20, 400), 1),
                    total_lesion_glycolysis=round(ctx.rand(0, 10) if ds <= 3 else ctx.rand(100, 3000), 1))
    return day


def _salvage(ctx, p, sub, ecog, primary, pd_day, lines, last_date, refractory, prior_regimen):
    """2차 구제요법 -> 반응 PET -> 자가이식 / CAR-T / 진행 -> 일부 사망. (last_date, dead) 반환."""
    hl, dlbcl = sub == "classical Hodgkin lymphoma", sub == "DLBCL"
    bcell = sub != "peripheral T-cell lymphoma"
    line = len(lines) + 1
    s2 = ctx.days(pd_day, ctx.randint(7, 21))
    if hl:
        regimen, drugs, cat, cyc_n = "Brentuximab vedotin", [1305058], 4, 4
    elif bcell:
        regimen, drugs, cat, cyc_n = "R-GDP", R_GDP, 2, 3
    else:
        regimen, drugs, cat, cyc_n = "GDP", GDP, 1, 3
    aid2, e2, cyc2 = ctx.antp(p, line, regimen, drugs, s2, cyc_n, 6, cat, ecog=min(ecog + 1, 3), response=None)
    lines.append(aid2)
    ctx.disease_row(p, ctx.visit_on(p, s2), antp_id=aid2, disease_course_status="refractory" if refractory else "relapsed", primary_refractory_yn=1 if refractory else 0,
                    prior_lines_of_therapy_count=line - 1, current_line_of_therapy=line, treatment_regimen=regimen, treatment_start_date=s2, treatment_end_date=e2,
                    treatment_cycle_count=len(cyc2), prior_anti_cd20_therapy_yn=1 if "R-" in prior_regimen else 0,
                    prior_anthracycline_therapy_yn=1 if ("CHOP" in prior_regimen or "ABVD" in prior_regimen) else 0, prior_btk_inhibitor_therapy_yn=0,
                    prior_checkpoint_inhibitor_yn=0, radiotherapy_yn=0)
    _chemo_monitoring(ctx, p, cyc2, aid2, drugs, ae_p=0.5)
    last_date = max(last_date, e2)
    resp_day = ctx.days(e2, ctx.randint(14, 28))
    sensitive = ctx.bern(0.35 if refractory else 0.7)
    ds = ctx.choice([2, 3, 4], p=[0.4, 0.4, 0.2]) if sensitive else 5
    last_date = max(last_date, _response(ctx, p, resp_day, "end of treatment", ds, aid2))
    ctx.antp_update(aid2, best_overall_response_source_value=RESP_OF_DS[ds][1])
    if not sensitive:
        ctx.antp_update(aid2, days_to_progression=resp_day, progression_or_recurrence_anatomic_site=primary)
        ctx.disease_row(p, ctx.visit_on(p, resp_day), progression_date=resp_day, relapse_sites=primary)
    p._remission = False
    if sensitive and p.age_at_index <= 68 and ecog <= 2 and ctx.days(resp_day, 90) <= ctx.today:
        # 자가조혈모세포이식 (입원 21일)
        sct = ctx.days(resp_day, ctx.randint(30, 50))
        svid = ctx.visit(p, sct, INPATIENT, los=21)
        ctx.procedure(p, ctx.days(sct, -10), 4283893, vid=ctx.visit_on(p, ctx.days(sct, -10)))          # 말초혈 조혈모세포 채집
        ctx.procedure(p, sct, 4030027, vid=svid)
        ctx.note(p, sct, "High-dose chemotherapy (BEAM) followed by autologous peripheral blood stem cell infusion (day 0).", note_type=32831, note_class=36716177, vid=svid)
        ctx.disease_row(p, svid, stem_cell_transplant_yn=1, stem_cell_transplant_type="autologous", stem_cell_transplant_date=sct)
        ctx.labs(p, ctx.days(sct, 7), [3000963, 3010813, 3017732, 3024929], vid=svid, shifts={3017732: -3.5, 3010813: -5.0, 3024929: -150, 3000963: -3.0})
        ctx.ae(p, ctx.days(sct, 6), 4304213, 3, antp_id=aid2, vid=svid, action=1)
        ctx.condition(p, ctx.days(sct, 6), 4304213, vid=svid)
        ctx.drug(p, ctx.days(sct, 5), 1301125, 7, vid=svid, freq=1)
        if ctx.bern(0.5):
            ctx.ae(p, ctx.days(sct, 8), 4265412, ctx.randint(2, 3), antp_id=aid2, vid=svid)
        post = ctx.days(sct, ctx.randint(90, 110))
        if post <= ctx.today:
            last_date = max(last_date, _response(ctx, p, post, "follow-up", ctx.choice([1, 2, 3]), aid2))
        p._remission = True
        return max(last_date, ctx.days(sct, 21)), False
    if dlbcl and (not sensitive or ctx.bern(0.3)) and ctx.days(resp_day, 120) <= ctx.today:
        # CAR-T (line+1): 성분채집 -> 림프구감소(입원) -> 주입 -> CRS
        line3 = len(lines) + 1
        leuk = ctx.days(resp_day, ctx.randint(7, 14))
        ctx.procedure(p, leuk, 4283893, vid=ctx.visit_on(p, leuk))
        ld = ctx.days(leuk, ctx.randint(24, 35))
        cvid = ctx.visit(p, ld, INPATIENT, los=16)
        aid3, e3, cyc3 = ctx.antp(p, line3, "Axicabtagene ciloleucel (CD19 CAR-T) after Flu/Cy lymphodepletion", [1310317], ld, 3, 6, 6, ecog=min(ecog + 1, 3), cycle_days=1)
        lines.append(aid3)
        inf = ctx.days(ld, 5)
        ctx.procedure(p, inf, 4053096, vid=cvid)
        ctx.note(p, inf, "CD19-directed CAR-T (axicabtagene ciloleucel) infused on day 0 after fludarabine/cyclophosphamide lymphodepletion.", note_type=32831, note_class=36716177, vid=cvid)
        ctx.disease_row(p, cvid, antp_id=aid3, disease_course_status="refractory", primary_refractory_yn=1 if refractory else 0, prior_lines_of_therapy_count=line3 - 1,
                        current_line_of_therapy=line3, treatment_regimen="Axicabtagene ciloleucel (CD19 CAR-T) after Flu/Cy lymphodepletion", treatment_start_date=ld,
                        treatment_end_date=e3, treatment_cycle_count=len(cyc3), prior_anti_cd20_therapy_yn=1, prior_anthracycline_therapy_yn=1,
                        prior_btk_inhibitor_therapy_yn=0, prior_checkpoint_inhibitor_yn=0, radiotherapy_yn=0)
        ctx.disease_row(p, cvid, antp_id=aid3, car_t_therapy_yn=1, car_t_target_antigen="CD19", car_t_product_source_value="axicabtagene ciloleucel (Yescarta)",
                        leukapheresis_date=leuk, lymphodepletion_start_date=ld, car_t_infusion_date=inf)
        crs_day = ctx.days(inf, ctx.randint(1, 5))
        g = ctx.choice([1, 2, 3], p=[0.4, 0.4, 0.2])
        ctx.ae(p, crs_day, 4185711, g, antp_id=aid3, vid=cvid, action=1, causality=1)
        ctx.condition(p, crs_day, 4185711, vid=cvid)
        ctx.labs(p, crs_day, [3020460, 3010813, 3017732], vid=cvid, shifts={3020460: 60 * g, 3017732: -3.0})
        d30 = ctx.days(inf, 30)
        ds30 = ctx.choice([1, 2, 3], p=[0.4, 0.35, 0.25]) if ctx.bern(0.55) else 5
        last_date = max(last_date, _response(ctx, p, d30, "follow-up", ds30, aid3))
        ctx.antp_update(aid3, best_overall_response_source_value=RESP_OF_DS[ds30][1])
        if ds30 == 5:
            ctx.antp_update(aid3, days_to_progression=d30, progression_or_recurrence_anatomic_site=primary)
            ctx.disease_row(p, ctx.visit_on(p, d30), progression_date=d30, relapse_sites=primary)
            return _disease_death(ctx, p, d30, last_date)
        p._remission = True
        return max(last_date, e3), False
    if not sensitive:
        return _disease_death(ctx, p, resp_day, last_date)
    p._remission = True
    return last_date, False


def _disease_death(ctx, p, after, last_date):
    """진행 후 30~150일 내 사망 (오늘 이후이면 생존 추적으로 남김)."""
    dd = ctx.days(after, ctx.randint(30, 150))
    if dd > ctx.today:
        return last_date, False
    ctx.visit(p, ctx.days(dd, -3), INPATIENT, los=3)
    ctx.set_death(p, dd)
    _finish(ctx, p, last_date, "progressive", cause="lymphoma progression")
    return dd, True


def _ihc(ctx, sub):
    pos, neg = "positive", "negative"
    f = dict(cd3_result=neg, cd5_result=neg, cd10_result=neg, cd15_result=neg, cd19_result=pos, cd20_result=pos, cd22_result=pos, cd23_result=neg, cd30_result=neg,
             cd79a_result=pos, pax5_result=pos, bcl2_expression_result=None, bcl6_expression_result=None, mum1_expression_result=None, myc_expression_result=None,
             cyclin_d1_result=neg, sox11_result=neg, alk_result=neg, pd_l1_result=None, ki67_proliferation_index_pct=None, ebv_eber_result=neg, cell_of_origin=None,
             double_expressor_yn=None, flow_cytometry_result=None)
    if sub == "DLBCL":
        cd10 = ctx.bern(0.4); bcl6 = ctx.bern(0.7); mum1 = ctx.bern(0.5)
        coo = "GCB" if cd10 or (bcl6 and not mum1) else "ABC/non-GCB"
        myc = ctx.randint(10, 80); bcl2 = ctx.randint(10, 95)
        f.update(cd10_result=pos if cd10 else neg, cd5_result=pos if ctx.bern(0.08) else neg, cd30_result=pos if ctx.bern(0.15) else neg,
                 bcl2_expression_result=f"{'positive' if bcl2 >= 50 else 'negative'} ({bcl2}%)", bcl6_expression_result=f"{'positive' if bcl6 else 'negative'} ({ctx.randint(40, 90) if bcl6 else ctx.randint(0, 25)}%)",
                 mum1_expression_result=f"{'positive' if mum1 else 'negative'} ({ctx.randint(35, 90) if mum1 else ctx.randint(0, 25)}%)", myc_expression_result=f"{'positive' if myc >= 40 else 'negative'} ({myc}%)",
                 pd_l1_result=f"{ctx.choice([0, 1, 5, 10, 30])}% (SP263)", ki67_proliferation_index_pct=ctx.randint(55, 95), ebv_eber_result=pos if ctx.bern(0.05) else neg,
                 cell_of_origin=coo, double_expressor_yn=1 if (myc >= 40 and bcl2 >= 50) else 0,
                 flow_cytometry_result="Clonal kappa-restricted B-cell population, CD19+ CD20+ CD10" + ("+" if cd10 else "-"))
    elif sub == "classical Hodgkin lymphoma":
        f.update(cd15_result=pos if ctx.bern(0.85) else neg, cd30_result=pos, cd20_result=neg if ctx.bern(0.8) else "weak positive (subset)", cd19_result=neg, cd22_result=neg,
                 cd79a_result=neg, pax5_result="weak positive", ki67_proliferation_index_pct=None, ebv_eber_result=pos if ctx.bern(0.3) else neg,
                 pd_l1_result=f"{ctx.choice([50, 70, 90])}% on Hodgkin/Reed-Sternberg cells (22C3)",
                 flow_cytometry_result="No clonal B-cell population; reactive background T cells")
    elif sub == "follicular lymphoma":
        f.update(cd10_result=pos, cd23_result=pos if ctx.bern(0.3) else neg, bcl2_expression_result=f"positive ({ctx.randint(80, 100)}%)", bcl6_expression_result="positive",
                 ki67_proliferation_index_pct=ctx.randint(10, 40), flow_cytometry_result="Clonal lambda-restricted B-cell population, CD19+ CD20+ CD10+ CD5-")
    elif sub == "mantle cell lymphoma":
        f.update(cd5_result=pos, cyclin_d1_result=pos, sox11_result=pos if ctx.bern(0.9) else neg, cd23_result=neg,
                 ki67_proliferation_index_pct=ctx.randint(15, 70), flow_cytometry_result="Clonal B-cell population, CD19+ CD20 bright, CD5+ CD23- FMC7+")
    else:  # PTCL
        f.update(cd3_result=pos, cd5_result=pos if ctx.bern(0.6) else neg, cd19_result=neg, cd20_result=neg, cd22_result=neg, cd79a_result=neg, pax5_result=neg,
                 cd30_result=pos if ctx.bern(0.35) else neg, alk_result=neg, ki67_proliferation_index_pct=ctx.randint(40, 85), ebv_eber_result=pos if ctx.bern(0.1) else neg,
                 flow_cytometry_result="Aberrant T-cell population, CD3+ CD4+ with loss of CD7")
    return f


def _molecular(ctx, sub):
    if sub == "classical Hodgkin lymphoma":
        return None
    if sub == "DLBCL":
        myc = ctx.bern(0.12); bcl2 = ctx.bern(0.25); bcl6 = ctx.bern(0.2)
        status = "triple-hit" if (myc and bcl2 and bcl6) else ("double-hit" if (myc and (bcl2 or bcl6)) else "negative")
        return dict(molecular_test_method="FISH", myc_rearrangement_result="positive" if myc else "negative", bcl2_rearrangement_result="positive" if bcl2 else "negative",
                    bcl6_rearrangement_result="positive" if bcl6 else "negative", double_hit_triple_hit_status=status,
                    t_14_18_result="positive" if bcl2 else "negative", tp53_aberration_result="TP53 mutation detected" if ctx.bern(0.15) else "not detected",
                    complex_karyotype_yn=None, clonality_test_result="IGH clonal rearrangement detected")
    if sub == "follicular lymphoma":
        return dict(molecular_test_method="FISH", t_14_18_result="positive" if ctx.bern(0.85) else "negative", bcl2_rearrangement_result="positive" if ctx.bern(0.85) else "negative",
                    clonality_test_result="IGH clonal rearrangement detected")
    if sub == "mantle cell lymphoma":
        return dict(molecular_test_method="FISH", t_11_14_result="positive", tp53_aberration_result="TP53 deletion (17p) detected" if ctx.bern(0.2) else "not detected",
                    complex_karyotype_yn=1 if ctx.bern(0.15) else 0, clonality_test_result="IGH clonal rearrangement detected")
    return dict(molecular_test_method="PCR", clonality_test_result="TCR gamma clonal rearrangement detected", alk_result=None)


def _stage_fields(ctx, stage, sub, ecog, wt):
    hl = sub == "classical Hodgkin lymphoma"
    adv = stage in ("III", "IV")
    nodal = {"I": 1, "II": ctx.randint(2, 4), "III": ctx.randint(3, 8), "IV": ctx.randint(3, 10)}[stage]
    bm = stage == "IV" and ctx.bern(0.55 if sub in ("follicular lymphoma", "mantle cell lymphoma") else 0.3)
    if stage == "IV":
        sites = (["bone marrow"] if bm else []) + list({ctx.choice(EXTRANODAL) for _ in range(ctx.randint(1, 2))})
        ex = 1
    elif stage in ("I", "II") and ctx.bern(0.2):
        sites, ex = [ctx.choice(EXTRANODAL)], 1
    else:
        sites, ex = [], 0
    spleen = 1 if (adv and ctx.bern(0.3)) else 0
    b = ctx.bern(0.45 if adv else 0.15)
    fever = sweats = 0; wl = round(ctx.rand(0, 8), 1)
    if b:
        fever, sweats = int(ctx.bern(0.6)), int(ctx.bern(0.6))
        if not (fever or sweats) or ctx.bern(0.4):
            wl = round(ctx.rand(10.5, 20), 1)
        if not (fever or sweats) and wl <= 10:
            fever = 1
    suffix = ("B" if b else "A") + ("E" if ex and stage != "IV" else "") + ("S" if spleen else "")
    thr = 10.0 if hl else 7.5
    bulky = ctx.bern(0.25)
    largest = round(ctx.rand(thr, thr + 6) if bulky else ctx.rand(1.5, thr - 0.5), 1)
    tl = ctx.randint(1, min(6, nodal + len(sites)))
    spd = round(sum(d * d * 0.7 for d in [largest] + [ctx.rand(1.5, largest) for _ in range(tl - 1)]), 1)
    return dict(stage_system="Lugano", ann_arbor_lugano_stage=stage, stage_suffix=suffix, staging_method="PET/CT", nodal_regions_involved_count=nodal,
                extranodal_involvement_yn=ex, extranodal_site_count=len(sites) if ex else 0, extranodal_sites="; ".join(sites) if sites else None,
                spleen_involvement_yn=spleen, bone_marrow_involvement_yn=1 if bm else 0, bone_marrow_involvement_pct=round(ctx.rand(5, 60), 1) if bm else None,
                cns_involvement_yn=0, bulky_disease_yn=1 if bulky else 0, bulky_disease_threshold_cm=thr, largest_lesion_diameter_cm=largest,
                b_symptom_yn=1 if b else 0, unexplained_fever_yn=fever, drenching_night_sweats_yn=sweats, weight_loss_6mo_pct=wl,
                ecog_performance_status=ecog, measurable_disease_yn=1, target_lesion_count=tl, sum_product_diameters=spd)


def _prognostic(ctx, sub, age, labs, ecog, stage, st, ihc, gender):
    ldh_high = labs[3022250] > 250
    adv = stage in ("III", "IV")
    out = {}
    if sub in ("DLBCL", "peripheral T-cell lymphoma"):
        ipi = int(age > 60) + int(ldh_high) + int(ecog >= 2) + int(adv) + int((st["extranodal_site_count"] or 0) > 1)
        out.update(ipi_score=ipi, ipi_risk_group=IPI_GROUP[ipi])
        if age <= 60:
            out["aaipi_score"] = int(ldh_high) + int(ecog >= 2) + int(adv)
        out["nccn_ipi_score"] = min(8, (0 if age <= 40 else 1 if age <= 60 else 2 if age <= 75 else 3) + (0 if not ldh_high else 1 if labs[3022250] <= 750 else 2)
                                    + int(ecog >= 2) + int(adv) + int(st["extranodal_involvement_yn"] == 1))
        if sub == "peripheral T-cell lymphoma":
            out["pit_score"] = int(age > 60) + int(ldh_high) + int(ecog >= 2) + int(st["bone_marrow_involvement_yn"] == 1)
    elif sub == "follicular lymphoma":
        out["flipi_score"] = int(age > 60) + int(adv) + int(labs[3000963] < 12) + int(ldh_high) + int(st["nodal_regions_involved_count"] > 4)
        out["flipi2_score"] = int(age > 60) + int(labs[3000963] < 12) + int(labs[3006315] > 2.2) + int(st["bone_marrow_involvement_yn"] == 1) + int(st["largest_lesion_diameter_cm"] > 6)
    elif sub == "mantle cell lymphoma":
        mipi = round(ctx.rand(4.5, 7.5) + 0.03 * max(0, age - 50), 2)
        out["mipi_score"] = mipi
        base = "low" if mipi < 5.7 else ("intermediate" if mipi < 6.2 else "high")
        ki = ihc.get("ki67_proliferation_index_pct") or 0
        out["mipi_c_risk_group"] = {"low": "low" if ki < 30 else "low-intermediate", "intermediate": "low-intermediate" if ki < 30 else "high-intermediate", "high": "high-intermediate" if ki < 30 else "high"}[base]
    elif sub == "classical Hodgkin lymphoma" and adv:
        out["hodgkin_ips_score"] = min(7, int(labs[3020491] < 4.0) + int(labs[3000963] < 10.5) + int(gender == MALE) + int(age >= 45) + int(stage == "IV")
                                       + int(labs[3010813] >= 15) + int(ctx.bern(0.2)))
    else:
        out["hodgkin_ips_score"] = None
    return out


def _chemo_monitoring(ctx, p, cycle_dates, aid, drugs, ae_p=0.45, fatal_cycle=None):
    """사이클마다 CBC/신장/간기능, 일부 사이클에 이상사례. fatal_cycle 이면 해당 사이클 후 5등급 열성 호중구감소증 -> 사망. 사망 여부 반환."""
    vinc = 1308290 in drugs
    for i, d in enumerate(cycle_dates):
        vid = ctx.visit_on(p, d)
        shifts = {3017732: -1.5 if i > 0 else 0, 3000963: -1.0 if i > 0 else 0}
        ctx.labs(p, d, [3000963, 3010813, 3017732, 3024929, 3016723, 3013721, 3006923], vid=vid, shifts=shifts)
        if fatal_cycle is not None and i == fatal_cycle:
            ae_day = ctx.days(d, ctx.randint(7, 12))
            avid = ctx.visit(p, ae_day, INPATIENT, los=3)
            dd = ctx.days(ae_day, 3)
            ctx.condition(p, ae_day, 4304213, vid=avid)
            ctx.ae(p, ae_day, 4304213, 5, antp_id=aid, vid=avid, action=4, causality=2)
            ctx.drug(p, ae_day, 1301125, 3, vid=avid, freq=1)
            ctx.note(p, ae_day, "Febrile neutropenia with septic shock after chemotherapy; transferred to ICU. Expired despite maximal support.", note_type=32831, note_class=36716177, vid=avid)
            ctx.set_death(p, dd)
            return True
        if i > 0 and ctx.bern(ae_p):
            ae_day = ctx.days(d, ctx.randint(3, 12))
            if p.death_date is not None and ae_day > p.death_date:
                continue
            if len(cycle_dates) > i + 1 and ae_day >= cycle_dates[i + 1]:
                ae_day = ctx.days(cycle_dates[i + 1], -1)
            concepts = [301794, 4304213, 27674, 4166735, 4223659, 439777, 4141062, 4265412, 432791]
            w = [0.25, 0.12, 0.15, 0.15 if vinc else 0.02, 0.1, 0.08, 0.06, 0.05, 0.04]
            tot = sum(w); w = [x / tot for x in w]
            concept = ctx.choice(concepts, p=w)
            lo, hi = CONCEPTS["adverse_events"][concept]["typical_grade"]
            grade = ctx.randint(lo, hi)
            avid = ctx.visit(p, ae_day, ER if grade >= 3 else OUTPATIENT)
            ctx.ae(p, ae_day, concept, grade, antp_id=aid, vid=avid, action=2 if grade >= 3 else 1)
            ctx.condition(p, ae_day, concept, vid=avid)
            if concept in (301794, 4304213):
                ctx.drug(p, ae_day, 1301125, 3, vid=avid, freq=1)
    return False
