# -*- coding: utf-8 -*-
import os
import re
import json
import subprocess
import wave
import contextlib
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from script import TITLE, SCENES, INTRO_IMAGE, OUTRO_IMAGE
import longcat_video_gen

_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
         "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
         "eighteen", "nineteen"]
_TENS = ["zero", "ten", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]


def _two_digit_words(x):
    if x == 0:
        return ""
    if x < 20:
        return _ONES[x]
    t, o = divmod(x, 10)
    return _TENS[t] + (f" {_ONES[o]}" if o else "")


def _year_words(n):
    # 1896 -> "eighteen hundred ninety six" (user-specified style, not "eighteen ninety six")
    first_two, last_two = divmod(n, 100)
    words = f"{_two_digit_words(first_two)} hundred"
    if last_two:
        words += f" {_two_digit_words(last_two)}"
    return words


def normalize_narration(text):
    # Expand bare 4-digit years (1000-2099) so Piper doesn't read them as
    # plain cardinal numbers ("one thousand eight hundred ninety six").
    def repl(m):
        return _year_words(int(m.group(0)))
    return re.sub(r"\b(1[0-9]{3}|20[0-9]{2})\b", repl, text)

W, H = 1920, 1080
OUT = "/home/claude/one-minute-video/out"
os.makedirs(OUT, exist_ok=True)
VOICE = "/home/claude/one-minute-video/voices/en-us-lessac-medium.onnx"

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# A small rotating palette of dark gradient tones (no external images needed)
PALETTES = [
    ((15, 23, 42), (30, 58, 138)),   # navy -> blue
    ((24, 24, 27), (76, 29, 149)),   # near-black -> violet
    ((12, 30, 26), (5, 90, 80)),     # deep green -> teal
    ((40, 20, 10), (120, 53, 15)),   # brown -> amber
    ((20, 10, 30), (109, 40, 217)),  # plum -> purple
    ((10, 20, 30), (14, 116, 144)),  # slate -> cyan
]


def make_gradient(size, top_color, bottom_color):
    img = Image.new("RGB", size, top_color)
    draw = ImageDraw.Draw(img)
    h = size[1]
    for y in range(h):
        t = y / h
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        draw.line([(0, y), (size[0], y)], fill=(r, g, b))
    return img


def wrap_and_draw_centered(draw, text, font, max_width, center_x, center_y, fill, line_spacing=1.35):
    lines = text.split("\n")
    sizes = [draw.textbbox((0, 0), ln, font=font) for ln in lines]
    heights = [b[3] - b[1] for b in sizes]
    line_h = max(heights) * line_spacing
    total_h = line_h * len(lines)
    y = center_y - total_h / 2
    for ln in lines:
        bbox = draw.textbbox((0, 0), ln, font=font)
        w = bbox[2] - bbox[0]
        x = center_x - w / 2
        # soft shadow for readability
        draw.text((x + 3, y + 3), ln, font=font, fill=(0, 0, 0, 160))
        draw.text((x, y), ln, font=font, fill=fill)
        y += line_h


def slugify(text):
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "video"


def make_card(caption, idx, out_path, big=False, icon=None, bg_image=None):
    if bg_image:
        img = Image.open(bg_image).convert("RGB").resize((W, H), Image.LANCZOS)
    else:
        # Fallback for any scene without real artwork: flat gradient card.
        top, bottom = PALETTES[idx % len(PALETTES)]
        img = make_gradient((W, H), top, bottom).convert("RGB")
        vign = Image.new("L", (W, H), 0)
        vd = ImageDraw.Draw(vign)
        vd.ellipse((-W * 0.3, -H * 0.3, W * 1.3, H * 1.3), fill=90)
        vign = vign.filter(ImageFilter.GaussianBlur(200))
        dark = Image.new("RGB", (W, H), (0, 0, 0))
        img = Image.composite(img, dark, vign)

    # Dark scrim across the lower portion so caption text stays legible over
    # a real photo/illustration background.
    scrim = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(scrim)
    scrim_top = int(H * 0.52)
    for y in range(scrim_top, H):
        t = (y - scrim_top) / (H - scrim_top)
        sd.line([(0, y), (W, y)], fill=int(190 * t))
    black = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.composite(black, img, scrim)

    draw = ImageDraw.Draw(img)

    font_size = 100 if big else 84
    font = ImageFont.truetype(FONT_BOLD, font_size)
    text_y = H * 0.5 if big else H * 0.78
    wrap_and_draw_centered(draw, caption, font, W * 0.85, W / 2, text_y, fill=(255, 255, 255))

    # watermark
    wm_font = ImageFont.truetype(FONT_BOLD, 32)
    wm = "THE ONE MINUTE CHANNEL"
    bbox = draw.textbbox((0, 0), wm, font=wm_font)
    wm_w = bbox[2] - bbox[0]
    draw.text((W / 2 - wm_w / 2, H - 70), wm, font=wm_font, fill=(255, 255, 255, 180))

    img.save(out_path, quality=95)


