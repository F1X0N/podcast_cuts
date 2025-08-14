"""
Active‑Speaker Detector ‑ Windows / Python
=========================================
A minimal wrapper that
1. Ensures the TalkNet‑ASD repository (https://github.com/TaoRuijie/TalkNet‑ASD) is cloned and its
   Python requirements are installed inside the current virtual‑env.
2. Receives a video (MP4/AVI), hands it to TalkNet’s demo script and
   returns the paths of the annotated video plus the frame‑level CSV
   that marks who is speaking.

Usage (inside an activated virtual‑env):
    python analyze_video.py --video "C:\videos\meeting.mp4" [--device cpu|directml]

Outputs (same folder as input unless --out_dir):
    <stem>_speaker_out.avi   – video showing each face (green= speaking, red= silent)
    <stem>_speaker_timeline.csv – CSV with columns [frame,id,conf,is_speaking]

Dependencies (see README instructions): torch/torch‑directml, ultralytics, opencv‑python‑headless,
ffmpeg‑python, pandas, tqdm, plus TalkNet’s own requirements.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import platform

REPO_URL = "https://github.com/TaoRuijie/TalkNet-ASD.git"


def run(cmd, **kwargs):
    """Run shell command and raise if it fails."""
    print("[cmd]", " ".join(cmd))
    subprocess.run(cmd, check=True, **kwargs)


def ensure_repo(repo_dir: Path):
    """Clone TalkNet‑ASD if it isn’t present and install its requirements."""
    if not repo_dir.exists():
        run(["git", "clone", REPO_URL, str(repo_dir)])
    # Install TalkNet’s Python deps inside current venv (they’re light ‑ mainly numpy, torch, opencv)
    req_file = repo_dir / "requirement.txt"
    run([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
    return repo_dir


def run_talknet(repo_dir: Path, video_path: Path, device: str):
    """Call TalkNet’s demo script and return annotated video + CSV paths."""
    demo_dir = repo_dir / "demo"
    demo_dir.mkdir(exist_ok=True)
    target = demo_dir / video_path.name
    shutil.copy(video_path, target)

    # Build command
    cmd = [sys.executable, "demoTalkNet.py", "--videoName", target.stem]
    if device == "cpu":
        # Easy CPU‑only execution: TalkNet figures out device internally when cuda not available
        pass
    elif device == "directml":
        # Experimental: torch‑directml acts like cuda:0 from the POV of PyTorch
        # Nothing extra needed provided torch‑directml is installed.
        pass
    run(cmd, cwd=str(repo_dir))

    out_dir = demo_dir / target.stem / "pyavi"
    out_video = out_dir / "video_out.avi"
    out_csv = out_dir / "label.csv"

    if not out_video.exists():
        raise RuntimeError("TalkNet did not generate expected output. Check logs above.")

    # Copy to same folder as original for convenience
    final_video = video_path.with_stem(video_path.stem + "_speaker_out")
    final_csv = video_path.with_stem(video_path.stem + "_speaker_timeline").with_suffix(".csv")
    shutil.copy(out_video, final_video)
    shutil.copy(out_csv, final_csv)

    print(f"\nDone! Annotated video: {final_video}\nFrame‑level CSV:   {final_csv}\n")


def main():
    parser = argparse.ArgumentParser(description="Active speaker detection wrapper for TalkNet‑ASD")
    parser.add_argument("--video", required=True, type=Path, help="Path to input video (.mp4/.avi)")
    parser.add_argument("--device", default="cpu", choices=["cpu", "directml"], help="Inference device")
    parser.add_argument("--repo_dir", type=Path, default=Path("talknet_repo"), help="Where to clone TalkNet")
    args = parser.parse_args()

    if not args.video.exists():
        sys.exit(f"Input video {args.video} does not exist.")

    # Basic Windows sanity checks
    if platform.system() != "Windows":
        print("Warning: Script optimised for Windows; it may still work elsewhere.")

    repo_dir = ensure_repo(args.repo_dir)
    run_talknet(repo_dir, args.video, args.device)


if __name__ == "__main__":
    main()
