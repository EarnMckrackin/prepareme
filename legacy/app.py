"""
Prep Suite Generator — local web front end  (roadmap step 2)

Upload a document + type an instruction + pick kid/adult  ->  generate  ->
view or download a finished interactive study course (the Alpine/Tailwind engine).

Run:
    pip install fastapi uvicorn python-multipart
    # plus ONE model backend:
    #   Ollama (local, default):     pip install ollama   + `ollama pull llama3.1:8b`
    #   Anthropic (stronger):        pip install anthropic + set ANTHROPIC_API_KEY
    # plus document parsers as needed:
    #   pip install pypdf python-docx
    uvicorn app:app --reload --port 8000
    # open http://localhost:8000
"""

import json
import os
import re
import uuid
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse

from generator import build_course, GenerationError

# ----------------------------------------------------------------------------
APP_DIR = Path(__file__).parent
TEMPLATE_PATH = APP_DIR / "course_template.html"
OUTPUT_DIR = APP_DIR / "generated"
OUTPUT_DIR.mkdir(exist_ok=True)

# Which model backend to use: "ollama" (local) or "anthropic" (hosted).
BACKEND = os.environ.get("PREP_BACKEND", "ollama")

app = FastAPI(title="Prep Suite Generator")

# In-memory index of generated courses (id -> {title, path}). Survives until restart.
LIBRARY: dict[str, dict] = {}


# ---------- document extraction ---------------------------------------------
def extract_text(filename: str, raw: bytes) -> str:
    """Pull plain text out of an uploaded file. Supports txt/md/pdf/docx."""
    ext = Path(filename).suffix.lower()
    if ext in (".txt", ".md", ".markdown", ".csv"):
        return raw.decode("utf-8", errors="replace")
    if ext == ".pdf":
        try:
            from pypdf import PdfReader
            import io
        except ImportError:
            raise GenerationError("PDF support needs: pip install pypdf")
        try:
            reader = PdfReader(io.BytesIO(raw))
            return "\n\n".join((p.extract_text() or "") for p in reader.pages)
        except Exception as e:
            raise GenerationError(f"Could not read that PDF ({type(e).__name__}). "
                                  "Try pasting the text instead.")
    if ext == ".docx":
        try:
            import io, docx
        except ImportError:
            raise GenerationError("DOCX support needs: pip install python-docx")
        try:
            d = docx.Document(io.BytesIO(raw))
            return "\n\n".join(p.text for p in d.paragraphs if p.text.strip())
        except Exception as e:
            raise GenerationError(f"Could not read that DOCX ({type(e).__name__}). "
                                  "Try pasting the text instead.")
    # last resort: try utf-8
    return raw.decode("utf-8", errors="replace")


# ---------- routes ----------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def home():
    return UPLOAD_PAGE


@app.post("/generate")
async def generate(
    instruction: str = Form(""),
    learner: str = Form("adult"),
    pasted: str = Form(""),
    file: UploadFile | None = File(None),
):
    # gather source material: uploaded file and/or pasted text
    material_parts = []
    if file is not None and file.filename:
        raw = await file.read()
        try:
            material_parts.append(extract_text(file.filename, raw))
        except GenerationError as e:
            raise HTTPException(400, str(e))
    if pasted.strip():
        material_parts.append(pasted.strip())
    material = "\n\n".join(material_parts).strip()

    if not material:
        raise HTTPException(400, "Provide a document or paste some study material.")
    if not instruction.strip():
        raise HTTPException(400, "Add a one-line instruction (topic / grade / tone).")

    try:
        course, html = build_course(
            instruction=instruction.strip(),
            material=material,
            learner=learner,
            template_path=TEMPLATE_PATH,
            backend=BACKEND,
        )
    except GenerationError as e:
        raise HTTPException(422, f"Generation failed: {e}")

    cid = uuid.uuid4().hex[:10]
    out_path = OUTPUT_DIR / f"{cid}.html"
    out_path.write_text(html, encoding="utf-8")
    title = course.get("meta", {}).get("title", "Untitled course")
    LIBRARY[cid] = {"title": title, "path": str(out_path),
                    "modules": len(course.get("modules", []))}

    return {
        "id": cid,
        "title": title,
        "modules": len(course.get("modules", [])),
        "view_url": f"/course/{cid}",
        "download_url": f"/download/{cid}",
    }


