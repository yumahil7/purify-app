# 그레고리오 성가 — 선율만 부드러운 오르간/패드로 직접 합성 (노래·녹음·외부 MIDI 없음). 자유 리듬, 느리게.
import numpy as np, wave, json
SR = 32000; U = 0.66
J = json.load(open('chant_notes.json'))
def midi(m): return 440.0 * 2 ** ((m - 69) / 12)
def organ(f, dur, vel):
    rel = 0.35; n = int(SR*(dur + rel)); tt = np.arange(n)/SR
    out = np.zeros(n)
    for h, a in ((1,1.0),(2,0.32),(3,0.10),(4,0.07),(6,0.025)):
        out += a*np.sin(2*np.pi*f*h*tt*(1 + 0.0007*np.sin(2*np.pi*0.7*tt)))
    env = np.minimum(1, tt/0.09); env = np.where(tt > dur, np.exp(-(tt-dur)/0.12), env)
    return out*env*vel
def drone(m, dur):
    n = int(SR*dur); tt = np.arange(n)/SR; out = np.zeros(n)
    for mm, a in ((m-12, 1.0), (m-5, 0.55), (m, 0.3)):
        for det in (-0.04, 0.04):
            out += a*np.sin(2*np.pi*midi(mm)*2**(det/12)*tt)
    env = np.minimum(1, tt/6) * np.minimum(1, (dur - tt)/6)
    return out*np.clip(env, 0, 1)
PLAN = {'salve': ['salve'], 'veni': ['veni', 'veni'], 'avemaris': ['avemaris', 'avemaris'], 'pange': ['pange', 'pange'], 'ubi': ['ubi', 'ubi_ant']}
J['ubi_ant'] = J['ubi'][:next(i for i, x in enumerate(J['ubi']) if x[0] == 'rest' and x[1] >= 1.5)]
lens = {}
for name, parts in PLAN.items():
    seq = []
    for i, p in enumerate(parts):
        if i: seq.append(['rest', 2.4])
        seq += J[p]
    total = sum(d for _, d in seq) * U + 4.0           # 끝에 여운 4초 (원형으로 처음과 겹침)
    N = int(round(total * SR)); buf = np.zeros(N)
    t = 1.2
    pitches = [p for p, _ in seq if p != 'rest']; fin = pitches[-1]
    for k, (p, d) in enumerate(seq):
        dur = d * U
        if p != 'rest':
            s = organ(midi(p), dur*1.04, 0.5); i0 = int(t*SR); idx = (i0 + np.arange(len(s))) % N; np.add.at(buf, idx, s)
        t += dur
    dr = drone(fin, N/SR) * 0.16; buf += dr
    # 리버브 (원형)
    r = np.random.default_rng(5); n = int(SR*5.5); tt = np.arange(n)/SR
    ir = r.normal(0,1,n)*np.exp(-6.9*tt/4.8); ir = np.convolve(ir, np.ones(10)/10, mode='same'); ir[:int(SR*.03)] *= np.linspace(0,1,int(SR*.03))
    irf = np.zeros(N); irf[:min(n, N)] = ir[:N]; irf /= np.sqrt(np.sum(irf**2))
    wet = np.fft.irfft(np.fft.rfft(buf)*np.fft.rfft(irf), n=N)
    mix = 0.55*buf/np.max(np.abs(buf)) + 0.6*wet/np.max(np.abs(wet))
    X = np.fft.rfft(mix); f = np.fft.rfftfreq(N, 1/SR); a = np.exp(-2*np.pi*5000/SR)
    H = (1-a)/(1-a*np.exp(-2j*np.pi*f/SR)); mix = np.fft.irfft(X*H*H, n=N); mix -= mix.mean()
    mix *= 10**(-23/20)/np.sqrt(np.mean(mix**2)); pk = np.max(np.abs(mix))
    if pk > 0.6: mix *= 0.6/pk
    P = SR//2; pad = np.concatenate([mix[-P:], mix, mix[:P]])
    pcm = np.clip(np.round(pad*32767), -32768, 32767).astype('<i2')
    with wave.open(name + '.wav', 'wb') as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    np.save(name + '-loop.npy', mix); lens[name] = [N, SR]
    print(name, round(N/SR, 2), 's')
json.dump(lens, open('lens.json', 'w'))
