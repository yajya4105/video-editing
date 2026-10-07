---
name: finance-short
description: Make a ~50s vertical Hinglish finance-advice short (Reels/Shorts) with recurring comic characters, from topic to finished MP4. Use when the user says "make today's video", "new short on <topic>", "finance reel", "script options for <topic>", or names a recurring character. Script approval is a hard gate - nothing that spends credits runs before the user finalises the script.
---

# Finance short

Vertical 1080x1920, 45-55 s, Hinglish voiceover, word-timed Hindi subtitles, title banner,
multi-shot edit. Generation runs on the **ElevenLabs connector** (`mcp__ElevenLabs__*`);
editing runs locally with ffmpeg via `build.py`. Reference project: `noida-short/`.

## Phase 1 - Script (no credits spent)

1. Get the topic. If the user gives a reference video link, try to read it; YouTube is
   blocked in this environment, so ask them to paste the transcript or key points.
2. Write **5-6 distinct script versions**, each 110-140 Hindi/Hinglish words (about 45-50 s).
   Vary the angle, not just wording: e.g. checklist, myth-vs-fact, story/case, comic
   dialogue between characters, "mistakes I see daily", Q&A.
   For each version show: title banner text, cast (from `characters/characters.json`),
   the script with speaker tags (`[Babuji]: ...`), estimated length, and new shots needed.
3. Facts: only well-established, general guidance; no specific stock/fund picks, no
   return promises; always end with the disclaimer line (e.g. "ये सलाह है, गारंटी नहीं।").
   Flag any figure the user should verify.
4. **STOP and wait.** Do not create flows, images, voices or anything that costs credits.
   Revise as asked. Proceed only when the user clearly finalises one version
   ("final", "go with 3", "lock it").

## Phase 2 - Plan and price (still no credits)

1. Write `videos/<YYYY-MM-DD>-<slug>/script.md` with the locked script.
2. Shot list: one shot per 2-4 s, cut on sentence/point boundaries; reuse existing
   character/location images and crops wherever possible.
3. Price every paid step with `estimate_only: true` and show the total. Get a "go".

## Phase 3 - Generate (spends credits, after "go")

- `creative_create_flow` once per video; every node goes on that flow.
- **Voices**: one TTS node per speaker line group with that character's fixed `voice_id`
  (`eleven_multilingual_v2`, or `eleven_v3` for emotion tags), `generations_count: 1`.
  Write Hindi in Devanagari for correct pronunciation.
- **Images**: `bytedance-seedream-5-lite`, `aspect_ratio: 9:16`, `generations_count: 1`,
  `connect_from` the character's reference node(s). Two-character shots: connect both
  references (use `gemini-3-pro-image` if identities drift). Never invent node ids.
- **Lip-sync** (paid plans only): only for shots where a character speaks to camera, one
  face per shot, `bytedance-omnihuman-v1.5` fed with that shot's image + that line's audio.
  Cutaways stay as stills with camera moves.
- Never re-run a generation call to "retry"; check status with `creative_get_flow_run_status`.
- **Timing**: `creative_transcribe_audio` (Scribe, free) on the final voice -> `words.json`.

## Phase 4 - Edit (local, free)

Copy `noida-short/build.py` into the video folder, fill `shots.json` (times from
`words.json`), set banner text, run `python3 build.py preview`, check frames, then render.
Banner must cover any AI-misspelled signage. Send the MP4 with SendUserFile, commit + push.

## Credit rules

- Default `generations_count: 1` for images and voices (4 costs 4x).
- Re-voicing costs ~700 credits per 50 s - lock the script first; edits/subtitles are free.
- Reuse character reference images and location crops; generate only shots that add meaning.
- Free plan: daily image cap and no video. Report failures, don't retry the same day.

## Characters

Registry: `characters/characters.json` (look, reference image, ElevenLabs node id,
voice id). Add new characters there once - a reference sheet image + fixed voice - and
reuse them in every video so the channel has a consistent cast.
