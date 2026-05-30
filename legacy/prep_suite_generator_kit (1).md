# Prep Suite Generator — Kit

How to turn the one-off HTML course into a **repeatable product**: feed documents + instructions, get a finished interactive study suite in the same Alpine + Tailwind dark/purple style.

---

## 1. The core idea: content vs. template

The course you have is **one hard-coded instance** of a template. The product move is to split it in two:

```
  CONTENT  (a JSON object)          ← the LLM generates this from your docs
     +
  TEMPLATE (the rendering engine)   ← fixed; you never regenerate it
     ↓
  one finished course
```

`course_template.html` is exactly this. Open it — it renders a 6th-grade ecosystems course. Everything it shows comes from one `const COURSE = {...}` object near the bottom. **Swap that object and you have a new course.** The ~450 lines of engine below it never change.

So "generate a course" reduces to "generate a valid `COURSE` JSON object." That's a single, well-scoped LLM task — and it's the same shape as the RAG work you just did: documents in, structured output out, then render.

---

## 2. The pipeline

```
documents (.md/.pdf/.txt) + instructions ("6th grade science test on ecosystems")
        ↓
   [optional] chunk + retrieve the relevant parts   ← reuse your RAG when docs are big
        ↓
   LLM with the GENERATION PROMPT (section 4)
        ↓
   strict JSON conforming to the COURSE schema (section 3)
        ↓
   validate (JSON.parse + a schema check)
        ↓
   inject into course_template.html  (replace the COURSE constant)
        ↓
   finished_course.html
```

For test-prep, source docs are usually small (a chapter, a study guide), so you can pass them whole. Only reach for retrieval when the material is too large for the context window — and that's exactly the RAG you already built.

---

## 3. The COURSE schema

Top level:

```jsonc
{
  "meta": {
    "title": "string — shown in the header",
    "subtitle": "string — small text, header right",
    "learner": "kid" | "adult"   // tunes tone + result messages
  },
  "modules": [ /* ordered; each becomes one tab */ ]
}
```

Each module is `{ "type", "id", "label", "data" }`. `id` must be unique (used for state + localStorage). `label` is the tab text. There are **7 module types** — they cover every interactive pattern in the original 14-tab course:

| type | what it renders | original tab(s) it replaces |
|---|---|---|
| `overview` | hero + concept cards + a step/ladder strip | Thesis |
| `concept_cards` | expandable cards with labeled fields + a "watch out" box | Pipeline, The 3 Questions |
| `flashcards` | active recall w/ mastery + streak (saved locally) | Active Recall |
| `glossary` | term/definition grid | Glossary |
| `cheatsheet` | printable one-pager | Cheat-Sheet |
| `sequence` | drag-free ordering challenge, multiple modes | Sequence |
| `challenge` | MCQ engine with 4 `kind`s (below) | Quiz, Build Game, Speed Round, Gauntlet |

`challenge.data.kind` is the key consolidation — one component, four behaviors:

- `"quiz"` — plain scored multiple choice, single explanation per question.
- `"rounds"` — scenario + constraints + option detail + right/wrong feedback (the "build game").
- `"timed"` — per-question countdown, auto-advances (the "speed round").
- `"classify"` — same as rounds, framed as diagnosis (the "failure gauntlet").

### Per-type `data` shapes

