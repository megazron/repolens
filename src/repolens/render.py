"""SVG renderers: the hotspot treemap, language donut, timeline, and a repo card.
Pure stdlib string building -- crisp in light and dark, embeddable in a README."""
from __future__ import annotations
import html, math, datetime
from .treemap import squarify

FONT="-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
def esc(s): return html.escape(str(s))

def _risk_color(r):
    # 0 green -> .5 amber -> 1 red
    stops=[(0.0,(43,138,62)),(0.5,(178,90,0)),(1.0,(176,42,55))]
    for (a,ca),(b,cb) in zip(stops,stops[1:]):
        if a<=r<=b:
            t=(r-a)/(b-a) if b>a else 0
            return "#%02x%02x%02x"%tuple(int(ca[i]+(cb[i]-ca[i])*t) for i in range(3))
    return "#b02a37"

def hotspot_treemap(analysis, out, w=1100, h=760, max_files=220, title=None):
    files=sorted(analysis["files"], key=lambda f: f["loc"], reverse=True)[:max_files]
    if not files:
        open(out,"w").write('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="60"><text x="10" y="30">no source files</text></svg>'%w); return
    groups={}
    for f in files: groups.setdefault(f["top"],[]).append(f)
    gitems=[(g, sum(x["loc"] for x in fs)) for g,fs in groups.items()]
    pad_top=64; body_h=h-pad_top-58
    b=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">']
    b.append(f'<rect width="{w}" height="{h}" fill="#0d1117"/>')
    b.append(f'<text x="24" y="34" font-size="21" font-weight="700" fill="#e6edf3">{esc(title or "Hotspot map")}</text>')
    b.append(f'<text x="24" y="54" font-size="12.5" fill="#8b949e">Each tile is a file - area is lines of code, colour is risk (change frequency x complexity). Red = a hotspot.</text>')
    for g,gv,gx,gy,gw,gh in squarify(gitems,24,pad_top,w-48,body_h):
        fs=groups[g]
        b.append(f'<rect x="{gx:.1f}" y="{gy:.1f}" width="{gw:.1f}" height="{gh:.1f}" fill="none" stroke="#30363d" stroke-width="2"/>')
        for f,fl,fx,fy,fw,fh in squarify([(x["path"],x["loc"]) for x in fs],gx+2,gy+2,max(1,gw-4),max(1,gh-4)):
            rec=next(x for x in fs if x["path"]==f)
            col=_risk_color(rec.get("risk_rank",rec["risk"]))
            b.append(f'<rect x="{fx:.1f}" y="{fy:.1f}" width="{fw:.1f}" height="{fh:.1f}" fill="{col}" stroke="#0d1117" stroke-width="0.7" rx="1.5"><title>{esc(f)}\nrisk {rec["risk"]:.2f} - {rec["churn"]} commits, complexity {rec["complexity"]}, {rec["loc"]} loc</title></rect>')
            if fw>62 and fh>16:
                name=f.split("/")[-1]
                b.append(f'<text x="{fx+4:.1f}" y="{fy+13:.1f}" font-size="10" fill="#0d1117" font-weight="600">{esc(name[:int(fw/6)])}</text>')
        # group label
        if gw>40 and gh>22:
            b.append(f'<text x="{gx+5:.1f}" y="{gy+gh-6:.1f}" font-size="12" fill="#e6edf3" font-weight="700" opacity="0.85">{esc(g)}/</text>')
    # legend
    ly=h-34
    b.append(f'<text x="24" y="{ly}" font-size="12" fill="#8b949e">risk</text>')
    for i in range(60):
        b.append(f'<rect x="{60+i*4}" y="{ly-11}" width="4" height="12" fill="{_risk_color(i/59)}"/>')
    b.append(f'<text x="60" y="{ly+16}" font-size="11" fill="#8b949e">calm</text>')
    b.append(f'<text x="270" y="{ly+16}" font-size="11" fill="#8b949e">hotspot</text>')
    b.append("</svg>")
    open(out,"w").write("\n".join(b))
    return out


LANG_COLORS={"Python":"#3572A5","JavaScript":"#f1e05a","TypeScript":"#3178c6",
 "C++":"#f34b7d","C":"#555555","C/C++":"#6d6d6d","Java":"#b07219","Go":"#00ADD8",
 "Rust":"#dea584","Ruby":"#701516","Shell":"#89e051","HTML":"#e34c26","CSS":"#563d7c",
 "YAML":"#cb171e","JSON":"#a0a0a0","Docs":"#7f8c8d","Notebook":"#DA5B0B","Julia":"#a270ba",
 "MATLAB":"#e16737","Config":"#6e7681","Vue":"#41b883","Other":"#5b6673","SQL":"#e38c00","XML":"#0060ac"}
