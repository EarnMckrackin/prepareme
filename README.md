# Prep Suite Generator

Turn any document into a finished, interactive study course (visual maps, flashcards,
sorting practice, teach-back prompts, quiz, build game, speed round, glossary,
cheat-sheet) — deployed as a production web app on **Vercel**.

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
For production, prefer **Vercel AI Gateway** so model routing, failover, observability,
and cost tracking happen behind one endpoint. Direct provider calls remain available for
BYOK and fallback use.

| Provider | Cost | Get a key |
|---|---|---|
| **Vercel AI Gateway** | Usage based | https://vercel.com/docs/ai-gateway |
| **Gemini** (default) | Free tier | https://aistudio.google.com/apikey |
| **Groq** | Free tier | https://console.groq.com/keys |
| **Grok / xAI** | Usage based | https://console.x.ai/ |
| **OpenAI** | Paid | https://platform.openai.com/api-keys |
| **OpenRouter** | Usage based | https://openrouter.ai/keys |
| **Anthropic** | Paid | https://console.anthropic.com/ |

There are two ways to supply a key:

1. **Server-side key** — set the env var in Vercel (e.g. `GEMINI_API_KEY`). Everyone using
   the site uses your free tier / account. This is the default.
2. **BYOK (bring your own key)** — a visitor pastes their own key into the form. It's used
   only for that request and never stored. Works even if no server key is set.

The form's **Model** dropdown picks the provider; leave the key field blank to use the
server key, or paste one to override.

## Learning preferences

The generator supports a **Study preference** dropdown:

- **Mixed modes** — balanced course flow for most learners.
- **Visual map-first** — prioritizes concept maps and relationship views.
- **Practice-first** — prioritizes sorting, sequencing, scenario challenges, and quizzes.
- **Read-first** — prioritizes structured notes, glossary, and printable study sheets.
- **Listen / verbal** — adds read-aloud script modules and teach-back practice.

These preferences change the module emphasis and order, but generated courses remain
multimodal so learners can switch strategies when they get stuck.

## Source material

The generator can combine multiple source types in one request:

- Uploaded documents: txt, md, csv, pdf, and docx.
- Direct URLs: fetched and extracted with SSRF safeguards.
- Tavily web searches: set `TAVILY_API_KEY`, then enter one search query per line.
- Pasted text: useful for notes, transcripts, or hand-curated excerpts.

## Deploy to Vercel

1. Push this folder to a Git repo (GitHub/GitLab/Bitbucket).
2. In Vercel: **Add New → Project → Import** that repo. No build settings needed —
   `vercel.json` wires everything up (Python serverless function + routing).
3. **Settings → Environment Variables**, add at least one key. To match the default:
   - `PREP_BACKEND` = `gateway`
   - `AI_GATEWAY_API_KEY` = your Vercel AI Gateway key
   - (optional) direct-provider keys: `GEMINI_API_KEY`, `GROQ_API_KEY`, `XAI_API_KEY`,
     `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `ANTHROPIC_API_KEY`
   - (optional) OpenRouter attribution headers: `OPENROUTER_SITE_URL` and
     `OPENROUTER_APP_NAME`
   - (optional) web search source: `TAVILY_API_KEY`
   - (optional) shared rate limit: `UPSTASH_REDIS_REST_URL` and
     `UPSTASH_REDIS_REST_TOKEN` (or Vercel KV REST equivalents)
   - (optional) persisted course links: `PREP_STORE_COURSES=1` plus
     `BLOB_READ_WRITE_TOKEN` from a Vercel Blob store
4. **Deploy**. Open the URL, upload a document, describe what you want, Generate.

When you hit a provider limit, either use AI Gateway failover, switch the dropdown to
another provider, add a paid key as the relevant env var, or set `PREP_BACKEND` to the
provider you prefer.

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

## Tests / QA

An offline QA suite covers the core logic without needing network or the runtime deps
(it stubs `httpx`/`fastapi` and exercises validation, JSON extraction, template injection,
the provider tables, the `build_course` retry loop, rate limiting, and the SSRF guard):

```bash
python3 tests/run_qa.py    # exits non-zero on any failure
```

For a true end-to-end check, run a Vercel **preview deploy** (or `vercel dev`) with an API
key set, since live model + URL fetching can't run in a sandbox.

## Notes

- **No persistence.** Serverless storage is ephemeral, so the generated course is returned
  in the response and the browser builds a Blob URL for **Open** / **Download** by default.
  Set `PREP_STORE_COURSES=1` with Vercel Blob to return shareable persisted URLs instead.
  Downloaded courses still load Alpine + Tailwind from CDN.
- **Self-correcting generation.** `validate()` enforces every rule the template relies on;
  if the model slips, one retry feeds the errors back before failing with a clear message.
- **Add a provider** by adding one function + one `PROVIDERS` entry in `_generator.py`.
- **Rate limiting.** The app uses a shared Upstash/Vercel KV REST counter when configured;
  otherwise it falls back to warm-instance in-memory limiting. Add Vercel WAF/BotID rules
  at the project edge for stronger public deployments.
- **Legacy folder.** `legacy/` is reference-only and excluded from the function bundle by
  `vercel.json` (`includeFiles: api/**`).
