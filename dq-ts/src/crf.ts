// 서식(CRF) → 저장 레코드 변환.
//
// v2 에서 병원이 채우는 것은 저장 테이블이 아니라 **서식**이다. 한 서식의 한 행이 여러 저장
// 테이블의 여러 레코드가 된다. 그 규칙은 `spec/v2/crf_forms_v2.yaml` 에 있고, 여기서 그대로 읽어 쓴다.
// 규칙을 코드에 옮겨 적지 않는 이유는, 명세가 바뀌면 변환도 따라 바뀌어야 하기 때문이다.
//
// 서식은 두 종류다.
//   확장 저장  서식 하나가 확장 테이블 하나다. 필드가 그대로 컬럼이 된다(mapping 이 없다).
//   OMOP 투영  한 행이 OMOP 여러 테이블로 흩어진다. mapping 의 anchors 로 기준 레코드를 먼저 만들고,
//             나머지 필드는 target 이 가리키는 자리(MEASUREMENT·OBSERVATION·EPISODE…)에 앉힌다.
import fs from "node:fs";
import path from "node:path";
import { parse } from "yaml";
import { getRoot } from "./load.js";

export interface FieldTarget {
  kind: "skip" | "column" | "attr" | "episode" | "anchor";
  table?: string;
  column?: string;
  concept?: number | string;
  value_column?: string;
  date?: string;
  event_ref?: string;
  event_field?: string;
  unit?: string | null;
  start?: string;
  parent?: string;
  object?: string;
}

export interface FormField { name: string; kor?: string; codelist?: string; target?: FieldTarget }

export interface FormMapping {
  date_field?: string | null;
  attr_default: string;
  anchors: Array<{ table: string; ref?: string | null; columns: Record<string, string> }>;
  links: Array<{ table: string; columns: Record<string, string>; note?: string | null }>;
}

export interface FormSpec {
  name: string; kor: string; grain: string; kind: string;
  storage: string[]; cohorts: string[];
  mapping?: FormMapping | null;
  fields: FormField[];
}

export interface CrfSpec {
  forms: Record<string, FormSpec>;
  /** 씨앗·값 집합 concept: 키(예: TYPE_REGISTRY, CS:CL_BIOPSY_METHOD:CORE) → concept_id */
  conceptByKey: Map<string, number>;
  /** 저장 테이블의 PK 이름 */
  pkOf: Map<string, string>;
  /** 저장 테이블의 전체 컬럼(명세 순서). 변환 결과는 이 컬럼을 다 갖춰야 한다. */
  columnsOf: Map<string, string[]>;
}

export function loadCrfSpec(root = getRoot()): CrfSpec {
  const forms = parse(fs.readFileSync(path.join(root, "spec/v2/crf_forms_v2.yaml"), "utf-8")).forms as Record<string, FormSpec>;
  const conceptByKey = new Map<string, number>();
  const conceptCsv = fs.readFileSync(path.join(root, "spec/v2/vocab/CONCEPT.csv"), "utf-8").split(/\r?\n/);
  const header = conceptCsv[0].replace(/^﻿/, "").split(",");
  const iId = header.indexOf("concept_id");
  for (const line of conceptCsv.slice(1)) {
    if (!line.trim()) continue;
    const cells = line.split(",");
    const key = cells[cells.length - 1];
    if (key) conceptByKey.set(key, Number(cells[iId]));
  }
  const spec = parse(fs.readFileSync(path.join(root, "spec/v2/kai_cdm_spec_v2.yaml"), "utf-8")) as
    { tables: Record<string, { pk: string; fields: Array<{ name: string }> }> };
  const pkOf = new Map(Object.entries(spec.tables).map(([t, v]) => [t, v.pk]));
  const columnsOf = new Map(Object.entries(spec.tables).map(([t, v]) => [t, v.fields.map((f) => f.name)]));
  return { forms, conceptByKey, pkOf, columnsOf };
}

export interface ConvertIssue { form: string; row: number; field?: string; message: string }

