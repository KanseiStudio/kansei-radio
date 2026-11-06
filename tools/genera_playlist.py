#!/usr/bin/env python3
"""Rigenera playlist.json dai file MP3 in tracks/.

Uso (dalla cartella del progetto):
    python3 tools/genera_playlist.py

Richiede ffprobe (incluso in ffmpeg). Titolo, artista e commento vengono letti
dai tag ID3 dei file; se mancano, il titolo si ricava dal nome del file.
L'ordine di riproduzione è l'ordine alfabetico dei nomi (01-..., 02-..., ...).
"""
import json, subprocess, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRACKS = ROOT / "tracks"
OUT = ROOT / "playlist.json"

def probe(path):
    out = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration:format_tags=title,artist,comment",
        "-of", "json", str(path)])
    fmt = json.loads(out)["format"]
    tags = {k.lower(): v for k, v in fmt.get("tags", {}).items()}
    return float(fmt["duration"]), tags

old = json.loads(OUT.read_text()) if OUT.exists() else {}
tracks = []
for f in sorted(TRACKS.glob("*.mp3")):
    dur, tags = probe(f)
    prev = next((t for t in old.get("tracks", []) if t["file"] == f"tracks/{f.name}"), {})
    title = tags.get("title") or f.stem.split("-", 1)[-1].replace("-", " ").capitalize()
    tracks.append({
        "file": f"tracks/{f.name}",
        "title": title,
        "artist": tags.get("artist", "Kansei Radio"),
        "info": prev.get("info", tags.get("comment", "")),
        "duration": round(dur, 3),
    })

if not tracks:
    sys.exit("Nessun MP3 in tracks/")

playlist = {"name": old.get("name", "Kansei Radio"),
            "epoch": old.get("epoch", "2026-11-06T00:00:00Z"),
            "tracks": tracks}
OUT.write_text(json.dumps(playlist, ensure_ascii=False, indent=2))
tot = sum(t["duration"] for t in tracks) / 60
print(f"playlist.json aggiornata: {len(tracks)} brani, {tot:.1f} minuti in loop")