def synth(text, out_wav):
    text = normalize_narration(text)
    p = subprocess.run(
        ["python3", "-m", "piper", "-m", VOICE, "-f", out_wav],
        input=text.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stderr.decode())


def wav_duration(path):
    with contextlib.closing(wave.open(path, "r")) as f:
        frames = f.getnframes()
        rate = f.getframerate()
        return frames / float(rate)


def split_phrases(text, chunk_size=4):
    words = text.split()
    return [" ".join(words[i:i + chunk_size]) for i in range(0, len(words), chunk_size)] or [text]


def phrase_timings(narration_text, total_duration, chunk_size=4):
    phrases = split_phrases(narration_text, chunk_size)
    lengths = [max(len(p), 1) for p in phrases]
    total_len = sum(lengths)
    timings = []
    t = 0.0
    for p, l in zip(phrases, lengths):
        pdur = total_duration * (l / total_len)
        timings.append((p, t, pdur))
        t += pdur
    return timings


def make_music(duration, out_path, sr=44100):
    import numpy as np
    import scipy.io.wavfile as wavfile

    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    root, fifth, octave = 73.42, 73.42 * 1.5, 73.42 * 2  # low D-minor-ish drone
    sig = (
        0.5 * np.sin(2 * np.pi * root * t)
        + 0.3 * np.sin(2 * np.pi * fifth * t)
        + 0.15 * np.sin(2 * np.pi * octave * t + 0.5)
    )
    lfo = 0.85 + 0.15 * np.sin(2 * np.pi * 0.07 * t)  # slow tremolo for movement
    sig = sig * lfo
    shimmer = 0.05 * np.sin(2 * np.pi * (octave * 2) * t + 0.3 * np.sin(2 * np.pi * 0.05 * t))
    sig = sig + shimmer
    sig = sig / np.max(np.abs(sig))

    fade_len = min(int(sr * 2), len(sig) // 2)
    sig[:fade_len] *= np.linspace(0, 1, fade_len)
    sig[-fade_len:] *= np.linspace(1, 0, fade_len)

    sig = sig * 0.5
    pcm = (sig * 32767).astype(np.int16)
    wavfile.write(out_path, sr, pcm)


# ---------------------------------------------------------------------------
# Audio-quality remediation (see Big-4-style audio audit):
#   1. make_silent_clip(): video-only render, no per-phrase audio slicing.
#      Narration is never cut mid-word anymore -- each scene's TTS output
#      stays one continuous, unsliced WAV from synthesis to final mix.
#   2. fade_wav(): a tiny (20ms) in/out fade applied only at the few real
#      scene-to-scene joins (7 total, down from 28), as cheap insurance
#      against any residual onset/offset click.
#   3. mix_and_duck(): resamples voice + music to 44.1kHz stereo (instead of
#      collapsing everything to Piper's native 16kHz mono) and sidechain-
#      ducks the music bed under the narration instead of a static blend.
#   4. apply_loudnorm(): two-pass loudness normalization to -14 LUFS with a
#      -1.5 dBTP true-peak ceiling, matching platform delivery norms instead
#      of leaving the master with ~0dB of peak headroom.
# ---------------------------------------------------------------------------

def make_silent_clip(image_path, duration, out_path, start_frame_offset=0, max_zoom=1.14, rate=0.00045):
    fps = 30
    frames = max(int(duration * fps), 1)
    zoom_expr = f"min(1+{rate}*({start_frame_offset}+on),{max_zoom})"
    vf = (
        f"zoompan=z='{zoom_expr}':d={frames}:s={W}x{H}:fps={fps},"
        f"format=yuv420p"
    )
    cmd = [
        "ffmpeg", "-y", "-loop", "1", "-i", image_path,
        "-vf", vf,
        "-c:v", "libx264", "-t", f"{duration}",
        "-an",
        out_path,
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def escape_drawtext(text):
    return (text.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "’").replace("%", "\\%"))


def caption_overlay_filter(timings, font_path=FONT_BOLD, font_size=84, text_y_frac=0.78):
    # Burns each phrase in as an ffmpeg drawtext, timed to match the same
    # phrase_timings used to cut per-phrase cards in the zoompan path --
    # used instead of make_card() when a scene's background is an
    # animated LongCat-Video clip rather than a static image.
    parts = []
    for phrase, start, dur in timings:
        end = start + dur
        esc = escape_drawtext(phrase)
        parts.append(
            f"drawtext=fontfile={font_path}:text='{esc}':fontsize={font_size}:"
            f"fontcolor=white:shadowcolor=black@0.6:shadowx=3:shadowy=3:"
            f"x=(w-text_w)/2:y=h*{text_y_frac}-text_h/2:"
            f"enable='between(t\\,{start:.3f}\\,{end:.3f})'"
        )
    wm = escape_drawtext("THE ONE MINUTE CHANNEL")
    parts.append(
        f"drawtext=fontfile={font_path}:text='{wm}':fontsize=32:"
        f"fontcolor=white@0.7:x=(w-text_w)/2:y=h-70"
    )
    return ",".join(parts)


def overlay_captions(video_in, video_out, timings):
    vf = caption_overlay_filter(timings)
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_in, "-vf", vf, "-an", "-c:v", "libx264", video_out],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def fade_wav(in_wav, out_wav, fade_s=0.02):
    dur = wav_duration(in_wav)
    st = max(dur - fade_s, 0)
    subprocess.run(
        ["ffmpeg", "-y", "-i", in_wav, "-af",
         f"afade=t=in:d={fade_s},afade=t=out:st={st:.3f}:d={fade_s}",
         out_wav],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def mix_and_duck(video_in, music_wav, video_out, music_level=0.22):
    filter_complex = (
        f"[0:a]aresample=44100,asplit=2[voice_sc][voice_mix];"
        f"[1:a]aresample=44100,volume={music_level}[music_pre];"
        f"[music_pre][voice_sc]sidechaincompress=threshold=0.05:ratio=7:attack=5:release=300:makeup=1[music_ducked];"
        f"[voice_mix]pan=stereo|c0=c0|c1=c0[voice_st];"
        f"[music_ducked]pan=stereo|c0=c0|c1=c0[music_st];"
        f"[voice_st][music_st]amix=inputs=2:duration=first:dropout_transition=3:normalize=0[aout]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_in, "-i", music_wav,
         "-filter_complex", filter_complex,
         "-map", "0:v", "-map", "[aout]",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "44100", "-ac", "2",
         video_out],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def apply_loudnorm(video_in, video_out, target_i=-14.0, target_tp=-1.5, target_lra=11.0):
    analyze = subprocess.run(
        ["ffmpeg", "-i", video_in, "-af",
         f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:print_format=json",
         "-f", "null", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    stderr = analyze.stderr.decode(errors="ignore")
    json_str = stderr[stderr.rfind("{"):stderr.rfind("}") + 1]
    stats = json.loads(json_str)

    af = (
        f"loudnorm=I={target_i}:TP={target_tp}:LRA={target_lra}:"
        f"measured_I={stats['input_i']}:measured_TP={stats['input_tp']}:"
        f"measured_LRA={stats['input_lra']}:measured_thresh={stats['input_thresh']}:"
        f"offset={stats['target_offset']}:linear=true:print_format=summary"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", video_in, "-af", af,
         "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "44100", "-ac", "2",
         video_out],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )
    return stats


def main():
    silent_clip_paths = []   # video-only clips, one per caption phrase (visual cuts only)
    audio_seg_paths = []     # one CONTINUOUS, unsliced audio piece per intro/scene/outro
    cumulative_frames = 0

    # Intro card (title only, ~2s, synthesize the title itself as a short intro line)
    intro_wav = f"{OUT}/intro.wav"
    synth(TITLE + ".", intro_wav)
    intro_dur = wav_duration(intro_wav)
    intro_img = f"{OUT}/intro.png"
    make_card(TITLE, 0, intro_img, big=True, bg_image=INTRO_IMAGE)
    intro_silent = f"{OUT}/intro_silent.mp4"
    make_silent_clip(intro_img, intro_dur, intro_silent, start_frame_offset=cumulative_frames)
    silent_clip_paths.append(intro_silent)
    cumulative_frames += int(intro_dur * 30)
    intro_faded = f"{OUT}/intro_faded.wav"
    fade_wav(intro_wav, intro_faded)
    audio_seg_paths.append(intro_faded)

    for i, scene in enumerate(SCENES, start=1):
        wav_path = f"{OUT}/scene_{i}.wav"
        synth(scene["narration"], wav_path)
        dur = wav_duration(wav_path)

        # Split the scene into short (~4-word) caption phrases with
        # proportional on-screen durations -- this now drives ONLY the
        # visual cuts. The narration audio itself is never sliced: it stays
        # one continuous WAV straight from TTS synthesis through to the
        # final mix, eliminating the mid-word splice clicks that a
        # per-phrase audio cut produced.
        normalized = normalize_narration(scene["narration"])
        timings = phrase_timings(normalized, dur, chunk_size=4)

        # Optional path: animate the whole scene with LongCat-Video
        # (one generated clip per scene) instead of a zoompan on a static
        # card per caption phrase, with captions burned in afterward via
        # ffmpeg drawtext at the same timings. Falls back to the zoompan
        # path below on any failure or when disabled (default).
        used_longcat = False
        if longcat_video_gen.is_available():
            longcat_raw = f"{OUT}/scene_{i}_longcat.mp4"
            motion_prompt = scene.get("motion_prompt", scene["narration"])
            ok = longcat_video_gen.generate_scene_clip(
                scene["bg_image"], dur, longcat_raw, motion_prompt,
                tmp_dir=OUT,
            )
            if ok:
                scene_silent = f"{OUT}/scene_{i}_silent.mp4"
                overlay_captions(longcat_raw, scene_silent, timings)
                silent_clip_paths.append(scene_silent)
                cumulative_frames += int(dur * 30)
                used_longcat = True

        if not used_longcat:
            for j, (phrase, start, pdur) in enumerate(timings):
                phrase_img = f"{OUT}/scene_{i}_p{j}.png"
                make_card(phrase, i, phrase_img, bg_image=scene["bg_image"])
                silent_clip = f"{OUT}/scene_{i}_p{j}_silent.mp4"
                make_silent_clip(phrase_img, pdur, silent_clip, start_frame_offset=cumulative_frames)
                silent_clip_paths.append(silent_clip)
                cumulative_frames += int(pdur * 30)

        scene_faded = f"{OUT}/scene_{i}_faded.wav"
        fade_wav(wav_path, scene_faded)
        audio_seg_paths.append(scene_faded)

    # Outro card
    outro_wav = f"{OUT}/outro.wav"
    synth("Subscribe to The One Minute Channel for more history in sixty seconds.", outro_wav)
    outro_dur = wav_duration(outro_wav)
    outro_img = f"{OUT}/outro.png"
    make_card("Subscribe for more\nhistory in 60 seconds.", len(SCENES) + 1, outro_img, big=True, bg_image=OUTRO_IMAGE)
    outro_silent = f"{OUT}/outro_silent.mp4"
    make_silent_clip(outro_img, outro_dur, outro_silent, start_frame_offset=cumulative_frames)
    silent_clip_paths.append(outro_silent)
    outro_faded = f"{OUT}/outro_faded.wav"
    fade_wav(outro_wav, outro_faded)
    audio_seg_paths.append(outro_faded)

    # Concat the silent video clips (stream copy -- all share the same
    # codec/resolution/fps, so no re-encode is needed here).
    vid_list = f"{OUT}/concat_video.txt"
    with open(vid_list, "w") as f:
        for c in silent_clip_paths:
            f.write(f"file '{os.path.abspath(c)}'\n")
    full_silent_video = f"{OUT}/full_silent_video.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", vid_list,
         "-c", "copy", full_silent_video],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )

    # Concat the continuous narration audio segments (stream copy on PCM --
    # sample-accurate, lossless). Only 7 real joins now (down from 28), each
    # at an actual sentence boundary and each already 20ms-faded above.
    aud_list = f"{OUT}/concat_audio.txt"
    with open(aud_list, "w") as f:
        for a in audio_seg_paths:
            f.write(f"file '{os.path.abspath(a)}'\n")
    full_audio = f"{OUT}/full_narration_audio.wav"
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", aud_list,
         "-c", "copy", full_audio],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )

    # Mux silent video + single continuous audio track -- one AAC encode
    # pass total for narration (vs. 28 independent per-clip encodes before).
    narration_only_path = f"{OUT}/narration_only.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-i", full_silent_video, "-i", full_audio,
         "-map", "0:v", "-map", "1:a",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
         narration_only_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )

    # Background music bed, synthesized locally (no external audio APIs
    # reachable from this sandbox), sidechain-ducked under the narration.
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", narration_only_path],
        check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    total_video_dur = float(probe.stdout.decode().strip())
    music_path = f"{OUT}/music.wav"
    make_music(total_video_dur + 1, music_path)

    premaster_path = f"{OUT}/premaster.mp4"
    mix_and_duck(narration_only_path, music_path, premaster_path)

    # Two-pass loudness normalization to -14 LUFS / -1.5 dBTP (platform
    # delivery standard) instead of leaving ~0dB of true-peak headroom.
    slug = slugify(TITLE)
    final_path = f"{OUT}/{slug}.mp4"
    stats = apply_loudnorm(premaster_path, final_path)
    print("Loudnorm pass:", stats)

    # Thumbnail (1280x720)
    thumb = Image.open(intro_img).resize((1280, 720))
    thumb.save(f"{OUT}/thumbnail.jpg", quality=95)

    total_dur = sum(wav_duration(p) for p in [intro_wav] + [f"{OUT}/scene_{i}.wav" for i in range(1, len(SCENES)+1)] + [outro_wav])
    print(f"DONE. Final video: {final_path}")
    print(f"Total narration duration: {total_dur:.1f}s")


if __name__ == "__main__":
    main()
