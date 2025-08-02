from typing import Optional
import numpy as np
from vispy import scene
from vispy.scene.visuals import Polygon
from timeline_extractor import NoteEvent  # ou ta propre version

class NoteVisual:
    def __init__(self, note: NoteEvent) -> None:
        self.note = note
        self.angle_start = 0.0
        self.angle_total = 0.0
        self.patch: Optional[Polygon] = None

        self.base_radius = 100.0
        self.radius_scale = 2.0
        self.max_radius = self.base_radius + self.note.pitch * self.radius_scale

    def is_alive(self, t: float) -> bool:
        return self.note.start <= t <= self.note.end

    def progress(self, t: float) -> float:
        return (t - self.note.start) / self.note.duration if self.note.duration > 0 else 0.0

    def compute_radius(self, t: float) -> float:
        p = self.progress(t)
        attack = 0.15
        release = 0.15
        if p < attack:
            return self.max_radius * (p / attack)
        elif p > 1 - release:
            return self.max_radius * ((1 - p) / release)
        else:
            return self.max_radius

    def generate_shape(self, t: float, resolution: int = 20) -> np.ndarray:
        # r = self.compute_radius(t)
        r = self.max_radius
        if r < 154:
            print(r)

        angles = np.linspace(self.angle_start, self.angle_start + self.angle_total, resolution)
        x = r * np.cos(angles)
        y = r * np.sin(angles)
        return np.vstack(([0, 0], np.column_stack((x, y))))

    def update(self, t: float, parent: scene.Node) -> None:
        vertices = self.generate_shape(t)
        if self.patch is None:
            self.patch = Polygon(vertices, color=self.note.color, border_color='black', parent=parent)
        else:
            self.patch.parent = None  # supprimer l'ancien
            self.patch = scene.visuals.Polygon(
                vertices,
                color=self.note.color,
                border_color='black',
                parent=parent
            )

    def destroy(self) -> None:
        if self.patch:
            self.patch.parent = None
            self.patch = None

    def __repr__(self) -> str:
        return (
            f"<NoteVisual pitch={self.note.pitch} "
            f"start={self.note.start:.2f} "
            f"end={self.note.end:.2f} "
            f"dur={self.note.duration:.2f} "
            f"angle=({np.degrees(self.angle_start):.1f}°→{np.degrees(self.angle_start + self.angle_total):.1f}°) "
            f"color={self.note.color}> "
        )