```jsonc
// overview
{ "kicker":"", "headline":"", "body":"",
  "cards":[ {"tag":"","title":"","text":""} ],
  "stepsTitle":"", "steps":["","",""] }

// concept_cards
{ "intro":"",
  "cards":[ { "badge":"", "name":"",
              "fields":[ {"label":"","text":"","tone":"neutral|good|info|bad|warn"} ],
              "highlight":{"label":"⚠ ...","q":"","a":""} } ] }

// flashcards
{ "cards":[ {"q":"","a":""} ] }

// glossary
{ "intro":"", "terms":[ {"t":"term","d":"definition"} ] }

// cheatsheet
{ "title":"", "intro":"",
  "blocks":[ {"title":"", "wide":true, "text":""},
             {"title":"", "items":["","",""]} ] }

// sequence
{ "title":"", "intro":"",
  "modes":[ { "key":"unique",
              "label":"button text",
              "items":[ {"id":"a","label":"","why":""} ],
              "correct":["a","b","c"] } ] }   // ids in correct order

// challenge
{ "kind":"quiz|rounds|timed|classify",
  "title":"", "intro":"", "startLabel":"", "timer":30,
  "rounds":[ {
     "title":"optional",
     "scenario":"optional (rounds/classify)",
     "constraints":["optional","chips"],
     "question":"",
     "opts":[ "plain string" | {"label":"","detail":""} ],
     "correct":0,
     "exp":"single explanation (quiz/timed)",
     "rightFeedback":"shown when correct (rounds/classify)",
     "wrongFeedback":["per-option, indexed like opts"]
  } ] }
```

Rules the generator must follow: `correct` is a 0-based index into `opts`; `wrongFeedback` is parallel to `opts` (use `null` for the correct slot); use `exp` **or** `rightFeedback`+`wrongFeedback`, not both; keep every module's `id` unique.

---

## 4. The generation prompt

Paste this as the system prompt, then send the source documents + a one-line instruction as the user message.

```
You are a course generator. You convert study material into a single JSON object
that drives an interactive study app. Output ONLY valid JSON — no markdown, no
prose, no code fences.

The JSON must match this schema exactly:
{ meta:{title,subtitle,learner}, modules:[ {type,id,label,data} ] }

Allowed module types and their data shapes:
- overview: {kicker, headline, body, cards:[{tag,title,text}], stepsTitle, steps:[...]}
- concept_cards: {intro, cards:[{badge, name, fields:[{label,text,tone}], highlight:{label,q,a}}]}
  tone is one of: neutral, good, info, bad, warn
- flashcards: {cards:[{q,a}]}
- glossary: {intro, terms:[{t,d}]}
- cheatsheet: {title, intro, blocks:[{title, wide?, text?, items?:[...]}]}
- sequence: {title, intro, modes:[{key,label,items:[{id,label,why}],correct:[ids in order]}]}
- challenge: {kind, title, intro, startLabel, timer?, rounds:[{title?, scenario?,
  constraints?:[], question, opts:[string | {label,detail}], correct (0-based index),
  exp? | (rightFeedback + wrongFeedback:[parallel to opts, null for correct slot])}]}
  kind is one of: quiz, rounds, timed, classify

Requirements:
- Build a coherent course from the material. Always include, in this order:
  one overview, one concept_cards, one flashcards, one challenge(kind:quiz),
  one glossary, one cheatsheet. Add a challenge(kind:rounds or classify) and a
  challenge(kind:timed) and a sequence when the material supports them.
- Every module id must be unique. Tab labels should be short and numbered.
- Ground every fact in the provided material. Do not invent facts. If something
  is ambiguous, leave it out rather than guess.
- Write a "highlight" / "watch out" box on each concept card calling out the
  single most common mistake or test trap for that concept.
- Match the requested audience: if the instruction says a grade level or "kid",
  set meta.learner="kid", keep language simple, friendly, and encouraging, and
  use concrete examples. Otherwise set meta.learner="adult".
- 8-12 flashcards, 6-10 quiz questions. Quizzes test understanding, not trivia.

Return the JSON object and nothing else.
```

Then the user turn is just:

```
INSTRUCTION: 6th grade science test on ecosystems and food webs, friendly tone.

MATERIAL:
<paste the chapter / study guide / notes here>
```

---

## 5. Local pipeline (matches your stack)

A ~30-line script ties it together. This uses Ollama (local, closed-loop). Swap `call_model` for the Anthropic or OpenAI API to use a stronger model.

