"""
_generator.py — the engine of the prep suite (serverless / multi-provider build).

documents + instruction  ->  strict COURSE json  ->  validated  ->  injected into template

This is the reusable core. api/index.py (the web front end) is a thin wrapper around it.

All model calls go over plain HTTP (httpx) so the serverless bundle stays small and
cold-starts stay fast — no heavy vendor SDKs. Add a provider by adding one function and
one entry to PROVIDERS.

Providers:
  - gateway    (Vercel AI Gateway — unified model routing)
  - gemini     (Google AI Studio — generous free tier)   default
  - groq       (Groq — fast free tier, OpenAI-compatible)
  - grok       (xAI Grok — OpenAI-compatible)
  - openai     (paid fallback)
  - anthropic  (paid fallback)
"""

import json
import logging
import os
import re
from pathlib import Path

import httpx


log = logging.getLogger(__name__)


class GenerationError(Exception):
    """Raised when generation or validation fails in a way worth showing the user."""


def normalize_url(url: str) -> str:
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    return url


def _regex_html_to_text(html: str) -> str:
    """Dependency-free fallback: strip tags into rough plain text."""
    html = re.sub(r"(?is)<(script|style|noscript|head)[^>]*>.*?</\1>", " ", html)
    html = re.sub(r"(?is)<br\s*/?>", "\n", html)
    html = re.sub(r"(?is)</(p|div|li|h[1-6]|tr)>", "\n", html)
    text = re.sub(r"(?s)<[^>]+>", " ", html)
    for a, b in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">"),
                 ("&quot;", '"'), ("&#39;", "'")):
        text = text.replace(a, b)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n\s*\n+", "\n\n", text).strip()
    return text


def extract_main_text(html: str, url: str = "", max_chars: int = 40000) -> str:
    """Pull the readable main content out of an HTML page.

    Prefers trafilatura (readability-style main-content detection, drops nav/ads/boilerplate);
    falls back to a built-in regex cleaner if trafilatura is unavailable or returns nothing.
    """
    text = ""
    try:
        import trafilatura
        extracted = trafilatura.extract(
            html, url=url or None,
            include_comments=False, include_tables=True,
            favor_recall=True, no_fallback=False,
        )
        if extracted:
            text = extracted.strip()
    except Exception:
        text = ""
    if not text:
        text = _regex_html_to_text(html)
    return text[:max_chars]


def fetch_url_text(url: str, max_chars: int = 40000) -> str:
    """Synchronous fetch + extract for a single URL (used in CLI/local contexts)."""
    url = normalize_url(url)
    try:
        with httpx.Client(timeout=httpx.Timeout(30.0, connect=10.0),
                          follow_redirects=True,
                          headers={"User-Agent": "Mozilla/5.0 (PrepSuiteBot)"}) as c:
            r = c.get(url)
    except httpx.HTTPError as e:
        raise GenerationError(f"Could not fetch {url} ({type(e).__name__}).")
    if r.status_code != 200:
        raise GenerationError(f"Could not fetch {url} (HTTP {r.status_code}).")
    text = extract_main_text(r.text, url=url, max_chars=max_chars)
    if not text:
        raise GenerationError(f"Fetched {url} but found no readable text.")
    return text


