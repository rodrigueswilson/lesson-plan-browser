# Encoding hypothesis: UTF-8 saved, read as ANSI/ISO-8859?

## Question

Could the Wilson W11 corruption (e.g. "traço" → "trae7o", "conspiração" → "conspirae7e3o") be explained by text being **saved with one encoding** (e.g. UTF-8) and **read by the browser** (or another consumer) with another (e.g. ANSI / Windows-1252 / ISO-8859-1)?

## Short answer

**No.** The pattern we see is not consistent with a simple encoding mismatch. The stored values are the **literal ASCII characters** "e7", "e3", "e9", etc., not the single bytes 0xE7, 0xE3, 0xE9 interpreted with the wrong encoding.

## Why the “wrong encoding” hypothesis does not fit

### If UTF-8 were read as Latin-1 (ANSI)

- In UTF-8, "ç" is the **two bytes** `0xC3 0xA7`.
- If that sequence is interpreted as Latin-1 (or Windows-1252), you get:
  - `0xC3` → Ã  
  - `0xA7` → §  
- So you would see **"traÃ§o"** (or similar), not **"trae7o"**.

### If Latin-1 were read as UTF-8

- In Latin-1, "ç" is the **single byte** `0xE7`.
- `0xE7` by itself is not valid UTF-8 (it is a continuation byte). A UTF-8 decoder would typically replace it with a replacement character or raise an error, not turn it into the two characters "e" and "7".

### What we actually see

- We see the **two characters** "e" and "7" in the text (e.g. "tra**e7**o").
- So in the stored JSON string we have the **bytes** for the ASCII digits: `0x65` 'e' and `0x37` '7', not the single byte `0xE7`.
- That means the corruption is **at save/generation time**: the character was replaced by its **hex representation** (e.g. byte 0xE7 → the string "e7"). This can happen if:
  - The LLM or an upstream step output the hex form instead of the character, or
  - Some code escaped non-ASCII bytes as hex and the result was stored as the final string.

## How to verify (diagnostic script)

Run the encoding diagnostic script on a plan that contains the corruption. It will:

1. Load one Wilson W11 plan from the DB.
2. Find a Portuguese field value that contains a pattern like "e7" or "e3".
3. Print the **raw bytes** (hex) of that string.

If the script shows bytes `65 37` ('e', '7') for the corrupted part, that confirms the stored value is the literal "e7", not the byte 0xE7. So the issue is **not** “UTF-8 saved, opened in ANSI”; it is **hex substitution at source or during persistence**.

```bash
python scripts/diagnose_wilson_w11_encoding.py
```

## Pipeline encoding (for completeness)

- **Backend**: Python 3; `json.loads` / `json.dumps` use Unicode strings; SQLAlchemy stores the JSON column as text (SQLite stores the file in UTF-8).
- **API**: FastAPI returns JSON with UTF-8; the browser uses the response encoding (UTF-8) to decode.
- **Repair script**: Writes with `json.dumps(..., ensure_ascii=False)` so Unicode is preserved.

So the only way to see the two characters "e7" in the browser is if the **stored string** in the DB is already `"trae7o"` (ASCII). Fixing that requires repairing the string content (e.g. the existing repair that maps "e7" → "ç" in Portuguese fields), not changing how the browser or the API decodes the response.
