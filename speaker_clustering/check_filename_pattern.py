"""Download an external HF dataset (columns: audio_file, text) and check
whether filenames follow the {chapter_key}_{segment_index}.{ext} pattern,
e.g. "1ch_10_0.wav" -> chapter_key="1ch_10", segment_index=0.

Run this BEFORE cluster_external_dataset.py to confirm the pattern actually
holds across the whole dataset, not just a single example.
"""
import argparse
import re
from collections import defaultdict

FILENAME_RE = re.compile(r"^(?P<chapter>.+)_(?P<index>\d+)\.[A-Za-z0-9]+$")


def parse_args():
    parser = argparse.ArgumentParser(description="Check the {chapter}_{index}.ext filename pattern on a HF dataset")
    parser.add_argument("--repo_id", required=True)
    parser.add_argument("--split", default="train")
    parser.add_argument("--hf_token", default=None)
    parser.add_argument("--audio_column", default="audio_file")
    return parser.parse_args()


def main():
    args = parse_args()

    from datasets import load_dataset

    print(f"Loading {args.repo_id} (split={args.split})...")
    dataset = load_dataset(args.repo_id, split=args.split, token=args.hf_token)
    print(f"{len(dataset)} rows")

    if args.audio_column not in dataset.column_names:
        raise SystemExit(
            f"Column '{args.audio_column}' not found. Available columns: {dataset.column_names}"
        )

    # dataset[audio_column] returns a list of dicts without decoding audio arrays,
    # since we only need the "path" field here.
    paths = dataset[args.audio_column]

    matched = 0
    unmatched_examples = []
    chapter_segment_counts = defaultdict(int)
    chapter_index_sets = defaultdict(set)
    duplicate_index_examples = []

    for i, entry in enumerate(paths):
        path = entry["path"] if isinstance(entry, dict) else entry
        m = FILENAME_RE.match(path)
        if not m:
            unmatched_examples.append((i, path))
            continue
        matched += 1
        chapter = m.group("chapter")
        index = m.group("index")
        chapter_segment_counts[chapter] += 1
        if index in chapter_index_sets[chapter]:
            duplicate_index_examples.append((chapter, index, path))
        chapter_index_sets[chapter].add(index)

    total = len(paths)
    print(f"\nMatched pattern: {matched}/{total} ({100 * matched / total:.1f}%)")
    print(f"Distinct chapters inferred: {len(chapter_segment_counts)}")

    if chapter_segment_counts:
        counts = sorted(chapter_segment_counts.values())
        print(
            f"Segments per chapter: min={counts[0]}, max={counts[-1]}, "
            f"median={counts[len(counts) // 2]}"
        )

    if unmatched_examples:
        print(f"\n{len(unmatched_examples)} filenames did NOT match the pattern, e.g.:")
        for i, path in unmatched_examples[:10]:
            print(f"  row {i}: {path!r}")

    if duplicate_index_examples:
        print(f"\n{len(duplicate_index_examples)} duplicate (chapter, index) pairs found, e.g.:")
        for chapter, index, path in duplicate_index_examples[:10]:
            print(f"  chapter={chapter!r} index={index!r} path={path!r}")

    if not unmatched_examples and not duplicate_index_examples:
        print("\nPattern holds cleanly across the whole dataset.")


if __name__ == "__main__":
    main()