# ----------------------------------------------------------------------------
# 1. The generation prompt (kept in sync with the COURSE schema)
# ----------------------------------------------------------------------------
SYSTEM_PROMPT = """You are an expert teacher and course architect. Your job is to TEACH a subject, then express that teaching as a single JSON object that drives an interactive study app. Output ONLY valid JSON — no markdown, no prose, no code fences.

THINK LIKE A SUBJECT-MATTER EXPERT WRITING A REAL COURSE — NOT A KEYWORD INDEXER.
The single most common failure mode you must avoid is producing a shallow "word-association"
course: vague one-line definitions, restated labels, and synonyms with no actual instruction.
That output is unacceptable. A learner who finishes your course must come away understanding
the real material: the concepts explained, the mechanics shown, worked examples carried out,
concrete artifacts written down (actual scales, chords, formulas, code, dates, equations,
diagrams-in-text), and the common mistakes named. If you cannot teach a point with real
substance, do not include a hollow placeholder for it — teach a different point properly.

HOW TO USE THE PROVIDED MATERIAL:
- Treat the provided material as the SCOPE, focus, and syllabus for the course — what to cover
  and at what level — NOT as the only sentences you are allowed to use.
- You are an authority on the subject. Bring in accurate, established domain knowledge to
  actually explain and demonstrate each topic, even when the source material only names it.
  A topic like "voice leading," "the Krebs cycle," "gradient descent," or "the subjunctive"
  must be explained and demonstrated, not merely listed.
- Be factually correct. Use standard, well-established knowledge and real, checkable examples.
  Do NOT fabricate claims about the user's specific/proprietary material, private data, or
  numbers that would have to come from their document. Everything else: teach it for real.

The JSON must match this schema exactly:
{ "meta": {"title","subtitle","learner","learningStyle"}, "modules": [ {"type","id","label","data"} ] }

Allowed module types and their data shapes:
- overview: {kicker, headline, body, cards:[{tag,title,text}], stepsTitle, steps:[...]}
- concept_cards: {intro, cards:[{badge, name, fields:[{label,text,tone}], highlight:{label,q,a}}]}
  tone is one of: neutral, good, info, bad, warn
- flashcards: {cards:[{q,a}]}
- visual_map: {title, intro, nodes:[{id,label,tag,summary}], links:[{from,to,label}]}
- drag_sort: {title, intro, buckets:[{id,label,hint}], items:[{id,label,detail,bucket}]}
- teach_back: {title, intro, prompts:[{q,keyPoints:[...],sample}]}
- notes: {title, intro, sections:[{heading,summary,bullets:[...],check}]}
- audio_script: {title, intro, segments:[{label,text}]}
- glossary: {intro, terms:[{t,d}]}
- cheatsheet: {title, intro, blocks:[{title, wide(optional bool), text(optional), items(optional array)}]}
- sequence: {title, intro, modes:[{key, label, items:[{id,label,why}], correct:[ids in correct order]}]}
- challenge: {kind, title, intro, startLabel, timer(optional int), rounds:[{title(optional), scenario(optional), constraints(optional array), question, opts:[string OR {label,detail}], correct (0-based index into opts), exp(optional) OR (rightFeedback AND wrongFeedback array parallel to opts with null in the correct slot)}]}
  kind is one of: quiz, rounds, timed, classify

Course design requirements:
- First infer the learning domain from the instruction and material. Do NOT reuse a job-prep,
  interview, business, or software framing unless the user explicitly asks for that. A music,
  arts, language, fitness, craft, or hobby topic should become a guided skill-practice journey,
  not a career-prep course.
- Build a complete, domain-specific course from the material. Always include these modules:
  one overview, one visual_map, one concept_cards, one drag_sort, one flashcards,
  one challenge with kind "quiz", one teach_back, one challenge with kind "rounds",
  one challenge with kind "timed" and timer 20, one glossary, one notes, one cheatsheet,
  and one sequence. Add audio_script when the learner preference is audio.
- Domain adaptation examples:
  * Jazz/music: use listening, ear training, harmonic movement, instrument/repertoire practice,
    improvisation choices, chord-scale relationships, voice-leading, transcription, and practice
    routine language. Rounds should feel like musical decisions, not workplace cases.
  * Programming/AI/web: use build steps, debugging, architecture decisions, and implementation drills.
  * Academic/test prep: use misconceptions, worked examples, retrieval practice, and exam traps.
  * Professional/interview prep: use role pressure, executive framing, decision judgment, and answer drills.
- Make the course as rich as the curated examples: each module should teach or practice a distinct
  skill, not repeat the same summary in different formats.

DEPTH CONTRACT (NON-NEGOTIABLE):
- Every explanatory text must be substantive prose, not a label or a synonym. Concept-card field
  text, notes summaries, glossary definitions, flashcard answers, and quiz explanations should be
  full multi-sentence explanations that (1) define the idea precisely, (2) explain HOW/WHY it
  works, and (3) include a CONCRETE, specific example with real artifacts.
- "Concrete artifacts" means actual content, written out in text:
    * Music: spell scales and chords by note name and degree (e.g. "C major = C D E F G A B";
      "Dmin7 = D F A C, the ii of C"); write a real ii–V–I in a named key; describe voice-leading
      by which notes move where; give simple fret/string or fingering hints in text.
    * Programming/CS: include short, correct code snippets, exact commands, signatures, or
      step-by-step algorithm traces.
    * Math/science: write real equations, units, and a worked numeric example with the steps.
    * Language: give real example sentences with translation/gloss and the rule applied.
    * History/humanities: cite specific events, dates, people, causes, and consequences.
- BAD (forbidden): {"label":"Definition","text":"Improvisation is making up music spontaneously."}
  GOOD (required): {"label":"Definition","text":"Improvisation is composing melody in real time
  over a chord progression by choosing notes from the chord tones and a matching scale. Over a
  Dmin7–G7–Cmaj7 (ii–V–I in C), you can play D Dorian over Dmin7, G Mixolydian over G7, and C
  major over Cmaj7 — these are the same seven notes, so the trick is targeting the chord tones
  (3rds and 7ths) on the strong beats while the others connect them."}
- Concept cards must read like mini-lessons: 3–4 fields, and at least one field is a worked,
  specific EXAMPLE (not a generality). The highlight box names the single most common real mistake
  and how to fix it — also specifically, not generically.
- Notes sections must contain teaching prose plus bullets that carry real, specific information.
- The cheatsheet must hold quick-reference facts a learner would actually want at hand (formulas,
  spellings, key tables, command lists), not slogans.
- Treat the visual_map as an actual diagram, not a list. Each node should represent a conceptual
  role and each link should explain the relationship between roles or functions, with a specific
  summary on each node (e.g. what it is and one concrete instance), not a 4-word tag.
- Quiz/rounds/timed questions test real understanding and application of the taught material;
  wrong options should be plausible misconceptions, and explanations should teach why.
- Quantity targets:
  overview cards 3-5; concept cards 5-8 with 3-4 fields each; flashcards 10-12;
  quiz questions 8-10; glossary terms 10-16; notes sections 4-8; cheatsheet blocks 5-8;
  visual map nodes 5-9; drag_sort items 8-12; teach_back prompts 4-6;
  sequence modes 1-3 with 5-8 items each; rounds challenge 4-7 rounds;
  timed challenge 6-10 rounds.
- If the topic is music, include at least one visual map that reads like a theory diagram
  (for example: tonic/function/voice-leading/improvisation choices), and make the expandable
  concept cards explain the theory in plain language with concrete instrument-level examples.
- If learningStyle is visual, put visual_map before concept_cards. If practice, put drag_sort,
  sequence, and challenge modules earlier. If read, put notes and cheatsheet earlier. If audio,
  put audio_script near the top. If mixed, balance the order naturally.
- Every module id must be unique and lowercase. Tab labels should be short and numbered (e.g. "1. Big Idea").
- Be accurate: teach the real subject with correct, well-established knowledge and real examples.
  Do not fabricate claims about the user's private/proprietary material or invent numbers that
  would have to come from their specific document; for everything else, teach it fully and concretely.
- On each concept card, write a "highlight" box (label starts with an emoji like ⚠) calling out the single most common mistake or test trap for that concept.
- Match the requested audience. If the instruction names a grade level or says "kid", set meta.learner="kid", keep language simple, friendly and encouraging, use concrete examples. Otherwise set meta.learner="adult".
- Set meta.learningStyle to one of: mixed, visual, practice, read, audio.
- 8 to 12 flashcards. 6 to 10 quiz questions. Questions test understanding, not trivia.
- "correct" is a 0-based index into "opts". For rounds/classify, "wrongFeedback" is parallel to "opts" (use null for the correct slot). Use "exp" OR rightFeedback+wrongFeedback, not both.

Return the JSON object and nothing else."""


