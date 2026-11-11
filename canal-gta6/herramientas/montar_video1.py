import json, os, re, glob, subprocess, wave, random, sys, math
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ROOT = "/tmp/claude-0/-home-user-creative-velas/836e68d2-3ca3-5ed0-bd33-fc0cebbfc14f/scratchpad"
RS = f"{ROOT}/rs"
WK = f"{ROOT}/work/v1"
P = "/home/user/creative-velas/canal-gta6/video01"
os.makedirs(f"{WK}/shots", exist_ok=True)
FPS, F = 30, 0.35          # fps y duración del fundido entre planos
INTRO, OUTRO = 3.0, 5.5     # tarjetas de apertura y cierre
USE_EXT = os.environ.get("EXT") == "1"
random.seed(11)

tiempos = json.load(open(f"{P}/tiempos.json"))
with wave.open(f"{P}/narracion.wav") as w:
    NSR, NDUR = w.getframerate(), w.getnframes() / w.getframerate()
TOTAL = INTRO + NDUR + OUTRO

# ---------- reservas de imágenes ----------
imgs = {}
for f in sorted(glob.glob(f"{RS}/img/*.jpg")):
    if Image.open(f).size[0] < 1900: continue
    imgs[os.path.basename(f)] = f
def pool(pat): return [v for k, v in imgs.items() if re.match(pat, k)]
POOLS = {
    "vice": pool(r"Vice_City"), "jason": pool(r"Jason_Duval"), "lucia": pool(r"Lucia_Caminos"),
    "jl": pool(r"Jason_and_Lucia|Jason_Lucia_|desktop|hero|mediaDesktop|onlyInLeonida|outro"),
    "cal": pool(r"Cal_Hampton"), "boobie": pool(r"Boobie_Ike"), "dre": pool(r"DreQuan"), "raul": pool(r"Raul_"),
    "keys": pool(r"Leonida_Keys"), "gell": pool(r"Port_Gellhorn"), "amb": pool(r"Ambrosia"),
    "grass": pool(r"Grassrivers"), "kalaga": pool(r"Mount_Kalaga"), "dimez": pool(r"Real_Dimez"),
    "preload": pool(r"GTAVI_Pre_Load|pre-load"),
}
for k in ("dimez",):
    if not POOLS[k]: POOLS[k] = POOLS["vice"]
TRAILER = f"{RS}/vid/launch_trailer.mp4"
EXT = f"{RS}/vid/extended_look.mp4"
use_ext = USE_EXT and os.path.exists(EXT)
cursor_tr = [3.0]; cursor_ex = [60.0]
used = set()

def next_item(name):
    if name == "trailer":
        t = cursor_tr[0]; cursor_tr[0] = t + 3.4 if t + 3.4 < 84 else 3.0
        return ("vid", TRAILER, t)
    if name == "ext":
        if not use_ext: return next_item("trailer")
        t = cursor_ex[0]; cursor_ex[0] += 47.0
        if cursor_ex[0] > 1500: cursor_ex[0] = 75.0
        return ("vid", EXT, t)
    lst = POOLS[name]
    for p in lst:
        if p not in used:
            used.add(p); return ("img", p, 0)
    used.difference_update(lst)
    used.add(lst[0]); return ("img", lst[0], 0)

LINE_RULES = [
    (r"Cal Hampton", ["cal", "boobie", "dre", "raul"]),
    (r"Entre ellas encontramos", ["keys", "gell", "amb", "grass", "kalaga"]),
    (r"Real Dimez", ["dimez", "vice"]),
    (r"Jason tiene|ejército", ["jason"]),
    (r"Lucía, por su parte|prisión", ["lucia"]),
    (r"Jason Duval y Lucía", ["jl", "jason", "lucia"]),
    (r"Sus caminos|relación", ["jl"]),
    (r"Vice City, con playas", ["vice"]),
    (r"Leonida, un estado", ["vice", "keys", "grass"]),
    (r"Desde grandes ciudades", ["grass", "kalaga", "vice", "keys"]),
    (r"precarga|Esto significa", ["preload", "trailer"]),
    (r"Rockstar ha presentado música|Justice", ["trailer", "jl"]),
    (r"búsqueda policial|conducción", ["trailer", "ext"]),
]
SECTION_DEFAULT = {
    "INTRO": ["trailer", "vice", "jl", "trailer", "jason", "lucia"],
    "1": ["trailer", "preload", "vice", "trailer"],
    "2": ["jl", "jason", "lucia", "trailer"],
    "3": ["vice", "keys", "grass", "gell", "amb", "kalaga", "trailer"],
    "4": ["jl", "vice", "trailer", "dimez"],
    "5": ["ext", "trailer", "vice", "jl", "ext"],
    "6": ["vice", "trailer", "jl", "ext"],
    "7": ["vice", "trailer", "jl", "jason", "lucia"],
    "DESPEDIDA": ["vice", "jl", "trailer", "jason"],
}
def sec_key(s):
    m = re.match(r"(\d+)\.", s)
    return m.group(1) if m else s

