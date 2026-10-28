# tree_model.py
# Reines Datenmodell für mehrstufige Zufallsexperimente.
# Bewusst OHNE py5-Abhängigkeit, damit es testbar bleibt und später
# leicht um "mit Zurücklegen" erweitert werden kann.

from __future__ import annotations
from dataclasses import dataclass, field
from itertools import product

MAX_STUFEN = 10
MAX_OUTCOMES = 5


@dataclass
class Outcome:
    """Ein möglicher Ausgang pro Stufe, z.B. 'Kopf' mit p=0.5."""
    name: str
    p: float                       # Wahrscheinlichkeit 0..1
    color: tuple[int, int, int] = (100, 100, 100)


@dataclass
class Path:
    """Ein kompletter Pfad durch den Baum (eine Folge von Outcomes)."""
    outcomes: list[Outcome]

    @property
    def probability(self) -> float:
        """1. Pfadregel: Wahrscheinlichkeiten entlang des Pfades multiplizieren."""
        prob = 1.0
        for o in self.outcomes:
            prob *= o.p
        return prob

    @property
    def label(self) -> str:
        return " → ".join(o.name for o in self.outcomes)


@dataclass
class TreeModel:
    """Hält Stufen + Outcomes und berechnet daraus alle Pfade."""
    stufen: int
    outcomes: list[Outcome]        # gelten für ALLE Stufen (gleichbleibend)

    def __post_init__(self):
        if not (1 <= self.stufen <= MAX_STUFEN):
            raise ValueError(f"stufen muss 1..{MAX_STUFEN} sein, war {self.stufen}")
        if not (1 <= len(self.outcomes) <= MAX_OUTCOMES):
            raise ValueError(
                f"outcomes muss 1..{MAX_OUTCOMES} sein, waren {len(self.outcomes)}"
            )
        total = sum(o.p for o in self.outcomes)
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Summe der Wahrscheinlichkeiten muss 1 sein, war {total}")

    def paths(self) -> list[Path]:
        """Alle möglichen Pfade = outcomes^stufen (Kartesisches Produkt)."""
        return [Path(list(combo)) for combo in product(self.outcomes, repeat=self.stufen)]

    def path_probabilities(self) -> dict[str, float]:
        """Dict Pfad-Label -> Wahrscheinlichkeit (nützlich fürs spätere UI)."""
        return {p.label: p.probability for p in self.paths()}


def validate_outcomes(outcomes: list[Outcome]) -> bool:
    """Hilfsfunktion fürs UI: prüfen, ob Summe der p's 1 ergibt."""
    return abs(sum(o.p for o in outcomes) - 1.0) < 1e-6