import argparse as a,base64 as b,math,sys
from pathlib import Path as P

M=b"musicex\x00";Y=192;H=176;O=72;B=100;G=0x1400
T=bytes(int(abs(math.tan(106+i*.1))*100)&255 for i in range(8))
V=b"QQMusic EncV2,Key:"
K1=bytes.fromhex("3338365A4A592140232A24255E262928")
K2=bytes.fromhex("2A2A232128232425265E6131635A2C54")

def q():
    p=a.ArgumentParser()
    p.add_argument("input",nargs="?",type=P,default=P("1.mflac"))
    p.add_argument("-o","--output",type=P,default=P("1.flac"))
    p.add_argument("--ekey")
    p.add_argument("--chunk-size",type=int,default=1<<20)
    return p.parse_args()

def m(p):
    with p.open("rb") as f:
        f.seek(-16,2);t=f.read(16)
        if len(t)!=16 or t[8:]!=M or int.from_bytes(t[:4],"little")!=Y or int.from_bytes(t[4:8],"little")!=1: raise ValueError("musicex")
        f.seek(-Y,2);d=f.read(H)
        if len(d)!=H: raise ValueError("musicex")
    n=d[O:O+B].decode("utf-16le","ignore").split("\x00",1)[0]
    if not n: raise ValueError("musicex")
    return d,n

def s(p):
    n=p.stat().st_size
    try:
        m(p)
        return n-Y
    except ValueError:
        with p.open("rb") as f:
            f.seek(-4,2);k=int.from_bytes(f.read(4),"little")
        if 0<k<=0x3FF: return n-k-4
    raise ValueError("tail")

def t(d,k):
    if len(d)!=8 or len(k)!=16: raise ValueError("tea")
    y=int.from_bytes(d[:4],"big");z=int.from_bytes(d[4:],"big")
    k=[int.from_bytes(k[i:i+4],"big") for i in range(0,16,4)]
    c=0x9E3779B9;u=(c*16)&0xFFFFFFFF
    for _ in range(16):
        z=(z-((u+y)^(k[2]+((y<<4)&0xFFFFFFFF))^(k[3]+(y>>5))))&0xFFFFFFFF
        y=(y-((u+z)^(k[0]+((z<<4)&0xFFFFFFFF))^(k[1]+(z>>5))))&0xFFFFFFFF
        u=(u-c)&0xFFFFFFFF
    return y.to_bytes(4,"big")+z.to_bytes(4,"big")

def u(d,k):
    if len(d)<16 or len(d)%8: raise ValueError("qqtea")
    p=bytearray(t(d[:8],k));v=b"\0"*8;o=0;n=8
    l=len(d)-(p[0]&7)-10
    if l<0: raise ValueError("qqtea")
    def g():
        nonlocal p,v,o,n
        if n+8>len(d): raise ValueError("qqtea")
        p=bytearray(t(bytes(p[i]^d[n+i] for i in range(8)),k))
        v=d[o:o+8];o=n;n+=8
    i=(p[0]&7)+1;x=1
    while x<=2:
        if i<8:
            i+=1;x+=1
        if i==8:
            g();i=0
    r=bytearray()
    while l:
        if i<8:
            r.append(p[i]^v[i]);i+=1;l-=1
        if i==8 and l:
            g();i=0
    x=1
    while x<8:
        if i<8:
            if p[i]^v[i]: raise ValueError("qqtea")
            i+=1;x+=1
        if i==8 and x<8:
            g();i=0
    return bytes(r)

def k(e):
    d=b.b64decode(e)
    if d.startswith(V):
        d=u(d[len(V):],K1)
        d=u(d,K2)
        d=b.b64decode(d)
    if len(d)<16: raise ValueError("ekey")
    x=bytearray(16)
    for i,v in enumerate(T):
        x[i*2]=v;x[i*2+1]=d[i]
    return d[:8]+u(d[8:],bytes(x))

def r(v,s):
    s&=7
    return ((v<<s)|(v>>(8-s)))&0xFF if s else v

def j(k):
    n=len(k);b=bytearray(i&0xFF for i in range(n));x=0
    for i in range(n):
        x=(x+k[i]+b[i])%n
        b[i],b[x]=b[x],b[i]
    m=1
    for v in k:
        if v:
            x=(v*m)&0xFFFFFFFF
            if not x or x<=m: break
            m=x
    return b,m

def x(k,o,d):
    n=len(k)
    for i in range(len(d)):
        p=o+i
        if p>0x7FFF: p%=0x7FFF
        h=((p*p)+71214)%n
        y=h&7
        d[i]^=r(k[h],y+(-4 if y>3 else 4))

def y(k,m,o,d):
    if o>=128: return 0
    n=min(len(d),128-o);l=len(k)
    for i in range(n):
        p=o+i;v=k[p%l]*(p+1)
        d[i]^=k[(0 if not v else int(m/v*100.0))%l]
    return n

def z(k,b,m,o,d,s,c):
    n=len(k);g=o//G;h=g&0x1FF
    if h>=n: h%=n
    v=k[h]*(g+1);e=0 if not v else int(m/v*100.0);a=o+(e&0x1FF)-g*G
    q=bytearray(b);i=0;j=0
    for _ in range(max(a,0)):
        i=(i+1)%n;j=(j+q[i])%n;q[i],q[j]=q[j],q[i]
    for p in range(c):
        i=(i+1)%n;v=q[i];j=(j+v)%n;q[i],q[j]=q[j],v
        d[s+p]^=q[(v+q[i])%n]

def w(k,o,d):
    b,m=j(k);i=y(k,m,o,d);a=o+i
    while i<len(d):
        e=((a//G)+1)*G;n=min(len(d)-i,e-a)
        z(k,b,m,a,d,i,n)
        i+=n;a+=n

def c(k,o,d):
    d=bytearray(d)
    (w if len(k)>300 else x)(k,o,d)
    return bytes(d)

def l(p):
    with p.open("rb") as f:
        f.seek(-4,2);n=int.from_bytes(f.read(4),"little")
        if 0<n<=0x3FF:
            f.seek(-4-n,2)
            return f.read(n)

def f(a):
    n=None
    try:
        n=m(a.input)[1]
    except ValueError:
        pass
    if a.ekey: e=a.ekey
    elif n is None:
        e=(l(a.input) or b"").decode()
        if not e: raise RuntimeError("ekey")
    else:
        raise RuntimeError("ekey")
    k2=k(e);p=s(a.input)
    with a.input.open("rb") as i:
        d=i.read(min(a.chunk_size,p))
        if not d: raise RuntimeError("empty")
        h=c(k2,0,d)
        if a.output.suffix.lower()==".flac" and not h.startswith(b"fLaC"): raise RuntimeError("fLaC")
        with a.output.open("wb") as o:
            o.write(h);n=len(d)
            while n<p:
                r=min(a.chunk_size,p-n);d=i.read(r)
                if len(d)!=r: raise RuntimeError("eof")
                o.write(c(k2,n,d));n+=r

def main():
    try:
        f(q())
        return 0
    except Exception as e:
        print(e,file=sys.stderr)
        return 1

if __name__=="__main__":
    raise SystemExit(main())
