import json, os, re, glob, subprocess, wave, math
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ROOT = "/tmp/claude-0/-home-user-creative-velas/836e68d2-3ca3-5ed0-bd33-fc0cebbfc14f/scratchpad"
RS = f"{ROOT}/rs"; WK = f"{ROOT}/work/short"; P = "/home/user/creative-velas/canal-gta6/short01"
os.makedirs(f"{WK}/shots", exist_ok=True)
FPS, F = 30, 0.3
LEAD, TAIL = 0.15, 1.4
tiempos = json.load(open(f"{P}/tiempos_short.json"))
with wave.open(f"{P}/narracion_short.wav") as w:
    NSR, NDUR = w.getframerate(), w.getnframes() / w.getframerate()
TOTAL = LEAD + NDUR + TAIL
print("duración total", round(TOTAL, 1), flush=True)

BLACKLIST = ['Jason_and_Lucia_18.0kjv.et7330m_.jpg', 'Jason_and_Lucia_14.10e7v.06pcm_t.jpg', 'Boobie_Ike_04.0~1fr6ijgvnzx.jpg',
 'DreQuan_Priest_01.0_0~wi-ipdj35.jpg', 'Lucia_Caminos_06.0fxbjfk0jakb3.jpg', 'Port_Gellhorn_04.0hd-7kzfi51q..jpg',
 'Port_Gellhorn_07.053ldlg0m.2r..jpg', 'Real_Dimez_01.0djwwboo8-glx.jpg', 'Real_Dimez_02.1366u9.x.yp0_.jpg', 'Vice_City_05.0~r~o0jzpp4a-.jpg',
 'Vice_City_06.0_tdmr3u9w84x.jpg', 'Vice_City_07.0b3mhak4k78oh.jpg', 'Vice_City_18.001ebutl6h-9w.jpg', 'Vice_City_23.183sae.altxv3.jpg',
 'Vice_City_25.0f72z-5qgyd~v.jpg']
imgs = {}
for f in sorted(glob.glob(f"{RS}/img/*.jpg")):
    if Image.open(f).size[0] < 1900 or os.path.basename(f) in BLACKLIST: continue
    imgs[os.path.basename(f)] = f
def pool(pat): return [v for k, v in imgs.items() if re.match(pat, k)]
POOLS = {"vice": pool(r"Vice_City"), "jason": pool(r"Jason_Duval"), "lucia": pool(r"Lucia_Caminos"),
         "jl": pool(r"Jason_and_Lucia|Jason_Lucia_|desktop|hero|mediaDesktop|onlyInLeonida|outro"),
         "keys": pool(r"Leonida_Keys"), "gell": pool(r"Port_Gellhorn"), "amb": pool(r"Ambrosia"), "grass": pool(r"Grassrivers"),
         "kalaga": pool(r"Mount_Kalaga"), "dimez": pool(r"Real_Dimez"), "preload": pool(r"GTAVI_Pre_Load|pre-load")}
for k, v in POOLS.items(): print(k, len(v))
TRAILER = f"{RS}/vid/launch_trailer.mp4"
_v = [float(m.group(1)) for m in re.finditer(r"YAVG=([\d.]+)", open(f"{ROOT}/work/yavg.txt").read())]
OKR = [(3.0, 15.5), (19.5, 23.3), (27.0, 74.0)]
def _ok(ss): return any(a <= ss and ss + 3.0 <= b for a, b in OKR)
WINS = []
for c in [(i / 2) for i in range(0, len(_v) - 6) if min(_v[i:i + 6]) > 42 and _ok(i / 2)]:
    if not WINS or c - WINS[-1] >= 3.0: WINS.append(c)
_wi = [0]; used = set()
def next_item(name):
    if name == "trailer":
        if _wi[0] >= len(WINS): return next_item("vice")
        t = WINS[_wi[0]]; _wi[0] += 1; return ("vid", TRAILER, t)
    lst = POOLS[name]
    for p in lst:
        if p not in used: used.add(p); return ("img", p, 0)
    used.difference_update(lst); used.add(lst[0]); return ("img", lst[0], 0)

# (pools por línea, nº de planos forzado)
PLAN = [(["jl", "vice"], None), (["vice", "keys"], None), (["jason", "lucia"], None), (["lucia", "jason", "jl"], None),
        (["grass", "kalaga", "gell"], None), (["keys", "gell", "amb", "grass", "kalaga"], 5), (["dimez", "dimez", "vice"], 3),
        (["trailer", "vice"], None), (["trailer", "vice"], None), (["preload", "vice"], None), (["vice"], None), (["jl", "vice"], None)]
