# PROMPT — "Convert a scanned Answers & Solutions PDF into the Motion 'image' format bank"

I'm uploading a scanned **image-only** exam "Answers & Solutions" PDF (NEET/JEE style). Build it into a
"Full Paper (with Solutions)" bank in the EXACT same format as the existing
`neet-physics-motion-in-a-straight-line` bank — i.e. `mode:"image"` with SEPARATE cropped images:
`question_image` (stem only), `option_images {a,b,c,d}` (each option cropped, label removed), and
`solution_image`. NO LaTeX. Reuse `FullPaperSolutions.jsx`, endpoint `/api/full-paper/{id}`, and images
served by `/api/chapter-image/{file}`. Follow this proven pipeline (it works first try, minimal cost):

## 0. Setup
- Render pages with PyMuPDF `fitz.Matrix(2.5, 2.5)`. Do NOT rely on `get_text()` (scanned = no text layer).
- Install `PyMuPDF`, `pytesseract`, `Pillow`, `numpy`; `apt-get install -y tesseract-ocr`.
- Copy the PDF into `/app/backend/build_scripts/` so it persists.

## 1. Question tops (OCR-independent, exact count)
- Question numbers live ALONE in the far-left strip (x ≈ 132–200 px @2.5x); body text starts ~x=212.
- Detect one "question top" per question by ink rows in that strip: grayscale < 140, >=4 dark px/row,
  merge rows with <15px gaps, keep bands with 250 <= y <= 1850. Skip page 0 (instructions).
- This gives EXACTLY one top per question in reading order. VALIDATE count == expected total (e.g. 180).
- Subjects from headers "PHYSICS"/"CHEMISTRY"/"BIOLOGY" (numbering is continuous: e.g. 1–45 / 46–90 / 91–180).

## 2. Answer split (OCR only the word "Answer")
- OCR each page once with `pytesseract.image_to_data`; cache line-level {x,y,x0,x1,first,text} to JSON.
- Reliable per-question anchor = a line whose first token is "Answer" and text matches `answer\s*\(`.
  Parse the letter with `\(([1-4])\)` -> a/b/c/d; "No option"/"Bonus" -> answer = null.
- Per question k: QUESTION region = [top_k .. answer_k]; SOLUTION region = [answer_k .. top_{k+1}].

## 3. Split options (best-effort auto-split of the 2x2 / single-column layout)
Find option markers `(1)(2)(3)(4)` as line-starts inside the QUESTION region (x0 < ~340):
- **2×2 grid** (a marker line's text holds two markers, e.g. "(1) .. (2)", next line "(3) .. (4)"):
  - `stem` = crop [top_k .. row1_y] (options excluded).
  - column split ≈ x=740 (left col x[118..735], right col x[748..1445]); row split = midpoint of row1_y & row2_y.
  - opt_a = row1/left, opt_b = row1/right, opt_c = row2/left, opt_d = row2/right (down to answer_y).
- **single-column** (markers (1),(2),(3),(4) each on their own line): stem above (1); each option = [marker_i .. marker_{i+1}] full width; last option down to answer_y.
- **Whiteout the "(N)" label** in each option cell (fill white from cell-left up to x≈262 for left/single, x≈814 for right) so no label shows (app draws its own a/b/c/d badge).
- If markers can't be detected -> FALLBACK: put the whole [top_k .. answer_k] in `question_image` and leave `option_images` empty (options stay inside the stem). Log these question numbers.
- SOLUTION `solution_image` = crop [answer_k .. top_{k+1}].
- Cross-page crops: stack slices (start.y→BODY_BOTTOM, full middle pages BODY_TOP→BODY_BOTTOM, BODY_TOP→end.y; BODY_TOP≈250, BODY_BOTTOM≈1838). Trim surrounding whitespace (gray<235, pad ~8). Crop x band ≈ 118..1445.

## 4. Data
Save PNGs to `/app/backend/chapter_images/` as `reexam2026_q{N}_question.png`, `_opt_a/b/c/d.png`, `_solution.png`.
Write `/app/backend/reexam_solutions.json`:
```
{ "id":"reexam-2026","title":"...","exam":"NEET","source":"...","mode":"image",
  "subjects":["Physics","Chemistry","Biology"],"total_questions":180,
  "questions":[ {"question_no":1,"subject":"Physics","year":"NEET 2026","answer":"d",
    "question_image":"...","option_images":{"a":"...","b":"...","c":"...","d":"..."},"solution_image":"..."} ] }
```
Backend already loads this and exposes `GET /api/full-paper/{id}`.

## 5. Frontend (already implemented — no changes needed for a new PDF)
`FullPaperSolutions.jsx` shows: question_image -> 4 option cards (a/b/c/d badge + option_image; correct one
turns green on reveal; if option_images empty it just shows the stem image) -> "Show Answer & Solution" ->
answer letter + solution_image. Subject tabs (no "All"), Prev/Next, tap-to-zoom on every image.

## 6. Verify
Count == expected; each question has question_image + solution_image; most have 4 option_images (log fallbacks);
no broken image files; images return 200; the viewer flows on desktop and mobile.
```
```