# ---------- planificación de planos ----------
shots = []   # dict(blk, dur, kind, src, ss)
blocks = []  # orden de bloques
def add_shot(blk, dur, item):
    shots.append(dict(blk=blk, dur=dur, kind=item[0], src=item[1], ss=item[2]))
    if blk not in blocks: blocks.append(blk)

starts = [t["inicio"] + INTRO for t in tiempos]
ends = starts[1:] + [INTRO + NDUR]
# tarjeta de apertura
add_shot("INTRO", INTRO, ("img", POOLS["vice"][0], 0)); used.add(POOLS["vice"][0])
for i, t in enumerate(tiempos):
    seg = ends[i] - (starts[i] if i else INTRO)
    n = max(1, round(seg / 3.9))
    names = None
    for pat, p in LINE_RULES:
        if re.search(pat, t["texto"]): names = p; break
    if not names: names = SECTION_DEFAULT[sec_key(t["seccion"])]
    for k in range(n):
        add_shot(sec_key(t["seccion"]), seg / n, next_item(names[k % len(names)]))
# tarjeta de cierre
add_shot("DESPEDIDA", OUTRO, ("img", POOLS["vice"][-1], 0))
json.dump(shots, open(f"{WK}/shots.json", "w"), indent=1)
print("planos:", len(shots), "duración total", round(TOTAL, 1))

