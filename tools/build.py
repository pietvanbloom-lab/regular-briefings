#!/usr/bin/env python3
"""Parse archived AI briefs (editorial HTML) into a structured data index for the portal."""
import re, json, os, glob, html as htmlmod
from collections import Counter, defaultdict
from datetime import datetime, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "briefs")
OUT = os.path.join(ROOT, "data", "briefs.json")
HUB = os.path.join(ROOT, "archive.html")

def strip_tags(s):
    s = re.sub(r"<[^>]+>", "", s)
    return htmlmod.unescape(s).strip()

TOPICS = {
    "Anthropic": r"anthropic|claude|opus|sonnet|haiku|mythos|fable",
    "OpenAI": r"openai|chatgpt|\bgpt-?\d|sam altman",
    "Google / DeepMind": r"google|deepmind|gemini",
    "Nvidia": r"nvidia|\bcuda\b|blackwell|\bgpu\b",
    "MCP / Agents": r"\bmcp\b|model context protocol|agent(ic|s)?\b|tool use",
    "xAI / Grok": r"\bxai\b|grok",
    "Meta": r"\bmeta\b|llama",
    "Mistral": r"mistral",
    "DeepSeek": r"deepseek",
    "Microsoft": r"microsoft|copilot|azure",
    "Amazon / AWS": r"amazon|\baws\b|bedrock|trainium",
    "Coding tools": r"cursor|windsurf|codex|coding",
    "Funding / M&A": r"funding|raise[sd]?|valuation|\bipo\b|acqui|\$\d",
    "Open source": r"open[- ]?source|open[- ]?weight|hugging ?face",
    "Regulation": r"regulat|export[- ]control|white house|eu ai act|lawsuit|\bban\b|order",
    "Robotics": r"robot|humanoid|figure ai|tesla bot",
    "Chips / Compute": r"\bchip|semiconductor|data ?cent|compute deal|tpu|wafer",
}

def topic_hits(text):
    t = text.lower()
    return [label for label, pat in TOPICS.items() if re.search(pat, t)]

def parse_brief(path):
    raw = open(path, encoding="utf-8").read()
    fname = os.path.basename(path)
    d = re.search(r"(\d{4}-\d{2}-\d{2})", fname).group(1)

    top3 = []
    mtop = re.search(r'<div class="top3">(.*?)(?:<h2|<div class="bucket")', raw, re.S)
    top_block = mtop.group(1) if mtop else ""
    for cm in re.finditer(r'<div class="card([^"]*)">(.*?)(?=<div class="card|\Z)', top_block, re.S):
        cls, card = cm.group(1), cm.group(2)
        h3 = re.search(r"<h3[^>]*>(.*?)</h3>", card, re.S)
        if not h3:
            continue
        tags = [strip_tags(t) for t in re.findall(r'<span class="tag[^"]*">(.*?)</span>', card, re.S)]
        why = re.search(r'<(?:div|p) class="why">(.*?)</(?:div|p)>', card, re.S)
        topic = ""
        for t in tags:
            tl = t.lower()
            if "tier" in tl or "confidence" in tl or tl == "early":
                continue
            topic = t
        top3.append({
            "headline": strip_tags(h3.group(1)),
            "tags": tags, "topic": topic,
            "early": ("early" in cls.lower()) or any(t.lower() == "early" for t in tags),
            "why": strip_tags(why.group(1)) if why else "",
        })

    buckets = []
    item_headlines = []
    total_items = 0
    for bm in re.finditer(r'<div class="bucket">(.*?)(?=<div class="bucket">|<h2|<div class="footer|\Z)', raw, re.S):
        b = bm.group(1)
        name_m = re.search(r'<div class="eyebrow">(.*?)</div>', b, re.S)
        name = strip_tags(name_m.group(1)) if name_m else "Other"
        items = re.findall(r'<div class="item[^"]*">(.*?)</div>', b, re.S)
        hs = []
        for it in items:
            h4 = re.search(r"<h4[^>]*>(.*?)</h4>", it, re.S)
            if h4:
                hs.append(strip_tags(h4.group(1))); item_headlines.append(strip_tags(h4.group(1)))
        buckets.append({"name": name, "count": len(hs)})
        total_items += len(hs)

    bmap, order = {}, []
    for b in buckets:
        if b["name"] not in bmap:
            bmap[b["name"]] = 0; order.append(b["name"])
        bmap[b["name"]] += b["count"]
    buckets = [{"name": n, "count": bmap[n]} for n in order]

    headlines = [t["headline"] for t in top3] + item_headlines
    tcounts = Counter()
    for h in headlines:
        for lab in topic_hits(h):
            tcounts[lab] += 1
    return {
        "date": d, "file": f"briefs/{d}.html", "top3": top3, "buckets": buckets,
        "totalItems": total_items + len(top3),
        "earlySignals": len(re.findall(r'class="tag early"', raw)),
        "topics": sorted(tcounts, key=lambda k: -tcounts[k]),
        "topicCounts": dict(tcounts),
    }

