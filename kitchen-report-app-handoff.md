# Kitchen Report Breakout App — Handoff Doc for Claude Code

## 1. What this app should do

Take N days' worth of "Kitchen Report" PDFs (same format as Arlington Hts' system
produces) and generate a shift-by-shift breakout: one page per station, each
listing every item with one quantity column per day, in a Word doc (or on-screen
table) — exactly what we built manually for Monday/Tuesday. The app should
generalize that to any number of days, not just two.

**Input:** 1–7+ PDF kitchen reports (one per day), same "Station → Shift → Item"
format.
**Output:** Either an in-browser table view, and/or a generated .docx with one
page per station, columns = Item + one column per uploaded day.

This doc is the spec + algorithm writeup so a fresh Claude Code session doesn't
have to rediscover the parsing quirks we hit. Hand this whole file to Claude
Code as the first message in a new project.

---

## 2. Why this isn't a trivial "extract text from PDF" job

The source PDFs are **not** plain-text-friendly. Three specific problems will
bite anyone who does a naive `pdftotext` or `pdf-parse` dump:

1. **Two-column "snake" layout.** Each station's shift data is laid out in two
   print columns per page. Reading the page top-to-bottom, left-to-right (the
   default order almost every PDF text extractor gives you) interleaves rows
   from both columns and scrambles which item belongs to which shift.
   **Fix:** split text by x-coordinate into left/right halves *before*
   reconstructing lines, then read left column fully (top→bottom), then right
   column fully (top→bottom). This "reading order" — not raw document order —
   is what matches how a human would read the printed page.

2. **Numbers glued to item names with no space character.** e.g. the text
   literally renders as `"BRSEB - Bacon, Egg & Cheese SanNaN"` — really
   `"...San10"` with **no space glyph** between "San" and "10" in the PDF
   content stream, even though visually there's a small gap. A word-level
   extractor (like `pdfplumber.extract_words()` or `pdfjs`'s default text runs)
   will NOT split these into two tokens, because there's no actual space
   character, and the visual gap is smaller than distinct-word thresholds
   typically expect. **Fix:** parse at the character level, and split into a
   new "word" whenever the horizontal gap between adjacent characters exceeds
   a threshold (~1.2pt in the reports we saw, but recompute from your own
   files) — the gap between the end of a name and the start of its number is
   reliably close to (or larger than) the gap used for an explicit space
   elsewhere on the same line, even without an actual space character.

3. **Duplicate report content.** Both source PDFs had every station printed
   **twice**, back-to-back (page N repeats verbatim at some later page). If
   you don't dedupe, every quantity effectively doubles. **Fix:** scan for the
   station header sequence (e.g. "Alcohol Station", "Salad Station", …) and
   only use pages up through the *first* full pass; discard everything from
   the second occurrence of the first station onward.

4. **A shift-labeling quirk ("Blank" shift can appear early).** Occasionally a
   later shift (e.g. "Shift 3") is declared "Blank" *before* the previous
   shift's item list has actually finished printing (because that shift's
   content overflowed onto the next page/column). If you naively track
   "current shift = last Shift-N marker seen," you'll misattribute the
   overflow items to the blank shift. **Fix heuristic:** when you see a
   `Shift N` marker immediately followed by the literal word `Blank`, do
   **not** update "current shift" — treat it as a no-op and keep attributing
   subsequent unlabeled items to whatever shift was active before it. We
   validated this by summing our shift-level parse back up and comparing to
   the report's own day-total figures (see item 5).

5. **Cross-check everything against a ground-truth total when one exists.**
   The Sandwich Station page includes a "BREAD SUMMARY" section with a clean
   day-total per item (no shift breakdown, but a reliable total). We summed
   our shift-attributed quantities for each item across all shifts and
   confirmed they matched the Bread Summary total exactly. **Do this for any
   station/report that has a redundant total** — it's the cheapest way to
   catch a parsing bug before it reaches the output doc.

---

## 3. The parsing algorithm (language-agnostic pseudocode)

This is what worked, station-by-station:

```
for each PDF (= one day):
    dedupe pages (see §2.3)
    for each page:
        chars = extract_chars_with_positions(page)   # x0, x1, top, text
        mid_x = page_width / 2
        left_chars  = [c for c in chars if c.x0 < mid_x]
        right_chars = [c for c in chars if c.x0 >= mid_x]

        left_lines  = cluster_into_lines(left_chars,  top_tolerance=2.5)
        right_lines = cluster_into_lines(right_chars, top_tolerance=2.5)
        # cluster_into_lines: group chars whose 'top' is within tolerance,
        # i.e. same visual row

        for each line in left_lines then right_lines (in that order):
            words = split_line_into_words(line, gap_threshold=1.2)
            text = words.joined(" ")
            page_lines.append(text)   # preserves correct reading order

    # Now walk page_lines in order, tracking state:
    current_station = None
    current_shift = None
    for i, line in enumerate(all_lines):
        if line matches STATION_HEADER_PATTERN:      # "Salad Station 9/14/2026"
            current_station = extracted name
            current_shift = None
            continue
        if line == "Shift N":
            if next_nonblank_line == "Blank":
                skip both lines, do NOT change current_shift
            else:
                current_shift = N
            continue
        if line startswith one of ("ORDER ", "Total Rolls", "Total Wraps",
                                    "Total Croissants", "BREAD SUMMARY", ...):
            continue   # sub-order noise, not needed
        if line matches r'^(.+?):\s*(\d+)\s*All Day$':
            # the "bold" top-level item line most stations use
            record(current_station, current_shift, name=match[1], qty=match[2])
        elif current_station == "Sandwich Station" and
             line matches r'^(.+?)\s+(\d+)(\s+.*)?$':
            # sandwich items: no "All Day" suffix, qty sums across order blocks
            accumulate(current_station, current_shift, name=match[1], qty += match[2])
```

