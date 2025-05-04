import os
import json
import pretty_midi
from collections import Counter
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

# === Track Filtering Heuristics ===

def should_exclude_track(notes, short_duration_thresh=0.0725, dominant_pitch_ratio=0.8,
                         window_size=9, window_pitch_diversity_thresh=3, low_diversity_window_ratio=0.8):
    if not notes:
        return False
    avg_duration = sum(note.end - note.start for note in notes) / len(notes)
    if avg_duration <= short_duration_thresh:
        return True
    pitches = [note.pitch for note in notes]
    pitch_counts = Counter(pitches)
    most_common_pitch_ratio = pitch_counts.most_common(1)[0][1] / len(pitches)
    if most_common_pitch_ratio >= dominant_pitch_ratio:
        return True
    if len(pitches) >= window_size:
        low_div_windows = 0
        total_windows = len(pitches) - window_size + 1
        for i in range(total_windows):
            window = pitches[i:i + window_size]
            if len(set(window)) < window_pitch_diversity_thresh:
                low_div_windows += 1
        if total_windows > 0 and (low_div_windows / total_windows) >= low_diversity_window_ratio:
            return True
    return False

# === Extract only relative pitch differences ===

def extract_pitch_intervals(notes):
    pitches = [note.pitch for note in notes]
    return [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]

# === Process One MIDI File ===

def process_midi_file(midi_path):
    try:
        pm = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        return None, f" Failed to process {midi_path}: {e}"

    track_results = []

    for idx, instrument in enumerate(pm.instruments):
        notes = sorted(instrument.notes, key=lambda n: n.start)
        if not notes or should_exclude_track(notes):
            continue

        intervals = extract_pitch_intervals(notes)
        if not intervals:
            continue

        # Force conversion to Python native types
        intervals = [int(i) for i in intervals]

        track_results.append({
            "track_index": int(idx),
            "instrument_name": str(instrument.name or "Unknown"),
            "program": int(instrument.program),
            "is_drum": bool(instrument.is_drum),
            "pitch_intervals": intervals
        })

    return track_results, None



# === Traverse Directory and Save Only Interval JSONs ===

def process_all_midis(base_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    for artist in os.listdir(base_dir):
        artist_path = os.path.join(base_dir, artist)
        if not os.path.isdir(artist_path):
            continue

        artist_output_path = os.path.join(output_dir, artist)
        os.makedirs(artist_output_path, exist_ok=True)

        for file in os.listdir(artist_path):
            if not file.lower().endswith(('.mid', '.midi')):
                continue

            file_path = os.path.join(artist_path, file)
            data, error = process_midi_file(file_path)

            if data is None:
                print(error)
                continue

            song_name = os.path.splitext(file)[0]
            output_path = os.path.join(artist_output_path, f"{song_name}.json")
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

    print(f"\n All MIDI files processed and saved to: {output_dir}")

# === Run Script ===

if __name__ == "__main__":
    process_all_midis(
        base_dir=r"C:\Users\Ben Dizdar\Downloads\clean_midi\clean_midi_deduplicated_and_bytes",
        output_dir=r"Z:\clean_midi_deduplicated_and_bytes_intervals_only"
    )