def _course_design_hint(instruction: str, material: str) -> str:
    haystack = f"{instruction}\n{material[:4000]}".lower()
    if re.search(r"\b(jazz|music|musical|chord|scale|harmony|harmonic|melody|improv|improvis|piano|guitar|sax|trumpet|bass|drum|ear training|voice[- ]?leading)\b", haystack):
        return (
            "Course archetype: creative musical practice path. Structure the experience as a "
            "guided progression from hearing/recognizing ideas to applying them on an instrument "
            "or in improvisation. Use drills such as ear-training choices, chord/scale fit, "
            "voice-leading order, listening analysis, repertoire study, and practice routines. "
            "Make the visual map read like a theory diagram and make expandable concept cards "
            "teach actual theory, not just labels. You MUST write out real musical artifacts in "
            "text: spell scales and chords by note name and scale degree, give at least one real "
            "ii–V–I (or relevant progression) in a named key, describe specific voice-leading "
            "moves (which note resolves where), and include concrete guitar/piano examples "
            "(fret/string or fingering hints). Concept cards and notes should read like a real "
            "theory lesson with worked examples, not a glossary. "
            "Avoid interview, employer, resume, product, or job-prep framing unless the instruction "
            "explicitly requests it."
        )
    if re.search(r"\b(interview|job|career|resume|onsite|hiring|role|stakeholder|executive)\b", haystack):
        return (
            "Course archetype: professional readiness path. Emphasize role-specific judgment, "
            "answer practice, decision pressure, narrative clarity, and scenario drills."
        )
    if re.search(r"\b(code|programming|javascript|html|css|python|react|api|gen ai|llm|rag|model|software|web app)\b", haystack):
        return (
            "Course archetype: technical build lab. Emphasize concepts, implementation sequence, "
            "debugging choices, architecture tradeoffs, and hands-on build/apply challenges."
        )
    if re.search(r"\b(test|exam|grade|school|quiz|homework|class|biology|history|math|science)\b", haystack):
        return (
            "Course archetype: academic mastery path. Emphasize misconception repair, worked "
            "examples, retrieval practice, and exam-style understanding checks."
        )
    return (
        "Course archetype: guided learning path. Adapt the module names, examples, drills, "
        "sequence, and challenge scenarios to the actual subject instead of using a generic "
        "job-prep or software-project frame."
    )


def _user_message(instruction: str, learner: str, material: str,
                  context: str = "", learning_style: str = "mixed",
                  max_chars: int = 24000) -> str:
    learner_hint = ("Audience: a child / the specified grade level. Use meta.learner=\"kid\"."
                    if learner == "kid" else
                    "Audience: an adult learner. Use meta.learner=\"adult\".")
    style_hint = (
        "Study preference: "
        f"{learning_style if learning_style in {'mixed', 'visual', 'practice', 'read', 'audio'} else 'mixed'}. "
        "Use this as a starting preference, but keep the course multimodal."
    )
    trimmed = material[:max_chars]
    if len(material) > max_chars:
        trimmed += "\n\n[material truncated for length]"
    context_block = f"\nADDITIONAL CONTEXT (goals, constraints, focus areas):\n{context.strip()}\n" \
        if context and context.strip() else ""
    design_hint = _course_design_hint(instruction, material)
    depth_demand = (
        "DEPTH REQUIREMENT: Teach the actual subject. Use the material below as the scope and "
        "focus, but draw on your full expert knowledge to explain every concept with real "
        "substance and concrete, worked examples (actual notes/chords/formulas/code/equations/"
        "events as appropriate). Reject any output that is just labels, synonyms, or one-line "
        "definitions — that is a failed course. A learner should finish genuinely understanding "
        "the topic."
    )
    return (f"INSTRUCTION: {instruction}\n{learner_hint}\n{style_hint}\n"
            f"COURSE DESIGN ADAPTATION:\n{design_hint}\n{depth_demand}\n"
            f"{context_block}\nMATERIAL:\n{trimmed}")