export interface ConvertResult {
  /** 테이블 이름 → 만들어진 레코드들 */
  records: Map<string, Array<Record<string, string>>>;
  issues: ConvertIssue[];
}

/** 서식 한 벌(서식명 → 행 목록)을 저장 레코드로 바꾼다. */
export class CrfConverter {
  private readonly spec: CrfSpec;
  private readonly cohort: string;
  private readonly ids = new Map<string, number>();
  private readonly idBase: number;
  readonly issues: ConvertIssue[] = [];
  readonly records = new Map<string, Array<Record<string, string>>>();

  constructor(spec: CrfSpec, cohort: string, idBase = 1) {
    this.spec = spec;
    this.cohort = cohort;
    this.idBase = idBase;
  }

  private nextId(table: string): number {
    const n = (this.ids.get(table) ?? this.idBase - 1) + 1;
    this.ids.set(table, n);
    return n;
  }

  private push(table: string, rec: Record<string, string>): void {
    const list = this.records.get(table) ?? [];
    list.push(rec);
    this.records.set(table, list);
  }

  private concept(key: string): number | undefined {
    return this.spec.conceptByKey.get(key);
  }

  /** 값 집합의 코드를 concept_id 로. 없으면 undefined (원천값만 남긴다). */
  private codeConcept(codelist: string | undefined, code: string): number | undefined {
    if (!codelist) return undefined;
    return this.spec.conceptByKey.get(`CS:${codelist}:${code}`);
  }

  /**
   * 매핑 식을 값으로 바꾼다.
   *   $field      서식의 그 필드 값 ($field:concept 이면 값 집합 코드를 concept_id 로)
   *   @KEY        어휘의 씨앗 concept ({cohort} 는 코호트 이름으로)
   *   #REF        이 행에서 앞서 만든 레코드의 PK
   *   a|b|c       앞에서부터 값이 있는 것
   *   그 밖       글자 그대로
   */
  private value(src: unknown, row: Record<string, string>, form: FormSpec, refs: Map<string, number>): string | undefined {
    if (typeof src !== "string") return src === undefined || src === null ? undefined : String(src);
    if (src.startsWith("#")) {
      const key = src.slice(1).split("(")[0];
      const v = refs.get(key);
      return v === undefined ? `<${src.slice(1)}>` : String(v);
    }
    for (const raw of src.split("|")) {
      const alt = raw.trim();
      if (alt.startsWith("@")) {
        const key = alt.slice(1).replace("{cohort}", this.cohort);
        const v = this.concept(key);
        return v === undefined ? `<${key}>` : String(v);
      }
      if (alt.startsWith("$")) {
        const [fld, mode] = alt.slice(1).split(":");
        const v = row[fld];
        if (v === undefined || v === "") continue;
        if (mode === "concept") {
          const f = form.fields.find((x) => x.name === fld);
          const c = this.codeConcept(f?.codelist, v);
          return c === undefined ? `<concept: ${v}>` : String(c);
        }
        return v;
      }
      return alt;
    }
    return undefined;
  }