```python
# build_course.py — documents + instruction -> finished_course.html
import json, re, sys
from pathlib import Path
import ollama

CHAT_MODEL = "llama3.1:8b"   # or a larger local model for better courses
TEMPLATE = Path("course_template.html")
SYSTEM = Path("generation_prompt.txt").read_text()   # the prompt from section 4

def call_model(system, user):
    resp = ollama.chat(
        model=CHAT_MODEL,
        messages=[{"role":"system","content":system},
                  {"role":"user","content":user}],
        options={"temperature": 0.2},
        format="json",          # ask Ollama to constrain output to JSON
    )
    return resp["message"]["content"]

def build(instruction, material, out="finished_course.html"):
    user = f"INSTRUCTION: {instruction}\n\nMATERIAL:\n{material}"
    raw = call_model(SYSTEM, user)
    course = json.loads(raw)                 # validate it parses
    assert course["modules"], "no modules generated"
    ids = [m["id"] for m in course["modules"]]
    assert len(ids) == len(set(ids)), "duplicate module ids"

    template = TEMPLATE.read_text()
    # replace everything between `const COURSE =` and the closing `;`
    injected = re.sub(
        r"const COURSE =\s*[\s\S]*?\n\s*;",
        "const COURSE =\n" + json.dumps(course, indent=2) + "\n;",
        template, count=1,
    )
    Path(out).write_text(injected)
    print(f"Wrote {out}  ({len(course['modules'])} modules)")

if __name__ == "__main__":
    instruction = sys.argv[1]
    material = Path(sys.argv[2]).read_text()
    build(instruction, material)
```

Run it:

```bash
python build_course.py "6th grade ecosystems test, friendly" study_guide.md
open finished_course.html
```

Because the generated JSON is strict JSON (and strict JSON is valid JS), injecting it as `const COURSE = <json>;` renders identically to the hand-written example.

---

## 6. Close the loop (reuse your RAG instincts)

A course generator has the same failure modes as a RAG system, and the same fix: **observe → classify → change one thing → re-run.** Build a tiny eval set so quality is measured, not vibed:

- **Faithfulness:** every fact in the JSON traces to the source material (no invented content). This is the same "grounded, no hallucination" check from your RAG evals.
- **Schema validity:** JSON parses, ids unique, `correct` indices in range, `wrongFeedback` parallel to `opts`.
- **Coverage:** the key concepts from the instruction all appear as cards/flashcards.
- **Answerability:** every quiz question is answerable from the flashcards/cards in the same course (no orphan questions).

When a generated course is weak, classify it (bad source coverage? prompt too loose? model too small?) and change one variable — exactly the discipline from the RAG eval tab.

---

## 7. Productization roadmap

You're closer than it looks — you already have the engine and the generator.

1. **CLI (today).** `build_course.py` above. Good enough to crank out study suites for your daughter tonight.
2. **Local web front end.** A small FastAPI/Flask page: upload a file, type an instruction, pick "kid / adult", click Generate → it runs the pipeline and returns the finished HTML to download or view. This is the "feed a front end documents and instructions" product you described.
3. **Library + sharing.** Save generated courses, list them, re-open. Add a difficulty toggle (the `learner` field already does tone; extend it to control question depth and count). Track which flashcards/quizzes a learner struggles with (the localStorage signals are already there) and regenerate a focused review set — a genuine closed loop for studying.
4. **Multi-tenant SaaS (later).** Auth, per-user libraries, a hosted model. Same separation holds: the engine is static; only the JSON is per-course.

A few product notes:
- **Keep the engine fixed and versioned.** Treat `course_template.html` as a release artifact. New component types are additive (add a `type`, add a render block, add state seeding) and never break old courses.
- **The `kid` vs `adult` switch is your differentiator.** Same engine, same generator, two audiences — one for your daughter's tests, one for your technical/architecture prep.
- **The generator prompt is your real IP.** The quality of the courses lives almost entirely in that prompt and the eval loop around it. Iterate on it like you iterate on a RAG prompt.

---

### What you have right now
- `course_template.html` — the reusable engine, rendering a complete 6th-grade course out of the box. Swap the `COURSE` object to make any course.
- This kit — the schema, the generation prompt, the local pipeline, and the roadmap to a front end.
