#!/usr/bin/env python3
import os, glob
HERE = os.path.dirname(os.path.abspath(__file__))
CURRENT = 'Aoede'
EXCERPT = (
  "Your AI intelligence brief for June 19, 2026. Today's top signal: "
  "Alibaba's Qwen team shipped the Qwen-Robot Suite, its first robotics "
  "foundation-model stack, with separate models for navigation, manipulation, "
  "and world prediction. Qwen-RobotManip was trained on more than 38,000 hours "
  "of robot and human demonstration data, and Qwen-RobotWorld predicts the "
  "outcome of actions before they run. This moves Alibaba from a pure language "
  "lab into embodied, physical AI."
)
voices = sorted(os.path.basename(p)[5:-4] for p in glob.glob(os.path.join(HERE,'demo-*.mp3')))
cards = []
for v in voices:
    badge = '<span class="badge">brief voice</span>' if v == CURRENT else ''
    cards.append(
      f'<div class="card{" cur" if v==CURRENT else ""}"><div class="vn">{v}{badge}</div>'
      f'<div class="fn">en-US-Chirp3-HD-{v}</div>'
      f'<audio controls preload="none" src="demo-{v}.mp3"></audio></div>'
    )
html = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>AI Brief voice selector</title><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{--bg:#0b0c0f;--panel:#14161c;--text:#e7e9ef;--mute:#8a8f9a;--line:#262a33;--accent2:#6db4ff;--good:#3fb95d}
*{box-sizing:border-box}body{background:var(--bg);color:var(--text);margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,sans-serif;line-height:1.5}
.wrap{max-width:1100px;margin:0 auto;padding:28px 24px 80px}
.eyebrow{font-family:ui-monospace,monospace;font-size:11px;letter-spacing:.12em;text-transform:uppercase;color:var(--mute)}
h1{font-family:Georgia,serif;font-size:26px;margin:4px 0 6px}
.excerpt{background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--accent2);border-radius:4px;padding:14px 16px;margin:16px 0 24px;font-size:14px;color:#d2d5dc;font-style:italic}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:14px 16px}
.card.cur{border-color:var(--good)}
.vn{font-size:16px;font-weight:600;display:flex;align-items:center;gap:8px}
.fn{font-family:ui-monospace,monospace;font-size:11px;color:var(--mute);margin:2px 0 10px}
.badge{font-family:ui-monospace,monospace;font-size:9px;letter-spacing:.06em;text-transform:uppercase;color:var(--good);border:1px solid var(--good);border-radius:3px;padding:1px 6px}
audio{width:100%;height:36px}
.meta{font-family:ui-monospace,monospace;font-size:11px;color:var(--mute);margin-top:24px}
</style></head><body><div class="wrap">
<div class="eyebrow">AI Intelligence Brief</div>
<h1>Chirp 3 HD voice selector</h1>
<div class="excerpt">''' + EXCERPT + '''</div>
<div class="grid">''' + ''.join(cards) + '''</div>
<div class="meta">''' + str(len(voices)) + ''' voices, same excerpt from the 2026-06-19 brief, Google Cloud Chirp 3 HD, en-US. The brief currently uses Aoede.</div>
</div></body></html>'''
open(os.path.join(HERE,'index.html'),'w',encoding='utf-8').write(html)
print('wrote index.html,', len(voices),'voices, current', CURRENT)