NUM = {1: "1", 2: "2", 3: "2", 4: "3", 5: "3", 6: "4", 7: "5"}
assert len(PLAN) == len(tiempos), (len(PLAN), len(tiempos))

starts = [t["inicio"] + LEAD for t in tiempos]
ends = starts[1:] + [LEAD + NDUR + TAIL]
shots = []
for i, t in enumerate(tiempos):
    seg = ends[i] - (starts[i] if i else 0)
    names, force = PLAN[i]
    n = force or max(1, round(seg / 2.7))
    for k in range(n): shots.append(dict(dur=seg / n, line=i, **dict(zip(("kind", "src", "ss"), next_item(names[k % len(names)])))))
json.dump(shots, open(f"{WK}/shots.json", "w"), indent=1)
print("planos:", len(shots), "trailer:", sum(s["kind"] == "vid" for s in shots), flush=True)

def render(i):
    s = shots[i]; out = f"{WK}/shots/{i:03d}.mp4"
    if os.path.exists(out): return out
    L = s["dur"] + F; n = int(round(L * FPS))
    BG = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=40:6,eq=brightness=-0.22:saturation=1.25"
    if s["kind"] == "vid":
        pre = ["-ss", f"{s['ss']:.2f}", "-t", f"{L:.2f}", "-i", s["src"]]
        fc = (f"[0:v]crop=3840:1920:0:120,fps={FPS},split[a][b];[a]{BG}[bg];"
              f"[b]crop=3413:1920,scale=1080:608,setsar=1,eq=contrast=1.06:saturation=1.2[fg];[bg][fg]overlay=0:656,fps=30,vignette=angle=PI/5,setsar=1,format=yuv420p[v]")
    else:
        pre = ["-framerate", str(FPS), "-i", s["src"]]
        mode = i % 4
        if mode == 0: z, x, y = f"1+0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 1: z, x, y = f"1.12-0.12*on/{n}", "iw/2-(iw/zoom/2)", "ih/2-(ih/zoom/2)"
        elif mode == 2: z, x, y = "1.12", f"(iw-iw/zoom)*on/{n}", "ih/2-(ih/zoom/2)"
        else: z, x, y = "1.12", f"(iw-iw/zoom)*(1-on/{n})", "ih/2-(ih/zoom/2)"
        fc = (f"[0:v]split[a][b];[a]{BG}[bg];"
              f"[b]scale=2160:1215:force_original_aspect_ratio=increase,crop=2160:1215,setsar=1,"
              f"zoompan=z='{z}':x='{x}':y='{y}':d={n}:s=1080x608:fps={FPS},eq=contrast=1.06:saturation=1.2[fg];[bg][fg]overlay=0:656,fps=30,vignette=angle=PI/5,setsar=1,format=yuv420p[v]")
    cmd = ["ffmpeg", "-y", "-loglevel", "error", *pre, "-filter_complex", fc, "-map", "[v]", "-frames:v", str(n), "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", out]
    subprocess.run(cmd, check=True); return out
with ThreadPoolExecutor(3) as ex:
    for k, _ in enumerate(ex.map(render, range(len(shots)))):
        if k % 8 == 0: print("render", k, "/", len(shots), flush=True)

# ensamblado con fundidos
files = [f"{WK}/shots/{i:03d}.mp4" for i in range(len(shots))]; durs = [s["dur"] for s in shots]
cmd = ["ffmpeg", "-y", "-loglevel", "error"]
for f in files: cmd += ["-i", f]
fc = "".join(f"[{k}:v]fps=30,setsar=1,format=yuv420p,settb=AVTB[n{k}];" for k in range(len(files)))
last = "[n0]"; acc = 0.0
for k in range(1, len(files)):
    acc += durs[k - 1]; fc += f"{last}[n{k}]xfade=transition=fade:duration={F}:offset={acc:.3f}[x{k}];"; last = f"[x{k}]"
fc += f"{last}null[v]"
cmd += ["-filter_complex", fc, "-map", "[v]", "-t", f"{sum(durs):.3f}", "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p", "-r", str(FPS), f"{WK}/video_sin_audio.mp4"]
subprocess.run(cmd, check=True); print("ensamblado ok", flush=True)

# subtítulos y animaciones
def ts(t):
    h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
def chunks(text, maxc=44):
    out = []; cur = ""
    for w in text.split():
        if len((cur + " " + w).strip()) > maxc and cur: out.append(cur); cur = w
        else: cur = (cur + " " + w).strip()
    if cur: out.append(cur)
    return out
