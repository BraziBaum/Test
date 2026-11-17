# main.py
# Baumdiagramm für mehrstufige Zufallsexperimente
# Stabilisierte Version mit repariertem Culling und sicherem Panning/Zoom.

from __future__ import annotations
from dataclasses import dataclass
from itertools import product

import py5

MAX_STUFEN = 10
MAX_OUTCOMES = 5
# Ein 10x5 Baum hat ~9,7 Mio Pfade. Das ist zu viel für flüssiges Zeichnen.
# Wir limitieren auf 100.000 Pfade (z.B. 5 Stufen bei 10 Optionen, oder 10 Stufen bei 3 Optionen).
MAX_PATHS_LIMIT = 100_000  

# ---------- Farbschema ----------
BG_SALBEI     = (222, 233, 221)
PANEL_SALBEI  = (204, 219, 204)
TEXT_DARK     = (46, 64, 54)
LINE_BASE     = (120, 150, 130)
HIGHLIGHT     = (255, 140, 60)
BTN_COLOR     = (150, 180, 160)
BTN_HOVER     = (130, 160, 140)
ERROR_COLOR   = (180, 60, 60)

OUTCOME_PALETTE = [
    (63, 114, 91), (198, 93, 82), (214, 168, 74), (74, 124, 168), (150, 108, 158)
]


# ============================================================
# MODELL
# ============================================================
@dataclass
class Outcome:
    name: str
    p: float
    color: tuple[int, int, int]


@dataclass
class Path:
    outcomes: list[Outcome]

    @property
    def probability(self) -> float:
        prob = 1.0
        for o in self.outcomes:
            prob *= o.p
        return prob


@dataclass
class TreeModel:
    stufen: int
    outcomes: list[Outcome]

    def __post_init__(self):
        if not (1 <= self.stufen <= MAX_STUFEN):
            raise ValueError(f"Stufen: 1-{MAX_STUFEN}")
        if not (1 <= len(self.outcomes) <= MAX_OUTCOMES):
            raise ValueError(f"Optionen: 1-{MAX_OUTCOMES}")
        total = sum(o.p for o in self.outcomes)
        if abs(total - 1.0) > 1e-6:
            raise ValueError("Summe muss 1 sein")

    def paths(self) -> list[Path]:
        return [Path(list(c)) for c in product(self.outcomes, repeat=self.stufen)]


# ============================================================
# EINGABEFELD
# ============================================================
class InputField:
    def __init__(self, x, y, w, h, label, value):
        self.x, self.y, self.w, self.h = x, y, w, h
        self.label = label
        self.value = str(value)
        self.active = False
        self.on_change = None

    def draw(self):
        py5.no_stroke()
        py5.fill(*TEXT_DARK)
        py5.text_size(13)
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text(self.label, self.x, self.y + self.h / 2)

        bx = self.x + 130
        if self.active:
            py5.stroke(*TEXT_DARK)
            py5.stroke_weight(2)
        else:
            py5.stroke(*LINE_BASE)
            py5.stroke_weight(1)
            
        py5.fill(245)
        py5.rect(bx, self.y, self.w, self.h, 6)

        py5.no_stroke()
        py5.fill(*TEXT_DARK)
        py5.text_align(py5.LEFT, py5.CENTER)
        py5.text(self.value, bx + 8, self.y + self.h / 2)

    def contains(self, mx, my):
        bx = self.x + 130
        return bx <= mx <= bx + self.w and self.y <= my <= self.y + self.h

    def handle_click(self, mx, my):
        self.active = self.contains(mx, my)

    def handle_key(self, key, key_code):
        if not self.active:
            return False
        if key == py5.BACKSPACE:
            self.value = self.value[:-1]
        elif key == py5.ENTER or key == py5.RETURN:
            self.active = False
            if self.on_change:
                self.on_change(self.value)
        elif 32 <= key_code <= 126 and len(self.value) < 3:
            if chr(key_code).isdigit():
                self.value += chr(key_code)
        return True


