# Crawlers
This folder contains web scrapers to collect Dyula and Mooré language audio and text data from online sources.

### Included scrapers
- **bible/bible_scraper.py**: scrapes aligned text and audio from the Bible website (bible.com), for any language/version (Dyula, Mooré, ...).
- **contes_website/contes_scraper.py**: scrapes aligned text and audio from the mooreburkina.com website (Mooré).
- **proverbes_website/proverbes_scraper.py**: scrapes Mooré proverbs from the mooreburkina.com website.
- **youtube/youtube_scraper.py**: downloads videos and extracts audio (Not implemented yet!)


### Usage
`crawl.py` accepts three arguments: `--output_folder`, `--url` (first chapter to crawl) and `--code` (Bible version code).
Run scripts (assuming you're in main folder):

- **Dyula Bible**:
```bash
python crawlers/bible/crawl.py \
  --output_folder crawlers/bible/dyu_data \
  --url https://www.bible.com/bible/1754/GEN.1.AKKDC08 \
  --code AKKDC08
```

- **Mooré Bible**:
```bash
python crawlers/bible/crawl.py \
  --output_folder datasets/moore/bible/raw \
  --url https://www.bible.com/bible/3058/GEN.1.MPBU \
  --code MPBU
```
or if you prefer bash scripts, open [crawl.sh](./bible/crawl.sh), modify params as you wish then execute:
```bash
sh crawlers/bible/crawl.sh
```

On Windows, see [SETUP.md](../SETUP.md) for the environment setup that makes the crawler work.

**Inspect the output folder**, which should now contain one `<book>_<chapter>_<code>` pair per chapter:
```
   GEN_1_AKKDC08.txt    #transcript of Genesis 1
   GEN_1_AKKDC08.mp3    #audio of Genesis 1
   GEN_2_AKKDC08.txt
   GEN_2_AKKDC08.mp3
   ...
   AKKDC08.books        #book / chapter / title index
```

> bible.com regularly renames its CSS classes. If the crawler produces empty `.txt` files, update the class names in `bible_scraper.py`.

### TO DO
- [✅] [Dyula Bible AKKDC08](https://www.bible.com/bible/1754/GEN.1.AKKDC08)
- [✅] [WẼNNAAM SEBRE 2014](https://www.bible.com/bible/3058/GEN.1.MPBU) (Mooré)
- [✅] [Contes vol 2 avec audio](https://mooreburkina.com/fr/contes-et-proverbes-en-moor%C3%A9/contes-en-moor%C3%A9): Collection de 18 contes en moore (avec audio) écrit par SIBALLO Jacques
- [ ] [YouTube](#)
