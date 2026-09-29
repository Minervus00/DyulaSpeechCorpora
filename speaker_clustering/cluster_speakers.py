"""Step 2: cluster per-chapter speaker embeddings into speaker_id groups."""
import argparse
import json
from collections import Counter

import numpy as np
from sklearn.cluster import AgglomerativeClustering


def parse_args():
    parser = argparse.ArgumentParser(description="Cluster chapter embeddings into speaker groups")
    parser.add_argument("--embeddings", default="embeddings.npz", help="Path to embeddings.npz from step 1")
    parser.add_argument("--output", default="speaker_map.json", help="Where to save the chapter -> speaker_id map")
    parser.add_argument(
        "--distance_threshold",
        type=float,
        default=0.35,
        help="Cosine distance threshold for merging clusters (lower = more/smaller speaker clusters). Ignored if --n_clusters is set.",
    )
    parser.add_argument("--n_clusters", type=int, default=None, help="Force an exact number of speakers instead of using --distance_threshold")
    return parser.parse_args()


def main():
    args = parse_args()

    data = np.load(args.embeddings, allow_pickle=True)
    chapters = data["chapters"]
    embeddings = data["embeddings"]

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

    speaker_map = {
        str(chapter): f"SPEAKER_{label:02d}"
        for chapter, label in zip(chapters, labels)
    }

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(speaker_map, f, ensure_ascii=False, indent=2, sort_keys=True)

    counts = Counter(speaker_map.values())
    print(f"Found {len(counts)} speaker(s) across {len(chapters)} chapters:")
    for speaker_id, n in sorted(counts.items()):
        print(f"  {speaker_id}: {n} chapters")
    print(f"Saved chapter -> speaker_id map to {args.output}")


if __name__ == "__main__":
    main()