def _lc(l): return LANG_COLORS.get(l,"#5b6673")
_GRADE_COL={"A+":"#2b8a3e","A":"#2b8a3e","B":"#6a9e1f","C":"#b25a00","D":"#c25b2c","E":"#b02a37"}

def repo_card(summary, name, out, w=500, h=210):
    s=summary; total=sum(v for _,v in s["languages"]) or 1
    b=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" font-family="{FONT}">']
    b.append(f'<rect width="{w}" height="{h}" rx="10" fill="#0d1117" stroke="#30363d"/>')
    b.append(f'<text x="22" y="34" font-size="18" font-weight="700" fill="#e6edf3">{esc(name)}</text>')
    g=s["grade"]; gc=_GRADE_COL.get(g,"#8b949e")
    b.append(f'<rect x="{w-92}" y="16" width="70" height="30" rx="6" fill="{gc}"/>')
    b.append(f'<text x="{w-57}" y="37" font-size="17" font-weight="700" fill="#fff" text-anchor="middle">{esc(g)}</text>')
    b.append(f'<text x="{w-96}" y="60" font-size="10" fill="#8b949e" text-anchor="end">health</text>')
    # stats row
    stats=[("lines",f'{s["loc"]:,}'),("files",str(s["files"])),("commits",str(s["commits"])),
           ("authors",str(s["authors"])),("bus factor",str(s["bus_factor"]))]
    x=22
    for lab,val in stats:
        b.append(f'<text x="{x}" y="80" font-size="17" font-weight="700" fill="#e6edf3">{esc(val)}</text>')
        b.append(f'<text x="{x}" y="96" font-size="10.5" fill="#8b949e">{esc(lab)}</text>')
        x+= max(70, 14+len(val)*11)
    # language bar
    by=116; bx=22; bw=w-44
    b.append(f'<text x="22" y="{by-4}" font-size="10.5" fill="#8b949e">languages</text>')
    ox=bx
    for lang,loc in s["languages"]:
        seg=bw*loc/total
        b.append(f'<rect x="{ox:.1f}" y="{by}" width="{seg:.1f}" height="9" fill="{_lc(lang)}"><title>{esc(lang)} {100*loc/total:.0f}%</title></rect>')
        ox+=seg
    # legend (top 4)
    lx=22
    for lang,loc in s["languages"][:4]:
        b.append(f'<circle cx="{lx+4}" cy="140" r="4" fill="{_lc(lang)}"/>')
        b.append(f'<text x="{lx+13}" y="144" font-size="10.5" fill="#8b949e">{esc(lang)} {100*loc/total:.0f}%</text>')
        lx+= 30+len(lang)*7+22
    # top hotspot
    if s["hotspots"]:
        hp=s["hotspots"][0]
        b.append(f'<text x="22" y="170" font-size="10.5" fill="#8b949e">top hotspot</text>')
        b.append(f'<text x="22" y="186" font-size="12.5" fill="#e6edf3" font-weight="600">{esc(hp["path"][-52:])}</text>')
        b.append(f'<text x="22" y="200" font-size="10" fill="#b02a37">{hp["churn"]} commits x complexity {hp["complexity"]} - refactor first</text>')
    b.append(f'<text x="{w-14}" y="200" font-size="9.5" fill="#484f58" text-anchor="end">RepoLens</text>')
    b.append("</svg>")
    open(out,"w").write("\n".join(b)); return out

def _timeline_bars(timeline, w, h):
    if not timeline: return ""
    items=list(timeline.items()); mx=max(timeline.values()) or 1
    n=len(items); bw=w/n
    out=[]
    for i,(mth,c) in enumerate(items):
        bh=(h-4)*c/mx
        out.append(f'<rect x="{i*bw:.1f}" y="{h-bh:.1f}" width="{max(1,bw-1):.1f}" height="{bh:.1f}" fill="#3fb950"><title>{esc(mth)}: {c} commits</title></rect>')
    return "".join(out)

