"""Build compact production markup and an offline preview."""
from pathlib import Path
from base64 import b64encode
from datetime import datetime, timezone
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
logo_source = (ROOT / 'assets/gta-vi-logo-original.svg').read_text(encoding='utf-8')
texture_ids = []
for gradient in re.findall(r'<linearGradient\b.*?</linearGradient>', logo_source, re.S):
    if '#FF4CB9' in gradient and '#2B60DA' in gradient:
        texture_ids.append(re.search(r'id="([^"]+)"', gradient).group(1))
assert len(texture_ids) == 2, 'Expected the two original VI interior gradients'
# An ordered 1-bit pattern at one dot per final display pixel (logo width 210px).
# Only the VI interiors receive this texture; lettering, borders and palms stay solid.
bayer = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))
dot = 980 / 210
dots = []
for row in range(160):
    fraction = row / 159
    black_density = 0.78 - 0.98 * fraction if fraction < 0.5 else 0.29 + 0.58 * (fraction - 0.5)
    for col in range(4):
        if (bayer[row % 4][col] + 0.5) / 16 < black_density:
            dots.append(f'M{col*dot:.4f},{row*dot:.4f}h{dot:.4f}v{dot:.4f}h-{dot:.4f}z')
texture = (f'<defs><pattern id="gta-vi-dots" patternUnits="userSpaceOnUse" x="10" y="28.01" width="{4*dot:.4f}" height="{160*dot:.4f}">'
           f'<rect width="100%" height="100%" fill="white"/><path fill="black" d="{"".join(dots)}"/></pattern></defs>')
logo_mono = re.sub(r'stop-color:#[0-9A-Fa-f]{6}', 'stop-color:#000000', logo_source)
for texture_id in texture_ids:
    logo_mono = logo_mono.replace('fill:url(#' + texture_id + ')', 'fill:url(#gta-vi-dots)')
