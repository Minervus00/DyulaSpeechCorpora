# Setup Notes: Bible Scraper (Dyula)

The repo's `environment.yml` was exported from the original Linux/GPU training
machine (CUDA/fairseq/torch build artifacts) and doesn't install on Windows.
These are the exact commands that got `crawlers/bible` working end-to-end on
Windows, using `conda run -n <env>` so no shell activation is needed.

## 1. Create the environment

```bash
conda create -n dyudata_collect python=3.10 -y
```

## 2. Install PyICU from a prebuilt wheel

`icu-tokenizer` depends on `PyICU`, which has no conda-forge or PyPI build for
Windows (`pip install` tries to compile it from source and fails without
`pkg-config`/ICU headers). Install the prebuilt wheel instead — v2.15 is the
newest release of [cgohlke/pyicu-build](https://github.com/cgohlke/pyicu-build)
that still ships a Python 3.10 win_amd64 wheel:

```bash
conda run -n dyudata_collect pip install "https://github.com/cgohlke/pyicu-build/releases/download/v2.15/pyicu-2.15-cp310-cp310-win_amd64.whl"
```

## 3. Install `icu-tokenizer` without letting pip rebuild PyICU

```bash
conda run -n dyudata_collect pip install --no-deps icu-tokenizer==0.0.1
```

## 4. Install the rest of the dependencies

```bash
conda run -n dyudata_collect pip install -r requirements.txt
```

## 5. Pin Twisted to a version compatible with Scrapy 2.13.1

`requirements.txt` doesn't pin `twisted`, so step 4 installs the newest
release. Recent Twisted versions removed the internal
`_setAcceptableProtocols` symbol that Scrapy 2.13.1's TLS context factory
imports directly, which breaks every download handler (http/https/s3) with:

```
ImportError: cannot import name '_setAcceptableProtocols' from 'twisted.internet._sslverify'
```

Fix by installing the version the original `environment.yml` used:

```bash
conda run -n dyudata_collect pip install "twisted==24.11.0"
```

## 6. Verify the install

```bash
conda run -n dyudata_collect python -c "from icu_tokenizer import SentSplitter; import scrapy, datasets, librosa; s=SentSplitter(lang='en'); print(s.split('Hello world. This works.'))"
```

## 7. Run the crawler

`crawl.py` only accepts three arguments: `--output_folder`, `--url`, `--code`.
The Scrapy spider `name` is hardcoded to `"MooreBible"` and there is no
`--name`/`--language` flag.

```bash
conda run -n dyudata_collect python crawlers/bible/crawl.py --output_folder datasets_test --url https://www.bible.com/bible/1754/GEN.1.AKKDC08 --code AKKDC08
```

Output text/audio files land in `--output_folder`, named
`<book>_<chapter>_<code>.txt` / `.mp3`, parsed from the response URL (the
`--code` CLI argument itself isn't currently used for naming).

## Optional: SoX binary

`sox==1.5.0` in `requirements.txt` is just a Python wrapper around the SoX
command-line tool. Not needed for the bible crawler, but any audio
preprocessing script that calls it will fail with "sox not found" unless the
binary itself is separately installed and on `PATH`.
