# Intelligent Ticket Router & Triage Engine (LLM-powered)

An AI-based support ticket triage system that calls a real LLM endpoint to:

- Classify tickets into **Technical**, **Billing**, **Logistics**, or **Feedback**
- Assign a **priority level** (High / Medium / Low)
- Write a one-sentence **summary**
- Draft a ready-to-send **suggested response**

Each user signs in with their own account, and their triage history is stored in a local
**SQLite** database — so history survives refreshes and restarts, and no user can see
another user's tickets.

Works with any OpenAI-compatible chat completions endpoint, so you can use a **free**
provider like Groq or OpenRouter, Google Gemini's free tier, or a local Ollama model —
no paid OpenAI key required. If no key is configured, or the API call fails, it
automatically falls back to an offline keyword-based classifier so the app never breaks.

## Folder Structure

```
ticket-router/
├── src/
│   ├── app.py                    Streamlit entry point, auth gate + tab wiring
│   ├── config/
│   │   └── settings.py            Loads .env / environment into a typed Settings object
│   ├── db/
│   │   └── store.py               SQLite schema, password hashing, per-user history CRUD
│   ├── llm/
│   │   ├── client.py              OpenAI-compatible LLM client (calls the API)
│   │   ├── prompts.py              System/user prompt templates for the triage task
│   │   └── fallback.py             Offline keyword-based classifier (used if no key / API fails)
│   ├── audio/
│   │   ├── stt_client.py           Speech-to-Text client (Groq Whisper by default)
│   │   └── tts_client.py           Text-to-Speech client (ElevenLabs + free Edge-voice fallback)
│   ├── helpers/
│   │   ├── json_utils.py           JSON extraction + result validation/normalization
│   │   └── ui_helpers.py           Small shared UI formatting helpers
│   └── ui/
│       ├── theme.py                Shared CSS, priority badges, card helpers
│       ├── login.py                Sign in / sign up gate + account sidebar
│       ├── sidebar.py              LLM + Audio provider/key/model configuration sidebar
│       ├── single_ticket.py        Single ticket tab (voice input + audio playback)
│       ├── bulk_upload.py          Bulk CSV upload tab
│       └── dashboard.py            Per-user ticket history dashboard tab
├── .streamlit/
│   └── config.toml               Streamlit theme + server flags (XSRF/CORS off for uploads)
├── data/                         SQLite database lives here (Docker volume, git-ignored)
├── sample_tickets.csv            Ready-to-upload example CSV for the Bulk Upload tab
├── .env.example                  Example environment variables for free providers
├── .gitignore                    Excludes .env, data/ and the SQLite database
├── .dockerignore                 Keeps .env and the local database out of the image
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Accounts & history (SQLite)

The app opens on a **Sign In / Create Account** screen — nothing else is reachable until
you're authenticated.

- **Storage** — a single SQLite file at `data/ticket_router.db` (override with the
  `DB_PATH` environment variable). It holds two tables: `users` and `tickets`.
- **Passwords** — hashed with PBKDF2-HMAC-SHA256, 200,000 iterations and a random
  16-byte salt per user, verified with a constant-time comparison. Plaintext passwords
  are never written to disk.
- **Isolation** — every ticket row is keyed to a `user_id`, and all history reads,
  writes, and deletes are scoped by it. Signing in as a different user shows a
  different history.
- **Persistence** — `docker-compose.yml` mounts a named volume at `/app/data`, so the
  database survives `docker compose up --build` and container recreation. To wipe all
  accounts and history, run `docker compose down -v`.

The Dashboard tab shows only the signed-in user's tickets, with KPI tiles, category and
priority charts, a CSV export, and a "Clear My History" button.

## Try it with sample data

`sample_tickets.csv` in the project root contains 8 example tickets covering all four
categories and all three priority levels. Upload it in the **Bulk Upload** tab to
populate the dashboard immediately, or copy a single line into the **Single Ticket** tab.

> Note: with no API key configured, results come from the offline fallback classifier,
> which reports confidence as *keyword purity* (matches for the winning category ÷ total
> matches). Single-topic tickets therefore score 100%. Configure an LLM key for
> meaningful confidence values and genuinely drafted responses.

## Audio features (voice input + spoken replies)

The Single Ticket tab supports two optional audio features, both usable for free:

**🎙️ Speech-to-Text (talk instead of type)**
Record a ticket with your microphone (`st.audio_input`) and transcription starts
**automatically** as soon as you stop recording — the text lands in the message box ready
to review and analyze. The clip is fingerprinted so reruns never re-spend the API call.
By default this uses **Groq's free Whisper endpoint** (`whisper-large-v3-turbo`) — the same
free Groq account you use for the LLM works here too, and the sidebar auto-fills the STT key
from your LLM key if you're using Groq for both.

**🔊 Text-to-Speech (listen to the suggested reply)**
The audio player is rendered **with the result** — no button to reveal it. Synthesis is
cached per reply, so reruns don't re-call the API, and a sidebar-adjacent toggle lets the
reply play automatically as soon as the analysis lands.
- Uses **Groq's** OpenAI-compatible `/audio/speech` endpoint (`canopylabs/orpheus-v1-english`),
  so the *same* free Groq key powers the LLM, Whisper transcription, and speech synthesis —
  no ElevenLabs account needed.
- Available voices: **autumn, diana, hannah, austin, daniel, troy** (selectable in the
  sidebar). The model returns **WAV only** — requesting mp3 or flac fails with a 400.
- **One-time setup:** Groq TTS models are gated behind a terms acceptance. Visit
  https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english and accept,
  or every call returns `model_terms_required`.
- If no key is set, or the Groq call fails for any reason (including unaccepted terms),
  the app **automatically falls back to a free, no-key Microsoft Edge neural voice**
  (via `edge-tts`) — so audio playback always works, with zero API keys required.

> ElevenLabs support was removed in favor of Groq. If you previously set an ElevenLabs
> key in `.env`, replace `TTS_API_KEY` with your Groq key (or leave it blank) — sending an
> ElevenLabs `sk_…` key to Groq returns `401 Invalid API Key`.

Both audio settings live under **🎙️ Audio Settings** in the sidebar and can be changed at
runtime, same as the LLM settings.

## Get a free API key (pick one)

| Provider | Link | Notes |
|---|---|---|
| Groq | https://console.groq.com/keys | Fast, free tier, recommended default |
| OpenRouter | https://openrouter.ai/models?max_price=0 | Filter models tagged `:free` |
| Google Gemini | https://aistudio.google.com/apikey | Free tier via OpenAI-compatible endpoint |
| Ollama | https://ollama.com | Fully local, no key, no cost |
| Groq (TTS) | https://console.groq.com/playground | Same key as the LLM; requires one-time terms acceptance |
| Edge-TTS (TTS, no key) | built in via `edge-tts` | Fully free fallback voice, no signup |

## Setup

```bash
cp .env.example .env
# edit .env and paste your Groq API key into LLM_API_KEY
```

One free Groq key covers all three AI features — classification, Whisper transcription,
and speech synthesis. `STT_API_KEY` and `TTS_API_KEY` can be left blank; both fall back to
`LLM_API_KEY` automatically. `.env` is git-ignored and excluded from the Docker image, so
your key is never committed or baked into a layer.

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `LLM_API_KEY` | *(empty)* | Provider key. Empty → offline fallback classifier |
| `LLM_BASE_URL` | Groq | Any OpenAI-compatible `/chat/completions` endpoint |
| `LLM_MODEL` | `llama-3.1-8b-instant` | Chat model for triage |
| `LLM_TIMEOUT_SECONDS` / `LLM_TEMPERATURE` / `LLM_MAX_TOKENS` | `30` / `0.2` / `400` | Request tuning |
| `DB_PATH` | `./data/ticket_router.db` | SQLite location for accounts + history |
| `STT_API_KEY` | falls back to `LLM_API_KEY` | Whisper transcription key |
| `STT_BASE_URL` / `STT_MODEL` | Groq / `whisper-large-v3-turbo` | Transcription endpoint |
| `TTS_API_KEY` | falls back to `LLM_API_KEY` | Speech synthesis key |
| `TTS_BASE_URL` / `TTS_MODEL` | Groq / `canopylabs/orpheus-v1-english` | Synthesis endpoint |
| `TTS_VOICE` / `TTS_FORMAT` | `autumn` / `wav` | Voice name; Orpheus returns WAV only |
| `EDGE_TTS_VOICE` | `en-US-AriaNeural` | Free no-key fallback voice |

## Run with Docker

```bash
docker compose up --build
```

Open http://localhost:8501 and create an account on the first screen.

The SQLite database persists in the `ticket-router-data` volume across rebuilds. To reset
all accounts and history:

```bash
docker compose down -v
```

If startup fails with `Bind for 0.0.0.0:8501 failed: port is already allocated`, another
container is holding the port — find it with `docker ps` and stop it, or change the host
port mapping in `docker-compose.yml`.

## Run locally (without Docker)

```bash
pip install -r requirements.txt
streamlit run src/app.py
```

The database is created automatically at `data/ticket_router.db` on first run.

`src/config/settings.py` automatically loads variables from a `.env` file in the project
root via `python-dotenv`, so no manual exporting is required. You can also skip `.env`
entirely and paste the API key, base URL, and model name directly into the sidebar at
runtime — it's kept only in the browser session.

## How it works

1. **Settings** — `src/config/settings.py` centralizes all configuration (API key, base
   URL, model, timeout, temperature) loaded from `.env` with sensible defaults.
2. **Authentication** — `src/db/store.py` creates the SQLite schema on startup;
   `src/ui/login.py` gates the app with `st.stop()` until credentials verify, then keeps
   the user in `st.session_state`.
3. **Prompted classification** — `src/llm/prompts.py` defines a system prompt instructing
   the model to return strict JSON with category, priority, confidence, summary, and a
   suggested response.
4. **LLM call** — `src/llm/client.py` sends the ticket text to any OpenAI-compatible
   `/chat/completions` endpoint; `src/helpers/json_utils.py` parses and validates the
   response.
5. **Fallback** — if no API key is set or the request fails (rate limit, network, bad
   JSON), `src/llm/fallback.py` provides an offline keyword-based classification so the
   app keeps working.
6. **Persistence** — every analyzed ticket (single or bulk) is written to SQLite against
   the signed-in user's id via `helpers/ui_helpers.add_to_history`, and the dashboard
   reads it back with `store.get_history(user_id)`.
7. **Voice input** — `src/audio/stt_client.py` sends recorded audio to an OpenAI-compatible
   `/audio/transcriptions` endpoint (Groq's free Whisper by default) and returns the
   transcribed text, which pre-fills the ticket text area for review before analysis.
8. **Spoken replies** — `src/audio/tts_client.py` posts the suggested response to Groq's
   `/audio/speech` endpoint if a key is configured, and automatically falls back to the
   free, no-key `edge-tts` library otherwise or on failure, so playback never hard-fails.
   The returned MIME type follows the chosen format so `st.audio` plays it correctly.
9. **UI** — `src/ui/` splits the Streamlit interface into a login gate, a sidebar (account
   + LLM + audio config) and three tabs (single ticket with voice I/O, bulk upload,
   dashboard), wired together in `src/app.py`. Styling is centralized in `src/ui/theme.py`
   and `.streamlit/config.toml`.

## Extending

- Add a new category by updating `VALID_CATEGORIES` in `src/config/settings.py` and the
  category list in `src/llm/prompts.py`.
- Swap providers anytime from the sidebar — no restart needed.
- Adjust `LLM_TEMPERATURE` / `LLM_MAX_TOKENS` in `.env` for longer or more creative responses.
- Add new UI tabs by creating a module under `src/ui/` and wiring it into `src/app.py`
  (tab render functions take the signed-in `user` dict).
- Restyle the app from `src/ui/theme.py` (component CSS, badges) and `.streamlit/config.toml`
  (base theme colors) — no per-page style edits needed.
- Extend the schema in `src/db/store.py`; `init_db()` runs `CREATE TABLE IF NOT EXISTS` on
  every startup, so additive changes apply automatically.

## Troubleshooting

**"An error has occurred, please try again" under the audio recorder**
Streamlit's XSRF protection rejects the `st.audio_input` upload with a 403, because the
`_streamlit_xsrf` cookie is not issued on the initial page load. `.streamlit/config.toml`
disables `enableXsrfProtection` and `enableCORS` for this reason. Re-enable them if you
ever expose the app beyond localhost.

**`Text-to-speech failed: 403 ... speech.platform.bing.com`**
Old `edge-tts` releases fail Microsoft's `Sec-MS-GEC` token check. Requires `edge-tts>=7`
(pinned to `7.2.8` here). Also confirm the container clock is correct — the token is
time-based, and a skewed clock produces the same 403.

**`model_terms_required` from Groq TTS**
Accept the model terms once at
https://console.groq.com/playground?model=canopylabs%2Forpheus-v1-english.
Until then the app silently uses the free Edge fallback voice.

**Audio plays but the caption says "Free fallback (Edge neural voice)"**
The Groq call failed and the app degraded gracefully — the exact reason is shown in the
message above the player. Common causes: an invalid voice name (`voice must be one of
[autumn diana hannah austin daniel troy]`), a non-WAV `TTS_FORMAT`, or an ElevenLabs
`sk_…` key left in `TTS_API_KEY` (Groq answers `401 Invalid API Key`).

## Requirements note

`pandas`, `numpy`, and `pyarrow` are pinned to a mutually compatible set
(`2.2.3` / `2.1.3` / `17.0.0`). Streamlit converts every dataframe and chart through Arrow,
and mismatched versions here can **segfault the server process** rather than raise a Python
error. Change these pins together, and exercise the Dashboard tab afterward.