  /** 서식 한 행을 레코드들로 바꾼다. */
  convertRow(form: FormSpec, row: Record<string, string>, rowNo: number): void {
    const personId = row["person_id"] ?? "";
    if (!personId) {
      this.issues.push({ form: form.name, row: rowNo, field: "person_id", message: "person_id 가 비어 있어 어느 환자의 기록인지 알 수 없습니다" });
      return;
    }
    // 확장 저장 서식: 필드가 그대로 컬럼이 된다
    if (!form.mapping) {
      const table = form.storage[0] ?? form.name;
      const pk = this.spec.pkOf.get(table);
      const rec: Record<string, string> = {};
      for (const f of form.fields) {
        const t = f.target;
        if (t?.kind !== "column") continue;
        const v = row[f.name];
        if (v === undefined || v === "") continue;
        const col = t.column ?? f.name;
        if (col.endsWith("_concept_id")) {
          // 서식에는 사람이 고른 코드가 들어오고, 저장 컬럼은 concept_id 를 받는다.
          // 원천 코드는 항상 *_source_value 에 남겨 둔다(참조표를 나중에 실어도 되도록).
          const code = this.codeConcept(f.codelist, v);
          if (code === undefined) {
            if (f.codelist) {
              this.issues.push({ form: form.name, row: rowNo, field: f.name, message: `값 '${v}' 이 값 집합 ${f.codelist} 에 없어 원천값으로만 남깁니다` });
            }
          } else {
            rec[col] = String(code);
          }
          rec[col.replace(/_concept_id$/, "_source_value")] = v;
        } else {
          rec[col] = v;
        }
      }
      if (pk && !pk.includes("+") && !rec[pk]) rec[pk] = String(this.nextId(table));
      rec["person_id"] = personId;
      this.push(table, rec);
      return;
    }

    // OMOP 투영 서식
    const M = form.mapping;
    const refs = new Map<string, number>();
    for (const a of M.anchors) {
      const rec: Record<string, string> = {};
      for (const [col, src] of Object.entries(a.columns)) {
        const v = this.value(src, row, form, refs);
        if (v !== undefined && v !== "") rec[col] = v;
      }
      const pk = this.spec.pkOf.get(a.table);
      if (pk && !pk.includes("+")) {
        const id = this.nextId(a.table);
        rec[pk] = String(id);
        if (a.ref) refs.set(a.ref, id);
      }
      this.push(a.table, rec);
    }

    const date = (M.date_field ? row[M.date_field] : "") || row["index_date"] || "";
    for (const f of form.fields) {
      const t = f.target;
      const v = row[f.name];
      if (!t || v === undefined || v === "") continue;
      if (t.kind === "skip" || t.kind === "anchor" || t.kind === "column") continue;

      if (t.kind === "episode") {
        const rec: Record<string, string> = { person_id: personId };
        const concept = typeof t.concept === "string" ? this.concept(t.concept) : t.concept;
        if (concept !== undefined) rec["episode_concept_id"] = String(concept);
        const start = this.value(t.start, row, form, refs);
        if (start) rec["episode_start_date"] = start;
        const parent = t.parent ? this.value(t.parent, row, form, refs) : undefined;
        if (parent) rec["episode_parent_id"] = parent;
        const object = t.object ? this.value(t.object, row, form, refs) : undefined;
        if (object) rec["episode_object_concept_id"] = object;
        const type = this.concept("TYPE_REGISTRY");
        if (type !== undefined) rec["episode_type_concept_id"] = String(type);
        rec["episode_id"] = String(this.nextId("EPISODE"));
        this.push("EPISODE", rec);
        continue;
      }

      // attr: MEASUREMENT 또는 OBSERVATION 한 행
      const table = t.table ?? M.attr_default;
      const c = table === "MEASUREMENT"
        ? { concept: "measurement_concept_id", date: "measurement_date", type: "measurement_type_concept_id", eventId: "measurement_event_id", eventField: "meas_event_field_concept_id", pk: "measurement_id" }
        : { concept: "observation_concept_id", date: "observation_date", type: "observation_type_concept_id", eventId: "observation_event_id", eventField: "obs_event_field_concept_id", pk: "observation_id" };
      const rec: Record<string, string> = { person_id: personId };
      if (t.concept !== undefined) rec[c.concept] = String(t.concept);
      if (date) rec[c.date] = date;
      const type = this.concept("TYPE_REGISTRY");
      if (type !== undefined) rec[c.type] = String(type);

      if (t.value_column === "value_as_concept_id") {
        const code = this.codeConcept(f.codelist, v);
        if (code === undefined) {
          this.issues.push({ form: form.name, row: rowNo, field: f.name, message: `값 '${v}' 이 값 집합 ${f.codelist ?? "(없음)"} 에 없어 원천값으로만 남깁니다` });
        } else {
          rec["value_as_concept_id"] = String(code);
        }
        rec["value_source_value"] = v;
      } else if (t.value_column) {
        rec[t.value_column] = v;
      }
      if (t.unit) {
        const u = this.concept(`UNIT:${t.unit}`);
        if (u !== undefined) rec["unit_concept_id"] = String(u);
      }
      // 이 값이 어느 사건에 딸린 것인지(예: 진단 레코드)
      if (t.event_ref) {
        const ref = t.event_ref.split("|").find((r) => refs.has(r));
        if (ref) {
          rec[c.eventId] = String(refs.get(ref));
          if (t.event_field) {
            const ff = this.concept(t.event_field);
            if (ff !== undefined) rec[c.eventField] = String(ff);
          }
        }
      }
      rec[c.pk] = String(this.nextId(table));
      this.push(table, rec);
    }
  }

