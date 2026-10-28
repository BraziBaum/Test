# main.py
# Erster visueller Prototyp: Baumdiagramm für "ohne Zurücklegen"-artige
# Experimente mit gleichbleibenden Wahrscheinlichkeiten.
# Zoom mit Mausrad, Pan per Maus-Drag.

import py5
from tree_model import TreeModel, Outcome, MAX_STUFEN, MAX_OUTCOMES

# -------- Konfiguration (später aus UI) --------
STUFEN = 3
OUTCOMES = [
    Outcome("Kopf", 0.5, (66, 133, 244)),
    Outcome("Zahl", 0.5, (219, 68, 55)),
]

# Layout-Parameter
NODE_R = 18
LEVEL_HEIGHT = 150
LEAF_SPACING = 110

# Kamera (Zoom + Pan)
zoom = 1.0
pan_x = 0.0
pan_y = 0.0

model: TreeModel | None = None
nodes: list[dict] = []   # {level, index, x, y, outcome}


def build_nodes(m: TreeModel):
    """Berechnet Knotenpositionen Level für Level."""
    global nodes
    nodes = []
    n_paths = len(m.outcomes) ** m.stufen  # Anzahl Blätter
    root_x = (n_paths - 1) * LEAF_SPACING / 2

    for level in range(m.stufen + 1):
        count = len(m.outcomes) ** level
        # Blattabstand auf diesem Level
        span = (n_paths - 1) * LEAF_SPACING / max(count - 1, 1) if count > 1 else 0
        for i in range(count):
            x = root_x - span * (count - 1) / 2 + i * span if count > 1 else root_x
            y = level * LEVEL_HEIGHT
            outcome = None if level == 0 else m.outcomes[0]  # Platzhalter
            nodes.append({"level": level, "index": i, "x": x, "y": y})


def setup():
    global model
    py5.size(900, 700)
    py5.smooth()
    model = TreeModel(stufen=STUFEN, outcomes=OUTCOMES)
    build_nodes(model)
    # Kamera zentrieren
    global pan_x, pan_y
    pan_x = py5.width / 2
    pan_y = 80


def draw():
    py5.background(250)
    py5.push_matrix()
    py5.translate(pan_x, pan_y)
    py5.scale(zoom)

    # Kanten zeichnen
    py5.stroke(180)
    py5.stroke_weight(2 / zoom)
    py5.no_fill()
    for level in range(model.stufen):
        parents = [n for n in nodes if n["level"] == level]
        children = [n for n in nodes if n["level"] == level + 1]
        for child in children:
            parent = parents[child["index"] // len(model.outcomes)]
            py5.line(parent["x"], parent["y"], child["x"], child["y"])

    # Knoten zeichnen
    for n in nodes:
        py5.no_stroke()
        if n["level"] == 0:
            py5.fill(60)
        else:
            outcome = model.outcomes[n["index"] % len(model.outcomes)]
            py5.fill(*outcome.color)
        py5.circle(n["x"], n["y"], NODE_R * 2)

    py5.pop_matrix()

    # Info
    py5.fill(40)
    py5.text_size(14)
    py5.text(f"Stufen: {model.stufen} | Outcomes: {len(model.outcomes)} "
             f"| Pfade: {len(model.paths())}", 20, 25)
    py5.text("Zoom: Mausrad | Pan: Maus ziehen", 20, 45)


def mouse_wheel(event):
    global zoom
    zoom = max(0.2, min(3.0, zoom * (1.1 if event.get_count() > 0 else 0.9)))


def mouse_dragged():
    global pan_x, pan_y
    pan_x += py5.mouse_x - py5.pmouse_x
    pan_y += py5.mouse_y - py5.pmouse_y


py5.run_sketch()