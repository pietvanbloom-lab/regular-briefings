#!/usr/bin/env python3
"""Render the Top 3 + TL;DR of a daily AI brief to an MP3 using Google Cloud
Chirp 3 HD text-to-speech, then inject an <audio> player into the brief HTML.

Usage:  tts.py <YYYY-MM-DD>
Reads:  briefs/<DATE>.html
Writes: briefs/audio/<DATE>.mp3  and injects a player into briefs/<DATE>.html

Credential (local only, never committed): the Google Cloud API key is read from
the env var GCP_TTS_API_KEY, else from ~/.config/ai-brief/gcp-tts.key.
If no key is found, the script prints a notice and exits 0 so the daily deploy
continues without audio.
"""
import sys, os, re, json, base64, html as htmlmod, urllib.request, urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE = "en-US-Chirp3-HD-Charon"   # swap to taste, e.g. -Kore, -Aoede, -Puck, -Leda
LANG = "en-US"
SITE = "https://pietvanbloom-lab.github.io/regular-briefings"
MAX_BYTES = 4500                    # stay under the 5000-byte synth request limit
BYTES_PER_SEC = 4000               # 32 kbps MP3 = 4000 bytes/sec, for duration estimate

def get_key():
    k = os.environ.get("GCP_TTS_API_KEY", "").strip()
    if k:
        return k
    path = os.path.expanduser("~/.config/ai-brief/gcp-tts.key")
    if os.path.exists(path):
        return open(path, encoding="utf-8").read().strip()
    return ""

def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return htmlmod.unescape(re.sub(r"\s+", " ", s)).strip()

MONTHS = ["January","February","March","April","May","June","July","August",
          "September","October","November","December"]
def human_date(d):
    y, m, day = d.split("-")
    return f"{MONTHS[int(m)-1]} {int(day)}, {y}"

WORDNUM = ["one","two","three","four","five","six"]

def extract_script(raw, d):
    mtop = re.search(r'<div class="top3">(.*?)(?:<h2|<div class="bucket")', raw, re.S)
    if not mtop:
        return ""
    block = mtop.group(1)
    parts = [f"Your AI intelligence brief for {human_date(d)}. Here are today's top three signals."]
    n = 0
    for cm in re.finditer(r'<div class="card[^"]*"[^>]*>(.*?)(?=<div class="card|\Z)', block, re.S):
        card = cm.group(1)
        h3 = re.search(r"<h3[^>]*>(.*?)</h3>", card, re.S)
        if not h3:
            continue
        headline = strip_tags(h3.group(1))
        summary = ""
        for pm in re.finditer(r'<p( [^>]*)?>(.*?)</p>', card, re.S):
            attrs = pm.group(1) or ""
            if "meta" in attrs:
                continue
            summary = strip_tags(pm.group(2))
            break
        why = re.search(r'<div class="why">(.*?)</div>', card, re.S)
        why_txt = strip_tags(why.group(1)) if why else ""
        n += 1
        seg = f"Number {WORDNUM[n-1]}. {headline}. {summary}"
        if why_txt:
            seg += " " + why_txt
        parts.append(seg)
    parts.append("That's the top three. The full brief, with all of today's items, is on the dashboard.")
    return "\n\n".join(parts)

def chunk(text, limit=MAX_BYTES):
    out, cur = [], ""
    for sent in re.split(r'(?<=[.!?])\s+', text):
        cand = (cur + " " + sent).strip()
        if len(cand.encode("utf-8")) > limit and cur:
            out.append(cur.strip()); cur = sent
        else:
            cur = cand
    if cur.strip():
        out.append(cur.strip())
    return out

def synth(text, key):
    url = "https://texttospeech.googleapis.com/v1/text:synthesize?key=" + key
    body = json.dumps({
        "input": {"text": text},
        "voice": {"languageCode": LANG, "name": VOICE},
        "audioConfig": {"audioEncoding": "MP3"},
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        resp = json.loads(r.read().decode("utf-8"))
    return base64.b64decode(resp["audioContent"])

def fmt_duration(nbytes):
    secs = max(1, round(nbytes / BYTES_PER_SEC))
    mins = max(1, round(secs / 60))
    return f"about {mins} minute" + ("" if mins == 1 else "s")

LISTEN_RE = re.compile(r'<div class="listen".*?</audio>\s*</div>\s*', re.S)
def player_block(d, label):
    src = f"{SITE}/briefs/audio/{d}.mp3"
    return (
      '<div class="listen" style="background:#14161c;border:1px solid #262a33;'
      'border-left:3px solid #6db4ff;border-radius:4px;padding:12px 16px;margin:0 0 24px;'
      'display:flex;align-items:center;justify-content:space-between;gap:14px;flex-wrap:wrap;">'
      '<div style="display:flex;flex-direction:column;gap:2px;">'
      '<span style="font-family:ui-monospace,monospace;font-size:11px;letter-spacing:0.08em;'
      'text-transform:uppercase;color:#8a8f9a;">Audio edition</span>'
      f'<span style="font-size:14px;color:#e7e9ef;">Listen: Top 3 and TL;DR, {label}</span>'
      '</div>'
      f'<audio controls preload="none" src="{src}" style="height:36px;max-width:340px;width:100%;">'
      'Your browser does not support audio playback.</audio>'
      '</div>'
    )

def inject_player(raw, d, label):
    raw = LISTEN_RE.sub("", raw)  # remove any prior player so re-runs update the label
    blk = player_block(d, label)
    if "</header>" in raw:
        return raw.replace("</header>", "</header>\n\n" + blk, 1)
    return raw

def main():
    if len(sys.argv) != 2 or not re.match(r"^\d{4}-\d{2}-\d{2}$", sys.argv[1]):
        print("usage: tts.py <YYYY-MM-DD>"); sys.exit(1)
    d = sys.argv[1]
    brief_path = os.path.join(ROOT, "briefs", d + ".html")
    if not os.path.exists(brief_path):
        print("TTS: no brief at", brief_path); sys.exit(1)
    key = get_key()
    if not key:
        print("TTS: no API key (GCP_TTS_API_KEY or ~/.config/ai-brief/gcp-tts.key); skipping audio.")
        sys.exit(0)
    raw = open(brief_path, encoding="utf-8").read()
    script = extract_script(raw, d)
    if not script:
        print("TTS: could not extract Top 3; skipping audio."); sys.exit(0)
    try:
        audio = b"".join(synth(c, key) for c in chunk(script))
    except urllib.error.HTTPError as e:
        print("TTS: API error", e.code, e.read().decode("utf-8", "ignore")[:400]); sys.exit(0)
    except Exception as e:
        print("TTS: failed", repr(e)); sys.exit(0)
    audio_dir = os.path.join(ROOT, "briefs", "audio")
    os.makedirs(audio_dir, exist_ok=True)
    out = os.path.join(audio_dir, d + ".mp3")
    open(out, "wb").write(audio)
    label = fmt_duration(len(audio))
    new_raw = inject_player(raw, d, label)
    if new_raw != raw:
        open(brief_path, "w", encoding="utf-8").write(new_raw)
    print(f"TTS: wrote {out} ({len(audio)//1024} KB, {label}), voice {VOICE}, {len(script)} chars, player injected.")

if __name__ == "__main__":
    main()