def two_lines(c):
    if len(c) <= 22: return c
    mid = len(c) // 2; sp = [m.start() for m in re.finditer(" ", c)]
    k = min(sp, key=lambda x: abs(x - mid)); return c[:k] + r"\N" + c[k + 1:]
KEYWORDS = ["GTA 6", "Leonida Keys", "Leonida", "Vice City", "Jason", "Lucía", "Port Gellhorn", "Ambrosia", "Grassrivers", "Mount Kalaga",
            "Real Dimez", "Justice", "Flower in a Hurricane", "19 de noviembre", "10 de noviembre", "PS5", "PC", "26 minutos", "Cinco", "Uno", "Dos", "Tres", "Cuatro"]
KW_RE = re.compile("|".join(r"(?<!\w)" + re.escape(k) + r"(?!\w)" for k in sorted(KEYWORDS, key=len, reverse=True)))
def hl(c): return KW_RE.sub(lambda m: r"{\c&H00D7FF&}" + m.group(0) + r"{\c&HFFFFFF&}", c)
LABELS = [(r"^Jason_Duval", "JASON DUVAL"), (r"^Lucia_Caminos", "LUCÍA CAMINOS"), (r"^Jason_and_Lucia|^Jason_Lucia_", "JASON Y LUCÍA"),
          (r"^Real_Dimez", "REAL DIMEZ"), (r"^Leonida_Keys", "LEONIDA KEYS"), (r"^Port_Gellhorn", "PORT GELLHORN"), (r"^Ambrosia", "AMBROSIA"),
          (r"^Grassrivers", "GRASSRIVERS"), (r"^Mount_Kalaga", "PARQUE NACIONAL MOUNT KALAGA")]
ARROW = r"m 0 25 l 48 25 l 48 0 l 100 40 l 48 80 l 48 55 l 0 55"
ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "WrapStyle: 2", "",
 "[V4+ Styles]",
 "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
 "Style: Sub,Montserrat ExtraBold,68,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,7,3,2,50,50,440,1",
 "Style: Title,Anton,96,&H00FFFFFF,&H00FFFFFF,&H00C8509B,&H00000000,0,0,0,0,100,100,3,0,1,9,4,8,40,40,170,1",
 "Style: Num,Anton,200,&H00FFFFFF,&H00FFFFFF,&H00B4147A,&H00B4147A,0,0,0,0,100,100,2,0,3,18,0,8,40,40,330,1",
 "Style: Tag,Anton,58,&H00FFFFFF,&H00FFFFFF,&H00C8509B,&H00C8509B,0,0,0,0,100,100,2,0,3,14,0,1,150,40,735,1",
 "Style: Sticker,Anton,56,&H00FFFFFF,&H00FFFFFF,&H0000A5FF,&H0000A5FF,0,0,0,0,100,100,1,0,3,14,0,8,40,40,400,1",
 "Style: Mark,Anton,30,&H80FFFFFF,&H80FFFFFF,&H80000000,&H00000000,0,0,0,0,100,100,3,0,1,3,0,3,40,50,715,1",
 "Style: Shape,Anton,20,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,0,0,7,0,0,0,1",
 "", "[Events]", "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text"]
def ev(a, b, st, text, layer=0): ass.append(f"Dialogue: {layer},{ts(a)},{ts(max(b, a + 0.05))},{st},,0,0,0,,{text}")
def flash(at): ev(at, at + 0.35, "Shape", r"{\an7\pos(0,0)\p1\bord0\shad0\1c&HFFFFFF&\alpha&H70&\t(0,330,\alpha&HFF&)}m 0 0 l 1080 0 1080 1920 0 1920{\p0}", 9)
def arrow(a, b, x, y, color="&H0000A5FF&", scale=55):
    ev(a, b, "Shape", r"{\an7\p1\bord0\shad0\1c" + color + rf"\fscx{scale}\fscy{scale}\move({x-70},{y},{x},{y},0,250)\t(250,{int(max(300,(b-a)*1000))},\fscx{scale+14}\fscy{scale+14})\fad(120,150)" + "}" + ARROW + r"{\p0}", 3)