# ----------------------------------------------------------------------------
# 2. Model backends — all over HTTP. Each returns the raw text the model emitted.
# ----------------------------------------------------------------------------
# Default model per provider. Override with PREP_MODEL or a per-request `model`.
DEFAULT_MODELS = {
    "gateway": "openai/gpt-5.4",
    "gemini": "gemini-2.0-flash",
    "groq": "llama-3.3-70b-versatile",
    "grok": "grok-3-mini",
    "openai": "gpt-4o-mini",
    "openrouter": "openrouter/free",
    "anthropic": "claude-sonnet-4-20250514",
}

# Which env var holds each provider's key.
ENV_KEYS = {
    "gateway": "AI_GATEWAY_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "grok": "XAI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

_HTTP_TIMEOUT = httpx.Timeout(120.0, connect=15.0)


def _max_output_tokens() -> int:
    raw = os.environ.get("PREP_MAX_OUTPUT_TOKENS", "").strip()
    try:
        value = int(raw) if raw else 12000
    except ValueError:
        value = 12000
    return max(4000, min(value, 24000))


def _strict_generation_required() -> bool:
    # Strict generation is ON by default: a shallow, schema-valid course is treated as a failure
    # so the engine regenerates instead of shipping word-association filler. Opt out explicitly
    # (PREP_STRICT_GENERATION=0/false/no) to allow the warning-tagged fallback instead.
    raw = os.environ.get("PREP_STRICT_GENERATION", "").strip().lower()
    if raw in {"0", "false", "no", "off"}:
        return False
    return True


def _call_gemini(system: str, user: str, api_key: str, model: str) -> str:
    url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
           f"{model}:generateContent")
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": user}]}],
        "generationConfig": {"temperature": 0.3, "response_mime_type": "application/json"},
    }
    with httpx.Client(timeout=_HTTP_TIMEOUT) as c:
        r = c.post(url, headers={"x-goog-api-key": api_key}, json=payload)
    _raise_for_provider(r, "Gemini")
    data = r.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise GenerationError(f"Gemini returned no content: {json.dumps(data)[:300]}")


