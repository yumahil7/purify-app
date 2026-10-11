# GregoBase gabc (Liber Usualis 1961 등 공용 성가집의 디지털 전사)에서 음높이만 읽어 단순 음표 목록으로 바꿈.
# 결과(chant_notes.json)는 사람이 읽고 확인할 수 있는 '음이름 + 길이' 목록이며, 리듬·편곡은 직접 정함.
import re, json
DIA = [0, 2, 4, 5, 7, 9, 11]          # C D E F G A B
def segs(fname):
    s = open(fname, encoding='utf-8').read().split('%%', 1)[1]
    clef = re.search(r'\((c|f)(\d)\)', s); kind, line = clef.group(1), int(clef.group(2))
    s = s[clef.end():]
    out = []; cur = []
    for m in re.finditer(r'\(([^)]*)\)', s):
        g = m.group(1)
        if g.strip() in (',', ';', ':', '::', '`', "'") or re.fullmatch(r"[,;:`]+", g.strip() or 'x'):
            cur.append(('bar', g.strip())); 
            if g.strip() == '::': out.append(cur); cur = []
            continue
        cur.append(('neume', g))
    return kind, line, out
def pitch(letter, kind, line, flats):
    pos = 'abcdefghijklm'.index(letter)
    ref = 1 + 2 * line                        # 줄 n의 위치 (d=줄1 → index 3)
    step = pos - ref                          # 도(또는 파) 기준 몇 도 위
    base = 0 if kind == 'c' else 5
    k = base // 1; idx = (DIA.index(base) + step)
    o, r = divmod(idx, 7)
    semi = 72 + 12 * o + DIA[r] - (1 if letter in flats else 0)
    return semi
def notes(fname, take):
    kind, line, out = segs(fname)
    res = []
    for seg in out[:take]:
        flats = set()
        for typ, g in seg:
            if typ == 'bar':
                res.append(['rest', {',':0.35, ';':0.7, ':':0.9, '::':1.6, '`':0.2}.get(g, 0.4)]); flats = set(); continue
            g = re.sub(r'\[[^\]]*\]|<[^>]*>', '', g)
            for a in re.finditer(r'([a-m])x', g): flats.add(a.group(1))
            for a in re.finditer(r'([a-m])y', g): flats.discard(a.group(1))
            g2 = re.sub(r'[a-m][xy#]', '', g)
            for a in re.finditer(r'([a-mA-M])([^a-mA-M]*)', g2):
                L = a.group(1).lower(); mod = a.group(2)
                d = 1.0
                if '..' in mod: d = 2.2
                elif '.' in mod: d = 1.9
                elif '_' in mod: d = 1.4
                if a.group(1).isupper(): d *= 0.8      # 마름모꼴 음은 가볍게
                res.append([pitch(L, kind, line, flats), d])
    while res and res[-1][0] == 'rest': res.pop()
    return res
CH = {'salve': ('2435.gabc', 9), 'veni': ('2923.gabc', 1), 'avemaris': ('2232.gabc', 1), 'pange': ('1310.gabc', 1), 'ubi': ('1013.gabc', 3)}
J = {k: notes(f, n) for k, (f, n) in CH.items()}
json.dump(J, open('chant_notes.json', 'w'), indent=0)
NAMES = ['C','C#','D','Eb','E','F','F#','G','Ab','A','Bb','B']
for k, v in J.items():
    ps = [p for p, d in v if p != 'rest']
    print(k, len(ps), 'notes', min(ps), max(ps), ' '.join(NAMES[p % 12] + str(p // 12 - 1) if p != 'rest' else '|' for p, d in v[:40]))
