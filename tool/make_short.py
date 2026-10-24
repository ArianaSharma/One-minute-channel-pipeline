#!/usr/bin/env python3
"""Celebrity-Verse Short builder: script.json -> 1080x1920 MP4.
Piper narration per scene, generated visuals (no third-party images),
word-highlight captions, synthesized music bed with ducking, loudness-normalised."""
import json, os, subprocess, sys, wave, math, re
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = os.environ.get("PIPER_VOICE", os.path.join(HERE, "voices/en-us-lessac-medium.onnx"))
W, H, FPS = 1080, 1920, 30
F_HEAD = "/usr/share/fonts/opentype/inter/InterDisplay-Black.otf"
F_BOLD = "/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf"
F_SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
GAP = 0.28  # silence between scenes (s)
SR = None

spec = json.load(open(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "script.json")))
out_dir = os.path.join(HERE, "out", spec["slug"]); os.makedirs(out_dir, exist_ok=True)

def hexrgb(h): h = h.lstrip("#"); return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

# ---------- 1. narration ----------
def tts(text, path):
    # spell-outs for words Piper mangles
    t = text.replace("Celebrity-Verse", "Celebrity Verse").replace("crore", "crore")
    subprocess.run([sys.executable, "-m", "piper", "-m", VOICE, "-f", path, "--length-scale", "0.93", "--sentence-silence", "0.15"],
                   input=t.encode(), check=True, capture_output=True)
    with wave.open(path) as w:
        return w.readframes(w.getnframes()), w.getframerate()

pcm_all, timings, t = [], [], 0.25
for i, sc in enumerate(spec["scenes"]):
    raw, sr = tts(sc["say"], os.path.join(out_dir, f"s{i}.wav"))
    a = np.frombuffer(raw, np.int16)
    SR = SR or sr
    if sr != SR: raise SystemExit(f"sample rate changed {sr}")
    # trim leading/trailing near-silence
    nz = np.where(np.abs(a) > 300)[0]
    a = a[max(0, nz[0] - 600): nz[-1] + 1200] if len(nz) else a
    dur = len(a) / SR
    if not pcm_all: pcm_all.append(np.zeros(int(0.25 * SR), np.int16))
    timings.append((t, t + dur)); pcm_all.append(a)
    t += dur
    pad = GAP if i < len(spec["scenes"]) - 1 else 0.9
    pcm_all.append(np.zeros(int(pad * SR), np.int16)); t += pad
