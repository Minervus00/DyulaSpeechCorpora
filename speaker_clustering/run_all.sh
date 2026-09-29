#!/usr/bin/env bash
set -e

# Resolve the script's own directory without cd-ing into it, so that
# user-supplied relative paths like --input_folder stay relative to wherever
# this script was invoked from, not to speaker_clustering/ itself.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

SOURCE=""
INPUT_FOLDER=""
REPO_ID=""
SPLIT="train"
HF_TOKEN=""
DISTANCE_THRESHOLD="0.35"
N_CLUSTERS=""
PUSH_TO_HUB=""
OUTPUT_REPO_ID=""
OUTPUT_FOLDER=""

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --source) SOURCE="$2"; shift ;;
    --input_folder) INPUT_FOLDER="$2"; shift ;;
    --repo_id) REPO_ID="$2"; shift ;;
    --split) SPLIT="$2"; shift ;;
    --hf_token) HF_TOKEN="$2"; shift ;;
    --distance_threshold) DISTANCE_THRESHOLD="$2"; shift ;;
    --n_clusters) N_CLUSTERS="$2"; shift ;;
    --push_to_hub) PUSH_TO_HUB="1" ;;
    --output_repo_id) OUTPUT_REPO_ID="$2"; shift ;;
    --output_folder) OUTPUT_FOLDER="$2"; shift ;;
    *) echo "Unknown parameter: $1"; exit 1 ;;
  esac
  shift
done

if [[ -z "$SOURCE" ]]; then
  echo "Usage: $0 --source {local|hf} [options]"
  exit 1
fi

EMBEDDINGS_FILE="$SCRIPT_DIR/embeddings.npz"
SPEAKER_MAP_FILE="$SCRIPT_DIR/speaker_map.json"

EXTRACT_ARGS=(--source "$SOURCE" --output "$EMBEDDINGS_FILE")
APPLY_ARGS=(--source "$SOURCE" --speaker_map "$SPEAKER_MAP_FILE")

if [[ "$SOURCE" == "local" ]]; then
  if [[ -z "$INPUT_FOLDER" ]]; then
    echo "--input_folder is required for --source local"
    exit 1
  fi
  EXTRACT_ARGS+=(--input_folder "$INPUT_FOLDER")
  APPLY_ARGS+=(--input_folder "$INPUT_FOLDER")
else
  if [[ -z "$REPO_ID" ]]; then
    echo "--repo_id is required for --source hf"
    exit 1
  fi
  EXTRACT_ARGS+=(--repo_id "$REPO_ID" --split "$SPLIT")
  APPLY_ARGS+=(--repo_id "$REPO_ID" --split "$SPLIT")
  [[ -n "$HF_TOKEN" ]] && EXTRACT_ARGS+=(--hf_token "$HF_TOKEN") && APPLY_ARGS+=(--hf_token "$HF_TOKEN")
  [[ -n "$PUSH_TO_HUB" ]] && APPLY_ARGS+=(--push_to_hub)
  [[ -n "$OUTPUT_REPO_ID" ]] && APPLY_ARGS+=(--output_repo_id "$OUTPUT_REPO_ID")
  [[ -n "$OUTPUT_FOLDER" ]] && APPLY_ARGS+=(--output_folder "$OUTPUT_FOLDER")
fi

CLUSTER_ARGS=(--embeddings "$EMBEDDINGS_FILE" --output "$SPEAKER_MAP_FILE" --distance_threshold "$DISTANCE_THRESHOLD")
[[ -n "$N_CLUSTERS" ]] && CLUSTER_ARGS=(--embeddings "$EMBEDDINGS_FILE" --output "$SPEAKER_MAP_FILE" --n_clusters "$N_CLUSTERS")

echo "Step 1/3: extracting one embedding per chapter..."
python "$SCRIPT_DIR/extract_embeddings.py" "${EXTRACT_ARGS[@]}"

echo "Step 2/3: clustering chapters into speakers..."
python "$SCRIPT_DIR/cluster_speakers.py" "${CLUSTER_ARGS[@]}"

echo "Step 3/3: applying speaker_id..."
python "$SCRIPT_DIR/apply_speaker_ids.py" "${APPLY_ARGS[@]}"

echo "Done."
