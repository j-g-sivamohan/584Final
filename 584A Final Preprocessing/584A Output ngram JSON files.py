import os
import json
import pretty_midi
from collections import Counter
import warnings

warnings.filterwarnings("ignore", category=RuntimeWarning)

# === Track Filtering Heuristics ===

def is_monotonous_track(notes, duration_tolerance=0.05, interval_tolerance=0.05):
    if len(notes) < 2:
        return False
    notes = sorted(notes, key=lambda n: n.start)
    durations = [note.end - note.start for note in notes]
    intervals = [notes[i+1].start - notes[i].start for i in range(len(notes)-1)]
    avg_duration = sum(durations) / len(durations)
    avg_interval = sum(intervals) / len(intervals)
    duration_monotony = all(abs(d - avg_duration) <= duration_tolerance for d in durations)
    interval_monotony = all(abs(i - avg_interval) <= interval_tolerance for i in intervals)
    return duration_monotony and interval_monotony

def should_exclude_track(notes, short_duration_thresh=0.0725, dominant_pitch_ratio=0.8, window_size=9, window_pitch_diversity_thresh=3, low_diversity_window_ratio=0.8):
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

# === Optional: Supermaximal Repeat Dependencies ===

# class InternalNode:
#     def __init__(self, left, depth):
#         self.left = left
#         self.depth = depth
#         self.children = []
#         self.is_leaf_only = True
#         self.prev_chars = set()

# def build_suffix_array(seq):
#     return sorted(range(len(seq)), key=lambda i: seq[i:])

# def build_lcp(seq, sa):
#     n = len(seq)
#     rank = [0] * n
#     for i in range(n):
#         rank[sa[i]] = i
#     lcp = [0] * (n - 1)
#     h = 0
#     for i in range(n):
#         if rank[i] == 0:
#             h = 0
#             continue
#         j = sa[rank[i] - 1]
#         while i + h < n and j + h < n and seq[i + h] == seq[j + h]:
#             h += 1
#         lcp[rank[i] - 1] = h
#         if h > 0:
#             h -= 1
#     return lcp

# def collect_supermaximal_repeats(seq, sa, lcp, min_len=5):
#     n = len(seq)
#     supermaximal_repeats = set()
#     stack = []
#     def visit(left, right, depth):
#         if right <= left:
#             return
#         prev_chars = set()
#         for i in range(left, right + 1):
#             idx = sa[i]
#             prev_chars.add(seq[idx - 1] if idx > 0 else None)
#         is_left_supermaximal = len(prev_chars) == (right - left + 1)
#         if is_left_supermaximal and depth >= min_len:
#             substr = tuple(seq[sa[left]:sa[left] + depth])
#             supermaximal_repeats.add(substr)
#     stack.append(InternalNode(0, 0))
#     for i in range(1, n):
#         lcp_val = lcp[i - 1]
#         right = i - 1
#         while stack and lcp_val < stack[-1].depth:
#             top = stack.pop()
#             visit(top.left, right, top.depth)
#             right = top.left
#         if not stack or lcp_val > stack[-1].depth:
#             new_node = InternalNode(right, lcp_val)
#             stack.append(new_node)
#     visit(n - 1, n - 1, 0)
#     while stack:
#         top = stack.pop()
#         visit(top.left, n - 1, top.depth)
#     return supermaximal_repeats

# === Interval + n-gram utilities ===

def extract_pitch_intervals(notes):
    pitches = [note.pitch for note in notes]
    return [pitches[i+1] - pitches[i] for i in range(len(pitches)-1)]

def get_interval_ngrams(intervals, n=3):
    return [tuple(intervals[i:i+n]) for i in range(len(intervals)-n+1)]

def chroma_encode(pitches):
    return [p % 12 + 1 for p in pitches]

# === Main MIDI File Processor ===

