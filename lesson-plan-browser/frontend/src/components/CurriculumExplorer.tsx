import {
  useState,
  useEffect,
  useRef,
  useCallback,
  Fragment,
  useMemo,
  startTransition,
  type MouseEvent,
} from 'react';
import {
  getCachedBundle,
  setCachedBundle,
  saveDataPreferred,
} from '../lib/curriculumBundleCache';
import { enrichRichHtmlInlineTitles } from '../utils/enrichRichHtmlTitles';
import { 
  ChevronLeft,
  ChevronRight, 
  ChevronDown, 
  Book, 
  FileText, 
  Languages, 
  Layers, 
  Info,
  Clock,
  Hammer,
  Link,
  BookOpen,
  BookCopy,
} from 'lucide-react';

interface Unit {
  id: string;
  title: string;
  number: number;
}

interface Subject {
  name: string;
  units: Unit[];
}

interface Grade {
  name: string;
  subjects: Subject[];
}

const PREFETCH_ADJACENCY_RADIUS = 2;
const HOVER_PREFETCH_DELAY_MS = 200;
const LAST_LESSON_BY_UNIT_STORAGE_KEY = 'lp_curriculum_last_lesson_by_unit_v1';

function readLastLessonIdForUnit(unitId: string): string | null {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem(LAST_LESSON_BY_UNIT_STORAGE_KEY);
    if (!raw) return null;
    const map = JSON.parse(raw) as unknown;
    if (!map || typeof map !== 'object') return null;
    const id = (map as Record<string, unknown>)[unitId];
    return typeof id === 'string' && id.trim() ? id.trim() : null;
  } catch {
    return null;
  }
}

function writeLastLessonIdForUnit(unitId: string, lessonId: string): void {
  if (typeof localStorage === 'undefined') return;
  try {
    const raw = localStorage.getItem(LAST_LESSON_BY_UNIT_STORAGE_KEY);
    const map: Record<string, string> =
      raw && typeof raw === 'string'
        ? (JSON.parse(raw) as Record<string, string>)
        : {};
    if (typeof map !== 'object' || map === null) return;
    if (map[unitId] === lessonId) return;
    map[unitId] = lessonId;
    localStorage.setItem(LAST_LESSON_BY_UNIT_STORAGE_KEY, JSON.stringify(map));
  } catch {
    /* ignore quota / private mode */
  }
}

function normalizeGradeLabel(raw: string): string {
  const s = (raw || "").trim();
  const m = s.match(/grade\s*(\d+)/i);
  if (m) return `Grade ${m[1]}`;
  return s || "Grade";
}

function normalizeSubjectLabel(raw: string): string {
  const s = (raw || "").trim();
  if (!s) return "Subject";
  if (/^ela$/i.test(s)) return "ELA";
  return s.toUpperCase();
}

/** Grade 2 Science canonical modules use ids like ``Science_2_Mod1_PropertiesOfMatter``. */
function usesModuleNodeLabel(unit: Unit): boolean {
  return /_Mod\d+_/i.test(unit.id);
}

function moduleNumberFromCanonicalUnitId(unitId: string): number | null {
  const m = unitId.match(/_Mod(\d+)_/i);
  if (!m) return null;
  const n = parseInt(m[1], 10);
  return Number.isFinite(n) ? n : null;
}

/** "Module" or "Unit" for explorer copy (TOC heading, overview title, breadcrumbs). */
function explorerCurriculumNodeNoun(unit: Unit | null): "Module" | "Unit" {
  if (unit && usesModuleNodeLabel(unit)) return "Module";
  return "Unit";
}

function normalizeUnitLabel(unit: Unit): string {
  if (usesModuleNodeLabel(unit)) {
    const fromId = moduleNumberFromCanonicalUnitId(unit.id);
    if (fromId != null) return `Module ${fromId}`;
    if (Number.isFinite(unit.number)) return `Module ${unit.number}`;
    const mm = (unit.title || "").match(/\bmodule\s*(\d+)\b/i);
    if (mm) return `Module ${mm[1]}`;
    return "Module";
  }
  if (Number.isFinite(unit.number)) return `Unit ${unit.number}`;
  const m = (unit.title || "").match(/\bunit\s*(\d+)\b/i);
  if (m) return `Unit ${m[1]}`;
  return "Unit";
}

interface Lesson {
  id: string;
  lesson_number: number;
  title: string;
  learning_intentions?: string; // JSON in DB (Teacher-Facing)
  objectives_student?: string; // JSON in DB (Student-Facing)
  mlr?: string;
  purpose?: string;
  daily_instructional_task?: string;
  success_criteria?: string; // (Student-Facing Learning Targets)
  essential_questions?: string;
  procedure?: string; // JSON
  procedure_html?: string;
  materials?: string;
  lesson_narrative?: string;
  narrative_html?: string;
  instructional_resources?: string; // JSON array of {url,label} OR HTML from DOCX ingestion
  standards_structured?: string; // JSON from high-fidelity standards parsing
  /** Unit Summary of Key Learning matrix row (ELA ingest), JSON */
  ela_key_learning_summary?: string;
  /** Per-lesson detailed ELA plan table (ELA ingest), JSON */
  ela_lesson_plan_structured?: string;
  /** Science overview: Learning intention / Success criteria by day label (JSON) */
  science_li_sc_day_structured?: string;
  /** DOCX curriculum-writer lesson number (Science), for multi-module guides */
  science_doc_lesson_number?: number | null;
  source_doc_id?: string;
  source_url?: string;
  ingested_at?: string;
  ingest_run_id?: string;
  ingest_parser_version?: string;
  content_hash?: string;
}

/**
 * Resolve `selected` to an index in `lessons` for prev/next and list highlighting.
 * Unit list and full-lesson payloads can disagree on `id` type (string vs number from JSON/SQLite),
 * so ids are compared as strings; if that fails, a unique `lesson_number` match is used.
 */
function lessonIndexInUnitList(
  lessons: Lesson[],
  selected: { id?: string | number; lesson_number?: number } | null | undefined,
): number {
  if (!lessons.length || !selected) return -1;
  if (selected.id != null && selected.id !== '') {
    const sid = String(selected.id);
    const byId = lessons.findIndex((l) => String(l.id) === sid);
    if (byId >= 0) return byId;
  }
  const num = selected.lesson_number;
  if (num != null && Number.isFinite(Number(num))) {
    const hits = lessons.filter((l) => l.lesson_number === num);
    if (hits.length === 1) {
      return lessons.findIndex((l) => l.lesson_number === num);
    }
  }
  return -1;
}

/** Parsed `ela_key_learning_summary` (see tools/scraper/ela_summary_table.py). */
interface ElaKeyLearningSummaryPayload {
  schema_version?: number;
  learning_intention?: string;
  success_criteria?: string;
  learning_intentions_success_html?: string;
  daily_task_title?: string;
  daily_task_body?: string;
  content_and_strategies?: string;
  standards_mentions?: string[];
}

/** Parsed `ela_lesson_plan_structured` (see tools/scraper/ela_lesson_plan_table.py). */
interface ElaLessonPlanStructuredPayload {
  schema_version?: number;
  lesson_number?: number;
  lesson_title?: string;
  learning_intention_html?: string;
  success_criteria_html?: string;
  njsls_standards_html?: string;
  key_questions_html?: string;
  instructional_routines_assessments_html?: string;
  vocabulary_cell_html?: string;
  instructional_resources_cell_html?: string;
  procedures_preamble_html?: string;
  anticipatory_set_html?: string;
  learning_procedures_html?: string;
  engagement_with_content_html?: string;
  daily_instructional_task_html?: string;
  procedures_full_html?: string;
  differentiation_html?: string;
  addressing_misconceptions_html?: string;
}

/** Parsed `science_li_sc_day_structured` (see tools/scraper/science_lesson_tables.py). */
interface ScienceLiScDayStructuredPayload {
  schema_version?: number;
  source?: string;
  doc_lesson_number?: number;
  segments?: Array<{
    label: string;
    learning_intention_html?: string;
    success_criteria_html?: string;
    /** Summary of Key Learning for this segment (Science); may be empty until ingest extracts it. */
    brief_overview?: string;
    /** Full THE LESSON IN ACTION table HTML for this day band (Science), when scraped. */
    lesson_in_action_html?: string;
    /** Optional four-way split; only present when scraper validation passed. */
    experimental_splits?: {
      opening_html?: string;
      during_html?: string;
      closing_html?: string;
      online_html?: string;
    };
  }>;
}

function parseScienceLiScDayStructured(
  raw: string | null | undefined,
): ScienceLiScDayStructuredPayload | null {
  if (!raw || !String(raw).trim()) return null;
  try {
    const o = JSON.parse(raw) as ScienceLiScDayStructuredPayload;
    if (!o || !Array.isArray(o.segments) || o.segments.length === 0) return null;
    return o;
  } catch {
    return null;
  }
}

/** One row from GET .../bundle `science_day_segments` (relational mirror of JSON segments). */
interface CurriculumScienceDaySegment {
  id: string;
  lesson_id: string;
  segment_index: number;
  day_label: string;
  science_doc_lesson_number?: number | null;
  learning_intention_html?: string | null;
  success_criteria_html?: string | null;
  brief_overview_html?: string | null;
  lesson_in_action_html?: string | null;
  experimental_splits_json?: string | null;
}

function isCurriculumScienceDaySegment(v: unknown): v is CurriculumScienceDaySegment {
  if (!v || typeof v !== 'object') return false;
  const o = v as Record<string, unknown>;
  return (
    typeof o.id === 'string' &&
    typeof o.lesson_id === 'string' &&
    typeof o.segment_index === 'number' &&
    typeof o.day_label === 'string'
  );
}

function sciencePayloadFromBundleSegments(
  rows: CurriculumScienceDaySegment[],
): ScienceLiScDayStructuredPayload | null {
  if (!rows.length) return null;
  const sorted = [...rows].sort((a, b) => a.segment_index - b.segment_index);
  const doc = sorted[0]?.science_doc_lesson_number;
  return {
    schema_version: 2,
    doc_lesson_number:
      doc != null && Number.isFinite(Number(doc)) ? Number(doc) : undefined,
    segments: sorted.map((r) => {
      let experimental_splits:
        | NonNullable<
            NonNullable<ScienceLiScDayStructuredPayload['segments']>[number]['experimental_splits']
          >
        | undefined;
      const raw = r.experimental_splits_json;
      if (raw && String(raw).trim()) {
        try {
          experimental_splits = JSON.parse(String(raw)) as typeof experimental_splits;
        } catch {
          experimental_splits = undefined;
        }
      }
      return {
        label: r.day_label,
        learning_intention_html: r.learning_intention_html ?? undefined,
        success_criteria_html: r.success_criteria_html ?? undefined,
        brief_overview: (r.brief_overview_html || '').trim() || undefined,
        lesson_in_action_html: r.lesson_in_action_html ?? undefined,
        experimental_splits,
      };
    }),
  };
}

function normalizeBundleScienceSegments(raw: unknown): CurriculumScienceDaySegment[] {
  if (!Array.isArray(raw)) return [];
  return raw.filter(isCurriculumScienceDaySegment);
}

/** Grade 2 Science student workbook PDF page from bundle `book_page_extracts`. */
interface CurriculumBookPageExtract {
  id: string;
  lesson_id: string;
  page_number: number;
  body_text: string;
  char_count?: number | null;
  content_sha256?: string | null;
  alignment_confidence: string;
  alignment_ambiguous: number;
  source_pdf_label: string;
  ingest_parser_version: string;
  ingested_at?: string | null;
}

function isCurriculumBookPageExtract(v: unknown): v is CurriculumBookPageExtract {
  if (!v || typeof v !== 'object') return false;
  const o = v as Record<string, unknown>;
  const amb = o.alignment_ambiguous;
  return (
    typeof o.id === 'string' &&
    typeof o.lesson_id === 'string' &&
    typeof o.page_number === 'number' &&
    typeof o.body_text === 'string' &&
    typeof o.source_pdf_label === 'string' &&
    typeof o.ingest_parser_version === 'string' &&
    typeof o.alignment_confidence === 'string' &&
    typeof amb === 'number'
  );
}

function normalizeBookPageExtracts(raw: unknown): CurriculumBookPageExtract[] {
  if (!Array.isArray(raw)) return [];
  return [...raw.filter(isCurriculumBookPageExtract)].sort(
    (a, b) => a.page_number - b.page_number,
  );
}

function shouldRequestGrade2ScienceBookBundle(lessonId: string): boolean {
  return lessonId.startsWith('Science_2_');
}

function curriculumLessonBundleUrl(lessonId: string): string {
  const base = `/api/curriculum/lessons/${encodeURIComponent(lessonId)}/bundle`;
  if (shouldRequestGrade2ScienceBookBundle(lessonId)) {
    return `${base}?include_book_extracts=true&book_extract_max_pages=60`;
  }
  return base;
}

/** Response from GET /api/curriculum/units/{id}/science-day-outline */
interface ScienceUnitDayOutline {
  unit_id: string;
  total_writer_bands: number;
  lessons: Array<{
    lesson_id: string;
    lesson_number: number;
    title: string;
    segments: Array<{ segment_index: number; day_label: string }>;
  }>;
}

function isScienceUnitDayOutline(v: unknown): v is ScienceUnitDayOutline {
  if (!v || typeof v !== 'object') return false;
  const o = v as Record<string, unknown>;
  if (typeof o.unit_id !== 'string' || typeof o.total_writer_bands !== 'number') return false;
  if (!Array.isArray(o.lessons)) return false;
  return true;
}