# ---------- render de planos ----------
def render(i):
    s = shots[i]; out = f"{WK}/shots/{i:03d}.mp4"
    if os.path.exists(out): return out
    L = s["dur"] + F; n = int(round(L * FPS))
    base = ["ffmpeg", "-y", "-loglevel", "error"]
    if s["kind"] == "vid":
        cmd = base + ["-ss", f"{s['ss']:.2f}", "-t", f"{L:.2f}", "-i", s["src"],
                      "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps={FPS}"]
    else:
        zin = i % 2 == 0
        z = f"1+0.12*on/{n}" if zin else f"1.12-0.12*on/{n}"
        cmd = base + ["-i", s["src"], "-vf",
              f"scale=2880:1620:force_original_aspect_ratio=increase,crop=2880:1620,setsar=1,"
              f"zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s=1920x1080:fps={FPS}"]
    cmd += ["-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out]
    subprocess.run(cmd, check=True)
    return out
with ThreadPoolExecutor(3) as ex:
    for k, _ in enumerate(ex.map(render, range(len(shots)))):
        if k % 15 == 0: print("render", k, "/", len(shots), flush=True)

# ---------- ensamblado por bloques con fundidos ----------
block_files = []
for b in blocks:
    idx = [i for i, s in enumerate(shots) if s["blk"] == b]
    files = [f"{WK}/shots/{i:03d}.mp4" for i in idx]
    durs = [shots[i]["dur"] for i in idx]
    out = f"{WK}/blk_{b}.mp4"
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for f in files: cmd += ["-i", f]
    if len(files) == 1:
        fc = "[0:v]null[v]"
    else:
        fc = ""; last = "[0:v]"; acc = 0.0
        for k in range(1, len(files)):
            acc += durs[k - 1]
            fc += f"{last}[{k}:v]xfade=transition=fade:duration={F}:offset={acc:.3f}[x{k}];"; last = f"[x{k}]"
        fc = fc.rstrip(";").replace(last, "[v]") if False else fc + f"{last}null[v]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-t", f"{sum(durs):.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    subprocess.run(cmd, check=True); block_files.append(out); print("bloque", b, len(files), "planos", flush=True)
open(f"{WK}/list.txt", "w").write("".join(f"file '{f}'\n" for f in block_files))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{WK}/list.txt", "-c", "copy", f"{WK}/video_sin_audio.mp4"], check=True)

# ---------- subtítulos ASS ----------
def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
def chunks(text, maxc=68):
    words = text.split(); out = []; cur = ""
    for w in words:
        if len((cur + " " + w).strip()) > maxc and cur:
            out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    if cur: out.append(cur)
    return out
def two_lines(c):
    if len(c) <= 34: return c
    mid = len(c) // 2; sp = [m.start() for m in re.finditer(" ", c)]
    k = min(sp, key=lambda x: abs(x - mid)); return c[:k] + r"\N" + c[k + 1:]
BADGE = {"1": "INFORMACIÓN OFICIAL · Rockstar Games", "2": "INFORMACIÓN OFICIAL · Rockstar Games",
         "3": "INFORMACIÓN OFICIAL · Rockstar Games", "4": "INFORMACIÓN OFICIAL · Rockstar Games"}
def badge_for(t):
    k = sec_key(t["seccion"])
    if k in ("5",):
        return "TODAVÍA POR DESCUBRIR" if ("?" in t["texto"] or "tendremos" in t["texto"] or "Pero todavía" in t["texto"]) else "INFORMACIÓN OFICIAL · Rockstar Games"
    if k == "6": return "TODAVÍA SIN CONFIRMAR"
    return BADGE.get(k)
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "",
 "[V4+ Styles]",
 "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
 "Style: Sub,DejaVu Sans,66,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,6,3,2,80,80,90,1",
 "Style: Badge,DejaVu Sans,30,&H00FFFFFF,&H00FFFFFF,&H00B4147A,&H00B4147A,-1,0,0,0,100,100,1,0,3,10,0,7,60,60,50,1",
 "Style: Mark,DejaVu Sans,30,&H80FFFFFF,&H80FFFFFF,&H80000000,&H00000000,-1,0,0,0,100,100,3,0,1,3,0,9,60,60,50,1",
 "Style: Big,DejaVu Sans,150,&H00FFFFFF,&H00FFFFFF,&H00C8509B,&H00000000,-1,0,0,0,100,100,6,0,1,8,4,5,60,60,60,1",
 "Style: Mid,DejaVu Sans,64,&H00FFB4F0,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,4,0,1,5,3,5,60,60,60,1",
 "Style: Small,DejaVu Sans,34,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,3,0,2,60,60,60,1",
 "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
def ev(a, b, st, text, layer=0): ass.append(f"Dialogue: {layer},{ts(a)},{ts(b)},{st},,0,0,0,,{text}")
ev(0, TOTAL, "Mark", "SECRETOS DE GTA", 1)
ev(0.2, INTRO, "Big", r"{\fad(500,400)}SECRETOS DE GTA", 2)
ev(0.9, INTRO, "Mid", r"{\fad(500,400)\pos(960,700)}GTA 6: QUEDAN 8 DÍAS", 2)
ev(1.2, INTRO, "Small", r"{\fad(500,400)}Canal no oficial · Imágenes y vídeos © Rockstar Games", 2)
for i, t in enumerate(tiempos):
    a, b = t["inicio"] + INTRO, t["fin"] + INTRO
    cs = chunks(t["texto"]); tot = sum(len(c) for c in cs); cur = a
    for c in cs:
        d = (b - a) * len(c) / tot; ev(cur, cur + d, "Sub", two_lines(c)); cur += d
    bd = badge_for(t)
    if bd: ev(a, b + 0.3, "Badge", bd, 1)
e0 = INTRO + NDUR
ev(e0 + 0.2, TOTAL - 0.2, "Big", r"{\fad(500,500)}SECRETOS DE GTA", 2)
ev(e0 + 0.9, TOTAL - 0.2, "Mid", r"{\fad(500,500)\pos(960,700)}¡OCHO DÍAS PARA GTA 6!", 2)
ev(e0 + 1.4, TOTAL - 0.2, "Small", r"{\fad(500,500)}Suscríbete y cuéntame tu teoría en los comentarios", 2)
open(f"{WK}/subs.ass", "w", encoding="utf8").write("\n".join(ass))

# ---------- audio: narración, música, efectos ----------
SR = 44100
def save(path, x):
    x = np.clip(x, -1, 1)
    st = np.stack([x, x], 1) if x.ndim == 1 else x
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
N = int(TOTAL * SR); t = np.arange(N) / SR
rng = np.random.default_rng(5)
beat = 60 / 76.0
chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
cl = beat * 8
L = np.zeros(N); R = np.zeros(N)
for k in range(int(TOTAL / cl) + 2):
    a = int(k * cl * SR); b = min(N, int((k + 1) * cl * SR + 1.5 * SR))
    if a >= N: break
    tt = t[a:b] - k * cl; ch = chords[k % 4]
    env = np.clip(tt / 1.6, 0, 1) * np.clip((cl + 1.5 - tt) / 1.5, 0, 1)
    pad = sum(np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 1.004 * tt) + 0.25 * np.sin(4 * np.pi * f * tt) for f in ch) * env
    bass = np.sin(2 * np.pi * (ch[0] / 4) * tt) * env * 1.4
    L[a:b] += pad * 0.10 + bass * 0.16; R[a:b] += pad * 0.10 * 0.9 + bass * 0.16
