import os
import pretty_midi
from collections import defaultdict
import numpy as np

# LDA scoring function from earlier
MELODY_PROGRAMS = {1, 5, 11, 40, 41, 65, 68, 72, 73, 74, 76}

def is_percussion(instrument):
    return instrument.is_drum or len(instrument.notes) == 0

def get_note_sequence(instrument):
    return [note.pitch for note in instrument.notes]

def get_note_durations(instrument):
    return [round(note.end - note.start, 3) for note in instrument.notes]

def ngrams(seq, n=3):
    from itertools import islice
    return list(zip(*(islice(seq, i, None) for i in range(n))))

def rhythmic_pattern_count(durations, resolution=1/16):
    rounded = [round(d / resolution) for d in durations]
    return len(set(ngrams(rounded, 4)))

def count_steps_jumps(seq):
    steps = 0
    jumps = 0
    for i in range(1, len(seq)):
        diff = abs(seq[i] - seq[i - 1])
        if diff == 1 or diff == 2:
            steps += 1
        elif diff > 2:
            jumps += 1
    return steps, jumps

def count_repeats(seq):
    return sum(1 for i in range(1, len(seq)) if seq[i] == seq[i - 1])

def melody_program_score(program):
    return 1.0 if program in MELODY_PROGRAMS else 0.0

def compute_lda_score(inst):
    pitches = get_note_sequence(inst)
    durations = get_note_durations(inst)

    if len(pitches) < 5:
        return -np.inf, 0

    prgP = melody_program_score(inst.program)
    pavg = np.mean(pitches)
    rpat = rhythmic_pattern_count(durations)
    zeros = count_repeats(pitches)
    steps, jumps = count_steps_jumps(pitches)

    lda = (
        0.066 * prgP +
        0.070 * rpat +
        -0.001 * zeros +
        0.123 * steps +
        -0.006 * jumps +
        0.038 * pavg
    )
    return lda, pavg

def is_viable_midi(file_path):
    try:
        midi = pretty_midi.PrettyMIDI(file_path)
        _ = midi.instruments  # Try accessing instruments
        return True
    except Exception as e:
        print(f"⚠️ Skipping {file_path}: {e}")
        return False

def evaluate_melody_detection(base_dir):
    truth_matrix = {"TP": [], "FP": [], "FN": [], "TN": []}

    for root, _, files in os.walk(base_dir):
        for file in files:
            if file.endswith('.mid') or file.endswith('.midi'):
                file_path = os.path.join(root, file)

                if not is_viable_midi(file_path):
                    continue

                try:
                    midi_data = pretty_midi.PrettyMIDI(file_path)
                    candidate_tracks = [inst for inst in midi_data.instruments if not is_percussion(inst)]
                    labeled_index = next((i for i, inst in enumerate(candidate_tracks)
                                          if 'melody' in inst.name.lower()), None)
                    lda_scores = [compute_lda_score(inst) for inst in candidate_tracks]
                    lda_values = [score for score, pitch in lda_scores]
                    best_index = int(np.argmax(lda_values)) if lda_values else None

                    if labeled_index is not None:
                        if best_index == labeled_index:
                            truth_matrix["TP"].append(file_path)
                        else:
                            truth_matrix["FN"].append(file_path)
                    else:
                        if best_index is not None and lda_scores[best_index][1] > 45:
                            truth_matrix["FP"].append(file_path)
                        else:
                            truth_matrix["TN"].append(file_path)

                except Exception as e:
                    print(f"⚠️ Failed during processing {file_path}: {e}")

    # Print truth matrix
    print("\n🎯 Truth Matrix Summary")
    for k in truth_matrix:
        print(f"{k}: {len(truth_matrix[k])} songs")
        with open(f"{k}_songs.txt", "w", encoding="utf-8") as f:
            for path in truth_matrix[k]:
                f.write(f"{path}\n")

if __name__ == "__main__":
    base_dir = "C:/Users/Ben Dizdar/Downloads/clean_midi/clean_midi"
    evaluate_melody_detection(base_dir) 