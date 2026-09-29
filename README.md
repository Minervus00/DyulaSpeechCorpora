# Dyula Speech Corpora Toolkit
[![Python 3.10](https://img.shields.io/badge/python-3.10-blue)](https://www.python.org/downloads/release/python-3100/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Modular tools to collect, preprocess, align, and prepare **Dyula (Jula, `dyu`)** speech/text data for **Text-to-Speech (TTS)** and **Automatic Speech Recognition (ASR)**.

> **Origin & credits**
> This project is a fork of and builds on [**MooreSpeechCorpora**](https://github.com/anyantudre/MooreSpeechCorpora) by [Alban NYANTUDRE (@anyantudre)](https://github.com/anyantudre), the toolkit behind the [Moore Speech Corpora](https://huggingface.co/datasets/anyantudre/MooreSpeechCorpora) dataset.
> The whole crawl → align → export pipeline comes from that project. Many thanks to its author for making it open source!
> This fork adapts it to Dyula and adds Windows support, speaker clustering, and several fixes (see [What's new in this fork](#whats-new-in-this-fork)).
> The original Mooré scrapers (contes, proverbes) are still included.

---

## Table of Contents
1. [What's new in this fork](#whats-new-in-this-fork)
2. [Features](#features)
3. [Installation](#installation--setup)
4. [Quick Start](#quick-start)
5. [Contributing](#contributing)
6. [License](#license)
7. [Acknowledgments](#acknowledgments)

---

## What's new in this fork
- **Dyula Bible pipeline**: crawls the Dyula Bible ([AKKDC08](https://www.bible.com/bible/1754/GEN.1.AKKDC08)) and aligns it with MMS (`--lang dyu`).
- **Updated Bible scraper**: new CSS class names for the current bible.com layout, plus UTF-8 file writes so Dyula characters (`ɛ`, `ɔ`, `ɲ`, …) are preserved on Windows.
- **Windows setup guide**: [SETUP.md](SETUP.md) (PyICU wheel, Twisted pin, CPU-only PyTorch).
- **Segment conversion**: `convert.py` converts the aligned `.flac` segments to 16 kHz mono `.wav`, with optional parallel processing (`--workers`).
- **Speaker clustering**: new [`speaker_clustering/`](speaker_clustering/README.md) module assigns a `speaker_id` to every segment using ECAPA speaker embeddings (runs on CPU).
- **Dataset export**: `prepare_hf_dataset.py` now exports a `speaker_id` column and has a `--filter_nums` flag that drops transcriptions containing digits.

---

## Features
We offer modular, CLI-friendly scripts for tasks like:
- Scrape audios and texts from online sources (Bible, story/proverb websites, etc.)
- Segment and align long audios w/ texts
- Audio preprocessing: resampling, mono conversion
- Text normalization
- Speaker clustering (one narrator per chapter)
- Audio denoising and enhancement
- Export datasets to different formats (Hugging Face, LJSpeech etc...)

The toolkit is structured as follows:
```text
DyulaSpeechCorpora/
├─ crawlers/             # Bible, websites, YouTube
├─ preprocessing/        # Resample, normalize text, denoise
├─ forced_alignement/    # MMS scripts & wrappers
├─ speaker_clustering/   # Speaker embeddings + clustering
├─ data_export/          # HF dataset prep & push
├─ convert.py            # Aligned FLAC segments -> 16 kHz WAV
├─ environment.yml
├─ requirements.txt
├─ SETUP.md              # Windows setup notes
└─ README.md
```

---

## Installation & Setup

```bash
git clone https://github.com/Minervus00/DyulaSpeechCorpora.git
cd DyulaSpeechCorpora
conda create -n dyudata_collect python=3.10 -y
conda activate dyudata_collect
pip install -r requirements.txt
```

> It's highly recommended to use **Python 3.10**!
> On **Windows**, follow [SETUP.md](SETUP.md): a few dependencies (PyICU, Twisted) need special handling.
> The original Linux/GPU environment is still available in `environment.yml`.

---

## Quick Start

* **Data Crawling:** crawls the Dyula Bible (text + audio per chapter).
```bash
python crawlers/bible/crawl.py \
  --output_folder crawlers/bible/dyu_data \
  --url https://www.bible.com/bible/1754/GEN.1.AKKDC08 \
  --code AKKDC08
```

See [crawlers/README.md](crawlers/README.md) for full instructions and more details.

* **Preprocessing:** resample the raw audio to 16 kHz mono.

```bash
bash preprocessing/resample.sh --input_folder crawlers/bible/dyu_data --output_folder datasets/dyula/bible/resampled
```

See [preprocessing/README.md](preprocessing/README.md) for full instructions and more details.

* **Forced Alignment:** outputs segmented audio and a `manifest.json` file for each chapter.

```bash
bash forced_alignement/align_and_segment.sh \
  --audio_folder datasets/dyula/bible/resampled \
  --text_folder datasets/dyula/bible/resampled \
  --output_folder dyu_audio_sgmt \
  --lang dyu \
  --uroman_path ../uroman/bin
```

See [forced_alignement/README.md](forced_alignement/README.md) for full instructions and more details.

* **Conversion:** converts the aligned `.flac` segments in `dyu_audio_sgmt/` to 16 kHz `.wav` in `output/`, and rewrites the manifests.

```bash
python convert.py --input_folder dyu_audio_sgmt --output_folder output --workers 4
```

Both folders default to the values above. `--start` / `--end` restrict the run to a range of chapters (by sorted index).

* **Speaker Clustering (optional):** writes a `speaker_id` into each chapter's `manifest.json`.

```bash
bash speaker_clustering/run_all.sh --source local --input_folder output
```

See [speaker_clustering/README.md](speaker_clustering/README.md) for full instructions and more details.

* **Dataset Preparation/Export:** uploads the dataset to the Hugging Face Hub with columns: audio, transcription, duration, chapter, speaker_id.

```bash
python data_export/prepare_hf_dataset.py \
  --input_folder output \
  --repo_id <hf-username>/dyula-speech-bible \
  --hf_token hf_xxxx \
  --filter_nums
```

See [data_export/README.md](data_export/README.md) for full instructions and more details.

* **Denoising & Enhancement (optional):** applies Resemble Enhance to improve audio quality, optionally skipping enhancement or keeping original audio.

```bash
python preprocessing/denoise_enhance.py \
  --dataset_id <hf-username>/dyula-speech-bible \
  --output_repo_id <hf-username>/dyula-speech-bible-denoised \
  --hf_token hf_xxxx \
  --enhance_audio \
  --keep_original_audio
```

> The resulting dataset will include `denoised_audio` and optionally `enhanced_audio` fields, depending on the flags.

---

## Contributing
Contributions are more than welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to get started.

Improvements that also apply to the original Mooré toolkit are worth proposing upstream to [MooreSpeechCorpora](https://github.com/anyantudre/MooreSpeechCorpora) as well.

---

## License
Released under the [MIT License](LICENSE).
Copyright (c) 2025 Alban NYANTUDRE (original MooreSpeechCorpora toolkit) and (c) 2026 Fayçal OUEDRAOGO (this fork's modifications).

---

## Acknowledgments
* [Alban NYANTUDRE / MooreSpeechCorpora](https://github.com/anyantudre/MooreSpeechCorpora): the original toolkit this project is built on.
* [cawoylel](https://github.com/cawoylel/): the original toolkit was largely inspired by their excellent work on the Fula language!
* [Facebook AI Research Fairseq](https://github.com/facebookresearch/fairseq/) for multilingual alignment tools.
* [bible.com](https://www.bible.com/) for Dyula and Mooré audio/text
* [Uroman](https://github.com/isi-nlp/uroman) for romanization
* [SpeechBrain](https://github.com/speechbrain/speechbrain) for the ECAPA-TDNN speaker embedding model
* [Resemble Enhance](https://github.com/resemble-ai/resemble-enhance) for speech enhancement