def process_midi_file(midi_path, ngram_n=3):
    try:
        pm = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        return None, f" Failed to process {midi_path}: {e}"

    track_results = []

    for instrument in pm.instruments:
        notes = sorted(instrument.notes, key=lambda n: n.start)
        if not notes or should_exclude_track(notes):
            continue

        chroma_dur_seq = [[note.pitch % 12 + 1, round(note.end - note.start, 4)] for note in notes]
        intervals = extract_pitch_intervals(notes)
        interval_ngrams = get_interval_ngrams(intervals, n=ngram_n)

        # --- Optional supermax repeat logic ---
        # chroma_seq = [c for c, d in chroma_dur_seq]
        # sa = build_suffix_array(chroma_seq)
        # lcp = build_lcp(chroma_seq, sa)
        # repeats = collect_supermaximal_repeats(chroma_seq, sa, lcp)

        track_results.append({
            "instrument": instrument.name or "Unknown",
            "chroma_duration": chroma_dur_seq,
            "pitch_intervals": intervals,
            "interval_ngrams": interval_ngrams,
            # "supermaximal_repeats": [list(r) for r in sorted(repeats, key=len, reverse=True)]
        })

    return track_results, None

# === Traverse Directory and Save JSONs ===

def process_all_midis(base_dir, output_dir, ngram_n=3):
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
            data, error = process_midi_file(file_path, ngram_n=ngram_n)

            if data is None:
                print(error)
                continue

            song_name = os.path.splitext(file)[0]
            output_path = os.path.join(artist_output_path, f"{song_name}.json")
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)

    print(f"\n All MIDI files processed and saved to: {output_dir}")

# === Run if script is executed directly ===

if __name__ == "__main__":
    process_all_midis(
        base_dir=r"C:\Users\Ben Dizdar\Downloads\clean_midi\clean_midi_deduplicated_and_bytes",
        output_dir=r"Z:\clean_midi_deduplicated_and_bytes_text_n_gram",
        ngram_n=6  # Adjustable n-gram size for interval fingerprinting
    )

"""
import os
import json
from fastdtw import fastdtw
from scipy.spatial.distance import euclidean

# === Config: Paths to two JSON files ===
query_json_path = r"Z:\clean_midi_deduplicated_and_bytes_text_n_gram\Puff Daddy\I'll Be Missing You.1.json"
candidate_json_path = r"Z:\clean_midi_deduplicated_and_bytes_text_n_gram\Sting\The Police - Every Breath You Take.json"
DISTANCE_FN = lambda x, y: abs(x - y)  # scalar distance for 1D intervals

# === Helper: Safely extract pitch intervals ===
def get_flat_pitch_intervals(track):
    raw = track.get("pitch_intervals", [])
    return [int(i[0]) if isinstance(i, list) else int(i) for i in raw if isinstance(i, (int, float, list))]

# === Helper: Choose best track (longest interval list) ===
def choose_main_track(json_data):
    best = max(json_data, key=lambda t: len(t.get("pitch_intervals", [])), default=None)
    return get_flat_pitch_intervals(best) if best else []

# === Load and compare two tracks ===
def compare_two_json_tracks(file1, file2):
    try:
        with open(file1) as f1:
            data1 = json.load(f1)
        with open(file2) as f2:
            data2 = json.load(f2)
    except Exception as e:
        print(f"Failed to load JSON files: {e}")
        return

    intervals1 = choose_main_track(data1)
    intervals2 = choose_main_track(data2)

    if len(intervals1) < 2 or len(intervals2) < 2:
        print(" One or both tracks are too short for DTW.")
        return

    try:
        dist, path = fastdtw(intervals1, intervals2, dist=DISTANCE_FN)
        print(f" DTW distance between:\n{os.path.basename(file1)} and\n{os.path.basename(file2)}\nis: {dist:.2f}")
    except Exception as e:
        print(f"DTW failed: {e}")

# === Run ===
if __name__ == "__main__":
    compare_two_json_tracks(query_json_path, candidate_json_path)
"""