**Station header regex:** `^(Station Name) \d{1,2}/\d{1,2}/\d{4}$`
**Bold item line regex:** `^(.*?):\s*(\d+)\s*All Day\s*$`
**Sandwich item line:** trailing integer, optionally followed by a note
(`"NO CHEESE"`, `"MAKE VEGAN..."`, etc.) — take the first integer after the
name, ignore trailing text.

De-duplicate identical `(name, qty)` pairs within the same station+shift+day
(the source sometimes lists the same bold item twice because of how prep notes
are split across sub-lines).

---

## 4. Recommended architecture for the React app

You have two reasonable paths. **Path A is faster to get working** since it
reuses proven logic; **Path B is a cleaner single-stack app**.

### Path A — Python parsing service + React frontend (fastest to reuse our work)
- Small FastAPI (or Flask) service that ports the exact Python scripts we used
  (`pdfplumber` for char-level extraction — it exposes `page.chars` with
  `x0`/`x1`/`top` directly, which is exactly what the algorithm above needs).
- One endpoint: `POST /parse` — accepts N PDF files + their day labels, returns
  JSON: `{ [day]: { [station]: { [shift]: [{name, qty}] } } }`.
- React frontend: upload UI, calls the endpoint, renders/edits the table,
  and either exports to `.docx` client-side (see below) or asks the backend to
  generate it.
- **Start here if you want to literally copy our Python parsing code with
  minimal changes.**

### Path B — Pure JS/TypeScript, no backend
- Use `pdfjs-dist` (Mozilla's PDF.js) in the browser or a Node script. It
  exposes `getTextContent()` with per-item `transform` matrices, which give you
  x/y position — equivalent granularity to `pdfplumber.chars`, but you'll need
  to re-derive character-level positions (pdf.js groups into "text items,"
  which may already merge some characters — check whether glued numbers like
  `"San10"` come through as one item or are split; you may need
  `disableCombineTextItems: true` in `getTextContent` options to get finer
  granularity).
- Re-implement §3's column-split + gap-threshold logic in TypeScript.
- Generate the `.docx` output client-side with the `docx` npm package (same
  library we used — it works fine in-browser via Vite/webpack) plus
  `file-saver` to trigger the download.
- **Start here if you want one deployable static app with no server.**

### Suggested project structure (either path)
```
/src
  /parsing
    columnSplit.ts / .py      — the left/right column + gap-threshold logic
    lineClassifier.ts / .py   — station/shift/item regex matching + Blank heuristic
    sandwichParser.ts / .py   — special-cased order-block summing
    dedupePages.ts / .py      — detect & drop the repeated second pass
    types.ts                  — ParsedReport = Record<day, Record<station, Record<shift, Item[]>>>
  /components
    FileUploader.tsx          — accepts N files, lets user label each with a date
    ParsePreview.tsx          — table view per station/shift, editable before export
    ExportButton.tsx          — triggers docx generation/download
  /docx
    buildShiftDoc.ts          — port of build_docs2.js: running header, page-per-station,
                                 dynamic day columns instead of hardcoded Monday/Tuesday
  App.tsx
```

### Generalizing from 2 days to N days
The only hardcoded "Monday/Tuesday" assumptions to remove:
- Table columns: instead of `{name, mon, tue}`, use `{name, values: Record<dayLabel, qty>}`.
- Union-of-items-across-days logic (§ from our JSON build step) needs to loop
  over all N days, not just two, preserving first-seen order.
- The docx column widths need to flex with day count (or paginate/wrap if more
  than ~5–6 days would make columns too narrow).

### Validation to keep from day one
Bake in the Bread-Summary-style cross-check as an automated test wherever the
source format offers a redundant total — it caught our one real bug (the
"Blank shift" misattribution) before it reached the final document.

---

## 5. Suggested first prompt to Claude Code

Paste this file into the project, then ask something like:

> Scaffold a Vite + React + TypeScript app per the architecture in this doc
> (Path A or B — pick one). Start with the parsing module and a unit test that
> runs it against one sample PDF and checks the Sandwich Station shift totals
> sum to the Bread Summary totals, before wiring up any UI.

That ordering (parser + test first, UI second) is deliberate — the parsing
logic is where all the risk is; the React UI around it is comparatively
mechanical.
