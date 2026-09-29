"""Data-source abstraction: local `output/` chapter folders, or a HF dataset repo.

Both sources expose one representative (longest) segment per chapter, since we
assume a single speaker narrates each chapter.
"""
import json
from pathlib import Path


def iter_local_chapters(input_folder: str):
    """Yield (chapter_name, manifest_path, representative_audio_path) for each
    chapter folder under input_folder that has a manifest.json.
    """
    root = Path(input_folder)
    for chapter_dir in sorted(root.glob("*/")):
        manifest_path = chapter_dir / "manifest.json"
        if not manifest_path.exists():
            continue

        entries = []
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    entries.append(json.loads(line))
        if not entries:
            continue

        best = max(entries, key=lambda e: e["duration"])
        yield chapter_dir.name, str(manifest_path), best["audio_filepath"]


def rewrite_local_manifest(manifest_path: str, speaker_id: str):
    """Add/overwrite "speaker_id" on every line of a chapter's manifest.json."""
    with open(manifest_path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    for entry in lines:
        entry["speaker_id"] = speaker_id

    with open(manifest_path, "w", encoding="utf-8") as f:
        for entry in lines:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def load_hf_dataset(repo_id: str, split: str = "train", hf_token: str = None):
    from datasets import load_dataset

    return load_dataset(repo_id, split=split, token=hf_token)


def iter_hf_chapters(dataset):
    """Yield (chapter_name, audio_array, sampling_rate) for the longest-duration
    row of each distinct "chapter" value in the dataset. Only decodes audio for
    the selected representative rows, not the whole dataset.
    """
    best_idx_by_chapter = {}
    best_duration_by_chapter = {}

    for i, (chapter, duration) in enumerate(zip(dataset["chapter"], dataset["duration"])):
        if chapter not in best_duration_by_chapter or duration > best_duration_by_chapter[chapter]:
            best_duration_by_chapter[chapter] = duration
            best_idx_by_chapter[chapter] = i

    for chapter, idx in best_idx_by_chapter.items():
        audio = dataset[idx]["audio"]
        yield chapter, audio["array"], audio["sampling_rate"]


def apply_speaker_ids_to_hf_dataset(dataset, speaker_map: dict):
    def _map_fn(example):
        example["speaker_id"] = speaker_map.get(example["chapter"], "UNKNOWN")
        return example

    return dataset.map(_map_fn)
