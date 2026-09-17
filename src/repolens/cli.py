"""repolens CLI. `repolens <path>` builds a full report folder; `repolens card`
emits one embeddable SVG; `repolens report` prints the text health report."""
from __future__ import annotations
import argparse, os, sys
from . import gitdata, analyze, report, render

def _name(path): return os.path.basename(os.path.abspath(path.rstrip("/"))) or "repo"

def _check(path):
    if not gitdata.is_repo(path):
        print("Bhai... not a git repository: %s (run inside a repo, or `git init`)"%path, file=sys.stderr)
        sys.exit(2)

def cmd_build(a):
    _check(a.path); name=a.title or _name(a.path)
    an=analyze.analyze(a.path)
    if not an["files"]:
        print("no analysable source files found", file=sys.stderr); sys.exit(1)
    s=report.summarize(an)
    out=a.out or "repolens-report"; os.makedirs(out, exist_ok=True)
    render.hotspot_treemap(an, os.path.join(out,"hotspot.svg"), title="%s - hotspot map"%name)
    render.repo_card(s, name, os.path.join(out,"card.svg"))
    open(os.path.join(out,"report.txt"),"w").write(report.text(an,name))
    inline=open(os.path.join(out,"hotspot.svg")).read().split("?>")[-1]
    render.dashboard_html(an, s, name, inline, os.path.join(out,"index.html"))
    print("RepoLens: %s - grade %s (%d/100)"%(name,s["grade"],s["score"]))
    print("  wrote %s/index.html, hotspot.svg, card.svg, report.txt"%out)
    print("  %d files, %s lines, %d commits, bus factor %d"%(s["files"],f'{s["loc"]:,}',s["commits"],s["bus_factor"]))
    if s["hotspots"]: print("  top hotspot: %s"%s["hotspots"][0]["path"])

def cmd_card(a):
    _check(a.path); name=a.title or _name(a.path)
    s=report.summarize(analyze.analyze(a.path))
    render.repo_card(s, name, a.out or "repolens-card.svg")
    print("wrote %s"%(a.out or "repolens-card.svg"))

def cmd_report(a):
    _check(a.path)
    print(report.text(analyze.analyze(a.path), a.title or _name(a.path)))

def main(argv=None):
    p=argparse.ArgumentParser(prog="repolens", description="An offline X-ray of any git repository.")
    sub=p.add_subparsers(dest="cmd")
    def common(sp): sp.add_argument("path", nargs="?", default="."); sp.add_argument("--title"); sp.add_argument("-o","--out")
    b=sub.add_parser("build", help="full report folder (default)"); common(b)
    c=sub.add_parser("card", help="one embeddable SVG card"); common(c)
    r=sub.add_parser("report", help="print the text health report"); common(r)
    # allow `repolens <path>` with no subcommand -> build
    a,extra=p.parse_known_args(argv)
    if a.cmd is None:
        b2=argparse.Namespace(path=(argv[0] if argv else (extra[0] if extra else ".")), title=None, out=None)
        return cmd_build(b2)
    {"build":cmd_build,"card":cmd_card,"report":cmd_report}[a.cmd](a)

if __name__=="__main__":
    main()