# ============================================================
# GLOBAL STATE
# ============================================================
model: TreeModel | None = None
nodes: list[dict] = []
level_offsets: list[int] = []
is_too_large = False

stufen_field: InputField | None = None
optionen_field: InputField | None = None
error_msg = ""

view_scale = 1.0
view_offset_x = 0.0
view_offset_y = 0.0

# Dynamische Layout-Variablen
WORLD_LEVEL_H = 150
WORLD_LEAF_W = 110
NODE_R_WORLD = 18
PANEL_H = 90

is_panning = False
last_mouse_x = 0
last_mouse_y = 0


# ============================================================
# BUILD & LAYOUT
# ============================================================
def build_model(stufen: int, optionen: int):
    global model, nodes, level_offsets, error_msg, is_too_large
    global WORLD_LEVEL_H, WORLD_LEAF_W, NODE_R_WORLD

    stufen = max(1, min(MAX_STUFEN, stufen))
    optionen = max(1, min(MAX_OUTCOMES, optionen))

    p = 1.0 / optionen
    names = [f"O{i+1}" for i in range(optionen)]
    outcomes = [Outcome(name=names[i], p=p, color=OUTCOME_PALETTE[i]) for i in range(optionen)]

    try:
        model = TreeModel(stufen=stufen, outcomes=outcomes)
        error_msg = ""
    except ValueError as e:
        error_msg = str(e)
        return

    total_paths = optionen ** stufen
    if total_paths > MAX_PATHS_LIMIT:
        is_too_large = True
        return
    is_too_large = False

    # --- DYNAMISCHES LAYOUT ---
    # Je größer der Baum, desto kleiner die Abstände und Knoten
    if total_paths > 10000:
        NODE_R_WORLD = 2.0
        WORLD_LEAF_W = 3.5
        WORLD_LEVEL_H = 50
    elif total_paths > 1000:
        NODE_R_WORLD = 4.0
        WORLD_LEAF_W = 10
        WORLD_LEVEL_H = 80
    elif total_paths > 100:
        NODE_R_WORLD = 8.0
        WORLD_LEAF_W = 25
        WORLD_LEVEL_H = 120
    else:
        NODE_R_WORLD = 18.0
        WORLD_LEAF_W = 110
        WORLD_LEVEL_H = 150

    nodes = []
    level_offsets = []
    root_x = (total_paths - 1) * WORLD_LEAF_W / 2

    current_offset = 0
    for level in range(stufen + 1):
        level_offsets.append(current_offset)
        count = optionen ** level
        
        if count > 1:
            span = (total_paths - 1) * WORLD_LEAF_W / (count - 1)
        else:
            span = 0
            
        for i in range(count):
            if count > 1:
                x = root_x - span * (count - 1) / 2 + i * span
            else:
                x = root_x
            y = level * WORLD_LEVEL_H
            nodes.append({"level": level, "index": i, "x": x, "y": y})
        
        current_offset += count

    fit_to_window()


def fit_to_window():
    global view_scale, view_offset_x, view_offset_y
    if not nodes:
        return

    xs = [n["x"] for n in nodes]
    ys = [n["y"] for n in nodes]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    pad = NODE_R_WORLD * 2

    world_w = (max_x - min_x) + pad * 2
    world_h = (max_y - min_y) + pad * 2

    avail_w = py5.width - 40
    avail_h = py5.height - PANEL_H - 40

    if world_w == 0 or world_h == 0:
        return

    view_scale = min(avail_w / world_w, avail_h / world_h, 1.2)
    view_scale = max(view_scale, 0.01)

    cx = (min_x + max_x) / 2
    cy = (min_y + max_y) / 2
    view_offset_x = py5.width / 2 - cx * view_scale
    view_offset_y = (PANEL_H + (py5.height - PANEL_H) / 2) - cy * view_scale


def world_to_screen(x, y):
    return x * view_scale + view_offset_x, y * view_scale + view_offset_y

