# How the App Reads Primary Teachers' Lesson Plans - Beginner's Guide

## 📚 The Big Picture

**What happens:**
1. Primary teacher creates a lesson plan in Word (DOCX file)
2. You (ESL teacher) need to adapt it for bilingual students
3. The app reads the primary teacher's plan
4. Extracts the important parts
5. Sends it to AI (GPT-5) to transform it
6. Creates your bilingual version

---

## 🔍 What the App Extracts

### From Primary Teacher's Lesson Plan:

**1. Subject & Week Information**
- What subject? (Math, Science, ELA, etc.)
- What week? (10/6-10/10)
- What grade? (6th grade)

**2. Daily Lesson Content**
- **Monday:** What are they teaching?
- **Tuesday:** What are they teaching?
- **Wednesday:** What are they teaching?
- **Thursday:** What are they teaching?
- **Friday:** What are they teaching?

**3. Lesson Components (for each day):**
- **Objectives:** What should students learn?
- **Activities:** What will students do?
- **Materials:** What do they need?
- **Assessments:** How will learning be measured?

---

## 📖 How It Reads DOCX Files

### Step 1: Open the DOCX File

Think of a DOCX file like a ZIP folder with text inside:

```
Primary Teacher's File: "Davies_Math_W41.docx"
├── Text paragraphs
├── Tables (if any)
├── Headings (like "Monday", "Objectives")
└── Formatting (bold, italic, etc.)
```

### Step 2: Find the Subject Section

**Example:** If the file has multiple subjects, find just the Math section:

```
File contains:
- Math lessons (pages 1-3)
- Science lessons (pages 4-6)
- ELA lessons (pages 7-9)

App extracts: Only Math lessons (pages 1-3)
```

### Step 3: Extract Text by Patterns

The app looks for **keywords** and **headings**:

**Pattern 1: Headings**
```
MONDAY
Objectives: Students will...
Activities: Students will complete...

TUESDAY
Objectives: Students will...
```

**Pattern 2: Tables**
```
| Day      | Objectives           | Activities          |
|----------|---------------------|---------------------|
| Monday   | Students will...    | Complete worksheet  |
| Tuesday  | Students will...    | Group discussion    |
```

**Pattern 3: Keywords**
```
Looking for words like:
- "Monday", "Tuesday", "Wednesday"
- "Objective:", "Goal:", "Students will"
- "Activity:", "Instruction:", "Procedure"
- "Assessment:", "Evaluation:", "Check for understanding"
```

---

## 🔧 Real Example: Davies' Math Lesson

### Input (What Davies wrote):

```
MONDAY - Unit 3 Lesson 1: Fractions

Objective: Students will identify equivalent fractions using visual models.

Anticipatory Set: Show pizza divided into different pieces. Ask: Are 2/4 and 1/2 the same?

Instruction:
- Present fraction strips
- Demonstrate equivalent fractions with manipulatives
- Students complete comparison chart
- Practice problems on worksheet

Assessment: Exit ticket - Students identify 3 pairs of equivalent fractions

Materials: Fraction strips, pizza model, worksheet
```

### What the App Extracts:

```json
{
  "day": "Monday",
  "topic": "Unit 3 Lesson 1: Fractions",
  "objective": "Students will identify equivalent fractions using visual models",
  "anticipatory_set": "Show pizza divided into different pieces. Ask: Are 2/4 and 1/2 the same?",
  "instruction": "Present fraction strips, Demonstrate equivalent fractions with manipulatives, Students complete comparison chart, Practice problems on worksheet",
  "assessment": "Exit ticket - Students identify 3 pairs of equivalent fractions",
  "materials": "Fraction strips, pizza model, worksheet"
}
```

---

## 🤖 How the Extraction Works (Technical but Simple)

### Method 1: Heading Detection

```python
# App looks for styled headings in Word
If text is formatted as "Heading 1" or "Heading 2":
    This is probably a section title (like "Monday" or "Objectives")
```

### Method 2: Keyword Search

```python
# App searches for specific words
If line contains "Objective:" or "Students will":
    Extract everything after that word
    This is the objective
```

### Method 3: Table Reading

```python
# If lesson is in a table format
For each row in table:
    Column 1 = Day (Monday, Tuesday, etc.)
    Column 2 = Objectives
    Column 3 = Activities
    Extract each cell's content
```

