# Speaker Clustering

Assigns a `speaker_id` to every segment, assuming a **single narrator per
chapter** (true for most audio Bible narrations — voice changes happen at
most between books, not mid-chapter). Rather than embedding all ~53k verse
segments, it embeds only the **longest segment of each chapter** (one
embedding per chapter, e.g. 929 for the current corpus), clusters those, and
propagates the resulting `speaker_id` to every segment in that chapter.

### How it works
1. **`extract_embeddings.py`** — for each chapter, loads its longest segment
   and computes a 192-dim speaker embedding with
   [`speechbrain/spkrec-ecapa-voxceleb`](https://huggingface.co/speechbrain/spkrec-ecapa-voxceleb)
   (CPU-only, no `ffmpeg` needed — audio is read directly via `soundfile`).
   Saves `embeddings.npz` (chapter names + vectors).
2. **`cluster_speakers.py`** — runs agglomerative clustering (cosine
   distance) over the chapter embeddings, with no need to know the number of
   speakers in advance. Saves `speaker_map.json` (`{chapter: "SPEAKER_00"}`).
3. **`apply_speaker_ids.py`** — applies `speaker_map.json` back to the data:
   rewrites `speaker_id` into every line of each chapter's `manifest.json`
   (local mode), or adds a `speaker_id` column to a Hugging Face dataset and
   optionally pushes it back to the Hub (hf mode).

Each script works standalone, or run all three via `run_all.sh`.

### Setup
```bash
conda run -n dyudata_collect pip install torch --index-url https://download.pytorch.org/whl/cpu
conda run -n dyudata_collect pip install torchaudio --index-url https://download.pytorch.org/whl/cpu
conda run -n dyudata_collect pip install speechbrain
```
No GPU required — the ECAPA-TDNN model is small enough to run comfortably on
CPU. `torch`/`torchaudio`/`speechbrain` aren't in the main `requirements.txt`
since they're only needed for this optional step.

### Usage — local `output/` folder
Matches the folder structure produced by `convert.py`
(`output/<chapter>/manifest.json` + `.wav` files):
```bash
bash speaker_clustering/run_all.sh \
  --source local \
  --input_folder output
```
This rewrites `speaker_id` directly into each chapter's `manifest.json`, so
run it **before** `data_export/prepare_hf_dataset.py`.

### Usage — existing Hugging Face dataset
If the dataset was already pushed (e.g. via `prepare_hf_dataset.py`) and you
want to add `speaker_id` after the fact:
```bash
bash speaker_clustering/run_all.sh \
  --source hf \
  --repo_id <username>/dyula-speech-bible \
  --hf_token hf_xxxxxxxxxxxx \
  --push_to_hub
```
Add `--output_repo_id <username>/other-repo` to push the result to a
different repo instead of overwriting the source one, or `--output_folder
<path>` to save the updated dataset locally (via `save_to_disk`) instead of
or in addition to pushing.

### Running steps individually
```bash
cd speaker_clustering

python extract_embeddings.py --source local --input_folder ../output --output embeddings.npz

python cluster_speakers.py --embeddings embeddings.npz --output speaker_map.json \
  --distance_threshold 0.35   # lower = more/smaller speaker clusters
# or force an exact count: --n_clusters 2

python apply_speaker_ids.py --speaker_map speaker_map.json --source local --input_folder ../output
```

### Notes / caveats
- **`--distance_threshold` is an untuned default.** Unsupervised clustering
  has no ground truth — after running, spot-check a few chapters from each
  resulting `SPEAKER_XX` group by ear before trusting the assignment. If you
  get far more or fewer clusters than you expect, adjust the threshold (or
  pass `--n_clusters` if you already know how many narrators exist) and
  re-run `cluster_speakers.py` — it's cheap, no need to re-extract embeddings.
- **Timing** (measured on a 12-core CPU, no GPU, for the current 929-chapter
  corpus): ~2.5–3s per chapter for embedding extraction (~40 min total),
  clustering is near-instant, manifest rewriting is ~2 min. Total: roughly
  **45 minutes** for a full local run, one-time model download aside.
- On Windows, `speechbrain`'s model cache defaults to symlinking, which needs
  elevated privileges. `common.py` forces `LocalStrategy.COPY` to avoid that
  — if you see a `WinError 1314` regardless, delete
  `speaker_clustering/.model_cache` and retry.
