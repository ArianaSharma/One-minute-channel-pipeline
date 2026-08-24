# Optional: LongCat-Video scene animation

By default `build.py` animates each scene by zooming slowly into a static
background image (ffmpeg `zoompan`) with the caption baked into the image.

This repo can optionally use [LongCat-Video](https://github.com/meituan-longcat/LongCat-Video)
(Meituan's 13.6B-parameter image-to-video model) to generate one short,
actually-moving clip per scene instead, with the same captions burned in
afterward via ffmpeg `drawtext` at the original per-phrase timings.

**This integration is unverified.** It was written without access to a GPU
or the model weights, so treat it as a documented starting point to
validate on real hardware, not a tested feature. If it fails for any
reason, `build.py` automatically falls back to the existing zoompan path
scene-by-scene, so it's safe to try.

## Requirements

- A CUDA GPU with enough VRAM to run a 13.6B-parameter diffusion model
  (see LongCat-Video's own README for current guidance).
- Python 3.10, PyTorch 2.6.0, FlashAttention-2, as specified by
  LongCat-Video's `requirements.txt`.
- The model weights (tens of GB), downloaded via Hugging Face.

## Setup

1. Clone LongCat-Video and install its dependencies, following its README:

   ```bash
   git clone https://github.com/meituan-longcat/LongCat-Video.git
   cd LongCat-Video
   conda create -n longcat-video python=3.10
   conda activate longcat-video
   pip install -r requirements.txt
   huggingface-cli download meituan-longcat/LongCat-Video --local-dir ./weights/LongCat-Video
   ```

2. Copy (or symlink) this repo's `longcat_i2v_runner.py` into that checkout,
   so it can `import longcat_video` (the package LongCat-Video ships):

   ```bash
   cp /path/to/one-minute-channel-pipeline/longcat_i2v_runner.py ./LongCat-Video/
   ```

3. Point this pipeline at that checkout and enable the feature:

   ```bash
   export LONGCAT_VIDEO_ENABLED=1
   export LONGCAT_VIDEO_REPO_DIR=/path/to/LongCat-Video
   # optional overrides (defaults shown):
   export LONGCAT_VIDEO_CHECKPOINT_DIR=$LONGCAT_VIDEO_REPO_DIR/weights/LongCat-Video
   export LONGCAT_VIDEO_GEN_FPS=15
   export LONGCAT_VIDEO_USE_DISTILL=1   # 16-step distilled LoRA instead of 50-step base
   export LONGCAT_VIDEO_RESOLUTION=480p
   ```

4. Run the pipeline as usual:

   ```bash
   python3 build.py
   ```

   For each scene, `build.py` will try `torchrun --nproc_per_node=1
   longcat_i2v_runner.py ...` (via `longcat_video_gen.generate_scene_clip`)
   against the scene's `bg_image` and `motion_prompt` (see `script.py`). On
   success it scales/pads the result to the project's 1920x1080/30fps
   canvas, trims/holds it to the scene's narration duration, and overlays
   captions with `drawtext`. On any failure it logs a warning and falls
   back to the normal zoompan/`make_card` path for that scene.

## Files

- `longcat_i2v_runner.py` — a parameterized rewrite of LongCat-Video's own
  `run_demo_image_to_video.py` (which hard-codes the image/prompt/output
  path). Runs inside the LongCat-Video checkout via `torchrun`.
- `longcat_video_gen.py` — the orchestration layer `build.py` calls. Has no
  heavy ML dependencies itself; only shells out to the runner above when
  `LONGCAT_VIDEO_ENABLED=1` and the repo/checkpoint dirs look present.
- `motion_prompt` field on each scene in `script.py` — the text prompt
  describing the desired camera/subject motion, used only in this mode.

## Tuning notes (unverified, worth checking once you can test on a GPU)

- `num_frames` is rounded to satisfy LongCat-Video's temporal VAE
  constraint (`num_frames % 4 == 1`) — see `nearest_valid_frame_count()`
  in `longcat_video_gen.py`.
- The distilled path (`LONGCAT_VIDEO_USE_DISTILL=1`, 16 steps) trades
  quality for speed; for six ~7-10s scene clips per video this is likely
  necessary to keep render times reasonable versus the 50-step base path.
- LongCat-Video also ships a 720p refinement stage
  (`pipe.generate_refine`, used in its own demo) that isn't wired in here
  — it needs the stage-1 video as input and roughly doubles the work per
  clip. Worth adding once the base path is confirmed working.
