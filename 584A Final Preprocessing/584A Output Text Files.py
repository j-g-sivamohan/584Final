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

# === Suffix Array and Supermaximal Repeats ===

class InternalNode:
    def __init__(self, left, depth):
        self.left = left
        self.depth = depth
        self.children = []
        self.is_leaf_only = True
        self.prev_chars = set()

def build_suffix_array(seq):
    return sorted(range(len(seq)), key=lambda i: seq[i:])

def build_lcp(seq, sa):
    n = len(seq)
    rank = [0] * n
    for i in range(n):
        rank[sa[i]] = i

    lcp = [0] * (n - 1)
    h = 0
    for i in range(n):
        if rank[i] == 0:
            h = 0
            continue
        j = sa[rank[i] - 1]
        while i + h < n and j + h < n and seq[i + h] == seq[j + h]:
            h += 1
        lcp[rank[i] - 1] = h
        if h > 0:
            h -= 1
    return lcp


def collect_supermaximal_repeats(seq, sa, lcp, min_len=5):
    n = len(seq)
    supermaximal_repeats = set()
    stack = []

    def visit(left, right, depth):
        if right <= left:
            return
        prev_chars = set()
        for i in range(left, right + 1):
            idx = sa[i]
            prev_chars.add(seq[idx - 1] if idx > 0 else None)
        is_left_supermaximal = len(prev_chars) == (right - left + 1)
        if is_left_supermaximal and depth >= min_len:
            substr = tuple(seq[sa[left]:sa[left] + depth])
            supermaximal_repeats.add(substr)

    stack.append(InternalNode(0, 0))
    for i in range(1, n):
        lcp_val = lcp[i - 1]
        right = i - 1
        while stack and lcp_val < stack[-1].depth:
            top = stack.pop()
            visit(top.left, right, top.depth)
            right = top.left
        if not stack or lcp_val > stack[-1].depth:
            new_node = InternalNode(right, lcp_val)
            stack.append(new_node)

    visit(n - 1, n - 1, 0)
    while stack:
        top = stack.pop()
        visit(top.left, n - 1, top.depth)

    return supermaximal_repeats

def chroma_encode(pitches):
    return [p % 12 + 1 for p in pitches]  # 1=C, ..., 12=B

# === Process One MIDI File ===

def process_midi_file(midi_path):
    try:
        pm = pretty_midi.PrettyMIDI(midi_path)
    except Exception as e:
        return None, f"Failed to process {midi_path}: {e}"

    final_data = []

    for instrument in pm.instruments:
        notes = sorted(instrument.notes, key=lambda n: n.start)
        if not notes or should_exclude_track(notes):
            continue

        chroma_dur_seq = [[note.pitch % 12 + 1, round(note.end - note.start, 4)] for note in notes]
        chroma_seq = [c for c, d in chroma_dur_seq]

        sa = build_suffix_array(chroma_seq)
        lcp = build_lcp(chroma_seq, sa)
        repeats = collect_supermaximal_repeats(chroma_seq, sa, lcp)

        final_data.append(chroma_dur_seq)

        for r in sorted(repeats, key=len, reverse=True):
            positions = []
            for i in range(len(chroma_seq) - len(r) + 1):
                if tuple(chroma_seq[i:i + len(r)]) == r:
                    positions.append(i)
            for idx in positions:
                repeat_slice = chroma_dur_seq[idx:idx + len(r)]
                final_data.append(repeat_slice)

    return final_data, None

# === Traverse Directory and Save Output ===

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

# === Run ===

process_all_midis(
    base_dir=r"C:\Users\Ben Dizdar\Downloads\clean_midi\clean_midi_deduplicated_and_bytes",
    output_dir=r"Z:\clean_midi_deduplicated_and_bytes_text"
)
