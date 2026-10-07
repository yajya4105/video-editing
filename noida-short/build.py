"""Assemble the multi-shot vertical short.

Pipeline (all local, no credits):
  shots.json  -> one clip per cut (crop + Ken Burns move via zoompan, optional fx)
  words.json  -> subs.ass (word-timed Hindi subtitles, point headings, point tags)
  concat clips + title banner + subtitles + voice.mp3 -> noida_flat_short.mp4

Usage: python3 build.py            # full render
       python3 build.py preview    # also dump one still per shot to previews/
"""
import json, os, subprocess, sys

W, H, FPS, DUR = 1080, 1920, 30, 48.6
ORD = {"पहला": "1", "दूसरा": "2", "तीसरा": "3", "चौथा": "4", "पाँचवाँ": "5"}
LABELS = ["RERA CHECK", "OC CERTIFICATE", "AUTHORITY DUES", "CARPET AREA", "EMI ≤ 35%"]
OUT = "noida_flat_short.mp4"


def run(cmd):
    subprocess.run(cmd, check=True)


def ts(s):
    s = max(s, 0)
    return f"{int(s // 3600)}:{int(s % 3600 // 60):02d}:{s % 60:05.2f}"


# ---------- subtitles ----------
def build_subs():
    words = [w for w in json.load(open("words.json"))["words"] if w["type"] == "word"]
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

    ev = []
    for i, c in enumerate(chunks):
        start = c[0]["start"]
        end = chunks[i + 1][0]["start"] if i + 1 < len(chunks) else DUR
        end = min(end, c[-1]["end"] + 0.6)
        text = " ".join(w["text"] for w in c)
        if c[0]["text"] in ORD:
            ev.append(f"Dialogue: 1,{ts(start)},{ts(end)},Head,,0,0,0,,"
                      f"{{\\t(0,120,\\fscx115\\fscy115)\\t(120,240,\\fscx100\\fscy100)}}#{ORD[c[0]['text']]} {text}")
        else:
            ev.append(f"Dialogue: 1,{ts(start)},{ts(end)},Sub,,0,0,0,,{text}")

    starts = [c[0]["start"] for c in chunks if c[0]["text"] in ORD] + [43.5]
    for i, lab in enumerate(LABELS):
        ev.append(f"Dialogue: 0,{ts(starts[i])},{ts(starts[i + 1])},Tag,,0,0,0,,{{\\fad(150,150)}}{i + 1}/5 · {lab}")

    open("subs.ass", "w").write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,Inter Display Black,74,&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,-1,0,0,0,100,100,0,0,1,5,3,8,30,30,48,1
Style: Sub,Noto Sans Devanagari,80,&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,7,3,2,50,50,300,1
Style: Head,Noto Sans Devanagari,110,&H0000D7FF,&H0000D7FF,&H00000000,&H96000000,-1,0,0,0,100,100,0,0,1,8,4,2,50,50,290,1
Style: Tag,Inter Display Black,46,&H00000000,&H00000000,&H0000D7FF,&H0000D7FF,-1,0,0,0,100,100,1,0,3,14,0,2,50,50,480,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,{ts(0)},{ts(DUR)},Title,,0,0,0,,NOIDA MEIN FLAT\\NLENE SE PEHLE\\N{{\\c&H0000D7FF&}}KYA DEKHEIN?
""" + "\n".join(ev) + "\n")


# ---------- shots ----------
def motion(move, n):
    c = "x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2'"
    return {
        "in":    f"z='1+0.12*on/{n}':{c}",
        "out":   f"z='1.12-0.12*on/{n}':{c}",
        "left":  f"z='1.12':x='(iw-iw/zoom)*(1-on/{n})':y='ih/2-ih/zoom/2'",
        "right": f"z='1.12':x='(iw-iw/zoom)*on/{n}':y='ih/2-ih/zoom/2'",
        "up":    f"z='1.12':x='iw/2-iw/zoom/2':y='(ih-ih/zoom)*(1-on/{n})'",
        "punch": f"z='if(lt(on,6),1.30-0.05*on,1+0.05*(on-6)/{n})':{c}",
    }[move]


def fx(name):
    if name == "bars":  # jail bars for the "EMI ki jail" line
        bars = [f"drawbox=x={60 + k * 180}:y=0:w=46:h={H}:color=0x262626@1:t=fill" for k in range(6)]
        return "," + ",".join(bars + [f"drawbox=x=0:y=560:w={W}:h=40:color=0x262626@1:t=fill"])
    return ""


def build_clips(preview=False):
    shots = json.load(open("shots.json"))["shots"]
    os.makedirs("clips", exist_ok=True)
    if preview: os.makedirs("previews", exist_ok=True)
    edges = [round(s["t"] * FPS) for s in shots] + [round(DUR * FPS)]
    names = []
    for i, s in enumerate(shots):
        n = edges[i + 1] - edges[i]
        crop = (f"crop={s['crop'][0]}:{s['crop'][1]}:{s['crop'][2]}:{s['crop'][3]}" if s["crop"]
                else "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)'")
        vf = (f"{crop},scale={W * 2}:{H * 2},zoompan={motion(s['move'], n)}:d={n}:s={W}x{H}:fps={FPS}"
              f"{fx(s.get('fx', ''))},setsar=1,format=yuv420p")
        name = f"clips/{i:02d}.mp4"
        run(["ffmpeg", "-v", "error", "-y", "-i", s["src"], "-vf", vf, "-frames:v", str(n),
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-r", str(FPS), name])
        if preview:
            run(["ffmpeg", "-v", "error", "-y", "-ss", str(n / FPS / 2), "-i", name, "-frames:v", "1",
                 "-vf", "scale=270:-1", f"previews/{i:02d}.jpg"])
        names.append(name)
    open("clips/list.txt", "w").write("".join(f"file '{os.path.basename(p)}'\n" for p in names))


def final():
    banner = ",".join([
        f"drawbox=x=0:y=0:w={W}:h=372:color=0x1a2a6c@0.94:t=fill",
        f"drawbox=x=0:y=372:w={W}:h=12:color=0xffd700@1:t=fill",
    ])
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", "clips/list.txt", "-i", "voice.mp3",
         "-vf", f"{banner},ass=subs.ass,format=yuv420p", "-t", str(DUR),
         "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
         "-af", "apad", "-shortest", "-movflags", "+faststart", OUT])


if __name__ == "__main__":
    build_subs()
    build_clips(preview="preview" in sys.argv)
    final()
    print("wrote", OUT)
