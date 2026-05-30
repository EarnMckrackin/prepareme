"""
generator.py — the engine of the prep suite.

documents + instruction  ->  strict COURSE json  ->  validated  ->  injected into template

This is the reusable core. app.py (the web front end) is a thin wrapper around it;
you can also call build_course() from a CLI or a notebook.
"""

import json
import re
from pathlib import Path


class GenerationError(Exception):
    """Raised when generation or validation fails in a way worth showing the user."""


# ----------------------------------------------------------------------------
# 1. The generation prompt (kept in sync with the COURSE schema)
# ----------------------------------------------------------------------------
SYSTEM_PROMPT = """You are a course generator. You convert study material into a single JSON object that drives an interactive study app. Output ONLY valid JSON — no markdown, no prose, no code fences.

The JSON must match this schema exactly:
{ "meta": {"title","subtitle","learner"}, "modules": [ {"type","id","label","data"} ] }

Allowed module types and their data shapes:
- overview: {kicker, headline, body, cards:[{tag,title,text}], stepsTitle, steps:[...]}
- concept_cards: {intro, cards:[{badge, name, fields:[{label,text,tone}], highlight:{label,q,a}}]}
  tone is one of: neutral, good, info, bad, warn
- flashcards: {cards:[{q,a}]}
- glossary: {intro, terms:[{t,d}]}
- cheatsheet: {title, intro, blocks:[{title, wide(optional bool), text(optional), items(optional array)}]}
- sequence: {title, intro, modes:[{key, label, items:[{id,label,why}], correct:[ids in correct order]}]}
- challenge: {kind, title, intro, startLabel, timer(optional int), rounds:[{title(optional), scenario(optional), constraints(optional array), question, opts:[string OR {label,detail}], correct (0-based index into opts), exp(optional) OR (rightFeedback AND wrongFeedback array parallel to opts with null in the correct slot)}]}
  kind is one of: quiz, rounds, timed, classify

Requirements:
- Build a coherent course from the material. Always include, in this order:
  one overview, one concept_cards, one flashcards, one challenge with kind "quiz",
  one glossary, one cheatsheet. Add a challenge with kind "rounds" (a build/apply game),
  a challenge with kind "timed" (a speed round, timer 20), and a sequence when the material supports them.
- Every module id must be unique and lowercase. Tab labels should be short and numbered (e.g. "1. Big Idea").
- Ground every fact in the provided material. Do NOT invent facts. If something is ambiguous, leave it out.
- On each concept card, write a "highlight" box (label starts with an emoji like ⚠) calling out the single most common mistake or test trap for that concept.
- Match the requested audience. If the instruction names a grade level or says "kid", set meta.learner="kid", keep language simple, friendly and encouraging, use concrete examples. Otherwise set meta.learner="adult".
- 8 to 12 flashcards. 6 to 10 quiz questions. Questions test understanding, not trivia.
- "correct" is a 0-based index into "opts". For rounds/classify, "wrongFeedback" is parallel to "opts" (use null for the correct slot). Use "exp" OR rightFeedback+wrongFeedback, not both.

Return the JSON object and nothing else."""


def _user_message(instruction: str, learner: str, material: str, max_chars: int = 24000) -> str:
    learner_hint = ("Audience: a child / the specified grade level. Use meta.learner=\"kid\"."
                    if learner == "kid" else
                    "Audience: an adult learner. Use meta.learner=\"adult\".")
    trimmed = material[:max_chars]
    if len(material) > max_chars:
        trimmed += "\n\n[material truncated for length]"
    return f"INSTRUCTION: {instruction}\n{learner_hint}\n\nMATERIAL:\n{trimmed}"


# ----------------------------------------------------------------------------
# 2. Model backends (swap point — same idea as llm.py in the RAG)
# ----------------------------------------------------------------------------
def _call_ollama(system: str, user: str, model: str = "llama3.1:8b") -> str:
    try:
        import ollama
    except ImportError:
        raise GenerationError("Ollama backend needs: pip install ollama (and `ollama pull llama3.1:8b`)")
    resp = ollama.chat(
        model=model,
        messages=[{"role": "system", "content": system},
                  {"role": "user", "content": user}],
        options={"temperature": 0.3},
        format="json",  # constrain output to JSON
    )
    return resp["message"]["content"]


def _call_anthropic(system: str, user: str, model: str = "claude-sonnet-4-20250514") -> str:
    try:
        import anthropic
    except ImportError:
        raise GenerationError("Anthropic backend needs: pip install anthropic (and set ANTHROPIC_API_KEY)")
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=model,
        max_tokens=8000,
        temperature=0.3,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", None) == "text")


def _generate_json(system: str, user: str, backend: str) -> str:
    if backend == "anthropic":
        return _call_anthropic(system, user)
    return _call_ollama(system, user)


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
        # fall back to first { ... last }
        a, b = s.find("{"), s.rfind("}")
        if a == -1 or b == -1 or b <= a:
            raise GenerationError("Model did not return JSON.")
        try:
            return json.loads(s[a:b + 1])
        except json.JSONDecodeError as e:
            raise GenerationError(f"Model returned invalid JSON: {e}")


VALID_TYPES = {"overview", "concept_cards", "flashcards", "glossary",
               "cheatsheet", "sequence", "challenge"}
VALID_KINDS = {"quiz", "rounds", "timed", "classify"}


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
                 template_path: Path, backend: str = "ollama",
                 retries: int = 1) -> tuple[dict, str]:
    """Returns (course_dict, finished_html). Raises GenerationError on failure."""
    template = Path(template_path).read_text(encoding="utf-8")
    user = _user_message(instruction, learner, material)

    last_errs: list[str] = []
    for attempt in range(retries + 1):
        sys_prompt = SYSTEM_PROMPT
        if attempt > 0 and last_errs:
            # feed the validation errors back in for a self-correcting retry
            sys_prompt += ("\n\nYour previous output had these problems — fix them and "
                           "return corrected JSON only:\n- " + "\n- ".join(last_errs))
        raw = _generate_json(sys_prompt, user, backend)
        course = _extract_json(raw)
        # normalize learner if the model ignored it
        course.setdefault("meta", {}).setdefault("learner", learner)
        last_errs = validate(course)
        if not last_errs:
            return course, inject(course, template)

    raise GenerationError("Validation failed after retry:\n- " + "\n- ".join(last_errs))
