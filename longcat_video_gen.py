# -*- coding: utf-8 -*-
"""
Optional integration with meituan-longcat/LongCat-Video
(https://github.com/meituan-longcat/LongCat-Video), used to animate each
scene's background image into a short generated video clip instead of the
default ffmpeg zoompan (Ken Burns) effect in build.py.

This module is deliberately import-light (no torch/diffusers) so build.py
can import it unconditionally; the heavy LongCat-Video dependencies only
need to exist wherever LONGCAT_VIDEO_REPO_DIR points, and only get invoked
via subprocess when the feature is enabled.

Disabled by default. Enable with:

    export LONGCAT_VIDEO_ENABLED=1
    export LONGCAT_VIDEO_REPO_DIR=/path/to/LongCat-Video   # checked-out repo with weights/ downloaded
    python3 build.py

See LONGCAT_VIDEO.md for full setup instructions.

UNVERIFIED: authored without access to a GPU or the model weights, so the
subprocess invocation below has not been exercised end to end. Treat
generate_scene_clip() as a best-effort integration point -- it fails soft
(returns False) on any error so build.py always has a working fallback.
"""
import os
import subprocess

W, H = 1920, 1080
FPS = 30

LONGCAT_ENABLED = os.environ.get("LONGCAT_VIDEO_ENABLED", "0") == "1"
LONGCAT_REPO_DIR = os.environ.get("LONGCAT_VIDEO_REPO_DIR", "/home/claude/LongCat-Video")
LONGCAT_CHECKPOINT_DIR = os.environ.get(
    "LONGCAT_VIDEO_CHECKPOINT_DIR",
    os.path.join(LONGCAT_REPO_DIR, "weights", "LongCat-Video"),
)
LONGCAT_GEN_FPS = int(os.environ.get("LONGCAT_VIDEO_GEN_FPS", "15"))
LONGCAT_USE_DISTILL = os.environ.get("LONGCAT_VIDEO_USE_DISTILL", "1") == "1"
LONGCAT_RESOLUTION = os.environ.get("LONGCAT_VIDEO_RESOLUTION", "480p")
LONGCAT_NPROC = os.environ.get("LONGCAT_VIDEO_NPROC_PER_NODE", "1")

_RUNNER_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "longcat_i2v_runner.py")

DEFAULT_MOTION_SUFFIX = (
    ", subtle cinematic camera motion, slow push-in, muted documentary "
    "color grade, no text or subtitles"
)


def nearest_valid_frame_count(n, minimum=13):
    """LongCat-Video's temporal VAE requires num_frames % 4 == 1."""
    n = max(int(round(n)), minimum)
    remainder = (n - 1) % 4
    if remainder:
        n += 4 - remainder
    return n


def is_available():
    """Cheap local check that the feature is enabled AND plausibly set up.

    This does not guarantee generation will succeed (that also needs a
    GPU, matching CUDA/torch build, etc.) -- it just avoids shelling out
    when the obvious prerequisites are missing.
    """
    if not LONGCAT_ENABLED:
        return False
    if not os.path.isdir(LONGCAT_REPO_DIR):
        return False
    if not os.path.isdir(LONGCAT_CHECKPOINT_DIR):
        return False
    return True


def _scale_pad_fit(src_path, out_path, duration):
    """Fit an arbitrary-resolution/fps clip to the pipeline's WxH/FPS canvas
    and exactly `duration` seconds, matching make_silent_clip()'s contract.
    """
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=decrease,"
        f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
        f"fps={FPS},"
        f"tpad=stop_mode=clone:stop_duration={duration},"
        f"format=yuv420p"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-i", src_path, "-vf", vf, "-t", f"{duration}",
         "-an", "-c:v", "libx264", out_path],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
    )


def generate_scene_clip(image_path, duration, out_path, prompt, negative_prompt=None,
                         tmp_dir=None, seed=42):
    """Generate one LongCat-Video image-to-video clip for a scene, fit to
    `duration` seconds on the pipeline's WxH/FPS canvas, written to
    `out_path`. Returns True on success, False on any failure (in which
    case the caller should fall back to the zoompan path in build.py).
    """
    if not is_available():
        return False

    tmp_dir = tmp_dir or os.path.dirname(os.path.abspath(out_path))
    raw_out = os.path.join(tmp_dir, os.path.basename(out_path) + ".longcat_raw.mp4")
    num_frames = nearest_valid_frame_count(duration * LONGCAT_GEN_FPS)

    cmd = [
        "torchrun", f"--nproc_per_node={LONGCAT_NPROC}",
        _RUNNER_SCRIPT,
        "--checkpoint_dir", LONGCAT_CHECKPOINT_DIR,
        "--image", image_path,
        "--prompt", prompt + DEFAULT_MOTION_SUFFIX,
        "--out", raw_out,
        "--num_frames", str(num_frames),
        "--fps", str(LONGCAT_GEN_FPS),
        "--resolution", LONGCAT_RESOLUTION,
        "--seed", str(seed),
    ]
    if negative_prompt:
        cmd += ["--negative_prompt", negative_prompt]
    if LONGCAT_USE_DISTILL:
        cmd += ["--use_distill"]

    try:
        subprocess.run(
            cmd, check=True, cwd=LONGCAT_REPO_DIR,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        _scale_pad_fit(raw_out, out_path, duration)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
        print(f"[longcat_video_gen] generation failed for {image_path!r}, "
              f"falling back to zoompan: {e}")
        return False
    finally:
        if os.path.exists(raw_out):
            os.remove(raw_out)
