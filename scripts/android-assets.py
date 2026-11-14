"""Android launcher icons, TV banner and splash screens from the game's own icon and menu art.
usage: python3 scripts/android-assets.py   (run after `npx cap add android`)"""
import glob, os
from PIL import Image, ImageDraw, ImageFilter
RES = 'android/app/src/main/res'
icon = Image.open('public/icon-512.png').convert('RGBA')
sizes = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
for d, s in sizes.items():
    icon.resize((s, s), Image.LANCZOS).save(f'{RES}/mipmap-{d}/ic_launcher.png')
    m = Image.new('L', (s, s), 0); ImageDraw.Draw(m).ellipse((0, 0, s - 1, s - 1), fill=255)
    r = icon.resize((s, s), Image.LANCZOS); r.putalpha(m); r.save(f'{RES}/mipmap-{d}/ic_launcher_round.png')
    f = int(s * 108 / 48); fg = Image.new('RGBA', (f, f), (0, 0, 0, 0)); inner = int(f * 66 / 108)
    fg.alpha_composite(icon.resize((inner, inner), Image.LANCZOS), ((f - inner) // 2, (f - inner) // 2)); fg.save(f'{RES}/mipmap-{d}/ic_launcher_foreground.png')
open(f'{RES}/values/ic_launcher_background.xml', 'w').write('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#14100C</color>\n</resources>\n')
# Android TV launcher banner (320x180)
bg = Image.new('RGB', (320, 180), (20, 16, 12)); art = icon.resize((150, 150), Image.LANCZOS)
glow = Image.new('RGBA', (320, 180), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse((70, 0, 250, 180), fill=(214, 168, 72, 90)); bg.paste(glow.filter(ImageFilter.GaussianBlur(25)), (0, 0), glow.filter(ImageFilter.GaussianBlur(25)))
bg.paste(art, (85, 15), art); bg.save(f'{RES}/drawable/banner.png')
# splash: game icon centred on the dark background
for p in glob.glob(f'{RES}/drawable*/splash.png'):
    w, h = Image.open(p).size; sp = Image.new('RGB', (w, h), (20, 16, 12)); s = int(min(w, h) * .38)
    a = icon.resize((s, s), Image.LANCZOS); sp.paste(a, ((w - s) // 2, (h - s) // 2), a); sp.save(p)
print('android assets done')
