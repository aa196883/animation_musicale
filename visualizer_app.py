import time
import pygame
import pretty_midi
from typing import List, Dict, Optional
from vispy import scene, app
import numpy as np

from timeline_extractor import TimelineFrame, NoteEvent, extract_timeline
from note_visual import NoteVisual  # nouvelle version refactorée

class VisualizerApp(scene.SceneCanvas):
    def __init__(self, timeline: List[TimelineFrame]) -> None:
        super().__init__(title="Visualizer", keys='interactive', size=(800, 800), show=True)
        self.unfreeze()

        self.timeline = timeline
        self.current_frame = 0
        self.start_time: float = time.perf_counter()

        self.view = self.central_widget.add_view()
        self.view.camera = scene.cameras.PanZoomCamera(aspect=1)
        self.view.camera.set_range(x=(-400, 400), y=(-400, 400))

        self.note_visuals: List[NoteVisual] = []

        self.angle_persec = 2 * np.pi / self._compute_max_frame_note_cardinal() if self._compute_max_frame_note_cardinal() > 0 else 0

        self._generate_note_visuals()

        self.timer = app.Timer(interval=1.0/60, connect=self.on_timer, start=True)
        self.music_end_time = self.timeline[-1].time + 1.0

    def _compute_max_frame_duration(self) -> float:
        max_duration = 0.0
        for i, frame in enumerate(self.timeline):
            frame_duration = 0
            for notes in frame.notes_by_instrument.values():
                for note in notes:
                    frame_duration += note.duration
            if frame_duration > max_duration:
                max_duration = frame_duration
        return max_duration

    def _compute_max_frame_note_cardinal(self) -> int:
        """Retourne le nombre maximum de notes simultanées sur une frame de la timeline."""
        max_notes = 0
        for frame in self.timeline:
            active_notes = sum(len(notes) for notes in frame.notes_by_instrument.values())
            if active_notes > max_notes:
                max_notes = active_notes
        return max_notes

    def _generate_note_visuals(self) -> None:
        """Créer tous les NoteVisual à partir de la timeline, avec leur taille angulaire basée sur la durée."""
        all_notes: List[NoteEvent] = []
        for frame in self.timeline:
            for notes in frame.notes_by_instrument.values():
                all_notes.extend(notes)

        # Supprimer les doublons (car les notes sont répétées dans plusieurs frames)
        unique_notes = { (n.pitch, n.start, n.end, n.instrument): n for n in all_notes }.values()

        for note in sorted(unique_notes, key=lambda n: (n.start, n.instrument)):
            nv = NoteVisual(note)
            self.note_visuals.append(nv)

    def _get_active_notes_sorted(self, t: float) -> List[NoteVisual]:
        """
        Retourne la liste triée des NoteVisual actives à l’instant t,
        triée par instrument (ordre croissant), puis par durée croissante,
        puis par pitch croissant.
        """
        frame_index = max(i for i, f in enumerate(self.timeline) if f.time <= t)
        frame = self.timeline[frame_index]

        active_notes: List[NoteEvent] = []
        for instr_id in sorted(frame.notes_by_instrument):  # instruments dans l’ordre
            notes = frame.notes_by_instrument[instr_id]
            notes_sorted = sorted(notes, key=lambda n: (n.duration, n.pitch))
            active_notes.extend(notes_sorted)

        # Associer les NoteEvent à leur NoteVisual
        note_visual_map = {
            (nv.note.start, nv.note.pitch, nv.note.instrument): nv
            for nv in self.note_visuals
        }

        result = []
        for n in active_notes:
            key = (n.start, n.pitch, n.instrument)
            nv = note_visual_map.get(key)
            if nv:
                result.append(nv)

        return result
    
    def on_timer(self, event) -> None:
        t = time.perf_counter() - self.start_time

        # 1. Récupérer et trier les notes actives
        active_notes = self._get_active_notes_sorted(t)

        # 2. Nettoyer les anciens visuels s’ils sont morts
        for nv in self.note_visuals:
            if not nv.is_alive(t):
                nv.destroy()

        # 3. Répartition dynamique des angles
        angle_cursor = 0.0

        total_dur = 0.0
        for nv in active_notes:
            nv.angle_start = angle_cursor
            nv.angle_total = self.angle_persec
            nv.update(t, self.view.scene)
            angle_cursor += nv.angle_total
            total_dur += nv.note.duration

        # 4. Fermeture automatique
        if t > self.music_end_time:
            print("🎬 Fin de la musique — fermeture.")
            self.close()


    def on_key_press(self, event: app.KeyEvent) -> None:
        if event.key == 'Q':
            print("⌨️ 'q' pressé — fermeture.")
            self.close()



if __name__ == "__main__":
    path =  "audio/bad_liar"
    # Charger le fichier MIDI
    pm = pretty_midi.PrettyMIDI(path+".mid")
    timeline, _ = extract_timeline(pm)

    # Initialiser et jouer le fichier audio synchronisé (exporté au format .wav)
    pygame.mixer.init()
    pygame.mixer.music.load(path+".wav")
    pygame.mixer.music.play()

    # Lancer l’animation
    vis_app = VisualizerApp(timeline)
    vis_app.start_time = time.perf_counter()  # Point de référence pour l'animation
    vis_app.show()
    app.run()