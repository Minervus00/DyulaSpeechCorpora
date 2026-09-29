"""Step 3: apply a chapter -> speaker_id map to the dataset.

- local: rewrites "speaker_id" into every line of each chapter's manifest.json.
- hf: adds a "speaker_id" column to the dataset and either saves it locally
  or pushes it back to the Hub.
"""
import argparse
import json
import sys

from tqdm import tqdm

from sources import (
    iter_local_chapters,
    rewrite_local_manifest,
    load_hf_dataset,
    apply_speaker_ids_to_hf_dataset,
)


def parse_args():
    parser = argparse.ArgumentParser(description="Apply chapter speaker_id map to manifests or a HF dataset")
    parser.add_argument("--speaker_map", default="speaker_map.json", help="Path to speaker_map.json from step 2")
    parser.add_argument("--source", required=True, choices=["local", "hf"])

    parser.add_argument("--input_folder", help="[local] path to the output/ folder of chapter subfolders")

    parser.add_argument("--repo_id", help="[hf] dataset repo id to read from, e.g. username/dyula-speech-bible")
    parser.add_argument("--split", default="train", help="[hf] dataset split (default: train)")
    parser.add_argument("--hf_token", help="[hf] token (required to push, or if the dataset is private)")
    parser.add_argument("--push_to_hub", action="store_true", help="[hf] push the updated dataset back to the Hub")
    parser.add_argument("--output_repo_id", help="[hf] push to a different repo id instead of --repo_id")
    parser.add_argument("--output_folder", help="[hf] instead of/alongside pushing, save the updated dataset to disk here")
    parser.add_argument("--private", action="store_true", help="[hf] keep the pushed dataset private (default: private)")

    return parser.parse_args()


def main():
    args = parse_args()

    with open(args.speaker_map, "r", encoding="utf-8") as f:
        speaker_map = json.load(f)

    if args.source == "local":
        if not args.input_folder:
            sys.exit("--input_folder is required when --source local")
        items = list(iter_local_chapters(args.input_folder))
        updated, missing = 0, 0
        for chapter_name, manifest_path, _audio_path in tqdm(items, desc="Updating manifests"):
            speaker_id = speaker_map.get(chapter_name)
            if speaker_id is None:
                missing += 1
                continue
            rewrite_local_manifest(manifest_path, speaker_id)
            updated += 1
        print(f"Updated {updated} manifest.json files ({missing} chapters had no entry in speaker_map).")

    else:
        if not args.repo_id:
            sys.exit("--repo_id is required when --source hf")
        dataset = load_hf_dataset(args.repo_id, split=args.split, hf_token=args.hf_token)
        dataset = apply_speaker_ids_to_hf_dataset(dataset, speaker_map)

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
