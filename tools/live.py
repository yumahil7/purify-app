import re, os, time, html, urllib.request, sys
sys.path.insert(0, '/workspace/bible/bible-db/scripts')
from books import BOOKS
CODE = {name: code.lower() for _, code, name, _ in BOOKS}
CODE.update({'요한1서': '1jn', '요한2서': '2jn', '요한3서': '3jn'})
D = '/workspace/bible/live/'
def url(book, ch): return f'https://www.bskorea.or.kr/bible/korbibReadpage.php?version=HAN&book={CODE[book]}&chap={ch}'
def chapter(book, ch):
    f = D + f'{CODE[book]}.{ch}.html'
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        for attempt in range(3):
            try:
                req = urllib.request.Request(url(book, ch), headers={'User-Agent': 'Mozilla/5.0 (Purify verse check)'})
                data = urllib.request.urlopen(req, timeout=30).read()
                open(f, 'wb').write(data); time.sleep(0.7); break
            except Exception as e:
                time.sleep(2)
    s = open(f, encoding='utf-8', errors='ignore').read()
    out = {}
    parts = re.split(r'<span class="number">(\d+)(?:&nbsp;|\s)*</span>', s)
    for i in range(1, len(parts), 2):
        n = int(parts[i]); body = parts[i + 1]
        body = re.split(r'<br\s*/?>|</span>\s*</span>|<div', body)[0]
        body = re.sub(r'<a [^>]*class=.?comment[\s\S]*?</a>', '', body)
        body = re.sub(r'<[^>]+>', '', body)
        body = html.unescape(body).replace('\xa0', ' ')
        body = re.sub(r'(^|(?<=\s))[ㄱ-ㅎ0-9]{1,2}\)', '', body)
        body = re.sub(r'\s+', ' ', body).strip()
        if n not in out: out[n] = body
    return out
def get(ref):
    m = re.match(r'^(.+?)\s*(\d+):(\d+)(?:-(\d+))?$', ref.strip())
    bk, ch, a, b = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4) or m.group(3))
    c = chapter(bk, ch)
    vs = [c.get(v) for v in range(a, b + 1)]
    return None if any(v is None for v in vs) else ' '.join(vs)
if __name__ == '__main__':
    for r in sys.argv[1:]: print(r, '|', get(r))
