import os
import shutil
import time
from datetime import datetime
import pretty_midi
import difflib
import re

def normalize_filename(name):
    name = name.lower()
    name = name.replace('.mid', '').replace('.midi', '')
    name = name.replace('(copy)', '')
    name = re.sub(r'[\W_]+', ' ', name)  # remove punctuation
    name = re.sub(r'\b(copy|remastered|live|version|edit)\b', '', name)
    name = re.sub(r'\s*\(?\d+\)?$', '', name)  # strip trailing .1, (1), etc.
    return name.strip()

def is_similar(name, seen_names, threshold=0.9):
    return any(difflib.SequenceMatcher(None, name, existing).ratio() >= threshold for existing in seen_names)

def is_valid_midi_range(midi_data):
    for instrument in midi_data.instruments:
        for note in instrument.notes:
            if not (0 <= note.pitch <= 127 and 0 <= note.velocity <= 127):
                return False
        for cc in instrument.control_changes:
            if not (0 <= cc.value <= 127):
                return False
    return True

def scan_and_copy_midi(base_dir, output_dir, log_file="midi_integrity_log.txt"):
    start_time = time.time()
    start_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    success_count = 0
    failure_count = 0
    duplicate_count = 0

    with open(log_file, "w", encoding="utf-8") as log:
        log.write(f"Scan started at: {start_timestamp}\n\n")

        for artist in os.listdir(base_dir):
            artist_path = os.path.join(base_dir, artist)
            if not os.path.isdir(artist_path):
                continue

            seen_song_names = []
            output_artist_path = os.path.join(output_dir, artist)
            os.makedirs(output_artist_path, exist_ok=True)

            for file in sorted(os.listdir(artist_path)):
                if not file.lower().endswith(('.mid', '.midi')):
                    continue

                file_path = os.path.join(artist_path, file)
                normalized_name = normalize_filename(file)

                if is_similar(normalized_name, seen_song_names):
                    print(f"Duplicate (fuzzy match) skipped: {file_path}")
                    log.write(f"Duplicate (fuzzy match) skipped: {file_path}\n")
                    duplicate_count += 1
                    continue

                try:
                    midi_data = pretty_midi.PrettyMIDI(file_path)

                    if not is_valid_midi_range(midi_data):
                        raise ValueError("Data byte out of 0..127 range")

                    seen_song_names.append(normalized_name)

                    dest_file_path = os.path.join(output_artist_path, file)
                    shutil.copy2(file_path, dest_file_path)

                    print(f"Copied: {file_path}")
                    log.write(f"{file_path} -> {dest_file_path}\n")
                    success_count += 1

                except Exception as e:
                    print(f"Failed: {file_path} | Reason: {type(e).__name__}: {e}")
                    log.write(f"{file_path} | Reason: {type(e).__name__}: {e}\n")
                    failure_count += 1

        end_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        elapsed = time.time() - start_time

        log.write("\n Summary:\n")
        log.write(f"{success_count} valid files copied\n")
        log.write(f"{duplicate_count} duplicates skipped (fuzzy match)\n")
        log.write(f"{failure_count} failed files\n")
        log.write(f"\n Scan finished at: {end_timestamp}\n")
        log.write(f"Elapsed time: {elapsed:.2f} seconds\n")

    print(f"\n Finished at: {end_timestamp}")
    print(f" Total time: {elapsed:.2f} seconds")
    print(f" Log saved to: {log_file}")

if __name__ == "__main__":
    midi_root = r"C:\Users\Ben Dizdar\Downloads\clean_midi\clean_midi"
    output_root = r"C:\Users\Ben Dizdar\Downloads\clean_midi\clean_midi_deduplicated_and_bytes"
    scan_and_copy_midi(midi_root, output_root)