function buildScienceModuleOutlineDisplay(outline: ScienceUnitDayOutline | null) {
  if (!outline?.lessons?.length) return [];
  let moduleBand = 0;
  return outline.lessons.map((lesson) => ({
    lesson_id: lesson.lesson_id,
    lesson_number: lesson.lesson_number,
    title: lesson.title,
    segmentRows: lesson.segments.map((seg) => {
      moduleBand += 1;
      return {
        key: `${lesson.lesson_id}-${seg.segment_index}`,
        moduleBandNumber: moduleBand,
        dayLabel: seg.day_label,
      };
    }),
  }));
}

interface VocabularyTerm {
  term: string;
  translated_term: string;
  leveled_definitions: any;
}

interface LessonStandardRow {
  code: string;
  description: string | null;
  subject: string | null;
}

interface CachedLessonPayload {
  details: Lesson;
  vocabulary: VocabularyTerm[];
  standards: LessonStandardRow[];
  science_day_segments?: CurriculumScienceDaySegment[];
  book_page_extracts?: CurriculumBookPageExtract[];
  etag?: string | null;
}

interface StandardItem {
  code: string;
  description: string;
}

interface StructuredStandardItem {
  code: string;
  description_lines: string[];
}

interface StructuredStandardsSection {
  panel: "left" | "right";
  section: string;
  items: StructuredStandardItem[];
}

interface ProcedureSection {
  kind: "warmup" | "activity" | "cooldown" | "synthesis" | "other";
  title: string;
  bodyHtml: string;
}

/** Google Doc id from a docs.google.com URL (matches backend `_extract_source_doc_id`). */
function extractGoogleDocIdFromUrl(url: string): string | null {
  const m = url.match(/\/document\/d\/([a-zA-Z0-9_-]+)/);
  return m ? m[1] : null;
}