def screen_to_world(x, y):
    return (x - view_offset_x) / view_scale, (y - view_offset_y) / view_scale


# ============================================================
# HOVER (OPTIMIERT)
# ============================================================
def get_path_node_indices(leaf_index: int) -> list[int]:
    if model is None: return []
    k = len(model.outcomes)
    indices = []
    choices = []
    idx = leaf_index
    for _ in range(model.stufen):
        choices.append(idx % k)
        idx //= k
    choices.reverse()
    
    indices.append(level_offsets[0] + 0)
    current_position = 0
    for level, choice in enumerate(choices):
        current_position = current_position * k + choice
        indices.append(level_offsets[level + 1] + current_position)
    return indices


def find_hovered_path() -> tuple[Path, list[int]] | None:
    if model is None or is_too_large or py5.mouse_y < PANEL_H:
        return None
        
    wx, wy = screen_to_world(py5.mouse_x, py5.mouse_y)
    r_world = NODE_R_WORLD * 1.6
    if r_world < 5: r_world = 5 # Mindest-Hover-Radius für kleine Knoten

    start_idx = level_offsets[-1]
    k = len(model.outcomes)
    n_leaves = k ** model.stufen
    
    approx_leaf_x = (wx / WORLD_LEAF_W)
    search_radius = 10 
    
    start_search = max(0, int(approx_leaf_x) - search_radius)
    end_search = min(n_leaves, int(approx_leaf_x) + search_radius)

    for i in range(start_search, end_search):
        leaf_node = nodes[start_idx + i]
        dx = leaf_node["x"] - wx
        dy = leaf_node["y"] - wy
        if dx * dx + dy * dy <= r_world * r_world:
            path_outcomes = []
            idx = leaf_node["index"]
            for _ in range(model.stufen):
                path_outcomes.append(model.outcomes[idx % k])
                idx //= k
            path = Path(list(reversed(path_outcomes)))
            node_indices = get_path_node_indices(leaf_node["index"])
            return path, node_indices
            
    return None


# ============================================================
# SETUP / DRAW
# ============================================================
def setup():
    py5.size(1000, 780)
    py5.smooth()
    try:
        py5.text_font(py5.create_font("Arial", 14))
    except Exception:
        pass

    global stufen_field, optionen_field
    stufen_field = InputField(20, 20, 60, 30, "Stufen (1-10):", 3)
    optionen_field = InputField(20, 55, 60, 30, "Optionen (1-5):", 2)

    stufen_field.on_change = lambda v: _apply(v, None)
    optionen_field.on_change = lambda v: _apply(None, v)

    build_model(3, 2)


def _apply(stufen_str, optionen_str):
    global stufen_field, optionen_field
    try:
        s = int(stufen_str) if stufen_str else int(stufen_field.value or 1)
        o = int(optionen_str) if optionen_str else int(optionen_field.value or 1)
    except ValueError:
        return
    stufen_field.value = str(s)
    optionen_field.value = str(o)
    build_model(s, o)


def draw():
    py5.background(*BG_SALBEI)

    if is_too_large:
        _draw_too_large_msg()
        _draw_panel()
        return

    if model is None:
        _draw_panel()
        return

    hovered_data = find_hovered_path()
    hovered_path, hovered_set = (None, set())
    if hovered_data:
        hovered_path, hovered_indices = hovered_data
        hovered_set = set(hovered_indices)

    _draw_edges(hovered_set, hovered_path)
    _draw_nodes(hovered_set)
    _draw_panel()

    if hovered_path is not None and not is_panning:
        _draw_hover_tooltip(hovered_path)


def _draw_too_large_msg():
    py5.fill(*ERROR_COLOR)
    py5.text_size(18)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text(f"Dieser Baum ist zu groß.\nMaximal {MAX_PATHS_LIMIT:,} Pfade werden unterstützt.", py5.width/2, py5.height/2)


