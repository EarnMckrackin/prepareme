# Prep Suite Generator

Turn any document into a finished, interactive study course (flashcards, quiz, build game,
speed round, glossary, cheat-sheet) — deployed as a production web app on **Vercel**.

```
document / pasted text + instruction + audience + model provider
        │
        ▼  (api/index.py — FastAPI serverless function)
   extract text → build_course() → hosted LLM → strict COURSE JSON → validate
        │
        ▼  inject JSON into the course template
   finished standalone .html  → returned inline → browser opens / downloads it
```

## Model providers

This app calls **hosted** LLMs over HTTP (no local model — serverless can't run Ollama).
You can use a free tier and only switch to a paid key when you hit limits.

| Provider | Cost | Get a key |
|---|---|---|
| **Gemini** (default) | Free tier | https://aistudio.google.com/apikey |
| **Groq** | Free tier | https://console.groq.com/keys |
| **OpenAI** | Paid | https://platform.openai.com/api-keys |
| **Anthropic** | Paid | https://console.anthropic.com/ |

There are two ways to supply a key:

1. **Server-side key** — set the env var in Vercel (e.g. `GEMINI_API_KEY`). Everyone using
   the site uses your free tier / account. This is the default.
2. **BYOK (bring your own key)** — a visitor pastes their own key into the form. It's used
   only for that request and never stored. Works even if no server key is set.

The form's **Model** dropdown picks the provider; leave the key field blank to use the
server key, or paste one to override.

## Deploy to Vercel

1. Push this folder to a Git repo (GitHub/GitLab/Bitbucket).
2. In Vercel: **Add New → Project → Import** that repo. No build settings needed —
   `vercel.json` wires everything up (Python serverless function + routing).
3. **Settings → Environment Variables**, add at least one key. To match the default:
   - `PREP_BACKEND` = `gemini`
   - `GEMINI_API_KEY` = your free Gemini key
   - (optional) `GROQ_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` for the other options
4. **Deploy**. Open the URL, upload a document, describe what you want, Generate.

When you hit a free-tier limit, either switch the dropdown to another provider, add a paid
key as the relevant env var, or set `PREP_BACKEND` to the paid provider you prefer.

## Local development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # fill in a key
export $(grep -v '^#' .env | xargs)   # or use your own dotenv loader
uvicorn api.index:app --reload --port 8000
# open http://localhost:8000
```

## Layout

```
api/
  index.py               # FastAPI serverless function: UI + /api/generate + /api/config
  _generator.py          # engine: prompt, HTTP providers, schema validation, injection
  _course_template.html  # the fixed rendering engine (course JSON is injected into it)
vercel.json              # Python function config + route-all rewrite
requirements.txt
.env.example
legacy/                  # the original local-only Ollama/FastAPI version, for reference
```

> Files in `api/` prefixed with `_` are bundled as helpers but not treated as separate
> serverless functions by Vercel.

## Notes

- **No persistence.** Serverless storage is ephemeral, so the generated course is returned
  in the response and the browser builds a Blob URL for **Open** / **Download**. The
  downloaded `.html` is fully standalone (course JSON baked in, Alpine + Tailwind via CDN).
- **Self-correcting generation.** `validate()` enforces every rule the template relies on;
  if the model slips, one retry feeds the errors back before failing with a clear message.
- **Add a provider** by adding one function + one `PROVIDERS` entry in `_generator.py`.