function SourceUrlOpenRow({
  sourceUrl,
  sourceDocId,
}: {
  sourceUrl: string;
  sourceDocId?: string;
}) {
  const gid =
    (sourceDocId && sourceDocId.trim()) || extractGoogleDocIdFromUrl(sourceUrl) || null;
  const [resolveSource, setResolveSource] = useState<string | null>(null);

  useEffect(() => {
    if (!gid) {
      setResolveSource(null);
      return;
    }
    let cancelled = false;
    fetch(`/api/curriculum/resources/google-id/${encodeURIComponent(gid)}/resolve`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
      .then((data: { source?: string }) => {
        if (!cancelled) setResolveSource(data?.source ?? null);
      })
      .catch(() => {
        if (!cancelled) setResolveSource(null);
      });
    return () => {
      cancelled = true;
    };
  }, [gid]);

  const openPreferred = async (e: MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault();
    // Open a tab synchronously so popup blockers do not drop async opens.
    const popup = window.open("", "_blank");
    if (popup) popup.opener = null;
    const navigatePopup = (url: string) => {
      if (popup) {
        popup.location.href = url;
      } else {
        window.open(url, "_blank", "noopener,noreferrer");
      }
    };
    if (gid) {
      try {
        const r = await fetch(
          `/api/curriculum/resources/google-id/${encodeURIComponent(gid)}/resolve`,
        );
        if (r.ok) {
          const data = (await r.json()) as { url?: string };
          if (data?.url) {
            navigatePopup(data.url);
            return;
          }
        }
      } catch {
        /* fall through to Drive URL */
      }
    }
    navigatePopup(sourceUrl);
  };

  const badgeLabel =
    resolveSource === "local"
      ? "local export"
      : resolveSource === "remote"
        ? "Google Drive (registered)"
        : resolveSource === "remote_inferred"
          ? "Google Drive"
          : null;

  return (
    <div className="break-all">
      <span className="font-semibold text-slate-700">Source URL:</span>{" "}
      <a
        href={sourceUrl}
        target="_blank"
        rel="noopener noreferrer"
        className="text-blue-700 underline"
        onClick={openPreferred}
      >
        {sourceUrl}
      </a>
      {badgeLabel ? (
        <span className="ml-2 inline-block rounded bg-slate-200/80 px-1.5 py-0.5 text-[10px] font-medium text-slate-600">
          Opens: {badgeLabel}
        </span>
      ) : null}
    </div>
  );
}

function splitDescriptionLines(description: string | null): string[] {
  return (description ?? "")
    .split(/\r?\n+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function mergeStructuredStandards(raw: unknown): StructuredStandardsSection[] {
  if (!Array.isArray(raw)) return [];
  const map = new Map<string, StructuredStandardsSection>();
  raw.forEach((entry: any) => {
    const code = String(entry?.code || "").trim();
    let panel: "left" | "right" = entry?.panel === "right" ? "right" : "left";
    let section = String(entry?.section || "Standards").trim();
    const descriptionLines = Array.isArray(entry?.description_lines)
      ? entry.description_lines.map((x: unknown) => String(x).trim()).filter(Boolean)
      : [];
    if (!code) return;

    // Backward-compatible normalization for older parsed rows that used generic section/panel.
    if (!section || section.toLowerCase() === "standards") {
      if (code.startsWith("NJSLS-")) {
        panel = "left";
        section = "New Jersey State Learning Standards";
      } else if (/^MP\d+$/i.test(code)) {
        panel = "left";
        section = "Mathematical Practice Standards";
      } else if (code.startsWith("NCTM-MATH.CONTENT.")) {
        panel = "right";
        section = "National Council of Teachers of Mathematics Content Standards";
      } else if (/^PR\d+$/i.test(code)) {
        panel = "right";
        section = "National Council of Teachers of Mathematics Process Standards";
      }
    }

    const sectionKey = `${panel}__${section}`;
    if (!map.has(sectionKey)) {
      map.set(sectionKey, { panel, section, items: [] });
    }
    map.get(sectionKey)!.items.push({
      code,
      description_lines: descriptionLines,
    });
  });
  return Array.from(map.values());
}

function parseStructuredStandards(raw: string | undefined): StructuredStandardsSection[] {
  const trimmed = (raw ?? "").trim();
  if (!trimmed) return [];
  try {
    const parsed = JSON.parse(trimmed);
    return mergeStructuredStandards(parsed);
  } catch {
    return [];
  }
}

function groupLessonStandards(rows: LessonStandardRow[]): StructuredStandardsSection[] {
  const grouped = {
    nj: [] as StandardItem[],
    mp: [] as StandardItem[],
    nctmContent: [] as StandardItem[],
    nctmProcess: [] as StandardItem[],
  };

  rows.forEach((row) => {
    const code = (row.code ?? "").trim();
    if (!code) return;
    const lines = splitDescriptionLines(row.description);
    const desc = lines.join(" ");

    if (code.startsWith("NJSLS-")) {
      grouped.nj.push({ code, description: desc });
      return;
    }
    if (code.startsWith("NCTM-MATH.CONTENT.")) {
      // Original guides can repeat the same code with different bullets.
      // If extraction merged lines, present each line as its own item.
      if (lines.length > 1) {
        lines.forEach((line) => grouped.nctmContent.push({ code, description: line }));
      } else {
        grouped.nctmContent.push({ code, description: desc });
      }
      return;
    }
    if (/^MP\d+$/i.test(code)) {
      grouped.mp.push({ code, description: desc });
      return;
    }
    if (/^PR\d+$/i.test(code)) {
      grouped.nctmProcess.push({ code, description: desc });
      return;
    }
    grouped.nj.push({ code, description: desc });
  });

  return [
    {
      panel: "left",
      section: "New Jersey State Learning Standards",
      items: grouped.nj.map((i) => ({ code: i.code, description_lines: i.description ? [i.description] : [] })),
    },
    {
      panel: "left",
      section: "Mathematical Practice Standards",
      items: grouped.mp.map((i) => ({ code: i.code, description_lines: i.description ? [i.description] : [] })),
    },
    {
      panel: "right",
      section: "National Council of Teachers of Mathematics Content Standards",
      items: grouped.nctmContent.map((i) => ({ code: i.code, description_lines: i.description ? [i.description] : [] })),
    },
    {
      panel: "right",
      section: "National Council of Teachers of Mathematics Process Standards",
      items: grouped.nctmProcess.map((i) => ({ code: i.code, description_lines: i.description ? [i.description] : [] })),
    },
  ];
}

function parseProcedureHeading(text: string): {
  kind: ProcedureSection["kind"];
  title: string;
} | null {
  const t = text.trim();
  if (!t) return null;
  if (/^warm-?up\s*:/i.test(t)) return { kind: "warmup", title: t };
  if (/^activity\s+\d+\s*:/i.test(t)) return { kind: "activity", title: t };
  if (/^cool-?down\b/i.test(t)) return { kind: "cooldown", title: t };
  if (/^lesson synthesis\b/i.test(t)) return { kind: "synthesis", title: t };
  return null;
}

function splitProcedureSectionsFromHtml(html: string | undefined): ProcedureSection[] {
  const raw = (html ?? "").trim();
  if (!raw || typeof window === "undefined") return [];
  const root = document.createElement("div");
  root.innerHTML = raw;
  const sections: ProcedureSection[] = [];
  let current: ProcedureSection | null = null;

  Array.from(root.childNodes).forEach((node) => {
    const asElement = node.nodeType === Node.ELEMENT_NODE ? (node as HTMLElement) : null;
    const text = (asElement?.textContent ?? node.textContent ?? "").trim();
    const heading = parseProcedureHeading(text);

    if (heading) {
      current = {
        kind: heading.kind,
        title: heading.title,
        bodyHtml: "",
      };
      sections.push(current);
      return;
    }

    if (!current) {
      current = {
        kind: "other",
        title: "Lesson Segment",
        bodyHtml: "",
      };
      sections.push(current);
    }

    if (asElement) {
      current.bodyHtml += asElement.outerHTML;
    } else if (text) {
      current.bodyHtml += `<p>${text}</p>`;
    }
  });

  return sections.filter((s) => s.title.trim() || s.bodyHtml.trim());
}

function lessonFieldHtmlFromJsonOrHtml(
  raw: string | undefined,
  emptyFallback: string,
): string {
  const trimmed = (raw ?? "").trim();
  if (!trimmed) {
    return `<p>${emptyFallback}</p>`;
  }
  try {
    const parsed = JSON.parse(trimmed);
    if (Array.isArray(parsed) && parsed.length > 0) {
      const inner = parsed.map((i: unknown) => `<li>${String(i)}</li>`).join("");
      return `<ul>${inner}</ul>`;
    }
  } catch {
    /* stored as HTML or plain text */
  }
  if (trimmed.startsWith("<")) {
    return trimmed;
  }
  if (trimmed) {
    return trimmed.includes("<") ? trimmed : `<p>${trimmed}</p>`;
  }
  return `<p>${emptyFallback}</p>`;
}

function parseElaKeyLearningSummary(
  raw: string | undefined | null,
): ElaKeyLearningSummaryPayload | null {
  const trimmed = (raw ?? "").trim();
  if (!trimmed) return null;
  try {
    const o = JSON.parse(trimmed) as unknown;
    if (!o || typeof o !== "object") return null;
    return o as ElaKeyLearningSummaryPayload;
  } catch {
    return null;
  }
}

function parseElaLessonPlanStructured(
  raw: string | undefined | null,
): ElaLessonPlanStructuredPayload | null {
  const trimmed = (raw ?? "").trim();
  if (!trimmed) return null;
  try {
    const o = JSON.parse(trimmed) as unknown;
    if (!o || typeof o !== "object") return null;
    return o as ElaLessonPlanStructuredPayload;
  } catch {
    return null;
  }
}

function elaPlanHasProcedureBuckets(plan: ElaLessonPlanStructuredPayload): boolean {
  const keys: (keyof ElaLessonPlanStructuredPayload)[] = [
    "anticipatory_set_html",
    "learning_procedures_html",
    "engagement_with_content_html",
    "daily_instructional_task_html",
    "procedures_preamble_html",
    "procedures_full_html",
  ];
  return keys.some((k) => {
    const v = plan[k];
    return typeof v === "string" && v.trim().length > 0;
  });
}

function elaPlanIsPrimaryUi(plan: ElaLessonPlanStructuredPayload | null): boolean {
  if (!plan) return false;
  if (
    (plan.learning_intention_html ?? "").trim() ||
    (plan.success_criteria_html ?? "").trim() ||
    (plan.njsls_standards_html ?? "").trim()
  ) {
    return true;
  }
  return elaPlanHasProcedureBuckets(plan);
}

function studentObjectivesHtml(
  raw: string | undefined,
  successCriteria: string | undefined,
  emptyFallback: string,
): string {
  const trimmed = (raw ?? "").trim();
  const sc = (successCriteria ?? "").trim();
  if (!trimmed && !sc) {
    return `<p>${emptyFallback}</p>`;
  }
  try {
    const parsed = JSON.parse(trimmed || "[]");
    if (Array.isArray(parsed) && parsed.length > 0) {
      const inner = parsed.map((i: unknown) => `<li>${String(i)}</li>`).join("");
      return `<ul>${inner}</ul>`;
    }
  } catch {
    /* not JSON */
  }
  if (trimmed.startsWith("<")) {
    return trimmed;
  }
  if (trimmed) {
    return trimmed.includes("<") ? trimmed : `<p>${trimmed}</p>`;
  }
  if (sc) {
    return sc.includes("<") ? sc : `<p>${sc}</p>`;
  }
  return `<p>${emptyFallback}</p>`;
}

/**
 * Renders trusted curriculum HTML and ensures http(s) links open in a new tab
 * so the explorer stays on the lesson (covers older rows without target="_blank").
 */
function CurriculumRichHtml({
  html,
  className,
}: {
  html: string | undefined | null;
  className?: string;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const safe = useMemo(() => enrichRichHtmlInlineTitles(html ?? ''), [html]);

  useEffect(() => {
    const root = ref.current;
    if (!root) return;

    const onClickCapture = (ev: Event) => {
      const el = ev.target as HTMLElement | null;
      const a = el?.closest?.('a[href]') as HTMLAnchorElement | null;
      if (!a) return;
      const href = (a.getAttribute('href') || '').trim();
      if (!href || href.startsWith('#')) return;
      const fromAttr = (a.getAttribute('data-resource-id') || '').trim();
      // Only intercept links explicitly annotated by ingest with a stable resource id.
      // Unannotated links fall back to native anchor behavior (target=_blank).
      if (!fromAttr) return;
      const gid = fromAttr;
      /* Resolve local export for any Google Doc link, not only anchors with data-resource-id (ingest varies). */
      if (!href.includes('docs.google.com/document')) return;

      ev.preventDefault();
      ev.stopPropagation();
      // Open a tab in the click gesture to avoid popup blocking on async resolve.
      const popup = window.open("", "_blank");
      if (popup) popup.opener = null;
      const navigatePopup = (url: string) => {
        if (popup) {
          popup.location.href = url;
        } else {
          window.open(url, '_blank', 'noopener,noreferrer');
        }
      };
      const enc = encodeURIComponent(gid);
      fetch(`/api/curriculum/resources/google-id/${enc}/resolve`)
        .then((r) => (r.ok ? r.json() : Promise.reject(new Error(String(r.status)))))
        .then((data: { url?: string }) => {
          if (data?.url) navigatePopup(data.url);
          else navigatePopup(href);
        })
        .catch(() => {
          navigatePopup(href);
        });
    };

    root.addEventListener('click', onClickCapture, true);
    root.querySelectorAll('a[href]').forEach((node) => {
      const a = node as HTMLAnchorElement;
      const href = a.getAttribute('href');
      if (!href || href.startsWith('#')) return;
      if (/^https?:\/\//i.test(href) || href.startsWith('//')) {
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
      }
    });
    return () => root.removeEventListener('click', onClickCapture, true);
  }, [safe]);

  if (!safe) return null;

  return (
    <div
      ref={ref}
      className={className}
      dangerouslySetInnerHTML={{ __html: safe }}
    />
  );
}

/** Strip tags but keep line breaks from block-level HTML (for LI/SC split fallback). */
function htmlToPlainWithLineBreaks(html: string): string {
  return html
    .replace(/<br\s*\/?>/gi, "\n")
    .replace(/<\/p>\s*/gi, "\n")
    .replace(/<\/div>\s*/gi, "\n")
    .replace(/<\/tr>\s*/gi, "\n")
    .replace(/<[^>]+>/g, "")
    .replace(/\r\n/g, "\n")
    .replace(/\n{3,}/g, "\n\n")
    .trim();
}

/**
 * For LI/SC cells: if ingest didn't preserve list markup, promote topic-like
 * multi-line content into bullets for readability.
 */
function normalizeLiScTopicsToBulletsHtml(html: string | undefined): string | undefined {
  const raw = (html ?? "").trim();
  if (!raw) return html;
  // Respect existing list markup from ingest.
  if (/<(ul|ol|li)\b/i.test(raw)) return raw;

  const plain = htmlToPlainWithLineBreaks(raw);
  if (!plain) return raw;

  // Split on line breaks first; if still one line, allow semicolon-delimited topics.
  let topics = plain
    .split(/\r?\n+/)
    .map((s) => s.trim())
    .filter(Boolean);
  if (topics.length <= 1 && plain.includes(";")) {
    topics = plain
      .split(/\s*;\s*/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  // Keep single-line prose as paragraph; bullet only real topic collections.
  if (topics.length <= 1) return raw;

  const li = topics
    .map((t) => t.replace(/^\s*[-*•]\s*/, "").trim())
    .filter(Boolean)
    .map((t) => `<li>${t}</li>`)
    .join("");
  if (!li) return raw;
  return `<ul>${li}</ul>`;
}

/** Strip BOM/zero-width and wrapping quotes so filters match ingest-normalized labels. */
function normalizeVocabLabelNoise(t: string): string {
  let s = t.trim().replace(/^\ufeff|\u200b|\u200c|\u200d/g, "");
  s = s.replace(/^["'\u201c\u201d\u2018\u2019]+|["'\u201c\u201d\u2018\u2019]+$/g, "").trim();
  return s;
}

const JUNK_VOCAB_EXACT_LOW = new Set([
  "materials",
  "storytelling",
  "editing",
  "cultural meaning",
]);

/** Filter link titles and resource labels mistaken for vocabulary during ingest. */
function isLikelyJunkVocabLabel(t: string): boolean {
  const s = normalizeVocabLabelNoise(t);
  if (s.length < 2 || s.length > 48) return true;
  if (/https?:\/\//i.test(s)) return true;
  const low = s.toLowerCase();
  if (JUNK_VOCAB_EXACT_LOW.has(low)) return true;
  if (low.includes("and techniques")) return true;
  const junkNeedles = [
    "rubric",
    "slide deck",
    "screencast",
    ".pptx",
    "vocabulary boxes",
    "notice/wonder",
    "notice and wonder",
    "preview chart",
    "instructional resources",
    "primary source",
    "partner discussion",
    "discussion rubric",
    "questions",
    " video",
    "video",
    "read aloud",
    "google.com",
    "docs.google",
    "presentation",
    "culminating task",
    "portfolio artifact",
    "daily instructional",
    "anticipatory set",
    "engagement with the content",
    "learning procedures",
    "addressing misconceptions",
    "differentiation",
  ];
  if (junkNeedles.some((n) => low.includes(n))) return true;
  const wordCount = (s.match(/\s+/g) || []).length + 1;
  if (wordCount > 6) return true;
  const instructionalPrefixes = [
    "article:",
    "students will",
    "student will",
    "think about",
    "work with",
    "cite evidence",
    "include:",
    "share as",
    "revisit essential",
    "identify key",
    "clearly compare",
    "comparing and contrasting",
    "how are they",
    "what role",
    "who is responsible",
    "a body with",
    "a conclusion",
    "an introduction",
    "first draft",
    "publish final",
    "or independently",
    "support as",
    "or review",
    "editing and revising",
    "if students",
    "if working",
    "use correct",
    "launch the lesson",
    "for the daily",
    "the teacher",
    "in their writing",
    "notebook",
    "unit 1 ",
    "unit 2 ",
    "and ",
    "correct spelling",
  ];
  if (instructionalPrefixes.some((p) => low.startsWith(p))) return true;
  const st = s.trim();
  if (st.endsWith(")") && !st.includes("(")) return true;
  return false;
}

/**
 * Parse comma-/semicolon-separated vocabulary from the ELA structured plan vocabulary cell
 * (e.g. "Vocabulary: Constitution, protest, representatives").
 */
function extractElaVocabularyTermsFromStructuredCell(
  html: string | undefined | null,
): string[] {
  const raw = (html ?? "").trim();
  if (!raw) return [];
  const plain = htmlToPlainWithLineBreaks(raw).replace(/\s+/g, " ").trim();
  let segment = plain;
  const vi = plain.search(/\bvocabulary\s*:/i);
  if (vi !== -1) {
    segment = plain.slice(vi).replace(/^\s*vocabulary\s*:\s*/i, "").trim();
  }
  const parts = segment
    .split(/[,;\n]+/)
    .map((p) => normalizeVocabLabelNoise(p.replace(/\s*[.,;:]+$/g, "")))
    .filter(Boolean);
  const out: string[] = [];
  const seen = new Set<string>();
  for (const p of parts) {
    if (isLikelyJunkVocabLabel(p)) continue;
    const key = p.toLowerCase();
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(p);
  }
  return out;
}

type LearningIntentionSuccessDisplay =
  | { kind: "blocks"; li: string; sc: string }
  | { kind: "html"; html: string };

/** Match source matrix: bold labels and separate blocks for Learning Intention vs Success Criteria. */
function resolveLearningIntentionSuccessDisplay(
  summary: ElaKeyLearningSummaryPayload,
): LearningIntentionSuccessDisplay | null {
  const htmlRaw = (summary.learning_intentions_success_html ?? "").trim();
  const liPlain = (summary.learning_intention ?? "").trim();
  const scPlain = (summary.success_criteria ?? "").trim();

  /* Prefer column B HTML when ingest preserved structure (lists, bold, links); plain fields are a lossy split. */
  if (htmlRaw && /<(p|ul|ol|li|b|strong|a|span|br|table)\b/i.test(htmlRaw)) {
    return { kind: "html", html: htmlRaw };
  }

  if (liPlain || scPlain) {
    return { kind: "blocks", li: liPlain, sc: scPlain };
  }

  if (!htmlRaw) return null;

  const plain = htmlToPlainWithLineBreaks(htmlRaw);
  const idx = plain.search(/\bSuccess\s+Criteria\s*:/i);
  if (idx !== -1) {
    let before = plain.slice(0, idx).trim();
    let after = plain.slice(idx).trim();
    before = before.replace(/^\s*Learning\s+Intentions?\s*:\s*/i, "").trim();
    after = after.replace(/^\s*Success\s+Criteria\s*:\s*/i, "").trim();
    if (before || after) {
      return { kind: "blocks", li: before, sc: after };
    }
  }

  return { kind: "html", html: htmlRaw };
}

function ElaRichBlock({
  title,
  html,
  titleClassName,
}: {
  title: string;
  html: string | undefined;
  titleClassName?: string;
}) {
  const h = (html ?? "").trim();
  if (!h) return null;
  return (
    <section className="space-y-3">
      <h4
        className={
          titleClassName ??
          "text-sm font-semibold text-teal-800 border-b border-teal-200/80 pb-1"
        }
      >
        {title}
      </h4>
      <CurriculumRichHtml
        className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
        html={h}
      />
    </section>
  );
}

function ElaKeyLearningSection({ summary }: { summary: ElaKeyLearningSummaryPayload }) {
  const hasMatrixText =
    (summary.learning_intention ?? "").trim() ||
    (summary.success_criteria ?? "").trim() ||
    (summary.daily_task_title ?? "").trim() ||
    (summary.daily_task_body ?? "").trim() ||
    (summary.content_and_strategies ?? "").trim() ||
    (summary.learning_intentions_success_html ?? "").trim() ||
    (summary.standards_mentions?.length ?? 0) > 0;
  if (!hasMatrixText) return null;
  return (
    <section className="space-y-4 rounded-xl border border-teal-200/70 bg-teal-50/25 p-5">
      <h3 className="flex items-center gap-2 font-bold text-lg text-teal-800">
        <BookOpen className="w-5 h-5" />
        Summary of Key Learning (unit matrix)
      </h3>
      {(() => {
        const liScDisp = resolveLearningIntentionSuccessDisplay(summary);
        if (!liScDisp) return null;
        if (liScDisp.kind === "blocks") {
          return (
            <div className="space-y-4">
              <h4 className="text-sm font-semibold text-teal-800 border-b border-teal-200/80 pb-1">
                Learning intentions and success criteria
              </h4>
              {liScDisp.li ? (
                <div className="space-y-1.5">
                  <p className="text-sm font-semibold text-foreground">Learning Intention:</p>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                    {liScDisp.li}
                  </p>
                </div>
              ) : null}
              {liScDisp.sc ? (
                <div
                  className={`space-y-1.5 ${liScDisp.li ? "mt-5 pt-4 border-t border-teal-200/60" : ""}`}
                >
                  <p className="text-sm font-semibold text-foreground">Success Criteria:</p>
                  <p className="text-sm text-muted-foreground whitespace-pre-wrap leading-relaxed">
                    {liScDisp.sc}
                  </p>
                </div>
              ) : null}
            </div>
          );
        }
        return (
          <ElaRichBlock title="Learning intentions and success criteria" html={liScDisp.html} />
        );
      })()}
      {((summary.daily_task_title ?? "").trim() || (summary.daily_task_body ?? "").trim()) && (
        <div className="space-y-2">
          <h4 className="text-sm font-semibold text-teal-800">Daily instructional task</h4>
          {(summary.daily_task_title ?? "").trim() ? (
            <p className="text-sm font-semibold text-foreground">{summary.daily_task_title}</p>
          ) : null}
          {(summary.daily_task_body ?? "").trim() ? (
            <CurriculumRichHtml
              className="prose prose-sm max-w-none text-muted-foreground rich-html"
              html={summary.daily_task_body}
            />
          ) : null}
        </div>
      )}
      <ElaRichBlock title="Content and learning strategies" html={summary.content_and_strategies} />
      {summary.standards_mentions && summary.standards_mentions.length > 0 && (
        <div className="space-y-1">
          <h4 className="text-sm font-semibold text-teal-800">Standards mentions (from matrix)</h4>
          <ul className="list-disc pl-5 text-sm text-muted-foreground">
            {summary.standards_mentions.map((m) => (
              <li key={m}>{m}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

/** One content cell in the ELA detailed-lesson table (matches DOCX table body cells). */
function ElaPlanBodyTd({ html }: { html?: string }) {
  const h = (html ?? "").trim();
  return (
    <td className="border border-slate-300 bg-white p-3 align-top text-muted-foreground">
      {h ? (
        <CurriculumRichHtml className="prose prose-sm max-w-none rich-html" html={h} />
      ) : (
        <span className="text-muted-foreground/40 text-xs">&nbsp;</span>
      )}
    </td>
  );
}

const ELA_PROCEDURE_BANDS: {
  key: keyof ElaLessonPlanStructuredPayload;
  banner: string;
}[] = [
  { key: "anticipatory_set_html", banner: "Anticipatory Set" },
  { key: "learning_procedures_html", banner: "Learning Procedures" },
  { key: "engagement_with_content_html", banner: "Engagement with the Content" },
  { key: "daily_instructional_task_html", banner: "Daily Instructional Task" },
];

/**
 * Renders `ela_lesson_plan_structured` as HTML tables aligned to the teacher-guide grid:
 * title row (1 col), LI|SC headers + body (2 col), Key Instructional Practices banner + two columns,
 * Vocabulary|Resources headers + body, full-width procedure bands, then a second table for
 * Differentiation|Addressing Misconceptions when present, then optional NJSLS banner + body (1 col)
 * as the final table so it always appears last.
 */
function ElaStructuredLessonPlanSection({ plan }: { plan: ElaLessonPlanStructuredPayload }) {
  const preamble = (plan.procedures_preamble_html ?? "").trim();
  const hasProcedureBucket = ELA_PROCEDURE_BANDS.some(
    (b) => ((plan[b.key] as string | undefined) ?? "").trim().length > 0,
  );
  const proceduresFull = (plan.procedures_full_html ?? "").trim();
  const showProceduresFullFallback = Boolean(proceduresFull) && !hasProcedureBucket && !preamble;
  const njsls = (plan.njsls_standards_html ?? "").trim();
  const diffL = (plan.differentiation_html ?? "").trim();
  const diffR = (plan.addressing_misconceptions_html ?? "").trim();
  const showDifferentiation = Boolean(diffL || diffR);

  const lessonHead =
    plan.lesson_number != null
      ? `Lesson ${plan.lesson_number}${(plan.lesson_title ?? "").trim() ? `: ${(plan.lesson_title ?? "").trim()}` : ""}`
      : (plan.lesson_title ?? "").trim() || "Lesson plan";

  const tableShell =
    "w-full border-collapse border border-slate-300 text-sm shadow-sm rounded-md overflow-hidden";

  return (
    <section className="space-y-3 rounded-xl border border-cyan-200/70 bg-cyan-50/20 p-4">
      <div className="flex items-center gap-2 text-cyan-900">
        <Layers className="w-5 h-5 shrink-0" />
        <span className="text-sm font-semibold uppercase tracking-wide">
          ELA detailed lesson plan
        </span>
      </div>

      <table className={tableShell}>
        <tbody>
          <tr>
            <td
              colSpan={2}
              className="border border-slate-300 bg-sky-800 py-2.5 px-4 text-center text-sm font-semibold text-white"
            >
              {lessonHead}
            </td>
          </tr>
          <tr>
            <th
              scope="col"
              className="w-1/2 border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
            >
              Learning Intention
            </th>
            <th
              scope="col"
              className="w-1/2 border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
            >
              Success Criteria
            </th>
          </tr>
          <tr>
            <ElaPlanBodyTd html={normalizeLiScTopicsToBulletsHtml(plan.learning_intention_html)} />
            <ElaPlanBodyTd html={normalizeLiScTopicsToBulletsHtml(plan.success_criteria_html)} />
          </tr>

          <tr>
            <td
              colSpan={2}
              className="border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
            >
              Key Instructional Practices
            </td>
          </tr>
          <tr>
            <ElaPlanBodyTd html={plan.key_questions_html} />
            <ElaPlanBodyTd html={plan.instructional_routines_assessments_html} />
          </tr>

          <tr>
            <th
              scope="col"
              className="border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
            >
              Vocabulary
            </th>
            <th
              scope="col"
              className="border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
            >
              Instructional Resources
            </th>
          </tr>
          <tr>
            <ElaPlanBodyTd html={plan.vocabulary_cell_html} />
            <ElaPlanBodyTd html={plan.instructional_resources_cell_html} />
          </tr>

          {preamble ? (
            <>
              <tr>
                <td
                  colSpan={2}
                  className="border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
                >
                  Procedures
                </td>
              </tr>
              <tr>
                <td colSpan={2} className="border border-slate-300 bg-white p-3 align-top">
                  <CurriculumRichHtml
                    className="prose prose-sm max-w-none text-muted-foreground rich-html"
                    html={preamble}
                  />
                </td>
              </tr>
            </>
          ) : null}

          {ELA_PROCEDURE_BANDS.map(({ key, banner }) => {
            const html = ((plan[key] as string | undefined) ?? "").trim();
            if (!html) return null;
            return (
              <Fragment key={banner}>
                <tr>
                  <td
                    colSpan={2}
                    className="border border-slate-300 bg-sky-100 py-2 px-3 text-sm font-semibold text-foreground"
                  >
                    {banner}
                  </td>
                </tr>
                <tr>
                  <td colSpan={2} className="border border-slate-300 bg-white p-3 align-top">
                    <CurriculumRichHtml
                      className="prose prose-sm max-w-none text-muted-foreground rich-html"
                      html={html}
                    />
                  </td>
                </tr>
              </Fragment>
            );
          })}

          {showProceduresFullFallback ? (
            <>
              <tr>
                <td
                  colSpan={2}
                  className="border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
                >
                  Instructional procedures
                </td>
              </tr>
              <tr>
                <td colSpan={2} className="border border-slate-300 bg-white p-3 align-top">
                  <CurriculumRichHtml
                    className="prose prose-sm max-w-none text-muted-foreground rich-html"
                    html={proceduresFull}
                  />
                </td>
              </tr>
            </>
          ) : null}
        </tbody>
      </table>

      {showDifferentiation ? (
        <table className={`${tableShell} mt-4`}>
          <tbody>
            <tr>
              <th
                scope="col"
                className="w-1/2 border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
              >
                Differentiation
              </th>
              <th
                scope="col"
                className="w-1/2 border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
              >
                Addressing Misconceptions
              </th>
            </tr>
            <tr>
              <ElaPlanBodyTd html={plan.differentiation_html} />
              <ElaPlanBodyTd html={plan.addressing_misconceptions_html} />
            </tr>
          </tbody>
        </table>
      ) : null}

      {njsls ? (
        <table className={`${tableShell} mt-4`}>
          <tbody>
            <tr>
              <td
                colSpan={2}
                className="border border-slate-300 bg-sky-100 py-2 px-3 text-center text-sm font-semibold text-foreground"
              >
                NJSLS Standards
              </td>
            </tr>
            <tr>
              <td colSpan={2} className="border border-slate-300 bg-white p-3 align-top">
                <CurriculumRichHtml
                  className="prose prose-sm max-w-none text-muted-foreground rich-html"
                  html={njsls}
                />
              </td>
            </tr>
          </tbody>
        </table>
      ) : null}
    </section>
  );
}

/** Derives procedure / ELA UI flags from lesson API payload (Phase 4.2 subject-aware detail). */
function lessonDetailPresentationFlags(
  selectedLesson: unknown,
  scienceDaySegmentsFromBundle: CurriculumScienceDaySegment[] = [],
) {
  const sl = selectedLesson as Lesson | null | undefined;
  const elaSummaryPayload = parseElaKeyLearningSummary(sl?.ela_key_learning_summary);
  const elaPlanPayload = parseElaLessonPlanStructured(sl?.ela_lesson_plan_structured);
  const fromBundle = sciencePayloadFromBundleSegments(scienceDaySegmentsFromBundle);
  const scienceDayPayload =
    fromBundle ?? parseScienceLiScDayStructured(sl?.science_li_sc_day_structured);
  const useScienceDayStructuredPrimary = Boolean(scienceDayPayload?.segments?.length);
  const useElaStructuredPrimary = elaPlanIsPrimaryUi(elaPlanPayload);
  const skipMathProcedureBanding =
    Boolean(elaPlanPayload) && elaPlanHasProcedureBuckets(elaPlanPayload!);
  const procedureSections = skipMathProcedureBanding
    ? []
    : splitProcedureSectionsFromHtml(sl?.procedure_html);
  const showStreamedProcedureHtml =
    Boolean((sl?.procedure_html ?? "").trim()) && !skipMathProcedureBanding;
  return {
    elaSummaryPayload,
    elaPlanPayload,
    scienceDayPayload,
    useScienceDayStructuredPrimary,
    useElaStructuredPrimary,
    skipMathProcedureBanding,
    procedureSections,
    showStreamedProcedureHtml,
    hideTeacherObjectivesForEla:
      useElaStructuredPrimary && Boolean((elaPlanPayload?.learning_intention_html ?? "").trim()),
    hideStudentObjectivesForEla:
      useElaStructuredPrimary && Boolean((elaPlanPayload?.success_criteria_html ?? "").trim()),
    hideDailyTasksBandForEla:
      useElaStructuredPrimary &&
      (Boolean((elaPlanPayload?.daily_instructional_task_html ?? "").trim()) ||
        skipMathProcedureBanding),
    hideStandaloneSuccessCriteriaForEla:
      useElaStructuredPrimary && Boolean((elaPlanPayload?.success_criteria_html ?? "").trim()),
    hideStandaloneSuccessCriteriaForScience: useScienceDayStructuredPrimary,
    hideObjectivesWhenScienceStructured: useScienceDayStructuredPrimary,
    hideStandardsSectionForElaStructured:
      useElaStructuredPrimary && Boolean(elaPlanPayload),
  };
}

export function CurriculumExplorer() {
  const [hierarchy, setHierarchy] = useState<Grade[]>([]);
  const [expandedGrades, setExpandedGrades] = useState<Set<string>>(new Set());
  const [expandedSubjects, setExpandedSubjects] = useState<Set<string>>(new Set());
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null);
  const [unitIntro, setUnitIntro] = useState<any>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [selectedLesson, setSelectedLesson] = useState<any>(null);
  const [scienceDaySegmentsBundle, setScienceDaySegmentsBundle] = useState<
    CurriculumScienceDaySegment[]
  >([]);
  const [bookPageExtractsBundle, setBookPageExtractsBundle] = useState<CurriculumBookPageExtract[]>(
    [],
  );
  const [scienceUnitOutline, setScienceUnitOutline] = useState<ScienceUnitDayOutline | null>(null);
  const [showUnitIntro, setShowUnitIntro] = useState(false);
  const [vocabulary, setVocabulary] = useState<VocabularyTerm[]>([]);
  const [lessonStandards, setLessonStandards] = useState<LessonStandardRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const mainContentScrollRef = useRef<HTMLDivElement>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<
    {
      id: string;
      unit_id: string;
      lesson_number: number;
      title: string;
      snippet_html?: string | null;
    }[]
  >([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [hierarchyError, setHierarchyError] = useState<string | null>(null);
  const lessonDetailsCacheRef = useRef<Map<string, CachedLessonPayload>>(new Map());
  const hoverPrefetchTimerRef = useRef<number | null>(null);
  /** While set, auto-restore last lesson for the unit is suppressed (e.g. opening a search result). */
  const explicitOpenLessonIdRef = useRef<string | null>(null);
  const fetchLessonDetailsRef = useRef<((lesson: Lesson) => Promise<void>) | null>(null);
  const activeLessonListItemRef = useRef<HTMLButtonElement | null>(null);
  const preambleListButtonRef = useRef<HTMLButtonElement | null>(null);
  const scienceBookSectionRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    return () => {
      if (hoverPrefetchTimerRef.current != null) {
        window.clearTimeout(hoverPrefetchTimerRef.current);
      }
    };
  }, []);

  useEffect(() => {
    fetchHierarchy();
  }, []);

  useEffect(() => {
    if (selectedLesson && mainContentScrollRef.current) {
      mainContentScrollRef.current.scrollTo({ top: 0, behavior: 'smooth' });
    }
  }, [selectedLesson]);

  const fetchHierarchy = async () => {
    setHierarchyError(null);
    try {
      const response = await fetch('/api/curriculum/explorer');
      const data: unknown = await response.json();
      if (!response.ok) {
        const detail =
          typeof data === 'object' &&
          data !== null &&
          'detail' in data &&
          (data as { detail?: unknown }).detail !== undefined
            ? JSON.stringify((data as { detail: unknown }).detail)
            : response.statusText || `HTTP ${response.status}`;
        setHierarchy([]);
        setHierarchyError(
          `Could not load curriculum (${response.status}). ${detail}`,
        );
        setLoading(false);
        return;
      }
      if (!Array.isArray(data)) {
        console.error('Curriculum explorer: expected JSON array, got', data);
        setHierarchy([]);
        setHierarchyError('Curriculum server returned an unexpected response.');
        setLoading(false);
        return;
      }
      setHierarchy(data as Grade[]);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching curriculum hierarchy:', error);
      setHierarchy([]);
      setHierarchyError(
        error instanceof Error ? error.message : 'Network error loading curriculum.',
      );
      setLoading(false);
    }
  };

  const fetchLessons = async (unit: Unit) => {
    setSelectedUnit(unit);
    setSelectedLesson(null);
    setScienceDaySegmentsBundle([]);
    setBookPageExtractsBundle([]);
    setScienceUnitOutline(null);
    setShowUnitIntro(false);
    setUnitIntro(null);
    setVocabulary([]);
    setLessonStandards([]);
    try {
      const resp1 = await fetch(`/api/curriculum/units/${unit.id}/lessons`);
      const data1 = await resp1.json();
      setLessons(data1);

      const resp2 = await fetch(`/api/curriculum/units/${unit.id}/intro`);
      if (resp2.ok) {
        const data2 = await resp2.json();
        setUnitIntro(data2);
      }

      if (usesModuleNodeLabel(unit)) {
        try {
          const resp3 = await fetch(
            `/api/curriculum/units/${encodeURIComponent(unit.id)}/science-day-outline`,
          );
          if (resp3.ok) {
            const raw: unknown = await resp3.json();
            setScienceUnitOutline(isScienceUnitDayOutline(raw) ? raw : null);
          }
        } catch (outlineErr) {
          console.error('Error fetching science module day outline:', outlineErr);
        }
      }
    } catch (error) {
      console.error('Error fetching lessons or intro:', error);
    }
  };

  const runLessonSearch = async () => {
    const q = searchQuery.trim();
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    setSearchLoading(true);
    try {
      const r = await fetch(
        `/api/curriculum/search?q=${encodeURIComponent(q)}&limit=40`
      );
      if (!r.ok) throw new Error('search failed');
      const data = await r.json();
      setSearchResults(Array.isArray(data) ? data : []);
    } catch (e) {
      console.error('Curriculum search error:', e);
      setSearchResults([]);
    } finally {
      setSearchLoading(false);
    }
  };

  const openSearchHit = async (hit: {
    id: string;
    unit_id: string;
    lesson_number: number;
    title: string;
    snippet_html?: string | null;
  }) => {
    let unit: Unit | null = null;
    for (const g of hierarchy) {
      for (const s of g.subjects) {
        const u = s.units.find((x) => x.id === hit.unit_id);
        if (u) {
          unit = u;
          break;
        }
      }
      if (unit) break;
    }
    if (!unit) {
      console.warn('Search hit unit not in explorer tree:', hit.unit_id);
      return;
    }
    explicitOpenLessonIdRef.current = hit.id;
    try {
      await fetchLessons(unit);
      await fetchLessonDetails({
        id: hit.id,
        lesson_number: hit.lesson_number,
        title: hit.title,
      });
    } finally {
      explicitOpenLessonIdRef.current = null;
    }
  };

  const applyCachedLessonToUi = (p: CachedLessonPayload) => {
    setSelectedLesson(p.details);
    setScienceDaySegmentsBundle(p.science_day_segments ?? []);
    setBookPageExtractsBundle(
      shouldRequestGrade2ScienceBookBundle(p.details.id)
        ? normalizeBookPageExtracts(p.book_page_extracts as unknown)
        : [],
    );
    startTransition(() => {
      setVocabulary(p.vocabulary);
      setLessonStandards(p.standards);
    });
  };

  const fetchLessonDetails = async (lesson: Lesson) => {
    try {
      const memory = lessonDetailsCacheRef.current.get(lesson.id);
      if (memory) {
        const staleWithoutBookBundle =
          shouldRequestGrade2ScienceBookBundle(lesson.id) &&
          memory.book_page_extracts === undefined;
        if (!staleWithoutBookBundle) {
          applyCachedLessonToUi(memory);
          return;
        }
      }

      setLoadingDetails(true);
      const disk = await getCachedBundle(lesson.id);

      let revalidateEtag: string | null = null;
      if (disk) {
        const details = disk.lesson as Lesson;
        const vocab = (Array.isArray(disk.vocabulary) ? disk.vocabulary : []) as VocabularyTerm[];
        const std = (Array.isArray(disk.standards) ? disk.standards : []) as LessonStandardRow[];
        const diskSeg = normalizeBundleScienceSegments(disk.science_day_segments);
        const diskBook = normalizeBookPageExtracts(disk.book_page_extracts);
        const diskEtag =
          typeof disk.etag === 'string' && disk.etag.trim() ? disk.etag.trim() : null;
        applyCachedLessonToUi({
          details,
          vocabulary: vocab,
          standards: std,
          science_day_segments: diskSeg,
          book_page_extracts: diskBook,
          etag: diskEtag ?? undefined,
        });
        revalidateEtag =
          shouldRequestGrade2ScienceBookBundle(lesson.id) ? null : diskEtag;
        setLoadingDetails(false);
      }

      const headers: HeadersInit = {};
      if (revalidateEtag && !shouldRequestGrade2ScienceBookBundle(lesson.id)) {
        headers['If-None-Match'] = revalidateEtag;
      }

      const r = await fetch(curriculumLessonBundleUrl(lesson.id), { headers });

      if (r.status === 304) {
        if (disk) {
          const details = disk.lesson as Lesson;
          const vocab = (Array.isArray(disk.vocabulary) ? disk.vocabulary : []) as VocabularyTerm[];
          const std = (Array.isArray(disk.standards) ? disk.standards : []) as LessonStandardRow[];
          const diskSeg304 = normalizeBundleScienceSegments(disk.science_day_segments);
          const diskBook304 = normalizeBookPageExtracts(disk.book_page_extracts);
          lessonDetailsCacheRef.current.set(lesson.id, {
            details,
            vocabulary: vocab,
            standards: std,
            science_day_segments: diskSeg304,
            book_page_extracts: diskBook304,
            etag: revalidateEtag ?? undefined,
          });
        } else {
          setLoadingDetails(false);
        }
        return;
      }

      if (!r.ok) {
        setLoadingDetails(false);
        throw new Error('Failed to fetch lesson bundle');
      }

      const bundle = (await r.json()) as {
        lesson: Lesson;
        vocabulary: VocabularyTerm[];
        standards: LessonStandardRow[];
        science_day_segments?: unknown[];
        book_page_extracts?: unknown[];
      };

      const nextEtagHeader = r.headers.get('etag');
      const nextEtag =
        typeof nextEtagHeader === 'string' && nextEtagHeader.trim()
          ? nextEtagHeader.trim()
          : null;
      const vocabList = Array.isArray(bundle.vocabulary) ? bundle.vocabulary : [];
      const stdList = Array.isArray(bundle.standards) ? bundle.standards : [];
      const segList = normalizeBundleScienceSegments(bundle.science_day_segments);
      const bookList = normalizeBookPageExtracts(bundle.book_page_extracts);
      const payload: CachedLessonPayload = {
        details: bundle.lesson,
        vocabulary: vocabList,
        standards: stdList,
        science_day_segments: segList,
        book_page_extracts: bookList,
        etag: nextEtag ?? undefined,
      };
      applyCachedLessonToUi(payload);
      lessonDetailsCacheRef.current.set(lesson.id, payload);
      const ch = String(bundle.lesson?.content_hash ?? '').trim();
      void setCachedBundle(lesson.id, {
        lesson: bundle.lesson,
        vocabulary: vocabList,
        standards: stdList,
        science_day_segments: segList,
        book_page_extracts: bookList,
        etag: nextEtag ?? '',
        contentHash: ch,
      });
      setLoadingDetails(false);
    } catch (error) {
      console.error('Error fetching lesson details:', error);
      setLoadingDetails(false);
    }
  };

  fetchLessonDetailsRef.current = fetchLessonDetails;

  const prefetchLessonDetails = useCallback(async (lesson: Lesson | undefined) => {
    if (!lesson) return;
    if (lessonDetailsCacheRef.current.has(lesson.id)) return;
    try {
      const r = await fetch(curriculumLessonBundleUrl(lesson.id));
      if (!r.ok) return;
      const bundle = (await r.json()) as {
        lesson: Lesson;
        vocabulary: VocabularyTerm[];
        standards: LessonStandardRow[];
        science_day_segments?: unknown[];
        book_page_extracts?: unknown[];
      };
      const nextEtagHeader = r.headers.get('etag');
      const nextEtag =
        typeof nextEtagHeader === 'string' && nextEtagHeader.trim()
          ? nextEtagHeader.trim()
          : null;
      const vocabList = Array.isArray(bundle.vocabulary) ? bundle.vocabulary : [];
      const stdList = Array.isArray(bundle.standards) ? bundle.standards : [];
      const segListPrefetch = normalizeBundleScienceSegments(bundle.science_day_segments);
      const bookPrefetch = normalizeBookPageExtracts(bundle.book_page_extracts);
      const payload: CachedLessonPayload = {
        details: bundle.lesson,
        vocabulary: vocabList,
        standards: stdList,
        science_day_segments: segListPrefetch,
        book_page_extracts: bookPrefetch,
        etag: nextEtag ?? undefined,
      };
      lessonDetailsCacheRef.current.set(lesson.id, payload);
      const ch = String(bundle.lesson?.content_hash ?? '').trim();
      void setCachedBundle(lesson.id, {
        lesson: bundle.lesson,
        vocabulary: vocabList,
        standards: stdList,
        science_day_segments: segListPrefetch,
        book_page_extracts: bookPrefetch,
        etag: nextEtag ?? '',
        contentHash: ch,
      });
    } catch {
      // Prefetch is best-effort; ignore failures.
    }
  }, []);

  const scheduleLessonHoverPrefetch = (lesson: Lesson) => {
    if (saveDataPreferred()) return;
    if (lessonDetailsCacheRef.current.has(lesson.id)) return;
    if (hoverPrefetchTimerRef.current != null) {
      window.clearTimeout(hoverPrefetchTimerRef.current);
    }
    hoverPrefetchTimerRef.current = window.setTimeout(() => {
      hoverPrefetchTimerRef.current = null;
      void prefetchLessonDetails(lesson);
    }, HOVER_PREFETCH_DELAY_MS);
  };

  const clearLessonHoverPrefetch = () => {
    if (hoverPrefetchTimerRef.current != null) {
      window.clearTimeout(hoverPrefetchTimerRef.current);
      hoverPrefetchTimerRef.current = null;
    }
  };

  const toggleGrade = (grade: string) => {
    const newExpanded = new Set(expandedGrades);
    if (newExpanded.has(grade)) newExpanded.delete(grade);
    else newExpanded.add(grade);
    setExpandedGrades(newExpanded);
  };

  const toggleSubject = (gradeSubject: string) => {
    const newExpanded = new Set(expandedSubjects);
    if (newExpanded.has(gradeSubject)) newExpanded.delete(gradeSubject);
    else newExpanded.add(gradeSubject);
    setExpandedSubjects(newExpanded);
  };

  const lessonDetailFlags = useMemo(
    () => lessonDetailPresentationFlags(selectedLesson, scienceDaySegmentsBundle),
    [selectedLesson, scienceDaySegmentsBundle],
  );
  const selectedLessonHasScienceBook = Boolean(
    selectedLesson && shouldRequestGrade2ScienceBookBundle(selectedLesson.id),
  );

  const jumpToScienceBookSection = useCallback(() => {
    if (!selectedLessonHasScienceBook) return;
    scienceBookSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }, [selectedLessonHasScienceBook]);

  const elaVocabTermList = useMemo(() => {
    if (!lessonDetailFlags.useElaStructuredPrimary) return [];
    return extractElaVocabularyTermsFromStructuredCell(
      lessonDetailFlags.elaPlanPayload?.vocabulary_cell_html,
    );
  }, [
    lessonDetailFlags.useElaStructuredPrimary,
    lessonDetailFlags.elaPlanPayload?.vocabulary_cell_html,
  ]);

  const elaVocabTermsSanitized = useMemo(
    () => elaVocabTermList.filter((t) => !isLikelyJunkVocabLabel(t)),
    [elaVocabTermList],
  );

  const displayVocabulary = useMemo(() => {
    const voc = vocabulary.filter((v) => !isLikelyJunkVocabLabel(v.term));
    if (elaVocabTermsSanitized.length === 0) return voc;
    return elaVocabTermsSanitized.map((term) => {
      const hit = voc.find(
        (v) => v.term.trim().toLowerCase() === term.toLowerCase(),
      );
      if (hit) return hit;
      return {
        term,
        translated_term: term,
        leveled_definitions: [] as VocabularyTerm["leveled_definitions"],
      };
    });
  }, [elaVocabTermsSanitized, vocabulary]);

  const selectedHierarchyPath = useMemo(() => {
    if (!selectedUnit) return null;
    for (const grade of hierarchy) {
      for (const subject of grade.subjects) {
        const match = subject.units.find((u) => u.id === selectedUnit.id);
        if (match) {
          return {
            gradeLabel: normalizeGradeLabel(grade.name),
            subjectLabel: normalizeSubjectLabel(subject.name),
            unitLabel: normalizeUnitLabel(match),
          };
        }
      }
    }
    return null;
  }, [hierarchy, selectedUnit]);

  const hasScienceModuleWriterBands = useMemo(() => {
    if (!selectedUnit || !usesModuleNodeLabel(selectedUnit)) return false;
    return (scienceUnitOutline?.total_writer_bands ?? 0) > 0;
  }, [selectedUnit, scienceUnitOutline]);

  const hasUnitOverviewNav = Boolean(unitIntro) || hasScienceModuleWriterBands;

  const currentLessonIndex = useMemo(
    () => lessonIndexInUnitList(lessons, selectedLesson),
    [lessons, selectedLesson?.id, selectedLesson?.lesson_number],
  );

  const navigateToLessonByIndex = (index: number) => {
    if (index < 0 || index >= lessons.length) return;
    const lesson = lessons[index];
    setShowUnitIntro(false);
    void fetchLessonDetails(lesson);
  };

  const navigateToPreviousLesson = () => {
    if (currentLessonIndex <= 0) return;
    navigateToLessonByIndex(currentLessonIndex - 1);
  };

  const navigateToNextLesson = () => {
    if (currentLessonIndex < 0 || currentLessonIndex >= lessons.length - 1) return;
    navigateToLessonByIndex(currentLessonIndex + 1);
  };

  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      const target = e.target as HTMLElement | null;
      const tag = (target?.tagName || '').toLowerCase();
      const isTypingContext =
        tag === 'input' || tag === 'textarea' || target?.isContentEditable;
      if (isTypingContext) return;

      const scrollerActive =
        Boolean(selectedUnit) &&
        (lessons.length > 0 || Boolean(unitIntro) || hasScienceModuleWriterBands);

      if (scrollerActive && e.key === 'ArrowUp') {
        e.preventDefault();
        if (!lessons.length && !unitIntro && !hasScienceModuleWriterBands) return;
        if (showUnitIntro && (unitIntro || hasScienceModuleWriterBands)) return;
        if (
          (unitIntro || hasScienceModuleWriterBands) &&
          !showUnitIntro &&
          currentLessonIndex === 0
        ) {
          setSelectedLesson(null);
          setScienceDaySegmentsBundle([]);
          setBookPageExtractsBundle([]);
          setShowUnitIntro(true);
          return;
        }
        navigateToPreviousLesson();
        return;
      }

      if (scrollerActive && e.key === 'ArrowDown') {
        e.preventDefault();
        if (!lessons.length && !unitIntro && !hasScienceModuleWriterBands) return;
        if (showUnitIntro && (unitIntro || hasScienceModuleWriterBands)) {
          navigateToLessonByIndex(0);
          return;
        }
        navigateToNextLesson();
        return;
      }

      if (!selectedLesson) return;
      if (e.key === 'ArrowLeft') {
        e.preventDefault();
        navigateToPreviousLesson();
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        navigateToNextLesson();
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [
    selectedUnit,
    unitIntro,
    hasScienceModuleWriterBands,
    lessons,
    selectedLesson,
    showUnitIntro,
    currentLessonIndex,
  ]);

  useEffect(() => {
    if (currentLessonIndex < 0) return;
    for (let d = -PREFETCH_ADJACENCY_RADIUS; d <= PREFETCH_ADJACENCY_RADIUS; d++) {
      if (d === 0) continue;
      void prefetchLessonDetails(lessons[currentLessonIndex + d]);
    }
  }, [currentLessonIndex, lessons, prefetchLessonDetails]);

  useEffect(() => {
    const frame = window.requestAnimationFrame(() => {
      if (showUnitIntro && (unitIntro || hasScienceModuleWriterBands)) {
        preambleListButtonRef.current?.scrollIntoView({
          block: 'center',
          inline: 'nearest',
          behavior: 'smooth',
        });
        return;
      }
      if (currentLessonIndex < 0) return;
      activeLessonListItemRef.current?.scrollIntoView({
        block: 'center',
        inline: 'nearest',
        behavior: 'smooth',
      });
    });
    return () => window.cancelAnimationFrame(frame);
  }, [
    currentLessonIndex,
    showUnitIntro,
    unitIntro,
    hasScienceModuleWriterBands,
    lessons.length,
    selectedLesson?.id,
    selectedLesson?.lesson_number,
  ]);

  useEffect(() => {
    if (!selectedUnit || lessons.length === 0) return;
    if (explicitOpenLessonIdRef.current) return;
    if (showUnitIntro) return;
    if (selectedLesson) return;
    const lastId = readLastLessonIdForUnit(selectedUnit.id);
    const remembered = lastId ? lessons.find((l) => l.id === lastId) : undefined;
    const defaultFirst =
      lessons.find((l) => l.lesson_number === 1) ?? lessons[0];
    const toOpen = remembered ?? defaultFirst;
    if (toOpen && fetchLessonDetailsRef.current) {
      void fetchLessonDetailsRef.current(toOpen);
    }
  }, [selectedUnit, lessons, selectedLesson, showUnitIntro]);

  useEffect(() => {
    if (!selectedUnit?.id || !selectedLesson?.id) return;
    writeLastLessonIdForUnit(selectedUnit.id, selectedLesson.id);
  }, [selectedUnit?.id, selectedLesson?.id]);

  useEffect(() => {
    if (lessons.length === 0) return;
    if (saveDataPreferred()) return;

    const run = () => {
      for (const lesson of lessons) {
        void prefetchLessonDetails(lesson);
      }
    };

    const idle = window.requestIdleCallback?.(run, { timeout: 5000 });
    if (idle !== undefined) {
      return () => window.cancelIdleCallback?.(idle);
    }
    const t = window.setTimeout(run, 0);
    return () => window.clearTimeout(t);
  }, [lessons, prefetchLessonDetails]);

  if (loading) {
    return <div className="flex items-center justify-center p-12">Loading Curriculum...</div>;
  }

  const {
    elaSummaryPayload,
    elaPlanPayload,
    scienceDayPayload,
    useScienceDayStructuredPrimary,
    useElaStructuredPrimary,
    skipMathProcedureBanding,
    procedureSections,
    showStreamedProcedureHtml,
    hideTeacherObjectivesForEla,
    hideStudentObjectivesForEla,
    hideDailyTasksBandForEla,
    hideStandaloneSuccessCriteriaForEla,
    hideStandaloneSuccessCriteriaForScience,
    hideObjectivesWhenScienceStructured,
    hideStandardsSectionForElaStructured,
  } = lessonDetailFlags;
  const procedureHeaderUi: Record<
    ProcedureSection["kind"],
    { icon: any; iconClass: string; titleClass: string; cardClass: string }
  > = {
    warmup: {
      icon: Clock,
      iconClass: "text-blue-600",
      titleClass: "text-blue-700",
      cardClass: "bg-blue-50/40 border-blue-200",
    },
    activity: {
      icon: ChevronRight,
      iconClass: "text-emerald-600",
      titleClass: "text-emerald-700",
      cardClass: "bg-emerald-50/35 border-emerald-200",
    },
    cooldown: {
      icon: FileText,
      iconClass: "text-amber-600",
      titleClass: "text-amber-700",
      cardClass: "bg-amber-50/35 border-amber-200",
    },
    synthesis: {
      icon: BookOpen,
      iconClass: "text-violet-600",
      titleClass: "text-violet-700",
      cardClass: "bg-violet-50/35 border-violet-200",
    },
    other: {
      icon: Info,
      iconClass: "text-slate-600",
      titleClass: "text-slate-700",
      cardClass: "bg-slate-50/35 border-slate-200",
    },
  };

  return (
    <div className="flex h-[calc(100vh-12rem)] border rounded-xl overflow-hidden bg-background shadow-sm">
      {/* Sidebar Explorer - Narrower */}
      <div className="w-64 border-r bg-muted/20 overflow-y-auto p-4 space-y-2 flex-shrink-0">
        <div className="flex items-center gap-2 mb-4 px-2">
          <Layers className="w-5 h-5 text-primary" />
          <h2 className="font-semibold text-lg uppercase tracking-tight">Explorer</h2>
        </div>

        {hierarchyError && (
          <div
            className="mb-3 mx-2 rounded-md border border-destructive/40 bg-destructive/10 px-2 py-2 text-xs text-destructive"
            role="alert"
          >
            <p className="font-semibold mb-1">Curriculum unavailable</p>
            <p className="break-words text-destructive/90">{hierarchyError}</p>
            <p className="mt-2 text-[10px] text-muted-foreground">
              Ensure the API is running (for example port 8000) and the curriculum database file exists
              and is up to date.
            </p>
          </div>
        )}

        <div className="mb-4 px-2 space-y-2">
          <label className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wide">
            Search lessons
          </label>
          <div className="flex gap-1">
            <input
              type="search"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void runLessonSearch();
              }}
              placeholder="2+ characters"
              className="flex-1 min-w-0 text-xs rounded-md border border-border bg-background px-2 py-1.5"
            />
            <button
              type="button"
              onClick={() => void runLessonSearch()}
              disabled={searchLoading}
              className="text-xs px-2 py-1 rounded-md bg-primary text-primary-foreground disabled:opacity-50"
            >
              Go
            </button>
          </div>
          {searchResults.length > 0 && (
            <ul className="max-h-52 overflow-y-auto text-xs space-y-1 border border-border rounded-md p-1 bg-background">
              {searchResults.map((hit) => (
                <li key={hit.id}>
                  <button
                    type="button"
                    onClick={() => void openSearchHit(hit)}
                    className="w-full text-left px-1 py-0.5 rounded hover:bg-muted"
                    title={hit.title}
                  >
                    <span className="block truncate font-medium">
                      L{hit.lesson_number}: {hit.title}
                    </span>
                    {hit.snippet_html ? (
                      <span
                        className="block text-[10px] text-muted-foreground line-clamp-2 [&_mark]:bg-amber-200/80 dark:[&_mark]:bg-amber-600/50"
                        dangerouslySetInnerHTML={{ __html: hit.snippet_html }}
                      />
                    ) : null}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {hierarchy.map((grade) => (
          <div key={grade.name} className="space-y-1">
            <button
              onClick={() => toggleGrade(grade.name)}
              className="w-full flex items-center gap-2 px-2 py-1.5 hover:bg-muted rounded-md text-sm font-medium transition-colors"
            >
              {expandedGrades.has(grade.name) ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
              <span>{normalizeGradeLabel(grade.name)}</span>
            </button>
            
            {expandedGrades.has(grade.name) && (
              <div className="ml-4 space-y-1">
                {grade.subjects.map((subject) => {
                  const key = `${grade.name}-${subject.name}`;
                  return (
                    <div key={subject.name}>
                      <button
                        onClick={() => toggleSubject(key)}
                        className="w-full flex items-center gap-2 px-2 py-1.5 hover:bg-muted rounded-md text-xs font-semibold text-muted-foreground transition-colors"
                      >
                        {expandedSubjects.has(key) ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
                        <span>{normalizeSubjectLabel(subject.name)}</span>
                      </button>
                      
                      {expandedSubjects.has(key) && (
                        <div className="ml-4 space-y-1">
                          {subject.units.map((unit) => (
                            <button
                              key={unit.id}
                              onClick={() => fetchLessons(unit)}
                              className={`w-full text-left px-2 py-1.5 rounded-md text-xs transition-colors ${
                                selectedUnit?.id === unit.id ? 'bg-primary text-primary-foreground font-medium' : 'hover:bg-muted text-muted-foreground'
                              }`}
                            >
                              <span className="block">{normalizeUnitLabel(unit)}</span>
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Main Content Pane */}
      <div className="flex-1 flex flex-col min-h-0 overflow-hidden bg-card">
        {!selectedUnit ? (
          <div className="h-full flex flex-col items-center justify-center text-muted-foreground space-y-4 px-6">
            <Book className="w-16 h-16 opacity-10" />
            {hierarchyError ? (
              <>
                <p className="text-lg font-medium text-center text-destructive/90">
                  Curriculum could not be loaded
                </p>
                <p className="text-sm text-center max-w-md">{hierarchyError}</p>
              </>
            ) : (
              <p className="text-lg">
                Select a grade, subject, and module or unit to browse lessons
              </p>
            )}
          </div>
        ) : (
          <div className="flex flex-col flex-1 min-h-0 animate-in fade-in duration-500">
            {/* Fixed header: does not scroll with lesson content */}
            <div className="flex-shrink-0 z-20 border-b border-border bg-card px-4 py-2 shadow-sm">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-3">
                {lessons.length > 0 || hasUnitOverviewNav ? (
                  <div
                    className="flex w-full shrink-0 flex-col gap-1.5 sm:max-w-[min(100%,260px)] sm:w-[min(40vw,260px)]"
                  >
                    <div
                      className="rounded-md border border-border bg-background"
                      aria-label="Lesson list"
                    >
                      <div className="max-h-[min(5rem,40vh)] overflow-y-auto divide-y divide-border">
                        {hasUnitOverviewNav && (
                          <button
                            type="button"
                            ref={preambleListButtonRef}
                            onClick={() => {
                              setSelectedLesson(null);
                              setScienceDaySegmentsBundle([]);
                              setBookPageExtractsBundle([]);
                              setShowUnitIntro(true);
                            }}
                            className={`flex w-full items-center justify-between gap-2 px-2 py-1 text-left text-xs transition-colors ${
                              showUnitIntro ? 'bg-primary/10 text-primary' : 'hover:bg-muted/60'
                            }`}
                          >
                            <span className="truncate font-medium">
                              {explorerCurriculumNodeNoun(selectedUnit)} Overview &amp; TOC
                            </span>
                            <span className="shrink-0 text-[10px] uppercase text-muted-foreground">
                              Preamble
                            </span>
                          </button>
                        )}
                        {lessons.map((lesson, lessonIdx) => (
                          <button
                            key={lesson.id}
                            ref={
                              !showUnitIntro && lessonIdx === currentLessonIndex
                                ? activeLessonListItemRef
                                : undefined
                            }
                            type="button"
                            onMouseEnter={() => scheduleLessonHoverPrefetch(lesson)}
                            onMouseLeave={clearLessonHoverPrefetch}
                            onClick={() => {
                              setShowUnitIntro(false);
                              void fetchLessonDetails(lesson);
                            }}
                            className={`flex w-full items-center gap-1.5 px-2 py-1 text-left text-xs transition-colors ${
                              !showUnitIntro && lessonIdx === currentLessonIndex
                                ? 'bg-primary/10 text-primary'
                                : 'hover:bg-muted/60'
                            }`}
                          >
                            <span className="min-w-0 flex-1 truncate font-medium">
                              {`Lesson ${lesson.lesson_number}: ${lesson.title}`}
                            </span>
                            <ChevronRight className="h-3.5 w-3.5 shrink-0 text-muted-foreground" />
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-1.5">
                      <button
                        type="button"
                        onClick={navigateToPreviousLesson}
                        disabled={currentLessonIndex <= 0 || lessons.length === 0}
                        className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border border-border bg-background disabled:opacity-40"
                        title="Previous lesson (Left Arrow)"
                      >
                        <ChevronLeft className="w-3.5 h-3.5" />
                        Previous
                      </button>
                      <button
                        type="button"
                        onClick={navigateToNextLesson}
                        disabled={
                          currentLessonIndex < 0 ||
                          currentLessonIndex >= lessons.length - 1 ||
                          lessons.length === 0
                        }
                        className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border border-border bg-background disabled:opacity-40"
                        title="Next lesson (Right Arrow)"
                      >
                        Next
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                      {selectedLessonHasScienceBook && !showUnitIntro && (
                        <button
                          type="button"
                          onClick={jumpToScienceBookSection}
                          className="inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-md border border-amber-300/70 dark:border-amber-900/50 bg-amber-50/70 dark:bg-amber-950/30 text-amber-900 dark:text-amber-200 hover:bg-amber-100/70 dark:hover:bg-amber-900/40"
                          title="Jump to Science Book section"
                        >
                          <BookCopy className="w-3.5 h-3.5" />
                          Science Book
                        </button>
                      )}
                    </div>
                  </div>
                ) : null}
                <div
                  className={`min-w-0 flex flex-col gap-1 ${
                    lessons.length > 0 || hasUnitOverviewNav
                      ? 'flex-1 sm:items-end sm:text-right'
                      : 'flex-1'
                  }`}
                >
                  <div className="text-sm font-medium text-muted-foreground leading-tight">
                    {selectedHierarchyPath
                      ? `${selectedHierarchyPath.gradeLabel} - ${selectedHierarchyPath.unitLabel}`
                      : normalizeUnitLabel(selectedUnit)}
                  </div>
                  <div className="text-lg font-semibold leading-snug text-foreground line-clamp-2 sm:max-w-2xl">
                    {loadingDetails && selectedLesson
                      ? 'Loading lesson...'
                      : selectedLesson
                        ? `Lesson ${selectedLesson.lesson_number}: ${selectedLesson.title || 'Untitled Lesson'}`
                        : showUnitIntro && hasUnitOverviewNav
                          ? `${explorerCurriculumNodeNoun(selectedUnit)} Overview & TOC`
                          : 'Select a lesson'}
                  </div>
                </div>
              </div>
            </div>

            <div
              ref={mainContentScrollRef}
              className="flex-1 min-h-0 overflow-y-auto px-6 py-6 space-y-8"
            >
            {/* Content Display (Lesson or Unit Intro) */}
            {showUnitIntro && selectedUnit && hasUnitOverviewNav && (
              <div className="space-y-6 border-t border-border pt-6">
                <div className="space-y-4">
                  <h2 className="text-2xl font-bold">
                    {explorerCurriculumNodeNoun(selectedUnit)} Overview
                  </h2>
                  {unitIntro && String(unitIntro.procedure_html || '').trim() ? (
                    <CurriculumRichHtml
                      className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                      html={unitIntro.procedure_html}
                    />
                  ) : unitIntro ? (
                    <p className="text-sm text-muted-foreground">
                      No overview text is available for this unit.
                    </p>
                  ) : null}
                  {usesModuleNodeLabel(selectedUnit) &&
                    scienceUnitOutline &&
                    scienceUnitOutline.total_writer_bands > 0 && (
                      <section
                        className="space-y-3 rounded-lg border border-border bg-muted/5 p-4"
                        aria-label="Writer day bands for this module"
                      >
                        <h3 className="text-base font-semibold text-foreground">
                          Writer day bands ({scienceUnitOutline.total_writer_bands} in this{' '}
                          {explorerCurriculumNodeNoun(selectedUnit).toLowerCase()})
                        </h3>
                        <p className="text-xs text-muted-foreground">
                          Author clusters from the source guide. This is not mapped to your school
                          calendar; use it for pacing context only.
                        </p>
                        <div className="space-y-4">
                          {buildScienceModuleOutlineDisplay(scienceUnitOutline).map((lesson) => (
                            <div key={lesson.lesson_id} className="text-sm">
                              <p className="font-medium text-foreground">
                                Lesson {lesson.lesson_number}
                                {lesson.title ? `: ${lesson.title}` : ''}
                              </p>
                              <ul className="mt-1 list-disc pl-5 text-muted-foreground">
                                {lesson.segmentRows.map((row) => (
                                  <li key={row.key}>
                                    <span className="font-medium text-foreground/90">
                                      Band {row.moduleBandNumber}
                                    </span>
                                    {' \u2014 '}
                                    {row.dayLabel}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      </section>
                    )}
                </div>
              </div>
            )}

            {/* Lesson Detail Pane */}
            {(selectedLesson || loadingDetails) && (
              <div className="space-y-8 border-t border-border pt-6">
                {loadingDetails ? (
                  <div
                    className="space-y-4 py-8"
                    role="status"
                    aria-live="polite"
                    aria-label="Loading lesson content"
                  >
                    <div className="flex items-center gap-3 text-muted-foreground">
                      <Book className="h-8 w-8 shrink-0 animate-pulse" />
                      <div className="min-w-0 flex-1 space-y-2">
                        <div className="h-4 w-3/5 max-w-md rounded bg-muted animate-pulse" />
                        <div className="h-3 w-4/5 max-w-lg rounded bg-muted/80 animate-pulse" />
                        <div className="h-3 w-2/5 max-w-sm rounded bg-muted/70 animate-pulse" />
                      </div>
                    </div>
                    <div className="space-y-3 rounded-lg border border-border bg-muted/20 p-4">
                      <div className="h-3 w-full rounded bg-muted animate-pulse" />
                      <div className="h-3 w-[92%] rounded bg-muted animate-pulse" />
                      <div className="h-3 w-[88%] rounded bg-muted animate-pulse" />
                      <div className="h-24 w-full rounded-md bg-muted/60 animate-pulse" />
                    </div>
                  </div>
                ) : (
                  <>
                  <p className="text-muted-foreground text-sm">Detailed Lesson Plan & Vocabulary</p>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                  {/* Left: Content */}
                  <div className="lg:col-span-2 space-y-8">
                    {elaSummaryPayload && !useElaStructuredPrimary ? (
                      <ElaKeyLearningSection summary={elaSummaryPayload} />
                    ) : null}
                    {useElaStructuredPrimary && elaPlanPayload ? (
                      <ElaStructuredLessonPlanSection plan={elaPlanPayload} />
                    ) : null}
                    {useScienceDayStructuredPrimary && scienceDayPayload?.segments ? (
                      <section className="space-y-4" aria-label="Science learning intentions by day">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-sky-700">
                          <FileText className="w-5 h-5" />
                          Learning intention and success criteria (by day)
                        </h3>
                        <div className="space-y-6">
                          {scienceDayPayload.segments.map((seg, idx) => (
                            <div
                              key={`${seg.label}-${idx}`}
                              className="rounded-lg border border-border bg-muted/10 p-4 space-y-4"
                            >
                              <h4 className="font-semibold text-base text-foreground">
                                {seg.label}
                              </h4>
                              {(seg.brief_overview || "").trim() ? (
                                <div className="space-y-2 rounded-md border border-sky-200/60 bg-sky-50/50 p-3 dark:border-sky-900/40 dark:bg-sky-950/20">
                                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                    Summary of key learning
                                  </p>
                                  <CurriculumRichHtml
                                    className="prose prose-sm max-w-none text-muted-foreground rich-html"
                                    html={(seg.brief_overview || "").trim()}
                                  />
                                </div>
                              ) : null}
                              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                <div className="space-y-2">
                                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                    Learning intention
                                  </p>
                                  <CurriculumRichHtml
                                    className="prose prose-sm max-w-none text-muted-foreground rich-html"
                                    html={
                                      (seg.learning_intention_html || "").trim() ||
                                      "<p class=\"text-muted-foreground\">—</p>"
                                    }
                                  />
                                </div>
                                <div className="space-y-2">
                                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                    Success criteria
                                  </p>
                                  <CurriculumRichHtml
                                    className="prose prose-sm max-w-none text-muted-foreground rich-html"
                                    html={
                                      (seg.success_criteria_html || "").trim() ||
                                      "<p class=\"text-muted-foreground\">—</p>"
                                    }
                                  />
                                </div>
                              </div>
                              {(seg.lesson_in_action_html || "").trim() ? (
                                <div className="space-y-2 border-t border-border pt-4">
                                  <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                    Lesson in action
                                  </p>
                                  {seg.experimental_splits &&
                                  (
                                    seg.experimental_splits.opening_html ||
                                    seg.experimental_splits.during_html ||
                                    seg.experimental_splits.closing_html ||
                                    seg.experimental_splits.online_html
                                  )?.trim() ? (
                                    <details className="rounded-md border border-border bg-background/80 px-3 py-2 text-sm">
                                      <summary className="cursor-pointer font-medium text-foreground">
                                        Structured sections (parsed)
                                      </summary>
                                      <div className="mt-3 space-y-4 border-t border-border pt-3">
                                        {(seg.experimental_splits.opening_html || "").trim() ? (
                                          <div className="space-y-1">
                                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                              Lesson opening
                                            </p>
                                            <CurriculumRichHtml
                                              className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                                              html={(seg.experimental_splits.opening_html || "").trim()}
                                            />
                                          </div>
                                        ) : null}
                                        {(seg.experimental_splits.during_html || "").trim() ? (
                                          <div className="space-y-1">
                                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                              During the lesson
                                            </p>
                                            <CurriculumRichHtml
                                              className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                                              html={(seg.experimental_splits.during_html || "").trim()}
                                            />
                                          </div>
                                        ) : null}
                                        {(seg.experimental_splits.closing_html || "").trim() ? (
                                          <div className="space-y-1">
                                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                              Lesson closing
                                            </p>
                                            <CurriculumRichHtml
                                              className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                                              html={(seg.experimental_splits.closing_html || "").trim()}
                                            />
                                          </div>
                                        ) : null}
                                        {(seg.experimental_splits.online_html || "").trim() ? (
                                          <div className="space-y-1">
                                            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                                              Online learning activities
                                            </p>
                                            <CurriculumRichHtml
                                              className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                                              html={(seg.experimental_splits.online_html || "").trim()}
                                            />
                                          </div>
                                        ) : null}
                                      </div>
                                    </details>
                                  ) : null}
                                  <CurriculumRichHtml
                                    className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                                    html={(seg.lesson_in_action_html || "").trim()}
                                  />
                                </div>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      </section>
                    ) : null}
                    {selectedLessonHasScienceBook && (
                      <section
                        id="science-book"
                        ref={scienceBookSectionRef}
                        className="space-y-4 scroll-mt-20"
                        aria-label="Science student workbook"
                      >
                        <div className="border-t border-border pt-6 mt-2" />
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-amber-800 dark:text-amber-200">
                          <BookCopy className="w-5 h-5 shrink-0" />
                          Science Book
                        </h3>
                        <p className="text-xs text-muted-foreground leading-relaxed">
                          Plain text from the Inspire Grade 2 student workbook PDF (aligned by lesson
                          title; complement to the teacher plan, not a second source of truth).
                        </p>
                        {bookPageExtractsBundle.length === 0 ? (
                          <p className="text-sm text-muted-foreground italic">
                            No workbook pages linked for this lesson yet. After running{' '}
                            <code className="rounded bg-muted px-1 py-0.5 text-xs">
                              ingest_g2_science_book_pdf.py
                            </code>
                            , open the lesson again (or hard-refresh the app).
                          </p>
                        ) : (
                          <div className="space-y-3">
                            {bookPageExtractsBundle.map((ex) => (
                              <details
                                key={ex.id}
                                className="rounded-lg border border-amber-200/70 dark:border-amber-900/40 bg-amber-50/30 dark:bg-amber-950/20 px-3 py-2"
                                open={bookPageExtractsBundle.length <= 3}
                              >
                                <summary className="cursor-pointer list-none font-medium text-sm text-foreground flex flex-wrap items-baseline gap-x-2 gap-y-1 [&::-webkit-details-marker]:hidden">
                                  <span className="underline-offset-2 group-open:underline">
                                    PDF page {ex.page_number}
                                  </span>
                                  {ex.alignment_ambiguous ? (
                                    <span className="text-xs font-normal text-amber-700 dark:text-amber-300">
                                      ambiguous alignment
                                    </span>
                                  ) : null}
                                  <span className="text-xs font-normal text-muted-foreground">
                                    {ex.alignment_confidence} confidence
                                  </span>
                                </summary>
                                <pre className="mt-3 whitespace-pre-wrap text-xs text-muted-foreground font-sans border-t border-border/60 pt-3 max-h-[min(70vh,520px)] overflow-y-auto leading-relaxed">
                                  {ex.body_text}
                                </pre>
                              </details>
                            ))}
                          </div>
                        )}
                      </section>
                    )}
                    {(!hideTeacherObjectivesForEla || !hideStudentObjectivesForEla) &&
                      !hideObjectivesWhenScienceStructured && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      {!hideTeacherObjectivesForEla && (
                      <section className="space-y-3">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-blue-600">
                          <FileText className="w-5 h-5" />
                          Teacher Objectives
                        </h3>
                        <CurriculumRichHtml
                          className="prose prose-sm max-w-none text-muted-foreground rich-html"
                          html={lessonFieldHtmlFromJsonOrHtml(
                            selectedLesson.learning_intentions,
                            "No specific intentions provided.",
                          )}
                        />
                      </section>
                      )}

                      {!hideStudentObjectivesForEla && (
                      <section className="space-y-3">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-green-600">
                          <ChevronRight className="w-5 h-5" />
                          Student Objectives
                        </h3>
                        <CurriculumRichHtml
                          className="prose prose-sm max-w-none text-muted-foreground rich-html"
                          html={studentObjectivesHtml(
                            selectedLesson.objectives_student,
                            selectedLesson.success_criteria,
                            "No student-facing objectives provided.",
                          )}
                        />
                      </section>
                      )}
                    </div>
                    )}

                    {selectedLesson.mlr && (
                      <section className="bg-primary/5 p-4 rounded-xl border border-primary/20 space-y-2">
                        <h3 className="flex items-center gap-2 font-bold text-sm text-primary uppercase tracking-tight">
                          <Languages className="w-4 h-4" />
                          Mathematical Language Routine (MLR)
                        </h3>
                        <CurriculumRichHtml
                          className="prose prose-sm max-w-none text-foreground font-medium rich-html"
                          html={selectedLesson.mlr}
                        />
                      </section>
                    )}

                    {selectedLesson.purpose && (
                      <section className="space-y-3">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-orange-500">
                          <BookOpen className="w-5 h-5" />
                          Lesson Purpose
                        </h3>
                        <CurriculumRichHtml
                          className="prose prose-sm max-w-none text-muted-foreground rich-html italic"
                          html={selectedLesson.purpose || "No purpose provided."}
                        />
                      </section>
                    )}

                    {!hideDailyTasksBandForEla && (
                    <section className="space-y-3">
                      <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2">
                        <Info className="w-5 h-5 text-green-500" />
                        Daily Tasks & Procedure
                      </h3>
                      <CurriculumRichHtml
                        className="prose prose-sm max-w-none text-muted-foreground rich-html"
                        html={
                          selectedLesson.daily_instructional_task ||
                          (selectedLesson.procedure_html
                            ? "See detailed steps below."
                            : "No task details provided.")
                        }
                      />
                    </section>
                    )}

                    {selectedLesson.success_criteria &&
                      !hideStandaloneSuccessCriteriaForEla &&
                      !hideStandaloneSuccessCriteriaForScience && (
                      <section className="space-y-3">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-yellow-600">
                          <ChevronRight className="w-5 h-5" />
                          Success Criteria
                        </h3>
                        <div className="prose prose-sm max-w-none text-muted-foreground whitespace-pre-wrap italic">
                          {selectedLesson.success_criteria}
                        </div>
                      </section>
                    )}

                    {selectedLesson.essential_questions && (
                      <section className="space-y-3">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-purple-600">
                          <Layers className="w-5 h-5" />
                          Essential Questions
                        </h3>
                        <div className="prose prose-sm max-w-none text-muted-foreground whitespace-pre-wrap">
                          {selectedLesson.essential_questions}
                        </div>
                      </section>
                    )}

                    {(lessonStandards.length > 0 || (selectedLesson.standards_structured || "").trim()) &&
                      !hideStandardsSectionForElaStructured &&
                      (() => {
                      const structuredFromDb = parseStructuredStandards(selectedLesson.standards_structured);
                      const sections = structuredFromDb.length > 0
                        ? structuredFromDb
                        : groupLessonStandards(lessonStandards);
                      const leftSections = sections.filter((s) => s.panel === "left");
                      const rightSections = sections.filter((s) => s.panel === "right");
                      const renderStandardItems = (items: StructuredStandardItem[]) => (
                        <ul className="space-y-3 text-sm text-muted-foreground list-none pl-0">
                          {items.map((item, idx) => (
                            <li key={`${item.code}-${idx}`} className="border-l-2 border-slate-200 pl-3">
                              <div className="font-mono text-xs font-semibold text-foreground">{item.code}</div>
                              {item.description_lines.map((line, lineIdx) => (
                                <p key={`${item.code}-${idx}-d-${lineIdx}`} className="mt-1 leading-relaxed">{line}</p>
                              ))}
                            </li>
                          ))}
                        </ul>
                      );
                      return (
                      <section className="space-y-3">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-slate-600">
                          <Book className="w-5 h-5" />
                          Standards
                        </h3>
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                          <div className="space-y-4 p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                            {leftSections.map((section) => (
                              <div key={`left-${section.section}`} className="space-y-1">
                                <h4 className="font-semibold text-sm text-slate-800">{section.section}</h4>
                                {renderStandardItems(section.items)}
                              </div>
                            ))}
                          </div>
                          <div className="space-y-4 p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                            {rightSections.map((section) => (
                              <div key={`right-${section.section}`} className="space-y-1">
                                <h4 className="font-semibold text-sm text-slate-800">{section.section}</h4>
                                {renderStandardItems(section.items)}
                              </div>
                            ))}
                          </div>
                        </div>
                      </section>
                    )})()}

                    {selectedLesson.narrative_html ? (
                      <section className="space-y-3">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-indigo-500">
                          <BookOpen className="w-5 h-5" />
                          Lesson Narrative / Purpose
                        </h3>
                        <CurriculumRichHtml
                          className="prose prose-sm max-w-none text-muted-foreground rich-html"
                          html={selectedLesson.narrative_html}
                        />
                      </section>
                    ) : selectedLesson.lesson_narrative && (
                      <section className="space-y-3">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-indigo-500">
                          <BookOpen className="w-5 h-5" />
                          Lesson Narrative / Purpose
                        </h3>
                        <div className="prose prose-sm max-w-none text-muted-foreground whitespace-pre-wrap leading-relaxed">
                          {selectedLesson.lesson_narrative}
                        </div>
                      </section>
                    )}

                    {showStreamedProcedureHtml ? (
                      <section className="space-y-4">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-rose-500">
                          <Clock className="w-5 h-5" />
                          Instructional Steps & Activities
                        </h3>
                        {procedureSections.length > 0 ? (
                          <div className="space-y-5">
                            {procedureSections.map((sec, idx) => {
                              const ui = procedureHeaderUi[sec.kind];
                              const Icon = ui.icon;
                              return (
                                <div key={`${sec.title}-${idx}`} className={`rounded-xl border p-4 ${ui.cardClass}`}>
                                  <div className={`flex items-center gap-2 font-bold text-sm mb-3 ${ui.titleClass}`}>
                                    <Icon className={`w-4 h-4 ${ui.iconClass}`} />
                                    {sec.title}
                                  </div>
                                  <CurriculumRichHtml
                                    className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                                    html={sec.bodyHtml}
                                  />
                                </div>
                              );
                            })}
                          </div>
                        ) : (
                          <CurriculumRichHtml
                            className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                            html={selectedLesson.procedure_html}
                          />
                        )}
                      </section>
                    ) : !skipMathProcedureBanding ? (() => {
                      try {
                        const procedures = JSON.parse(selectedLesson.procedure || "[]");
                        if (!Array.isArray(procedures) || procedures.length === 0) return null;
                        return (
                          <section className="space-y-4">
                            <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-rose-500">
                              <Clock className="w-5 h-5" />
                              Instructional Steps & Activities
                            </h3>
                            <div className="space-y-6">
                              {procedures.map((p: any, idx: number) => {
                                const isNote = p.name.includes("Note for Building Thinking Classrooms");
                                const isAccess = p.name.includes("Access for");
                                
                                return (
                                  <div 
                                    key={idx} 
                                    className={`p-4 rounded-xl border transition-all ${
                                      isNote ? 'bg-blue-50/50 border-blue-100' : 
                                      isAccess ? 'bg-amber-50/50 border-amber-100 text-amber-900' :
                                      'bg-muted/30 border-muted/50'
                                    }`}
                                  >
                                    <h4 className={`font-bold text-sm mb-2 flex items-center gap-2 ${
                                      isNote ? 'text-blue-700' : 
                                      isAccess ? 'text-amber-700' : 
                                      'text-foreground'
                                    }`}>
                                      {!isNote && !isAccess && (
                                        <span className="flex items-center justify-center w-5 h-5 rounded-full bg-rose-100 text-rose-600 text-[10px]">{idx + 1}</span>
                                      )}
                                      <Info className="w-4 h-4" />
                                      {p.name}
                                    </h4>
                                    <div className={`text-sm whitespace-pre-wrap pl-6 border-l-2 ${
                                      isNote ? 'border-blue-200 text-blue-900/80' : 
                                      isAccess ? 'border-amber-200 text-amber-900/80' : 
                                      'border-rose-100/50 text-muted-foreground'
                                    }`}>
                                      {p.content}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </section>
                        );
                      } catch (e) {
                        return null;
                      }
                    })() : null}
                  </div>

                  {/* Right: Resources & Vocabulary */}
                  <div className="space-y-10">
                    {(selectedLesson.source_url ||
                      selectedLesson.ingested_at ||
                      selectedLesson.ingest_run_id ||
                      selectedLesson.ingest_parser_version ||
                      selectedLesson.source_doc_id) && (
                      <section className="space-y-4">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-slate-600">
                          <Info className="w-5 h-5" />
                          Source Metadata
                        </h3>
                        <div className="text-xs bg-slate-50/60 border border-slate-200 rounded-xl p-4 space-y-2">
                          {selectedLesson.source_url && (
                            <SourceUrlOpenRow
                              sourceUrl={selectedLesson.source_url}
                              sourceDocId={selectedLesson.source_doc_id}
                            />
                          )}
                          {selectedLesson.source_doc_id && (
                            <div>
                              <span className="font-semibold text-slate-700">Source doc ID:</span>{" "}
                              <span>{selectedLesson.source_doc_id}</span>
                            </div>
                          )}
                          {selectedLesson.ingested_at && (
                            <div>
                              <span className="font-semibold text-slate-700">Ingested at:</span>{" "}
                              <span>{selectedLesson.ingested_at}</span>
                            </div>
                          )}
                          {selectedLesson.ingest_run_id && (
                            <div className="break-all">
                              <span className="font-semibold text-slate-700">Run ID:</span>{" "}
                              <span>{selectedLesson.ingest_run_id}</span>
                            </div>
                          )}
                          {selectedLesson.ingest_parser_version && (
                            <div>
                              <span className="font-semibold text-slate-700">Parser version:</span>{" "}
                              <span>{selectedLesson.ingest_parser_version}</span>
                            </div>
                          )}
                        </div>
                      </section>
                    )}

                    {selectedLesson.materials && (
                      <section className="space-y-4">
                        <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-yellow-600">
                          <Hammer className="w-5 h-5" />
                          Materials
                        </h3>
                        <CurriculumRichHtml
                          className="prose prose-sm max-w-none text-muted-foreground rich-html bg-yellow-50/30 p-4 rounded-xl border border-yellow-100"
                          html={selectedLesson.materials}
                        />
                      </section>
                    )}

                    {(() => {
                      const raw = (selectedLesson.instructional_resources || "").trim();
                      if (!raw) return null;
                      try {
                        const resources = JSON.parse(raw);
                        if (!Array.isArray(resources) || resources.length === 0) return null;
                        return (
                          <section className="space-y-4">
                            <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-blue-600">
                              <Link className="w-5 h-5" />
                              Resources
                            </h3>
                            <div className="grid gap-2">
                              {resources.map((res: any, idx: number) => (
                                <a 
                                  key={idx} 
                                  href={res.url} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="curriculum-resource-link flex items-center gap-2 p-3 bg-blue-50/50 rounded-lg border border-blue-100 hover:bg-blue-100 transition-colors text-xs font-medium"
                                >
                                  <Link className="w-3 h-3 shrink-0" aria-hidden />
                                  {res.label}
                                </a>
                              ))}
                            </div>
                          </section>
                        );
                      } catch {
                        return (
                          <section className="space-y-4">
                            <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-blue-600">
                              <Link className="w-5 h-5" />
                              Supplemental &amp; formative resources
                            </h3>
                            <CurriculumRichHtml
                              className="prose prose-sm max-w-none text-muted-foreground rich-html bg-blue-50/30 p-4 rounded-xl border border-blue-100"
                              html={raw}
                            />
                          </section>
                        );
                      }
                    })()}

                    <section className="space-y-6">
                      <h3 className="flex items-center gap-2 font-bold text-lg border-b pb-2 text-orange-500">
                        <Languages className="w-5 h-5" />
                        Vocabulary
                      </h3>
                      <div className="space-y-4">
                        {displayVocabulary.length === 0 ? (
                          <p className="text-xs text-muted-foreground italic">No vocabulary terms identified for this lesson.</p>
                        ) : useElaStructuredPrimary && elaVocabTermsSanitized.length > 0 ? (
                          <div className="p-4 bg-muted/40 rounded-xl border border-transparent hover:border-orange-200 transition-colors">
                            <ul className="list-disc pl-5 space-y-1">
                              {displayVocabulary.map((vocab) => (
                                <li key={vocab.term}>
                                  <span className="font-bold text-sm tracking-tight">{vocab.term}</span>
                                </li>
                              ))}
                            </ul>
                          </div>
                        ) : (
                          displayVocabulary.map((vocab) => {
                            const def = vocab.leveled_definitions?.[5]?.definition;
                            const hasGlossaryRows =
                              Array.isArray(vocab.leveled_definitions) &&
                              vocab.leveled_definitions.length > 0;
                            return (
                            <div key={vocab.term} className="p-4 bg-muted/40 rounded-xl border border-transparent hover:border-orange-200 transition-colors">
                              <div className="mb-1">
                                <span className="font-bold text-sm tracking-tight">{vocab.term}</span>
                              </div>
                              <div className="text-xs text-muted-foreground leading-relaxed">
                                {def ? def : hasGlossaryRows ? "No definition available." : null}
                              </div>
                            </div>
                            );
                          })
                        )}
                      </div>
                    </section>
                  </div>
                </div>
                </>
                )}
              </div>
            )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
