"""I 12 brani di Kansei Radio, ognuno con un carattere diverso."""
import numpy as np
from synth import *  # noqa: F401,F403

MAJ = [0, 2, 4, 5, 7, 9, 11]
MIN = [0, 2, 3, 5, 7, 8, 10]


def bars_for(target, bpm, beats=4):
    return int(round(target / (beats * 60 / bpm)))


def in_rng(b, *ranges):
    return any(a <= b < c for a, c in ranges)


# =========================================================== 01 SUPERFICI
def t01(seed=101):
    """Ambient: pad lenti, campane di vetro, vento. Nessuna batteria."""
    bpm, B = 60, 4.0
    nb = 56
    m = Mix(nb * B + 6, seed)
    r = m.rng
    E = 40  # E2
    prog = [  # Mi lidio
        [E, E + 7, E + 11, E + 16, E + 18, E + 23],          # Emaj9
        [E + 2, E + 9, E + 14, E + 18, E + 21, E + 25],      # F#/...
        [E - 3, E + 9, E + 12, E + 16, E + 19, E + 23],      # C#m9
        [E - 5, E + 7, E + 11, E + 14, E + 18, E + 21],      # B6/9
    ]
    for i in range(0, nb, 4):
        ch = prog[(i // 4) % 4]
        m.add("pad", i * B, pad(mtof(ch[1:]), 4 * B + 1, r, a=4.5, r=5, detune=9, voices=2, fc=1400, wave="tri"), g=0.9)
        m.add("sub", i * B, sine(mtof(ch[0] - 12), int((4 * B + 2) * SR)) * adsr(4 * B, 3, 1, 1, 2)[: int((4 * B + 2) * SR)], g=0.5)
    scale = [E + x for x in [0, 2, 4, 6, 7, 9, 11]]
    t = 8 * B
    while t < (nb - 4) * B:
        dens = 1.2 if 20 * B < t < 40 * B else 2.6
        note = mtof(r.choice(scale) + 24 + 12 * r.integers(0, 2))
        m.add("bell", t, bell(note, 6, ratio=r.choice([2.0, 3.0, 3.5]), idx=1.5, decay=2.4, vel=r.uniform(0.3, 0.7)), pan=r.uniform(-0.8, 0.8))
        t += r.exponential(dens) + 0.4
    n = m.N
    wind = sweep_lp(r.standard_normal(n) * 0.25, lambda s: 500 + 400 * np.sin(2 * np.pi * s / 37), q=3)
    m.add("wind", 0, np.array([wind, np.roll(wind, 900)]), g=0.25)
    ir = make_ir(6.5, 5000, seed)
    return master(m, {
        "pad": (1.0, lambda s: s + 0.5 * reverb(s, ir)),
        "bell": (0.55, lambda s: 0.5 * s + reverb(s, ir) * 1.2),
        "sub": (0.6, None),
        "wind": (1.0, None),
    }, glue=1.05)


# =========================================================== 02 PORTA SUL FUTURO
def t02(seed=202):
    """Synthwave: arpeggio a sedicesimi che si apre, cassa dritta, rullante largo."""
    bpm = 118
    b = 60 / bpm
    B = 4 * b
    nb = 120
    m = Mix(nb * B + 5, seed)
    r = m.rng
    A = 57
    prog = [[A, A + 3, A + 7], [A - 4, A, A + 3], [A + 3, A + 7, A + 10], [A - 2, A + 2, A + 5]]  # Am F C G
    drums_on = lambda i: in_rng(i, (8, 56), (72, 112))
    kicks = []
    for i in range(nb):
        ch = prog[(i // 2) % 4]
        t0 = i * B
        # arpeggio 16esimi
        notes = [ch[0], ch[1], ch[2], ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[0] + 12, ch[2]]
        for s in range(16):
            f = mtof(notes[s % 8])
            env = adsr(b / 4 * 0.7, 0.002, 0.08, 0.4, 0.05)
            m.add("arp", t0 + s * b / 4, saw(f, len(env), 0) * env * (0.9 if s % 4 == 0 else 0.6), pan=0.25 * np.sin(s))
        if drums_on(i) or i >= 4:
            for s in range(8):
                if i < 8 and s % 2:
                    continue
                m.add("bass", t0 + s * b / 2, bass(mtof(ch[0] - 24 + (12 if s % 2 else 0)), b / 2 * 0.8, "saw", fc=650), g=0.7)
        if i % 2 == 0:
            m.add("pad", t0, pad(mtof([c + 12 for c in ch] + [ch[0] + 24]), 2 * B, r, a=0.6, r=1.2, detune=14, voices=4, fc=2200), g=0.6)
        if drums_on(i):
            for q in range(4):
                m.add("kick", t0 + q * b, kick(r, tone=50, punch=170, decay=0.28))
                kicks.append(t0 + q * b)
                m.add("hat", t0 + q * b + b / 2, hat(r, 0.07), pan=0.2, g=0.35)
            if i >= 16:
                for q in (1, 3):
                    m.add("snare", t0 + q * b, snare(r, tone=200, ndec=0.18))
        if in_rng(i, (24, 56), (80, 112)):
            motif = [(0, 7, 1.5), (1.5, 5, 0.5), (2, 3, 1), (3, 0, 1)]
            for (bt, deg, du) in motif:
                if i % 2 == 1 and bt > 2:
                    continue
                mn = ch[0] + 12 + [0, 2, 3, 5, 7, 8, 10, 12][deg % 8] if deg < 8 else ch[0] + 24
                env = adsr(du * b * 0.9, 0.01, 0.2, 0.7, 0.2)
                m.add("lead", t0 + bt * b, lp(pulse(mtof(mn), len(env), 0.3), 3200) * env, g=0.5)
    n = m.N

    def arp_fc(s):
        bar = s / B
        base = 300 if bar < 8 else 700 if bar < 24 else 1600 if bar < 56 else 500 if bar < 72 else 3800 if bar < 112 else 900
        return base * (1 + 0.6 * np.sin(2 * np.pi * s / (8 * B)) ** 2)
    m.bus["arp"] = np.array([sweep_lp(c, arp_fc, q=2.2) for c in m.get("arp")])
    dk = duck(n, kicks, 0.55, 0.15)
    ir = make_ir(2.4, 7000, seed)
    return master(m, {
        "arp": (0.45, lambda s: (s + 0.35 * pingpong(s, 0.75 * b, 0.45) + 0.3 * reverb(s, ir)) * dk),
        "pad": (0.5, lambda s: (s + 0.4 * reverb(s, ir)) * dk),
        "bass": (0.75, lambda s: s * dk),
        "kick": (0.9, None),
        "snare": (0.45, lambda s: s + 0.8 * reverb(s, ir)),
        "hat": (0.35, None),
        "lead": (0.45, lambda s: s + 0.4 * pingpong(s, 0.75 * b, 0.4) + 0.4 * reverb(s, ir)),
    })


# =========================================================== 03 LUCE LENTA
def t03(seed=303):
    """Piano elettrico solo, rarefatto, con un velo d'archi."""
    bpm = 64
    b = 60 / bpm
    B = 4 * b
    nb = 56
    m = Mix(nb * B + 6, seed)
    r = m.rng
    Db = 49
    prog = [
        (Db - 12, [Db, Db + 4, Db + 7, Db + 11, Db + 14]),       # Dbmaj9
        (Db - 3 - 12, [Db - 3, Db, Db + 4, Db + 8, Db + 11]),    # Bbm9
        (Db - 7 - 12, [Db - 7 + 12, Db - 3 + 12, Db + 12, Db + 5 + 12]),  # Gbmaj7#11
        (Db - 5 - 12, [Db - 5 + 12, Db + 12, Db + 2 + 12, Db + 7 + 12]),  # Absus
    ]
    penta = [Db + x for x in [0, 2, 4, 7, 9]]
    for i in range(nb):
        root, ch = prog[(i // 2) % 4]
        t0 = i * B
        if i % 2 == 0:
            m.add("ep", t0, epiano(mtof(root), 2 * B * 0.9, 0.7, 0.6), g=0.6)
            for k, nn in enumerate(ch):
                m.add("ep", t0 + 0.035 * k + r.uniform(0, 0.01), epiano(mtof(nn), 2 * B * 0.85, 0.45, 0.8), pan=-0.3 + 0.15 * k)
        else:
            if r.random() < 0.6:
                for k, nn in enumerate(ch[1:4]):
                    m.add("ep", t0 + 2 * b + 0.03 * k, epiano(mtof(nn), B, 0.3, 0.7), pan=0.2)
        if in_rng(i, (4, 24), (28, 52)):
            t = t0
            while t < t0 + B:
                du = r.choice([b, 1.5 * b, 2 * b, 0.5 * b], p=[0.35, 0.25, 0.25, 0.15])
                if r.random() < 0.72:
                    nn = r.choice(penta) + 12 * r.choice([1, 2], p=[0.7, 0.3])
                    m.add("ep", t, epiano(mtof(nn), du * 0.9, r.uniform(0.45, 0.8), 1.1), pan=0.25)
                t += du
        if in_rng(i, (16, 44)) and i % 2 == 0:
            m.add("str", t0, strings(mtof([c for c in ch[:3]]), 2 * B, r, a=3, r=4, fc=1800), g=0.35)
    hiss = lp(r.standard_normal(m.N), 4000) * 0.012
    m.add("hiss", 0, hiss)
    ir = make_ir(3.0, 6000, seed)
    return master(m, {
        "ep": (1.0, lambda s: lp_st(s, 6500) + 0.35 * reverb(s, ir)),
        "str": (0.6, lambda s: s + 0.6 * reverb(s, ir)),
        "hiss": (1.0, None),
    }, glue=1.1)


def lp_st(s, fc):
    return np.array([lp(c, fc) for c in s])


# =========================================================== 04 SALA 3
def t04(seed=404):
    """Techno minimale con basso acid risonante."""
    bpm = 124
    b = 60 / bpm
    B = 4 * b
    nb = 128
    m = Mix(nb * B + 4, seed)
    r = m.rng
    F = 29  # F1
    pat = [(0, 0, 1), (2, 12, 0), (3, 0, 0), (4, 15, 1), (6, 0, 0), (7, 10, 1), (8, 0, 0), (10, 12, 1),
           (11, 3, 0), (12, 0, 1), (14, 7, 0), (15, 12, 1)]
    pat2 = [(0, 0, 1), (1, 0, 0), (3, 12, 1), (4, 3, 0), (6, 15, 1), (8, 0, 1), (9, 0, 0), (11, 10, 1), (12, 12, 0), (14, 3, 1)]
    kicks = []

    def acid_base(bar):
        x = bar / nb
        return 260 + 1500 * (0.5 - 0.5 * np.cos(2 * np.pi * min(x * 1.6, 1.0) ** 1.2)) if bar < 64 else 400 + 1800 * ((bar - 64) / 64) ** 0.8

    for i in range(nb):
        t0 = i * B
        brk = in_rng(i, (64, 80))
        if not brk:
            for q in range(4):
                m.add("kick", t0 + q * b, kick(r, tone=46, punch=190, decay=0.24, click=0.5, drv=2.4))
                kicks.append(t0 + q * b)
        if i >= 16 and not brk:
            for q in range(4):
                m.add("ohat", t0 + q * b + b / 2, hat(r, 0.09, 6000), pan=0.15)
        if i >= 8:
            for s in range(16):
                acc = 1.0 if s % 4 == 2 else 0.45
                m.add("hat", t0 + s * b / 4, hat(r, 0.018, 9000) * acc, pan=-0.25)
        if i >= 32 and not brk:
            for q in (1, 3):
                m.add("clap", t0 + q * b, clap(r))
        if i >= 24 and i % 2 == 1:
            for s in (3, 7, 10, 14):
                m.add("rim", t0 + s * b / 4, rim(r, 1500), pan=0.4, g=0.5)
        if i >= 4:
            p = pat if (i // 8) % 2 == 0 else pat2
            base = acid_base(i)
            for (s, semi, accent) in p:
                f = mtof(F + 12 + semi)
                du = b / 4 * (1.6 if accent else 0.9)
                env = adsr(du, 0.002, 0.05, 0.8, 0.03)
                x = saw(f, len(env)) * env
                pk = base * (3.2 if accent else 1.6)
                y = sweep_lp(x, lambda tt, pk=pk, base=base: base + pk * np.exp(-tt / 0.07), q=7 if accent else 4, block=128)
                m.add("acid", t0 + s * b / 4, drive(y * 0.8, 2.0), g=0.9 if accent else 0.7)
        if in_rng(i, (48, 64), (96, 120)) and i % 2 == 0:
            st = pad(mtof([F + 24, F + 27, F + 31, F + 34]), b * 0.35, r, a=0.003, r=0.08, voices=2, fc=2400)
            m.add("stab", t0 + 3.5 * b, st)
    dk = duck(m.N, kicks, 0.5, 0.12)
    ir = make_ir(1.6, 6000, seed)
    return master(m, {
        "kick": (1.0, None),
        "ohat": (0.28, None),
        "hat": (0.22, None),
        "clap": (0.4, lambda s: s + 0.5 * reverb(s, ir)),
        "rim": (0.3, lambda s: s + 0.4 * pingpong(s, 0.75 * b, 0.4)),
        "acid": (0.5, lambda s: s * dk + 0.15 * pingpong(s, 0.75 * b, 0.35, lpf=2500)),
        "stab": (0.4, lambda s: s + 0.7 * pingpong(s, 0.75 * b, 0.55) + 0.5 * reverb(s, ir)),
    }, glue=1.4)


# =========================================================== 05 ATELIER
def t05(seed=505):
    """Marimba e kalimba in poliritmo 3 contro 4, percussioni di legno."""
    bpm = 96
    b = 60 / bpm
    B = 4 * b
    nb = 88
    m = Mix(nb * B + 5, seed)
    r = m.rng
    G = 55
    chords = [[G, G + 4, G + 7, G + 14], [G - 3, G + 4, G + 7, G + 12], [G - 7, G - 3, G, G + 9], [G - 5, G - 1, G + 2, G + 9]]
    for i in range(nb):
        ch = chords[(i // 4) % 4]
        t0 = i * B
        if True:
            seq1 = [ch[0] + 12, ch[2] + 12, ch[1] + 12]
            for s in range(8):
                m.add("mar", t0 + s * b / 2, marimba(mtof(seq1[(i * 8 + s) % 3]), 0.75 if s % 2 == 0 else 0.55), pan=-0.35)
        if in_rng(i, (8, 84)):
            seq2 = [ch[3] + 12, ch[1] + 24, ch[2] + 12, ch[0] + 24]
            for k in range(6):  # terzine di semiminima: 6 per battuta
                m.add("mar", t0 + k * (2 * b / 3), marimba(mtof(seq2[(i * 6 + k) % 4]), 0.5, decay=0.3), pan=0.4)
        if in_rng(i, (16, 48), (56, 84)):
            m.add("bass", t0, pluck(mtof(ch[0] - 24), b * 1.4, r, bright=900, damp=0.997), g=0.9)
            m.add("bass", t0 + 2.5 * b, pluck(mtof(ch[0] - 24 + (7 if i % 2 else 12)), b, r, bright=900, damp=0.995), g=0.7)
            for q in (0, 2):
                m.add("perc", t0 + q * b, tom(70, 0.25), g=0.6)
            for s in (3, 6, 11, 14):
                m.add("wood", t0 + s * b / 4, woodblock(r.choice([780, 980, 1170])), pan=r.uniform(-0.6, 0.6))
            for s in range(16):
                m.add("shk", t0 + s * b / 4, shaker(r, 0.04) * (0.8 if s % 2 else 0.4), pan=0.5)
        if in_rng(i, (32, 48), (56, 80)) and i % 2 == 0:
            phrase = r.choice([[0, 2, 4, 7], [7, 4, 2, 4], [9, 7, 4, 2], [4, 7, 9, 12]])
            times = [0, 0.75, 1.5, 3]
            for tt, deg in zip(times, phrase):
                m.add("kal", t0 + tt * b, pluck(mtof(G + 24 + deg), 1.6, r, bright=6000, damp=0.993), pan=0.15)
    ir = make_ir(1.8, 6500, seed)
    return master(m, {
        "mar": (0.55, lambda s: s + 0.3 * reverb(s, ir)),
        "bass": (0.6, None),
        "perc": (0.45, None),
        "wood": (0.25, lambda s: s + 0.3 * reverb(s, ir)),
        "shk": (0.12, None),
        "kal": (0.5, lambda s: s + 0.35 * pingpong(s, 0.75 * b, 0.4) + 0.4 * reverb(s, ir)),
    })


# =========================================================== 06 RIFLESSO
def t06(seed=606):
    """Dub techno: accordi filtrati con eco lunghe, sub profondo."""
    bpm = 112
    b = 60 / bpm
    B = 4 * b
    nb = 124
    m = Mix(nb * B + 8, seed)
    r = m.rng
    C = 48
    cm9 = [C, C + 3, C + 7, C + 10, C + 14]
    ab = [C - 4, C, C + 3, C + 7, C + 11]
    kicks = []
    for i in range(nb):
        t0 = i * B
        brk = in_rng(i, (64, 76))
        if not brk and i < 116:
            for q in range(4):
                m.add("kick", t0 + q * b, kick(r, tone=44, punch=120, decay=0.38, click=0.08, drv=1.4))
                kicks.append(t0 + q * b)
        if in_rng(i, (24, 64), (76, 112)):
            for q in range(4):
                m.add("hat", t0 + q * b + b / 2 + 0.012, hat(r, 0.05, 8000) * r.uniform(0.6, 1), pan=0.3)
            for s in range(16):
                if r.random() < 0.12:
                    m.add("rim", t0 + s * b / 4, rim(r, 1300, 0.012), pan=-0.4, g=0.5)
        if i >= 16:
            ch = ab if (i // 4) % 4 == 3 else cm9
            for s in [2, 7, 10, 14] if i % 2 == 0 else [2, 10, 13]:
                st = pad(mtof(ch), b * 0.22, r, a=0.004, r=0.12, voices=2, fc=9000)
                m.add("stab", t0 + s * b / 4, st)
        if in_rng(i, (32, 64), (76, 116)):
            m.add("sub", t0, sine(mtof(C - 24), int(1.4 * b * SR)) * adsr(1.3 * b, 0.01, 0.1, 0.9, 0.08)[: int(1.4 * b * SR)])
            m.add("sub", t0 + 2.5 * b, sine(mtof(C - 24), int(1.2 * b * SR)) * adsr(1.1 * b, 0.01, 0.1, 0.9, 0.08)[: int(1.2 * b * SR)])
    stab = m.get("stab")
    m.bus["stab"] = np.array([sweep_lp(c, lambda s: 350 + 1600 * (0.5 - 0.5 * np.cos(2 * np.pi * s / (32 * B))), q=1.6) for c in stab])
    m.add("hiss", 0, lp(r.standard_normal(m.N), 6000) * 0.02)
    dk = duck(m.N, kicks, 0.45, 0.2)
    ir = make_ir(3.5, 4500, seed)
    return master(m, {
        "kick": (1.0, None),
        "hat": (0.2, None),
        "rim": (0.25, lambda s: s + 0.6 * pingpong(s, 0.75 * b, 0.5)),
        "stab": (0.5, lambda s: (s + 0.9 * pingpong(s, 0.75 * b, 0.62, taps=12, lpf=2200) + 0.5 * reverb(s, ir)) * dk),
        "sub": (0.8, lambda s: s * dk),
        "hiss": (1.0, None),
    }, glue=1.3)


# =========================================================== 07 SOGLIA
def t07(seed=707):
    """Drone scuro, battito cardiaco, colpi metallici in un riverbero enorme."""
    bpm = 70
    b = 60 / bpm
    B = 4 * b
    nb = 68
    m = Mix(nb * B + 8, seed)
    r = m.rng
    D = 26  # D1
    n = m.N
    dr = np.zeros(n)
    for semi, g in [(0, 1.0), (12, 0.7), (19, 0.5), (13, 0.25)]:
        dr += saw(mtof(D + semi) * (1 + 0.0015 * g), n, r.random()) * g
    dr = sweep_lp(dr * 0.3, lambda s: 160 + 650 * (0.5 - 0.5 * np.cos(2 * np.pi * s / 48)) * (1.4 if 28 * B < s < 56 * B else 1), q=1.8)
    m.add("drone", 0, np.array([dr, np.roll(dr, 1300)]))
    for i in range(nb):
        t0 = i * B
        if in_rng(i, (12, 60)):
            per_bar = 4 if not in_rng(i, (36, 56)) else 8
            for q in range(per_bar):
                tq = t0 + q * B / per_bar
                m.add("heart", tq, kick(r, tone=42, punch=80, decay=0.16, click=0.02, drv=1.2), g=0.9)
                m.add("heart", tq + 0.24, kick(r, tone=40, punch=70, decay=0.13, click=0.0, drv=1.1), g=0.55)
        if in_rng(i, (12, 64)) and i % 2 == 0:
            f = mtof(D + 24 + r.choice([0, 1, 7, 10]))
            m.add("metal", t0 + r.choice([0, 1.5]) * b, bell(f, 7, ratio=1.414, idx=6, decay=2.5, vel=0.7), pan=r.uniform(-0.7, 0.7))
        if i % 4 == 0 and i > 4:
            m.add("piano", t0 + 3 * b, piano(mtof(D + 12 + r.choice([0, 1, -2])), 2 * B, r, vel=0.5))
    for s0 in (20, 28, 48):
        L = int(8 * B * SR)
        t = secs(L)
        sw = sweep_lp(r.standard_normal(L), lambda s: 200 + 3500 * (s / (8 * B)) ** 2, q=2) * (t / t[-1]) ** 2
        m.add("swell", s0 * B, np.array([sw, -sw]), g=0.18)
    ir = make_ir(8.0, 3500, seed)
    return master(m, {
        "drone": (0.55, lambda s: s + 0.3 * reverb(s, ir)),
        "heart": (0.9, lambda s: lp_st(s, 900) + 0.2 * reverb(s, ir)),
        "metal": (0.35, lambda s: 0.3 * s + 1.3 * reverb(s, ir)),
        "piano": (0.5, lambda s: 0.5 * s + reverb(s, ir)),
        "swell": (1.0, lambda s: s + 0.5 * reverb(s, ir)),
    }, glue=1.2)


# =========================================================== 08 CAMPO APERTO
def t08(seed=808):
    """Chitarra pizzicata, shaker, melodia fischiata. Luminoso."""
    bpm = 88
    b = 60 / bpm
    B = 4 * b
    nb = 80
    m = Mix(nb * B + 5, seed)
    r = m.rng
    D = 50
    prog = [[D - 12, D, D + 4, D + 7, D + 12], [D - 7, D - 5, D - 1, D + 2, D + 7], [D - 13, D - 1, D + 2, D + 6, D + 11], [D - 17, D - 3, D + 1, D + 4, D + 9]]
    melody = [(0, 9, 1), (1, 7, 0.5), (1.5, 4, 1.5), (4, 2, 1), (5, 4, 0.5), (5.5, 7, 2.5), (8, 9, 1), (9, 12, 1), (10, 9, 1), (11, 7, 1),
              (12, 4, 2), (14, 2, 2)]
    for i in range(nb):
        ch = prog[(i // 2) % 4]
        t0 = i * B
        order = [0, 2, 3, 4, 1, 3, 2, 4]
        strum = in_rng(i, (16, 40), (48, 72)) and i % 2 == 0
        for s in range(8):
            if strum and s == 0:
                for k, nn in enumerate(ch):
                    m.add("gtr", t0 + 0.018 * k, pluck(mtof(nn), 2.2, r, bright=3200, damp=0.9965), pan=-0.2 + 0.1 * k, g=0.5)
                continue
            nn = ch[order[s]]
            m.add("gtr", t0 + s * b / 2 + r.uniform(0, 0.01), pluck(mtof(nn), 1.8, r, bright=3800, damp=0.997, vel=0.85 if s % 2 == 0 else 0.6),
                  pan=-0.35 + 0.1 * (order[s]))
        if in_rng(i, (8, 76)):
            for s in range(8):
                m.add("shk", t0 + s * b / 2, shaker(r, 0.05) * (0.9 if s % 2 else 0.45), pan=0.45)
        if in_rng(i, (12, 40), (48, 76)):
            for q in (0, 2):
                m.add("kick", t0 + q * b, kick(r, tone=55, punch=110, decay=0.22, click=0.05, drv=1.2))
            m.add("bass", t0, bass(mtof(ch[0] - 12), b * 1.6, "sine"), g=0.8)
            m.add("bass", t0 + 2 * b, bass(mtof(ch[0] - 12), b * 1.4, "sine"), g=0.7)
            m.add("bass", t0 + 3.5 * b, bass(mtof(ch[0] - 10), b * 0.4, "sine"), g=0.5)
        if in_rng(i, (16, 40), (48, 76)):
            for q in (1, 3):
                m.add("snap", t0 + q * b, clap(r, 0.06), g=0.6, pan=-0.1)
        if in_rng(i, (24, 40), (56, 72)) and i % 4 == 0:
            for bt, deg, du in melody:
                nn = D + 12 + deg
                m.add("lead", t0 + bt * b, whistle(mtof(nn), du * b * 0.92, r), pan=0.1)
    ir = make_ir(2.2, 7000, seed)
    return master(m, {
        "gtr": (0.7, lambda s: s + 0.3 * reverb(s, ir)),
        "shk": (0.14, None),
        "kick": (0.6, None),
        "bass": (0.5, None),
        "snap": (0.25, lambda s: s + 0.4 * reverb(s, ir)),
        "lead": (0.32, lambda s: s + 0.3 * pingpong(s, 0.75 * b, 0.35) + 0.5 * reverb(s, ir)),
    })


# =========================================================== 09 NOTTURNO
def t09(seed=909):
    """Lo-fi hip hop: swing, Rhodes caldo, vinile."""
    bpm = 78
    b = 60 / bpm
    B = 4 * b
    nb = 72
    m = Mix(nb * B + 5, seed)
    r = m.rng
    Eb = 51
    prog = [
        (Eb - 12, [Eb, Eb + 3, Eb + 7, Eb + 10, Eb + 14]),        # Ebm9
        (Eb - 7 - 12, [Eb - 7 + 12, Eb - 7 + 16, Eb - 7 + 22, Eb - 7 + 26]),  # Ab13-ish
        (Eb - 2 - 12, [Eb - 2 + 12, Eb + 2 + 12, Eb + 5 + 12, Eb + 9 + 12]),  # Dbmaj7
        (Eb - 5 - 12, [Eb - 5 + 12, Eb - 2 + 12, Eb + 2 + 12, Eb + 5 + 12]),  # Bbm7
    ]
    sw = 0.62  # swing

    def st(beat):  # posizione con swing sugli ottavi
        whole = np.floor(beat)
        frac = beat - whole
        return (whole + (sw if abs(frac - 0.5) < 1e-6 else frac)) * b

    for i in range(nb):
        root, ch = prog[(i // 2) % 4]
        t0 = i * B
        comp = [(0, 1.4, 0.7), (1.5, 0.4, 0.45), (2.5, 1.2, 0.6)] if i % 2 == 0 else [(0.5, 1.0, 0.55), (3, 0.8, 0.5)]
        for bt, du, v in comp:
            for k, nn in enumerate(ch):
                m.add("rh", t0 + st(bt) + 0.012 * k, epiano(mtof(nn), du * b, v * 0.8, 0.7), pan=-0.25 + 0.12 * k)
        drums = in_rng(i, (4, 36), (44, 70))
        if drums:
            for kb in ([0, 2.5] if i % 2 == 0 else [0, 1.75, 2.5]):
                m.add("kick", t0 + st(kb), kick(r, tone=52, punch=120, decay=0.26, click=0.1, drv=1.6))
            for q in (1, 3):
                m.add("snr", t0 + q * b, snare(r, tone=180, ndec=0.13, bright=4500), g=0.9)
            if r.random() < 0.5:
                m.add("snr", t0 + st(3.5), snare(r, tone=190, ndec=0.05, bright=4000), g=0.22)
            for e in range(8):
                m.add("hat", t0 + st(e / 2), hat(r, 0.03, 6500) * (0.9 if e % 2 == 0 else 0.5) * r.uniform(0.75, 1), pan=0.3)
        if in_rng(i, (4, 70)):
            line = [(0, 0, 1.2), (1.75, 0, 0.4), (2.5, 7 if i % 2 else 12, 0.8), (3.5, 10, 0.4)]
            for bt, semi, du in line:
                m.add("bass", t0 + st(bt), bass(mtof(root - 12 + semi), du * b, "sine", drv=1.6), g=0.9)
        if in_rng(i, (48, 68)) and i % 4 == 0:
            riff = [(0, 14), (0.5, 15), (1, 19), (2.5, 17), (3, 15), (4.5, 14), (6, 10), (6.5, 12)]
            for bt, semi in riff:
                m.add("rh2", t0 + st(bt), epiano(mtof(Eb + semi), 0.6 * b, 0.55, 1.2), pan=0.3)
    m.add("vinyl", 0, crackle(m.N, r, density=9, hiss=0.03))
    ir = make_ir(1.8, 4500, seed)
    warm = lambda s: lp_st(s, 5200)
    lofi = lambda s: np.array([crush(c, 10, 2) for c in lp_st(s, 6000)])
    return master(m, {
        "rh": (0.55, lambda s: warm(s) + 0.3 * reverb(s, ir)),
        "rh2": (0.4, lambda s: warm(s) + 0.4 * pingpong(s, 0.75 * b, 0.4) + 0.4 * reverb(s, ir)),
        "kick": (0.85, lofi),
        "snr": (0.5, lambda s: lofi(s) + 0.25 * reverb(s, ir)),
        "hat": (0.18, lofi),
        "bass": (0.6, None),
        "vinyl": (0.35, None),
    }, glue=1.35)


# =========================================================== 10 MATERIA
def t10(seed=1010):
    """Glitch: ritmi spezzati, bleep, grani, basso sgranato, stutter."""
    bpm = 136
    b = 60 / bpm
    B = 4 * b
    nb = 112
    m = Mix(nb * B + 4, seed)
    r = m.rng
    A = 57
    penta = [0, 3, 5, 7, 10]
    pat = None
    for i in range(nb):
        t0 = i * B
        if i % 8 == 0:
            pr = np.random.default_rng(seed + i)
            pat = {
                "k": sorted(set([0] + list(pr.choice(range(1, 16), 3, replace=False)))),
                "s": sorted(set([4, 12] + list(pr.choice([6, 9, 11, 14, 15], 1)))),
                "h": [s for s in range(16) if pr.random() < 0.6],
                "bass": [(s, int(pr.choice(penta))) for s in sorted(pr.choice(range(16), 5, replace=False))],
            }
        drums = in_rng(i, (4, 40), (48, 106))
        if drums:
            for s in pat["k"]:
                m.add("drm", t0 + s * b / 4, kick(r, tone=50, punch=220, decay=0.15, click=0.6, drv=2.5))
            for s in pat["s"]:
                m.add("drm", t0 + s * b / 4, snare(r, tone=240, ndec=0.07, bright=9000) * 0.8)
            for s in pat["h"]:
                m.add("drm", t0 + s * b / 4, hat(r, r.choice([0.008, 0.015, 0.03]), 9000) * 0.5, pan=r.uniform(-0.5, 0.5))
        if in_rng(i, (12, 40), (48, 104)):
            for s, semi in pat["bass"]:
                f = mtof(A - 36 + semi)
                env = adsr(b / 4 * r.choice([1, 2, 3]), 0.002, 0.05, 0.9, 0.02)
                m.add("bass", t0 + s * b / 4, crush(pulse(f, len(env), 0.35) * env, 5, 6), g=0.6)
        if True:
            p = 0.22 if in_rng(i, (0, 8), (40, 48), (100, 112)) else 0.1
            for s in range(16):
                if r.random() < p:
                    f = mtof(A + 24 + r.choice(penta) + 12 * r.integers(0, 2))
                    L = int(r.choice([0.03, 0.06, 0.1]) * SR)
                    y = np.sin(2 * np.pi * f * secs(L) + 3 * np.sin(2 * np.pi * f * 2.01 * secs(L))) * expdec(L, 0.03)
                    m.add("blip", t0 + s * b / 4, y, pan=r.uniform(-0.9, 0.9), g=0.6)
        if True:
            dens = 30 if in_rng(i, (0, 8), (40, 48), (96, 112)) else 10
            for _ in range(r.poisson(dens)):
                L = int(r.uniform(0.02, 0.07) * SR)
                f = mtof(A + r.choice(penta) + 12 * r.integers(-1, 2))
                g = np.hanning(L) * (saw(f, L) if r.random() < 0.5 else sine(f, L))
                m.add("grain", t0 + r.uniform(0, B), g, pan=r.uniform(-1, 1), g=0.25)
        for _ in range(r.poisson(6)):
            m.add("click", t0 + r.uniform(0, B), hp(r.standard_normal(60), 3000) * 0.5, pan=r.uniform(-1, 1))
    drm = m.get("drm")
    for i in range(16, 100, 4):  # stutter: ripete una frazione di battuta
        if r.random() < 0.6:
            src = int((i * B + r.choice([2, 3]) * b) * SR)
            L = int(r.choice([b / 4, b / 8]) * SR)
            reps = r.choice([4, 6, 8])
            seg = drm[:, src:src + L].copy()
            for k in range(reps):
                a = src + k * L
                drm[:, a:a + L] = seg * (1 - 0.06 * k)
    m.bus["drm"] = drm
    ir = make_ir(1.2, 8000, seed)
    return master(m, {
        "drm": (0.8, None),
        "bass": (0.5, lambda s: lp_st(s, 2500)),
        "blip": (0.35, lambda s: s + 0.5 * pingpong(s, b / 4 * 3, 0.45, lpf=6000) + 0.3 * reverb(s, ir)),
        "grain": (0.3, lambda s: s + 0.6 * reverb(s, ir)),
        "click": (0.25, None),
    }, glue=1.4)


# =========================================================== 11 SEGNALE
def t11(seed=1111):
    """Drum & bass: break veloce, basso reese, bleep in morse."""
    bpm = 172
    b = 60 / bpm
    B = 4 * b
    nb = 168
    m = Mix(nb * B + 5, seed)
    r = m.rng
    Fs = 42  # F#2
    roots = [Fs - 24, Fs - 24, Fs - 28, Fs - 26]  # F#, F#, D, E
    morse = {"K": "-.-", "A": ".-", "N": "-.", "S": "...", "E": ".", "I": ".."}
    code = []
    for ch in "KANSEI":
        for sym in morse[ch]:
            code.append(1 if sym == "." else 3)
            code.append(-1)
        code.append(-2)
    code.append(-4)
    kicks = []
    for i in range(nb):
        t0 = i * B
        drums = in_rng(i, (16, 96), (112, 160))
        if drums:
            var = i % 4 == 3
            for kb in ([0, 2.5] if not var else [0, 1.75, 2.5]):
                m.add("kick", t0 + kb * b, kick(r, tone=50, punch=200, decay=0.18, click=0.5, drv=2.2))
                kicks.append(t0 + kb * b)
            for sb in (1, 3):
                m.add("snr", t0 + sb * b, snare(r, tone=210, ndec=0.12, bright=8000))
            for g_ in ([1.75, 3.25] if not var else [3.25, 3.5, 3.75]):
                m.add("snr", t0 + g_ * b, snare(r, tone=220, ndec=0.05, bright=7000), g=0.3)
            for s in range(8):
                m.add("hat", t0 + s * b / 2, hat(r, 0.025, 8000) * (0.9 if s % 2 else 0.5), pan=0.25)
        if in_rng(i, (32, 160)) and i % 2 == 0:
            root = roots[(i // 8) % 4]
            m.add("reese", t0, reese(mtof(root + 12), 2 * B * 0.96, r))
            se = adsr(2 * B * 0.96, 0.01, 0.1, 0.9, 0.04)
            m.add("sub", t0, sine(mtof(root), len(se)) * se)
        if i % 8 == 0:
            pm = mtof([Fs + 12, Fs + 15, Fs + 19, Fs + 22, Fs + 26])
            m.add("pad", t0, pad(pm, 8 * B, r, a=2.5, r=3, detune=10, voices=3, fc=1600), g=0.6)
    t = 0.0
    unit = b / 4
    k = 0
    while t < (nb - 4) * B:
        bar = t / B
        v = code[k % len(code)]
        if v > 0 and in_rng(int(bar), (0, 32), (64, 96), (128, 164)):
            L = int(v * unit * SR * 0.9)
            env = np.minimum(np.minimum(secs(L) / 0.004, 1), (L - np.arange(L)) / (0.004 * SR))
            m.add("morse", t, sine(1180, L) * env, pan=0.35)
        t += abs(v) * unit
        k += 1
    rs = m.get("reese")
    m.bus["reese"] = np.array([sweep_lp(c, lambda s: 260 + 700 * (0.5 - 0.5 * np.cos(2 * np.pi * s / (2 * B))), q=2.2) for c in rs])
    dk = duck(m.N, kicks, 0.5, 0.12)
    ir = make_ir(2.6, 6000, seed)
    return master(m, {
        "kick": (0.9, None),
        "snr": (0.5, lambda s: s + 0.3 * reverb(s, ir)),
        "hat": (0.2, None),
        "reese": (0.35, lambda s: drive(s * dk, 1.5)),
        "sub": (0.7, lambda s: s * dk),
        "pad": (0.35, lambda s: (s + 0.6 * reverb(s, ir)) * dk),
        "morse": (0.12, lambda s: s + 0.6 * pingpong(s, 3 * b / 4, 0.5, lpf=5000) + 0.4 * reverb(s, ir)),
    }, glue=1.4)


# =========================================================== 12 RITORNO
def t12(seed=1212):
    """Archi cinematici e pianoforte, crescendo e ritorno alla calma."""
    bpm = 72
    b = 60 / bpm
    B = 4 * b
    nb = 76
    m = Mix(nb * B + 8, seed)
    r = m.rng
    C = 48
    progA = [[C, C + 4, C + 7], [C - 3, C, C + 4], [C - 7, C - 3, C], [C - 5, C - 1, C + 2]]       # C Am F G
    progB = [[C - 7, C - 3, C, C + 4], [C - 5, C - 1, C + 2, C + 5], [C - 8, C - 5, C - 1, C + 2], [C - 3, C, C + 4, C + 7]]  # Fmaj7 G7 Em Am
    mel = [(0, 7), (1, 9), (2, 7), (3, 4), (4, 5), (5, 4), (6, 2), (7, 0)]

    def inten(i):
        if i < 16:
            return 0.25
        if i < 32:
            return 0.5
        if i < 44:
            return 0.7
        if i < 60:
            return 1.0
        return max(0.15, 1.0 - (i - 60) / 12)

    for i in range(nb):
        prog = progB if in_rng(i, (44, 60)) else progA
        ch = prog[(i // 2) % 4]
        t0 = i * B
        I = inten(i)
        if i < 16 or i >= 64:
            arp = [ch[0], ch[1] + 12, ch[2] + 12, ch[1] + 12] * 2
            for s, nn in enumerate(arp):
                m.add("pno", t0 + s * b / 2, piano(mtof(nn), b * 0.6, r, vel=0.55 if s % 4 else 0.7), pan=-0.1)
            if i % 2 == 0:
                m.add("pno", t0, piano(mtof(ch[0] - 12), 2 * B * 0.8, r, vel=0.6), pan=-0.3)
        if in_rng(i, (8, 72)) and i % 2 == 0:
            m.add("str", t0, strings(mtof([c + 12 for c in ch]), 2 * B, r, a=2.2 if I < 1 else 0.8, r=2.8, fc=1500 + 2500 * I), g=0.35 + 0.65 * I)
            m.add("lstr", t0, strings(mtof([ch[0] - 12, ch[0]]), 2 * B, r, a=2.0, r=2.5, fc=900), g=0.25 + 0.6 * I)
        if in_rng(i, (16, 60)) and i % 2 == 0:
            for bt, deg in mel[(i // 2) % 2 * 4:(i // 2) % 2 * 4 + 4]:
                nn = C + 12 + [0, 2, 4, 5, 7, 9, 11, 12][deg % 8]
                m.add("pno", t0 + bt * b * 2, piano(mtof(nn), 2 * b, r, vel=0.6 + 0.3 * I), pan=0.15)
        if in_rng(i, (44, 60)):
            m.add("timp", t0, tom(55, 0.9), g=0.9)
            if i % 2 == 1:
                for k in range(8):
                    m.add("timp", t0 + 3 * b + k * b / 8, tom(55, 0.3), g=0.15 + 0.08 * k)
    ir = make_ir(4.5, 5000, seed)
    return master(m, {
        "pno": (0.6, lambda s: s + 0.45 * reverb(s, ir)),
        "str": (0.5, lambda s: width(s, 1.4) + 0.6 * reverb(s, ir)),
        "lstr": (0.45, lambda s: s + 0.4 * reverb(s, ir)),
        "timp": (0.5, lambda s: lp_st(s, 1200) + 0.7 * reverb(s, ir)),
    }, glue=1.15)


TRACKS = {
    1: ("01-superfici", "Superfici", "Ambient · Mi lidio · 60 BPM", t01),
    2: ("02-porta-sul-futuro", "Porta sul futuro", "Synthwave · La minore · 118 BPM", t02),
    3: ("03-luce-lenta", "Luce lenta", "Piano elettrico · Re♭ maggiore · 64 BPM", t03),
    4: ("04-sala-3", "Sala 3", "Techno acid · Fa minore · 124 BPM", t04),
    5: ("05-atelier", "Atelier", "Marimba in poliritmo · Sol pentatonica · 96 BPM", t05),
    6: ("06-riflesso", "Riflesso", "Dub techno · Do minore · 112 BPM", t06),
    7: ("07-soglia", "Soglia", "Drone scuro · Re frigio · 70 BPM", t07),
    8: ("08-campo-aperto", "Campo aperto", "Chitarra e fischio · Re maggiore · 88 BPM", t08),
    9: ("09-notturno", "Notturno", "Lo-fi hip hop · Mi♭ minore · 78 BPM", t09),
    10: ("10-materia", "Materia", "Glitch · La minore · 136 BPM", t10),
    11: ("11-segnale", "Segnale", "Drum & bass · Fa# minore · 172 BPM", t11),
    12: ("12-ritorno", "Ritorno", "Archi e pianoforte · Do maggiore · 72 BPM", t12),
}