ev(0, TOTAL, "Title", r"{\fad(300,0)}5 CURIOSIDADES DE GTA 6", 5)
ev(0, TOTAL, "Mark", "SECRETOS DE GTA", 1)
cur_num = None
for i, t in enumerate(tiempos):
    a, b = t["inicio"] + LEAD, t["fin"] + LEAD
    cs = chunks(t["texto"]); tot = sum(len(c) for c in cs); cur = a
    for c in cs:
        d = (b - a) * len(c) / tot
        ev(cur, cur + d, "Sub", r"{\fscx88\fscy88\t(0,130,\fscx104\fscy104)\t(130,230,\fscx100\fscy100)}" + hl(two_lines(c)), 4); cur += d
    nm = NUM.get(i)
    if nm and nm != cur_num:
        cur_num = nm; e = next((tiempos[j]["fin"] + LEAD for j in range(len(tiempos) - 1, -1, -1) if NUM.get(j) == nm), b)
        flash(a - 0.05); ev(a, e + 0.2, "Num", rf"{{\fad(100,150)\t(0,150,\fscx118\fscy118)\t(150,300,\fscx100\fscy100)}}#{nm}", 6)
mid = lambda t: (t["inicio"] + t["fin"]) / 2 + LEAD
def sticker(a, b, text): ev(a, b, "Sticker", rf"{{\fad(120,200)\move(540,330,540,400,0,230)\t(0,180,\fscx110\fscy110)\t(180,330,\fscx100\fscy100)}}{text}", 6)
sticker(tiempos[8]["inicio"] + LEAD + 0.1, tiempos[8]["fin"] + LEAD + 0.5, "26 MIN DE JUEGO OFICIAL")
sticker(tiempos[9]["inicio"] + LEAD + 0.1, mid(tiempos[9]), "SALE EL 19 NOV 2026")
sticker(mid(tiempos[9]), tiempos[9]["fin"] + LEAD + 0.4, "PRECARGA DESDE EL 10 NOV")
sticker(tiempos[10]["inicio"] + LEAD + 0.1, tiempos[10]["fin"] + LEAD + 0.5, "PC: SIN FECHA OFICIAL")
tcur = 0.0
for s in shots:
    s0, s1 = tcur, tcur + s["dur"]; tcur = s1
    if s["kind"] != "img": continue
    base = os.path.basename(s["src"])
    for pat, text in LABELS:
        if re.match(pat, base):
            a, b = s0 + 0.3, s1 - 0.1
            if b - a > 0.8:
                ev(a, b, "Tag", rf"{{\fad(120,150)\move(-500,1190,150,1190,0,260)}}{text}".replace("1190", "1190"), 7)
                arrow(a, b, 50, 1118)
            break
last = tiempos[-1]; a = last["inicio"] + LEAD
ev(a + 0.3, TOTAL - 0.1, "Sticker", r"{\an8\pos(540,420)\fad(200,300)\1c&HFFFFFF&\3c&H0000FF&\bord18\fscx130\fscy130\t(0,300,\fscx150\fscy150)\t(300,500,\fscx130\fscy130)}SÍGUEME", 6)
arrow(a + 0.3, TOTAL - 0.1, 270, 395, "&H0000FFFF&", 75)
open(f"{WK}/subs.ass", "w", encoding="utf8").write("\n".join(ass))

# música y efectos
SR = 44100
def save(path, x):
    st = np.stack([x, x], 1) if x.ndim == 1 else x
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(st, -1, 1) * 32767).astype(np.int16).tobytes())
N = int(TOTAL * SR); t = np.arange(N) / SR; rng = np.random.default_rng(9)
beat = 60 / 92.0
chords = [(220.0, 261.6, 329.6), (174.6, 220.0, 261.6), (261.6, 329.6, 392.0), (196.0, 246.9, 293.7)]
cl = beat * 8; L = np.zeros(N); R = np.zeros(N)
for k in range(int(TOTAL / cl) + 2):
    a_ = int(k * cl * SR); b_ = min(N, int((k + 1) * cl * SR + 1.0 * SR))
    if a_ >= N: break
    tt = t[a_:b_] - k * cl; ch = chords[k % 4]
    env = np.clip(tt / 0.8, 0, 1) * np.clip((cl + 1.0 - tt) / 1.0, 0, 1)
    pad = sum(np.sin(2 * np.pi * f * tt) + 0.4 * np.sin(2 * np.pi * f * 1.004 * tt) + 0.25 * np.sin(4 * np.pi * f * tt) for f in ch) * env
    L[a_:b_] += pad * 0.10 + np.sin(2 * np.pi * (ch[0] / 4) * tt) * env * 0.22; R[a_:b_] += pad * 0.09 + np.sin(2 * np.pi * (ch[0] / 4) * tt) * env * 0.22
