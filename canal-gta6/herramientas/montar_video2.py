import json, os, re, glob, subprocess, wave, math, sys
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ROOT = "/tmp/claude-0/-home-user-creative-velas/836e68d2-3ca3-5ed0-bd33-fc0cebbfc14f/scratchpad"
RS = f"{ROOT}/rs"
WK = f"{ROOT}/work/v2"
P = "/home/user/creative-velas/canal-gta6/video01"
os.makedirs(f"{WK}/shots", exist_ok=True)
FPS, F = 30, 0.35
INTRO, OUTRO = 3.0, 6.0
OUTNAME = os.environ.get("OUTNAME", "gta6_quedan_8_dias_v2.mp4")

tiempos = json.load(open(f"{P}/tiempos_youtuber.json"))
with wave.open(f"{P}/narracion_youtuber.wav") as w:
    NSR, NDUR = w.getframerate(), w.getnframes() / w.getframerate()
TOTAL = INTRO + NDUR + OUTRO

# ---------- reservas de imágenes oficiales ----------
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
if not POOLS["dimez"]: POOLS["dimez"] = POOLS["vice"]
TRAILER = f"{RS}/vid/launch_trailer.mp4"
used = set()
_v = [float(m.group(1)) for m in re.finditer(r"YAVG=([\d.]+)", open(f"{ROOT}/work/yavg.txt").read())]
_cand = [(i / 2) for i in range(0, len(_v) - 7) if min(_v[i:i + 7]) > 42]
WINS = []
for c in _cand:
    if not WINS or c - WINS[-1] >= 3.5: WINS.append(c)
print("tomas luminosas del tráiler:", len(WINS), flush=True)
_wi = [0]; _fb = [0]

def next_item(name):
    if name in ("trailer", "ext"):
        if _wi[0] >= len(WINS):   # sin tomas luminosas nuevas: usar otra imagen oficial en vez de repetir
            _fb[0] += 1; return next_item(["vice", "jl", "jason", "lucia"][_fb[0] % 4])
        t = WINS[_wi[0]]; _wi[0] += 1
        return ("vid", TRAILER, t)
    lst = POOLS[name]
    for p in lst:
        if p not in used:
            used.add(p); return ("img", p, 0)
    used.difference_update(lst); used.add(lst[0]); return ("img", lst[0], 0)

LINE_RULES = [
    (r"Cal Hampton", ["cal", "boobie", "dre", "raul"]),
    (r"Tenemos Leonida Keys", ["keys", "gell", "amb", "grass", "kalaga"]),
    (r"Real Dimez", ["dimez", "vice"]),
    (r"Jason tiene|ejército", ["jason"]),
    (r"Lucía, por su parte|cárcel", ["lucia"]),
    (r"Los protagonistas son", ["jl", "jason", "lucia"]),
    (r"Sus caminos|relación", ["jl"]),
    (r"Su ciudad más famosa", ["vice"]),
    (r"Leonida, un estado", ["vice", "keys", "grass"]),
    (r"ambientes totalmente", ["grass", "kalaga", "vice", "keys"]),
    (r"precarga|Eso sí", ["preload", "trailer"]),
    (r"Justice", ["trailer", "jl"]),
    (r"búsqueda policial|conducción", ["trailer", "trailer"]),
]
SECTION_DEFAULT = {
    "INTRO": ["trailer", "vice", "jl", "trailer", "jason", "lucia"],
    "1": ["trailer", "preload", "vice", "trailer"], "2": ["jl", "jason", "lucia", "trailer"],
    "3": ["vice", "keys", "grass", "gell", "amb", "kalaga", "trailer"], "4": ["jl", "vice", "trailer", "dimez"],
    "5": ["trailer", "vice", "jl", "trailer"], "6": ["vice", "trailer", "jl"],
    "7": ["vice", "trailer", "jl", "jason", "lucia"], "DESPEDIDA": ["vice", "jl", "trailer", "jason"],
}
def sec_key(s):
    m = re.match(r"(\d+)\.", s); return m.group(1) if m else s