  convertForm(form: FormSpec, rows: Array<Record<string, string>>): void {
    rows.forEach((row, i) => this.convertRow(form, row, i + 2)); // 2행부터가 데이터(1행은 머리글)
  }

  result(): ConvertResult {
    return { records: this.records, issues: this.issues };
  }
}

/** 서식 이름 목록 중 이 코호트가 채워야 하는 것 */
export function formsForCohort(spec: CrfSpec, cohort: string): FormSpec[] {
  return Object.values(spec.forms).filter((f) => f.cohorts.includes(cohort));
}

// ---------------------------------------------------------------- 파일 단위
import { readCsv, writeCsv } from "./csv.js";

export interface ConvertDirResult {
  /** 읽은 서식 → 행 수 */
  formsRead: Record<string, number>;
  /** 쓴 저장 테이블 → 레코드 수 */
  tablesWritten: Record<string, number>;
  issues: ConvertIssue[];
  /** 이 코호트가 채워야 하는데 파일이 없는 서식 */
  missingForms: string[];
  /**
   * 어느 서식도 만들지 않는 저장 테이블. 서식은 EHR 에 구조화되어 있지 않은 것을 받는 자리라,
   * 환자·방문·약물·사망처럼 EHR 에서 그대로 뽑는 표는 서식이 아니라 추출본으로 받아야 한다.
   * 이 표들은 변환 결과에 없으므로, 검증할 때 병원의 추출본과 합쳐야 한다.
   */
  tablesFromEhr: string[];
}

/**
 * 서식 CSV 가 든 디렉터리를 읽어 저장 테이블 CSV 로 쓴다.
 * 파일 이름은 서식 이름(예: PATHOLOGY_REPORT.csv)이다. 없는 서식은 건너뛰고 무엇이 없는지 알려준다.
 */
export function convertCrfDirectory(opts: {
  cohort: string; inDir: string; outDir: string; root?: string; idBase?: number;
}): ConvertDirResult {
  const spec = loadCrfSpec(opts.root ?? getRoot());
  const conv = new CrfConverter(spec, opts.cohort, opts.idBase ?? 1);
  const formsRead: Record<string, number> = {};
  const missingForms: string[] = [];
  for (const form of formsForCohort(spec, opts.cohort)) {
    const p = path.join(opts.inDir, `${form.name}.csv`);
    if (!fs.existsSync(p)) { missingForms.push(form.name); continue; }
    const df = readCsv(p);
    const rows: Array<Record<string, string>> = [];
    for (let i = 0; i < df.n; i++) {
      const row: Record<string, string> = {};
      for (const c of df.columns) row[c] = df.cols.get(c)![i];
      rows.push(row);
    }
    conv.convertForm(form, rows);
    formsRead[form.name] = rows.length;
  }
  fs.mkdirSync(opts.outDir, { recursive: true });
  const { records, issues } = conv.result();
  const tablesWritten: Record<string, number> = {};
  for (const [table, recs] of records) {
    // 명세의 컬럼을 모두 쓴다. 값이 없는 컬럼도 빈 칸으로 둬야 '컬럼 구성' 검사를 지난다.
    const cols = spec.columnsOf.get(table) ?? [];
    const extra: string[] = [];
    for (const r of recs) for (const k of Object.keys(r)) if (!cols.includes(k) && !extra.includes(k)) extra.push(k);
    if (extra.length) {
      conv.issues.push({ form: "(변환)", row: 0, message: `${table} 에 명세에 없는 컬럼이 생겼습니다: ${extra.join(", ")}` });
    }
    writeCsv(path.join(opts.outDir, `${table}.csv`), [...cols, ...extra], recs);
    tablesWritten[table] = recs.length;
  }
  // 이 코호트에 필요한 표 가운데 어느 서식도 만들지 않는 것
  const profiles = parse(fs.readFileSync(path.join(opts.root ?? getRoot(), "spec/v2/cohort_profiles_v2.yaml"), "utf-8"))
    .cohorts as Record<string, { omop_tables: string[]; extension_tables: string[] }>;
  const needed = new Set([...(profiles[opts.cohort]?.omop_tables ?? []), ...(profiles[opts.cohort]?.extension_tables ?? [])]);
  const producible = new Set<string>();
  for (const form of formsForCohort(spec, opts.cohort)) {
    for (const t of form.storage) producible.add(t);
    for (const f of form.fields) if (f.target?.table) producible.add(f.target.table);
  }
  const tablesFromEhr = [...needed].filter((t) => !producible.has(t)).sort();
  return { formsRead, tablesWritten, issues, missingForms, tablesFromEhr };
}

