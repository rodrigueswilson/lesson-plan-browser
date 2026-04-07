/**
 * Post-process trusted curriculum HTML so section labels inside one <p> or <li> (joined by <br>)
 * render bold like the source DOCX, with extra top margin when a label follows body text.
 *
 * DOCX often emits "Label: body" in a single HTML segment. Known headers must only bold the
 * prefix through the first ":"; body text stays normal weight.
 *
 * Matching pitfalls (see MDN / Stack Overflow on regex `^` and DOCX spacing):
 * - A BOM (U+FEFF) or odd Unicode spaces (NBSP U+00A0, narrow NBSP U+202F, etc.) between words
 *   break patterns anchored with `^` or literal ASCII spaces unless normalized.
 * - `json_to_html` uses <li> for Word list paragraphs, not <p>; title enrichment must run on
 *   both or those sections never match.
 */

const BR_SPLIT = /<br\s*\/?>/gi;

/** BOM + space_separators often seen in Word/DOCX round-trips; normalize before title regex. */
const UNICODE_SPACE_LIKE = /[\uFEFF\u00A0\u202F\u2007\u2009\u200A\u3000]/g;

/**
 * Leading phrases treated as in-cell section headers when followed by ":" in plain text.
 */
const KNOWN_HEADER =
  /^(Learning Intentions?|Instructional Routines and Assessments|Anticipatory Set|Learning Procedures|Daily Instructional Task|Anticipated Student Response|Engagement with the Content|Key Questions|Instructional Resources|Vocabulary|Differentiation|Addressing Misconceptions|NJSLS Standards?|Priority Standards|Supporting Standards|Read Aloud|Guided Practice|Independent Practice|Closing|Assessment|Warm-?up|Do Now|Focus Lesson|Modeling|Practice|Reflection|Homework|Extension)\b/i;

/** Teacher-facing notes: italic label through ":", not bold (matches source DOCX). */
const TEACHER_NOTE_HEADER = /^Teacher Notes?\b/i;
const STANDARDS_TOKEN =
  /\b(?:[A-Z]{1,4}\.[A-Z]{1,4}\.[0-9A-Za-z.\-]+|[0-9]+\.[0-9]+\.[0-9A-Za-z.\-]+)\b/g;

function plainOneLine(html: string): string {
  return html
    .replace(BR_SPLIT, " ")
    .replace(/<[^>]+>/g, "")
    .replace(UNICODE_SPACE_LIKE, " ")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/^\uFEFF+/, "");
}

