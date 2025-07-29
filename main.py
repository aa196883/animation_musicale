import pretty_midi
import csv
from collections import defaultdict

def midi_to_quantized_csv(midi_path, csv_path):
    pm = pretty_midi.PrettyMIDI(midi_path)

    # Étape 1 : Récupérer tous les timestamps de début/fin de note
    change_times = set()
    for instr in pm.instruments:
        for note in instr.notes:
            change_times.add(note.start)
            change_times.add(note.end)

    # Tri des timestamps
    sorted_times = sorted(change_times)

    # Étape 2 : Préparer les colonnes (instruments)
    instrument_labels = []
    instrument_notes = []
    for idx, instr in enumerate(pm.instruments):
        name = f"Instrument_{idx}"
        if instr.name:
            name += f"_{instr.name}"
        elif instr.program < 128:
            name += f"_{pretty_midi.program_to_instrument_name(instr.program)}"
        instrument_labels.append(name)
        instrument_notes.append(instr.notes)

    # Étape 3 : Créer une table [time][instrument] = notes actives
    timeline = []
    for t in sorted_times:
        row = [t]
        for notes in instrument_notes:
            active_notes = [n.pitch for n in notes if n.start <= t < n.end]
            row.append(" ".join(str(p) for p in sorted(active_notes)))
        timeline.append(row)

    # Étape 4 : Écriture CSV
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        header = ['time_sec'] + instrument_labels
        writer.writerow(header)
        for row in timeline:
            writer.writerow(row)

    print(f"✅ CSV généré : {csv_path}")

# Exemple d’utilisation
midi_to_quantized_csv('bad_liar.mid', 'timeline.csv')
