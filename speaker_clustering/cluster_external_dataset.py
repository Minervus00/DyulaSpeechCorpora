"""Cluster speakers by chapter on an external HF dataset (columns: audio_file,
text; chapter inferred from the audio filename, e.g. "1ch_10_0.wav" ->
chapter "1ch_10") and re-upload with duration/chapter/speaker_id added.

Only run this after check_filename_pattern.py confirms the filename
convention actually holds across the dataset.
"""
import argparse
import re
import sys
from collections import Counter

from sklearn.cluster import AgglomerativeClustering
from tqdm import tqdm

from common import load_embedding_model, embed_waveform

FILENAME_RE = re.compile(r"^(?P<chapter>.+)_(?P<index>\d+)\.[A-Za-z0-9]+$")


def parse_args():
    parser = argparse.ArgumentParser(description="Cluster speakers by chapter on an external HF dataset")
    parser.add_argument("--repo_id", required=True, help="Dataset repo id to read from")
    parser.add_argument("--split", default="train")
    parser.add_argument("--hf_token", default=None, help="Token to read (if private) and/or push")
    parser.add_argument("--audio_column", default="audio_file")
    parser.add_argument("--text_column", default="text")
    parser.add_argument("--num_proc", type=int, default=1, help="Parallel workers for the duration/chapter pass")

    parser.add_argument("--distance_threshold", type=float, default=0.35)
    parser.add_argument("--n_clusters", type=int, default=None, help="Overrides --distance_threshold if set")

    parser.add_argument("--push_to_hub", action="store_true")
    parser.add_argument("--output_repo_id", default=None, help="Push to a different repo id instead of --repo_id")
    parser.add_argument("--output_folder", default=None, help="Also/instead save the dataset to disk here")
    return parser.parse_args()


def add_chapter_and_duration(example, audio_column):
    path = example[audio_column]["path"]
    m = FILENAME_RE.match(path)
    if not m:
        raise ValueError(f"Filename does not match the expected pattern: {path!r}")
    array = example[audio_column]["array"]
    sr = example[audio_column]["sampling_rate"]
    # Return only the new columns, not the whole `example` dict: handing back
    # the audio column's value forces datasets to re-encode it from the
    # decoded array, which drops the original "path".
    return {"chapter": m.group("chapter"), "duration": len(array) / sr}


def main():
    args = parse_args()

    from datasets import load_dataset

    print(f"Loading {args.repo_id} (split={args.split})...")
    dataset = load_dataset(args.repo_id, split=args.split, token=args.hf_token)

    if args.audio_column not in dataset.column_names:
        sys.exit(f"Column '{args.audio_column}' not found. Available columns: {dataset.column_names}")

    print("Deriving 'chapter' and 'duration' columns from filenames (decodes every row's audio once)...")
    dataset = dataset.map(
        add_chapter_and_duration,
        fn_kwargs={"audio_column": args.audio_column},
        num_proc=args.num_proc,
        desc="chapter/duration",
    )

    # Pick the longest-duration row per chapter as that chapter's representative
    # segment for speaker embedding, using the cheap (already-computed) columns
    # so we don't decode audio for rows we won't embed.
    best_idx_by_chapter = {}
    best_duration_by_chapter = {}
    for i, (chapter, duration) in enumerate(zip(dataset["chapter"], dataset["duration"])):
        if chapter not in best_duration_by_chapter or duration > best_duration_by_chapter[chapter]:
            best_duration_by_chapter[chapter] = duration
            best_idx_by_chapter[chapter] = i

    print(f"{len(best_idx_by_chapter)} chapters found. Extracting one embedding per chapter...")
    print("Loading speaker embedding model (speechbrain/spkrec-ecapa-voxceleb)...")
    classifier = load_embedding_model()

    chapters = []
    embeddings = []
    for chapter, idx in tqdm(best_idx_by_chapter.items(), desc="Embedding chapters"):
        audio = dataset[idx][args.audio_column]
        try:
            emb = embed_waveform(classifier, audio["array"], audio["sampling_rate"])
        except Exception as e:
            print(f"Skipping {chapter}: {e}", file=sys.stderr)
            continue
        chapters.append(chapter)
        embeddings.append(emb)

    if not embeddings:
        sys.exit("No embeddings were extracted.")

    if args.n_clusters:
        clustering = AgglomerativeClustering(n_clusters=args.n_clusters, metric="cosine", linkage="average")
    else:
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=args.distance_threshold,
            metric="cosine",
            linkage="average",
        )
    labels = clustering.fit_predict(embeddings)
    speaker_map = {chapter: f"SPEAKER_{label:02d}" for chapter, label in zip(chapters, labels)}

    counts = Counter(speaker_map.values())
    print(f"\nFound {len(counts)} speaker(s) across {len(chapters)} chapters:")
    for speaker_id, n in sorted(counts.items()):
        print(f"  {speaker_id}: {n} chapters")

    print("\nApplying speaker_id to every row...")
    dataset = dataset.map(
        lambda example: {"speaker_id": speaker_map.get(example["chapter"], "UNKNOWN")},
        desc="speaker_id",
    )

    dataset = dataset.rename_column(args.audio_column, "audio")

    if args.output_folder:
        dataset.save_to_disk(args.output_folder)
        print(f"Saved updated dataset to {args.output_folder}")

    if args.push_to_hub:
        target_repo = args.output_repo_id or args.repo_id
        dataset.push_to_hub(target_repo, split=args.split, private=True, token=args.hf_token)
        print(f"Pushed updated dataset to https://huggingface.co/datasets/{target_repo}")

    if not args.output_folder and not args.push_to_hub:
        print("Note: neither --output_folder nor --push_to_hub was given, so the updated dataset was not saved anywhere.")


if __name__ == "__main__":
    main()
