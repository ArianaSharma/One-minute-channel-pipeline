# -*- coding: utf-8 -*-
"""
Parameterized single-clip runner for LongCat-Video's image-to-video pipeline.

This is NOT part of the LongCat-Video project itself. It is a thin,
argument-driven rewrite of that project's `run_demo_image_to_video.py`,
which hard-codes the input image, prompt, frame count and output path
directly in source. This script exposes those as CLI flags so the
pipeline in this repo (see longcat_video_gen.py / build.py) can request
one short animated clip per scene.

Usage (must be run with the LongCat-Video repo checkout as the working
directory / on PYTHONPATH, since it imports the `longcat_video` package
that repo provides -- this script does NOT bundle or reimplement the
model itself):

    torchrun --nproc_per_node=1 longcat_i2v_runner.py \
        --checkpoint_dir /path/to/weights/LongCat-Video \
        --image scene1_clock.jpg \
        --prompt "slow cinematic push-in on an antique clock, muted tones" \
        --out scene1_raw.mp4 \
        --num_frames 45 --fps 15 --use_distill

UNVERIFIED: this script has not been run against real LongCat-Video
weights or a GPU (none are available in the environment it was authored
in). It mirrors the official demo's model-loading and generate_i2v() /
generate_refine() call signatures as closely as possible, but treat it
as a starting point to validate on real hardware, not a tested artifact.
"""
import os
import argparse
import datetime

import numpy as np
import PIL.Image

import torch
import torch.distributed as dist

from transformers import AutoTokenizer, UMT5EncoderModel
from torchvision.io import write_video
from diffusers.utils import load_image

from longcat_video.pipeline_longcat_video import LongCatVideoPipeline
from longcat_video.modules.scheduling_flow_match_euler_discrete import FlowMatchEulerDiscreteScheduler
from longcat_video.modules.autoencoder_kl_wan import AutoencoderKLWan
from longcat_video.modules.longcat_video_dit import LongCatVideoTransformer3DModel
from longcat_video.context_parallel import context_parallel_util
from longcat_video.context_parallel.context_parallel_util import init_context_parallel

DEFAULT_NEGATIVE_PROMPT = (
    "Bright tones, overexposed, static, blurred details, subtitles, style, "
    "works, paintings, images, static, overall gray, worst quality, low "
    "quality, JPEG compression residue, ugly, incomplete, extra fingers, "
    "poorly drawn hands, poorly drawn faces, deformed, disfigured, "
    "misshapen limbs, fused fingers, still picture, messy background, "
    "three legs, many people in the background, walking backwards"
)


def torch_gc():
    torch.cuda.empty_cache()
    torch.cuda.ipc_collect()


def generate(args):
    image = load_image(args.image)
    target_size = image.size  # (width, height)

    rank = int(os.environ["RANK"])
    num_gpus = torch.cuda.device_count()
    local_rank = rank % num_gpus
    torch.cuda.set_device(local_rank)
    dist.init_process_group(backend="nccl", timeout=datetime.timedelta(seconds=3600 * 24))
    global_rank = dist.get_rank()
    num_processes = dist.get_world_size()

    init_context_parallel(
        context_parallel_size=args.context_parallel_size,
        global_rank=global_rank,
        world_size=num_processes,
    )
    cp_size = context_parallel_util.get_cp_size()
    cp_split_hw = context_parallel_util.get_optimal_split(cp_size)

    tokenizer = AutoTokenizer.from_pretrained(args.checkpoint_dir, subfolder="tokenizer", torch_dtype=torch.bfloat16)
    text_encoder = UMT5EncoderModel.from_pretrained(args.checkpoint_dir, subfolder="text_encoder", torch_dtype=torch.bfloat16)
    vae = AutoencoderKLWan.from_pretrained(args.checkpoint_dir, subfolder="vae", torch_dtype=torch.bfloat16)
    scheduler = FlowMatchEulerDiscreteScheduler.from_pretrained(args.checkpoint_dir, subfolder="scheduler", torch_dtype=torch.bfloat16)
    dit = LongCatVideoTransformer3DModel.from_pretrained(args.checkpoint_dir, subfolder="dit", cp_split_hw=cp_split_hw, torch_dtype=torch.bfloat16)

    if args.enable_compile:
        dit = torch.compile(dit)

    pipe = LongCatVideoPipeline(
        tokenizer=tokenizer,
        text_encoder=text_encoder,
        vae=vae,
        scheduler=scheduler,
        dit=dit,
    )
    pipe.to(local_rank)

    generator = torch.Generator(device=local_rank)
    generator.manual_seed(args.seed + global_rank)

    if args.use_distill:
        cfg_step_lora_path = os.path.join(args.checkpoint_dir, "lora/cfg_step_lora.safetensors")
        pipe.dit.load_lora(cfg_step_lora_path, "cfg_step_lora")
        pipe.dit.enable_loras(["cfg_step_lora"])
        output = pipe.generate_i2v(
            image=image,
            prompt=args.prompt,
            resolution=args.resolution,
            num_frames=args.num_frames,
            num_inference_steps=args.num_inference_steps,
            use_distill=True,
            guidance_scale=1.0,
            generator=generator,
        )[0]
        pipe.dit.disable_all_loras()
    else:
        output = pipe.generate_i2v(
            image=image,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            resolution=args.resolution,
            num_frames=args.num_frames,
            num_inference_steps=args.num_inference_steps,
            guidance_scale=args.guidance_scale,
            generator=generator,
        )[0]

    if local_rank == 0:
        frames = [(output[i] * 255).astype(np.uint8) for i in range(output.shape[0])]
        frames = [PIL.Image.fromarray(img) for img in frames]
        frames = [frame.resize(target_size, PIL.Image.BICUBIC) for frame in frames]
        frames_tensor = torch.from_numpy(np.array(frames))
        write_video(args.out, frames_tensor, fps=args.fps, video_codec="libx264", options={"crf": "18"})

    del output
    torch_gc()


def _parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint_dir", type=str, required=True)
    parser.add_argument("--image", type=str, required=True)
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--negative_prompt", type=str, default=DEFAULT_NEGATIVE_PROMPT)
    parser.add_argument("--out", type=str, required=True)
    parser.add_argument("--num_frames", type=int, default=45,
                         help="Must satisfy num_frames % 4 == 1 (LongCat-Video's temporal VAE constraint).")
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--resolution", type=str, default="480p", choices=["480p", "720p"])
    parser.add_argument("--num_inference_steps", type=int, default=None,
                         help="Defaults to 16 with --use_distill, else 50.")
    parser.add_argument("--guidance_scale", type=float, default=4.0)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--use_distill", action="store_true",
                         help="Use the cfg-step distillation LoRA for ~3x fewer steps.")
    parser.add_argument("--context_parallel_size", type=int, default=1)
    parser.add_argument("--enable_compile", action="store_true")

    args = parser.parse_args()
    if args.num_inference_steps is None:
        args.num_inference_steps = 16 if args.use_distill else 50
    if (args.num_frames - 1) % 4 != 0:
        parser.error("--num_frames must satisfy num_frames % 4 == 1 (e.g. 45, 61, 93)")
    return args


if __name__ == "__main__":
    generate(_parse_args())
