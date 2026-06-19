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

# ======================================================================
# Analytical layer: entities, momentum/movers, narrative arcs,
# early-signal payoff, and a co-occurrence relationship network.
# All deterministic (pure text stats), no external calls.
# ======================================================================

# Canonical entity -> (category, alias regex). Finer-grained than the 17 TOPICS.
ENTITIES = {
    "Anthropic": ("lab", r"anthropic"),
    "OpenAI": ("lab", r"openai"),
    "Google DeepMind": ("lab", r"deepmind|google deepmind"),
    "Google": ("bigtech", r"\bgoogle\b|alphabet"),
    "Meta": ("bigtech", r"\bmeta\b|facebook"),
    "Microsoft": ("bigtech", r"microsoft"),
    "Amazon": ("bigtech", r"amazon|\baws\b"),
    "Apple": ("bigtech", r"\bapple\b"),
    "xAI": ("lab", r"\bxai\b"),
    "Mistral": ("lab", r"mistral"),
    "DeepSeek": ("lab", r"deepseek"),
    "Cohere": ("lab", r"cohere"),
    "Stability AI": ("lab", r"stability ai|stable diffusion"),
    "Hugging Face": ("infra", r"hugging ?face"),
    "Perplexity": ("app", r"perplexity"),
    "Alibaba": ("bigtech", r"alibaba|qwen"),
    "Baidu": ("bigtech", r"baidu|ernie"),
    "Tencent": ("bigtech", r"tencent"),
    "ByteDance": ("bigtech", r"bytedance|tiktok|doubao"),
    "Moonshot AI": ("lab", r"moonshot|\bkimi\b"),
    "Reka": ("lab", r"\breka\b"),
    "AI21": ("lab", r"ai21"),
    "Thinking Machines": ("lab", r"thinking machines"),
    "Safe Superintelligence": ("lab", r"safe superintelligence|\bssi\b"),
    "Nvidia": ("chips", r"nvidia|\bcuda\b|blackwell"),
    "AMD": ("chips", r"\bamd\b|instinct mi\d"),
    "Intel": ("chips", r"\bintel\b|gaudi"),
    "TSMC": ("chips", r"\btsmc\b"),
    "Broadcom": ("chips", r"broadcom"),
    "Cerebras": ("chips", r"cerebras"),
    "Groq": ("chips", r"\bgroq\b"),
    "SambaNova": ("chips", r"sambanova"),
    "CoreWeave": ("infra", r"coreweave"),
    "Nscale": ("infra", r"nscale"),
    "Together AI": ("infra", r"together ai|together\.ai"),
    "Lambda": ("infra", r"lambda labs|lambda cloud"),
    "Oracle": ("infra", r"oracle"),
    "Databricks": ("infra", r"databricks"),
    "Snowflake": ("infra", r"snowflake"),
    "SoftBank": ("investor", r"softbank"),
    "Cursor": ("app", r"cursor|anysphere"),
    "Windsurf": ("app", r"windsurf|codeium"),
    "Replit": ("app", r"replit"),
    "Vercel": ("app", r"vercel|\bv0\b"),
    "GitHub": ("app", r"github"),
    "LangChain": ("infra", r"langchain|langgraph"),
    "Ollama": ("infra", r"ollama"),
    "vLLM": ("infra", r"\bvllm\b"),
    "Sierra": ("app", r"\bsierra\b"),
    "Harvey": ("app", r"\bharvey\b"),
    "Glean": ("app", r"\bglean\b"),
    "Notion": ("app", r"notion"),
    "Figma": ("app", r"figma"),
    "Scale AI": ("infra", r"scale ai"),
    "Salesforce": ("bigtech", r"salesforce"),
    "Tesla": ("bigtech", r"tesla"),
    "Figure": ("robotics", r"figure ai|figure robot"),
    "Sam Altman": ("person", r"sam altman|altman"),
    "Dario Amodei": ("person", r"dario amodei|amodei"),
    "Demis Hassabis": ("person", r"demis hassabis|hassabis"),
    "Sundar Pichai": ("person", r"sundar pichai|pichai"),
    "Satya Nadella": ("person", r"satya nadella|nadella"),
    "Mark Zuckerberg": ("person", r"zuckerberg"),
    "Jensen Huang": ("person", r"jensen huang|jensen"),
    "Elon Musk": ("person", r"elon musk|\bmusk\b"),
    "Mira Murati": ("person", r"mira murati|murati"),
    "Ilya Sutskever": ("person", r"ilya sutskever|sutskever"),
    "Mustafa Suleyman": ("person", r"mustafa suleyman|suleyman"),
    "Yann LeCun": ("person", r"yann lecun|lecun"),
    "Andrej Karpathy": ("person", r"karpathy"),
    "GPT-5": ("model", r"gpt-?5"),
    "GPT-4o": ("model", r"gpt-?4o"),
    "o3": ("model", r"\bo3\b"),
    "ChatGPT": ("product", r"chatgpt"),
    "Claude Code": ("product", r"claude code"),
    "Claude": ("model", r"\bclaude\b"),
    "Gemini": ("model", r"gemini"),
    "Copilot": ("product", r"copilot"),
    "Grok": ("model", r"grok"),
    "Llama": ("model", r"llama"),
    "Sora": ("product", r"\bsora\b"),
    "Veo": ("product", r"\bveo\b"),
    "Codex": ("product", r"codex"),
    "Devin": ("product", r"devin"),
    "MCP": ("protocol", r"\bmcp\b|model context protocol"),
}
ENT_PAT = {k: re.compile(v[1], re.I) for k, v in ENTITIES.items()}
ENT_CAT = {k: v[0] for k, v in ENTITIES.items()}

