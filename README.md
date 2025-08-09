# GameTok 🎮

GameTok is TikTok for gaming. Addictive, endless-scroll experience of TikTok to generative gaming.

## Demo Video

*[Demo video placeholder - add your demo video here]*

## Features
 - Scroll endlessly or generate game from prompt
 - Prefetching and cache for speed optimiations
 - Morph LLM for on the fly code edits and freestyle.sh for dev server hosting

## Built in 5 Hours ⚡

This project was built in just 5 hours for the **YCombinator Hackathon 2025**, showcasing rapid prototyping and innovative game delivery.

## How We Used Morph
- We use Morph as a fast "apply engine" during full generation flow (`POST /generate-game`).
- Flow:
  1) Claude (Anthropic) generates a complete React `GameZone` component (imports + component + `export default`).
  2) We send Morph a single-file apply request with an explicit contract: keep path `src/GameZone.js`, return only final code, no fences.
  3) Morph returns the updated file contents; we sanitize to enforce React import and `export default GameZone;`, then write it.
- Model: `morph-v3-large` via Chat Completions API with structured `<instruction>`, `<code>` (current file), `<update>` (new component) message.
- Why Morph: it reliably merges/rewrites the target file to match the contract and avoids brittle string diffs during full regenerate.

Notes:
- For ultra-fast scroll, we skip Morph and directly write cached code (see Prefetch Queue + `/scroll-apply`). Morph remains in the full generate path for correctness and resilience.

## How We Used Freestyle
- Freestyle provisions an on-demand dev server for this repo and hosts the live app:
  - `POST /connect` → `freestyle.Freestyle.create_repository(...)` then `request_dev_server(...)`.
  - Returns `ephemeral_url` (live app) and `code_server_url` (VS Code in browser).
- We read/write files on the dev server to deploy games in real time:
  - `dev_server.fs.read_file("src/GameZone.js")`
  - `dev_server.fs.write_file("src/GameZone.js", updated_code)`
- Endpoints powered by Freestyle FS:
  - `/gamezone/read`, `/gamezone/write` — direct file ops
  - `/scroll-apply` — writes a prefetched React component instantly (no rebuild)
  - `/generate-game` — after Claude+Morph, writes the final component

## Prefetch Queue (Speed)
- Backend keeps a FIFO queue (up to 5) of ready-to-apply `GameZone.js` components.
- Key endpoints:
  - `POST /fill-next {count?: number, idea?: string}` → generate and queue items
  - `GET /prepared-status` → { has_next, count, sample }
  - `POST /scroll-apply` → pop head and write directly for instant next
- Frontend shows a tiny "Prefetched: N" counter and a blue dot when ready; it also tops off to 5 in the background.

Built with ❤️ at YC Hackathon 2025