logo_mono = logo_mono.replace('</svg>', texture + '</svg>')
logo_mono = logo_mono.replace('#1D0030', '#000000').replace('#FF2B90', '#FFFFFF')
ET.fromstring(logo_mono)
(ROOT / 'assets/gta-vi-logo-mono.svg').write_text(logo_mono, encoding='utf-8')
font = b64encode((ROOT / 'assets/Montserrat-ExtraBold.woff2').read_bytes()).decode()
arts = sorted((ROOT / 'assets').glob('art-*.png'))
assert arts, 'Add at least one art-*.png'
images = ['data:image/png;base64,' + b64encode(p.read_bytes()).decode() for p in arts]
target_day = int(datetime(2026, 11, 19, tzinfo=timezone.utc).timestamp()) // 86400
logic = '''{% liquid
  assign moscow_seconds = 'now' | date: '%s' | plus: 10800
  assign day_number = moscow_seconds | divided_by: 86400
  assign days_left = TARGET_DAY | minus: day_number | at_least: 0
  assign random_value = day_number | times: 48271 | modulo: 2147483647
  assign random_value = random_value | times: random_value | modulo: 2147483647
  assign art_count = artworks | size
  if art_count > 0
    assign art_index = random_value | modulo: art_count
  endif
%}
'''.replace('TARGET_DAY', str(target_day))
style = '''<style>
@font-face { font-family: GTA-Montserrat; src: url(data:font/woff2;base64,FONT) format('woff2'); font-weight: 800; font-style: normal; font-display: block; }
.gta-frame { position: relative; width: 800px; height: 480px; flex: none; padding: 0; margin: 0; overflow: hidden; background: white; }
.gta-art { position: absolute; inset: 0; width: 800px; height: 480px; max-width: none; object-fit: cover; filter: grayscale(1); }
.gta-number { position: absolute; inset: 0; width: 800px; height: 480px; overflow: hidden; }
.gta-logo { position: absolute; left: 56px; top: 48px; width: 210px; height: auto; max-width: none; filter: drop-shadow(1px 0 0 white) drop-shadow(-1px 0 0 white) drop-shadow(0 1px 0 white) drop-shadow(0 -1px 0 white); }
.gta-number text { font-family: GTA-Montserrat; font-size: 180px; font-weight: 800; font-variant-numeric: tabular-nums; letter-spacing: 0; stroke: black; stroke-width: 8px; stroke-linejoin: round; paint-order: stroke fill; }
</style>
'''.replace('FONT', font)
# SVG paint-order covers the inner half of an 8px stroke: 4px visible outside.
# Both layers share x and baseline; shadow is translated down exactly 10px.
number = '''<svg class="gta-number" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 480" aria-label="Days until GTA VI: {{ days_left }}">
  <text x="50" y="426" fill="black">{{ days_left }}</text>
  <text x="50" y="416" fill="white">{{ days_left }}</text>
</svg>'''
font_url = 'https://raw.githubusercontent.com/lerston/trmnl-gta-countdown/main/assets/Montserrat-ExtraBold.woff2'
production_style = style.replace('data:font/woff2;base64,' + font, font_url)
choices = '''{% if art_count > 0 %}
<img class="gta-art image image-dither" src="{{ artworks[art_index] | escape }}" alt="">
{% else %}
<p style="position:absolute;top:24px;left:24px;color:black;font:20px sans-serif">Add image HTTPS URLs to Static Data: artworks</p>
{% endif %}'''
logo = '<img class="gta-logo image" src="https://raw.githubusercontent.com/lerston/trmnl-gta-countdown/main/assets/gta-vi-logo-mono.svg?v=2" alt="Grand Theft Auto VI">'
markup = logic + production_style + '<div class="gta-frame">\n' + choices + '\n' + number + '\n' + logo + '\n</div>'
assert len(markup.encode('utf-8')) < 100_000, 'TRMNL Full markup must be less than 100 KB'
assert 'base64' not in markup
(ROOT / 'full.liquid').write_text(markup, encoding='utf-8')
preview = '<!doctype html><meta charset="utf-8"><title>GTA VI — preview</title>' + style
preview += '<style>body{margin:24px;background:#444;color:white;font:16px sans-serif} input{font:inherit;width:90px} .gta-frame{margin-top:16px}</style>'
preview += '<label>Проверить число: <input id="days" type="number" min="0" max="999" value="83"></label>'
preview += '<label> Фон: <select id="art-picker">' + ''.join(f'<option value="{i}">{p.stem}</option>' for i, p in enumerate(arts)) + '</select></label>'
local_logo = logo.replace('https://raw.githubusercontent.com/lerston/trmnl-gta-countdown/main/assets/gta-vi-logo-mono.svg?v=2', 'data:image/svg+xml;base64,' + b64encode(logo_mono.encode()).decode())
preview += '<div class="gta-frame"><img class="gta-art" src="' + images[0] + '" alt="">' + number.replace('{{ days_left }}', '83') + local_logo + '</div>'
preview += '<p>Предпросмотр в оттенках серого. Дизеринг выполняет сервер TRMNL; здесь он не показан.</p><script>document.getElementById("days").addEventListener("input",e=>{document.querySelectorAll(".gta-number text").forEach(t=>t.textContent=Math.max(0,Math.min(999,Math.floor(Number(e.target.value)||0))))});</script>'
preview += '<script>document.getElementById("art-picker").addEventListener("change",e=>{document.querySelector(".gta-art").src="assets/art-"+String(Number(e.target.value)+1).padStart(2,"0")+".png"});</script>'
(ROOT / 'preview.html').write_text(preview, encoding='utf-8')

def days_at(iso):
    stamp = datetime.fromisoformat(iso).timestamp()
    return max(0, target_day - int((stamp + 10800) // 86400))

assert days_at('2026-08-28T12:00:00+03:00') == 83
assert days_at('2026-11-18T23:59:59+03:00') == 1
assert days_at('2026-11-19T00:00:00+03:00') == 0
assert days_at('2026-11-20T00:00:00+03:00') == 0
assert days_at('2026-08-28T20:59:59+00:00') == 83
assert days_at('2026-08-28T21:00:00+00:00') == 82

def art_at(iso, count):
    if count == 0:
        return None
    day = int((datetime.fromisoformat(iso).timestamp() + 10800) // 86400)
    value = day * 48271 % 2147483647
    return (value * value % 2147483647) % count

for count in (1, 2, 3, 4, 10):
    early = art_at('2026-08-28T00:00:00+03:00', count)
    late = art_at('2026-08-28T23:59:59+03:00', count)
    assert early == late and 0 <= early < count
    indices = [art_at(f'2026-09-{day:02d}T12:00:00+03:00', count) for day in range(1, 29)]
    assert all(0 <= index < count for index in indices)
    if count > 1:
        assert len(set(indices)) > 1
assert art_at('2026-08-28T12:00:00+03:00', 0) is None
for day in range(28, 32):
    iso = f'2026-08-{day:02d}T12:00:00+03:00'
    print(f'{iso[:10]}: art-{art_at(iso, len(arts))+1:02d}')
print('Rotation arithmetic checked for 0, 1, 2, 3, 4 and 10 artworks; real multi-art rendering still requires supplied assets.')
print(f'Built template with {len(arts)} image(s). Six date boundary checks passed.')
print(f'Template size: {(ROOT / "full.liquid").stat().st_size:,} bytes')
