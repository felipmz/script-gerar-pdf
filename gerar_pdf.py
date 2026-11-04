"""Gera um PDF simples (texto + imagens PNG/JPG) a partir de um arquivo JSON.

Uso:
    python3 gerar_pdf.py <conteudo.json> <saida.pdf>

Só usa a biblioteca padrão do Python. Veja o README para o formato do JSON.
"""
import sys, zlib, struct, unicodedata, os, json
if len(sys.argv) != 3:
    sys.exit("Uso: python3 gerar_pdf.py <conteudo.json> <saida.pdf>")
fonte, out = sys.argv[1], sys.argv[2]
with open(fonte, encoding="utf-8") as f:
    DADOS = json.load(f)
# Imagens: relativas à pasta do JSON, ou a "pasta_imagens" se informada.
IMG = os.path.join(os.path.dirname(os.path.abspath(fonte)), DADOS.get("pasta_imagens", "")) + os.sep

W = {32:278,33:278,34:355,35:556,36:556,37:889,38:667,39:191,40:333,41:333,42:389,43:584,44:278,45:333,46:278,47:278,
 58:278,59:278,60:584,61:584,62:584,63:556,64:1015,91:278,92:278,93:278,94:469,95:556,96:333,123:334,124:260,125:334,126:584}
for c in range(48,58): W[c]=556
for ch,w in zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ",[667,667,722,722,667,611,778,722,278,500,667,556,833,722,778,667,778,722,667,611,722,667,944,667,667,611]): W[ord(ch)]=w
for ch,w in zip("abcdefghijklmnopqrstuvwxyz",[556,556,500,556,556,278,556,556,222,222,500,222,833,556,556,556,556,333,500,278,556,500,722,500,500,500]): W[ord(ch)]=w
def cw(ch):
    if ch in "“”": return 333
    if ch=="–": return 556
    if ch=="·": return 278
    if ch=="•": return 350
    if ord(ch) in W: return W[ord(ch)]
    b = unicodedata.normalize("NFD", ch)[0]
    return W.get(ord(b), 556)
def tw(s, size): return sum(cw(c) for c in s)*size/1000

def esc(s):
    return s.encode("cp1252").decode("latin-1").replace("\\","\\\\").replace("(","\\(").replace(")","\\)")

PW, PH, M = 595, 842, 56
objs = []   # bytes bodies
def add(b): objs.append(b); return len(objs)

