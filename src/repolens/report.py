"""Turn the analysis into a plain-English health report + a letter grade."""
from __future__ import annotations
import collections, datetime, math

def summarize(analysis):
    files=analysis["files"]; hist=analysis["hist"]
    loc=sum(f["loc"] for f in files)
    langs=collections.Counter()
    for f in files: langs[f["lang"]]+=f["loc"]
    code_files=[f for f in files if f["complexity"]>0]
    # bus factor: min authors covering >=50% of churn
    author_churn=collections.Counter()
    for f in files:
        author_churn[None]  # noop
    ac=hist["authors"]; total_c=sum(ac.values()) or 1
    bus=0; acc=0
    for _,c in ac.most_common():
        acc+=c; bus+=1
        if acc>=0.5*total_c: break
    # hotspots
    hot=[f for f in files if f.get("risk_rank",0)>=0.85 and f["complexity"]>0][:10]
    # stale hotspots: high risk, not touched in >1yr
    now=datetime.datetime.utcnow().timestamp()
    stale=[f for f in hot if f["last"] and (now-f["last"])>365*86400]
    # single-owner risky files
    solo=[f for f in files if f.get("risk_rank",0)>=0.8 and f["authors"]<=1 and f["complexity"]>0][:8]
    # grade: penalize concentration of risk + low bus factor + huge files
    big=[f for f in code_files if f["loc"]>800]
    score=100
    score-= min(30, len(hot)*3)
    score-= 0 if bus>=3 else (18 if bus==1 else 8)
    score-= min(20, len(big)*4)
    score-= min(12, len(stale)*3)
    grade= "A+" if score>=93 else "A" if score>=85 else "B" if score>=72 else "C" if score>=58 else "D" if score>=45 else "E"
    return {
        "loc":loc,"files":len(files),"code_files":len(code_files),
        "commits":hist["ncommits"],"authors":len(ac),"bus_factor":bus,
        "languages":langs.most_common(8),"primary":langs.most_common(1)[0][0] if langs else "-",
        "hotspots":hot,"stale":stale,"solo":solo,"big_files":big,
        "months":len(hist["timeline"]),"grade":grade,"score":max(0,score),
        "timeline":hist["timeline"],
    }

def text(analysis, name):
    s=summarize(analysis); L=[]
    L.append("RepoLens report - %s"%name)
    L.append("="*(15+len(name)))
    L.append("Health grade: %s (%d/100)"%(s["grade"],s["score"]))
    L.append("%d files, %s lines, %d commits, %d author(s), bus factor %d"
             %(s["files"], f'{s["loc"]:,}', s["commits"], s["authors"], s["bus_factor"]))
    L.append("Primary language: %s"%s["primary"])
    L.append("")
    L.append("Top hotspots (change often AND complex - refactor/test these first):")
    for f in s["hotspots"][:6]:
        L.append("  - %s  (%d commits, complexity %d, %d loc)"%(f["path"],f["churn"],f["complexity"],f["loc"]))
    if s["solo"]:
        L.append("")
        L.append("Bus-factor risk (risky files with a single author):")
        for f in s["solo"][:5]: L.append("  - %s"%f["path"])
    if s["big_files"]:
        L.append("")
        L.append("Large files (>800 loc - candidates to split):")
        for f in s["big_files"][:5]: L.append("  - %s (%d loc)"%(f["path"],f["loc"]))
    if s["stale"]:
        L.append("")
        L.append("Stale hotspots (risky but untouched >1yr - fragile knowledge):")
        for f in s["stale"][:5]: L.append("  - %s"%f["path"])
    return "\n".join(L)
