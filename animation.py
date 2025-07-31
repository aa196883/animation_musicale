import time
import numpy as np
import pygame
import pretty_midi
from vispy import app, scene
from vispy.color import Color
from vispy.scene.visuals import Polygon
from vispy.scene.widgets import ViewBox

from typing import List
from timeline_extractor import TimelineFrame, extract_timeline  # à adapter selon ton organisation

DEBUG = False

class NoteVisual:
    def __init__( self, pitch: int, duration: float, color: str, angle_start: float, angle_size: float, base_radius: float = 100.0, radius_scale: float = 2.0) -> None:
        self.pitch: int = pitch
        self.duration: float = duration
        self.color: str = color
        self.angle_start: float = angle_start
        self.angle_size: float = angle_size
        self.base_radius: float = base_radius
        self.radius_scale: float = radius_scale

        self.vertices: np.ndarray = self.generate_shape()
        self.patch: Polygon = scene.visuals.Polygon(
            self.vertices,
            color=color,
            border_color='black',
            parent=None  # sera rattaché ensuite
        )

    def generate_shape(self, resolution: int = 20) -> np.ndarray:
        r: float = self.base_radius + self.pitch * self.radius_scale
        theta_start: float = self.angle_start
        theta_end: float = self.angle_start + self.angle_size

        angles: np.ndarray = np.linspace(theta_start, theta_end, resolution)
        x: np.ndarray = r * np.cos(angles)
        y: np.ndarray = r * np.sin(angles)

        points: np.ndarray = np.vstack(([0, 0], np.column_stack((x, y))))
        return points

    def attach_to(self, parent: scene.Node) -> None:
        self.patch.parent = parent

    def update_opacity(self, alpha: float) -> None:
        col: List[float] = list(Color(self.color).rgba)
        col[-1] = alpha
        self.patch.set_data(color=col)


class VisualizerApp(scene.SceneCanvas):
    def __init__(self, timeline: List[TimelineFrame], max_notes: int) -> None:
        super().__init__(title='MIDI Visualizer', keys='interactive', size=(800, 800), show=True)

        self.unfreeze()
        self.start_time = time.perf_counter()
        self.timeline: List[TimelineFrame] = timeline
        self.max_notes: int = max_notes
        self.current_frame: int = 0

        self.view: ViewBox = self.central_widget.add_view()
        self.view.camera = scene.cameras.PanZoomCamera(aspect=1)
        self.view.camera.set_range(x=(-300, 300), y=(-300, 300))

        self.note_visuals: List[NoteVisual] = []

        self.timer: app.Timer = app.Timer(interval=1/30, connect=self.on_timer, start=True)

    def on_timer(self, event) -> None:
        self.view.scene.children.clear()
        # Supprimer les objets graphiques de la scène précédente
        for note in self.note_visuals:
            note.patch.parent = None  # détache proprement le visuel de la scène
        self.note_visuals.clear()

        elapsed_time = time.perf_counter() - self.start_time
        # Trouver la frame dont frame.time <= elapsed_time < frame.time suivante
        frame_index = max(i for i, f in enumerate(self.timeline) if f.time <= elapsed_time)

        frame: TimelineFrame = self.timeline[frame_index]
        angle_unit: float = 2 * np.pi / self.max_notes if self.max_notes > 0 else np.pi
        angle_cursor: float = 0.0

        if DEBUG:
            print(f"\n🌀 Frame {frame_index} — time = {frame.time:.3f}s")
            total_notes = sum(len(notes) for notes in frame.notes_by_instrument.values())
            print(f"Total notes actives : {total_notes}")
            print(f"Angle unitaire (note) : {np.degrees(angle_unit):.2f}°")

        for instr_id, notes in frame.notes_by_instrument.items():
            if not notes:
                continue

            if DEBUG:
                print(f"🎼 Instrument {instr_id} — {len(notes)} note(s)") 
            for note in notes:
                if DEBUG:
                    print(f"  🎵 pitch={note.pitch}, dur={note.duration:.2f}s, angle={np.degrees(angle_cursor):.2f}°")

                nv = NoteVisual(
                    pitch=note.pitch,
                    duration=note.duration,
                    color=note.color,
                    angle_start=angle_cursor,
                    angle_size=angle_unit
                )
                nv.attach_to(self.view.scene)
                self.note_visuals.append(nv)

                angle_cursor += angle_unit

        if elapsed_time > self.timeline[-1].time + 1.0:  # 1 sec de buffer
            if DEBUG:
                print("🎬 Animation terminée — fermeture.")
            self.close()

    def on_key_press(self, event: app.KeyEvent) -> None:
        if event.key == 'Q' or event.key == 'Escape':
            if DEBUG:
                print("Touche 'q' pressée — fermeture.")
            self.close()

    def on_close(self, event) -> None:
        app.quit()


if __name__ == "__main__":
    path =  "audio/bad_liar"
    # Charger le fichier MIDI
    pm = pretty_midi.PrettyMIDI(path+".mid")
    timeline, max_notes, _ = extract_timeline(pm)

    # Initialiser et jouer le fichier audio synchronisé (exporté au format .wav)
    pygame.mixer.init()
    pygame.mixer.music.load(path+".wav")
    pygame.mixer.music.play()

    # Lancer l’animation
    vis_app = VisualizerApp(timeline, max_notes)
    vis_app.start_time = time.perf_counter()  # Point de référence pour l'animation
    vis_app.show()
    app.run()