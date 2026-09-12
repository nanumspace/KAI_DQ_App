# -*- coding: utf-8 -*-
"""사전 v2.1 · 값 집합(코드표) 채우기 + K-AI 어휘 표준 매핑.

배치표(1단계)에서 만든 62개 빈 값 집합에 실제 값을 채운다. 두 가지 원천을 쓴다.
  - LOINC: 로컬 파일(/Users/min/Research/standard_terminology/LOINC/Loinc_2.80/LoincTableCore/LoincTableCore.csv)에서
    grep 으로 직접 확인한 코드만 LOINC_CODES/PFT_ITEMS/ALCOHOL_ITEMS 에 넣었다.
  - SNOMED CT: MCP 용어 서버로 확인해야 한다. 이 파일을 만든 시점에는 서버가 연결되지 않아
    VALUE_SETS 의 값에는 SNOMED 코드가 없다(전부 vocabulary=KAI). SNOMED_CODES 딕셔너리에
    (코드표, 코드) → concept_id 형태로 채우면 build_spec_v2.py 가 그 값만 SNOMED 로 승격한다.
    다음 세션에서 SNOMED MCP 로 채울 항목은 spec/v2/spec_v2_report.md 의 "SNOMED 확인 대기" 절에 나열된다.

값의 임상 근거는 각 절 주석에 표기했다(AJCC 8판, WHO/ICC, RECIST 1.1, Lugano/Cheson, ITBCC 2016, MERCURY, EASL-EASD-EASO 2023 MASLD 등).
팀 검토 후 코드·라벨을 바꾸려면 이 파일만 고치고 build_spec_v2.py 를 다시 실행한다.
"""