# pulso y plucks: más energía a partir de la narración
tick = np.arange(0, TOTAL, beat / 2)
for j, tk in enumerate(tick):
    if tk < INTRO - 0.5: continue
    a = int(tk * SR); n = int(0.35 * SR)
    if a + n >= N: break
    tt = np.arange(n) / SR; ch = chords[int(tk // cl) % 4]
    if j % 2 == 0:   # bombo suave
        kick = np.sin(2 * np.pi * (50 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9) * 0.22
        L[a:a + n] += kick; R[a:a + n] += kick
    f = ch[(j // 2) % 3] * 2
    pl = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7) * 0.05
    pan = 0.5 + 0.4 * math.sin(j)
    L[a:a + n] += pl * (1 - pan); R[a:a + n] += pl * pan
mus = np.stack([L, R], 1); mus /= np.abs(mus).max(); mus *= 0.6
save(f"{WK}/musica.wav", mus)

def whoosh(dur=1.0, up=True):
    n = int(dur * SR); x = rng.standard_normal(n); y = np.zeros(n); lp = 0.0
    for i in range(n):
        u = i / n; fc = 250 + 4500 * (u if up else 1 - u)
        a = 1 - math.exp(-2 * math.pi * fc / SR); lp += a * (x[i] - lp); y[i] = lp
    env = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    return y * env * 1.2
def impact(dur=2.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * (45 + 80 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 2.2)
    nz = rng.standard_normal(n) * np.exp(-tt * 14) * 0.25
    return (body + nz) * 0.9
sfx = np.zeros(N)
def put(x, at):
    a = int(at * SR); b = min(N, a + len(x))
    if a < N: sfx[a:b] += x[:b - a]
put(whoosh(INTRO, True), 0.0); put(impact(), INTRO); put(impact(1.5) * 0.7, INTRO + 0.9)
seen = set()
for tt_ in tiempos:
    k = sec_key(tt_["seccion"])
    if k not in seen:
        seen.add(k)
        if k != "INTRO": put(whoosh(0.9, True), tt_["inicio"] + INTRO - 0.9 + 0.1)
put(whoosh(1.2, False), e0 + 0.3); put(impact(2.5) * 0.6, e0 + 0.9)
save(f"{WK}/sfx.wav", sfx * 0.7)

# ---------- mezcla y muxado final ----------
pitch = 0.94
subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
  "-i", f"{P}/narracion.wav", "-i", f"{WK}/musica.wav", "-i", f"{WK}/sfx.wav",
  "-filter_complex",
  f"[0:a]asetrate={int(NSR*pitch)},aresample={SR},atempo={1/pitch:.5f},equalizer=f=130:t=h:w=120:g=4,equalizer=f=3000:t=h:w=800:g=2,"
  f"acompressor=threshold=0.1:ratio=3:attack=5:release=80,loudnorm=I=-15:TP=-1.5:LRA=7,aformat=channel_layouts=stereo,adelay={int(INTRO*1000)}|{int(INTRO*1000)},apad=whole_dur={TOTAL}[n];"
  f"[n]asplit[n1][n2];[1:a]aecho=0.8:0.85:70:0.35,volume=0.9[m];"
  f"[m][n1]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[md];"
  f"[md][n2][2:a]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[a]",
  "-map", "[a]", "-t", f"{TOTAL:.2f}", "-ar", str(SR), f"{WK}/mezcla.wav"], check=True)
os.chdir(WK)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "video_sin_audio.mp4", "-i", "mezcla.wav",
  "-vf", "ass=subs.ass", "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
  "-c:a", "aac", "-b:a", "192k", "-t", f"{TOTAL:.2f}", "-movflags", "+faststart", f"{P}/gta6_quedan_8_dias.mp4"], check=True)
print("LISTO", round(TOTAL / 60, 2), "min")