@app.get("/course/{cid}", response_class=HTMLResponse)
def view_course(cid: str):
    item = LIBRARY.get(cid)
    if not item:
        raise HTTPException(404, "Course not found (the server may have restarted).")
    return Path(item["path"]).read_text(encoding="utf-8")


@app.get("/download/{cid}")
def download_course(cid: str):
    item = LIBRARY.get(cid)
    if not item:
        raise HTTPException(404, "Course not found.")
    safe = re.sub(r"[^a-z0-9]+", "_", item["title"].lower()).strip("_") or "course"
    return FileResponse(item["path"], media_type="text/html",
                        filename=f"{safe}.html")


@app.get("/library")
def library():
    return [{"id": k, **v} for k, v in LIBRARY.items()]


# ---------- the upload page (dark/purple, matches the course aesthetic) ------
UPLOAD_PAGE = r"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prep Suite Generator</title>
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4/dist/index.global.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');
body{font-family:'Inter',sans-serif;background:#030712;}
.mono{font-family:'JetBrains Mono',monospace;}
.seg.active{background:#7e22ce;color:#fff;border-color:#a855f7;}
</style></head>
<body class="text-gray-100 min-h-screen bg-gray-950">
<header class="border-b border-gray-800 bg-gray-900/40 px-4 py-3">
  <div class="max-w-3xl mx-auto flex items-center gap-3">
    <div class="h-3 w-3 rounded-full bg-purple-500 animate-pulse"></div>
    <h1 class="text-base font-bold tracking-wider mono uppercase">Prep Suite Generator</h1>
  </div>
</header>

<main class="max-w-3xl mx-auto px-4 py-10 space-y-6">
  <div class="bg-gradient-to-r from-purple-950/30 to-gray-900/60 border border-purple-900/40 p-6 rounded-xl">
    <h2 class="text-xl font-black text-white mb-2">Turn any document into an interactive study course.</h2>
    <p class="text-sm text-gray-300 leading-relaxed">Upload notes, a chapter, or a study guide (or paste text), describe what you want, and get a finished course with flashcards, a quiz, a build game, a speed round, a cheat-sheet, and more — in the same engine you've been using.</p>
  </div>

  <form id="f" class="space-y-5 bg-gray-900 border border-gray-800 rounded-xl p-6">
    <div>
      <label class="text-xs mono uppercase tracking-widest text-purple-400 block mb-2">1 · Source material</label>
      <input type="file" name="file" id="file" accept=".txt,.md,.markdown,.pdf,.docx,.csv"
        class="block w-full text-sm text-gray-400 file:mr-3 file:py-2 file:px-4 file:rounded file:border-0 file:bg-purple-700 file:text-white file:font-bold file:cursor-pointer hover:file:bg-purple-600"/>
      <p class="text-[11px] text-gray-600 mt-1">txt, md, pdf, docx, csv — or paste below. You can do both.</p>
      <textarea name="pasted" id="pasted" rows="5" placeholder="…or paste study material here"
        class="mt-3 w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-600 focus:outline-none"></textarea>
    </div>

    <div>
      <label class="text-xs mono uppercase tracking-widest text-purple-400 block mb-2">2 · Instruction</label>
      <input type="text" name="instruction" id="instruction" required
        placeholder="e.g. 6th grade science test on ecosystems, friendly tone"
        class="w-full bg-gray-950 border border-gray-800 rounded-lg p-3 text-sm text-gray-200 placeholder-gray-600 focus:border-purple-600 focus:outline-none"/>
    </div>

    <div>
      <label class="text-xs mono uppercase tracking-widest text-purple-400 block mb-2">3 · Audience</label>
      <div class="flex gap-2 mono text-xs">
        <button type="button" data-v="kid"   class="seg flex-1 border border-gray-800 bg-gray-950 rounded-lg py-2.5 font-bold">🎒 Kid (simple, encouraging)</button>
        <button type="button" data-v="adult" class="seg active flex-1 border border-gray-800 bg-gray-950 rounded-lg py-2.5 font-bold">🎓 Adult (technical)</button>
      </div>
      <input type="hidden" name="learner" id="learner" value="adult"/>
    </div>

    <button type="submit" id="go" class="w-full bg-purple-600 hover:bg-purple-500 disabled:opacity-50 px-4 py-3 rounded-lg mono font-bold text-white transition">Generate course →</button>
  </form>

  <div id="status" class="hidden bg-gray-900 border border-gray-800 rounded-xl p-6 text-center">
    <div class="inline-block h-6 w-6 border-2 border-purple-500 border-t-transparent rounded-full animate-spin mb-3"></div>
    <p id="statusText" class="text-sm text-gray-400 mono">Reading your document and building the course… (local models can take 30–90s)</p>
  </div>

  <div id="result" class="hidden bg-gray-900 border border-emerald-900/40 rounded-xl p-6 space-y-3">
    <div class="text-emerald-400 mono text-xs uppercase tracking-widest">✓ Course ready</div>
    <h3 id="rTitle" class="text-lg font-bold text-white"></h3>
    <p id="rMeta" class="text-xs text-gray-500 mono"></p>
    <div class="flex gap-3 pt-2">
      <a id="rView" target="_blank" class="bg-purple-600 hover:bg-purple-500 px-5 py-2.5 rounded-lg mono font-bold text-sm text-white">Open course ↗</a>
      <a id="rDownload" class="bg-gray-800 hover:bg-gray-700 px-5 py-2.5 rounded-lg mono font-bold text-sm text-gray-200">Download .html</a>
    </div>
  </div>

  <div id="error" class="hidden bg-gray-900 border border-red-900/40 rounded-xl p-5">
    <div class="text-red-400 mono text-xs uppercase tracking-widest mb-1">✗ Something went wrong</div>
    <p id="errText" class="text-sm text-gray-300"></p>
  </div>
</main>

<script>
const segs=document.querySelectorAll('.seg'), learner=document.getElementById('learner');
segs.forEach(b=>b.onclick=()=>{segs.forEach(x=>x.classList.remove('active'));b.classList.add('active');learner.value=b.dataset.v;});
const f=document.getElementById('f'),go=document.getElementById('go');
const elStatus=document.getElementById('status'),elResult=document.getElementById('result'),elErr=document.getElementById('error');
f.onsubmit=async(e)=>{
  e.preventDefault();
  elResult.classList.add('hidden'); elErr.classList.add('hidden'); elStatus.classList.remove('hidden');
  go.disabled=true; go.textContent='Generating…';
  try{
    const data=new FormData(f);
    const r=await fetch('/generate',{method:'POST',body:data});
    const j=await r.json();
    if(!r.ok){throw new Error(j.detail||'Generation failed');}
    document.getElementById('rTitle').textContent=j.title;
    document.getElementById('rMeta').textContent=j.modules+' modules · id '+j.id;
    document.getElementById('rView').href=j.view_url;
    document.getElementById('rDownload').href=j.download_url;
    elResult.classList.remove('hidden');
  }catch(err){
    document.getElementById('errText').textContent=err.message;
    elErr.classList.remove('hidden');
  }finally{
    elStatus.classList.add('hidden'); go.disabled=false; go.textContent='Generate course →';
  }
};
</script>
</body></html>"""
