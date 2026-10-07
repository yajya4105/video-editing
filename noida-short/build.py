"""Assemble the vertical short: cropped still + slow zoom + sign/title overlays + synced Hindi subtitles + voiceover."""
import json, subprocess, sys

W, H, FPS, DUR = 1080, 1920, 30, 48.6
ORD = {"पहला": "1", "दूसरा": "2", "तीसरा": "3", "चौथा": "4", "पाँचवाँ": "5"}

words = [w for w in json.load(open("words.json"))["words"] if w["type"] == "word"]

# Group words into short on-screen chunks: break after punctuation, at ordinals, or at 4 words.
chunks, cur = [], []
for w in words:
    t = w["text"]
    if t == "—":
        continue
    if t in ORD:
        if cur: chunks.append(cur); cur = []
        chunks.append([w]); continue
    cur.append(w)
    if t[-1] in "।,?" or len(cur) >= 4:
        chunks.append(cur); cur = []
if cur: chunks.append(cur)

def ts(s):
    s = max(s, 0); h = int(s // 3600); m = int(s % 3600 // 60)
    return f"{h}:{m:02d}:{s % 60:05.2f}"

ev = []
for i, c in enumerate(chunks):
    start = c[0]["start"]
    end = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else DUR
    end = min(end, c[-1]["end"] + 0.6)
    text = " ".join(w["text"] for w in c)
    if c[0]["text"] in ORD:
        n = ORD[c[0]["text"]]
        ev.append(f"Dialogue: 1,{ts(start)},{ts(end)},Head,,0,0,0,,{{\\fad(80,0)\\t(0,120,\\fscx112\\fscy112)\\t(120,240,\\fscx100\\fscy100)}}#{n} {text}")
    else:
        ev.append(f"Dialogue: 1,{ts(start)},{ts(end)},Sub,,0,0,0,,{text}")

# Point labels that stay up for each whole point (top-left of subtitle area).
starts = [c[0]["start"] for c in chunks if c[0]["text"] in ORD] + [43.5]
labels = ["RERA CHECK", "OC CERTIFICATE", "AUTHORITY DUES", "CARPET AREA", "EMI ≤ 35%"]
for i, lab in enumerate(labels):
    ev.append(f"Dialogue: 0,{ts(starts[i])},{ts(starts[i+1])},Tag,,0,0,0,,{{\\fad(150,150)}}{i+1}/5 · {lab}")

ass = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Sign,Inter Display Black,96,&H00F2F2F2,&H00F2F2F2,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,0,3,8,40,40,95,1
Style: Title,Inter Display Black,86,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,6,4,8,30,30,1000,1
Style: Sub,Noto Sans Devanagari,76,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,6,3,2,50,50,210,1
Style: Head,Noto Sans Devanagari,104,&H0000D7FF,&H0000D7FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,4,2,50,50,200,1
Style: Tag,Inter Display Black,46,&H00000000,&H00000000,&H0000D7FF,&H0000D7FF,-1,0,0,0,100,100,1,0,3,14,0,2,50,50,390,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ts(0)},{ts(DUR)},Sign,,0,0,0,,PAISA SAHAYATA\\NKENDRA
Dialogue: 0,{ts(0)},{ts(DUR)},Title,,0,0,0,,NOIDA MEIN FLAT\\NLENE SE PEHLE\\N{{\\c&H0000D7FF&}}KYA DEKHEIN?
""" + "\n".join(ev) + "\n"
open("subs.ass", "w").write(ass)

# Crop a 9:16 window around the character + cat from the 2048x1152 landscape still.
crop = "crop=648:1152:700:0"
zoom = f"scale={W*2}:{H*2},zoompan=z='min(1+0.0009*on,1.08)':x='iw/2-(iw/zoom/2)':y='ih/3-(ih/zoom/3)':d={int(DUR*FPS)}:s={W}x{H}:fps={FPS}"
boxes = ",".join([
    # sign plate over the misspelled AI sign
    "drawbox=x=30:y=40:w=1020:h=330:color=0x163a73@1:t=fill",
    "drawbox=x=30:y=40:w=1020:h=330:color=0xd9d9d9@1:t=8",
    # title banner: navy fill with yellow rails
    "drawbox=x=0:y=985:w=1080:h=330:color=0x1a2a6c@0.92:t=fill",
    "drawbox=x=0:y=978:w=1080:h=12:color=0xffd700@1:t=fill",
    "drawbox=x=0:y=1312:w=1080:h=12:color=0xffd700@1:t=fill",
])
vf = f"{crop},{zoom},{boxes},ass=subs.ass,format=yuv420p"
cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", "image.png", "-i", "voice.mp3",
       "-vf", vf, "-t", str(DUR), "-r", str(FPS),
       "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
       "-af", "apad", "-shortest", "-movflags", "+faststart", "noida_flat_short.mp4"]
if len(sys.argv) > 1:  # preview frames only
    for t in sys.argv[1:]:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", "image.png", "-vf", vf.replace(f"d={int(DUR*FPS)}", "d=1"),
                        "-ss", "0", "-frames:v", "1", f"frame_{t}.jpg"], check=True) if False else None
    sys.exit()
subprocess.run(cmd, check=True)