# ================================================================ 값 집합(코드표): codelist_id -> [(code, ko, en), ...]
VALUE_SETS = {
    # ---------------- 병리·검체 공통
    "CL_BIOPSY_METHOD": [
        ("CORE", "코어 생검(총생검)", "Core needle biopsy"), ("FNA", "세침흡인검사", "Fine needle aspiration"),
        ("EXCISION", "절제생검", "Excisional biopsy"), ("INCISION", "절개생검", "Incisional biopsy"),
        ("PUNCH", "펀치생검", "Punch biopsy"), ("ENDOSCOPIC", "내시경 생검", "Endoscopic biopsy"),
        ("EBUS", "기관지초음파 세침흡인(EBUS-TBNA)", "EBUS-guided transbronchial needle aspiration"),
        ("IMAGE_GUIDED", "영상유도 생검(CT/US)", "Image-guided (CT/US) biopsy"),
        ("VACUUM", "진공보조 생검", "Vacuum-assisted biopsy"), ("SURGICAL", "수술적 생검", "Surgical biopsy"), ("OTHER", "기타", "Other"),
    ],
    "CL_BIOPSY_ADEQUACY": [
        ("ADEQUATE", "적정", "Adequate"), ("INADEQUATE", "부적정·검체 부족", "Inadequate/insufficient"), ("NONDIAGNOSTIC", "비진단적", "Non-diagnostic"),
    ],
    "CL_BIOPSY_DIFFERENTIATION": [  # WHO 등급 (조직학적 분화도)
        ("WD", "고분화(Grade 1)", "Well differentiated (G1)"), ("MD", "중분화(Grade 2)", "Moderately differentiated (G2)"),
        ("PD", "저분화(Grade 3)", "Poorly differentiated (G3)"), ("UD", "미분화·역형성(Grade 4)", "Undifferentiated/anaplastic (G4)"),
        ("GX", "평가 불가", "Not assessable (GX)"),
    ],
    "CL_SURGICAL_HISTOLOGIC_GRADE": [
        ("G1", "Grade 1 (고분화)", "Grade 1 (well differentiated)"), ("G2", "Grade 2 (중분화)", "Grade 2 (moderately differentiated)"),
        ("G3", "Grade 3 (저분화)", "Grade 3 (poorly differentiated)"), ("G4", "Grade 4 (미분화)", "Grade 4 (undifferentiated)"), ("GX", "평가 불가", "Not assessable"),
    ],
    "CL_BIOPSY_LATERALITY": [("RIGHT", "우측", "Right"), ("LEFT", "좌측", "Left"), ("BILATERAL", "양측", "Bilateral"), ("NA", "해당없음", "Not applicable")],
    "CL_SURGICAL_SPECIMEN_LATERALITY": [("RIGHT", "우측", "Right"), ("LEFT", "좌측", "Left"), ("BILATERAL", "양측", "Bilateral"), ("NA", "해당없음(정중)", "Not applicable/midline")],
    "CL_BIOPSY_SITE": [  # 원발/국소/원격 구분 (일반)
        ("PRIMARY", "원발 부위", "Primary tumor site"), ("REGIONAL_NODE", "국소 림프절", "Regional lymph node"),
        ("DISTANT", "원격 전이 부위", "Distant metastatic site"), ("OTHER", "기타(직접 기재)", "Other (specify)"),
    ],
    "CL_SURGICAL_SPECIMEN_SITE": [
        ("PRIMARY", "원발 부위", "Primary tumor site"), ("REGIONAL_NODE", "국소 림프절", "Regional lymph node"),
        ("MARGIN", "절제연", "Resection margin"), ("OTHER", "기타(직접 기재)", "Other (specify)"),
    ],
    "CL_BIOPSY_SITE_DETAIL": [  # 폐엽 + 대장 분절 공용 (질환별로 해당 값만 사용)
        ("RUL", "우상엽", "Right upper lobe"), ("RML", "우중엽", "Right middle lobe"), ("RLL", "우하엽", "Right lower lobe"),
        ("LUL", "좌상엽", "Left upper lobe"), ("LLL", "좌하엽", "Left lower lobe"),
        ("CECUM", "맹장", "Cecum"), ("ASC_COLON", "상행결장", "Ascending colon"), ("HEP_FLEX", "간만곡부", "Hepatic flexure"),
        ("TRANS_COLON", "횡행결장", "Transverse colon"), ("SPL_FLEX", "비만곡부", "Splenic flexure"), ("DESC_COLON", "하행결장", "Descending colon"),
        ("SIGMOID", "S상결장", "Sigmoid colon"), ("RECTUM", "직장", "Rectum"),
    ],
    "CL_GROSS_TYPE": [  # Borrmann 분류 (위장관 종양 육안형)
        ("TYPE1", "제1형(용종형)", "Type 1 (polypoid)"), ("TYPE2", "제2형(경계명확 궤양형)", "Type 2 (fungating/ulcerative, sharp margin)"),
        ("TYPE3", "제3형(침윤성 궤양형)", "Type 3 (ulcerative infiltrative)"), ("TYPE4", "제4형(미만성 침윤형)", "Type 4 (diffusely infiltrative, linitis plastica)"),
        ("TYPE5", "제5형(분류불능)", "Type 5 (unclassifiable)"),
    ],
    "CL_DCIS_NUCLEAR_GRADE": [("LOW", "저등급(Grade 1)", "Low grade (Grade 1)"), ("INTERMEDIATE", "중등도(Grade 2)", "Intermediate grade (Grade 2)"), ("HIGH", "고등급(Grade 3)", "High grade (Grade 3)")],
    "CL_ADENOCARCINOMA_PREDOMINANT_SUBTYPE": [  # IASLC/WHO 폐선암 아형
        ("LEPIDIC", "인설상형(lepidic)", "Lepidic"), ("ACINAR", "선방형(acinar)", "Acinar"), ("PAPILLARY", "유두형(papillary)", "Papillary"),
        ("MICROPAPILLARY", "미세유두형(micropapillary)", "Micropapillary"), ("SOLID", "고형형(solid)", "Solid"),
        ("MUCINOUS", "점액형(invasive mucinous)", "Invasive mucinous"), ("COLLOID", "교질형(colloid)", "Colloid"),
        ("FETAL", "태아형(fetal)", "Fetal"), ("ENTERIC", "장형(enteric)", "Enteric"),
    ],
    "CL_TUMOR_BUDDING_GRADE": [  # ITBCC 2016 consensus (대장암)
        ("BD1", "Bd1(저등급, 0~4개)", "Bd1 - low (0-4 buds)"), ("BD2", "Bd2(중등도, 5~9개)", "Bd2 - intermediate (5-9 buds)"), ("BD3", "Bd3(고등급, ≥10개)", "Bd3 - high (≥10 buds)"),
    ],
    "CL_VPI_GRADE": [  # IASLC 장측흉막침범 등급 (폐암)
        ("PL0", "PL0(침범 없음)", "PL0 - no invasion beyond elastic layer"), ("PL1", "PL1(탄력층 넘어 침범)", "PL1 - invasion beyond elastic layer"),
        ("PL2", "PL2(장측흉막 표면 침범)", "PL2 - invasion to visceral pleural surface"), ("PL3", "PL3(벽측흉막 침범)", "PL3 - invasion into parietal pleura"),
    ],
    "CL_CRM_STATUS": [("NEGATIVE", "음성(>1mm)", "Negative (>1 mm clearance)"), ("POSITIVE", "양성(≤1mm)", "Positive (≤1 mm clearance)"), ("NA", "평가 불가", "Not assessable")],
    "CL_RESECTION_MARGIN_STATUS": [("R0", "R0(음성)", "R0 - margin negative"), ("R1", "R1(현미경적 잔존)", "R1 - microscopic residual"), ("R2", "R2(육안적 잔존)", "R2 - macroscopic residual"), ("RX", "평가 불가", "RX - cannot be assessed")],
    "CL_RESIDUAL_TUMOR_R_CLASS": [("R0", "R0(잔존 없음)", "R0 - no residual tumor"), ("R1", "R1(현미경적 잔존)", "R1 - microscopic residual"), ("R2", "R2(육안적 잔존)", "R2 - macroscopic residual"), ("RX", "평가 불가", "RX - cannot be assessed")],
    "CL_RESECTION_COMPLETENESS": [("CURATIVE", "근치적 절제(R0)", "Curative resection (R0)"), ("NONCURATIVE", "비근치적 절제(R1/R2)", "Non-curative resection (R1/R2)"), ("UNDETERMINED", "미확정", "Undetermined")],
    "CL_TME_QUALITY": [("COMPLETE", "완전(Grade 3)", "Complete (Grade 3)"), ("NEARLY_COMPLETE", "거의 완전(Grade 2)", "Nearly complete (Grade 2)"), ("INCOMPLETE", "불완전(Grade 1)", "Incomplete (Grade 1)")],
    "CL_INVASION_DEPTH": [  # 대장암 벽 침윤 깊이
        ("TIS", "상피내(Tis)", "In situ (Tis)"), ("T1", "점막하층(T1)", "Submucosa (T1)"), ("T2", "고유근층(T2)", "Muscularis propria (T2)"),
        ("T3", "장막하·주위지방(T3)", "Subserosa/pericolic fat (T3)"), ("T4A", "장측복막(T4a)", "Visceral peritoneum (T4a)"), ("T4B", "주위 장기 침범(T4b)", "Adjacent organ invasion (T4b)"),
    ],
    "CL_PERITONEAL_CYTOLOGY_RESULT": [("POSITIVE", "양성", "Positive"), ("NEGATIVE", "음성", "Negative"), ("INDETERMINATE", "판정 불가·미시행", "Indeterminate/not performed")],
    "CL_STOMA_REASON": [
        ("DIVERTING", "전환·보호 장루", "Diverting/protective stoma"), ("OBSTRUCTION", "장폐색", "Obstruction"),
        ("PERFORATION", "천공", "Perforation"), ("LEAK_PREVENTION", "문합부 누출 예방", "Anastomotic leak prevention"),
        ("PERMANENT", "영구 장루(APR 등)", "Permanent stoma (e.g. APR)"), ("OTHER", "기타", "Other"),
    ],
    "CL_ANASTOMOSIS_METHOD": [("STAPLED", "문합기 사용", "Stapled"), ("HAND_SEWN", "수기 봉합", "Hand-sewn"), ("HYBRID", "문합기+수기 병용", "Stapled + hand-sewn hybrid")],
    "CL_IMA_LIGATION_LEVEL": [("HIGH", "고위 결찰(대동맥 기시부)", "High ligation (at aortic origin)"), ("LOW", "저위 결찰(좌결장동맥 원위부)", "Low ligation (distal to left colic artery)")],
    "CL_WATCH_AND_WAIT_STATUS": [
        ("ONGOING", "경과관찰 중", "On active surveillance"), ("REGROWTH", "국소 재성장", "Local regrowth"),
        ("CONVERTED_SURGERY", "수술로 전환", "Converted to surgery"), ("SUSTAINED_CCR", "지속적 임상완전관해", "Sustained clinical complete response"),
    ],
    # ---------------- 영상
    "CL_IMAGING_DIAGNOSTIC_CLASSIFICATION": [  # BI-RADS(유방) 기준. 폐암에 재사용 시 2.2 에서 Lung-RADS 로 분리 검토
        ("0", "0(추가 영상 필요)", "0 - Incomplete, need additional imaging"), ("1", "1(음성)", "1 - Negative"), ("2", "2(양성 소견)", "2 - Benign"),
        ("3", "3(양성 추정)", "3 - Probably benign"), ("4A", "4A(낮은 악성 의심)", "4A - Low suspicion"), ("4B", "4B(중등도 악성 의심)", "4B - Moderate suspicion"),
        ("4C", "4C(높은 악성 의심)", "4C - High suspicion"), ("5", "5(악성 고도 의심)", "5 - Highly suggestive of malignancy"), ("6", "6(조직검사 확인된 악성)", "6 - Known biopsy-proven malignancy"),
    ],
    "CL_NODULE_RADIOLOGIC_TYPE": [("SOLID", "고형(solid)", "Solid"), ("PART_SOLID", "부분고형(part-solid)", "Part-solid"), ("GGN", "간유리음영(pure GGN)", "Pure ground-glass")],
    "CL_MRI_ANTERIOR_PERITONEAL_RELATION": [("ABOVE", "복막반전부 위", "Above peritoneal reflection"), ("AT", "복막반전부", "At peritoneal reflection"), ("BELOW", "복막반전부 아래", "Below peritoneal reflection")],
    "CL_MRI_CIRCUMFERENTIAL_EXTENT": [("LT25", "<25%", "<25%"), ("25_50", "25~50%", "25-50%"), ("50_75", "50~75%", "50-75%"), ("GT75", ">75%", ">75%"), ("CIRC", "전둘레(360°)", "Circumferential (360°)")],
    "CL_MRI_CIRCUMFERENTIAL_LOCATION": [("ANTERIOR", "전방", "Anterior"), ("POSTERIOR", "후방", "Posterior"), ("LEFT_LAT", "좌측방", "Left lateral"), ("RIGHT_LAT", "우측방", "Right lateral"), ("CIRC", "전둘레", "Circumferential")],
    "CL_MRI_T4B_INVADED_ORGAN": [
        ("PROSTATE", "전립선", "Prostate"), ("SEMINAL_VESICLE", "정낭", "Seminal vesicle"), ("VAGINA", "질", "Vagina"), ("UTERUS", "자궁", "Uterus"),
        ("BLADDER", "방광", "Bladder"), ("PELVIC_SIDEWALL", "골반측벽", "Pelvic sidewall"), ("SACRUM", "천골", "Sacrum"), ("OTHER", "기타 인접 장기", "Other adjacent organ"),
    ],
    "CL_MRI_TUMOR_REGRESSION_GRADE": [  # MERCURY mrTRG
        ("MRTRG1", "mrTRG1(완전반응)", "mrTRG1 - complete response"), ("MRTRG2", "mrTRG2", "mrTRG2"), ("MRTRG3", "mrTRG3", "mrTRG3"),
        ("MRTRG4", "mrTRG4", "mrTRG4"), ("MRTRG5", "mrTRG5(반응 없음)", "mrTRG5 - no response"),
    ],
    # ---------------- 진단·병기 공통
    "CL_DIAGNOSIS_STATUS": [("CONFIRMED", "확진", "Confirmed"), ("SUSPECTED", "의증", "Suspected"), ("RECURRENT", "재발성", "Recurrent"), ("EXCLUDED", "배제됨", "Excluded/ruled out")],
    "CL_DIAGNOSIS_SUBTYPE": [  # 대장암 세부 진단명 (WHO 조직학)
        ("ADENO_NOS", "선암종(NOS)", "Adenocarcinoma, NOS"), ("MUCINOUS", "점액성 선암종", "Mucinous adenocarcinoma"),
        ("SIGNET_RING", "인환세포암종", "Signet ring cell carcinoma"), ("NEUROENDOCRINE", "신경내분비암종", "Neuroendocrine carcinoma"),
        ("SCC", "편평상피세포암종", "Squamous cell carcinoma"), ("OTHER", "기타", "Other"),
    ],
    "CL_LOBULAR_INFLAMMATION_GRADE": [("0", "0(없음)", "0 - none"), ("1", "1(경도, <2 병소/배율시야)", "1 - mild (<2 foci/200x field)"), ("2", "2(중등도, 2~4 병소/배율시야)", "2 - moderate (2-4 foci/200x field)"), ("3", "3(중증, >4 병소/배율시야)", "3 - severe (>4 foci/200x field)")],  # NASH CRN
    "CL_BALLOONING_GRADE": [("0", "0(없음)", "0 - none"), ("1", "1(소수)", "1 - few balloon cells"), ("2", "2(다수/현저)", "2 - many/prominent balloon cells")],  # NASH CRN
    "CL_MASLD_DIAGNOSIS_BASIS": [  # 2023 AASLD/EASL MASLD 명명법 합의
        ("BIOPSY", "간생검 확인", "Liver biopsy confirmed"), ("IMAGING", "영상 지방간 소견 + 심장대사 위험인자", "Imaging steatosis + cardiometabolic risk factor"),
        ("LFT_RISK", "간효소 상승 + 위험인자", "Elevated liver enzymes with risk factors"), ("SCORE", "비침습 점수 기반(FIB-4/NFS 등)", "Non-invasive score-based (FIB-4/NFS etc.)"),
    ],
    "CL_LYMPHOMA_CATEGORY": [("HL", "호지킨림프종", "Hodgkin lymphoma"), ("NHL_B", "비호지킨림프종-B세포", "Non-Hodgkin lymphoma, B-cell"), ("NHL_T", "비호지킨림프종-T/NK세포", "Non-Hodgkin lymphoma, T/NK-cell")],
    "CL_CELL_LINEAGE": [("B_CELL", "B세포", "B-cell"), ("T_CELL", "T세포", "T-cell"), ("NK_CELL", "NK세포", "NK-cell"), ("HRS", "호지킨/리드-스턴버그세포", "Hodgkin/Reed-Sternberg cell"), ("UNCERTAIN", "불명확·혼합", "Uncertain/mixed")],
    "CL_HISTOLOGIC_SUBTYPE": [  # WHO/ICC 림프종 아형(대표)
        ("DLBCL", "미만성 거대B세포림프종(DLBCL, NOS)", "Diffuse large B-cell lymphoma, NOS"), ("FL", "여포림프종", "Follicular lymphoma"),
        ("MCL", "외투세포림프종", "Mantle cell lymphoma"), ("MZL", "변연부림프종", "Marginal zone lymphoma"), ("BL", "버킷림프종", "Burkitt lymphoma"),
        ("CHL", "고전적 호지킨림프종", "Classic Hodgkin lymphoma"), ("NLPHL", "결절성 림프구우세형 호지킨림프종", "Nodular lymphocyte-predominant Hodgkin lymphoma"),
        ("PTCL_NOS", "말초T세포림프종(NOS)", "Peripheral T-cell lymphoma, NOS"), ("ALCL", "역형성대세포림프종", "Anaplastic large cell lymphoma"),
        ("NKTCL", "비강형 NK/T세포림프종", "Extranodal NK/T-cell lymphoma, nasal type"), ("OTHER", "기타·미분류", "Other/not otherwise specified"),
    ],
    "CL_PRIMARY_SITE": [("RUL", "우상엽", "Right upper lobe"), ("RML", "우중엽", "Right middle lobe"), ("RLL", "우하엽", "Right lower lobe"), ("LUL", "좌상엽", "Left upper lobe"), ("LLL", "좌하엽", "Left lower lobe"), ("MAIN_BRONCHUS", "주기관지", "Main bronchus"), ("OVERLAPPING", "중복 병변", "Overlapping lesion"), ("UNSPECIFIED", "불명확", "Unspecified")],
    "CL_PRIMARY_SIDEDNESS": [("RIGHT", "우측(맹장~횡행결장)", "Right-sided (cecum to transverse colon)"), ("LEFT", "좌측(비만곡부~S상결장)", "Left-sided (splenic flexure to sigmoid)"), ("RECTUM", "직장", "Rectum"), ("MULTIPLE", "다발성·양측성", "Multiple/synchronous")],
    "CL_PRIMARY_INVOLVED_SITE": [
        ("NODAL", "림프절(말초)", "Nodal, peripheral"), ("MEDIASTINAL", "종격동", "Mediastinal"), ("WALDEYER", "발다이어고리", "Waldeyer's ring"),
        ("EXTRANODAL_GI", "결절외-위장관", "Extranodal - GI tract"), ("EXTRANODAL_SKIN", "결절외-피부", "Extranodal - skin"),
        ("EXTRANODAL_CNS", "결절외-중추신경계", "Extranodal - CNS"), ("EXTRANODAL_BONE", "결절외-골", "Extranodal - bone"), ("EXTRANODAL_OTHER", "결절외-기타", "Extranodal - other"),
    ],
    "CL_CLINICAL_TUMOR_FEATURE": [
        ("PALPABLE", "촉지되는 종괴", "Palpable mass"), ("NONPALPABLE", "비촉지(영상 발견)", "Non-palpable (imaging detected)"),
        ("SKIN_INVOLVEMENT", "피부·흉벽 침범", "Skin/chest wall involvement"), ("INFLAMMATORY", "염증성 소견", "Inflammatory features"),
        ("OBSTRUCTION", "폐색", "Obstruction"), ("PERFORATION", "천공", "Perforation"), ("BLEEDING", "출혈", "Bleeding"), ("INCIDENTAL", "무증상·우연 발견", "Asymptomatic/incidental"),
    ],
    "CL_DISTANT_METASTASIS_SITE": [("LIVER", "간", "Liver"), ("LUNG", "폐", "Lung"), ("BONE", "골", "Bone"), ("BRAIN", "뇌", "Brain"), ("ADRENAL", "부신", "Adrenal gland"), ("PERITONEUM", "복막", "Peritoneum"), ("DISTANT_NODE", "원격 림프절", "Distant lymph node"), ("OTHER", "기타", "Other")],
    "CL_EXTRANODAL_SITES": [("GI", "위장관", "GI tract"), ("BONE_MARROW", "골수", "Bone marrow"), ("CNS", "중추신경계", "CNS"), ("SKIN", "피부", "Skin"), ("LUNG", "폐", "Lung"), ("LIVER", "간", "Liver"), ("BONE", "골", "Bone"), ("TESTIS", "고환", "Testis"), ("OTHER", "기타", "Other")],
    "CL_STAGING_METHOD": [
        ("CLINICAL", "임상적(진찰·영상)", "Clinical (exam/imaging)"), ("PATHOLOGIC", "병리적(수술 후)", "Pathologic (post-surgical)"),
        ("PET_CT", "PET-CT 기반", "PET-CT based"), ("BONE_MARROW", "골수생검 기반", "Bone marrow biopsy-based"), ("COMBINED", "임상+병리 병합", "Combined clinical + pathologic"),
    ],
    # ---------------- 생식·산과 (유방암)
    "CL_CONCEPTION_METHOD": [("NATURAL", "자연 임신", "Natural conception"), ("IVF", "체외수정(IVF)", "In vitro fertilization"), ("IUI", "자궁내 인공수정(IUI)", "Intrauterine insemination"), ("OTHER_ART", "기타 보조생식술", "Other assisted reproduction")],
    "CL_PREGNANCY_OUTCOME": [("LIVE_BIRTH", "출산(생존아)", "Live birth"), ("STILLBIRTH", "사산", "Stillbirth"), ("MISCARRIAGE", "자연유산", "Spontaneous abortion"), ("INDUCED_ABORTION", "인공유산", "Induced abortion"), ("ECTOPIC", "자궁외임신", "Ectopic pregnancy"), ("ONGOING", "임신 중", "Ongoing pregnancy")],
    "CL_FERTILITY_PRESERVATION_TYPE": [("OOCYTE", "난자 동결보존", "Oocyte cryopreservation"), ("EMBRYO", "배아 동결보존", "Embryo cryopreservation"), ("OVARIAN_TISSUE", "난소조직 동결보존", "Ovarian tissue cryopreservation"), ("GNRH_AGONIST", "GnRH 작용제 난소기능 억제", "GnRH agonist ovarian suppression"), ("OTHER", "기타", "Other")],
    "CL_MENOPAUSAL_STATUS_AT_DIAGNOSIS": [("PRE", "폐경 전", "Premenopausal"), ("PERI", "폐경이행기", "Perimenopausal"), ("POST", "폐경 후", "Postmenopausal"), ("UNKNOWN", "미확인", "Unknown/not assessed")],
    "CL_MENSES_REGULARITY_AFTER_CHEMO": [("REGULAR", "규칙적", "Regular"), ("IRREGULAR", "불규칙적", "Irregular"), ("AMENORRHEA", "무월경", "Amenorrhea")],
    "CL_MARITAL_STATUS_DETAIL": [("NEVER_MARRIED", "미혼", "Never married"), ("MARRIED", "기혼", "Married"), ("DIVORCED", "이혼", "Divorced"), ("WIDOWED", "사별", "Widowed"), ("SEPARATED", "별거", "Separated"), ("OTHER", "기타·동거 등", "Cohabiting/other")],
    # ---------------- 이상사례
    "CL_COMPLICATION_TREATMENT": [
        ("OBSERVATION", "보존적 관찰", "Conservative/observation"), ("MEDICAL", "약물 치료", "Medical management"),
        ("ENDOSCOPIC", "내시경적 시술", "Endoscopic intervention"), ("REOPERATION", "재수술", "Reoperation/surgical intervention"), ("DRAINAGE", "경피적 배액", "Percutaneous drainage"),
    ],
    "CL_ACTION_TAKEN_CONCEPT_ID": [  # ICH E2B 조치 범주
        ("NO_CHANGE", "용량 변경 없음", "Dose not changed"), ("REDUCED", "용량 감량", "Dose reduced"), ("INTERRUPTED", "투여 중단(일시)", "Dose interrupted/withheld"),
        ("WITHDRAWN", "투여 영구 중단", "Drug withdrawn permanently"), ("DELAYED", "치료 연기", "Treatment delayed"), ("NA", "해당없음", "Not applicable"),
    ],
    "CL_OUTCOME_CONCEPT_ID": [  # ICH E2B 결과 범주
        ("RECOVERED", "회복", "Recovered/resolved"), ("RECOVERED_SEQUELAE", "후유증 동반 회복", "Recovered with sequelae"),
        ("NOT_RECOVERED", "미회복·진행중", "Not recovered/ongoing"), ("FATAL", "사망", "Fatal"), ("UNKNOWN", "불명", "Unknown"),
    ],
    "CL_ADVERSE_EVENT_TYPE_CONCEPT_ID": [  # 기록 출처 유형 (TYPE_REGISTRY/TYPE_EHR/TYPE_DERIVED 씨앗과 동일한 뜻)
        ("REGISTRY", "등록 서식 입력", "Registry (CRF entry)"), ("EHR", "전자의무기록", "EHR"), ("DERIVED", "파생", "Derived"),
    ],
}
# 예/아니오(is_serious) 는 새 값을 만들지 않고 기존 YN 값 집합을 그대로 가리킨다.
ALIAS_CODELIST = {"CL_IS_SERIOUS": "YN"}