SEC_TITLE = {"1": "1 · FECHA Y PREPARATIVOS", "2": "2 · JASON Y LUCÍA", "3": "3 · LEONIDA", "4": "4 · CURIOSIDADES",
             "5": "5 · ¿QUÉ DESCUBRIREMOS?", "6": "6 · LO QUE FALTA POR SABER", "7": "7 · BIENVENIDOS"}

# ---------- planificación de planos ----------
shots = []; blocks = []
def add_shot(blk, dur, item):
    shots.append(dict(blk=blk, dur=dur, kind=item[0], src=item[1], ss=item[2]))
    if blk not in blocks: blocks.append(blk)
starts = [t["inicio"] + INTRO for t in tiempos]
ends = starts[1:] + [INTRO + NDUR]
add_shot("INTRO", INTRO, ("img", POOLS["vice"][0], 0)); used.add(POOLS["vice"][0])
for i, t in enumerate(tiempos):
    seg = ends[i] - (starts[i] if i else INTRO)
    n = max(1, round(seg / 3.6))
    names = next((p for pat, p in LINE_RULES if re.search(pat, t["texto"])), None) or SECTION_DEFAULT[sec_key(t["seccion"])]
    for k in range(n):
        add_shot(sec_key(t["seccion"]), seg / n, next_item(names[k % len(names)]))
add_shot("DESPEDIDA", OUTRO, ("img", POOLS["vice"][-1], 0))
json.dump(shots, open(f"{WK}/shots.json", "w"), indent=1)
print("planos:", len(shots), "duración total", round(TOTAL, 1), flush=True)

