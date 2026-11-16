"""Pixel digitisation of the logged response plots (MATLAB figures embedded in the dissertation).
Axis limits per plot were read visually; values are sampled on the blue trace at each integer
sample index. Keys are the dissertation plot numbers (see data/README.md for the run mapping).
Output: tools/digitized_traces_check.json, comparable with simulation/data/digitized_traces_raw.json."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "data", "source_plots")
from PIL import Image
import numpy as np, json
G={ # graf: (img, x0,x1, [(ylo,yhi) lux,PE,CE], ndata)
 19:("A1-1.png",1,7,[(0,10),(-100,0),(0,10)],7),
 20:("A1-2.png",1,11,[(0,40),(-100,0),(0,10)],11),
 22:("A1-3.png",0,14,[(0,100),(0,100),(-10,0)],13),
 24:("A1-4.png",1,10,[(20,60),(0,100),(-10,0)],10),
 26:("A2-1.png",0,30,[(8,12),(-20,20),(-5,5)],27),
 27:("A2-2.png",0,35,[(0,20),(-100,100),(-10,10)],35),
 28:("A2-3.png",0,25,[(0,40),(-100,100),(-10,10)],24),
 29:("A2-4.png",0,16,[(33,34),(-1,1),(-1,1)],16),
 30:("A2-5.png",0,35,[(30,40),(-20,20),(-5,5)],35),
 31:("A2-6.png",0,30,[(20,60),(-50,50),(-10,10)],30),
}
def boxes(im):
    dark=(im.max(axis=2)<140)&(np.abs(im[:,:,2]-im[:,:,0])<20)
    rows=np.where(dark.sum(axis=1)>0.45*im.shape[1])[0]
    # group rows
    grp=[];
    for r in rows:
        if grp and r-grp[-1][-1]<=2: grp[-1].append(r)
        else: grp.append([r])
    hs=[int(np.mean(g)) for g in grp]
    cols=np.where(dark.sum(axis=0)>0.5*(hs[1]-hs[0]) )[0] if len(hs)>1 else []
    return hs,dark
out={}
for g,(f,x0,x1,yl,nd) in G.items():
    im=np.array(Image.open(os.path.join(SRC, f)).convert("RGB")).astype(int)
    hs,dark=boxes(im)
    assert len(hs)==6, (g,hs)
    res=[]
    for k in range(3):
        top,bot=hs[2*k],hs[2*k+1]
        band=dark[top+5:bot-5]
        cs=np.where(band.sum(axis=0)>0.9*band.shape[0])[0]
        left,right=cs.min(),cs.max()
        blue=(im[:,:,2]>200)&(im[:,:,0]<80)&(im[:,:,1]<80)
        ylo,yhi=yl[k]; vals=[]
        for c in range(1,nd+1):
            px=left+(c-x0)/(x1-x0)*(right-left); xi=int(round(px))
            colb=np.where(blue[top-6:bot+6, max(xi-1,0):xi+2].any(axis=1))[0]+top-6
            if len(colb)==0: vals.append(None); continue
            # at vertices choose extreme consistent: use median of blue rows
            yc=(colb.min()+colb.max())/2 if colb.max()-colb.min()<8 else None
            if yc is None:
                # vertex/steep segment: take row nearest to the segment thickness centre at exact column
                cb=np.where(blue[top-6:bot+6, xi])[0]+top-6
                yc=(cb.min()+cb.max())/2 if len(cb) else (colb.min()+colb.max())/2
                flag="*"
            else: flag=""
            v=yhi-(yc-top)/(bot-top)*(yhi-ylo)
            vals.append((round(float(v),2),flag))
        res.append(vals)
    out[g]=res
    print(f"Gráfico {g} ({f}) boxes={hs}")
    names=["lux","PE","CE"]
    for i in range(nd):
        row=[f"{res[k][i][0]:7.2f}{res[k][i][1]:1s}" if res[k][i] else "   None " for k in range(3)]
        print(f"  ciclo {i+1:2d}: "+"  ".join(row))
json.dump({str(k):v for k,v in out.items()},open(os.path.join(HERE,"digitized_traces_check.json"),"w"))