def detect_entities(text):
    return [k for k, pat in ENT_PAT.items() if pat.search(text)]

STOPWORDS = set("""the a an and or of for to in on at by with from as is are was were be been being
this that these those it its their his her our your they them him us also into over under out
new now first more most than then after before amid via versus has have had will would can could
may might should against among about across what when where which while who whom why how
says say said report reports reportedly launch launches launched make makes made get gets adds add
ships ship plus key top big per according source sources brief week day days year years month
percent billion million trillion company companies startup startups model models data tech update
updates release releases general available availability still around roughly today window tier early""".split())

def tokenize(h):
    return [t for t in re.findall(r"[a-z0-9]+", h.lower()) if len(t) >= 4 and t not in STOPWORDS]

def compute_analytics(articles, last7_dates, prior7_dates):
    """Mutates each article with `ents`; returns dict of analytics keys.
    `articles` is the flat, date-descending list with date/file/aid/lead/early."""
    from collections import Counter as C, defaultdict as DD
    import itertools

    # ---- entity tagging + distinctive keyword sets ----
    DF = C()
    for a in articles:
        a["ents"] = detect_entities(a["h"])
        a["_kw"] = set(tokenize(a["h"]))
        for kw in a["_kw"]:
            DF[kw] += 1
    DF_CUT = 25  # tokens in <=25 articles are "distinctive" (drops june/agent/etc.)
    for a in articles:
        a["_rkw"] = set(kw for kw in a["_kw"] if DF[kw] <= DF_CUT)

    def wk(s):
        y, w, _ = date.fromisoformat(s).isocalendar(); return f"{y}-W{w:02d}"
    all_weeks = sorted(set(wk(a["date"]) for a in articles))
    recent_weeks = all_weeks[-8:]

    # ---- entity momentum / movers ----
    tot, rec, pri, first = C(), C(), C(), {}
    ent_week = DD(C)
    for a in articles:
        for e in a["ents"]:
            tot[e] += 1
            if a["date"] in last7_dates: rec[e] += 1
            if a["date"] in prior7_dates: pri[e] += 1
            first[e] = min(first.get(e, a["date"]), a["date"])
            ent_week[e][wk(a["date"])] += 1
    def spark(weekcounter):
        return [weekcounter.get(w, 0) for w in recent_weeks]
    movers = []
    for e, n in tot.items():
        if n < 4: continue
        r, p = rec[e], pri[e]
        growth = round((r - p) / p, 2) if p > 0 else (float(r) if r else 0.0)
        movers.append({"name": e, "cat": ENT_CAT.get(e, "other"), "total": n,
                       "recent": r, "prior": p, "delta": r - p, "growth": growth,
                       "first": first[e], "spark": spark(ent_week[e])})
    risers = sorted([m for m in movers if m["delta"] > 0],
                    key=lambda m: (-m["delta"], -m["growth"]))[:10]
    faders = sorted([m for m in movers if m["delta"] < 0],
                    key=lambda m: (m["delta"], m["growth"]))[:10]
    total_signals = len(articles)
    entity_insights = {m["name"]: {"total": m["total"], "recent": m["recent"], "cat": m["cat"],
                                   "first": m["first"], "spark": m["spark"],
                                   "share": round(m["total"] / total_signals * 100, 1) if total_signals else 0,
                                   "busiestWeek": (max(ent_week[m["name"]].items(), key=lambda kv: kv[1])[0]
                                                   if ent_week[m["name"]] else None)}
                       for m in movers}

    # ---- narrative arcs: entity-anchored, distinctive-keyword union-find ----
    n = len(articles)
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry: parent[ry] = rx
    rkw_index = DD(list)
    for i, a in enumerate(articles):
        for kw in a["_rkw"]:
            rkw_index[kw].append(i)
    seen = set()
    for kw, members in rkw_index.items():
        if len(members) < 2 or len(members) > 120: continue
        for i, j in itertools.combinations(members, 2):
            if (i, j) in seen: continue
            seen.add((i, j))
            A, B = articles[i], articles[j]
            if set(A["ents"]) & set(B["ents"]) and len(A["_rkw"] & B["_rkw"]) >= 2:
                union(i, j)
    comp = DD(list)
    for i in range(n):
        comp[find(i)].append(i)

    narratives = []
    for root, members in comp.items():
        if len(members) < 3: continue
        ds = sorted(set(articles[m]["date"] for m in members))
        if len(ds) < 2: continue
        entc, kwc = C(), C()
        for m in members:
            for e in articles[m]["ents"]: entc[e] += 1
            for k in articles[m]["_rkw"]: kwc[k] += 1
        size = len(members)
        prim = [e for e, c in entc.most_common() if c >= size * 0.4][:2] or [entc.most_common(1)[0][0]]
        kws = [k for k, _ in kwc.most_common(5) if k not in {e.lower() for e in prim}][:3]
        label = " + ".join(prim) + (": " + ", ".join(kws) if kws else "")
        wc = C(wk(articles[m]["date"]) for m in members)
        rcnt = sum(1 for m in members if articles[m]["date"] in last7_dates)
        pcnt = sum(1 for m in members if articles[m]["date"] in prior7_dates)
        status = ("emerging" if rcnt >= 2 and pcnt == 0 else
                  "cooling" if rcnt == 0 else
                  "hot" if rcnt > pcnt else "ongoing")
        peak = max(wc.items(), key=lambda kv: kv[1])[0]
        mem_sorted = sorted(members, key=lambda m: articles[m]["date"], reverse=True)
        narratives.append({"label": label, "entities": prim, "size": size,
                           "status": status, "span": [ds[0], ds[-1]], "peakWeek": peak,
                           "recent": rcnt, "spark": [wc.get(w, 0) for w in recent_weeks],
                           "m": mem_sorted})
    # order: active first (recent desc), then size
    narratives.sort(key=lambda x: (-x["recent"], -x["size"]))

    # ---- early-signal payoff (did an early call develop into ongoing coverage?) ----
    root_of = {i: find(i) for i in range(n)}
    early_idx = [i for i, a in enumerate(articles) if a.get("early")]
    calls, lead_days = [], []
    developed = 0
    for i in early_idx:
        a = articles[i]
        members = comp[root_of[i]]
        later = [m for m in members if articles[m]["date"] > a["date"]]
        if later:
            developed += 1
            later.sort(key=lambda m: articles[m]["date"])
            ld = (date.fromisoformat(articles[later[0]]["date"]) - date.fromisoformat(a["date"])).days
            lead_days.append(ld)
            calls.append({"h": a["h"], "date": a["date"], "file": a["file"], "aid": a.get("aid", ""),
                          "leadDays": ld, "followups": len(later),
                          "examples": [{"h": articles[m]["h"], "date": articles[m]["date"],
                                        "file": articles[m]["file"], "aid": articles[m].get("aid", "")}
                                       for m in later[:3]]})
    calls.sort(key=lambda c: (-c["followups"], -c["leadDays"]))
    total_early = len(early_idx)
    med = 0
    if lead_days:
        s = sorted(lead_days); k = len(s)
        med = s[k // 2] if k % 2 else round((s[k // 2 - 1] + s[k // 2]) / 2, 1)
    early_payoff = {"totalEarly": total_early, "developed": developed,
                    "hitRate": round(developed / total_early * 100) if total_early else 0,
                    "medianLeadDays": med, "calls": calls[:20]}

    # ---- relationship network (headline co-occ strong + same-narrative co-occ) ----
    edge = C()
    for a in articles:
        es = sorted(set(a["ents"]))
        for x in range(len(es)):
            for y in range(x + 1, len(es)):
                edge[(es[x], es[y])] += 2
    for root, members in comp.items():
        if len(members) < 3: continue
        es = sorted({e for m in members for e in articles[m]["ents"]})
        for x in range(len(es)):
            for y in range(x + 1, len(es)):
                edge[(es[x], es[y])] += 1
    edges = sorted(([{"s": a, "t": b, "w": w} for (a, b), w in edge.items() if w >= 3]),
                   key=lambda e: -e["w"])[:130]
    nodes_in = {}
    for e in edges:
        for k in (e["s"], e["t"]):
            nodes_in[k] = nodes_in.get(k, 0) + 1
    nodes = [{"id": k, "cat": ENT_CAT.get(k, "other"), "mentions": tot.get(k, 0)} for k in nodes_in]
    network = {"nodes": nodes, "edges": edges}

    # strip private fields before serialization
    for a in articles:
        a.pop("_kw", None); a.pop("_rkw", None)

    return {"movers": {"risers": risers, "faders": faders},
            "entityInsights": entity_insights,
            "narratives": narratives,
            "earlyPayoff": early_payoff,
            "network": network}

ID_TAG = re.compile(r'<div class="(?:card|item)[^"]*"')
def assign_ids(raw):
    """Give each top3 card and bucket item a stable anchor id (a1, a2, ...) in DOM order.
    Idempotent: strips any prior aN ids first. Returns (new_raw, {headline: aid})."""
    raw = re.sub(r'(<div class="(?:card|item)[^"]*")\s+id="a\d+"', r'\1', raw)
    matches = list(ID_TAG.finditer(raw))
    hmap = {}
    # build headline map from original positions
    for i, m in enumerate(matches):
        region = raw[m.end(): matches[i+1].start() if i+1 < len(matches) else len(raw)]
        h = re.search(r'<h[34][^>]*>(.*?)</h[34]>', region, re.S)
        if h:
            hl = strip_tags(h.group(1))
            hmap.setdefault(hl, f"a{i+1}")
    # insert ids from the end so offsets stay valid
    new = raw
    for i in range(len(matches) - 1, -1, -1):
        pos = matches[i].end()
        new = new[:pos] + f' id="a{i+1}"' + new[pos:]
    return new, hmap

def parse_brief(raw, d):

    top3 = []
    mtop = re.search(r'<div class="top3">(.*?)(?:<h2|<div class="bucket")', raw, re.S)
    top_block = mtop.group(1) if mtop else ""
    for cm in re.finditer(r'<div class="card([^"]*)"[^>]*>(.*?)(?=<div class="card|\Z)', top_block, re.S):
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
    article_records = []
    total_items = 0
    for bm in re.finditer(r'<div class="bucket">(.*?)(?=<div class="bucket">|<h2|<div class="footer|\Z)', raw, re.S):
        b = bm.group(1)
        name_m = re.search(r'<div class="eyebrow">(.*?)</div>', b, re.S)
        name = strip_tags(name_m.group(1)) if name_m else "Other"
        items = re.findall(r'<div class="item[^"]*"[^>]*>(.*?)</div>', b, re.S)
        hs = []
        for it in items:
            h4 = re.search(r"<h4[^>]*>(.*?)</h4>", it, re.S)
            if h4:
                hl = strip_tags(h4.group(1))
                hs.append(hl); item_headlines.append(hl)
                href = re.search(r'href="(https?://[^"]+)"', it)
                article_records.append({"h": hl, "u": href.group(1) if href else "", "bucket": name,
                                        "topics": topic_hits(hl + " " + name),
                                        "early": bool(re.search(r'class="[^"]*\bearly\b', it))})
        buckets.append({"name": name, "count": len(hs)})
        total_items += len(hs)

    bmap, order = {}, []
    for b in buckets:
        if b["name"] not in bmap:
            bmap[b["name"]] = 0; order.append(b["name"])
        bmap[b["name"]] += b["count"]
    buckets = [{"name": n, "count": bmap[n]} for n in order]

    for t in top3:
        article_records.append({"h": t["headline"], "u": "", "bucket": t.get("topic") or "Top 3",
                                "topics": topic_hits(t["headline"] + " " + (t.get("topic") or "")),
                                "lead": True, "early": t["early"]})
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
        "articles": article_records,
    }

