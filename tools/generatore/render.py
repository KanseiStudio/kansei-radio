"""Uso: python3 render.py N [N ...]  → out/<file>.wav e out/<file>-v2.mp3"""
import json
import subprocess
import sys
import time
import pathlib
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from synth import SR  # noqa: E402
from tracks import TRACKS  # noqa: E402

OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
TARGET_LUFS = -15.0


def encode(wav, mp3, title, info):
    p1 = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(wav), "-af",
                         f"loudnorm=I={TARGET_LUFS}:TP=-1.2:LRA=11:print_format=json", "-f", "null", "-"],
                        capture_output=True, text=True)
    js = p1.stderr[p1.stderr.rindex("{"):p1.stderr.rindex("}") + 1]
    mj = json.loads(js)
    af = (f"loudnorm=I={TARGET_LUFS}:TP=-1.2:LRA=11:linear=true:"
          f"measured_I={mj['input_i']}:measured_TP={mj['input_tp']}:measured_LRA={mj['input_lra']}:"
          f"measured_thresh={mj['input_thresh']}:offset={mj['target_offset']},aresample=44100")
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(wav), "-af", af,
                    "-c:a", "libmp3lame", "-b:a", "128k", "-ar", "44100", "-ac", "2",
                    "-metadata", f"title={title}", "-metadata", "artist=Kansei Radio",
                    "-metadata", f"comment={info}", str(mp3)], check=True)
    return float(mj["input_i"])


for arg in sys.argv[1:]:
    k = int(arg)
    stem, title, info, fn = TRACKS[k]
    t = time.time()
    y = fn()
    wav = OUT / f"{stem}.wav"
    wavfile.write(wav, SR, y.T)
    lufs_in = encode(wav, OUT / f"{stem}-v2.mp3", title, info)
    print(f"{stem}: {y.shape[1] / SR:6.1f}s  render {time.time() - t:5.1f}s  LUFS prima {lufs_in:.1f}", flush=True)
