"""Build compact production markup and an offline preview."""
from pathlib import Path
from base64 import b64encode
from datetime import datetime, timezone
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
logo_source = (ROOT / 'assets/gta-vi-logo-original.svg').read_text(encoding='utf-8')
logo_mono = re.sub(r'stop-color:#[0-9A-Fa-f]{6}', 'stop-color:#000000', logo_source)
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
.gta-logo { position: absolute; left: 44px; top: 40px; width: 210px; height: auto; max-width: none; filter: drop-shadow(1px 0 0 white) drop-shadow(-1px 0 0 white) drop-shadow(0 1px 0 white) drop-shadow(0 -1px 0 white); }
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
logo = '<img class="gta-logo image" src="https://raw.githubusercontent.com/lerston/trmnl-gta-countdown/main/assets/gta-vi-logo-mono.svg" alt="Grand Theft Auto VI">'
markup = logic + production_style + '<div class="gta-frame">\n' + choices + '\n' + number + '\n' + logo + '\n</div>'
assert len(markup.encode('utf-8')) < 100_000, 'TRMNL Full markup must be less than 100 KB'
assert 'base64' not in markup
(ROOT / 'full.liquid').write_text(markup, encoding='utf-8')
preview = '<!doctype html><meta charset="utf-8"><title>GTA VI — preview</title>' + style
preview += '<style>body{margin:24px;background:#444;color:white;font:16px sans-serif} input{font:inherit;width:90px} .gta-frame{margin-top:16px}</style>'
preview += '<label>Проверить число: <input id="days" type="number" min="0" max="999" value="83"></label>'
local_logo = logo.replace('https://raw.githubusercontent.com/lerston/trmnl-gta-countdown/main/assets/gta-vi-logo-mono.svg', 'data:image/svg+xml;base64,' + b64encode(logo_mono.encode()).decode())
preview += '<div class="gta-frame"><img class="gta-art" src="' + images[0] + '" alt="">' + number.replace('{{ days_left }}', '83') + local_logo + '</div>'
preview += '<p>Предпросмотр в оттенках серого. Дизеринг выполняет сервер TRMNL; здесь он не показан.</p><script>document.getElementById("days").addEventListener("input",e=>{document.querySelectorAll(".gta-number text").forEach(t=>t.textContent=Math.max(0,Math.min(999,Math.floor(Number(e.target.value)||0))))});</script>'
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
print(f'Built template with {len(arts)} image(s). Six date boundary checks passed.')
print(f'Template size: {(ROOT / "full.liquid").stat().st_size:,} bytes')
