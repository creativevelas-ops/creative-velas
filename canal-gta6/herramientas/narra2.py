import json, re, wave, sys, numpy as np
from kokoro_onnx import Kokoro
S="/tmp/claude-0/-home-user-creative-velas/836e68d2-3ca3-5ed0-bd33-fc0cebbfc14f/scratchpad"
P="/home/user/creative-velas/canal-gta6/video01"
k=Kokoro(f"{S}/models/kokoro-onnx.dl/kokoro-v1.0.onnx",f"{S}/models/kokoro-onnx.dl/voices-v1.0.bin")
VOICE=sys.argv[1] if len(sys.argv)>1 else "em_alex"
SPEED=float(sys.argv[2]) if len(sys.argv)>2 else 1.08
REPL=[("Dre'Quan Priest","Drecuán Prist"),("Boobie Ike","Búbi Áik"),("Real Dimez","Ríal Dáimez"),("Bae-Luxe","Bei Lux"),("Raul Bautista","Raúl Bautista"),
("Cal Hampton","Cal Jámpton"),("Flower in a Hurricane","Fláuer in a Járriquein"),("Justice","Yástis"),("Leonida Keys","Leonida Quis"),("Port Gellhorn","Port Guélhorn"),
("Grassrivers","Grásrivers"),("Mount Kalaga","Maunt Kalaga"),("Grand Theft Auto","Grand Zeft Ótou"),("SECRETOS DE GTA","Secretos de gue te a"),("GTA 6","gue te a seis"),
("PlayStation 5","PleiStéishon cinco"),("Xbox Series X y Series S","Equisbox Sirís Equis y Sirís Ese"),("Rockstar Games","Rocstar Géimz"),("Rockstar","Rocstar"),
("19 de noviembre de 2026","diecinueve de noviembre de dos mil veintiséis"),("10 de noviembre","diez de noviembre"),("19 de noviembre","diecinueve de noviembre"),
("Vice City","Váis Siti"),("hype","jáip"),("PC","pe ce"),("online","onlain"),("Jason","Yéison"),("Duval","Duvál")]
def tts_text(t):
    for a,b in REPL: t=t.replace(a,b)
    t=re.sub(r"\b[A-ZÁÉÍÓÚÑ]{2,}\b",lambda m:m.group(0).lower(),t)
    return t
sec=None; out=[]; timing=[]; t=0.0; sr=24000
def pause(s):
    global t; out.append(np.zeros(int(sr*s),dtype=np.float32)); t+=s
for line in open(f"{P}/guion_youtuber.txt",encoding="utf8"):
    line=line.strip()
    if not line: continue
    if line.startswith("## "): sec=line[3:]; pause(0.7); continue
    sp=SPEED*(1.06 if line.endswith("!") else 1.0)
    x,_=k.create(tts_text(line),voice=VOICE,speed=sp,lang="es")
    x=np.asarray(x,dtype=np.float32)
    # recorte de silencios largos al inicio/fin
    thr=0.01; idx=np.where(np.abs(x)>thr)[0]
    if len(idx): x=x[max(0,idx[0]-int(0.03*sr)):idx[-1]+int(0.08*sr)]
    d=len(x)/sr; timing.append({"seccion":sec,"texto":line,"inicio":round(t,2),"fin":round(t+d,2)})
    out.append(x); t+=d; pause(0.55 if line.endswith("?") else 0.32)
a=np.concatenate(out)
with wave.open(f"{P}/narracion_youtuber.wav","wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(a,-1,1)*32767).astype(np.int16).tobytes())
json.dump(timing,open(f"{P}/tiempos_youtuber.json","w"),ensure_ascii=False,indent=1)
print("duración",round(t/60,2),"min",len(timing),"líneas")