/**
 * 병원이 채울 빈 서식(CSV)을 만든다. 서식마다 파일 하나이고 첫 줄이 필드 이름이다.
 * 값을 고르는 필드에는 고를 수 있는 코드를 README 에 함께 적는다 — 코드를 모르면 채울 수 없기 때문이다.
 */
export function writeCrfTemplates(cohort: string, dir: string, root = getRoot()): string[] {
  const spec = loadCrfSpec(root);
  const forms = formsForCohort(spec, cohort);
  fs.mkdirSync(dir, { recursive: true });
  const written: string[] = [];
  // 값 집합 코드 목록 (CS:<집합>:<코드> 키에서 모은다)
  const codesOf = new Map<string, string[]>();
  for (const key of spec.conceptByKey.keys()) {
    if (!key.startsWith("CS:")) continue;
    const [, set, code] = key.split(":");
    if (!code) continue;
    const list = codesOf.get(set) ?? [];
    list.push(code);
    codesOf.set(set, list);
  }

  const guide: string[] = [
    `K-AI 코호트 입력 양식 — ${cohort} (서식 ${forms.length}개)`, "",
    "- 파일 하나가 서식 하나입니다. 파일 이름은 바꾸지 마세요.",
    "- 첫 줄은 필드 이름입니다. 순서는 바꿔도 되지만 이름은 바꾸지 마세요.",
    "- 인코딩 UTF-8, 빈 값은 빈 칸, 날짜는 YYYY-MM-DD 입니다.",
    "- person_id 는 모든 서식에 있어야 합니다. 같은 환자는 같은 값을 쓰세요.",
    "- 값을 고르는 필드는 아래 목록의 코드를 그대로 적습니다(한글 라벨이 아니라 코드).",
    "",
  ];
  for (const form of forms) {
    const fields = form.fields.filter((f) => f.target?.kind !== "skip" || f.name === "person_id");
    const p = path.join(dir, `${form.name}.csv`);
    fs.writeFileSync(p, "﻿" + fields.map((f) => f.name).join(",") + "\n", "utf-8");
    written.push(p);
    guide.push(`[${form.name}] ${form.kor} · 행 단위: ${form.grain}`);
    for (const f of fields) {
      if (!f.codelist) continue;
      const codes = codesOf.get(f.codelist) ?? [];
      guide.push(`   ${f.name} (${f.kor ?? ""}) : ${codes.length ? codes.join(" | ") : "(값 집합이 아직 비어 있습니다)"}`);
    }
    guide.push("");
  }
  fs.writeFileSync(path.join(dir, "README.txt"), guide.join("\n"), "utf-8");
  return written;
}
