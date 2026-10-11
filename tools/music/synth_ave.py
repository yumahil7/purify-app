# 아베마리아 (Schubert D.839, PD) — 선율만 살린 가벼운 편곡을 직접 합성. 샘플·녹음·외부 MIDI 사용 없음.
import numpy as np, wave
from melody import MEL, CH, INTRO
SR = 44100; BPM = 46; BEAT = 60 / BPM
BARS = 1 + 10 + 10
N = int(round(SR * BEAT * 4 * BARS))
rng = np.random.default_rng(3)
def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
def add_circ(buf, start, sig):
    idx = (start + np.arange(len(sig))) % N; np.add.at(buf, idx, sig)
def at(beat): return int(round(beat * BEAT * SR))

def piano(f, dur, vel):
    n = int(SR*dur); tt = np.arange(n)/SR; out = np.zeros(n)
    for h, a in [(1,1.0),(2,0.4),(3,0.14),(4,0.06),(5,0.03)]:
        fh = f*h*np.sqrt(1 + 0.0004*h*h)
        if fh > 8000: break
        dec = 2.2 / (1 + 0.7*(h-1)) * (440/f)**0.25
        out += a*np.sin(2*np.pi*fh*tt)*np.exp(-tt/dec)
    att = np.minimum(1, tt/0.008); rel = np.ones(n); r = int(SR*0.6); rel[-r:] = np.linspace(1,0,r)**2
    return out*att*rel*vel

def strings(f, dur, vel):
    rel_t = 0.5; n = int(SR*(dur + rel_t)); tt = np.arange(n)/SR
    vib = 1 + 0.0035*np.sin(2*np.pi*4.8*tt) * np.minimum(1, tt/0.6)
    ph = 2*np.pi*f*np.cumsum(vib)/SR; out = np.zeros(n)
    for h in range(1, 8):
        if f*h > 7000: break
        out += np.sin(h*ph + 0.3*h) / h**1.6
    env = np.minimum(1, tt/0.22) ; env = np.where(tt > dur, np.exp(-(tt-dur)/0.18), env)
    return out*env*vel*(1 + 0.05*np.sin(2*np.pi*0.3*tt))

def pad_chord(notes, dur, vel):
    xf = 0.8; n = int(SR*(dur + xf)); tt = np.arange(n)/SR; out = np.zeros(n)
    for m in notes:
        f = midi(m)
        for det in (-0.05, 0.05):
            ff = f*2**(det/12); p = rng.uniform(0, 2*np.pi)
            out += (np.sin(2*np.pi*ff*tt+p) + 0.15*np.sin(4*np.pi*ff*tt+p)) / (1 + max(0, m-48)/30)
    env = np.ones(n); a = int(SR*xf)
    ramp = 0.5 - 0.5*np.cos(np.linspace(0, np.pi, a)); env[:a] = ramp; env[-a:] = ramp[::-1]
    return out*env*vel

L = np.zeros(N); R = np.zeros(N)
def put(sig, beat, pan=0.0):
    s = at(beat); add_circ(L, s, sig*np.sqrt(.5-pan/2)); add_circ(R, s, sig*np.sqrt(.5+pan/2))

chords = INTRO + [c for bar in CH for c in bar] * 2
for i, (bass, up) in enumerate(chords):          # 박마다 패드 (같은 화음이면 이어 붙임)
    put(pad_chord(up, BEAT, 0.10), i - 0.3, -0.15)
    put(pad_chord([bass, bass+12], BEAT, 0.12), i - 0.3, 0.1)
# 두 번째 절에는 피아노가 화음을 아주 작게 짚어 줌
for i, (bass, up) in enumerate(chords):
    if i < 4 + 40: continue
    if i % 2 == 0: put(piano(midi(bass+12), 3.0, 0.22), i + 0.02, 0.2)
    put(piano(midi(up[(i//1) % len(up)]), 2.2, 0.12), i + 0.5, 0.25)

def melody(start, voice):
    b = start
    for k, (m, d) in enumerate(MEL):
        if m is not None:
            if voice == 'piano': put(piano(midi(m), max(2.0, d*BEAT + 1.2), 0.55 if d >= 0.5 else 0.42), b + rng.normal(0, 0.006), -0.1)
            else:
                nxt = MEL[k+1][0] if k+1 < len(MEL) else None
                put(strings(midi(m - 12 if False else m), d*BEAT*(1.02 if nxt else 0.9), 0.16), b, 0.05)
        b += d
melody(4, 'piano')
melody(44, 'strings')

def ir(seed, rt=3.6):
    r = np.random.default_rng(seed); n = int(SR*rt*1.3); tt = np.arange(n)/SR
    x = r.normal(0,1,n)*np.exp(-6.9*tt/rt); x = np.convolve(x, np.ones(14)/14, mode='same')
    x[:int(SR*.025)] *= np.linspace(0,1,int(SR*.025)); out = np.zeros(N); out[:n] = x; return out/np.sqrt(np.sum(x**2))
dry = np.stack([L, R]); dry /= np.max(np.abs(dry))
wet = np.stack([np.fft.irfft(np.fft.rfft(dry[i])*np.fft.rfft(ir(21+i)), n=N) for i in (0,1)])
mix = 0.62*dry + 0.5*wet/np.max(np.abs(wet))
def lp(x, fc):
    a = np.exp(-2*np.pi*fc/SR); X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1/SR)
    H = (1-a)/(1-a*np.exp(-2j*np.pi*f/SR)); return np.fft.irfft(X*H*H, n=len(x))
mix = np.stack([lp(mix[0], 6500), lp(mix[1], 6500)]); mix -= mix.mean(axis=1, keepdims=True)
mix *= 10**(-22/20)/np.sqrt(np.mean(mix**2))
pk = np.max(np.abs(mix))
if pk > 0.7: mix *= 0.7/pk
P = SR//2
padded = np.concatenate([mix[:, -P:], mix, mix[:, :P]], axis=1)
for name, x in (('ave-loop.wav', mix), ('ave-padded.wav', padded)):
    pcm = np.clip(np.round(x.T*32767), -32768, 32767).astype('<i2')
    with wave.open(name, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
print('loop sec', N/SR, 'peak dBFS', 20*np.log10(np.max(np.abs(mix))), 'rms', 20*np.log10(np.sqrt(np.mean(mix**2))))