def iso_week(d):
    y, w, _ = date.fromisoformat(d).isocalendar(); return f"{y}-W{w:02d}"
def month(d): return d[:7]

def main():
    briefs = []
    for p in sorted(glob.glob(os.path.join(SRC, "*.html"))):
        try:
            d = re.search(r"(\d{4}-\d{2}-\d{2})", os.path.basename(p)).group(1)
            raw = open(p, encoding="utf-8").read()
            new_raw, hmap = assign_ids(raw)
            if new_raw != raw:
                open(p, "w", encoding="utf-8").write(new_raw)
                raw = new_raw
            b = parse_brief(raw, d)
            b["_hmap"] = hmap
            briefs.append(b)
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

    # Flat article list (newest first) with date + file, for the topic drawer.
    articles = []
    for b in briefs:
        hmap = b.get("_hmap", {})
        for a in b.get("articles", []):
            articles.append({"h": a["h"], "u": a.get("u", ""), "topics": a.get("topics", []),
                             "date": b["date"], "file": b["file"], "lead": a.get("lead", False),
                             "early": a.get("early", False), "aid": hmap.get(a["h"], "")})
    articles.sort(key=lambda a: a["date"], reverse=True)

    # Deterministic analytical layer: entities, momentum, narratives, early payoff, network.
    last7_dates = set(b["date"] for b in recent)
    prior7_dates = set(b["date"] for b in prior)
    analytics = compute_analytics(articles, last7_dates, prior7_dates)

    # Per-topic insights: busiest week + share, keyed by topic label.
    wt = defaultdict(lambda: defaultdict(int))
    for b in briefs:
        wk = iso_week(b["date"])
        for t, c in b.get("topicCounts", {}).items():
            wt[t][wk] += c
    insights = {}
    for h in hottest:
        t = h["topic"]
        weeks = wt[t]
        bw = max(weeks.items(), key=lambda kv: kv[1]) if weeks else (None, 0)
        insights[t] = {"stories": h["stories"], "recent": h["recent"], "trend": h["trend"],
                       "busiestWeek": bw[0], "busiestCount": bw[1],
                       "share": round(h["stories"] / total_signals * 100) if total_signals else 0}

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
            hmap = b.get("_hmap", {})
            for i, t in enumerate(b["top3"]):
                groups[period_fn(b["date"])].append({
                    "headline": t["headline"], "topic": t["topic"], "why": t["why"],
                    "date": b["date"], "rank": i + 1, "early": t["early"], "file": b["file"],
                    "aid": hmap.get(t["headline"], "")})
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
        "hottest": hottest, "topicInsights": insights, "articles": articles,
        "movers": analytics["movers"], "entityInsights": analytics["entityInsights"],
        "narratives": analytics["narratives"], "earlyPayoff": analytics["earlyPayoff"],
        "network": analytics["network"],
        "weekly": weekly, "monthly": monthly,
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
