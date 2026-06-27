# Migration: Cowork task `daily-ai-briefing` -> Remote Routine

This branch (claude/migrate-routine) carries everything the cloud routine needs from
the local Mac. Merge it to `main` before the routine's first run, because remote
routines clone the default branch.

## What was local and how it now travels
| Local dependency | Cloud handling |
|---|---|
| daily-ai-brief skill | Copied to .claude/skills/daily-ai-brief/ in this repo |
| tools/ (deploy.sh, build.py, add_brief.py, tts.py) | Already in repo, cloned each run |
| briefs/ (CSS template + yesterday's brief) | Already in repo; prompt reads from here, not local archive |
| Local output/ archive | Replaced by /tmp during run; durable copy lands in briefs/ via deploy |
| mac_terminal shell | Replaced by the routine's native bash |
| git push via local gh keyring | Push via connected GitHub App (needs unrestricted branch pushes ON) |
| Google TTS local key file | Env var GCP_TTS_API_KEY in the Cloud Environment panel |
| Gmail draft connector | Gmail connector attached to the routine |
| 7 parallel sub-agents | Prompt falls back to sequential if Task tool is unavailable |

## Manual UI steps (cannot be scripted)
1. Merge claude/migrate-routine into main.
2. Create a Remote Routine: Desktop app -> Code -> Routines -> New routine -> Remote. Connect repo pietvanbloom-lab/regular-briefings. Install the Claude GitHub App if prompted.
3. Prompt: paste the block from CLOUD-ROUTINE-PROMPT.md.
4. Schedule: Mon-Sat 06:00 Europe/Berlin (cron 0 6 * * 1-6). Respects the 1-hour-minimum and daily run-cap rules.
5. Cloud Environment panel:
   - Env var GCP_TTS_API_KEY = your Google Cloud TTS key (do not commit it).
   - Network access: Full (broad source sweep + Google TTS + github.io checks; Trusted will block sources).
   - Connectors: keep Gmail; remove the rest to shrink the footprint.
6. Repo settings: enable "Allow unrestricted branch pushes" for this repo so deploy.sh can push to main and Pages auto-deploys.
7. Run now. Inspect the log. Verify HTTP 200 on the live site + a Gmail draft to both recipients.
8. Cut over: once a clean run is confirmed, disable the local Cowork task `daily-ai-briefing` so the brief does not run twice.

## Likely first-run snags (and fixes)
- Source fetches blocked -> network is on Trusted, switch to Full.
- No audio -> GCP_TTS_API_KEY missing or misnamed in the panel.
- Push rejected -> unrestricted branch pushes not enabled on the repo.
- Gmail step 401 -> re-authenticate the Gmail connector in the cloud.
- Skill ignored -> branch not merged to main yet, or prompt did not name the skill.