# ================================================================ SNOMED CT 매핑 (MCP 로 확인된 값만)
# key: (codelist_id, code) -> SNOMED concept_id. 이 세션에서는 SNOMED CT 용어 서버 연결이 끊겨 비어 있다.
# 다음 세션에서 mcp SNOMED 도구로 확인 후 채우면 build_spec_v2.py 가 해당 값의 vocabulary 를 KAI -> SNOMED 로 승격한다.
SNOMED_CODES = {
    # 예시(연결 복구 후 다음 형식으로 추가):
    # ("CL_BIOPSY_METHOD", "CORE"): "462092009",
}

# ================================================================ LOINC (로컬 파일에서 grep 으로 확인)
LOINC_SOURCE = "/Users/min/Research/standard_terminology/LOINC/Loinc_2.80/LoincTableCore/LoincTableCore.csv (2.80)"
# 개별 FIELD concept(측정값)에 표준 코드를 부여. key: 필드명 -> (loinc_code, 영문명)
LOINC_FIELD_CODES = {
    "hba1c_percent": ("4548-4", "Hemoglobin A1c/Hemoglobin.total in Blood"),
    "fpg_mg_dl": ("1558-6", "Fasting glucose [Mass/volume] in Serum or Plasma"),
    "random_glucose_mg_dl": ("2345-7", "Glucose [Mass/volume] in Serum or Plasma"),
    "postprandial_glucose_mg_dl": ("1521-4", "Glucose [Mass/volume] in Serum or Plasma --2 hours post meal"),
    "ogtt_2h_glucose_mg_dl": ("1521-4", "Glucose [Mass/volume] in Serum or Plasma --2 hours post meal"),
    "c_peptide_ng_ml": ("1986-9", "C peptide [Mass/volume] in Serum or Plasma"),
    "fasting_insulin_uiu_ml": ("20448-7", "Insulin [Units/volume] in Serum or Plasma"),
    "homa_ir": ("47214-2", "Homeostasis model assessment (HOMA) in Serum or Plasma"),
    "fructosamine_umol_l": ("33805-3", "Fructosamine [Mass/volume] in Serum or Plasma"),
    "gad_antibody_result": ("101233-5", "Glutamate decarboxylase 65 Ab [Presence] in Serum by Immunoblot"),
    "uacr_mg_g": ("14959-1", "Microalbumin/Creatinine [Mass Ratio] in Urine"),
    "ki67_percent": ("29593-1", "Cells.Ki-67 nuclear Ag/Cells in Tissue by Immune stain"),
    "pdl1_result": ("105304-0", "Tumor cells.PD-L1/Viable tumor cells in Tissue by Immune stain"),
}
# PFT_ITEM: 검사 항목 자체가 LOINC 코드를 가리키는 목록(값이 아니라 항목 concept 참조)
PFT_ITEMS = [
    ("FEV1", "1초간노력성호기량(FEV1)", "Volume expired during 1.0 s of forced expiration", "20150-9"),
    ("FVC", "노력성폐활량(FVC)", "Forced vital capacity", "19870-5"),
    ("FEV1_FVC", "FEV1/FVC 비", "FEV1/FVC ratio", "19926-5"),
    ("DLCO", "폐확산능(DLCO)", "Diffusion capacity, carbon monoxide", "19911-7"),
]
# ALCOHOL: 음주 이력 항목도 항목 concept 참조 목록
ALCOHOL_ITEMS = [
    ("AUDIT_TOTAL", "AUDIT 총점", "Total score [AUDIT]", "75624-7"),
    ("DRINKS_PER_DAY", "1일 음주량(잔)", "Alcoholic drinks per day", "74013-4"),
    ("DRINKS_PER_WEEK", "주간 음주량(잔)", "Alcoholic drinks per week", "105992-2"),
]