voice = np.concatenate(pcm_all)
TOTAL = len(voice) / SR
voice_path = os.path.join(out_dir, "voice.wav")
with wave.open(voice_path, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(voice.tobytes())

# word timings: spread each scene's span by word length (letters + small constant)
words = []
for (s, e), sc in zip(timings, spec["scenes"]):
    ws = sc["say"].split()
    wt = np.array([len(re.sub(r"\W", "", x)) + 2.2 + (2.5 if re.search(r"[.,?!]$", x) else 0) for x in ws], float)
    edges = s + (e - s) * np.concatenate([[0], np.cumsum(wt) / wt.sum()])
    for k, x in enumerate(ws): words.append((edges[k], edges[k + 1], x, len(words), timings.index((s, e))))

# ---------- 2. music bed (A minor suspense pad + soft pulse), ducked under voice ----------
MSR = 44100; n = int(TOTAL * MSR); tt = np.arange(n) / MSR
chords = [(220.0, 261.63, 329.63), (174.61, 220.0, 261.63), (196.0, 246.94, 293.66), (164.81, 207.65, 246.94)]
pad = np.zeros(n)
bar = 60 / 92 * 4
for ci in range(int(TOTAL / bar) + 1):
    a0, a1 = int(ci * bar * MSR), min(n, int((ci + 1) * bar * MSR) + int(0.4 * MSR))
    if a0 >= n: break
    seg = tt[a0:a1] - ci * bar
    env = np.minimum(1, seg / 0.6) * np.exp(-np.maximum(0, seg - bar) * 6)
    for f in chords[ci % 4]:
        pad[a0:a1] += env * (np.sin(2 * np.pi * f / 2 * seg) * 0.5 + np.sin(2 * np.pi * f * seg + 0.3 * np.sin(2 * np.pi * 0.3 * seg)) * 0.25)
beat = 60 / 92
for b in range(int(TOTAL / beat)):
    a0 = int(b * beat * MSR); L = min(n - a0, int(0.35 * MSR))
    if L <= 0: break
    s = np.arange(L) / MSR
    pad[a0:a0 + L] += np.sin(2 * np.pi * (55 + 40 * np.exp(-s * 30)) * s) * np.exp(-s * 9) * (0.9 if b % 2 == 0 else 0.5)
pad /= np.max(np.abs(pad)) + 1e-9
# duck: envelope from voice
v44 = np.interp(np.arange(n) / MSR, np.arange(len(voice)) / SR, np.abs(voice.astype(float)) / 32768)
k = int(0.25 * MSR); env = np.convolve(v44, np.ones(k) / k, mode="same")
duck = 1 - 0.65 * np.clip(env * 12, 0, 1)
fade = np.minimum(1, tt / 1.0) * np.minimum(1, (TOTAL - tt) / 1.2)
music = (pad * duck * fade * 0.16 * 32767).astype(np.int16)
music_path = os.path.join(out_dir, "music.wav")
with wave.open(music_path, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(MSR); w.writeframes(music.tobytes())

# ---------- 3. visuals ----------
fh = {s: ImageFont.truetype(F_HEAD, s) for s in (210, 190, 170, 150, 130, 115)}
fcap = ImageFont.truetype(F_BOLD, 64)
fsub = ImageFont.truetype(F_SEMI, 46)
fsmall = ImageFont.truetype(F_SEMI, 30)
ftag = ImageFont.truetype(F_BOLD, 34)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
top, bot = np.array([18, 14, 38], np.float32), np.array([6, 10, 24], np.float32)
grad = (top[None, None] * (1 - yy[..., None] / H) + bot[None, None] * (yy[..., None] / H))
rng = np.random.default_rng(7)
grains = [rng.normal(0, 5, (H // 2, W // 2, 1)).astype(np.float32) for _ in range(6)]

def background(tsec, accent):
    cx = W * (0.5 + 0.28 * math.sin(tsec * 0.5)); cy = H * (0.33 + 0.06 * math.cos(tsec * 0.37))
    d2 = ((xx - cx) ** 2 + (yy - cy) ** 2) / (520.0 ** 2)
    glow = np.exp(-d2)[..., None] * np.array(accent, np.float32)[None, None] * 0.38
    beam = np.exp(-(((xx - cx) * 1.0) ** 2) / (2 * (140 + yy * 0.18) ** 2))[..., None] * (1 - yy[..., None] / H) * 26
    g = grains[int(tsec * 12) % 6].repeat(2, 0).repeat(2, 1)
    img = np.clip(grad + glow + beam + g, 0, 255).astype(np.uint8)
    return Image.fromarray(img)

def draw_icon(d, kind, cx, cy, s, col, ph):
    w = max(6, int(s * 0.09))
    if kind == "gavel":
        ang = math.radians(-35 + 12 * math.sin(ph * 6))
        def rot(px, py): return (cx + px * math.cos(ang) - py * math.sin(ang), cy + px * math.sin(ang) + py * math.cos(ang))
        head = [rot(-s*.42, -s*.62), rot(s*.42, -s*.62), rot(s*.42, -s*.22), rot(-s*.42, -s*.22)]
        d.polygon(head, fill=col)
        d.line([rot(0, -s*.22), rot(0, s*.55)], fill=col, width=w * 2)
        d.rounded_rectangle([cx - s*.6, cy + s*.62, cx + s*.6, cy + s*.78], radius=8, fill=col)
    elif kind == "film":
        d.rounded_rectangle([cx - s*.75, cy - s*.5, cx + s*.75, cy + s*.5], radius=18, outline=col, width=w)
        off = (ph * 120) % (s * .3)
        for k in range(-3, 4):
            x = cx - s*.6 + k * s*.3 + off
            if cx - s*.7 < x < cx + s*.6:
                for yv in (cy - s*.42, cy + s*.32): d.rectangle([x, yv, x + s*.12, yv + s*.1], fill=col)
        d.polygon([(cx - s*.15, cy - s*.2), (cx - s*.15, cy + s*.2), (cx + s*.22, cy)], fill=col)
    elif kind == "coin":
        r = s * .55 * (1 + 0.04 * math.sin(ph * 5))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=col, width=w)
        f = ImageFont.truetype(F_HEAD, int(s * .7)); tb = d.textbbox((0, 0), "₹", font=f)
        d.text((cx - (tb[2]+tb[0]) / 2, cy - (tb[3]+tb[1]) / 2), "₹", font=f, fill=col)
    elif kind == "ask":
        f = ImageFont.truetype(F_HEAD, int(s * 1.2)); tb = d.textbbox((0, 0), "?", font=f)
        d.text((cx - (tb[2]+tb[0]) / 2, cy - (tb[3]+tb[1]) / 2 + 6 * math.sin(ph * 4)), "?", font=f, fill=col)

def fit_head(lines):
    for s, f in fh.items():
        if all(f.getlength(l) <= W - 150 for l in lines): return f
    return fh[115]

def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3

def caption_lines(scene_words, maxw=W - 160):
    lines, cur = [], []
    for wd in scene_words:
        test = " ".join(x[2] for x in cur + [wd])
        if cur and fcap.getlength(test) > maxw: lines.append(cur); cur = [wd]
        else: cur.append(wd)
    if cur: lines.append(cur)
    return lines

scene_caps = {i: caption_lines([w for w in words if w[4] == i]) for i in range(len(spec["scenes"]))}

def frame(tsec):
    # current scene = last scene whose start <= t
    si = 0
    for i, (s, e) in enumerate(timings):
        if tsec >= s - 0.12: si = i
    sc = spec["scenes"][si]; s0, e0 = timings[si]; acc = hexrgb(sc["accent"])
    img = background(tsec, acc); d = ImageDraw.Draw(img)
    ph = tsec - s0; k = ease((ph + 0.12) / 0.38)
    # top tag
    d.rounded_rectangle([72, 150, 72 + ftag.getlength(spec["tag"]) + 56, 214], radius=32, fill=acc)
    d.text((100, 160), spec["tag"], font=ftag, fill=(10, 10, 20))
    d.text((W - 72 - fsmall.getlength("CELEBRITY-VERSE"), 168), "CELEBRITY-VERSE", font=fsmall, fill=(220, 225, 240))
    # icon
    draw_icon(d, sc["icon"], W / 2, 380 - 40 * (1 - k), 230, acc + (255,) if False else acc, tsec)
    # headline (slide up + fade via colour blend)
    lines = sc["head"].split("\n"); f = fit_head(lines)
    lh = f.size * 1.02; y = 610 + 60 * (1 - k)
    for j, l in enumerate(lines):
        kk = ease((ph + 0.12 - j * 0.09) / 0.38)
        col = tuple(int(255 * kk + 20 * (1 - kk)) for _ in range(3))
        d.text(((W - f.getlength(l)) / 2, y + j * lh), l, font=f, fill=col if j == 0 else tuple(int(c * kk + 20 * (1 - kk)) for c in acc))
    yb = y + len(lines) * lh + 30
    d.text(((W - fsub.getlength(sc["sub"])) / 2, yb), sc["sub"], font=fsub, fill=(205, 210, 228))
    # captions: show the line containing the current word (plus the next line)
    caps = scene_caps[si]; cur_idx = max([w[3] for w in words if w[4] == si and w[0] <= tsec] or [None] if False else [-1])
    li = 0
    for n_, ln in enumerate(caps):
        if any(w[3] == cur_idx for w in ln): li = n_
    show = caps[li:li + 2]
    cy = 1200
    box_h = 40 + len(show) * 86
    d.rounded_rectangle([60, cy - 24, W - 60, cy - 24 + box_h], radius=28, fill=(8, 8, 18))
    for r, ln in enumerate(show):
        tx = " ".join(w[2] for w in ln); x = (W - fcap.getlength(tx)) / 2
        for w in ln:
            said = w[3] <= cur_idx; now = w[3] == cur_idx
            colr = acc if now else ((255, 255, 255) if said else (150, 155, 175))
            d.text((x, cy + r * 86), w[2], font=fcap, fill=colr)
            x += fcap.getlength(w[2] + " ")
    # sources + progress
    src = spec["source_line"]; parts = [src] if fsmall.getlength(src) < W - 140 else src.split(" via ")
    if len(parts) == 2: parts[1] = "via " + parts[1]
    for r, ptxt in enumerate(parts):
        d.text(((W - fsmall.getlength(ptxt)) / 2, 1420 + r * 40), ptxt, font=fsmall, fill=(140, 146, 170))
    d.rectangle([0, H - 14, W * min(1, tsec / TOTAL), H], fill=acc)
    return img

silent = os.path.join(out_dir, "video_silent.mp4")
nframes = int(TOTAL * FPS)
p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                      "-c:v", "libx264", "-preset", "veryfast", "-b:v", "1400k", "-maxrate", "1800k", "-bufsize", "3000k", "-pix_fmt", "yuv420p", silent], stdin=subprocess.PIPE)
for fi in range(nframes):
    p.stdin.write(frame(fi / FPS).tobytes())
    if fi % 300 == 0: print(f"frame {fi}/{nframes}", flush=True)
p.stdin.close(); p.wait()

final = os.path.join(out_dir, f"{spec['slug']}.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", silent, "-i", voice_path, "-i", music_path, "-filter_complex",
                "[1:a]aresample=44100,pan=stereo|c0=c0|c1=c0,highpass=f=70,acompressor=threshold=0.1:ratio=3[v];"
                "[2:a]pan=stereo|c0=c0|c1=c0[m];[v][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=9[a]",
                "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-ar", "44100", "-shortest", "-movflags", "+faststart", final], check=True)
print("DONE", final, f"{TOTAL:.1f}s")