### Method 4: Pattern Matching

```python
# App recognizes common patterns
Pattern: "MONDAY - Topic Name"
Extract: Day = Monday, Topic = Topic Name

Pattern: "Objective: [text]"
Extract: Objective = [text]
```

---

## 📊 Different File Formats the App Handles

### Format 1: Heading-Based (Davies' Style)

```
MONDAY
Objective: ...
Activities: ...

TUESDAY
Objective: ...
Activities: ...
```

**How app reads it:**
1. Find "MONDAY" heading
2. Look for "Objective:" below it
3. Extract text until next heading

### Format 2: Table-Based (Lang's Style)

```
| Day     | Objectives        | Activities       |
|---------|-------------------|------------------|
| Monday  | Students will...  | Read chapter 1   |
| Tuesday | Students will...  | Group discussion |
```

**How app reads it:**
1. Find the table
2. Read each row
3. Extract: Day, Objectives, Activities

### Format 3: Mixed Format (Savoca's Style)

```
Week of 10/6-10/10

Monday: States of Matter
- Objective: Identify three states
- Activity: Lab experiment
- Assessment: Quiz

Tuesday: Properties
- Objective: Compare properties
...
```

**How app reads it:**
1. Find day names (Monday, Tuesday)
2. Look for bullets or dashes
3. Extract content after keywords

---

## 🎯 What Gets Sent to AI (GPT-5)

### Input to AI:

```
Primary Teacher's Content:
"Monday - Fractions
Objective: Students will identify equivalent fractions using visual models
Activity: Use fraction strips and manipulatives
Assessment: Exit ticket with 3 pairs of equivalent fractions"

Grade: 6
Subject: Math
Week: 10/6-10/10
```

### AI Transforms It To:

```json
{
  "monday": {
    "content_objective": "Students will identify equivalent fractions using visual models",
    "student_goal": "I can find fractions that are equal using pictures and models",
    "wida_objective": "Students will describe equivalent fractions using visual supports (ELD-MA.6-8.Explain)",
    "bilingual_bridge": "Frações equivalentes = Equivalent fractions (mesma quantidade, aparência diferente)",
    "ell_support": [
      {
        "strategy": "Visual Scaffolding",
        "implementation": "Use fraction strips with labels in English and Portuguese"
      }
    ],
    "materials": "Fraction strips (labeled bilingually), pizza model, visual anchor chart"
  }
}
```

---

## 🔄 The Complete Flow

### Step-by-Step Process:

```
1. YOU place primary teacher's file in week folder
   📁 F:\...\25 W41\Davies_Math_W41.docx

2. APP finds the file automatically
   🔍 "Looking for teacher: Davies, subject: Math"
   ✅ Found: Davies_Math_W41.docx

3. APP opens and reads the DOCX
   📖 Extracting text, tables, headings...

4. APP finds Math section (if multiple subjects)
   📑 Pages 1-3 contain Math lessons

5. APP extracts lesson components
   📝 Monday: Objective, Activities, Assessment
   📝 Tuesday: Objective, Activities, Assessment
   📝 ... (all 5 days)

6. APP sends to GPT-5
   🤖 "Transform this for ESL students, add WIDA standards, 
       bilingual strategies, Portuguese translations..."

7. GPT-5 returns bilingual version
   ✨ Complete lesson plan with:
      - WIDA standards
      - Bilingual strategies
      - Portuguese cognates
      - ELL scaffolds
      - Modified assessments

8. APP creates your DOCX file
   📄 Wilson_Rodrigues_Lesson_plan_W41_10-06-10-10.docx
   
9. Saved to same week folder
   💾 F:\...\25 W41\Wilson_Rodrigues_Lesson_plan_W41_10-06-10-10.docx
```

---

## 🛠️ What You Need to Know

### ✅ What Works Automatically:

1. **File Finding**
   - You just put files in week folder
   - App finds them by teacher name
   - No need to select files manually

2. **Content Extraction**
   - App reads different formats
   - Handles tables, headings, bullets
   - Finds objectives, activities, assessments

3. **Subject Detection**
   - If file has multiple subjects, app finds the right one
   - Matches based on your slot configuration

### ⚠️ What You Should Do:

