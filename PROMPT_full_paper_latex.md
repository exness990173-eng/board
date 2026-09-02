# PROMPT — "Build a Full-Paper-with-Solutions (LaTeX) from a scanned Answers & Solutions PDF"

I'm uploading a scanned **image-only** exam "Answers & Solutions" PDF (e.g. NEET/JEE). Build it into a
"Full Paper (with Solutions)" viewer EXACTLY like the existing `reexam-2026` bank in this app
(pages `FullPaperSolutions.jsx`, component `MathText.jsx`, endpoint `/api/full-paper/{id}`,
images via `/api/chapter-image/{file}`). Follow this proven pipeline so it works first try and
DOES NOT waste LLM credits.

## 0. Assume the PDF has NO text layer
Do NOT rely on PyMuPDF `get_text()` markers (they return empty on scanned PDFs) and do NOT expect any
`/root/*.py` script to exist. Render pages with `fitz.Matrix(2.5, 2.5)`.

## 1. Segment questions WITHOUT OCR of question numbers (they are unreliable)
- Question numbers live ALONE in the far-left margin strip (x ≈ 132–200 px at 2.5×); body text starts ~x=212.
- Detect one "question top" per question by scanning that left strip for rows with ink
  (grayscale < 140, ≥4 dark px/row, merge rows within 15px gaps, keep bands with 250 ≤ y ≤ 1850).
- This yields EXACTLY one top per question (validate the count == expected total, e.g. 180).
- Skip the instructions page (page 0). Subject headers ("PHYSICS"/"CHEMISTRY"/"BIOLOGY") mark subject
  boundaries; numbering is usually continuous (Physics 1–45, Chemistry 46–90, Biology 91–180).

## 2. Find the Answer/solution split with OCR (only the word "Answer")
- OCR each page once with `pytesseract.image_to_data`, cache to JSON (OCR is slow ~2s/page).
- "Answer (N)" lines are reliable (first token "Answer", x≈212). Parse the letter: `\(([1-4])\)` -> a/b/c/d;
  "No option"/"Bonus" -> answer = null.
- Per question k: stem = crop [top_k .. answer_k], solution = crop [answer_k .. top_{k+1}]
  (stack across pages: start.y→BODY_BOTTOM, full middle pages, BODY_TOP→end.y; BODY_TOP≈250, BODY_BOTTOM≈1838).
  Crop x range ≈ 118..1445, then trim whitespace (getbbox on gray<235, pad 10).
- Save `reexam2026_q{N}_q.png` (stem+options) and `reexam2026_q{N}_s.png` (answer+solution) to
  `/app/backend/chapter_images/`. Build `reexam_solutions.json`:
  `{id, title, exam, source, mode:"image", subjects:[...], total_questions, questions:[{question_no, subject, year, answer, question_image, solution_image}]}`.

## 3. LaTeX via ONE vision-LLM call per question (minimise credits)
- Use Emergent LLM key, model `gpt-5.4` (openai), library `emergentintegrations`.
- Send BOTH images in a single `UserMessage(file_contents=[ImageContent(base64=stem), ImageContent(base64=solution)])`.
  (1 call per question = 180 calls, NOT 360.)
- **Do NOT ask for JSON** — LaTeX backslashes break JSON parsing and cause failed calls / re-runs / wasted credits.
  Ask for a **delimiter format** (no escaping):
  `###QUESTION###` / `###OPTA###` / `###OPTB###` / `###OPTC###` / `###OPTD###` / `###QDIAG###` /
  `###EXPLANATION###` / `###SDIAG###`, content on the lines after each marker; parse by slicing between markers.
- Rules in the prompt: transcribe exactly; wrap math in `$...$`; options carry NO (1)/A. labels;
  linearize simple tables; `QDIAG`/`SDIAG` = true only when an essential figure/graph/structure can't be text.
- **Checkpoint after every question** to `reexam_latex.json` and make the runner **resumable** (skip already-done),
  with `Semaphore(5)` concurrency and a `TEST_QNOS="1,46,91"` env to validate on 3 before the full run.
- Merge the latex fields (`question_latex`, `options_latex`, `question_has_diagram`, `explanation_latex`,
  `solution_has_diagram`) into `reexam_solutions.json`.

## 4. Frontend (render LaTeX ALWAYS, hybrid image fallback — like Motion)
- Question: if `question_latex && !question_has_diagram` -> `MathText` stem + 4 option rows (A–D badges + `MathText`);
  else show `question_image`.
- Solution (on reveal): "Answer · X" (or "Bonus / No option"); if `explanation_latex && !solution_has_diagram`
  -> `MathText`; else show `solution_image`. Keep subject tabs (no "All"), Prev/Next, tap-to-zoom on image parts.

## 5. Verify
Bank loads with all N questions; each has 4 options + an answer (nulls only for bonus); diagram-flagged
questions show images; images return 200; LaTeX renders on desktop+mobile. Bump `?v=` on `chapterImageUrl`
only if you regenerate image files.