def iso_week(d):
    y, w, _ = date.fromisoformat(d).isocalendar(); return f"{y}-W{w:02d}"
def month(d): return d[:7]

def main():
    briefs = []
    for p in sorted(glob.glob(os.path.join(SRC, "*.html"))):
        try: briefs.append(parse_brief(p))
        except Exception as e: print("skip", p, e)
    briefs.sort(key=lambda b: b["date"])

    total_signals = sum(b["totalItems"] for b in briefs)
    total_early = sum(b["earlySignals"] for b in briefs)
    topic_counter = Counter()
    for b in briefs:
        for t, c in b.get("topicCounts", {}).items(): topic_counter[t] += c
    recent = briefs[-7:]; prior = briefs[-14:-7]
    def vol(group):
        c = Counter()
        for b in group:
            for t, n in b.get("topicCounts", {}).items(): c[t] += n
        return c
    rv, pv = vol(recent), vol(prior)
    hottest = []
    for t, c in topic_counter.most_common(12):
        delta = rv[t] - pv[t]
        trend = "up" if delta > 1 else ("down" if delta < -1 else "flat")
        hottest.append({"topic": t, "stories": c, "recent": rv[t], "trend": trend})

    week_counts = defaultdict(int); month_counts = defaultdict(int)
    week_briefs = defaultdict(int); month_briefs = defaultdict(int)
    for b in briefs:
        week_counts[iso_week(b["date"])] += b["totalItems"]; month_counts[month(b["date"])] += b["totalItems"]
        week_briefs[iso_week(b["date"])] += 1; month_briefs[month(b["date"])] += 1
    weekly = [{"period": k, "signals": week_counts[k], "briefs": week_briefs[k]} for k in sorted(week_counts)]
    monthly = [{"period": k, "signals": month_counts[k], "briefs": month_briefs[k]} for k in sorted(month_counts)]

    def top_stories(period_fn):
        groups = defaultdict(list)
        for b in briefs:
            for i, t in enumerate(b["top3"]):
                groups[period_fn(b["date"])].append({
                    "headline": t["headline"], "topic": t["topic"], "why": t["why"],
                    "date": b["date"], "rank": i + 1, "early": t["early"], "file": b["file"]})
        out = {}
        for per, items in groups.items():
            items.sort(key=lambda x: (x["rank"], not x["early"], x["date"]))
            out[per] = items[:6]
        return out

    data = {
        "generated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": {
            "totalBriefs": len(briefs), "totalSignals": total_signals, "totalEarly": total_early,
            "firstDate": briefs[0]["date"] if briefs else None,
            "lastDate": briefs[-1]["date"] if briefs else None,
            "avgPerBrief": round(total_signals / len(briefs), 1) if briefs else 0,
        },
        "hottest": hottest, "weekly": weekly, "monthly": monthly,
        "topStoriesByWeek": top_stories(iso_week), "topStoriesByMonth": top_stories(month),
        "briefs": [{
            "date": b["date"], "file": b["file"], "totalItems": b["totalItems"], "early": b["earlySignals"],
            "topics": b["topics"], "lead": b["top3"][0]["headline"] if b["top3"] else "",
            "leadTopic": b["top3"][0]["topic"] if b["top3"] else "",
            "top3": [t["headline"] for t in b["top3"]],
        } for b in reversed(briefs)],
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(data, open(OUT, "w"), indent=2, ensure_ascii=False)
    # Re-inject inline data block into index.html so the portal works on file:// and HTTP.
    try:
        idx = open(HUB, encoding="utf-8").read()
        payload = json.dumps(data, ensure_ascii=False)
        new_block = '<script id="brief-data" type="application/json">\n' + payload + '\n</script>'
        idx2 = re.sub(r'<script id="brief-data"[^>]*>.*?</script>', new_block, idx, count=1, flags=re.S)
        if idx2 != idx:
            open(HUB, "w", encoding="utf-8").write(idx2)
            print("Re-injected inline data into archive.html")
    except FileNotFoundError:
        pass
    # Root index.html is ALWAYS the latest brief (the top page).
    if briefs:
        latest = briefs[-1]["date"]
        src = os.path.join(ROOT, "briefs", latest + ".html")
        try:
            bh = open(src, encoding="utf-8").read()
            # rewrite asset/script depth from briefs/ (../assets) to root (assets)
            bh = bh.replace('src="../assets/brief-enhance.js"', 'src="assets/brief-enhance.js"')
            open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(bh)
            print(f"Root index.html set to latest brief {latest}")
        except FileNotFoundError:
            pass
    print(f"Parsed {len(briefs)} briefs -> totals: signals={total_signals} early={total_early}")
    print("Hottest:", ", ".join(f"{h['topic']}({h['stories']},{h['trend']})" for h in hottest[:8]))
    print("Weeks:", ", ".join(f"{w['period']}:{w['signals']}" for w in weekly))

if __name__ == "__main__":
    main()