1. **Consistent File Naming**
   - Include teacher name in filename
   - Example: `Davies_Math_W41.docx` ✅
   - Example: `Lesson_Plan.docx` ❌ (too generic)

2. **Clear Structure in Primary Plans**
   - Use headings (Monday, Tuesday, etc.)
   - Or use tables with clear columns
   - Label sections (Objective, Activity, Assessment)

3. **One Week Per Folder**
   - Keep all Week 41 files in `25 W41` folder
   - Don't mix weeks

---

## 📋 Common Scenarios

### Scenario 1: Davies Uses Headings

**Davies' File:**
```
MONDAY
Objective: Students will...
Activity: Complete worksheet

TUESDAY
Objective: Students will...
```

**App extracts:**
- ✅ Finds "MONDAY" heading
- ✅ Extracts objective below it
- ✅ Extracts activity below that
- ✅ Repeats for Tuesday, Wednesday, etc.

### Scenario 2: Lang Uses Tables

**Lang's File:**
```
| Day | Objectives | Activities |
|-----|-----------|-----------|
| Mon | Read Ch 1 | Discussion |
| Tue | Read Ch 2 | Quiz      |
```

**App extracts:**
- ✅ Finds table
- ✅ Reads each row
- ✅ Maps: Day → Objectives → Activities

### Scenario 3: Savoca Has Multiple Subjects

**Savoca's File:**
```
SCIENCE
Monday: States of matter...
Tuesday: Properties...

SOCIAL STUDIES
Monday: Geography...
Tuesday: History...
```

**App extracts:**
- ✅ Finds "SCIENCE" section
- ✅ Extracts only Science lessons
- ✅ Ignores Social Studies (if slot is for Science)

---

## 🎓 Key Takeaways

### What the App Does:

1. **Reads** primary teacher's DOCX file
2. **Finds** the right subject section
3. **Extracts** lesson components (objectives, activities, etc.)
4. **Sends** to AI for transformation
5. **Creates** your bilingual version

### What You Do:

1. **Place** primary teacher files in week folder
2. **Configure** teacher names once (in app)
3. **Select** week to process
4. **Click** generate
5. **Get** your bilingual lesson plan!

### What You DON'T Do:

- ❌ Manually copy/paste from primary plans
- ❌ Select files every week
- ❌ Tell app where to find content
- ❌ Format the output

---

## 🔮 Example: Your Weekly Workflow

### Monday Morning (5 minutes):

1. **Check email** - Primary teachers sent their plans
2. **Download files** to week folder:
   ```
   F:\...\25 W41\
   ├── Davies_Math_W41.docx
   ├── Lang_ELA_W41.docx
   └── Savoca_Science_W41.docx
   ```

3. **Open app** → Select "Week 41" → Click "Generate"

4. **Wait 2-3 minutes** while app:
   - Reads all 3 files
   - Extracts Math, ELA, Science content
   - Sends to GPT-5
   - Creates your bilingual plan

5. **Done!** Your file is ready:
   ```
   Wilson_Rodrigues_Lesson_plan_W41_10-06-10-10.docx
   ```

---

## ❓ FAQ

**Q: What if primary teacher's file is messy?**
A: App tries multiple methods (headings, keywords, tables). Usually finds content anyway.

**Q: What if file has no clear structure?**
A: App extracts all text and sends to GPT-5. AI is smart enough to organize it.

**Q: What if teacher name is spelled differently?**
A: App uses fuzzy matching. "Davies", "Davis", "Ms. Davies" all work.

**Q: What if file has multiple subjects?**
A: App finds your subject based on slot configuration and keywords.

**Q: What if I have 2 slots with same teacher?**
A: App uses the same file but extracts different subjects for each slot.

---

## 🚀 Bottom Line

**The app is like a smart assistant that:**

1. 📖 **Reads** Word documents (like you would)
2. 🔍 **Finds** important parts (objectives, activities)
3. 🤖 **Asks AI** to make it bilingual
4. 📝 **Creates** your lesson plan automatically

**You just:**
- Put files in folder ✅
- Click generate ✅
- Get your bilingual plan ✅

**No manual copying, no formatting, no stress!** 🎉

---

**Next:** Ready to see it in action? We can test with your real Week 41 files!
