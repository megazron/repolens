"""Squarified treemap layout (Bruls, Huizing, van Wijk). Pure math."""
from __future__ import annotations

def _worst(row, w, total, area_scale):
    s=sum(row); s2=s*area_scale
    if s2==0 or w==0: return float("inf")
    rmax=max(row)*area_scale; rmin=min(row)*area_scale
    return max((w*w*rmax)/(s2*s2), (s2*s2)/(w*w*rmin))

def squarify(items, x, y, w, h):
    """items: list of (key, value). Returns [(key,value,x,y,w,h)] filling the box."""
    items=[(k,v) for k,v in items if v>0]
    total=sum(v for _,v in items) or 1
    scale=(w*h)/total
    rects=[]; items=sorted(items,key=lambda kv:kv[1],reverse=True)
    def layoutrow(row, x,y,w,h,horizontal):
        s=sum(v for _,v in row)*scale
        if horizontal:
            rw=s/h if h else 0; oy=y
            for k,v in row:
                rh=(v*scale)/rw if rw else 0
                rects.append((k,v,x,oy,rw,rh)); oy+=rh
            return x+rw,y,w-rw,h
        else:
            rh=s/w if w else 0; ox=x
            for k,v in row:
                rw=(v*scale)/rh if rh else 0
                rects.append((k,v,ox,y,rw,rh)); ox+=rw
            return x,y+rh,w,h-rh
    row=[]; i=0
    while i<len(items):
        horizontal = w<h  # lay along the shorter side... actually along shorter dimension
        length = min(w,h)
        cur=[v*scale for _,v in row]
        nxt=cur+[items[i][1]*scale]
        if not row or _worst(nxt,length,total,1) <= _worst(cur,length,total,1):
            row.append(items[i]); i+=1
        else:
            x,y,w,h=layoutrow(row,x,y,w,h, w>=h)
            row=[]
    if row:
        layoutrow(row,x,y,w,h, w>=h)
    return rects
