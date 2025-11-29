# Where to Find Generated Files

## Current File Locations

### 📁 Test Output Files (Generated During Testing)

```
d:\LP\test_output\
├── same_folder_test_20251116_231716/
│   ├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx
│   └── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.html  ← YOUR HTML FILE
├── batch_integration_test_20251116_231443/
│   └── Wilson_W47_Objectives.html  ← YOUR HTML FILE
└── objectives_pdf_test_20251116_230329/
    └── Wilson_W47_Objectives.html  ← YOUR HTML FILE
```

### 📁 Main Output Directory (Production Files)

```
d:\LP\output\
├── Maria Garcia_Lesson plan_W06_10-07-10-11.docx
├── test_objectives_test_merged.docx
└── [Your existing DOCX files here]
```

## 🔍 How to Access Your Generated HTML Files

### Option 1: Open Directly in Browser
1. Navigate to: `d:\LP\test_output\batch_integration_test_20251116_231443\`
2. Double-click: `Wilson_W47_Objectives.html`
3. The file will open in your default web browser

### Option 2: Open from VS Code
1. In VS Code Explorer, go to: `test_output/batch_integration_test_20251116_231443/`
2. Right-click on `Wilson_W47_Objectives.html`
3. Select "Open with Live Server" or "Reveal in Explorer"

### Option 3: Print to PDF from Browser
1. Open the HTML file in any browser
2. Press `Ctrl+P` (or `Cmd+P` on Mac)
3. Select "Save as PDF"
4. Choose landscape orientation for best results

## 📋 What You'll See in the HTML File

The generated HTML contains:
- **5 objectives pages** (Monday-Friday)
- **Landscape layout** (11" × 8.5")
- **Auto-sized fonts** (56-60pt for student goals)
- **Perfect 75%/25% split** (Student Goal / WIDA Objective)
- **Print-optimized CSS** for professional printing

## 🚀 When Integrated into Your Application

After integration, files will be saved in the same location as your existing DOCX files:

```
d:\LP\output\
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx     (existing)
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107.json     (existing)
├── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.html  (NEW)
└── Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.pdf    (NEW)
```

## 📁 File Naming Pattern

The objectives files follow this naming pattern:
```
[Original_Docx_Name]_Objectives.[html|pdf]
```

Examples:
- `Wilson_Weekly_W47_11-17-11-21_20251116_213107.docx`
- `Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.html`
- `Wilson_Weekly_W47_11-17-11-21_20251116_213107_Objectives.pdf`

## 🔧 Quick Test Right Now

1. **Open the test file**:
   ```
   d:\LP\test_output\batch_integration_test_20251116_231443\Wilson_W47_Objectives.html
   ```

2. **View in browser**: See the precise layout with auto-sized fonts

3. **Print to PDF**: Test the PDF functionality using your browser

4. **Check layout**: Verify the 75%/25% split and font sizing

## 📱 Mobile/Tablet Viewing

The HTML files are also mobile-friendly:
- Open on tablet for classroom display
- Responsive design adapts to screen size
- Touch-friendly for interactive use

## 🎯 Next Steps

1. **Review the test files** in `d:\LP\test_output\`
2. **Test the HTML in your browser** to see the layout quality
3. **Print to PDF** to test the output format
4. **Integrate the code** into your batch processor using the provided guide
5. **Generate real objectives** alongside your existing DOCX workflow
