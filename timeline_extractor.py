from dataclasses import dataclass
from typing import List, Dict
import pretty_midi

@dataclass
class NoteEvent:
    pitch: int
    velocity: int
    start: float
    end: float
    duration: float
    instrument: int
    color: str

@dataclass
class TimelineFrame:
    time: float
    notes_by_instrument: Dict[int, List[NoteEvent]]

def extract_timeline(pm: pretty_midi.PrettyMIDI) -> tuple[List[TimelineFrame], int, Dict[int, str]]:
    # Étape 1 : rassembler tous les timestamps de début/fin de notes
    change_times = set()
    for instr in pm.instruments:
        for note in instr.notes:
            change_times.add(note.start)
            change_times.add(note.end)
    sorted_times = sorted(change_times)

    # Étape 2 : assigner une couleur par instrument
    color_palette = [
        "#FF6B6B", "#6BCB77", "#4D96FF", "#FFD93D",
        "#C34A36", "#9D4EDD", "#38B6FF", "#FF924C",
        "#00A878", "#FF4D6D"
    ]
    instrument_colors = {}
    instrument_notes = []
    for idx, instr in enumerate(pm.instruments):
        color = color_palette[idx % len(color_palette)]
        instrument_colors[idx] = color
        instrument_notes.append((idx, instr.notes))

    # Étape 3 : construire les frames
    timeline = []
    for t in sorted_times:
        notes_by_instr = {}
        for idx, notes in instrument_notes:
            active_notes = [
                NoteEvent(
                    pitch=n.pitch,
                    velocity=n.velocity,
                    start=n.start,
                    end=n.end,
                    duration=n.end - n.start,
                    instrument=idx,
                    color=instrument_colors[idx]
                )
                for n in notes if n.start <= t < n.end
            ]
            active_notes.sort(key=lambda n: (-n.duration, n.pitch))
            notes_by_instr[idx] = active_notes
        timeline.append(TimelineFrame(time=t, notes_by_instrument=notes_by_instr))

    # Étape 4 : trouver le nombre max de notes simultanées
    max_notes = max(
        sum(len(notes) for notes in frame.notes_by_instrument.values())
        for frame in timeline
    )

    return timeline, max_notes, instrument_colors

if __name__ == "__main__":
    midi_path = 'bad_liar.mid'
    pm = pretty_midi.PrettyMIDI(midi_path)
    timeline, max_notes, colors =  extract_timeline(pm)
    print(f"Max notes simultanées : {max_notes}")
    for i, frame in enumerate(timeline):
        print(f"Frame {i} : {frame}")