for j, tk in enumerate(np.arange(0.0, TOTAL, beat / 2)):
    a_ = int(tk * SR); n = int(0.35 * SR)
    if a_ + n >= N: break
    tt = np.arange(n) / SR; ch = chords[int(tk // cl) % 4]
    if j % 2 == 0:
        kick = np.sin(2 * np.pi * (50 + 60 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 9) * 0.26; L[a_:a_ + n] += kick; R[a_:a_ + n] += kick
    else:
        hat = rng.standard_normal(n) * np.exp(-tt * 60) * 0.035; L[a_:a_ + n] += hat; R[a_:a_ + n] += hat
    f = ch[(j // 2) % 3] * 2; pl = np.sin(2 * np.pi * f * tt) * np.exp(-tt * 7) * 0.055; pan = 0.5 + 0.4 * math.sin(j)
    L[a_:a_ + n] += pl * (1 - pan); R[a_:a_ + n] += pl * pan
mus = np.stack([L, R], 1); mus /= np.abs(mus).max(); mus *= 0.6
save(f"{WK}/musica.wav", mus)
def whoosh(dur=0.7):
    n = int(dur * SR); x = rng.standard_normal(n); y = np.zeros(n); lp = 0.0
    for i in range(n):
        u = i / n; fc = 250 + 4500 * u; a_ = 1 - math.exp(-2 * math.pi * fc / SR); lp += a_ * (x[i] - lp); y[i] = lp
    return y * np.sin(np.pi * np.linspace(0, 1, n)) ** 2 * 1.2
def pop(dur=0.16):
    n = int(dur * SR); tt = np.arange(n) / SR
    return np.sin(2 * np.pi * (600 + 900 * tt / dur) * tt) * np.exp(-tt * 22) * 0.5
def impact(dur=1.5):
    n = int(dur * SR); tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * (45 + 80 * np.exp(-tt * 12)) * tt) * np.exp(-tt * 2.5) + rng.standard_normal(n) * np.exp(-tt * 14) * 0.2) * 0.8
sfx = np.zeros(N)
def put(x, at):
    a_ = int(at * SR); b_ = min(N, a_ + len(x))
    if 0 <= a_ < N: sfx[a_:b_] += x[:b_ - a_]
put(impact(), 0.05)
cur_num = None
for i, tt_ in enumerate(tiempos):
    nm = NUM.get(i)
    if nm and nm != cur_num: cur_num = nm; put(whoosh(0.6), tt_["inicio"] + LEAD - 0.55); put(pop(), tt_["inicio"] + LEAD)
for i in (8, 9, 10): put(pop(), tiempos[i]["inicio"] + LEAD + 0.1)
tcur = 0.0
for s in shots:
    s0 = tcur; tcur += s["dur"]
    if s["kind"] == "img" and any(re.match(p, os.path.basename(s["src"])) for p, _ in LABELS) and s["dur"] > 1.1: put(pop(0.13) * 0.7, s0 + 0.3)
put(pop(0.25), tiempos[-1]["inicio"] + LEAD + 0.3)
save(f"{WK}/sfx.wav", sfx * 0.7)

subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{P}/narracion_short.wav", "-i", f"{WK}/musica.wav", "-i", f"{WK}/sfx.wav", "-filter_complex",
  f"[0:a]aresample={SR},highpass=f=70,equalizer=f=180:t=h:w=150:g=2,equalizer=f=3500:t=h:w=1500:g=2.5,acompressor=threshold=0.1:ratio=3:attack=5:release=80,"
  f"loudnorm=I=-14:TP=-1.5:LRA=7,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},apad=whole_dur={TOTAL}[n];"
  f"[n]asplit[n1][n2];[1:a]aecho=0.8:0.85:70:0.3,volume=0.8[m];[m][n1]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[md];"
  f"[md][n2][2:a]amix=inputs=3:duration=first:normalize=0,alimiter=limit=0.95[a]",
  "-map", "[a]", "-t", f"{TOTAL:.2f}", "-ar", str(SR), f"{WK}/mezcla.wav"], check=True)
os.chdir(WK)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", "video_sin_audio.mp4", "-i", "mezcla.wav", "-vf", "ass=subs.ass", "-map", "0:v", "-map", "1:a",
  "-c:v", "libx264", "-preset", "medium", "-b:v", "5000k", "-maxrate", "7000k", "-bufsize", "10000k", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
  "-t", f"{TOTAL:.2f}", "-movflags", "+faststart", f"{WK}/gta6_short_curiosidades.mp4"], check=True)
print("LISTO", round(TOTAL, 1), "s", flush=True)
