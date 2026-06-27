# Cloud routine prompt — Daily AI Intelligence Brief

Paste the block below as the prompt of the Remote Routine. It is the cloud-adapted
version of the local Cowork task `daily-ai-briefing`. Differences from the local
version: no mac_terminal (uses the routine's own bash shell), reads yesterday's
brief from the cloned repo's briefs/ folder instead of a local archive, saves the
generated HTML to /tmp, and deploys by pushing to main from inside the clone.

Prerequisites in the routine's Cloud Environment panel:
- Env var GCP_TTS_API_KEY set (keeps audio working). deploy.sh skips audio cleanly if absent.
- Network access: Full (broad multi-source sweep + Google TTS + github.io checks).
- Gmail connector attached (for the draft).
- Repo regular-briefings connected, with "Allow unrestricted branch pushes" ON (Pages serves from main).

---

Use the `daily-ai-brief` skill in this repo's `.claude/skills/` folder to produce the AI Intelligence Brief. You are running fully autonomously in a cloud session: no permission prompts, no human in the loop. The repository is already cloned into your working directory; treat its root as the project root for every relative path below.

=== STEP 0: PICK TODAY'S EDITION BY WEEKDAY ===
In your bash shell run `date +%u` (1=Mon ... 7=Sun) and `TZ=Europe/Berlin date +%Y-%m-%d`. Choose the edition:
- MONDAY (1): WEEKEND CATCH-UP. Window = last 72 hours (Friday 06:00 CET to now). Full 7-bucket sweep. In the header meta line write "Window: <Fri date> 06:00 CET to <today> 06:00 CET (72h weekend catch-up)".
- TUESDAY to THURSDAY (2-4): FULL edition. Window = last 24 hours.
- FRIDAY (5): FULL edition PLUS the Week in review block (STEP 5b). Window = last 24 hours.
- SATURDAY (6): LIGHT PULSE. Window = last 24 hours. Tier 1 confirmed items only, 5 to 8 items in a single consolidated list, no forced 7-bucket sweep, no forced Top 3 if the day is thin. Still deploy and email. Keep it short and honest.
- SUNDAY (7): the cron skips Sunday. If it ever fires, run the Saturday light pulse.

=== STEP 1: SOURCE SWEEP ===
If the Task tool (sub-agents) is available in this environment, spawn one sub-agent per theme bucket so the 7 buckets run in parallel. If sub-agents are NOT available, sweep the 7 buckets sequentially in a single pass (skip the parallel sweep on Saturday's light pulse regardless). The 7 buckets: 1) Anthropic / Claude, 2) Frontier LLM Labs, 3) Agentic AI and MCP, 4) AI Coding Tools, 5) AI Data Centers, 6) AI Business, 7) Open Source and Research. If a bucket is quiet, say "Quiet day" plainly. Do not pad. Anthropic is saturated and cooling, so do not force 3-4 Anthropic items, only report genuine first-party movement. MCP/Agents, OpenAI, Coding tools, and Microsoft are the rising frontiers worth more attention.

Avoid day-over-day Top 3 echo: read yesterday's brief from the cloned repo at `briefs/<YESTERDAY-YYYY-MM-DD>.html`, and if today's top scorers share themes with yesterday's Top 3, prefer the next-highest scorer from a different bucket. Tie-breaker: Anthropic-bonus items, then forward-looking items with a concrete falsifiable "Why it matters".

=== STEP 2: DASHBOARD HTML ===
Build a single self-contained HTML file. Copy the CSS + inline Ask-LLM v2 JS verbatim from the most recent brief in the cloned repo's `briefs/` folder (newest dated file), then replace the content. Do NOT hardcode the audio player block and do NOT add the ../assets/brief-enhance.js include: tools/tts.py injects the audio player and tools/add_brief.py injects the enhance script during deploy.

Ask-LLM v2 spec (must hold):
- `<meta name="ask-type" content="brief">` and `<meta name="ask-date" content="YYYY-MM-DD">` in `<head>`.
- `.ask-btn` opacity 0.3 default, opacity 1 on hover of the surrounding `.item`/`.card`; on touch default 0.55, 1 on row hover.
- Do NOT put `#ask-popover` or `#ask-backdrop` markup in the body; the script auto-injects via ensurePopoverDOM().
- Mobile bottom-sheet at `(max-width: 600px)`, respects safe-area-inset-bottom. CSS + JS inline, single file.
- Top 3 implication lines use the short label `<strong>Why it matters:</strong>`.

Sections: Header strip, Top 3 (skip on Saturday pulse), Latest by bucket, Rumors and Early Signals, Upcoming next 7 days, Source log. On Friday also add the Week in review block (STEP 5b).

=== STEP 3: SAVE GENERATED FILE ===
Write the generated HTML to `/tmp/ai-brief-<YYYY-MM-DD>.html`. (The local disk is ephemeral; the durable archive copy lands in the repo's `briefs/` folder when deploy.sh runs add_brief.py, so do not rely on /tmp persisting.)

=== STEP 4: VERIFY NO EM-DASHES ===
grep `/tmp/ai-brief-<YYYY-MM-DD>.html` for the em-dash char U+2014; it must return 0 (box-drawing U+2500 in CSS comments is fine). Confirm no banned words (revolutionary, game-changing, groundbreaking).

=== STEP 5: DEPLOY ===
From the repo root in your bash shell run:
`tools/deploy.sh <YYYY-MM-DD> /tmp/ai-brief-<YYYY-MM-DD>.html`
deploy.sh does: pull, add_brief.py (files briefs/DATE.html + enhance.js), tts.py (renders audio from GCP_TTS_API_KEY, injects player; skips cleanly if the key is missing), build.py (rebuilds index.html, archive.html, data/briefs.json, data/weekly-digest.{txt,html}), commit, and `git push origin main`. The push to main succeeds because this routine has unrestricted branch pushes enabled and authenticates via the connected GitHub App. Use deploy.sh for git; do not call any github MCP tool.
Then sleep ~45s and curl for HTTP 200 on https://pietvanbloom-lab.github.io/regular-briefings/ , the dated brief briefs/<YYYY-MM-DD>.html, and the audio briefs/audio/<YYYY-MM-DD>.mp3.

=== STEP 5b: FRIDAY WEEK IN REVIEW (Friday only) ===
On Friday add an H2 "Week in review" section after Rumors and before the Source log, built from the cloned repo's `data/briefs.json` (read it BEFORE running deploy.sh). Summarize, all sourced from that file: Movers (movers.risers / movers.faders); Hot threads (narratives[] with status hot or emerging); Early-signal scorecard (earlyPayoff.hitRate, medianLeadDays, plus 2-3 earlyPayoff.calls[] examples). No em-dashes.

=== STEP 6: EMAIL DELIVERY ===
After the 200 check, fetch https://pietvanbloom-lab.github.io/regular-briefings/data/weekly-digest.txt and .../weekly-digest.html. Create a Gmail draft via the connected Gmail connector to markus.possiel@gmail.com AND sabrina.possiel@gmail.com.
- Subject (no em-dashes): `AI Brief [DATE]: [N early signals, TOP TOPIC]`.
- body: short note + the live URL https://pietvanbloom-lab.github.io/regular-briefings/ + the 3-line TL;DR + the weekly-digest.txt text.
- htmlBody: a styled button linking to the URL, then the TL;DR, then the weekly-digest.html snippet.
- If a digest fetch fails, skip that section and still send. Email is the only delivery channel: do NOT post to Slack.

=== STYLE (hard rules) ===
English throughout. No em-dashes anywhere (use colons, commas, or split sentences); box-drawing U+2500 in CSS comments allowed. Ban: revolutionary, game-changing, groundbreaking. Every claim has a clickable source. Paraphrase, never quote more than 15 words. Mark unverifiable claims [UNVERIFIED] and exclude them from the Top 3.

=== SUCCESS CRITERIA ===
A correct run: the dated brief is live at the github.io URL (HTTP 200), the root index.html shows today's edition, and a Gmail draft addressed to both recipients exists with the subject line and TL;DR. On a thin day an honest short brief still deploys and emails.
