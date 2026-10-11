import json, re, os
B='/workspace/bible/'
def _load(path):
    d={}
    for l in open(path,encoding='utf-8'):
        o=json.loads(l); d[(o['name_kr'],o['chapter'],o['verse'])]=o['text']
    return d
HB=_load(B+'bible-db/data/krv/krv_holybible.jsonl')
BS=_load(B+'bible-db/data/krv/krv_bskorea.jsonl')
YU={}
for f in os.listdir(B+'Bible-krv'):
    if f.endswith('.json') and f!='books.json':
        o=json.load(open(B+'Bible-krv/'+f,encoding='utf-8'))
        for c in o['chapters']:
            for v in c['verses']: YU[(o['book'],c['chapter'],v['verse'])]=v['text']
ALIAS={'요한일서':'요한1서','요한이서':'요한2서','요한삼서':'요한3서'}
def norm(s): return re.sub(r'[\s\.,·“”"\'‘’!?;:()\-–—]','',s)
def parse(ref):
    m=re.match(r'^(.+?)\s*(\d+):(\d+)(?:-(\d+))?$',ref.strip())
    bk,ch,v1,v2=m.group(1),int(m.group(2)),int(m.group(3)),int(m.group(4) or m.group(3))
    return bk,ch,v1,v2
def get(ref, src=HB):
    bk,ch,v1,v2=parse(ref)
    keys=[bk,ALIAS.get(bk,bk)]
    out=[]
    for v in range(v1,v2+1):
        t=None
        for k in keys:
            t=src.get((k,ch,v))
            if t: break
        if t is None: return None
        out.append(t)
    return ' '.join(out)
def books(src): return sorted(set(k[0] for k in src))
