from pathlib import Path
from PIL import Image
import csv,json,shutil
root=Path(__file__).resolve().parents[2];source=Path('/workspace/scratch/d96bc0fd2488/original-assets/decoded');out=root/'public/assets/original/ui-v7';out.mkdir(parents=True,exist_ok=True);manifest={}
def save(name,file,box=None):
 p=source/file;im=Image.open(p).convert('RGBA');im=im.crop(box) if box else im;im.save(out/(name+'.webp'),lossless=True);manifest[name]={'source':file,'crop':box,'size':im.size}
for name,file in [('menu-background','GUI/MenuBackground.webp'),('parchment-panel','GUI/Popupbackground.webp'),('arena-floor','Arenas/Arena_01/CM_lava_floor_01.webp')]:save(name,file)
for name,b in {'button-purple':(0,326,400,422),'button-silver':(416,328,810,422),'wordmark':(278,690,545,788),'chests':(9,434,218,568),'pointing-hand':(133,696,255,803),'arrow-left':(347,554,470,674),'arrow-right':(476,554,601,674)}.items():save(name,'GUI/ButtonBits2.webp',b)
for name,b in {'singleplayer-art':(20,0,202,202),'skirmish-art':(820,0,1002,212),'solo-quests-art':(621,0,804,209),'ribbon-purple':(0,612,684,731),'ribbon-orange':(0,736,684,855)}.items():save(name,'GUI/ButtonBits3.webp',b)
for name,b in {'coin':(673,334,753,414),'icon-cards':(0,81,82,163),'icon-shop':(167,164,246,246),'icon-settings':(924,81,1003,163),'icon-back':(0,248,80,330),'icon-check':(0,164,80,246),'icon-close':(82,248,163,330),'icon-trophy':(82,583,163,664),'icon-play':(924,164,1003,246),'rarity-common':(43,4,66,34),'rarity-uncommon':(84,4,108,34),'rarity-rare':(123,4,146,34),'rarity-legendary':(204,4,228,34)}.items():save(name,'GUI/icons.webp',b)
for r in csv.DictReader(open(root/'reference/native-rules/table-341b48.txt')):
 id=r['eAbilityType enum'];icon=r.get('Icon','')
 if not id or id=='AT_NONE' or '*' not in icon:continue
 n=int(icon.split('*')[1]);save('ability-'+id,'GUI/AssortedIcons1.webp',((n%8)*128,(n//8)*128,(n%8+1)*128,(n//8+1)*128))
(out/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Extracted',len(manifest),'native UI crops')