# ---------- render de planos ----------
def render(i):
    s = shots[i]; out = f"{WK}/shots/{i:03d}.mp4"
    if os.path.exists(out): return out
    L = s["dur"] + F; n = int(round(L * FPS))
    base = ["ffmpeg", "-y", "-loglevel", "error"]
    if s["kind"] == "vid":
        cmd = base + ["-ss", f"{s['ss']:.2f}", "-t", f"{L:.2f}", "-i", s["src"],
                      "-vf", f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps={FPS},eq=contrast=1.06:saturation=1.2,vignette=angle=PI/5"]
    else:
        mode = i % 4
        if mode == 0: z, x, y = f"1+0.13*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 1: z, x, y = f"1.13-0.13*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 2: z, x, y = "1.14", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"
        else: z, x, y = "1.14", f"(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"
        cmd = base + ["-i", s["src"], "-vf",
              f"scale=2880:1620:force_original_aspect_ratio=increase,crop=2880:1620,setsar=1,"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s=1920x1080:fps={FPS},eq=contrast=1.06:saturation=1.2,vignette=angle=PI/5"]
    cmd += ["-frames:v", str(n), "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out]
    subprocess.run(cmd, check=True); return out
with ThreadPoolExecutor(3) as ex:
    for k, _ in enumerate(ex.map(render, range(len(shots)))):
        if k % 15 == 0: print("render", k, "/", len(shots), flush=True)

# ---------- ensamblado ----------
block_files = []
for b in blocks:
    idx = [i for i, s in enumerate(shots) if s["blk"] == b]
    files = [f"{WK}/shots/{i:03d}.mp4" for i in idx]; durs = [shots[i]["dur"] for i in idx]
    out = f"{WK}/blk_{b}.mp4"; cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    for f in files: cmd += ["-i", f]
    if len(files) == 1: fc = "[0:v]null[v]"
    else:
        fc = ""; last = "[0:v]"; acc = 0.0
        for k in range(1, len(files)):
            acc += durs[k - 1]
            fc += f"{last}[{k}:v]xfade=transition=fade:duration={F}:offset={acc:.3f}[x{k}];"; last = f"[x{k}]"
        fc += f"{last}null[v]"
    cmd += ["-filter_complex", fc, "-map", "[v]", "-t", f"{sum(durs):.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), out]
    subprocess.run(cmd, check=True); block_files.append(out); print("bloque", b, flush=True)
open(f"{WK}/list.txt", "w").write("".join(f"file '{f}'\n" for f in block_files))
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", f"{WK}/list.txt", "-c", "copy", f"{WK}/video_sin_audio.mp4"], check=True)

# ---------- subtítulos y animaciones (ASS) ----------
def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
def chunks(text, maxc=62):
    out = []; cur = ""
    for w in text.split():
        if len((cur + " " + w).strip()) > maxc and cur: out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    if cur: out.append(cur)
    return out
def two_lines(c):
    if len(c) <= 32: return c
    mid = len(c) // 2; sp = [m.start() for m in re.finditer(" ", c)]
    k = min(sp, key=lambda x: abs(x - mid)); return c[:k] + r"\N" + c[k + 1:]
KEYWORDS = ["GTA 6", "Leonida Keys", "Leonida", "Vice City", "Jason Duval", "Lucía Caminos", "Jason", "Lucía", "Rockstar Games",
            "PlayStation 5", "Xbox Series X y Series S", "19 de noviembre de 2026", "19 de noviembre", "10 de noviembre", "PC", "SECRETOS DE GTA",
            "OCHO DÍAS", "Justice", "Flower in a Hurricane", "Real Dimez", "Port Gellhorn", "Ambrosia", "Grassrivers", "Mount Kalaga"]
KW_RE = re.compile("|".join(r"(?<!\w)" + re.escape(k) + r"(?!\w)" for k in sorted(KEYWORDS, key=len, reverse=True)))
def hl(c): return KW_RE.sub(lambda m: r"{\c&H00D7FF&}" + m.group(0) + r"{\c&HFFFFFF&}", c)
BADGE_OFF = "INFORMACIÓN OFICIAL · Rockstar Games"
def badge_for(t):
    k = sec_key(t["seccion"])
    if k in ("1", "2", "3", "4"): return BADGE_OFF
    if k == "5": return "TODAVÍA POR DESCUBRIR" if re.search(r"\?|nos toca|hype", t["texto"]) else BADGE_OFF
    if k == "6": return "TODAVÍA SIN CONFIRMAR"
    return None
STICKERS = [
    (r"jueves 19 de noviembre", "SALE EL 19 NOV 2026"), (r"PlayStation 5", "PS5 · XBOX SERIES X|S"),
    (r"^Y de PC|^De PC", "PC: SIN FECHA OFICIAL"), (r"precarga digital", "PRECARGA DESDE EL 10 NOV"),
    (r"no vas a poder jugar", "JUEGO: SOLO DESDE EL 19 NOV"), (r"cuenta atrás", "8 DÍAS PARA EL LANZAMIENTO"),
    (r"redes sociales ficticias", "REDES SOCIALES DENTRO DEL JUEGO"), (r"Flower in a Hurricane", "JUSTICE · FLOWER IN A HURRICANE"),
    (r"búsqueda policial", "BÚSQUEDA POLICIAL CON NIVELES"), (r"multijugador", "MULTIJUGADOR: SIN ANUNCIO OFICIAL"),
    (r"estado inspirado en Florida", "LEONIDA = ESTADO INSPIRADO EN FLORIDA"), (r"alternar entre Jason y Lucía", "PODREMOS ALTERNAR ENTRE LOS DOS"),
    (r"presentación extendida", "PRESENTACIÓN EXTENDIDA OFICIAL"),
]
LABELS = [(r"^Jason_Duval", "JASON DUVAL"), (r"^Lucia_Caminos", "LUCÍA CAMINOS"), (r"^Jason_and_Lucia|^Jason_Lucia_", "JASON Y LUCÍA"),
          (r"^Cal_Hampton", "CAL HAMPTON"), (r"^Boobie_Ike", "BOOBIE IKE"), (r"^DreQuan", "DRE'QUAN PRIEST"), (r"^Raul_", "RAUL BAUTISTA"),
          (r"^Real_Dimez", "REAL DIMEZ"), (r"^Leonida_Keys", "LEONIDA KEYS"), (r"^Port_Gellhorn", "PORT GELLHORN"), (r"^Ambrosia", "AMBROSIA"),
          (r"^Grassrivers", "GRASSRIVERS"), (r"^Mount_Kalaga", "PARQUE NACIONAL MOUNT KALAGA")]
ARROW = r"m 0 25 l 48 25 l 48 0 l 100 40 l 48 80 l 48 55 l 0 55"
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1920", "PlayResY: 1080", "WrapStyle: 2", "",
 "[V4+ Styles]",
 "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
 "Style: Sub,Montserrat ExtraBold,60,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,6,3,2,80,80,90,1",
 "Style: Badge,Anton,34,&H00FFFFFF,&H00FFFFFF,&H00B4147A,&H00B4147A,-1,0,0,0,100,100,1,0,3,10,0,7,60,60,50,1",
 "Style: Mark,Anton,32,&H80FFFFFF,&H80FFFFFF,&H80000000,&H00000000,-1,0,0,0,100,100,3,0,1,3,0,9,60,60,50,1",
 "Style: Big,Anton,210,&H00FFFFFF,&H00FFFFFF,&H00C8509B,&H00000000,-1,0,0,0,100,100,6,0,1,8,4,5,60,60,60,1",
 "Style: Mid,Bebas Neue,96,&H00FFB4F0,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,4,0,1,5,3,5,60,60,60,1",
 "Style: Small,Montserrat ExtraBold,36,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,3,0,2,60,60,60,1",
 "Style: Title,Anton,72,&H00FFFFFF,&H00FFFFFF,&H00B4147A,&H00B4147A,-1,0,0,0,100,100,2,0,3,16,0,8,60,60,110,1",
 "Style: Sticker,Anton,54,&H00FFFFFF,&H00FFFFFF,&H0000A5FF,&H0000A5FF,-1,0,0,0,100,100,1,0,3,14,0,9,60,60,250,1",
 "Style: Tag,Anton,58,&H00FFFFFF,&H00FFFFFF,&H00C8509B,&H00C8509B,-1,0,0,0,100,100,2,0,3,14,0,1,190,60,300,1",
 "Style: Shape,DejaVu Sans,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
 "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
def ev(a, b, st, text, layer=0): ass.append(f"Dialogue: {layer},{ts(a)},{ts(max(b, a + 0.05))},{st},,0,0,0,,{text}")
def arrow(a, b, x, y, color="&H0000A5FF&", scale=60, layer=3, flip=False):
    # flecha animada: entra desde la izquierda y "late" (movimiento de ida y vuelta)
    rot = r"\frz180" if flip else ""
    ev(a, b, "Shape", r"{\an7\p1\bord0\shad0\1c" + color + r"\fscx" + str(scale) + r"\fscy" + str(scale) + rot +
       rf"\move({x-80},{y},{x},{y},0,250)\t(250,{int(max(300,(b-a)*1000))},\fscx{scale+14}\fscy{scale+14})\fad(120,150)" + "}" + ARROW + r"{\p0}", layer)

ev(0, TOTAL, "Mark", "SECRETOS DE GTA", 1)
ev(0.2, INTRO, "Big", r"{\fad(500,400)\t(0,600,\fscx108\fscy108)\t(600,1000,\fscx100\fscy100)}SECRETOS DE GTA", 2)
ev(0.9, INTRO, "Mid", r"{\fad(500,400)\pos(960,700)}GTA 6: QUEDAN 8 DÍAS", 2)
ev(1.2, INTRO, "Small", r"{\fad(500,400)}Canal no oficial · Imágenes y vídeos © Rockstar Games", 2)
# destello blanco al arrancar
def flash(at): ev(at, at + 0.4, "Shape", r"{\an7\pos(0,0)\p1\bord0\shad0\1c&HFFFFFF&\alpha&H70&\t(0,380,\alpha&HFF&)}m 0 0 l 1920 0 1920 1080 0 1080{\p0}", 9)
flash(INTRO)
seen = set()
for i, t in enumerate(tiempos):
    a, b = t["inicio"] + INTRO, t["fin"] + INTRO
    k = sec_key(t["seccion"])
    if k not in seen:
        seen.add(k)
        if k in SEC_TITLE:
            flash(a - 0.1); ev(a, a + 2.6, "Title", rf"{{\fad(150,300)\move(960,40,960,110,0,250)\t(0,250,\fscx108\fscy108)\t(250,420,\fscx100\fscy100)}}{SEC_TITLE[k]}", 5)
    cs = chunks(t["texto"]); tot = sum(len(c) for c in cs); cur = a
    for c in cs:
        d = (b - a) * len(c) / tot
        ev(cur, cur + d, "Sub", r"{\fscx88\fscy88\t(0,130,\fscx104\fscy104)\t(130,230,\fscx100\fscy100)}" + hl(two_lines(c)), 4); cur += d
    bd = badge_for(t)
    if bd: ev(a, b + 0.3, "Badge", rf"{{\fad(120,120)}}{bd}", 1)
    for pat, text in STICKERS:
        if re.search(pat, t["texto"]):
            e = b + 0.6
            ev(a + 0.15, e, "Sticker", rf"{{\fad(120,200)\move(2300,250,1860,250,0,230)\t(230,380,\fscx110\fscy110)\t(380,520,\fscx100\fscy100)}}{text}", 6)
            break
# etiquetas con flecha según la imagen oficial que se muestra (nombre fiable por nombre de archivo)
tcur = 0.0
for s in shots:
    s0, s1 = tcur, tcur + s["dur"]; tcur = s1
    if s["kind"] != "img": continue
    base = os.path.basename(s["src"])
    for pat, text in LABELS:
        if re.match(pat, base):
            a, b = s0 + 0.35, s1 - 0.15
            if b - a > 0.8:
                ev(a, b, "Tag", rf"{{\fad(120,150)\move(-600,780,190,780,0,260)}}{text}", 7)
                arrow(a, b, 60, 745)
            break
e0 = INTRO + NDUR
flash(e0 + 0.1)
ev(e0 + 0.2, TOTAL - 0.2, "Big", r"{\fad(500,500)\t(0,500,\fscx108\fscy108)\t(500,900,\fscx100\fscy100)}SECRETOS DE GTA", 2)
ev(e0 + 0.9, TOTAL - 0.2, "Mid", r"{\fad(500,500)\pos(960,700)}¡OCHO DÍAS PARA GTA 6!", 2)
# botón de suscribirse + flecha que rebota
ev(e0 + 1.8, TOTAL - 0.2, "Sticker", r"{\an2\pos(960,960)\fad(200,300)\1c&H0000FF&\3c&H0000FF&\bord16\t(0,300,\fscx112\fscy112)\t(300,500,\fscx100\fscy100)}SUSCRÍBETE", 6)
arrow(e0 + 1.8, TOTAL - 0.2, 600, 920, "&H0000FFFF&", 70, 7)
ev(e0 + 1.8, TOTAL - 0.2, "Small", r"{\an2\pos(960,1040)\fad(200,300)}Y cuéntame tu teoría en los comentarios", 2)
open(f"{WK}/subs.ass", "w", encoding="utf8").write("\n".join(ass))

# ---------- música y efectos ----------
SR = 44100
def save(path, x):
    st = np.stack([x, x], 1) if x.ndim == 1 else x
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
N = int(TOTAL * SR); t = np.arange(N) / SR
rng = np.random.default_rng(7)
beat = 60 / 84.0
chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
cl = beat * 8; L = np.zeros(N); R = np.zeros(N)
for k in range(int(TOTAL / cl) + 2):
    a = int(k * cl * SR); b = min(N, int((k + 1) * cl * SR + 1.5 * SR))
    if a >= N: break
    tt = t[a:b] - k * cl; ch = chords[k % 4]
    env = np.clip(tt / 1.4, 0, 1) * np.clip((cl + 1.5 - tt) / 1.5, 0, 1)
    pad = sum(np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 1.004 * tt) + 0.25 * np.sin(4 * np.pi * f * tt) for f in ch) * env
    bass = np.sin(2 * np.pi * (ch[0] / 4) * tt) * env * 1.4
    L[a:b] += pad * 0.10 + bass * 0.16; R[a:b] += pad * 0.09 + bass * 0.16
for j, tk in enumerate(np.arange(0, TOTAL, beat / 2)):
    if tk < INTRO - 0.5: continue
    a = int(tk * SR); n = int(0.35 * SR)
    if a + n >= N: break
    tt = np.arange(n) / SR; ch = chords[int(tk // cl) % 4]
    if j % 2 == 0:
        kick = np.sin(2 * np.pi * (50 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9) * 0.24; L[a:a + n] += kick; R[a:a + n] += kick
    else:
        hat = rng.standard_normal(n) * np.exp(-tt * 60) * 0.03; L[a:a + n] += hat; R[a:a + n] += hat
    f = ch[(j // 2) % 3] * 2; pl = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7) * 0.05; pan = 0.5 + 0.4 * math.sin(j)
    L[a:a + n] += pl * (1 - pan); R[a:a + n] += pl * pan
mus = np.stack([L, R], 1); mus /= np.abs(mus).max(); mus *= 0.6
save(f"{WK}/musica.wav", mus)
def whoosh(dur=1.0, up=True):
    n = int(dur * SR); x = rng.standard_normal(n); y = np.zeros(n); lp = 0.0
    for i in range(n):
        u = i / n; fc = 250 + 4500 * (u if up else 1 - u); a = 1 - math.exp(-2 * math.pi * fc / SR); lp += a * (x[i] - lp); y[i] = lp
    return y * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * 1.2
def impact(dur=2.0):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * (45 + 80 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 2.2) + rng.standard_normal(n) * np.exp(-tt * 14) * 0.25) * 0.9
def pop(dur=0.18):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (600 + 900 * tt / dur) * tt) * np.exp(-tt * 22) * 0.5
sfx = np.zeros(N)
def put(x, at):
    a = int(at * SR); b = min(N, a + len(x))
    if 0 <= a < N: sfx[a:b] += x[:b - a]
put(whoosh(INTRO, True), 0.0); put(impact(), INTRO); put(impact(1.5) * 0.7, INTRO + 0.7)
seen = set()
for tt_ in tiempos:
    k = sec_key(tt_["seccion"])
    if k not in seen:
        seen.add(k)
        if k != "INTRO": put(whoosh(0.8, True), tt_["inicio"] + INTRO - 0.7)
    for pat, _ in STICKERS:
        if re.search(pat, tt_["texto"]): put(pop(), tt_["inicio"] + INTRO + 0.15); break
tcur = 0.0
for s in shots:
    s0 = tcur; tcur += s["dur"]
    if s["kind"] == "img" and any(re.match(p, os.path.basename(s["src"])) for p, _ in LABELS) and s["dur"] > 1.15: put(pop(0.14) * 0.7, s0 + 0.35)
put(whoosh(1.2, False), e0 + 0.2); put(impact(2.5) * 0.6, e0 + 0.8); put(pop(0.25), e0 + 1.8)
save(f"{WK}/sfx.wav", sfx * 0.7)

# ---------- mezcla y render final ----------
subprocess.run(["ffmpeg", "-y", "-loglevel", "error",
  "-i", f"{P}/narracion_youtuber.wav", "-i", f"{WK}/musica.wav", "-i", f"{WK}/sfx.wav", "-filter_complex",
  f"[0:a]aresample={SR},highpass=f=70,equalizer=f=180:t=h:w=150:g=2,equalizer=f=3500:t=h:w=1500:g=2.5,acompressor=threshold=0.1:ratio=3:attack=5:release=80,"
  f"loudnorm=I=-15:TP=-1.5:LRA=7,aformat=channel_layouts=stereo,adelay={int(INTRO*1000)}|{int(INTRO*1000)},apad=whole_dur={TOTAL}[n];"
  f"[n]asplit[n1][n2];[1:a]aecho=0.8:0.85:70:0.3,volume=0.8[m];[m][n1]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[md];"
  f"[md][n2][2:a]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[a]",
  "-map", "[a]", "-t", f"{TOTAL:.2f}", "-ar", str(SR), f"{WK}/mezcla.wav"], check=True)
os.chdir(WK)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "video_sin_audio.mp4", "-i", "mezcla.wav", "-vf", "ass=subs.ass",
  "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-b:v", "6000k", "-maxrate", "8000k", "-bufsize", "12000k", "-pix_fmt", "yuv420p",
  "-c:a", "aac", "-b:a", "192k", "-t", f"{TOTAL:.2f}", "-movflags", "+faststart", f"{WK}/{OUTNAME}"], check=True)
print("LISTO", round(TOTAL / 60, 2), "min", flush=True)
