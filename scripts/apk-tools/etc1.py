"""Decode the game's !ETC textures (10-byte header, ETC1 mip chain) to RGBA PNG."""
import sys, struct
import numpy as np
from PIL import Image
MOD=np.array([[2,8],[5,17],[9,29],[13,42],[18,60],[24,80],[33,106],[47,183]])
def decode(path):
    d=open(path,'rb').read()
    assert d[:4]==b'!ETC',path
    w,h=struct.unpack('<HH',d[4:8])
    n=(w//4)*(h//4)
    blk=np.frombuffer(d[10:10+n*8],dtype='>u4').reshape(n,2).astype(np.int64)
    hi,lo=blk[:,0],blk[:,1]
    diff=(hi>>1)&1; flip=hi&1
    t1=(hi>>5)&7; t2=(hi>>2)&7
    base=np.zeros((n,2,3),np.int64)
    for c,(s4a,s4b,s5,sd) in enumerate([(28,24,27,24),(20,16,19,16),(12,8,11,8)]):
        a4=(hi>>s4a)&15; b4=(hi>>s4b)&15
        b5=(hi>>s5)&31; dd=(hi>>sd)&7; dd=np.where(dd>3,dd-8,dd); c2=b5+dd
        ind1=a4*17; ind2=b4*17
        d1=(b5<<3)|(b5>>2); d2=((c2&31)<<3)|((c2&31)>>2)
        base[:,0,c]=np.where(diff==1,d1,ind1); base[:,1,c]=np.where(diff==1,d2,ind2)
    out=np.zeros((n,4,4,3),np.int64)  # [block,y,x,c]
    for x in range(4):
        for y in range(4):
            i=x*4+y
            msb=(lo>>(16+i))&1; lsb=(lo>>i)&1
            sub=np.where(flip==1,int(y>=2),int(x>=2))
            t=np.where(sub==0,t1,t2)
            mag=np.where(lsb==1,MOD[t,1],MOD[t,0]); val=np.where(msb==1,-mag,mag)
            b=np.where(sub[:,None]==0,base[:,0],base[:,1])
            out[:,y,x]=np.clip(b+val[:,None],0,255)
    img=out.reshape(h//4,w//4,4,4,3).transpose(0,2,1,3,4).reshape(h,w,3).astype(np.uint8)
    return Image.fromarray(img,'RGB')
if __name__=='__main__':
    decode(sys.argv[1]).save(sys.argv[2])
def decode_alpha(etc, a8=None):
    """ETC colour plus optional LUM8 alpha file (8-byte header: 'LUM8', width, height)."""
    import os
    im=decode(etc).convert('RGBA')
    if a8 and os.path.isfile(a8):
        d=open(a8,'rb').read(); w,h=struct.unpack('<HH',d[4:8])
        a=Image.frombytes('L',(w,h),d[8:8+w*h])
        if a.size!=im.size: a=a.resize(im.size)
        im.putalpha(a)
    return im
