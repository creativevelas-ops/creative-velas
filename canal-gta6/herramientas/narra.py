import json, wave, glob, re, numpy as np
from piper import PiperVoice
S="/tmp/claude-0/-home-user-creative-velas/836e68d2-3ca3-5ed0-bd33-fc0cebbfc14f/scratchpad"
P="/home/user/creative-velas/canal-gta6/video01"
d="es_ES-davefx-medium"; base=glob.glob(f"{S}/models/vits-piper-{d}.dl/*")[0]
voice=PiperVoice.load(f"{base}/{d}.onnx",config_path=f"{base}/{d}.onnx.json")
from piper import SynthesisConfig
cfg=SynthesisConfig(length_scale=1.08)
sr=voice.config.sample_rate; out=[]; timing=[]; t=0.0; sec=None
def add(a): out.append(a)
for line in open(f"{P}/guion.txt",encoding="utf8"):
    line=line.strip()
    if not line: continue
    if line.startswith("## "):
        sec=line[3:]; pause=0.9; add(np.zeros(int(sr*pause),dtype=np.int16)); t+=pause; continue
    chunks=[]
    for c in voice.synthesize(line,syn_config=cfg): chunks.append(np.frombuffer(c.audio_int16_bytes,dtype=np.int16))
    a=np.concatenate(chunks); dur=len(a)/sr
    timing.append({"seccion":sec,"texto":line,"inicio":round(t,2),"fin":round(t+dur,2)})
    add(a); t+=dur
    p=0.45 if not line.endswith("?") else 0.6; add(np.zeros(int(sr*p),dtype=np.int16)); t+=p
a=np.concatenate(out)
with wave.open(f"{P}/narracion.wav","wb") as w: w.setnchannels(1);w.setsampwidth(2);w.setframerate(sr);w.writeframes(a.tobytes())
json.dump(timing,open(f"{P}/tiempos.json","w"),ensure_ascii=False,indent=1)
print("duración total", round(t/60,2),"min", "lineas",len(timing))
