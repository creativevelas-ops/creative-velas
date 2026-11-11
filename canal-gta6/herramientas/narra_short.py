import json, re, wave, sys, numpy as np
from kokoro_onnx import Kokoro
S="/tmp/claude-0/-home-user-creative-velas/836e68d2-3ca3-5ed0-bd33-fc0cebbfc14f/scratchpad"
P="/home/user/creative-velas/canal-gta6/short01"
LINES=[
 "¡Cinco curiosidades de GTA 6 que seguro no sabías!",
 "Uno: el juego pasa en Leonida, un estado inspirado en Florida, con Vice City como ciudad estrella.",
 "Dos: vas a poder alternar entre Jason y Lucía.",
 "Él viene del ejército, y ella acaba de salir de la cárcel. Sus caminos se cruzan y acaban metidos en una conspiración criminal.",
 "Tres: el mapa no es solo ciudad. Hay ambientes muy distintos, desde playas hasta pantanos y zonas rurales.",
 "Hay regiones como Leonida Keys, Port Gellhorn, Ambrosia, Grassrivers y el Parque Nacional Mount Kalaga.",
 "Cuatro: dentro del juego hay redes sociales ficticias, y un dúo musical llamado Real Dimez que intenta triunfar.",
 "Cinco: la música original es de Justice, con el tema Flower in a Hurricane.",
 "Y un extra: Rockstar ya ha enseñado unos 26 minutos de juego, grabados en PS5.",
 "Sale el 19 de noviembre en PS5 y Xbox Series X y S, y la precarga digital empezó el 10 de noviembre.",
 "De PC, por ahora, no hay fecha.",
 "¡Sígueme para más secretos de GTA 6 y dime cuál te ha flipado más!",
]
json.dump(LINES,open(f"{P}/guion_short.json","w"),ensure_ascii=False,indent=1)
k=Kokoro(f"{S}/models/kokoro-onnx.dl/kokoro-v1.0.onnx",f"{S}/models/kokoro-onnx.dl/voices-v1.0.bin")
REPL=[("Dre'Quan Priest","Drecuán Prist"),("Boobie Ike","Búbi Áik"),("Real Dimez","Ríal Dáimez"),("Bae-Luxe","Bei Lux"),
("Flower in a Hurricane","Fláuer in a Járriquein"),("Justice","Yástis"),("Leonida Keys","Leonida Quis"),("Port Gellhorn","Port Guélhorn"),
("Grassrivers","Grásrivers"),("Mount Kalaga","Maunt Kalaga"),("SECRETOS DE GTA","Secretos de gue te a"),("GTA 6","gue te a seis"),
("19 de noviembre","diecinueve de noviembre"),("10 de noviembre","diez de noviembre"),("26 minutos","veintiséis minutos"),("PS5","pe ese cinco"),("Xbox Series X y S","Equisbox Sirís Equis y Ese"),("PC","pe ce"),("Vice City","Váis Siti"),("Jason","Yéison")]
def tts_text(t):
    for a,b in REPL: t=t.replace(a,b)
    return re.sub(r"\b[A-ZÁÉÍÓÚÑ]{2,}\b",lambda m:m.group(0).lower(),t)
SPEED=float(sys.argv[1]) if len(sys.argv)>1 else 1.12
sr=24000; out=[]; timing=[]; t=0.0
for line in LINES:
    sp=SPEED*(1.06 if line.endswith("!") else 1.0)
    x,_=k.create(tts_text(line),voice="em_alex",speed=sp,lang="es"); x=np.asarray(x,dtype=np.float32)
    idx=np.where(np.abs(x)>0.01)[0]
    if len(idx): x=x[max(0,idx[0]-int(0.03*sr)):idx[-1]+int(0.06*sr)]
    d=len(x)/sr; timing.append({"texto":line,"inicio":round(t,2),"fin":round(t+d,2)}); out.append(x); t+=d
    g=0.22; out.append(np.zeros(int(sr*g),dtype=np.float32)); t+=g
a=np.concatenate(out)
with wave.open(f"{P}/narracion_short.wav","wb") as w:
    w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes((np.clip(a,-1,1)*32767).astype(np.int16).tobytes())
json.dump(timing,open(f"{P}/tiempos_short.json","w"),ensure_ascii=False,indent=1)
print("duración",round(t,1),"s")
