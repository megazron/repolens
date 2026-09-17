"""Per-file metrics joined with git churn -> a risk model. Pure stdlib."""
from __future__ import annotations
import os, re, math
from . import gitdata

LANG = {".py":"Python",".js":"JavaScript",".ts":"TypeScript",".tsx":"TypeScript",
 ".jsx":"JavaScript",".c":"C",".h":"C/C++",".hpp":"C++",".cpp":"C++",".cc":"C++",
 ".cs":"C#",".java":"Java",".go":"Go",".rs":"Rust",".rb":"Ruby",".php":"PHP",
 ".swift":"Swift",".kt":"Kotlin",".scala":"Scala",".m":"Obj-C/MATLAB",".r":"R",
 ".jl":"Julia",".sh":"Shell",".bash":"Shell",".pl":"Perl",".lua":"Lua",
 ".html":"HTML",".css":"CSS",".scss":"CSS",".vue":"Vue",".dart":"Dart",
 ".yaml":"YAML",".yml":"YAML",".json":"JSON",".toml":"Config",".xml":"XML",
 ".md":"Docs",".rst":"Docs",".txt":"Docs",".ipynb":"Notebook",".sql":"SQL"}
CODE = {"Python","JavaScript","TypeScript","C","C/C++","C++","C#","Java","Go",
 "Rust","Ruby","PHP","Swift","Kotlin","Scala","R","Julia","Shell","Lua","Dart","Vue"}
BRANCH = re.compile(r'\b(if|elif|else|for|while|case|switch|catch|except|when|and|or)\b|&&|\|\||\?|\bmatch\b')
SKIP_DIRS = {".git","node_modules","build","install","log","dist","__pycache__",
 "vendor","third_party",".venv","venv",".tox","target",".next",".cache"}
BINARY_EXT = {".png",".jpg",".jpeg",".gif",".svg",".pdf",".zip",".gz",".pt",".pth",
 ".onnx",".bin",".so",".o",".a",".dll",".dylib",".mp4",".mov",".ico",".ttf",".woff",
 ".stl",".dae",".step",".stp",".f3z",".bag",".db",".npz",".npy",".parquet",".jpg"}

def _looks_venv(rel):
    return any(p in SKIP_DIRS or p.startswith(".venv") or p.endswith("_venv") for p in rel.split("/"))

def _pct_ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    r=[0.0]*len(values); n=len(values)
    for rank,i in enumerate(order): r[i]= rank/(n-1) if n>1 else 0.0
    return r

def analyze(path, max_bytes=400_000):
    hist = gitdata.history(path)
    churn_map = hist["files"]
    rows=[]
    for rel in gitdata.tracked_files(path):
        ext=os.path.splitext(rel)[1].lower()
        if ext in BINARY_EXT or _looks_venv(rel): continue
        lang=LANG.get(ext,"Other")
        full=os.path.join(path,rel)
        try:
            if os.path.getsize(full)>max_bytes: continue
            with open(full, encoding="utf-8", errors="ignore") as f: text=f.read()
        except OSError: continue
        loc=sum(1 for ln in text.splitlines() if ln.strip())
        if loc==0: continue
        cx = len(BRANCH.findall(text)) if lang in CODE else 0
        ci = churn_map.get(rel, {})
        rows.append({"path":rel,"lang":lang,"loc":loc,"complexity":cx,
            "churn":ci.get("commits",0),"authors":len(ci.get("authors",set())),
            "last":ci.get("last"),"top":rel.split("/")[0] if "/" in rel else "."})
    if not rows: return {"files":[],"hist":hist}
    cr=_pct_ranks([r["churn"] for r in rows])
    xr=_pct_ranks([r["complexity"] for r in rows])
    for r,c,x in zip(rows,cr,xr):
        r["risk"]=round(c*x,4)   # hotspot = frequently changed AND complex
    rr=_pct_ranks([r["risk"] for r in rows])
    for r,rk in zip(rows,rr): r["risk_rank"]=round(rk,4)
    rows.sort(key=lambda r:r["risk"], reverse=True)
    return {"files":rows,"hist":hist}
