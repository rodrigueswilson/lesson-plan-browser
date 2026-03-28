import { useState, useEffect, useRef } from 'react';
import { 
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
  BookOpen
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
  source_doc_id?: string;
  source_url?: string;
  ingested_at?: string;
  ingest_run_id?: string;
  ingest_parser_version?: string;
  content_hash?: string;
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
  const safe = html ?? '';

  useEffect(() => {
    const root = ref.current;
    if (!root) return;
    root.querySelectorAll('a[href]').forEach((node) => {
      const a = node as HTMLAnchorElement;
      const href = a.getAttribute('href');
      if (!href || href.startsWith('#')) return;
      if (/^https?:\/\//i.test(href) || href.startsWith('//')) {
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
      }
    });
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

export function CurriculumExplorer() {
  const [hierarchy, setHierarchy] = useState<Grade[]>([]);
  const [expandedGrades, setExpandedGrades] = useState<Set<string>>(new Set());
  const [expandedSubjects, setExpandedSubjects] = useState<Set<string>>(new Set());
  const [selectedUnit, setSelectedUnit] = useState<Unit | null>(null);
  const [unitIntro, setUnitIntro] = useState<any>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [selectedLesson, setSelectedLesson] = useState<any>(null);
  const [showUnitIntro, setShowUnitIntro] = useState(false);
  const [vocabulary, setVocabulary] = useState<VocabularyTerm[]>([]);
  const [lessonStandards, setLessonStandards] = useState<LessonStandardRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [language, setLanguage] = useState<'en' | 'pt'>('en');
  const detailsRef = useRef<HTMLDivElement>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<
    { id: string; unit_id: string; lesson_number: number; title: string }[]
  >([]);
  const [searchLoading, setSearchLoading] = useState(false);
  const [hierarchyError, setHierarchyError] = useState<string | null>(null);

  useEffect(() => {
    fetchHierarchy();
  }, []);

  useEffect(() => {
    if (selectedLesson && detailsRef.current) {
      detailsRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' });
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
    await fetchLessons(unit);
    await fetchLessonDetails({
      id: hit.id,
      lesson_number: hit.lesson_number,
      title: hit.title,
    });
  };

  const fetchLessonDetails = async (lesson: Lesson) => {
    try {
      setLoadingDetails(true);
      console.log('Fetching details for lesson:', lesson.id);
      const resp1 = await fetch(`/api/curriculum/lessons/${lesson.id}`);
      if (!resp1.ok) throw new Error('Failed to fetch lesson details');
      const details = await resp1.json();
      setSelectedLesson(details);

      const [vocabResp, standardsResp] = await Promise.all([
        fetch(`/api/curriculum/lessons/${lesson.id}/vocabulary`),
        fetch(`/api/curriculum/lessons/${lesson.id}/standards`),
      ]);
      if (!vocabResp.ok) throw new Error('Failed to fetch vocabulary');
      const vocab = await vocabResp.json();
      setVocabulary(Array.isArray(vocab) ? vocab : []);
      if (standardsResp.ok) {
        const std = await standardsResp.json();
        setLessonStandards(Array.isArray(std) ? std : []);
      } else {
        setLessonStandards([]);
      }
      setLoadingDetails(false);
    } catch (error) {
      console.error('Error fetching lesson details:', error);
      setLoadingDetails(false);
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

  if (loading) {
    return <div className="flex items-center justify-center p-12">Loading Curriculum...</div>;
  }

  const procedureSections = splitProcedureSectionsFromHtml(selectedLesson?.procedure_html);
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
            <ul className="max-h-36 overflow-y-auto text-xs space-y-1 border border-border rounded-md p-1 bg-background">
              {searchResults.map((hit) => (
                <li key={hit.id}>
                  <button
                    type="button"
                    onClick={() => void openSearchHit(hit)}
                    className="w-full text-left px-1 py-0.5 rounded hover:bg-muted truncate"
                    title={hit.title}
                  >
                    L{hit.lesson_number}: {hit.title}
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
              <span>{grade.name}</span>
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
                        <span>{subject.name}</span>
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
                              {unit.title}
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
      <div className="flex-1 overflow-y-auto bg-card">
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
              <p className="text-lg">Select a Grade and Unit to browse lessons</p>
            )}
          </div>
        ) : (
          <div className="p-8 space-y-8 animate-in fade-in duration-500">
            {/* Unit Header */}
            <div className="space-y-2">
              <div className="flex items-center gap-2 text-primary font-semibold uppercase tracking-widest text-xs">
                <Book className="w-4 h-4" />
                <span>Unit {selectedUnit.number}</span>
              </div>
              <h1 className="text-3xl font-bold tracking-tight">{selectedUnit.title}</h1>
            </div>

            {/* Lessons Grid/List */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {unitIntro && (
                <button
                  onClick={() => {
                    setSelectedLesson(null);
                    setShowUnitIntro(true);
                  }}
                  className={`flex flex-col text-left p-4 border rounded-xl transition-all ${
                    showUnitIntro ? 'border-primary ring-1 ring-primary bg-primary/5' : 'hover:border-primary/50 hover:bg-muted/50'
                  }`}
                >
                  <span className="text-[10px] font-bold text-primary uppercase mb-1">Unit Preamble</span>
                  <span className="font-semibold text-sm">Unit Overview & TOC</span>
                </button>
              )}
              {lessons.map((lesson) => (
                <button
                  key={lesson.id}
                  onClick={() => {
                    setShowUnitIntro(false);
                    fetchLessonDetails(lesson);
                  }}
                  className={`flex flex-col text-left p-4 border rounded-xl transition-all ${
                    !showUnitIntro && selectedLesson?.id === lesson.id ? 'border-primary ring-1 ring-primary bg-primary/5' : 'hover:border-primary/50 hover:bg-muted/50'
                  }`}
                >
                  <span className="text-[10px] font-bold text-muted-foreground uppercase mb-1">Lesson {lesson.lesson_number}</span>
                  <span className="font-semibold text-sm line-clamp-2">{lesson.title}</span>
                </button>
              ))}
            </div>

            {/* Content Display (Lesson or Unit Intro) */}
            {(showUnitIntro && unitIntro) && (
              <div ref={detailsRef} className="mt-12 space-y-12 border-t pt-12 animate-in slide-in-from-bottom-4 duration-500">
                <div className="space-y-4">
                  <h2 className="text-2xl font-bold">Unit Overview</h2>
                  <CurriculumRichHtml
                    className="prose prose-sm max-w-none text-muted-foreground rich-html overflow-x-auto"
                    html={unitIntro.procedure_html}
                  />
                </div>
              </div>
            )}

            {/* Lesson Detail Pane */}
            {(selectedLesson || loadingDetails) && (
              <div ref={detailsRef} className="mt-12 space-y-12 border-t pt-12 animate-in slide-in-from-bottom-4 duration-500">
                {loadingDetails ? (
                   <div className="flex items-center justify-center py-20 text-muted-foreground animate-pulse">
                     <Book className="w-8 h-8 mr-3 animate-bounce" />
                     <p className="text-xl font-medium">Loading Lesson Content...</p>
                   </div>
                ) : (
                  <>
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <h2 className="text-2xl font-bold">{selectedLesson?.title || "Untitled Lesson"}</h2>
                      <p className="text-muted-foreground text-sm">Detailed Lesson Plan & Vocabulary</p>
                    </div>
                  
                  {/* Bilingual Toggle */}
                  <div className="flex bg-muted p-1 rounded-lg">
                    <button 
                      onClick={() => setLanguage('en')}
                      className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${language === 'en' ? 'bg-white shadow-sm text-primary' : 'text-muted-foreground'}`}
                    >
                      EN
                    </button>
                    <button 
                      onClick={() => setLanguage('pt')}
                      className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${language === 'pt' ? 'bg-white shadow-sm text-primary' : 'text-muted-foreground'}`}
                    >
                      PT
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
                  {/* Left: Content */}
                  <div className="lg:col-span-2 space-y-8">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
                    </div>

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

                    {selectedLesson.success_criteria && (
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

                    {(lessonStandards.length > 0 || (selectedLesson.standards_structured || "").trim()) && (() => {
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

                    {selectedLesson.procedure_html ? (
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
                    ) : (() => {
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
                    })()}
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
                            <div className="break-all">
                              <span className="font-semibold text-slate-700">Source URL:</span>{" "}
                              <a
                                href={selectedLesson.source_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-blue-700 underline"
                              >
                                {selectedLesson.source_url}
                              </a>
                            </div>
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
                        {vocabulary.length === 0 ? (
                          <p className="text-xs text-muted-foreground italic">No vocabulary terms identified for this lesson.</p>
                        ) : (
                          vocabulary.map((vocab) => (
                            <div key={vocab.term} className="p-4 bg-muted/40 rounded-xl border border-transparent hover:border-orange-200 transition-colors">
                              <div className="flex justify-between items-center mb-1">
                                <span className="font-bold text-sm tracking-tight">{vocab.term}</span>
                                <span className="text-[10px] font-bold text-orange-600 uppercase bg-orange-100 px-2 py-0.5 rounded-full">
                                  {language === 'en' ? 'English' : 'Português'}
                                </span>
                              </div>
                              <div className="text-xs text-muted-foreground leading-relaxed">
                                {language === 'en' 
                                  ? vocab.leveled_definitions?.[5]?.definition || "No definition available."
                                  : vocab.translated_term + ": " + (vocab.leveled_definitions?.[5]?.definition_pt || "Sem definição disponível.")
                                }
                              </div>
                            </div>
                          ))
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
        )}
      </div>
    </div>
  );
}