# ================================================================ 콤보 목록(개별 값이 아니라 표준 개념 참조) — SNOMED/ATC 확인 대기
# COMORBIDITY_SET: 과거력 진단명 목록. SNOMED concept_id 는 MCP 확인 후 채운다(현재 None -> KAI 임시 코드).
COMORBIDITY_ITEMS = [
    ("HTN", "고혈압", "Hypertensive disorder", None), ("T2DM", "제2형 당뇨병", "Type 2 diabetes mellitus", None),
    ("DYSLIPIDEMIA", "이상지질혈증", "Hyperlipidemia", None), ("CVD", "심혈관질환", "Ischemic heart disease", None),
    ("CEREBROVASCULAR", "뇌혈관질환", "Cerebrovascular disease", None), ("CKD", "만성콩팥병", "Chronic kidney disease", None),
    ("PANCREATIC", "췌장질환", "Disorder of pancreas", None), ("HBV", "B형간염", "Chronic viral hepatitis B", None),
    ("HCV", "C형간염", "Chronic viral hepatitis C", None), ("HIV", "HIV 감염", "HIV infection", None),
    ("TB", "결핵", "Tuberculosis", None), ("HEART_DISEASE", "심장질환", "Heart disease", None),
    ("OTHER_RESPIRATORY", "기타 호흡기질환", "Respiratory disorder", None), ("COLORECTAL_DISEASE", "대장 질환", "Disorder of colon", None),
    ("KIDNEY_DISEASE", "신장 질환", "Disorder of kidney", None), ("LIVER_DISEASE", "간질환", "Liver disease", None),
    ("HYPOTHYROIDISM", "갑상선기능저하증", "Hypothyroidism", None), ("BARIATRIC_SURGERY_HX", "비만대사수술 과거력", "History of bariatric surgery", None),
    ("HEREDITARY_CRC", "유전성 대장암", "Hereditary nonpolyposis colorectal cancer", None), ("CANCER_HX", "암 과거력", "History of malignant neoplasm", None),
]
# DRUG_CLASS_SET: 약물 계열. ATC(WHO Anatomical Therapeutic Chemical) 분류는 안정적 국제 표준이라 MCP 없이도 기재 가능.
DRUG_CLASS_ITEMS = [
    ("INSULIN", "인슐린", "Insulin", "A10A"), ("METFORMIN", "메트포르민", "Metformin", "A10BA02"),
    ("SGLT2I", "SGLT2 억제제", "SGLT2 inhibitor", "A10BK"), ("GLP1RA", "GLP-1 수용체 작용제", "GLP-1 receptor agonist", "A10BJ"),
    ("DPP4I", "DPP-4 억제제", "DPP-4 inhibitor", "A10BH"), ("ANTI_CD20", "Anti-CD20 항체", "Anti-CD20 monoclonal antibody", "L01FA"),
    ("ANTHRACYCLINE", "안트라사이클린", "Anthracycline", "L01DB"), ("BTK_INHIBITOR", "BTK 억제제", "BTK inhibitor", "L01EL"),
    ("CHECKPOINT_INHIBITOR", "면역관문억제제", "Immune checkpoint inhibitor", "L01FF"),
]
