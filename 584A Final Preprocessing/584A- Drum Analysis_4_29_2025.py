import os
import pretty_midi
from collections import Counter
import warnings

# Suppress known pretty_midi format warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

def analyze_rhythm_tracks(base_dir, output_file="rhythm_track_summary.txt"):
    with open(output_file, "w", encoding="utf-8") as out:
        for artist in os.listdir(base_dir):
            artist_path = os.path.join(base_dir, artist)
            if not os.path.isdir(artist_path):
                continue

            for file in os.listdir(artist_path):
                if not file.lower().endswith(('.mid', '.midi')):
                    continue

                file_path = os.path.join(artist_path, file)
                try:
                    pm = pretty_midi.PrettyMIDI(file_path)
                except Exception as e:
                    out.write(f"Failed to load {file_path}: {e}\n")
                    print(f"Failed to load: {file_path}")
                    continue

                if not any(inst.notes for inst in pm.instruments):
                    out.write(f" No note-containing tracks found in {file_path}\n")
                    print(f"No usable tracks in: {file_path}")
                    continue

                out.write(f"\n {artist} — {file}\n")
                print(f" Processing: {file_path}")

                for idx, inst in enumerate(pm.instruments):
                    try:
                        pitches = [note.pitch for note in inst.notes]
                        pitch_counts = Counter(pitches)

                        if not pitches:
                            out.write(f"--- Track {idx} has no notes ---\n\n")
                            continue

                        is_drum = "Yes" if inst.is_drum else "No"
                        name = inst.name if inst.name else "Unnamed"
                        pitch_min = min(pitches)
                        pitch_max = max(pitches)
                        note_count = len(pitches)

                        out.write(f"--- Track {idx} ---\n")
                        out.write(f"Name           : {name}\n")
                        out.write(f"Is Drum        : {is_drum}\n")
                        out.write(f"Program        : {inst.program} ({pretty_midi.program_to_instrument_name(inst.program)})\n")
                        out.write(f"Note Count     : {note_count}\n")
                        out.write(f"Pitch Range    : {pitch_min} to {pitch_max}\n")
                        out.write(f"Pitch Spread   : {pitch_max - pitch_min}\n")
                        out.write(f"Unique Pitches : {len(set(pitches))}\n")
                        out.write(f"Pitch Frequencies:\n")

                        for pitch, count in pitch_counts.most_common():
                            out.write(f"  - {pitch:3} ({pretty_midi.note_number_to_name(pitch):3}): {count} times\n")

                        out.write("\n")
                    except Exception as e:
                        out.write(f" Failed to analyze track {idx} in {file_path}: {e}\n")
                        print(f" Error in track {idx} of: {file_path}")

    print(f"\n Rhythm track analysis complete.\n Summary saved to: {output_file}")

if __name__ == "__main__":
    base_dir = r"C:\Users\Ben Dizdar\Downloads\clean_midi\clean_midi_deduplicated_and_bytes"
    analyze_rhythm_tracks(base_dir)


