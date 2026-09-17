"""Read history from a local git repo via the git CLI. Pure stdlib."""
from __future__ import annotations
import subprocess, os, collections, datetime

def _run(args, cwd, timeout=120):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                          text=True, timeout=timeout).stdout

def is_repo(path):
    try:
        return subprocess.run(["git","rev-parse","--is-inside-work-tree"], cwd=path,
                              capture_output=True, text=True).returncode == 0
    except (OSError, ValueError):
        return False

def history(path):
    """Per-file churn (commit count), distinct authors, first/last commit time,
    plus repo-level commit timeline and author totals. One `git log` pass."""
    out = _run(["log","--no-merges","--numstat","--date=unix",
                "--format=@C|%H|%an|%at"], path, timeout=300)
    files = collections.defaultdict(lambda: {"commits":0,"authors":set(),
              "added":0,"deleted":0,"first":None,"last":None})
    timeline = collections.Counter()     # yyyy-mm -> commits
    author_commits = collections.Counter()
    cur_author=None; cur_t=None; ncommits=0
    for line in out.splitlines():
        if line.startswith("@C|"):
            _,_h,an,at = line.split("|",3)
            cur_author=an; cur_t=int(at); ncommits+=1
            author_commits[an]+=1
            timeline[datetime.datetime.fromtimestamp(cur_t, datetime.timezone.utc).strftime("%Y-%m")]+=1
        elif line.strip():
            parts=line.split("\t")
            if len(parts)==3:
                a,d,f = parts
                fi=files[f]
                fi["commits"]+=1; fi["authors"].add(cur_author)
                fi["added"]+= int(a) if a.isdigit() else 0
                fi["deleted"]+= int(d) if d.isdigit() else 0
                if fi["first"] is None or cur_t<fi["first"]: fi["first"]=cur_t
                if fi["last"] is None or cur_t>fi["last"]: fi["last"]=cur_t
    return {"files":files, "timeline":dict(sorted(timeline.items())),
            "authors":author_commits, "ncommits":ncommits}

def tracked_files(path):
    return [f for f in _run(["ls-files"], path).splitlines() if f.strip()]
