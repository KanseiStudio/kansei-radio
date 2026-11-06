"""Motore di sintesi minimale (numpy/scipy) per i brani di Kansei Radio."""
import numpy as np
import scipy.signal as ss

SR = 44100


def mtof(m):
    return 440.0 * 2 ** ((np.asarray(m, dtype=float) - 69) / 12)


def secs(n):
    return np.arange(n) / SR


# ---------------------------------------------------------------- oscillatori
def saw(f, n, ph0=0.0):
    dt = f / SR
    ph = (ph0 + np.arange(n) * dt) % 1.0
    y = 2 * ph - 1
    m = ph < dt
    x = ph[m] / dt
    y[m] -= x + x - x * x - 1
    m = ph > 1 - dt
    x = (ph[m] - 1) / dt
    y[m] -= x * x + x + x + 1
    return y


def pulse(f, n, width=0.5, ph0=0.0):
    return saw(f, n, ph0) - saw(f, n, ph0 + width)


def sine(f, n, ph0=0.0):
    return np.sin(2 * np.pi * (f * np.arange(n) / SR + ph0))


def sine_fm(freq_arr):
    """Seno a frequenza variabile (array)."""
    return np.sin(2 * np.pi * np.cumsum(freq_arr) / SR)


def noise(n, rng):
    return rng.standard_normal(n)


# ---------------------------------------------------------------- inviluppi
def adsr(gate, a=0.01, d=0.1, s=0.7, r=0.2):
    ng = max(1, int(gate * SR))
    nr = max(1, int(r * SR))
    x = np.arange(ng) / SR
    e = np.full(ng, float(s))
    if a > 0:
        m = x < a
        e[m] = x[m] / a
    if d > 0:
        m = (x >= a) & (x < a + d)
        e[m] = 1 - (1 - s) * ((x[m] - a) / d)
    lvl = e[-1]
    rel = lvl * (1 - np.arange(nr) / nr) ** 2
    return np.concatenate([e, rel])