def _draw_panel():
    py5.no_stroke()
    py5.fill(*PANEL_SALBEI)
    py5.rect(0, 0, py5.width, PANEL_H)
    py5.stroke(*LINE_BASE)
    py5.stroke_weight(1)
    py5.line(0, PANEL_H, py5.width, PANEL_H)

    stufen_field.draw()
    optionen_field.draw()

    btn_x, btn_y, btn_w, btn_h = 420, 20, 130, 30
    is_hover = btn_x <= py5.mouse_x <= btn_x + btn_w and btn_y <= py5.mouse_y <= btn_y + btn_h
    py5.fill(*(BTN_HOVER if is_hover else BTN_COLOR))
    py5.no_stroke()
    py5.rect(btn_x, btn_y, btn_w, btn_h, 6)
    
    py5.fill(255)
    py5.text_size(13)
    py5.text_align(py5.CENTER, py5.CENTER)
    py5.text("Fit to Window", btn_x + btn_w/2, btn_y + btn_h/2)

    py5.fill(*TEXT_DARK)
    py5.text_align(py5.LEFT, py5.CENTER)
    info = f"Pfade: {len(model.paths()) if model and not is_too_large else 'Zu groß'}"
    py5.text(info, 420, PANEL_H / 2 + 18)

    py5.fill(100, 120, 105)
    py5.text_size(11)
    py5.text("Mausrad: Zoom | R-Klick + Ziehen: Verschieben", 580, PANEL_H / 2 + 18)


def _draw_edges(hovered_set, hovered_path):
    py5.no_fill()
    
    min_sx, min_sy = -50, PANEL_H - 50
    max_sx, max_sy = py5.width + 50, py5.height + 50

    for level in range(model.stufen):
        offset_parents = level_offsets[level]
        offset_children = level_offsets[level + 1]
        
        n_children = len(model.outcomes) ** (level + 1)
        
        for child_idx in range(n_children):
            child = nodes[offset_children + child_idx]
            cx, cy = world_to_screen(child["x"], child["y"])
            
            parent_idx = child_idx // len(model.outcomes)
            parent = nodes[offset_parents + parent_idx]
            px, py = world_to_screen(parent["x"], parent["y"])
            
            # CULLING: Zeichne die Kante, wenn mindestens ein Punkt sichtbar ist
            if (cx < min_sx and px < min_sx) or (cx > max_sx and px > max_sx) or \
               (cy < min_sy and py < min_sy) or (cy > max_sy and py > max_sy):
                continue
                
            parent_global = offset_parents + parent_idx
            child_global = offset_children + child_idx
            
            is_hl = (parent_global in hovered_set and child_global in hovered_set) if hovered_path else False

            if is_hl:
                py5.stroke(*HIGHLIGHT)
                py5.stroke_weight(max(1.5, 3.5 * view_scale))
            else:
                py5.stroke(*LINE_BASE)
                py5.stroke_weight(max(0.5, 1.0 * view_scale))
            
            py5.line(px, py, cx, cy)


def _draw_nodes(hovered_set):
    py5.stroke_weight(0)
    
    min_sx, min_sy = -50, PANEL_H - 50
    max_sx, max_sy = py5.width + 50, py5.height + 50

    for i, n in enumerate(nodes):
        x, y = world_to_screen(n["x"], n["y"])
        
        if not (min_sx <= x <= max_sx and min_sy <= y <= max_sy):
            continue

        r = max(NODE_R_WORLD * view_scale, 1.5)

        if n["level"] == 0:
            color = TEXT_DARK
        else:
            k = len(model.outcomes)
            outcome_idx = n["index"] % k
            color = model.outcomes[outcome_idx].color

        py5.no_stroke()
        py5.fill(*color)
        py5.circle(x, y, r * 2)

        if i in hovered_set:
            py5.no_fill()
            py5.stroke(*HIGHLIGHT)
            py5.stroke_weight(max(2, 4 * view_scale))
            py5.circle(x, y, r * 2 + max(4, 8 * view_scale))


