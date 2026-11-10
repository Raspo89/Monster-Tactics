import asyncio, base64, io, json
import numpy as np
from PIL import Image
from playwright.async_api import async_playwright
G='/home/claude/game/SOURCE/'
class R:
    async def __aenter__(self):
        self.p=await async_playwright().start()
        self.b=await self.p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--use-gl=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'])
        self.pg=await self.b.new_page(); errs=[]
        self.pg.on('pageerror',lambda e:print('PAGEERROR',e))
        await self.pg.goto('http://127.0.0.1:8765/render/index.html'); await self.pg.wait_for_function('window.ready===true',timeout=120000)
        return self
    async def __aexit__(self,*a): await self.b.close(); await self.p.stop()
    async def render(self,**o):
        url=await self.pg.evaluate('o=>window.render(o)',o)
        return Image.open(io.BytesIO(base64.b64decode(url.split(',')[1]))).convert('RGBA')
def bbox(im,th=128):
    a=np.asarray(im)[...,3]>th; ys,xs=np.where(a); return xs.min(),ys.min(),xs.max()+1,ys.max()+1
def fit(src,target):
    """Scale/translate src so its alpha bbox matches target's alpha bbox (uniform scale by height)."""
    sx0,sy0,sx1,sy1=bbox(src); tx0,ty0,tx1,ty1=bbox(target)
    crop=src.crop((sx0,sy0,sx1,sy1)); s=(ty1-ty0)/(sy1-sy0)
    nw=max(1,round((sx1-sx0)*s)); crop=crop.resize((nw,ty1-ty0),Image.LANCZOS)
    out=Image.new('RGBA',target.size,(0,0,0,0)); cx=(tx0+tx1)//2-nw//2; out.alpha_composite(crop,(max(0,cx),ty0)) if cx>=0 else out.paste(crop,(cx,ty0),crop)
    return out
def iou(a,b):
    A=np.asarray(a)[...,3]>128;B=np.asarray(b)[...,3]>128; return (A&B).sum()/max(1,(A|B).sum())
def rgbdiff(a,b):
    A=np.asarray(a).astype(int);B=np.asarray(b).astype(int);m=(A[...,3]>200)&(B[...,3]>200)
    return abs(A[...,:3]-B[...,:3])[m].mean()