def expdec(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


# ---------------------------------------------------------------- filtri
def _clip_fc(fc):
    return float(np.clip(fc, 20, SR * 0.45))


def lp(x, fc, order=2):
    return ss.sosfilt(ss.butter(order, _clip_fc(fc), "low", fs=SR, output="sos"), x)


def hp(x, fc, order=2):
    return ss.sosfilt(ss.butter(order, _clip_fc(fc), "high", fs=SR, output="sos"), x)


def bp(x, lo, hi, order=2):
    return ss.sosfilt(ss.butter(order, [_clip_fc(lo), _clip_fc(hi)], "band", fs=SR, output="sos"), x)


def _rbj_lp(fc, q):
    w0 = 2 * np.pi * _clip_fc(fc) / SR
    al = np.sin(w0) / (2 * q)
    c = np.cos(w0)
    b = np.array([(1 - c) / 2, 1 - c, (1 - c) / 2])
    a = np.array([1 + al, -2 * c, 1 - al])
    return b / a[0], a / a[0]


def sweep_lp(x, fc_func, q=0.9, block=256):
    """Lowpass risonante con cutoff variabile nel tempo: fc_func(t_sec) -> Hz."""
    out = np.empty_like(x)
    zi = np.zeros(2)
    for i in range(0, len(x), block):
        b, a = _rbj_lp(fc_func((i + block / 2) / SR), q)
        out[i:i + block], zi = ss.lfilter(b, a, x[i:i + block], zi=zi)
    return out


# ---------------------------------------------------------------- effetti
def make_ir(sec, damp=6000, seed=0, predelay=0.012):
    rng = np.random.default_rng(seed)
    n = int(sec * SR)
    t = secs(n)
    env = np.exp(-6.9 * t / sec)
    pd = int(predelay * SR)
    irs = []
    for _ in range(2):
        nz = rng.standard_normal(n) * env
        nz = lp(nz, damp, 1)
        nz = np.concatenate([np.zeros(pd), nz])
        irs.append(nz / np.sqrt(np.sum(nz ** 2)))
    return np.array(irs)


def reverb(st, ir):
    n = st.shape[1]
    out = np.zeros_like(st)
    for c in range(2):
        out[c] = ss.fftconvolve(st[c], ir[c])[:n]
    return out


def pingpong(st, time, fb=0.5, taps=8, lpf=3500, hpf=200):
    n = st.shape[1]
    d = int(time * SR)
    out = np.zeros_like(st)
    sig = hp(st.mean(0), hpf, 1)
    for k in range(1, taps + 1):
        sig = lp(sig, lpf, 1) * fb
        s = k * d
        if s >= n:
            break
        out[k % 2, s:] += sig[: n - s]
    return out


def width(st, amt=1.0):
    m = st.mean(0)
    s = (st[0] - st[1]) / 2
    return np.array([m + s * amt, m - s * amt])


def drive(x, amt=1.5):
    return np.tanh(x * amt) / np.tanh(amt)


def crush(x, bits=8, down=4):
    q = 2 ** (bits - 1)
    y = np.round(x * q) / q
    y = np.repeat(y[::down], down)[: len(x)]
    return y


# ---------------------------------------------------------------- mixer
class Mix:
    def __init__(self, dur, seed=0):
        self.N = int(dur * SR)
        self.dur = dur
        self.bus = {}
        self.rng = np.random.default_rng(seed)

    def add(self, bus, t0, sig, pan=0.0, g=1.0):
        b = self.bus.setdefault(bus, np.zeros((2, self.N)))
        i = int(round(t0 * SR))
        if i >= self.N or i < 0:
            return
        if sig.ndim == 1:
            sig = sig[: self.N - i]
            a = (pan + 1) * np.pi / 4
            b[0, i:i + len(sig)] += sig * g * np.cos(a)
            b[1, i:i + len(sig)] += sig * g * np.sin(a)
        else:
            sig = sig[:, : self.N - i]
            b[:, i:i + sig.shape[1]] += sig * g

    def get(self, bus):
        return self.bus.get(bus, np.zeros((2, self.N)))


def duck(n, times, depth=0.6, rel=0.18):
    """Inviluppo di sidechain: abbassa al passaggio della cassa."""
    g = np.ones(n)
    L = int(rel * 4 * SR)
    shape = 1 - depth * np.exp(-np.arange(L) / (rel * SR))
    for t in times:
        i = int(t * SR)
        if i >= n:
            continue
        seg = shape[: n - i]
        g[i:i + len(seg)] = np.minimum(g[i:i + len(seg)], seg)
    return g


# ---------------------------------------------------------------- batteria
def kick(rng, tone=48, punch=160, decay=0.32, click=0.25, drv=1.8):
    n = int(decay * 6 * SR)
    t = secs(n)
    f = tone + (punch - tone) * np.exp(-t / 0.028)
    y = sine_fm(f) * np.exp(-t / decay)
    c = hp(rng.standard_normal(n), 2000) * np.exp(-t / 0.004) * click
    return drive(y + c, drv)


def snare(rng, tone=190, ndec=0.16, bright=6000, tone_amt=0.55):
    n = int(ndec * 6 * SR)
    t = secs(n)
    body = sine_fm(tone * (1 + 0.5 * np.exp(-t / 0.01))) * np.exp(-t / 0.06) * tone_amt
    nz = bp(rng.standard_normal(n), 1200, bright) * np.exp(-t / ndec)
    return body + nz * 0.9


def hat(rng, decay=0.035, lo=7500):
    n = int(decay * 7 * SR)
    t = secs(n)
    return hp(rng.standard_normal(n), lo, 2) * np.exp(-t / decay)


def clap(rng, decay=0.18):
    n = int((decay * 5 + 0.04) * SR)
    t = secs(n)
    env = np.exp(-t / decay)
    for k in range(3):
        i = int(k * 0.011 * SR)
        e = np.zeros(n)
        e[i:] = np.exp(-np.arange(n - i) / (0.006 * SR))
        env = np.maximum(env * (t > 0.022), e) if k < 2 else np.maximum(env, e)
    return bp(rng.standard_normal(n), 900, 3200) * env


def shaker(rng, decay=0.06):
    n = int(decay * 5 * SR)
    t = secs(n)
    env = np.minimum(t / 0.012, 1) * np.exp(-t / decay)
    return bp(rng.standard_normal(n), 4500, 12000) * env


def rim(rng, f=1700, decay=0.018):
    n = int(decay * 8 * SR)
    t = secs(n)
    return sine(f, n) * np.exp(-t / decay) + bp(rng.standard_normal(n), 2000, 6000) * np.exp(-t / 0.006) * 0.6


def woodblock(f=880, decay=0.05):
    n = int(decay * 6 * SR)
    t = secs(n)
    return (sine(f, n) + 0.5 * sine(f * 1.58, n)) * np.exp(-t / decay)


def tom(f=110, decay=0.35):
    n = int(decay * 6 * SR)
    t = secs(n)
    return sine_fm(f * (1 + 0.6 * np.exp(-t / 0.04))) * np.exp(-t / decay)


# ---------------------------------------------------------------- strumenti
def pad(freqs, dur, rng, a=2.0, r=3.0, detune=12, voices=3, fc=1800, wave="saw"):
    env = adsr(dur, a, 0.5, 0.85, r)
    n = len(env)
    out = np.zeros((2, n))
    for f in freqs:
        for v in range(voices):
            cents = (v - (voices - 1) / 2) * detune * 2 / max(1, voices - 1) if voices > 1 else 0
            ff = f * 2 ** (cents / 1200)
            if wave == "saw":
                osc = saw(ff, n, rng.random())
            elif wave == "tri":
                osc = 2 * np.abs(saw(ff, n, rng.random())) - 1
            else:
                osc = sine(ff, n, rng.random())
            out[v % 2] += osc
    out = np.array([lp(c, fc, 2) for c in out]) * env / (len(freqs) * voices) * 2
    return out


def epiano(f, dur, vel=1.0, bright=1.0):
    n = int((dur + 1.2) * SR)
    t = secs(n)
    idx = (2.2 * bright * vel) * np.exp(-t / 0.35) + 0.2
    mod = sine(f, n) * idx
    car = np.sin(2 * np.pi * f * t + mod)
    tine = np.sin(2 * np.pi * f * 14 * t) * np.exp(-t / 0.012) * 0.25 * vel * bright
    e2 = adsr(dur, 0.002, 0.1, 1.0, 1.2)
    e2 = np.pad(e2, (0, max(0, n - len(e2))))[:n]
    return (car + tine) * np.exp(-t / 1.8) * e2 * vel


def bell(f, n_sec=4.0, ratio=3.5, idx=4.0, decay=1.8, vel=1.0):
    n = int(n_sec * SR)
    t = secs(n)
    i = idx * np.exp(-t / (decay * 0.4))
    y = np.sin(2 * np.pi * f * t + i * np.sin(2 * np.pi * f * ratio * t))
    return y * np.exp(-t / decay) * np.minimum(t / 0.002, 1) * vel


def marimba(f, vel=1.0, decay=0.45):
    n = int(decay * 6 * SR)
    t = secs(n)
    y = sine(f, n) * np.exp(-t / decay) + 0.35 * sine(f * 3.93, n) * np.exp(-t / (decay * 0.12)) \
        + 0.12 * sine(f * 9.2, n) * np.exp(-t / 0.012)
    return y * np.minimum(t / 0.001, 1) * vel


def pluck(f, dur, rng, bright=4000, damp=0.996, vel=1.0):
    """Karplus-Strong vettoriale (chitarra / kalimba)."""
    n = int(dur * SR)
    N = max(2, int(round(SR / f)))
    y = np.zeros(n + N + 1)
    y[: N + 1] = lp(rng.uniform(-1, 1, N + 1), bright, 1)
    s = N + 1
    while s < len(y):
        e = min(s + N, len(y))
        k = e - s
        y[s:e] = damp * 0.5 * (y[s - N:s - N + k] + y[s - N - 1:s - N - 1 + k])
        s = e
    y = y[N + 1:N + 1 + n]
    fade = np.ones(n)
    fl = min(n, int(0.05 * SR))
    fade[-fl:] = np.linspace(1, 0, fl)
    return y * fade * vel


def piano(f, dur, rng, vel=1.0):
    n = int((dur + 1.5) * SR)
    t = secs(n)
    B = 0.0004
    y = np.zeros(n)
    nh = int(min(12, (SR * 0.45) / f))
    for k in range(1, nh + 1):
        fk = k * f * np.sqrt(1 + B * k * k)
        dec = 2.8 / (1 + 0.45 * (k - 1)) * (220 / max(f, 60)) ** 0.35
        y += sine(fk, n, rng.random()) * np.exp(-t / dec) / k ** (1.4 - 0.4 * vel)
    ham = lp(rng.standard_normal(n), 3000) * np.exp(-t / 0.004) * 0.15
    rel = adsr(dur, 0.001, 0.05, 1.0, 0.35)
    rel = np.pad(rel, (0, max(0, n - len(rel))))[:n]
    return (y + ham) * rel * vel


def bass(f, dur, kind="sine", fc=900, drv=1.3):
    env = adsr(dur, 0.005, 0.08, 0.85, 0.06)
    n = len(env)
    if kind == "sine":
        y = sine(f, n) + 0.25 * sine(2 * f, n)
    elif kind == "saw":
        y = lp(saw(f, n), fc, 2)
    else:
        y = lp(pulse(f, n, 0.5), fc, 2)
    return drive(y * env, drv)


def reese(f, dur, rng):
    env = adsr(dur, 0.01, 0.1, 0.9, 0.08)
    n = len(env)
    y = saw(f * 2 ** (-14 / 1200), n, rng.random()) + saw(f * 2 ** (14 / 1200), n, rng.random()) + 0.6 * sine(f / 2, n)
    return y * env


def whistle(f, dur, rng, vib=5.2):
    env = adsr(dur, 0.08, 0.1, 0.8, 0.25)
    n = len(env)
    t = secs(n)
    depth = 0.012 * np.minimum(t / 0.5, 1)
    fr = f * (1 + depth * np.sin(2 * np.pi * vib * t))
    y = sine_fm(fr) + 0.04 * bp(rng.standard_normal(n), f * 0.8, f * 1.6)
    return y * env


def strings(freqs, dur, rng, a=1.8, r=2.5, fc=2600):
    env = adsr(dur, a, 0.4, 0.9, r)
    n = len(env)
    t = secs(n)
    out = np.zeros((2, n))
    for f in freqs:
        for v in range(6):
            vib = 1 + 0.004 * np.sin(2 * np.pi * (4.6 + 0.4 * rng.random()) * t + rng.random() * 6)
            det = 2 ** (rng.uniform(-9, 9) / 1200)
            ph = np.cumsum(f * det * vib) / SR
            x = 2 * (ph + rng.random()) % 2 - 1
            out[v % 2] += x
    out = np.array([hp(lp(c, fc, 2), 110) for c in out]) * env / (len(freqs) * 3)
    return out


def crackle(n, rng, density=6, hiss=0.02):
    y = np.zeros(n)
    k = rng.poisson(density * n / SR)
    idx = rng.integers(0, n, k)
    y[idx] = rng.uniform(-1, 1, k) * rng.uniform(0.2, 1, k)
    y = bp(y, 800, 6000) + lp(rng.standard_normal(n), 3000) * hiss
    return y


# ---------------------------------------------------------------- master
def master(mix, buses_fx, lufs_hint=0.9, hpf=28, fade_in=2.5, fade_out=7.0, glue=1.25):
    """buses_fx: dict bus -> (gain, fn(st)->st or None)."""
    out = np.zeros((2, mix.N))
    for name, st in mix.bus.items():
        g, fn = buses_fx.get(name, (1.0, None))
        out += (fn(st) if fn else st) * g
    out = np.array([hp(c, hpf, 2) for c in out])
    pk = np.max(np.abs(out)) + 1e-9
    out = out / pk * 0.95
    out = np.tanh(out * glue) / np.tanh(glue)
    n = mix.N
    fi = int(fade_in * SR)
    fo = int(fade_out * SR)
    out[:, :fi] *= np.linspace(0, 1, fi) ** 2
    out[:, n - fo:] *= np.linspace(1, 0, fo) ** 1.5
    out = out / (np.max(np.abs(out)) + 1e-9) * lufs_hint
    return out.astype(np.float32)
