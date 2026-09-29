import os
import json
import glob
import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed

import soundfile as sf
import librosa
from tqdm import tqdm

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_SR = 16000


def parse_args():
    parser = argparse.ArgumentParser(description="Convert aligned .flac segments to 16 kHz .wav and rewrite manifests")
    parser.add_argument("--input_folder", default=os.path.join(SCRIPT_DIR, "dyu_audio_sgmt"),
                        help="Folder of aligned chapters (<chapter>/manifest.json + .flac)")
    parser.add_argument("--output_folder", default=os.path.join(SCRIPT_DIR, "output"),
                        help="Where to write <chapter>/manifest.json + .wav")
    parser.add_argument("--workers", type=int, default=1,
                        help="Number of chapters converted in parallel (default: 1)")
    parser.add_argument("--start", type=int, default=0, help="Index of the first chapter to process (default: 0)")
    parser.add_argument("--end", type=int, default=None, help="Index after the last chapter to process (default: all)")
    return parser.parse_args()


def convert_chapter(chapter_path, base_output_dir):
    chapter_name = os.path.basename(chapter_path)
    output_chapter_dir = os.path.join(base_output_dir, chapter_name)

    manifest_input = os.path.join(chapter_path, "manifest.json")
    manifest_output = os.path.join(output_chapter_dir, "manifest.json")

    if not os.path.exists(manifest_input):
        return
    os.makedirs(output_chapter_dir, exist_ok=True)

    new_manifest_lines = []

    with open(manifest_input, "r", encoding="utf-8") as f:
        for line in f:
            data = json.loads(line)

            # Rebuild the flac path from the chapter dir we already resolved,
            # rather than trusting the CWD-relative path stored in the manifest.
            filename_flac = os.path.basename(data["audio_filepath"])
            old_flac_path = os.path.join(chapter_path, filename_flac)
            filename_wav = filename_flac.replace(".flac", ".wav")

            # New paths
            new_wav_path = os.path.join(output_chapter_dir, filename_wav)

            # Convert Audio
            try:
                audio, sr = sf.read(old_flac_path, dtype="int16")
                if sr != TARGET_SR:
                    audio = librosa.resample(
                        audio.astype("float32"), orig_sr=sr, target_sr=TARGET_SR
                    )
                    sr = TARGET_SR
                sf.write(new_wav_path, audio, sr, subtype="PCM_16")

                # Update metadata for the new manifest
                data["audio_filepath"] = new_wav_path
                new_manifest_lines.append(json.dumps(data, ensure_ascii=False))
            except Exception as e:
                print(f"Error processing {old_flac_path}: {e}")

    # Write updated manifest
    with open(manifest_output, "w", encoding="utf-8") as f:
        for line in new_manifest_lines:
            f.write(line + "\n")


def main():
    args = parse_args()
    base_output_dir = os.path.abspath(args.output_folder)

    # Get all chapter directories
    chapter_dirs = [
        p for p in sorted(glob.glob(os.path.join(args.input_folder, "*")))
        if os.path.isdir(p)
    ][args.start:args.end]

    if args.workers <= 1:
        for chapter_path in tqdm(chapter_dirs, desc="Processing Chapters"):
            convert_chapter(chapter_path, base_output_dir)
        return

    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(convert_chapter, p, base_output_dir) for p in chapter_dirs]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing Chapters"):
            future.result()


if __name__ == "__main__":
    main()
