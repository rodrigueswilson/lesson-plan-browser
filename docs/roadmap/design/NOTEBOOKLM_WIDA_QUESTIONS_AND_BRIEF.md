# NotebookLM: Questions and Brief for WIDA Documents

Use this when you have uploaded WIDA documents (e.g. Can Do Key Uses Edition PDFs, ELD Standards Framework 2020 grade-cluster PDFs, Language Charts, or Standards FAQ) into [NotebookLM](https://notebooklm.google.com). Paste the **Brief** first to set context, then use the **Questions** to deepen your understanding and get concrete ideas for conversion.

**Project NotebookLM notebook (for future reference):** [https://notebooklm.google.com/notebook/bfdba55b-931b-495b-9ef1-7b30713d5eb0](https://notebooklm.google.com/notebook/bfdba55b-931b-495b-9ef1-7b30713d5eb0) — use this link to open the notebook when adding sources (e.g. Can Do Original, 2020 ELD, Language Charts) or asking follow-up questions; capture any new answers in the synthesis sections below.

---

## NotebookLM synthesis (captured from conversation)

After pasting the brief and asking follow-up questions, NotebookLM provided the following. This is the single captured synthesis in this repo; details are reflected in [WIDA_FRAMEWORK_INGESTION_AND_USE.md](./WIDA_FRAMEWORK_INGESTION_AND_USE.md) and the reference_docs READMEs.

### (a) Structure of the two WIDA document types

**1. Can Do Descriptors (Key Uses Edition)**

- **Grade-level bands:** K, 1, 2–3, 4–5, 6–8, 9–12.
- **Key Uses:** Recount, Explain, Argue, **Discuss** (not Narrate/Inform). In the 2020 ELD Framework, "Recount" was split into Narrate and Inform; "Discuss" is no longer a standalone Key Use there but is threaded throughout.
- **Domains:** For Recount, Explain, and Argue: all four domains (Listening, Reading, Speaking, Writing). For **Discuss:** only Listening and Speaking (oral language focus).
- **Proficiency levels:** Six levels (Entering, Emerging, Developing, Expanding, Bridging, Reaching) within each domain.

**2. ELD Standards Framework (2020 Edition)**

- **Grade-level clusters:** K, 1, 2-3, 4-5, 6-8, 9-12.
- **Standards (subjects):** Standard 1 (Social/Instructional), 2 (Language Arts), 3 (Mathematics), 4 (Science), 5 (Social Studies).
- **Key Language Uses:** Narrate, Inform, Explain, Argue.
- **Communication modes:** The four domains are consolidated into two modes. **Interpretive** = listening, reading, viewing; **Expressive** = speaking, writing, representing.
- **Language Expectations** (Interpretive and Expressive) with **Language Functions** and **Language Features**.
- **Proficiency Level Descriptors (PLDs):** Six proficiency levels; three dimensions: Discourse, Sentence, Word/Phrase.

**App logic:** The app UI can keep "domains" (Listening, Reading, Speaking, Writing) for teacher familiarity. The backend must map **Listening + Reading → Interpretive** and **Speaking + Writing → Expressive** when querying the 2020 Standards (and PLDs).

### (b) Conversion options (from NotebookLM)

- **Option 1 – Relational DB:** Three tables: `Can_Do_Descriptors` (grade_cluster, key_use, domain, proficiency_level, descriptor_text); `WIDA_2020_Language_Expectations` (grade_cluster, standard_subject, key_language_use, communication_mode, language_functions, language_features); `WIDA_2020_PLDs` (grade_cluster, communication_mode, language_dimension, proficiency_level, descriptor_text). Query by grade, subject, key_use, and mode (derived from domain) so the LLM gets only the matching rows.
- **Option 2 – Markdown with YAML frontmatter:** One file per Grade Cluster + Subject + Key Use (e.g. `WIDA_Grade2-3_Science_Explain.md`). Frontmatter: `grade_cluster`, `standard`, `key_language_use`, `modes`, `mapped_domains`. Body: Language Expectations (by mode) and Can Do descriptors (by domain). Retrieval by metadata; inject the single file for the slot into the LLM.

### (c) Structure and chunking details (from Q1–4)

**2020 Framework document layout**

- Four main sections: Section 1 Big Ideas, Section 2 Understanding the Framework, Section 3 Grade-Level Cluster Materials, Section 4 Resources. **Section 3** holds the grade-level materials (K, 1, 2-3, 4-5, 6-8, 9-12).
- Under each Key Use (e.g. Inform), content is split into **Interpretive** and **Expressive** subsections (side-by-side or stacked).

**Can Do Key Uses Edition – hierarchy, table layout, and slice boundaries**

- **Exact hierarchy:** **Key Use first, then domain.** Outermost vertical label on the far left = Key Use (e.g. "KEY USE OF RECOUNT"); nested to the right = domain (e.g. "READING"). Discuss is labeled **"ORAL LANGUAGE"** in the document (Listening + Speaking only).
- **Table layout:** Within each Key Use + domain, **domain = row**, **proficiency levels = columns.** Each row has six cells (one per ELP level). Column headers are consistent across grade clusters: **ELP Level 1 Entering**, **ELP Level 2 Emerging**, **ELP Level 3 Developing**, **ELP Level 4 Expanding**, **ELP Level 5 Bridging**, **ELP Level 6 Reaching**.
- **Slice boundaries (for parsing):**  
  - **Grade cluster:** Top corner of page or table header (e.g. "2-3", "4-5", "K").  
  - **Key Use (outer block):** Large all-caps vertical text on far-left margin ("KEY USE OF RECOUNT", etc.). A single Key Use often spans two pages; the vertical label repeats on the next page with a new table.  
  - **Table start:** Row of six ELP Level column headers marks the start of a new set of slices.  
  - **Domain (inner block / slice start):** Second vertical text block to the right of the Key Use label (LISTENING, SPEAKING, READING, WRITING, or ORAL LANGUAGE). Start of this block = start of the row (one slice = one row = six descriptor cells).  
  - **Slice end:** Next vertical domain label, or bottom of table/page.

**2020 Framework – presentation of Key Language Uses and mode split**

- **Primary organizer:** Within each grade cluster and ELD Standard, **Key Language Uses (Narrate, Argue, Inform, Explain)** are the primary organizing principle. Prominent headings for each Key Use (e.g. **Inform**, **Narrate**). Under each Key Use heading: **Language Expectations** first, then **Language Functions and Sample Language Features**. Standard 1 provides Language Expectations per Key Use but **no specific Language Features** (interwoven with Standards 2–5).
- **Split by mode, not domain:** Content under a Key Use is split by **communication mode (Interpretive vs. Expressive)**, not by the four domains. Marked in two ways: (1) **Reference code** ends in `.Interpretive` or `.Expressive`; (2) **Action labels** in the text: e.g. "Interpret informational texts… by" (Interpretive) vs. "Construct informational texts… that" (Expressive). Language Features appear only under Expressive.

**2020 Framework – reference codes as keys**

- **Pattern:** `Standard.GradeCluster.KeyUse.Mode` — e.g. `ELD-LA.2-3.Narrate.Expressive` decodes to: Standard = ELD-LA (Language Arts), Grade cluster = 2-3, Key Use = Narrate, Mode = Expressive. Codes are consistent and unique.
- **Use as keys:** Ideal as **primary keys** in the database or **file names** in a Markdown index (e.g. `ELD-LA_2-3_Narrate_Expressive.md`). Parse the PDF by searching for this string pattern; split on periods to populate columns or YAML metadata (`standard`, `grade_cluster`, `key_use`, `mode`). **Backend retrieval:** When a teacher configures a slot (e.g. Grade 2 Language Arts, Narrate, Writing), map "Writing" → Expressive, build `ELD-LA.2-3.Narrate.Expressive`, and fetch only that chunk for the LLM.

**Language Expectations, Functions, and Features (2020 only)**

- **Language Expectations:** Under each Key Use, split by Interpretive and Expressive; each has a Reference Code.
- **Language Functions:** Bulleted lists (●) directly under Interpretive and Expressive Language Expectations.
- **Language Features:** Marked with a square box (■) under the associated Language Functions.
- **Rules:** Language Features are **only** provided for the **Expressive** mode (educators evaluate expressive output). **Standard 1 (Social and Instructional)** does *not* contain specific Language Features; it is meant to be interwoven with the other standards.

### (d) Markdown naming, database columns, boilerplate, and pitfalls (from Q11–14)

**Markdown naming and content**

- **2020 ELD:** File name = reference code with underscores: `[Standard]_[GradeCluster]_[KeyUse]_[Mode].md` (e.g. `ELD-LA_2-3_Narrate_Expressive.md`). YAML frontmatter: standard, grade_cluster, key_use, mode. Body: overarching Language Expectation statement; list of Language Functions; under each Function, associated Language Features (if applicable).
- **Can Do Key Uses Edition:** `CanDo_[GradeCluster]_[KeyUse]_[Domain].md` (e.g. `CanDo_2-3_Explain_Speaking.md`). YAML: grade_cluster, key_use, domain. Body: six ELP level descriptors (Level 1 Entering through Level 6 Reaching) for that grade, use, and domain.

**Database columns (suggested)**

- **Table `wida_2020_expectations`:** `id` / `reference_code` (PK, e.g. "ELD-LA.2-3.Inform.Expressive"), `grade_cluster`, `standard` (ELD-SI, ELD-LA, ELD-MA, ELD-SC, ELD-SS), `key_language_use`, `mode`, `expectation_text`, `language_functions` (JSON array or related table), `language_features` (JSON array or related table).
- **Table `wida_can_do_descriptors`:** `grade_cluster`, `key_use` (Recount, Explain, Argue, Discuss), `domain` (Listening, Speaking, Reading, Writing, or Oral Language), `level_1_entering`, `level_2_emerging`, `level_3_developing`, `level_4_expanding`, `level_5_bridging`, `level_6_reaching` (each Text).

**Boilerplate to store once**

- **Standard 1:** Language Expectations for Standard 1 are identical for K–3 and identical for 4–12; no Language Features. Store once, link by ID.
- **PLDs (2020):** One set per grade cluster (not per standard or Key Use). Store one set of PLDs per grade cluster.
- **Key Language Use definitions:** Definitions for Narrate, Inform, Explain, Argue are consistent across grades and disciplines; store once.

**Pitfalls when extracting**

- **2020 side-by-side layout:** Interpretive and Expressive are often two columns. A left-to-right scraper can merge them; extract by mode (e.g. by Reference Code) to keep Interpretive and Expressive separate.
- **Null Language Features:** Expressive-only; Standard 1 has none. Handle null/empty `language_features` without breaking.
- **Symbol-based lists (2020):** Functions = bullet (●), Features = square (■) nested under Functions. Parser must distinguish symbols to keep Functions vs. Features and parent-child correct.
- **Discuss (Can Do):** Discuss has a single row "Oral Language", not four domain rows. Table layout differs; scraper must not assume four rows per Key Use.
- **Page-spanning tables (Can Do):** Key Use vertical label repeats on the next page. Merge rows across the break; do not treat the new page as a new Key Use.
- **Annotated Language Samples:** Do not scrape as raw text; they depend on visual cues (colored backgrounds, underlines, arrows). Text-only extraction strips meaning.
- **Footnotes (Can Do):** Repeating footnote (e.g. "*Except for Level 6, for which there is no ceiling") must not be appended to descriptor text (e.g. Level 1).

### (e) Retrieval path example, Language Charts, and balance (from Q15–17)

**Concrete retrieval: "Grade 2, ELA, Inform, Writing"**

- **Can Do (Grades 2-3 PDF):** Can Do uses Recount, Explain, Argue, Discuss (no "Inform"). Map **Inform to Recount** (2020 split Recount into Narrate and Inform). Path: **KEY USE OF RECOUNT** then row **WRITING** for the six ELP level descriptors.
- **2020 ELD:** Grades 2-3, **Standard 2 (Language for Language Arts)**, Key Use **Inform**, **Expressive** (Writing = Expressive). Fetch slice with Reference Code `ELD-LA.2-3.Inform.Expressive` (Language Expectations, Language Functions, Language Features).

**Key-use mapping for Can Do:** When the app uses 2020 Key Uses (Narrate, Inform, Explain, Argue), the backend must map **Narrate and Inform to Recount** when querying the Can Do Key Uses Edition.

**Language Charts / PLD charts**

- The specific "WIDA Language Charts" may not be in every source set; sources may include **Features of Academic Language Chart** (2014) and **Dimensions of Language Table** (2020) with PLDs.
- They add a **rubric layer**: Can Do and ELD give task- and vocabulary-specific content per lesson; PLD charts describe how language complexity scales across **Discourse, Sentence, Word/Phrase**. Storing them allows retrieval of "what output looks like at Level 2 vs Level 5" regardless of Key Use or subject.

**Balance (WIDA guidance)**

- WIDA **does not mandate** a specific formula or balance of domains or Key Uses per week or unit. The framework "does not prescribe a specific curriculum, pedagogy, or teaching methodology."
- Educators are advised to identify the **"most prominent Key Language Uses"** that align with the unit's academic content standards, essential questions, and main learning events. All Key Uses appear across grades and disciplines; priority depends on the lesson. **Flexible tagging** (e.g. query "Writing descriptors for Inform") is the right approach so teachers retrieve the expectations that support their chosen content for that slot.

### (f) Can Do Descriptors Original Edition (from NotebookLM, domain-only source)

**Organization:** **Grade cluster first, then domain.** Under each cluster: sequential subsections for Listening, Speaking, Reading, Writing (in that order), then the document moves to the next cluster. No Key Uses layer.

**Grade bands:** PreK-K, 1-2, 3-5, 6-8, 9-12. Consistent heading: `Can Do Descriptors: Grade Level Cluster [Band]`.

**Proficiency levels:** Six levels as **column headers**: Level 1 Entering, **Level 2 Beginning** (Original uses "Beginning"; Key Uses Edition uses "Emerging"), Level 3 Developing, Level 4 Expanding, Level 5 Bridging, Level 6 Reaching. Store with the correct label per edition when building the database.

**Slice boundaries (one slice per grade cluster, domain):**

- **Start of grade cluster:** Heading `Can Do Descriptors: Grade Level Cluster [Band]`.
- **Start of domain (slice):** Large all-caps **vertical text** on far-left margin (LISTENING, SPEAKING, READING, WRITING). Often with prompt "Write in grade-level [Domain] expectations below:".
- **End of slice:** Next vertical domain label, or next Grade Level Cluster heading.

**Boilerplate to strip (Original is a fill-in chart for teachers):**

- Introductory sentence: *"For the given level of English language proficiency and with visual, graphic, or interactive support through Level 4, English language learners can process or produce the language needed to:"*.
- WIDA framework explanation: the Can Do Descriptors "work in conjunction with" the **WIDA Performance Definitions of the English language proficiency standards**. Performance Definitions describe *quality and quantity* of language (vs Can Do, which describes *what* tasks students can do). They use **three criteria:** Linguistic complexity, Vocabulary usage, Language control—the original iterations of the 2020 PLD dimensions (Discourse, Word/Phrase, Sentence). **Official source:** WIDA hosts the **Receptive** (Listening and Reading) Performance Definitions at [Performance Definitions – Receptive Domains, Grades K–12](https://wida.wisc.edu/sites/default/files/resource/Performance-Definitions-Receptive-Domains.pdf). A separate **Expressive** (Speaking and Writing) Performance Definitions document exists; obtain from WIDA if needed.
- Teacher input prompts: empty boxes with *"Write in grade-level [Domain] expectations below:"*.
- **NAMES** column (vertical label with empty space for student names).

**Markdown naming and content (Original):**

- **File naming:** `CanDo-Original_[GradeCluster]_[Domain].md` (e.g. `CanDo-Original_1-2_Writing.md`).
- **YAML frontmatter:** `framework: "Can Do Descriptors Original"`, `grade_cluster`, `domain`.
- **Body:** Bulleted descriptors for Levels 1–6 only (no boilerplate).

### (g) Performance Definitions (Receptive) – structure, retrieval, ingestion (from NotebookLM)

**Structure:** One page = one table. **Boilerplate above table:** (1) "Within sociocultural contexts for processing language…" (2) "At each grade, toward the end of a given level of English language proficiency, and with instructional support, English language learners will process…" **Table:** four columns — **Proficiency Level** | **Discourse Dimension (Linguistic Complexity)** | **Sentence Dimension (Language Forms and Conventions)** | **Word/Phrase Dimension (Vocabulary Usage)**. **Rows:** Level 6 (Reaching) down to Level 1 (Entering). **Level 6:** one continuous paragraph in the first data column (Discourse); the descriptor spans all three dimensions—store as one block or repeat in all three fields. **Levels 1–5:** two bullet points per dimension column (Discourse, Sentence, Word/Phrase). **Footer:** "WIDA Performance Definitions - Listening and Reading Grades K–12".

**Slicing:** **Slice by level.** Retrieve only the level(s) needed (e.g. Level 2 for a Level 2 lesson) to keep the LLM context small. Do not load the whole page as one chunk.

**When to use:** Use **in addition to** Can Do Descriptors when focusing on **Listening and Reading**: Can Do = *tasks* students can do; Performance Definitions = *quality and linguistic complexity* expected. Use **instead of** this document when the user is planning with the **2020 ELD Framework**—then use the 2020 grade-cluster PLDs (Dimensions of Language Table) instead.

**Ingestion:** One row (or one file) **per proficiency level** (six records). **Schema:** `level` (int 1–6), `discourse_dimension` (array or text), `sentence_dimension` (array or text), `word_phrase_dimension` (array or text). Level 6 can store a single text block; Levels 1–5 store the two bullets per dimension.

**Boilerplate to strip:** (1) Introductory header *"Within sociocultural contexts for processing language…"*; (2) repeating level intro *"At each grade, toward the end of a given level of English language proficiency, and with instructional support, English language learners will process…"*; (3) footer *"WIDA Performance Definitions - Listening and Reading Grades K–12"*.

### (h) WIDA Language Charts (2025) – structure, retrieval, ingestion (from NotebookLM)

**Document:** 38 pages. Three sections: Introduction/Tips; Language Charts; Definitions and Examples glossary.

**Structure:** Charts organized by **grade-level cluster first** (K, 1, 2-3, 4-5, 6-8, 9-12), then **mode** (Expressive, Interpretive). Each chart = matrix: **columns** = three dimensions (Discourse, Sentence, Word/Phrase); **rows** = proficiency levels (Level 6 down to End of Level 1). **Exception:** "End of Level 1" section at end of PDF inverts layout—**rows = grade clusters**, columns = dimensions; parse separately and distribute Level 1 back into each (grade_cluster, mode) file.

**Slicing:** Chunk by **(grade cluster + mode)** (e.g. Grades 2-3 Expressive). For a lesson, optionally slice to **one proficiency level** within that file (e.g. only Level 3 row) to keep context small. **Glossary** (Definitions and Examples, pages 23+) = one global chunk; applies to all grades/modes.

**When to use:** Language Charts (2025) = update to K–12 Speaking and Writing Rubrics; aligned with 2020 ELD. Use **instead of** older Performance Definitions (Features of Academic Language) when using the 2020 Framework. Use **in addition to** 2020 Language Expectations and PLDs (bridge expectations with specific output criteria). For **both** assessment and lesson objectives (plan curriculum, instruction, classroom assessment; align with KLUs in unit planning).

**Key Language Uses in Discourse:** Discourse column header = "Organization, Cohesion, and Density of Language by Key Language Uses." Chart cells do **not** split Narrate/Inform/Explain/Argue—they give general criteria. For "Discourse for Inform": **cross-reference the glossary** "Discourse Dimension Definitions," which maps KLUs to patterns (e.g. Inform → "Topic statement → Description → Summary or Synthesis"; Argue → "Position → Evidence → Reasoning"). App uses glossary for KLU-specific discourse prompts.

**Ingestion:** One file per **(grade cluster, mode)**, e.g. `LanguageChart_Grades2-3_Expressive.md`. **YAML:** `framework: "WIDA Language Charts 2025"`, `grade_cluster`, `mode`. **Body:** rows keyed by `proficiency_level` (6 down to 1), fields `discourse`, `sentence`, `word_phrase`. Parse "End of Level 1" section separately (rows = grade clusters); add each row as the Level 1 entry to the corresponding (grade_cluster, mode) file. **One global file** for the Glossary (Definitions and Examples).

**Boilerplate to strip:** Footer *"WIDA is housed within the Wisconsin Center for Education Research..."*; repeating header *"As multilingual learners work toward the end of a proficiency level, they can consistently..."*; the four "Planning Questions for Instruction and Classroom Assessment" (e.g. *"What can the student do with language?"*) that repeat at the bottom of every chart.

**Pitfall:** End of Level 1 section: rows = grade clusters, not proficiency levels; scraper must not assume "Level [X]" as row label there.

**Referenced in Language Charts (not in our sources):** The document cites **Marco DALE** (WIDA Spanish language development framework; parallel to 2020 ELD); **K–12 WIDA Speaking and Writing Rubrics** (superseded by 2025 Language Charts); **external bilingual dictionaries/glossaries** (e.g. NYU Glossaries of Cognates, Massachusetts DOE Bilingual Word-to-Word Dictionaries) for state content assessments; and **WIDA ACCESS** (Language Charts tie classroom assessment to ACCESS scores). See [WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md) "Documents and resources referenced in WIDA sources."

### (i) WIDA vocabulary categories and instructional guidelines (from NotebookLM)

Sources analyzed (Language Charts, Can Do, ELD) recommend **three vocabulary categories:** (1) **Everyday (General)** — nontechnical, social/instructional (e.g. *dogs* vs *canines*); (2) **Cross-disciplinary (Specific)** — common academic across content areas (e.g. *analyze*, *evaluate*, *summarize*, *chart*); (3) **Technical** — specialized, content-area specific (e.g. *mitosis*, *imperialism*). **Instructional guidelines:** list visually supported key words (cross-disciplinary and technical with meanings); prompt students to generate lists in English and L1; create/revise conceptual webs with sketches and labels in relevant languages; point to approved bilingual dictionaries and glossaries of cognates. **Student activities:** create vocabulary/concept cards; use word and phrase banks to generate lists or label diagrams. Captured in [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) § WIDA vocabulary categories and instructional guidelines.

### (j) Additional vocabulary pedagogy (NotebookLM, non-WIDA sources)

New (non-WIDA) sources summarized in NotebookLM emphasize **how to choose and teach academic vocabulary** beyond categorization. **Strategic selection and pacing:** Teach a **small set of academic words intensively over several days** using varied activities, selecting words from brief, engaging, content-rich texts (trade books, op-eds, student essays). Chosen words should connect to prior knowledge, unlock related vocabulary, and link curriculum topics to real-world applications. **Morphology:** Highlight a small set of high-value morphemes (e.g. “14 morphemes” list) and focus on **transfer**, helping students use known roots and affixes to infer new words rather than memorizing lists. **Embedding in sensemaking:** Especially in science, move away from isolated pre-teaching toward embedding vocabulary in **sensemaking** (investigations, explanations), and show how genre, stance (certainty/possibility/caution), and cohesion language shape word choice. Support work on **connotation** and **collocations** (fixed or frequent word pairs like *plus and minus*, *multiply and divide*, *ebb and flow*). **Classroom supports:** Recommend tools such as the **Frayer Model**, illustrated vocabulary banks and evidence walls, and interactive math/science workbooks as scaffolds for vocabulary mastery. Reflected in [ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md](./ENHANCED_GENERATION_AND_VOCABULARY_MODULES.md) § Additional vocabulary pedagogy (NotebookLM, non-WIDA sources).

---

## Brief to paste into NotebookLM (set context first)

```
I am building a lesson-planning application that uses the WIDA ELD framework as a reference. Our app needs to:

1. Retrieve only the relevant slice of WIDA content for each lesson slot (by grade cluster, subject/standard, Key Language Use, and domain: Listening, Reading, Speaking, Writing).
2. Convert these documents into formats that support that retrieval: e.g. structured Markdown (one file per slice), or a database with columns for grade_cluster, standard, key_use, domain, and content.
3. Keep the LLM context window small: we never load the full PreK-12 set for one slot.

Documents you have: [list the WIDA docs you uploaded, e.g. "Can Do Descriptors Key Uses Edition for Grades 2-3", "ELD Standards Framework 2020 for Grades 2-3", "WIDA Language Charts".]

Please help me (a) understand how these documents are structured (sections, headings, Key Uses, domains), and (b) how we could convert them into formats that serve our purpose: precise retrieval by grade cluster, Key Use, and domain for lesson plan generation.
```

---

## Questions to ask NotebookLM (about the WIDA framework)

**Structure and organization**

1. How is this document organized? What are the main sections and how do they map to grade clusters, Key Language Uses (Narrate, Inform, Explain, Argue), and the four domains (Listening, Reading, Speaking, Writing)?
2. Where exactly do you see the split between Key Use and domain? For example, within "Inform," are there distinct subsections or tables for Listening, Reading, Speaking, and Writing?
3. Is there a consistent heading or label pattern (e.g. "Grades 2-3", "Inform", "Writing") that we could use to programmatically split this PDF into smaller chunks?
4. How do Language Expectations and Language Functions/Features appear in this document, and how are they tied to Key Use and domain?

**Can Do Descriptors (Key Uses Edition)**

5. In the Can Do Key Uses Edition, what is the exact hierarchy: Key Use first, then domain (Listening, Reading, Speaking, Writing)? Or domain first, then Key Use?
6. Are there proficiency levels (e.g. 1–6) within each Key Use + domain cell? How are they labeled?
7. If we wanted one "slice" per (grade cluster, key use, domain), how would we identify the start and end of each slice in the PDF (headings, page breaks, table boundaries)?

**ELD Standards Framework 2020 (grade-level editions)**

8. In the grade-level cluster PDF, how are the four Key Language Uses (Narrate, Argue, Inform, Explain) presented? One section per Key Use, with Language Expectations and Language Functions/Features under each?
9. Within a single Key Use section, is there a further split by domain (Listening, Reading, Speaking, Writing) or by mode (Interpretive vs. Expressive)? What headings or labels mark those splits?
10. What reference codes or IDs (e.g. ELD-LA.2-3.Inform.Expressive) appear in the document, and how could we use them as keys when building a database or Markdown index?

**Conversion and retrieval**

11. If we want to convert this document into Markdown files (one file per grade cluster + Key Use + domain, or per grade cluster + Key Use), what would be a clear naming convention and what content should go in each file?
12. If we want to put this content in a database, what columns would you suggest? (e.g. grade_cluster, standard, key_use, domain, mode, expectation_text, function_heading, feature_bullets.)
13. Are there parts of this document that are "boilerplate" or repeated across slices that we could store once and reference by ID, instead of duplicating in every slice?
14. What pitfalls should we avoid when extracting or scraping (e.g. tables that span pages, nested bullets, footnotes)?

**Alignment with our use case**

15. When our app plans a lesson for "Grade 2, ELA, Inform, Writing," which exact parts of the documents you have would we need to retrieve? Describe the path (e.g. "In the Can Do Key Uses Gr-2-3 PDF, go to the Inform section, then the Writing subsection").
16. How do the WIDA Language Charts relate to the Can Do and ELD Standards documents? If we already have Can Do by Key Use + domain and ELD Standards by grade + standard + Key Use, what does the Language Charts add for our retrieval design?
17. Is there any WIDA guidance on "balance" across the four domains or the four Key Uses over a week or unit that we should reflect in our conversion (e.g. tagging content so we can query "show me all Writing descriptors for Inform for Grades 2-3")?

---

## When you have only the Can Do Descriptors (with domains) in NotebookLM

If your current NotebookLM source is **only** the Can Do Descriptors (domain-based or Key Uses Edition), use the brief below and the questions that match your document.

**Brief to paste (single-doc focus):**

```
I am building a lesson-planning app that uses WIDA. I have uploaded only the **Can Do Descriptors** (organized by domains: Listening, Reading, Speaking, Writing). We need to: (1) understand exactly how this document is structured so we can slice it by grade cluster and domain (and by Key Use if this is the Key Uses Edition); (2) convert it into Markdown or a database for retrieval (one slice per grade cluster + domain, or per grade cluster + Key Use + domain). Documents you have: [name the exact Can Do PDF(s) you uploaded, e.g. "Can Do Descriptors Key Uses Edition Grades 2-3" or "Can Do Descriptors Original Edition"]. Please answer the following so we can design our extraction and retrieval.
```

**If this is the Can Do Key Uses Edition (Recount, Explain, Argue, Discuss):**

- We already have answers for hierarchy (Key Use then domain), table layout (domain = row, six ELP columns), slice boundaries, and pitfalls. You can still ask:
  - Are there any **blank or merged cells** in the tables (e.g. for Level 6 or for Discuss) that our parser should treat differently?
  - What is the **exact wording** of the footnote (e.g. Level 6 ceiling) and where does it appear (every page, every table)?
  - Does the document ever use **"Narrate" or "Inform"** in a heading or caption, or only "Recount"? (So we know whether we need to map only at retrieval time.)
  - For **Discuss**, is the single row always labeled "Oral Language" or also "Listening and Speaking" or something else?

**If this is the Can Do Original Edition (domain-based only, no Key Uses):**

- We have less detail on this edition. Ask:
  - How is the document organized? Is it **grade cluster first, then domain** (e.g. 1-2 → Listening, Reading, Speaking, Writing), or domain first then grade cluster?
  - What are the **exact grade-level bands** (e.g. PreK-K, 1-2, 3-5, 6-8, 9-12)? Are they labeled the same way on every page?
  - Are there **six proficiency levels** (Entering … Reaching) per domain, and how are they labeled (columns, rows, or subsections)?
  - If we want **one slice per (grade cluster, domain)**, what headings or visual boundaries should we use to detect the start and end of each slice?
  - Are there **repeating footnotes or boilerplate** we should strip (e.g. about Level 6)?
  - How would you name **Markdown files** (e.g. `CanDo-Original_1-2_Writing.md`) and what should the **YAML frontmatter** contain?

**Other questions useful for either edition**

- What **pitfalls** should we avoid when scraping this PDF (tables spanning pages, rotated text, repeated headers)?
- For our **database**, should we store one row per (grade_cluster, domain) with six columns (level_1 … level_6) or one row per (grade_cluster, domain, proficiency_level) with a single descriptor text column?

---

## Do you need to ask NotebookLM about other documents?

| Document | Already in NotebookLM? | Do we need more questions? |
|----------|------------------------|----------------------------|
| **Can Do Descriptors (Key Uses or Original)** | Yes (you have this now) | Use the questions above as needed. |
| **ELD Standards Framework 2020** (grade-cluster PDFs) | We had answers earlier from a multi-doc conversation | Only if you add the 2020 PDFs again and want to double-check reference codes, side-by-side layout, or Standard 1 / Language Features rules. |
| **WIDA Language Charts** / **Features of Academic Language** / **Dimensions of Language Table** | Add when ready | **Yes.** Use the "When you have the WIDA Language Charts in NotebookLM" section below: brief + 6 questions (structure, slicing by mode/dimension/grade, when to use vs Can Do/PLDs, Key Language Uses in Discourse, ingestion naming, boilerplate/pitfalls). |
| **Standards FAQ** (Key Language Uses, Language Expectations) | Usually not needed in NotebookLM | Small, conceptual; we use as whole-doc. No need for slice-level questions. |
| **Performance Definitions (Receptive)** | Yes (one-page PDF in `reference_docs/`) | **Yes.** Use the "When you have the Performance Definitions (Receptive) PDF" section below: brief + 5 questions (structure, slicing, when to use vs Can Do/PLDs, ingestion shape, boilerplate). |

**Summary:** You don’t *have* to ask NotebookLM more questions for the **Can Do** if the structure we captured (Key Use → domain, domain = row, ELP = columns, slice boundaries, pitfalls) is enough for your extraction design. If your source is the **Original** (domain-only) edition, use the “Can Do Original Edition” questions above. Add **2020 ELD** or **Language Charts** to NotebookLM only if you need slice-level or chunking details we don’t already have in the synthesis.

---

## When you have the Performance Definitions (Receptive) PDF in NotebookLM

The document at `reference_docs/Performance-Definitions-Receptive-Domains.pdf` is a **single-page** PDF (Listening and Reading, Grades K–12). Use the brief and questions below to decide how to use it in retrieval and whether to ingest it.

**Brief to paste:**

```
I have uploaded the WIDA Performance Definitions for the Receptive domains (Listening and Reading), Grades K–12. It's a one-page document. Our app uses WIDA for lesson planning and assessment: we already use Can Do Descriptors (what tasks students can do) and the 2020 ELD Framework. We want to know: (1) how this one page is structured (levels, dimensions, any subsections); (2) whether we should use it as a single chunk or slice it (e.g. by proficiency level or by dimension); (3) when to retrieve it vs. Can Do or 2020 PLDs for the same lesson slot. Document you have: Performance Definitions – Receptive Domains (Listening and Reading).
```

**Questions to ask:**

1. **Structure:** How is the single page organized? Are the six proficiency levels (1 Entering … 6 Reaching) in rows, columns, or blocks? Are the three dimensions (Discourse/Linguistic complexity, Sentence/Language forms, Word/Phrase/Vocabulary) clearly separated (e.g. three columns or three bullet groups per level)?
2. **Slicing:** For our app we retrieve content by (grade cluster, domain, sometimes proficiency level). This document is K–12 and receptive only (no grade clusters). Should we treat it as **one chunk** (always load the whole page when we need "receptive language quality" guidance), or is there a meaningful way to **slice by level** (e.g. "show only Level 3–4 descriptors") for the LLM context?
3. **When to use it:** When would we pull this Performance Definitions page instead of (or in addition to) the Can Do Descriptors for Listening/Reading or the 2020 PLDs (Dimensions of Language Table)? For example: Can Do = "what tasks"; this doc = "what quality/quantity of language"; 2020 PLDs = updated dimensions. Should we retrieve this only when the teacher is focusing on *receptive* language quality, or always alongside Can Do for receptive domains?
4. **Ingestion:** If we add it to our database or Markdown: would you suggest one row (or one file) per **proficiency level** (six rows/files) with columns/fields for Discourse, Sentence, Word/Phrase text? Or one row/file for the whole page with structured content (e.g. JSON) inside?
5. **Boilerplate:** Is there introductory or footer text on the page we should strip when extracting (e.g. "Within sociocultural contexts…") so we store only the level/dimension descriptors?

After the conversation, add a short synthesis to this file (e.g. "Performance Definitions Receptive: one page; structure …; use as single chunk / slice by level …; retrieve when …") and update [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md) or the "Other WIDA documents" table if retrieval or ingestion guidance changes.

---

## When you have the WIDA Language Charts in NotebookLM

The Language Charts (and related documents such as **Features of Academic Language Chart** or **Dimensions of Language Table**) connect ACCESS scores to instruction and assessment. They use two modes (Expressive / Interpretive) and three dimensions (Discourse, Sentence, Word/Phrase). Use the brief and questions below when this document is in your NotebookLM sources.

**Brief to paste:**

```
I have uploaded the WIDA Language Charts (and/or Features of Academic Language Chart, Dimensions of Language Table). Our app uses WIDA for lesson planning: we already use Can Do Descriptors, the 2020 ELD Framework, and Performance Definitions (Receptive). We need to know: (1) how this document is organized (by mode, dimension, grade, or something else); (2) how we could slice or chunk it so that for a given lesson slot (e.g. Grade 2, Writing = Expressive) we retrieve only the relevant part; (3) when to retrieve it vs. Can Do vs. 2020 PLDs; (4) how the Discourse dimension relates to the four Key Language Uses (Narrate, Inform, Explain, Argue). Documents you have: [name the exact file(s) you uploaded].
```

**Questions to ask:**

1. **Structure:** How is the document organized? Are there clear sections by **communication mode** (Expressive vs. Interpretive), by **dimension** (Discourse, Sentence, Word/Phrase), by **grade or grade cluster**, or by **proficiency level**? How many pages or major sections, and what are the headings?
2. **Slicing for retrieval:** Our app retrieves content by (grade cluster, domain/mode, sometimes proficiency level). Is there a meaningful way to **chunk** this document so we can fetch only "Expressive mode" or only "Interpretive mode," or only one dimension (e.g. Discourse), or only one grade band? Or should we treat the whole document as one chunk and load it only when planning assessment or interpreting proficiency?
3. **When to use it:** When should we pull the Language Charts instead of (or in addition to) Can Do Descriptors, Performance Definitions (Receptive/Expressive), or the 2020 PLDs (Dimensions of Language Table)? For example: is this the same content as the 2020 Dimensions of Language Table, or an older version? Use for assessment design only, or also for lesson objectives?
4. **Key Language Uses in Discourse:** We've read that the **Discourse** dimension reflects the four Key Language Uses (Narrate, Inform, Explain, Argue) through organizational patterns. Where exactly does that appear in the document (e.g. a table, a subsection), and how would we extract or reference it for "show me Discourse descriptors for Inform"?
5. **Ingestion:** If we add this to our database or Markdown: would you suggest one file per mode (Expressive, Interpretive), one file per dimension, one file per (mode + dimension), or keep it as one or two whole-document files? What would the **naming convention** and **YAML frontmatter** (if Markdown) look like?
6. **Boilerplate and pitfalls:** Is there introductory text, footnotes, or repeated headers we should strip when extracting? Any layout issues (e.g. side-by-side modes, rotated text) that would break a simple PDF scraper?

After the conversation, add a short synthesis (structure, slicing strategy, when to retrieve, ingestion) and update [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md) (document catalog and "Other WIDA documents") and [WIDA_FRAMEWORK_INGESTION_AND_USE.md](./WIDA_FRAMEWORK_INGESTION_AND_USE.md) if we define new slice boundaries or a schema.

---

## After the conversation

- Note any structural details (heading levels, labels, reference codes) that NotebookLM identifies and add them to [reference_docs/WIDA_ELD/README.md](../../reference_docs/WIDA_ELD/README.md) or [WIDA_FRAMEWORK_INGESTION_AND_USE.md](./WIDA_FRAMEWORK_INGESTION_AND_USE.md).
- If NotebookLM suggests a schema or file naming convention, document it in the ingestion plan so the extraction module can follow it.
- If you learn that a document has a different structure than we assumed (e.g. Key Use then domain vs. domain then Key Use), update the relevant README so retrieval logic stays accurate.
