# Prep Suite Generator — Web App (roadmap step 2)

Upload a document + type an instruction + pick **kid / adult** → click Generate → open or download a finished interactive study course (the same Alpine + Tailwind engine you've been using).

```
documents / pasted text  +  instruction  +  audience
        ↓        (app.py — FastAPI front end)
   extract text  →  generator.build_course()
        ↓        (generator.py — prompt → model → strict JSON → validate)
   inject JSON into course_template.html
        ↓
   finished course  (view in browser or download .html)
```

## Files
- **`app.py`** — the web server: upload page, `/generate`, `/course/{id}`, `/download/{id}`, `/library`. Handles file extraction (txt, md, pdf, docx, csv) and friendly errors.
- **`generator.py`** — the reusable core: the generation prompt, the model backends (Ollama or Anthropic), strict schema validation for all 7 module types, and a self-correcting retry that feeds validation errors back to the model. Importable from a CLI or notebook too.
- **`course_template.html`** — the fixed rendering engine (must sit next to `app.py`).
- **`generated/`** — created automatically; each generated course is saved as `{id}.html`.

## Setup

```bash
pip install fastapi uvicorn python-multipart
# document parsers (optional, only for those file types):
pip install pypdf python-docx
```

Pick **one** model backend:

```bash
# Local, closed-loop (default) — keeps everything on your machine:
pip install ollama
ollama pull llama3.1:8b           # a larger model makes noticeably better courses

# OR hosted (stronger, costs money):
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
export PREP_BACKEND=anthropic
```

## Run

```bash
uvicorn app:app --reload --port 8000
# open http://localhost:8000
```

Upload a chapter or study guide (or paste text), type something like
`6th grade science test on ecosystems, friendly tone`, choose **Kid**, and Generate.
Local models take ~30–90s; the page shows a spinner, then an **Open course** /
**Download** card.

## Notes
- **Backend swap point.** `generator.py` isolates the model call in `_call_ollama` /
  `_call_anthropic` — exactly the "wrap the model behind one function" pattern from the
  RAG. Add a new provider by adding one function.
- **Validation mirrors the engine.** `validate()` checks every rule the template relies
  on (unique ids, valid types/kinds, `correct` in range, `wrongFeedback` parallel to
  `opts`, sequence ids match). If the model slips, the one self-correcting retry usually
  fixes it; otherwise you get a clear error instead of a broken course.
- **The generated file is standalone.** The downloaded `.html` has the course JSON baked
  in and loads Alpine + Tailwind from CDNs — open it anywhere, no server needed.
- **In-memory library.** Generated courses live in `generated/` on disk, but the `/library`
  index resets on restart. Persisting it (a small SQLite table of id/title/path) is the
  natural step-3 upgrade — and the same closed-loop instinct: log what you produce so you
  can list, re-open, and later track which courses worked.

## Big docs?
For material too large for the model's context window, chunk + retrieve the relevant
sections first (the RAG you already built) and pass only those to `build_course`. For
test-prep-sized inputs (a chapter, a guide) the whole document fits, so the app sends it
directly and trims only if it exceeds ~24k characters.
