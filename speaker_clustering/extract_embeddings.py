"""Step 1: extract one speaker embedding per chapter.

Assumes a single narrator per chapter, so only the longest segment of each
chapter is embedded (not all 53k+ individual verse segments).
"""
import argparse
import sys

import numpy as np
from tqdm import tqdm

from common import load_embedding_model, embed_file, embed_waveform
from sources import iter_local_chapters, load_hf_dataset, iter_hf_chapters


def parse_args():
    parser = argparse.ArgumentParser(description="Extract one speaker embedding per chapter")
    parser.add_argument("--source", required=True, choices=["local", "hf"])
    parser.add_argument("--input_folder", help="[local] path to the output/ folder of chapter subfolders")
    parser.add_argument("--repo_id", help="[hf] dataset repo id, e.g. username/dyula-speech-bible")
    parser.add_argument("--split", default="train", help="[hf] dataset split (default: train)")
    parser.add_argument("--hf_token", help="[hf] token, if the dataset is private")
    parser.add_argument("--output", default="embeddings.npz", help="Where to save embeddings (npz)")
    return parser.parse_args()


def main():
    args = parse_args()

    if args.source == "local" and not args.input_folder:
        sys.exit("--input_folder is required when --source local")
    if args.source == "hf" and not args.repo_id:
        sys.exit("--repo_id is required when --source hf")

    print("Loading speaker embedding model (speechbrain/spkrec-ecapa-voxceleb)...")
    classifier = load_embedding_model()

    chapters = []
    embeddings = []

    if args.source == "local":
        items = list(iter_local_chapters(args.input_folder))
        if not items:
            sys.exit(f"No chapters with manifest.json found under '{args.input_folder}'.")
        for chapter_name, _manifest_path, audio_path in tqdm(items, desc="Embedding chapters"):
            try:
                emb = embed_file(classifier, audio_path)
            except Exception as e:
                print(f"Skipping {chapter_name} ({audio_path}): {e}", file=sys.stderr)
                continue
            chapters.append(chapter_name)
            embeddings.append(emb)
    else:
        dataset = load_hf_dataset(args.repo_id, split=args.split, hf_token=args.hf_token)
        items = list(iter_hf_chapters(dataset))
        if not items:
            sys.exit(f"No 'chapter' groups found in dataset '{args.repo_id}'.")
        for chapter_name, audio_array, sampling_rate in tqdm(items, desc="Embedding chapters"):
            try:
                emb = embed_waveform(classifier, audio_array, sampling_rate)
            except Exception as e:
                print(f"Skipping {chapter_name}: {e}", file=sys.stderr)
                continue
            chapters.append(chapter_name)
            embeddings.append(emb)

    if not embeddings:
        sys.exit("No embeddings were extracted.")

    np.savez(args.output, chapters=np.array(chapters), embeddings=np.stack(embeddings))
    print(f"Saved {len(chapters)} chapter embeddings to {args.output}")


if __name__ == "__main__":
    main()