def _draw_hover_tooltip(path):
    probs = [o.p for o in path.outcomes]
    prob_str = " × ".join(f"{p:g}" for p in probs)
    if all(abs(p - probs[0]) < 1e-9 for p in probs) and len(probs) > 1:
        prob_str += f" = {probs[0]:g}^{len(probs)}"
    prob_str += f" = {path.probability:.4f} = {path.probability*100:.2f} %"

    py5.text_size(13)
    title = "Pfad:"
    step_names = " → ".join(o.name for o in path.outcomes)
    
    w_steps = py5.text_width(step_names)
    w_calc = py5.text_width(prob_str)
    circle_space = 20
    w_circles = len(path.outcomes) * circle_space
    
    max_w = max(w_steps, w_calc, w_circles)
    box_w = max_w + 40
    box_h = 90
    
    mx, my = py5.mouse_x, py5.mouse_y
    bx = min(mx + 18, py5.width - box_w - 10)
    by = max(my - box_h - 10, PANEL_H + 10)

    py5.no_stroke()
    py5.fill(255, 255, 255, 245)
    py5.rect(bx, by, box_w, box_h, 8)
    
    py5.no_fill()
    py5.stroke(*HIGHLIGHT)
    py5.stroke_weight(2)
    py5.rect(bx, by, box_w, box_h, 8)

    py5.no_stroke()
    py5.fill(*TEXT_DARK)
    py5.text_align(py5.LEFT, py5.TOP)
    py5.text(title, bx + 12, by + 10)
    py5.text(step_names, bx + 50, by + 10)
    
    start_x = bx + 12
    start_y = by + 35
    for i, o in enumerate(path.outcomes):
        py5.fill(*o.color)
        py5.circle(start_x + i * circle_space, start_y + 6, 12)
        
    py5.fill(*TEXT_DARK)
    py5.text(prob_str, bx + 12, by + 55)


# ============================================================
# INPUT, ZOOM & PANNING
# ============================================================
def mouse_pressed():
    global is_panning, last_mouse_x, last_mouse_y

    btn_x, btn_y, btn_w, btn_h = 420, 20, 130, 30
    if btn_x <= py5.mouse_x <= btn_x + btn_w and btn_y <= py5.mouse_y <= btn_y + btn_h:
        fit_to_window()
        return

    stufen_field.handle_click(py5.mouse_x, py5.mouse_y)
    optionen_field.handle_click(py5.mouse_x, py5.mouse_y)

    if py5.mouse_button == 39:  # Rechtsklick
        is_panning = True
        last_mouse_x = py5.mouse_x
        last_mouse_y = py5.mouse_y


def mouse_released():
    global is_panning
    if py5.mouse_button == 39:
        is_panning = False


def mouse_dragged():
    global view_offset_x, view_offset_y, last_mouse_x, last_mouse_y
    if is_panning:
        dx = py5.mouse_x - last_mouse_x
        dy = py5.mouse_y - last_mouse_y
        view_offset_x += dx
        view_offset_y += dy
        last_mouse_x = py5.mouse_x
        last_mouse_y = py5.mouse_y


def key_pressed():
    if stufen_field.handle_key(py5.key, py5.key_code):
        return
    if optionen_field.handle_key(py5.key, py5.key_code):
        return


def mouse_wheel(event):
    """Sicherer Zoom. Wir ignorieren Touchpad-Spezifika, die oft crashen."""
    global view_scale, view_offset_x, view_offset_y
    
    # get_count() ist der zuverlässigste Wert in py5 für Mausrad/Touchpad-Zoom
    count = event.get_count()
    if count == 0:
        return
        
    factor = 1.05 ** (1 if count > 0 else -1)
    new_scale = max(0.01, min(8.0, view_scale * factor))
    
    mx, my = py5.mouse_x, py5.mouse_y
    wx, wy = screen_to_world(mx, my)
    view_scale = new_scale
    view_offset_x = mx - wx * view_scale
    view_offset_y = my - wy * view_scale


def window_resized():
    fit_to_window()


py5.run_sketch()