def dashboard_html(analysis, summary, name, hotspot_svg, out):
    s=summary; total=sum(v for _,v in s["languages"]) or 1
    langbar="".join('<span style="display:inline-block;height:12px;width:%.2f%%;background:%s" title="%s %.0f%%"></span>'
                    %(100*loc/total,_lc(l),esc(l),100*loc/total) for l,loc in s["languages"])
    def rows(fs, fmt):
        return "".join("<li>%s</li>"%fmt(f) for f in fs)
    hot=rows(s["hotspots"][:8], lambda f:'<code>%s</code> <span class="m">%d commits &times; cx %d &middot; %d loc</span>'%(esc(f["path"]),f["churn"],f["complexity"],f["loc"]))
    solo=rows(s["solo"][:6], lambda f:'<code>%s</code>'%esc(f["path"]))
    big=rows(s["big_files"][:6], lambda f:'<code>%s</code> <span class="m">%d loc</span>'%(esc(f["path"]),f["loc"]))
    tl=_timeline_bars(s["timeline"], 720, 90)
    html_doc=_DASH.replace("{{NAME}}",esc(name)).replace("{{GRADE}}",esc(s["grade"]))\
      .replace("{{GC}}",_GRADE_COL.get(s["grade"],"#8b949e")).replace("{{SCORE}}",str(s["score"]))\
      .replace("{{LOC}}",f'{s["loc"]:,}').replace("{{FILES}}",str(s["files"]))\
      .replace("{{COMMITS}}",str(s["commits"])).replace("{{AUTHORS}}",str(s["authors"]))\
      .replace("{{BUS}}",str(s["bus_factor"])).replace("{{PRIMARY}}",esc(s["primary"]))\
      .replace("{{LANGBAR}}",langbar).replace("{{TREEMAP}}",hotspot_svg)\
      .replace("{{TL}}",tl).replace("{{HOT}}",hot).replace("{{SOLO}}",solo or "<li class='m'>none</li>")\
      .replace("{{BIG}}",big or "<li class='m'>none</li>")
    open(out,"w").write(html_doc); return out

_DASH="""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>RepoLens - {{NAME}}</title>
<style>:root{color-scheme:dark}body{margin:0;background:#0d1117;color:#e6edf3;
font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif;line-height:1.5}
main{max-width:1180px;margin:0 auto;padding:24px 16px}h1{margin:.2em 0}
.sub{color:#8b949e}.grade{display:inline-block;padding:2px 12px;border-radius:8px;font-weight:700;background:{{GC}};color:#fff}
.stats{display:flex;flex-wrap:wrap;gap:20px;margin:16px 0}
.stat b{font-size:22px}.stat span{display:block;color:#8b949e;font-size:12px}
.bar{border-radius:6px;overflow:hidden;line-height:0;margin:6px 0 18px}
.card{background:#161b22;border:1px solid #30363d;border-radius:10px;padding:16px;margin:14px 0}
h2{font-size:16px;margin:0 0 8px}ul{margin:0;padding-left:18px}li{margin:3px 0}
code{background:#0d1117;padding:1px 5px;border-radius:4px;font-size:12.5px}
.m{color:#8b949e;font-size:12px}svg{max-width:100%;height:auto}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}@media(max-width:760px){.grid{grid-template-columns:1fr}}
.tl{background:#0d1117;border-radius:6px;padding:8px}</style></head><body><main>
<h1>{{NAME}} <span class="grade">{{GRADE}}</span></h1>
<p class="sub">RepoLens health report &middot; score {{SCORE}}/100 &middot; primary language {{PRIMARY}}</p>
<div class="stats">
<div class="stat"><b>{{LOC}}</b><span>lines</span></div><div class="stat"><b>{{FILES}}</b><span>files</span></div>
<div class="stat"><b>{{COMMITS}}</b><span>commits</span></div><div class="stat"><b>{{AUTHORS}}</b><span>authors</span></div>
<div class="stat"><b>{{BUS}}</b><span>bus factor</span></div></div>
<div class="bar">{{LANGBAR}}</div>
<div class="card"><h2>Hotspot map</h2>{{TREEMAP}}</div>
<div class="card"><h2>Commit activity</h2><div class="tl"><svg viewBox="0 0 720 90" width="100%">{{TL}}</svg></div></div>
<div class="grid">
<div class="card"><h2>&#128293; Top hotspots</h2><ul>{{HOT}}</ul></div>
<div class="card"><h2>&#128101; Bus-factor risk</h2><ul>{{SOLO}}</ul>
<h2 style="margin-top:14px">&#128207; Large files</h2><ul>{{BIG}}</ul></div>
</div>
<p class="m">Generated offline by RepoLens &middot; no code left this machine.</p>
</main></body></html>"""
