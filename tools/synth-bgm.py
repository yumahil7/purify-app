# Purify 배경음악 — 완전 자체 합성 (샘플 사용 없음). 원형 버퍼로 렌더링해 루프가 수학적으로 이어짐.
import numpy as np, wave
SR = 44100
BPM = 60
L_SEC = 80.0
N = int(SR * L_SEC)
rng = np.random.default_rng(7)
t_all = np.arange(N) / SR

def midi(m): return 440.0 * 2 ** ((m - 69) / 12)

# 진행 (D major): 각 10초 · 8개 코드
CH = [
  ('D',  [50, 57, 62, 66, 69, 76]),   # Dadd9
  ('Bm', [47, 54, 59, 62, 66, 73]),
  ('G',  [43, 55, 59, 62, 67, 69]),   # Gadd9
  ('A',  [45, 52, 57, 61, 64, 71]),   # Asus2-ish
  ('D/F#',[42, 57, 62, 66, 69, 74]),
  ('G',  [43, 55, 62, 66, 67, 71]),   # Gmaj7
  ('Em', [40, 52, 59, 62, 67, 71]),   # Em7
  ('A',  [45, 52, 57, 62, 64, 69]),   # Asus4 → resolves to D at loop
]
SEG = N // len(CH)

def add_circ(buf, start, sig):
    n = len(sig); idx = (start + np.arange(n)) % N
    np.add.at(buf, idx, sig)

# ---------- 패드 (따뜻한 지속음, 느린 크로스페이드) ----------
pad = np.zeros((2, N))
fade = int(SR * 4.0)
for ci, (_, notes) in enumerate(CH):
    length = SEG + fade
    tt = np.arange(length) / SR
    env = np.ones(length)
    ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, fade))
    env[:fade] = ramp; env[-fade:] = ramp[::-1]
    for side in (0, 1):
        sig = np.zeros(length)
        for m in notes[:5]:
            f = midi(m)
            for det in (-0.06, 0.06):
                ff = f * 2 ** ((det + (0.02 if side else -0.02)) / 12)
                ph = rng.uniform(0, 2*np.pi)
                # 부드러운 음색: 기음 + 약한 2·3배음
                sig += (np.sin(2*np.pi*ff*tt + ph) + 0.18*np.sin(4*np.pi*ff*tt + ph) + 0.05*np.sin(6*np.pi*ff*tt + ph)) / (1 + (m - 40) / 24)
        trem = 1 + 0.08 * np.sin(2*np.pi*0.1*tt + side)
        add_circ(pad[side], ci*SEG - fade//2, sig * env * trem)
pad /= np.max(np.abs(pad)) + 1e-9

# ---------- 피아노 같은 음 ----------
def piano(f, dur=5.0, vel=1.0):
    n = int(SR*dur); tt = np.arange(n)/SR
    out = np.zeros(n)
    for h, a in [(1,1.0),(2,0.45),(3,0.18),(4,0.08),(5,0.04),(6,0.02)]:
        fh = f*h*np.sqrt(1 + 0.0004*h*h)          # 약한 비조화성
        if fh > 9000: break
        dec = 1.6 / (1 + 0.6*(h-1)) * (440/f)**0.25
        out += a*np.sin(2*np.pi*fh*tt)*np.exp(-tt/dec)
    att = np.minimum(1, tt/0.006)
    hammer = np.exp(-tt/0.004)*rng.normal(0,0.03,n)   # 아주 약한 해머 노이즈
    rel = np.ones(n); r = int(SR*0.8); rel[-r:] = np.linspace(1,0,r)**2
    return (out*att + hammer)*rel*vel

pno = np.zeros((2, N))
beat = SR * 60 / BPM
for ci, (_, notes) in enumerate(CH):
    pool = notes[2:] + [notes[2]+12, notes[3]+12]
    for b in range(10):                       # 코드당 10박
        if b % 2 == 1 and rng.random() < 0.55: continue    # 여백
        m = pool[rng.integers(len(pool))]
        if b == 0: m = notes[1] + 12           # 코드 시작음
        vel = rng.uniform(0.45, 0.75) * (1.0 if b == 0 else 0.8)
        start = int(ci*SEG + b*beat + rng.normal(0, 0.012)*SR)
        s = piano(midi(m), 5.0, vel)
        pan = rng.uniform(-0.35, 0.35)
        add_circ(pno[0], start, s*np.sqrt(0.5 - pan/2))
        add_circ(pno[1], start, s*np.sqrt(0.5 + pan/2))
    # 저음 한 번
    s = piano(midi(notes[0] + 12), 6.0, 0.5)
    add_circ(pno[0], ci*SEG, s*0.7); add_circ(pno[1], ci*SEG, s*0.7)
pno /= np.max(np.abs(pno)) + 1e-9

# ---------- 리버브 (원형 FFT 컨볼루션) ----------
def ir(seed, rt=3.2):
    r = np.random.default_rng(seed); n = int(SR*rt*1.3); tt = np.arange(n)/SR
    x = r.normal(0,1,n) * np.exp(-6.9*tt/rt)
    k = 12; x = np.convolve(x, np.ones(k)/k, mode='same')   # 어둡게
    x[:int(SR*0.02)] *= np.linspace(0,1,int(SR*0.02))        # 프리딜레이 느낌
    out = np.zeros(N); out[:n] = x; return out / np.sqrt(np.sum(x**2))
dry = 0.55*pad + 0.75*pno
wet = np.zeros_like(dry)
for side, seed in ((0, 11), (1, 12)):
    wet[side] = np.fft.irfft(np.fft.rfft(dry[side]) * np.fft.rfft(ir(seed)), n=N)
mix = 0.6*dry + 0.55*wet / (np.max(np.abs(wet)) + 1e-9) * np.max(np.abs(dry))

# 아주 완만한 하이컷 (원형 1-pole 두 번)
def lp(x, fc):
    a = np.exp(-2*np.pi*fc/SR); X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1/SR)
    H = (1-a) / (1 - a*np.exp(-2j*np.pi*f/SR)); return np.fft.irfft(X*H*H, n=len(x))
mix = np.stack([lp(mix[0], 7000), lp(mix[1], 7000)])
mix -= mix.mean(axis=1, keepdims=True)

# 조용하게: 피크 -3 dBFS
mix *= 10**(-21/20) / np.sqrt(np.mean(mix**2))
pcm = np.clip(np.round(mix.T * 32767), -32768, 32767).astype('<i2')
with wave.open('purify-bgm.wav', 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
rms = np.sqrt(np.mean(mix**2))
print('duration', N/SR, 'peak dBFS', 20*np.log10(np.max(np.abs(mix))), 'rms dBFS', 20*np.log10(rms))
