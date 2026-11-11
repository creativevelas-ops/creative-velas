import glob, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
RS="/tmp/claude-0/-home-user-creative-velas/836e68d2-3ca3-5ed0-bd33-fc0cebbfc14f/scratchpad/rs/img"
P="/home/user/creative-velas/canal-gta6/video01"
src=glob.glob(f"{RS}/Jason_Lucia_Rooftop_landscape*.jpg")[0]
W,H=1280,720
im=Image.open(src).convert("RGB"); r=max(W/im.width,H/im.height)
im=im.resize((int(im.width*r),int(im.height*r)),Image.LANCZOS); im=im.crop(((im.width-W)//2,(im.height-H)//2,(im.width-W)//2+W,(im.height-H)//2+H))
# degradado rosa -> morado a la izquierda y viñeta
ov=Image.new("RGB",(W,H)); px=ov.load()
for x in range(W):
    for y in range(0,H):
        u=x/W; a=max(0,1-u*1.5)
        px[x,y]=(int((255*(1-y/H)+110*(y/H))*a),int((40)*a),int((190+40*(y/H))*a))
im=ImageChops.add(ImageChops.multiply(im,Image.new("RGB",(W,H),(215,200,235))),ov.point(lambda v:int(v*0.55)))
fb="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def txt(text,size,xy,fill,glow):
    f=ImageFont.truetype(fb,size); g=Image.new("RGB",(W,H)); gd=ImageDraw.Draw(g)
    gd.text(xy,text,font=f,fill=glow,stroke_width=10,stroke_fill=glow)
    gg=g.filter(ImageFilter.GaussianBlur(18)); return f,gg
img=im
for text,size,xy,fill,glow in [("GTA 6:",190,(50,70),(255,255,255),(255,60,200)),("QUEDAN",150,(50,290),(255,255,255),(160,60,255)),("8 DÍAS",190,(50,430),(255,240,120),(255,60,160))]:
    f,gg=txt(text,size,xy,fill,glow); img=ImageChops.add(img,gg)
    d=ImageDraw.Draw(img); d.text(xy,text,font=f,fill=fill,stroke_width=8,stroke_fill=(20,0,40))
d=ImageDraw.Draw(img); f=ImageFont.truetype(fb,34); d.rectangle([40,H-70,420,H-22],fill=(190,20,120)); d.text((55,H-65),"SECRETOS DE GTA",font=f,fill=(255,255,255))
img.save(f"{P}/portada.jpg",quality=90); print(os.path.getsize(f"{P}/portada.jpg")//1024,"KB")