# images
def png_rgb(path):
    d = open(path,"rb").read(); p = 8; idat=b""
    while p < len(d):
        n,t = struct.unpack(">I4s", d[p:p+8]); body = d[p+8:p+8+n]
        if t==b"IHDR": w,h,bd,ct = struct.unpack(">IIBB", body[:10]); assert bd==8 and ct==6
        if t==b"IDAT": idat+=body
        p += 12+n
    raw = zlib.decompress(idat); bpp=4; stride=w*bpp; rows=[]; prev=bytearray(stride); q=0
    for _ in range(h):
        f=raw[q]; line=bytearray(raw[q+1:q+1+stride]); q+=1+stride
        for i in range(stride):
            a = line[i-bpp] if i>=bpp else 0; b = prev[i]; c = prev[i-bpp] if i>=bpp else 0
            if f==1: line[i]=(line[i]+a)&255
            elif f==2: line[i]=(line[i]+b)&255
            elif f==3: line[i]=(line[i]+((a+b)>>1))&255
            elif f==4:
                pa,pb,pc=abs(b-c),abs(a-c),abs(a+b-2*c)
                pr = a if pa<=pb and pa<=pc else (b if pb<=pc else c)
                line[i]=(line[i]+pr)&255
        rows.append(line); prev=line
    rgb=bytearray()
    for line in rows:
        for x in range(w):
            r,g,b_,al = line[x*4:x*4+4]
            rgb += bytes(((r*al+255*(255-al))//255, (g*al+255*(255-al))//255, (b_*al+255*(255-al))//255))
    return w,h,zlib.compress(bytes(rgb))
def jpg(path):
    d=open(path,"rb").read(); p=2
    while True:
        m=d[p+1]; n=struct.unpack(">H",d[p+2:p+4])[0]
        if m in (0xC0,0xC1,0xC2): h,w=struct.unpack(">HH",d[p+5:p+9]); return w,h,d
        p+=2+n
def addimg(kind,path):
    if kind=="png":
        w,h,data = png_rgb(path); filt="/FlateDecode"
    else:
        w,h,data = jpg(path); filt="/DCTDecode"
    n = add(b"<< /Type/XObject/Subtype/Image/Width %d/Height %d/ColorSpace/DeviceRGB/BitsPerComponent 8/Filter %s/Length %d >>\nstream\n"%(w,h,filt.encode(),len(data))+data+b"\nendstream")
    return n,w,h

def _item(d):
    t = d["tipo"]
    if t in ("h1", "h2", "p"):
        return (t, d["texto"])
    if t == "li":
        return ("li", d.get("nivel", 1), d["texto"])
    if t == "img":
        nome = d["arquivo"]
        return ("img", "png" if nome.lower().endswith(".png") else "jpg", nome)
    sys.exit("Tipo desconhecido: " + t)
content = [_item(d) for d in DADOS["itens"]]
TITULO = DADOS.get("titulo", "Documento")

def wrap(text,size,width):
    lines=[];cur=""
    for w in text.split(" "):
        t = (cur+" "+w) if cur else w
        if tw(t,size)<=width or not cur: cur=t
        else: lines.append(cur); cur=w
    lines.append(cur); return lines

pages=[]; ops=[]; y=PH-M; xobjs={}
def newpage():
    global ops,y,xobjs
    if ops or xobjs: pages.append((ops,xobjs))
    ops=[]; xobjs={}; y=PH-M
def text(x,yy,s,font,size): ops.append("BT /%s %d Tf %.2f %.2f Td (%s) Tj ET"%(font,size,x,yy,esc(s)))
newpage()
imgcache={}
for it in content:
    k=it[0]
    if k=="h1":
        y-=22; text(M,y,it[1],"F2",24); y-=14
    elif k=="h2":
        if y<M+80: newpage()
        y-=26; text(M,y,it[1],"F2",16); y-=6
    elif k in("p","li"):
        size=11; lead=16
        if k=="li":
            lvl=it[1]; txt=it[2]; ind=14+(lvl-1)*18; x=M+ind
            lines=wrap(txt,size,PW-2*M-ind-12)
            if y-lead*len(lines)<M and len(lines)<6: newpage()
            first=True
            for ln in lines:
                if y-lead<M: newpage()
                y-=lead
                if first: text(x-12,y,"•" if lvl==1 else "-","F1",size); first=False
                text(x,y,ln,"F1",size)
            y-=5
        else:
            lines=wrap(it[1],size,PW-2*M)
            for ln in lines:
                if y-lead<M: newpage()
                y-=lead; text(M,y,ln,"F1",size)
            y-=5
    elif k=="img":
        kind,fn=it[1],it[2]
        if fn not in imgcache: imgcache[fn]=addimg(kind,IMG+fn)
        n,w,h=imgcache[fn]; dw=300 if w<=500 else 330; dh=dw*h/w
        if y-dh-12<M: newpage()
        y-=dh+8; x=(PW-dw)/2; name="Im%d"%n; xobjs[name]=n
        ops.append("q %.2f 0 0 %.2f %.2f %.2f cm /%s Do Q"%(dw,dh,x,y,name)); y-=6
newpage()
pages=[p for p in pages if p[0] or p[1]]

f1=add(b"<< /Type/Font/Subtype/Type1/BaseFont/Helvetica/Encoding/WinAnsiEncoding >>")
f2=add(b"<< /Type/Font/Subtype/Type1/BaseFont/Helvetica-Bold/Encoding/WinAnsiEncoding >>")
pids=[]; pages_obj_id=len(objs)+1+2*len(pages)  # reserve: compute after
# page objects: content then page
cont_ids=[];page_ids=[]
start=len(objs)
pages_id = start + 2*len(pages) + 1
for i,(o,xo) in enumerate(pages):
    s=("\n".join(o)).encode("latin-1")
    c=add(b"<< /Length %d >>\nstream\n"%len(s)+s+b"\nendstream")
    xs=" ".join("/%s %d 0 R"%(k,v) for k,v in xo.items())
    pg=add(("<< /Type/Page/Parent %d 0 R/MediaBox[0 0 %d %d]/Contents %d 0 R/Resources<< /Font<< /F1 %d 0 R/F2 %d 0 R >>/XObject<< %s >> >> >>"%(pages_id,PW,PH,c,f1,f2,xs)).encode())
    page_ids.append(pg)
pid=add(("<< /Type/Pages/Kids[%s]/Count %d >>"%(" ".join("%d 0 R"%p for p in page_ids),len(page_ids))).encode())
assert pid==pages_id
cat=add(b"<< /Type/Catalog/Pages %d 0 R >>"%pid)
info=add(("<< /Title (%s) >>" % esc(TITULO)).encode("latin-1"))
buf=bytearray(b"%PDF-1.4\n"); offs=[]
for i,o in enumerate(objs,1):
    offs.append(len(buf)); buf+=b"%d 0 obj\n"%i+o+b"\nendobj\n"
x=len(buf); buf+=b"xref\n0 %d\n0000000000 65535 f \n"%(len(objs)+1)
for o in offs: buf+=b"%010d 00000 n \n"%o
buf+=b"trailer\n<< /Size %d/Root %d 0 R/Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"%(len(objs)+1,cat,info,x)
assert not os.path.exists(out)
open(out,"wb").write(buf); print("ok",len(pages),"paginas")