function alreadyEnrichedInlineLabel(seg: string): boolean {
  return (
    /class\s*=\s*["'][^"']*rich-inline-title/i.test(seg) ||
    /class\s*=\s*["'][^"']*rich-inline-teacher-note/i.test(seg)
  );
}

/** Index in plain text of the ":" that ends the header (after optional space). */
function colonPlainIndexAfterKnownHeader(plain: string, headerMatch: RegExpExecArray): number {
  const len = headerMatch[0].length;
  let i = len;
  while (i < plain.length && /\s/.test(plain[i])) i++;
  if (i < plain.length && plain[i] === ":") return i;
  return plain.indexOf(":", len);
}

/**
 * Split HTML segment so plain-text char at `colonPlainIdx` is ':' (0-based index of ':' in plain).
 */
function splitHtmlAtPlainColonIndex(seg: string, colonPlainIdx: number): [string, string] | null {
  let seen = 0;
  let idx = 0;
  while (idx < seg.length) {
    if (seg[idx] === "<") {
      const end = seg.indexOf(">", idx);
      if (end === -1) return null;
      idx = end + 1;
      continue;
    }
    if (seen === colonPlainIdx) {
      if (seg[idx] === ":") return [seg.slice(0, idx + 1), seg.slice(idx + 1)];
      return null;
    }
    seen += 1;
    idx += 1;
  }
  return null;
}

function titleClass(spaced: boolean): string {
  return spaced ? "rich-inline-title rich-inline-title-spaced" : "rich-inline-title";
}

function teacherNoteClass(spaced: boolean): string {
  return spaced
    ? "rich-inline-teacher-note rich-inline-title-spaced"
    : "rich-inline-teacher-note";
}

/**
 * Italic label through first ":"; body unchanged (same split rules as bold headers).
 */
function enrichTeacherNoteSegment(seg: string, plain: string, spaced: boolean): string | null {
  const m = TEACHER_NOTE_HEADER.exec(plain);
  if (!m) return null;

  const cidx = colonPlainIndexAfterKnownHeader(plain, m);
  if (cidx < 0 || plain[cidx] !== ":") return null;

  const afterColon = plain.slice(cidx + 1).trim();
  const cls = teacherNoteClass(spaced);

  if (!afterColon) {
    return `<em class="${cls}">${seg.trim()}</em>`;
  }

  const split = splitHtmlAtPlainColonIndex(seg, cidx);
  if (!split) return null;
  const [before, after] = split;
  return `<em class="${cls}">${before.trim()}</em>${after}`;
}

/**
 * If plain starts with a known header + ":", bold only through that colon when body follows;
 * if nothing after ":", bold the whole segment.
 */
function enrichKnownHeaderSegment(seg: string, plain: string, spaced: boolean): string | null {
  const m = KNOWN_HEADER.exec(plain);
  if (!m) return null;

  const cidx = colonPlainIndexAfterKnownHeader(plain, m);
  if (cidx < 0 || plain[cidx] !== ":") return null;

  const afterColon = plain.slice(cidx + 1).trim();
  const cls = titleClass(spaced);

  if (!afterColon) {
    return `<strong class="${cls}">${seg.trim()}</strong>`;
  }

  const split = splitHtmlAtPlainColonIndex(seg, cidx);
  if (!split) return null;
  const [before, after] = split;
  return `<strong class="${cls}">${before.trim()}</strong>${after}`;
}

/** Lines that are only a short colon-ending label (not handled as known-header body case). */
function isStandaloneColonTitleLine(plain: string): boolean {
  const t = plain.trim();
  if (!t || t.length > 220) return false;
  if (/https?:\/\//i.test(t) || /:\/\/\S/.test(t)) return false;
  if (KNOWN_HEADER.test(t)) return false;
  if (TEACHER_NOTE_HEADER.test(t)) return false;
  const standardsMatches = t.match(STANDARDS_TOKEN) ?? [];
  // Standards/code-only bullets often end with ":" but should stay normal text.
  if (standardsMatches.length >= 2 && t.includes(",")) return false;
  return t.length >= 4 && t.length <= 150 && t.endsWith(":");
}

function processBlockInner(inner: string): string {
  const segments = inner.split(BR_SPLIT);
  const out: string[] = [];
  let prevSubstantial = false;

  for (let i = 0; i < segments.length; i++) {
    const seg = segments[i];
    const plain = plainOneLine(seg);
    const substantial = plain.length > 0;

    if (substantial && !alreadyEnrichedInlineLabel(seg)) {
      const spaced = i > 0 && prevSubstantial;
      const teacher = enrichTeacherNoteSegment(seg, plain, spaced);
      if (teacher) {
        out.push(teacher);
        prevSubstantial = true;
        continue;
      }

      const known = enrichKnownHeaderSegment(seg, plain, spaced);
      if (known) {
        out.push(known);
        prevSubstantial = true;
        continue;
      }

      const alreadyBold =
        /^\s*<(?:strong|b)\b/i.test(seg.trim()) && /<\/(?:strong|b)>\s*$/i.test(seg.trim());
      if (alreadyBold) {
        out.push(seg);
        prevSubstantial = true;
        continue;
      }

      if (isStandaloneColonTitleLine(plain)) {
        out.push(`<strong class="${titleClass(spaced)}">${seg.trim()}</strong>`);
        prevSubstantial = true;
        continue;
      }
    }

    out.push(seg);
    prevSubstantial = substantial;
  }

  return out.join("<br>");
}

function replaceBlockInner(
  html: string,
  tag: "p" | "li",
  process: (inner: string) => string,
): string {
  const re =
    tag === "p"
      ? /<p(\s[^>]*)?>([\s\S]*?)<\/p>/gi
      : /<li(\s[^>]*)?>([\s\S]*?)<\/li>/gi;
  return html.replace(re, (_full, attrs: string, inner: string) => {
    const a = attrs ?? "";
    return `<${tag}${a}>${process(inner)}</${tag}>`;
  });
}

/**
 * Enriches br-separated title lines inside <p> and <li> (Word bullets → li, body → p).
 */
export function enrichRichHtmlInlineTitles(html: string): string {
  if (!html || !html.includes("<")) return html;
  let out = replaceBlockInner(html, "p", processBlockInner);
  out = replaceBlockInner(out, "li", processBlockInner);
  return out;
}
