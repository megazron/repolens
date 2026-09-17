import os, subprocess, sys, xml.dom.minidom, pathlib
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from repolens import gitdata, analyze, report, render
from repolens.treemap import squarify

def _mkrepo(tmp):
    d=str(tmp)
    def g(*a): subprocess.run(["git",*a],cwd=d,check=True,capture_output=True)
    g("init","-q"); g("config","user.email","a@b.c"); g("config","user.name","Dev One")
    (tmp/"simple.py").write_text("x = 1\ny = 2\n")
    (tmp/"complex.py").write_text("def f(a):\n"+ "".join("    if a>%d: a+=1\n"%i for i in range(20)))
    (tmp/"data.json").write_text('{"a":1}\n')
    g("add","-A"); g("commit","-q","-m","init")
    for i in range(4):  # churn complex.py
        (tmp/"complex.py").write_text((tmp/"complex.py").read_text()+"# c%d\n"%i)
        g("add","-A"); g("commit","-q","-m","edit %d"%i)
    return d

def test_is_repo(tmp_path):
    repo=tmp_path/"r"; repo.mkdir(); _mkrepo(repo)
    assert gitdata.is_repo(str(repo))
    plain=tmp_path/"p"; plain.mkdir()   # sibling, not under the repo
    assert gitdata.is_repo(str(plain)) is False

def test_history_counts(tmp_path):
    h=gitdata.history(_mkrepo(tmp_path))
    assert h["ncommits"]==5
    assert h["files"]["complex.py"]["commits"]==5
    assert h["files"]["simple.py"]["commits"]==1

def test_analyze_risk_orders_complex_churned_first(tmp_path):
    an=analyze.analyze(_mkrepo(tmp_path))
    paths=[f["path"] for f in an["files"]]
    assert "complex.py" in paths and "simple.py" in paths
    # complex.py churns a lot and is complex -> highest risk
    assert an["files"][0]["path"]=="complex.py"
    cx=next(f for f in an["files"] if f["path"]=="complex.py")
    assert cx["complexity"]>=20 and cx["churn"]==5

def test_language_detection(tmp_path):
    an=analyze.analyze(_mkrepo(tmp_path))
    langs={f["path"]:f["lang"] for f in an["files"]}
    assert langs["simple.py"]=="Python" and langs["data.json"]=="JSON"

def test_report_grade_and_fields(tmp_path):
    an=analyze.analyze(_mkrepo(tmp_path)); s=report.summarize(an)
    assert s["grade"] in ("A+","A","B","C","D","E")
    assert s["commits"]==5 and s["bus_factor"]>=1
    assert s["hotspots"][0]["path"]=="complex.py"

def test_treemap_fills_box_without_overlap():
    rects=squarify([("a",50),("b",30),("c",20)],0,0,100,100)
    area=sum(w*h for _,_,_,_,w,h in rects)
    assert abs(area-10000) < 50  # fills the box
    for _,_,x,y,w,h in rects:
        assert x>=-1e-6 and y>=-1e-6 and x+w<=100.001 and y+h<=100.001

def test_svg_outputs_are_wellformed(tmp_path):
    an=analyze.analyze(_mkrepo(tmp_path)); s=report.summarize(an)
    hp=tmp_path/"h.svg"; render.hotspot_treemap(an,str(hp),title="t")
    cp=tmp_path/"c.svg"; render.repo_card(s,"demo",str(cp))
    for p in (hp,cp):
        xml.dom.minidom.parse(str(p))  # raises if malformed
        assert "<svg" in p.read_text()

def test_dashboard_html_self_contained(tmp_path):
    an=analyze.analyze(_mkrepo(tmp_path)); s=report.summarize(an)
    hp=tmp_path/"h.svg"; render.hotspot_treemap(an,str(hp),title="t")
    inline=open(hp).read().split("?>")[-1]
    out=tmp_path/"i.html"; render.dashboard_html(an,s,"demo",inline,str(out))
    html=out.read_text()
    assert html.startswith("<!doctype html>")
    # no external resource loads (the SVG xmlns namespace URL is not a fetch)
    assert 'src="http' not in html and 'href="http' not in html and "url(http" not in html

def test_cli_build_and_report(tmp_path):
    d=_mkrepo(tmp_path); env=dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__),"..","src"))
    o=tmp_path/"out"
    r=subprocess.run([sys.executable,"-m","repolens.cli","build",d,"-o",str(o)],env=env,capture_output=True,text=True)
    assert r.returncode==0
    for f in ("index.html","hotspot.svg","card.svg","report.txt"):
        assert (o/f).exists()
    rr=subprocess.run([sys.executable,"-m","repolens.cli","report",d],env=env,capture_output=True,text=True)
    assert rr.returncode==0 and "Health grade" in rr.stdout

def test_cli_refuses_non_repo(tmp_path):
    nd=tmp_path/"plain"; nd.mkdir()
    env=dict(os.environ, PYTHONPATH=os.path.join(os.path.dirname(__file__),"..","src"))
    r=subprocess.run([sys.executable,"-m","repolens.cli","report",str(nd)],env=env,capture_output=True,text=True)
    assert r.returncode==2