def _call_openai_compatible(system: str, user: str, api_key: str, model: str,
                            base_url: str, label: str,
                            extra_headers: dict[str, str] | None = None) -> str:
    payload = {
        "model": model,
        "temperature": 0.3,
        "max_tokens": _max_output_tokens(),
        "response_format": {"type": "json_object"},
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    if extra_headers:
        headers.update(extra_headers)
    with httpx.Client(timeout=_HTTP_TIMEOUT) as c:
        r = c.post(f"{base_url}/chat/completions", headers=headers, json=payload)
    _raise_for_provider(r, label)
    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        raise GenerationError(f"{label} returned no content: {json.dumps(data)[:300]}")


def _call_gateway(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://ai-gateway.vercel.sh/v1", "AI Gateway")


def _call_groq(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.groq.com/openai/v1", "Groq")


def _call_grok(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.x.ai/v1", "Grok")


def _call_openai(system: str, user: str, api_key: str, model: str) -> str:
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://api.openai.com/v1", "OpenAI")


def _call_openrouter(system: str, user: str, api_key: str, model: str) -> str:
    headers = {}
    site_url = os.environ.get("OPENROUTER_SITE_URL", "").strip()
    app_name = os.environ.get("OPENROUTER_APP_NAME", "").strip()
    if site_url:
        headers["HTTP-Referer"] = site_url
    if app_name:
        headers["X-Title"] = app_name
    return _call_openai_compatible(system, user, api_key, model,
                                   "https://openrouter.ai/api/v1", "OpenRouter",
                                   extra_headers=headers)


def _call_anthropic(system: str, user: str, api_key: str, model: str) -> str:
    payload = {
        "model": model,
        "max_tokens": _max_output_tokens(),
        "temperature": 0.3,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}
    with httpx.Client(timeout=_HTTP_TIMEOUT) as c:
        r = c.post("https://api.anthropic.com/v1/messages", headers=headers, json=payload)
    _raise_for_provider(r, "Anthropic")
    data = r.json()
    try:
        return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text")
    except (KeyError, TypeError):
        raise GenerationError(f"Anthropic returned no content: {json.dumps(data)[:300]}")


PROVIDERS = {
    "gateway": _call_gateway,
    "gemini": _call_gemini,
    "groq": _call_groq,
    "grok": _call_grok,
    "openai": _call_openai,
    "openrouter": _call_openrouter,
    "anthropic": _call_anthropic,
}


def _raise_for_provider(r: httpx.Response, label: str) -> None:
    if r.status_code == 200:
        return
    detail = r.text[:300]
    log.warning("%s provider error HTTP %s: %s", label, r.status_code, detail)
    if r.status_code in (401, 403):
        raise GenerationError(f"{label} rejected the API key (HTTP {r.status_code}). "
                              "Check the key and that the API is enabled.")
    if r.status_code == 429:
        raise GenerationError(f"{label} rate limit / quota hit (HTTP 429). "
                              "Wait a moment or switch providers / add a paid key.")
    raise GenerationError(f"{label} could not complete the request (HTTP {r.status_code}). "
                          "Try again or switch providers.")


def resolve_provider(requested: str | None) -> str:
    provider = (requested or os.environ.get("PREP_BACKEND") or "gemini").lower()
    if provider not in PROVIDERS:
        raise GenerationError(f"Unknown provider '{provider}'. "
                              f"Choose one of: {', '.join(PROVIDERS)}.")
    return provider


def resolve_key(provider: str, requested_key: str | None) -> str:
    key = (requested_key or "").strip() or os.environ.get(ENV_KEYS[provider], "").strip()
    if not key:
        raise GenerationError(
            f"No API key for '{provider}'. Set {ENV_KEYS[provider]} in the environment "
            f"or paste a key in the form (BYOK).")
    return key


def _generate_json(system: str, user: str, provider: str, api_key: str, model: str) -> str:
    return PROVIDERS[provider](system, user, api_key, model)


# ----------------------------------------------------------------------------
# 3. Parsing + validation
# ----------------------------------------------------------------------------
def _extract_json(raw: str) -> dict:
    """Be forgiving: strip code fences and grab the outermost {...} if needed."""
    s = raw.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        a, b = s.find("{"), s.rfind("}")
        if a == -1 or b == -1 or b <= a:
            raise GenerationError("Model did not return JSON.")
        try:
            return json.loads(s[a:b + 1])
        except json.JSONDecodeError as e:
            raise GenerationError(f"Model returned invalid JSON: {e}")


VALID_TYPES = {"overview", "concept_cards", "flashcards", "visual_map",
               "drag_sort", "teach_back", "notes", "audio_script",
               "glossary", "cheatsheet", "sequence", "challenge"}
VALID_KINDS = {"quiz", "rounds", "timed", "classify"}
VALID_STYLES = {"mixed", "visual", "practice", "read", "audio"}
REQUIRED_GENERATED_TYPES = {"overview", "concept_cards", "flashcards", "visual_map",
                            "drag_sort", "teach_back", "notes", "glossary",
                            "cheatsheet", "sequence"}
REQUIRED_GENERATED_CHALLENGES = {"quiz", "rounds", "timed"}
MIN_GENERATED_MODULES = 12


def _repair_course(course: dict) -> None:
    """Fix common, harmless model formatting mistakes in place before validation.

    Models (especially smaller ones) reliably trip on a few schema details. Rather than burn
    retries on output that is substantively fine, normalize the well-understood mistakes:
      - challenge round `wrongFeedback` not parallel to `opts` (the classic: one entry per
        WRONG option instead of a full-length array with null in the correct slot).
      - `correct` provided as a string label or 1-based number instead of a 0-based index.
    The renderer already tolerates missing feedback slots, so this only loses malformed extras.
    """
    if not isinstance(course, dict):
        return
    for module in course.get("modules", []) or []:
        if not isinstance(module, dict) or module.get("type") != "challenge":
            continue
        data = module.get("data")
        if not isinstance(data, dict):
            continue
        for rnd in data.get("rounds", []) or []:
            if not isinstance(rnd, dict):
                continue
            opts = rnd.get("opts")
            if not isinstance(opts, list) or not opts:
                continue
            n = len(opts)

            # Rounds-style output often supplies `scenario` but forgets `question`.
            if not rnd.get("question"):
                scenario = rnd.get("scenario")
                if isinstance(scenario, str) and scenario.strip():
                    rnd["question"] = scenario.strip()
                    rnd.pop("scenario", None)
                else:
                    rnd["question"] = "Which option is the best choice here?"

            # Coerce a stringy / 1-based correct index into a 0-based int when unambiguous.
            correct = rnd.get("correct")
            if isinstance(correct, str):
                labels = [o if isinstance(o, str) else (o.get("label") if isinstance(o, dict) else None)
                          for o in opts]
                if correct in labels:
                    correct = labels.index(correct)
                elif correct.strip().isdigit():
                    correct = int(correct.strip())
                rnd["correct"] = correct
            if isinstance(correct, int) and correct == n and n >= 1:
                # looks 1-based
                rnd["correct"] = correct - 1
                correct = rnd["correct"]
            if not isinstance(correct, int) or not (0 <= correct < n):
                correct = None

            # Normalize wrongFeedback. Models sometimes emit it as a dict keyed by index/label,
            # or as a string — coerce to a list, else drop it (the renderer tolerates absence).
            wf = rnd.get("wrongFeedback")
            if wf is not None and not isinstance(wf, list):
                if isinstance(wf, dict):
                    coerced: list = [None] * n
                    for k, v in wf.items():
                        try:
                            idx = int(k)
                        except (TypeError, ValueError):
                            continue
                        if 0 <= idx < n:
                            coerced[idx] = v
                    wf = coerced
                    rnd["wrongFeedback"] = wf
                else:
                    rnd.pop("wrongFeedback", None)
                    wf = None
            if isinstance(wf, list) and len(wf) != n:
                fixed = [None] * n
                src = list(wf)
                si = 0
                for i in range(n):
                    if i == correct:
                        continue
                    if si < len(src):
                        fixed[i] = src[si]
                        si += 1
                if correct is not None:
                    fixed[correct] = None
                rnd["wrongFeedback"] = fixed
            elif isinstance(wf, list) and correct is not None and correct < n:
                wf[correct] = None


def validate(course: dict) -> list[str]:
    """Return a list of problems. Empty list == valid. Mirrors what the engine needs."""
    errs: list[str] = []
    if not isinstance(course, dict):
        return ["Top level is not an object."]

    meta = course.get("meta")
    if not isinstance(meta, dict) or not meta.get("title"):
        errs.append("meta.title is required.")
    if meta and meta.get("learner") not in (None, "kid", "adult"):
        errs.append("meta.learner must be 'kid' or 'adult'.")
    if meta and meta.get("learningStyle") not in (None, *VALID_STYLES):
        errs.append("meta.learningStyle must be one of mixed, visual, practice, read, audio.")

    modules = course.get("modules")
    if not isinstance(modules, list) or not modules:
        return errs + ["modules must be a non-empty array."]

    seen_ids = set()
    for i, m in enumerate(modules):
        where = f"module[{i}]"
        if not isinstance(m, dict):
            errs.append(f"{where} is not an object."); continue
        mid, mtype = m.get("id"), m.get("type")
        if not mid:
            errs.append(f"{where} missing id.")
        elif mid in seen_ids:
            errs.append(f"{where} duplicate id '{mid}'.")
        else:
            seen_ids.add(mid)
        if mtype not in VALID_TYPES:
            errs.append(f"{where} invalid type '{mtype}'."); continue
        if not m.get("label"):
            errs.append(f"{where} ({mtype}) missing label.")
        data = m.get("data")
        if not isinstance(data, dict):
            errs.append(f"{where} ({mtype}) missing data object."); continue

        if mtype == "flashcards":
            cards = data.get("cards")
            if not isinstance(cards, list) or not cards:
                errs.append(f"{where} flashcards need a non-empty cards array.")
            else:
                for j, c in enumerate(cards):
                    if not (c.get("q") and c.get("a")):
                        errs.append(f"{where} card[{j}] needs q and a.")
        elif mtype == "glossary":
            if not isinstance(data.get("terms"), list) or not data["terms"]:
                errs.append(f"{where} glossary needs a terms array.")
        elif mtype == "concept_cards":
            if not isinstance(data.get("cards"), list) or not data["cards"]:
                errs.append(f"{where} concept_cards needs a cards array.")
        elif mtype == "visual_map":
            nodes = data.get("nodes")
            links = data.get("links")
            if not isinstance(nodes, list) or not nodes:
                errs.append(f"{where} visual_map needs a nodes array.")
            elif not isinstance(links, list):
                errs.append(f"{where} visual_map needs a links array.")
            else:
                ids = {n.get("id") for n in nodes if isinstance(n, dict)}
                for j, link in enumerate(links):
                    if link.get("from") not in ids or link.get("to") not in ids:
                        errs.append(f"{where} link[{j}] must reference node ids.")
        elif mtype == "drag_sort":
            buckets = data.get("buckets")
            items = data.get("items")
            if not isinstance(buckets, list) or len(buckets) < 2:
                errs.append(f"{where} drag_sort needs at least two buckets.")
            elif not isinstance(items, list) or not items:
                errs.append(f"{where} drag_sort needs an items array.")
            else:
                bucket_ids = {b.get("id") for b in buckets if isinstance(b, dict)}
                for j, item in enumerate(items):
                    if item.get("bucket") not in bucket_ids:
                        errs.append(f"{where} item[{j}] bucket must reference a bucket id.")
        elif mtype == "teach_back":
            prompts = data.get("prompts")
            if not isinstance(prompts, list) or not prompts:
                errs.append(f"{where} teach_back needs a prompts array.")
            else:
                for j, prompt in enumerate(prompts):
                    if not prompt.get("q") or not isinstance(prompt.get("keyPoints"), list):
                        errs.append(f"{where} prompt[{j}] needs q and keyPoints.")
        elif mtype == "notes":
            sections = data.get("sections")
            if not isinstance(sections, list) or not sections:
                errs.append(f"{where} notes needs a sections array.")
        elif mtype == "audio_script":
            segments = data.get("segments")
            if not isinstance(segments, list) or not segments:
                errs.append(f"{where} audio_script needs a segments array.")
        elif mtype == "sequence":
            modes = data.get("modes")
            if not isinstance(modes, list) or not modes:
                errs.append(f"{where} sequence needs a modes array.")
            else:
                for j, mode in enumerate(modes):
                    items = mode.get("items", [])
                    ids = {it.get("id") for it in items}
                    correct = mode.get("correct", [])
                    if not items or not correct:
                        errs.append(f"{where} mode[{j}] needs items and correct.")
                    elif set(correct) != ids:
                        errs.append(f"{where} mode[{j}] correct ids must match item ids.")
        elif mtype == "challenge":
            kind = data.get("kind")
            if kind not in VALID_KINDS:
                errs.append(f"{where} challenge invalid kind '{kind}'.")
            rounds = data.get("rounds")
            if not isinstance(rounds, list) or not rounds:
                errs.append(f"{where} challenge needs a rounds array.")
            else:
                for j, r in enumerate(rounds):
                    opts = r.get("opts")
                    if not isinstance(opts, list) or len(opts) < 2:
                        errs.append(f"{where} round[{j}] needs >=2 opts."); continue
                    c = r.get("correct")
                    if not isinstance(c, int) or not (0 <= c < len(opts)):
                        errs.append(f"{where} round[{j}] correct index out of range.")
                    if not r.get("question"):
                        errs.append(f"{where} round[{j}] missing question.")
                    wf = r.get("wrongFeedback")
                    if wf is not None and len(wf) != len(opts):
                        errs.append(f"{where} round[{j}] wrongFeedback must be parallel to opts.")
    return errs


def _module_by_type(course: dict, mtype: str) -> list[dict]:
    return [m for m in course.get("modules", []) if isinstance(m, dict) and m.get("type") == mtype]


def _challenge_by_kind(course: dict, kind: str) -> list[dict]:
    return [
        m for m in _module_by_type(course, "challenge")
        if isinstance(m.get("data"), dict) and m["data"].get("kind") == kind
    ]


def _count_first(course: dict, mtype: str, field: str) -> int:
    modules = _module_by_type(course, mtype)
    if not modules or not isinstance(modules[0].get("data"), dict):
        return 0
    value = modules[0]["data"].get(field)
    return len(value) if isinstance(value, list) else 0


def validate_generation_design(course: dict) -> list[str]:
    """Quality gate for newly generated courses. Stricter than renderer validation."""
    errs = validate(course)
    if errs:
        return errs
    modules = course.get("modules", [])
    if len(modules) < MIN_GENERATED_MODULES:
        errs.append(f"generated course must include at least {MIN_GENERATED_MODULES} modules.")

    present_types = {m.get("type") for m in modules if isinstance(m, dict)}
    for mtype in sorted(REQUIRED_GENERATED_TYPES - present_types):
        errs.append(f"generated course missing required {mtype} module.")

    present_challenges = {
        m.get("data", {}).get("kind") for m in _module_by_type(course, "challenge")
        if isinstance(m.get("data"), dict)
    }
    for kind in sorted(REQUIRED_GENERATED_CHALLENGES - present_challenges):
        errs.append(f"generated course missing required challenge kind '{kind}'.")

    minimums = [
        ("overview", "cards", 3),
        ("concept_cards", "cards", 5),
        ("flashcards", "cards", 10),
        ("glossary", "terms", 10),
        ("notes", "sections", 4),
        ("cheatsheet", "blocks", 5),
        ("visual_map", "nodes", 5),
        ("drag_sort", "items", 8),
        ("teach_back", "prompts", 4),
    ]
    for mtype, field, minimum in minimums:
        count = _count_first(course, mtype, field)
        if count and count < minimum:
            errs.append(f"{mtype}.{field} should include at least {minimum} items.")

    sequences = _module_by_type(course, "sequence")
    if sequences:
        modes = sequences[0].get("data", {}).get("modes", [])
        if isinstance(modes, list) and modes:
            first_items = modes[0].get("items", [])
            if isinstance(first_items, list) and len(first_items) < 5:
                errs.append("sequence modes should include at least 5 items.")

    challenge_minimums = {"quiz": 8, "rounds": 4, "timed": 6}
    for kind, minimum in challenge_minimums.items():
        challenges = _challenge_by_kind(course, kind)
        if challenges:
            rounds = challenges[0].get("data", {}).get("rounds", [])
            if isinstance(rounds, list) and len(rounds) < minimum:
                errs.append(f"challenge kind '{kind}' should include at least {minimum} rounds.")

    errs.extend(_validate_generation_depth(course))
    return errs


def _texts_mean(values: list) -> float:
    lengths = [len(v.strip()) for v in values if isinstance(v, str) and v.strip()]
    return (sum(lengths) / len(lengths)) if lengths else 0.0


def _validate_generation_depth(course: dict) -> list[str]:
    """Reject shallow 'word-association' output: require substantive, taught content.

    These thresholds are about *substance per field*, not item counts (counts are covered
    above). They catch the common failure where every field is a one-line label/synonym
    instead of a real explanation with a concrete example.
    """
    errs: list[str] = []

    overviews = _module_by_type(course, "overview")
    if overviews:
        body = overviews[0].get("data", {}).get("body", "")
        if isinstance(body, str) and len(body.strip()) < 180:
            errs.append("overview.body is too thin — write a real introductory paragraph (>= 180 chars).")

    concepts = _module_by_type(course, "concept_cards")
    if concepts:
        field_texts: list[str] = []
        longest_per_card: list[int] = []
        for card in concepts[0].get("data", {}).get("cards", []) or []:
            if not isinstance(card, dict):
                continue
            texts = [f.get("text", "") for f in card.get("fields", []) or [] if isinstance(f, dict)]
            field_texts.extend(texts)
            lengths = [len(t.strip()) for t in texts if isinstance(t, str)]
            longest_per_card.append(max(lengths) if lengths else 0)
        if field_texts and _texts_mean(field_texts) < 110:
            errs.append("concept_cards fields are too shallow — each field needs a multi-sentence "
                        "explanation (avg >= 110 chars), not a label or synonym.")
        thin_cards = sum(1 for n in longest_per_card if n < 140)
        if longest_per_card and thin_cards > len(longest_per_card) // 2:
            errs.append("most concept cards lack a worked, concrete example — give each card at "
                        "least one detailed field (>= 140 chars) with specifics.")

    flashcards = _module_by_type(course, "flashcards")
    if flashcards:
        answers = [c.get("a", "") for c in flashcards[0].get("data", {}).get("cards", []) or []
                   if isinstance(c, dict)]
        if answers and _texts_mean(answers) < 70:
            errs.append("flashcard answers are too short — explain the answer (avg >= 70 chars), "
                        "don't just restate a term.")

    glossaries = _module_by_type(course, "glossary")
    if glossaries:
        defs = [t.get("d", "") for t in glossaries[0].get("data", {}).get("terms", []) or []
                if isinstance(t, dict)]
        if defs and _texts_mean(defs) < 60:
            errs.append("glossary definitions are too thin — define each term in a full sentence "
                        "(avg >= 60 chars).")

    notes = _module_by_type(course, "notes")
    if notes:
        summaries = [s.get("summary", "") for s in notes[0].get("data", {}).get("sections", []) or []
                     if isinstance(s, dict)]
        if summaries and _texts_mean(summaries) < 120:
            errs.append("notes sections are too thin — each section summary should teach "
                        "the idea (avg >= 120 chars).")

    return errs


# ----------------------------------------------------------------------------
# 4. Injection into the template
# ----------------------------------------------------------------------------
COURSE_RE = re.compile(r"const COURSE =\s*[\s\S]*?\n\s*;")


def inject(course: dict, template: str) -> str:
    payload = "const COURSE =\n" + json.dumps(course, indent=2, ensure_ascii=False) + "\n;"
    new, n = COURSE_RE.subn(lambda _: payload, template, count=1)
    if n != 1:
        raise GenerationError("Could not find the COURSE injection point in the template.")
    return new


# ----------------------------------------------------------------------------
# 5. Public entry point
# ----------------------------------------------------------------------------
def build_course(instruction: str, material: str, learner: str,
                 template_path: Path, provider: str | None = None,
                 api_key: str | None = None, model: str | None = None,
                 context: str = "", learning_style: str = "mixed",
                 retries: int = 3) -> tuple[dict, str]:
    """Returns (course_dict, finished_html). Raises GenerationError on failure."""
    template = Path(template_path).read_text(encoding="utf-8")
    learning_style = learning_style if learning_style in VALID_STYLES else "mixed"
    user = _user_message(instruction, learner, material,
                         context=context, learning_style=learning_style)

    prov = resolve_provider(provider)
    key = resolve_key(prov, api_key)
    mdl = (model or os.environ.get("PREP_MODEL") or DEFAULT_MODELS[prov])

    last_errs: list[str] = []
    best_schema_valid: dict | None = None
    for attempt in range(retries + 1):
        sys_prompt = SYSTEM_PROMPT
        if attempt > 0 and last_errs:
            sys_prompt += ("\n\nYour previous output had these problems — fix them and "
                           "return corrected JSON only:\n- " + "\n- ".join(last_errs))
        raw = _generate_json(sys_prompt, user, prov, key, mdl)
        course = _extract_json(raw)
        meta = course.setdefault("meta", {})
        meta.setdefault("learner", learner)
        meta.setdefault("learningStyle", learning_style)
        _repair_course(course)
        schema_errs = validate(course)
        if schema_errs:
            last_errs = schema_errs
            continue
        best_schema_valid = course
        design_errs = validate_generation_design(course)
        if not design_errs:
            return course, inject(course, template)
        last_errs = design_errs

    if best_schema_valid is not None and not _strict_generation_required():
        best_schema_valid.setdefault("meta", {})["qualityWarning"] = (
            "The model returned a schema-valid course but missed some richness targets."
        )
        log.warning("Returning schema-valid course despite design gaps: %s", "; ".join(last_errs[:6]))
        return best_schema_valid, inject(best_schema_valid, template)

    raise GenerationError("Validation failed after retry:\n- " + "\n- ".join(last_errs))
