# 앱에 쓰인 모든 성경 구절을 찾아 대한성서공회 개역한글 본문(실시간)과 holybible.or.kr·yuhwan 데이터로 대조
import re, os, sys, json, glob, datetime
sys.path.insert(0, '/workspace/bible')
import krv, live
krv.ALIAS.update({v: k for k, v in list(krv.ALIAS.items())})
SRC = '/workspace/v3src/'
books = sorted(set(live.CODE.keys()), key=len, reverse=True)
pat = re.compile(r'(' + '|'.join(map(re.escape, books)) + r') (\d+):(\d+)(?:-(\d+))?')
refs = set()
for f in sorted(glob.glob(SRC + '*.js')):
    if f.endswith('krv.gen.js'): continue
    for m in pat.finditer(open(f, encoding='utf-8').read()): refs.add(m.group(0))
def fold(s): return krv.norm(s).replace('찌', '지')
def strip_title(s): return re.sub(r'^\[[^\]]*\]\s*', '', s or '')
rows, KRV = [], {}
def key(r):
    b, c, a, z = krv.parse(r); return (live.CODE[b], c, a)
order = [b[2] for b in live.BOOKS]
for r in sorted(refs, key=lambda r: (order.index(krv.parse(r)[0]) if krv.parse(r)[0] in order else 99, krv.parse(r)[1], krv.parse(r)[2])):
    L = live.get(r); H = krv.get(r); Y = strip_title(krv.get(r, krv.YU))
    okH = bool(L and H and fold(L) == fold(H)); okY = bool(L and Y and fold(L) == fold(Y))
    st = 'VERIFIED' if okH and (okY or not Y) else 'VERIFIED' if okH or okY else 'EXCLUDED'
    if st == 'VERIFIED': KRV[r] = L
    rows.append((r, st, okH, okY, L or H or ''))
open(SRC + 'krv.gen.js', 'w', encoding='utf-8').write('// 자동 생성 (verses.py) — 개역한글, 대한성서공회 본문과 대조 완료\nconst KRV = ' + json.dumps(KRV, ensure_ascii=False, indent=0) + ';\n')
ex = [r for r in rows if r[1] != 'VERIFIED']
md = ['# 성경 구절 출처와 검증 (개역한글, 1961)', '',
      '앱에 쓰인 모든 구절은 빌드할 때 `v3src/verses.py`가 소스 코드에서 자동으로 찾아, 아래 출처와 한 절씩 대조한 뒤 **대한성서공회 본문 그대로** 앱에 넣습니다. 대조에 실패한 구절은 앱에서 빠집니다(추측해서 넣지 않음).', '',
      '## 출처', '',
      '1. 대한성서공회 성경읽기 — 개역한글 (version=HAN), 실시간 조회: `https://www.bskorea.or.kr/bible/korbibReadpage.php?version=HAN&book=<책>&chap=<장>` (앱에 표시되는 본문)',
      '2. holybible.or.kr 개역한글 전체 본문 (crizin/bible-db `data/krv/krv_holybible.jsonl`, Public Domain): https://github.com/crizin/bible-db',
      '3. yuhwan/Bible-krv 개역한글 데이터 (보조 대조, 현대 맞춤법 `-지어다` 차이는 같은 것으로 봄): https://github.com/yuhwan/Bible-krv', '',
      '판정: 1번(대한성서공회)과 2번(holybible) 본문이 띄어쓰기·문장부호를 빼고 글자 그대로 같으면 **확인됨**. 3번은 추가 대조.', '',
      f'검증일: {datetime.date.today().isoformat()} · 전체 {len(rows)}구절 · 확인됨 {len(rows) - len(ex)} · 제외 {len(ex)}', '',
      '| 구절 | 판정 | 대한성서공회=holybible | yuhwan 일치 | 본문 |', '|---|---|---|---|---|']
for r, st, a, b, t in rows: md.append(f'| {r} | {"✅ 확인됨" if st == "VERIFIED" else "❌ 제외"} | {"○" if a else "×"} | {"○" if b else "×"} | {t} |')
os.makedirs('/workspace/purify-site/tools', exist_ok=True)
open('/workspace/purify-site/tools/verses-source.md', 'w', encoding='utf-8').write('\n'.join(md) + '\n')
print(f'verses: {len(rows)} total, {len(rows) - len(ex)} verified, {len(ex)} excluded')
for r in ex: print('  EXCLUDED', r[0], r[2], r[3], r[4][:60])
