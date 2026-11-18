# ==============================================================================
# BAUMDIAGRAMM GENERATOR
# Ein interaktives Tool zur Visualisierung von mehrstufigen Zufallsexperimenten.
# Kompakt, performant und mit Hover-Highlighting.
# ==============================================================================

import py5
from dataclasses import dataclass
from itertools import product

# --- KONFIGURATION & STYLING ---
MAX_S, MAX_O, LIMIT = 10, 5, 100_000   # Limits für Stufen, Optionen und Pfade
BG = (222, 233, 221)                    # Hintergrund: Salbeigrün
PANEL = (204, 219, 204)                 # Panel-Farbe
TEXT = (46, 64, 54)                     # Dunkelgrün für Text
LINE = (120, 150, 130)                  # Linienfarbe
HL = (255, 140, 60)                     # Highlight: Orange
BTN = (150, 180, 160)                   # Button-Farbe
PALETTE = [(63,114,91), (198,93,82), (214,168,74), (74,124,168), (150,108,158)] # 5 Farben

# --- DATENMODELL ---
# Definiert die mathematische Struktur des Baums (unabhängig von der Grafik).
@dataclass
class Out:
    name: str
    p: float
    color: tuple

@dataclass
class Tree:
    stufen: int
    outs: list[Out]

    def __post_init__(self):
        # Validierung der Eingaben
        assert 1 <= self.stufen <= MAX_S
        assert 1 <= len(self.outs) <= MAX_O
        assert abs(sum(o.p for o in self.outs) - 1.0) < 1e-6

    def path_prob(self, idx):
        # Berechnet die Wahrscheinlichkeit für einen Pfad (1. Pfadregel)
        p = 1.0
        for _ in range(self.stufen):
            p *= self.outs[idx % len(self.outs)].p
            idx //= len(self.outs)
        return p

# --- GLOBALER ZUSTAND ---
m: Tree | None = None
nodes, offsets = [], []
scale, ox, oy = 1.0, 0.0, 0.0
drag = False
mx, my = 0, 0
too_big = False
LVL_H, LEAF_W, NODE_R = 150.0, 110.0, 18.0 # Dynamische Layout-Werte
PANEL_H = 90

# --- LAYOUT & KAMERA ---
def build_tree(s, o):
    """Erzeugt das Modell und berechnet die Positionen aller Knoten."""
    global m, nodes, offsets, too_big, LVL_H, LEAF_W, NODE_R
    
    s, o = max(1, min(MAX_S, s)), max(1, min(MAX_O, o))
    total = o ** s
    
    if total > LIMIT:
        too_big = True
        return
    too_big = False

    # Modell aufbauen (Gleichverteilung)
    m = Tree(s, [Out(f"O{i+1}", 1.0/o, PALETTE[i]) for i in range(o)])

    # Dynamische Anpassung der Größen, damit große Bäume auf den Schirm passen
    if total > 10000:   LVL_H, LEAF_W, NODE_R = 50.0, 3.5, 2.0
    elif total > 1000:  LVL_H, LEAF_W, NODE_R = 80.0, 10.0, 4.0
    elif total > 100:   LVL_H, LEAF_W, NODE_R = 120.0, 25.0, 8.0
    else:               LVL_H, LEAF_W, NODE_R = 150.0, 110.0, 18.0

    # Knoten berechnen (Level für Level)
    nodes, offsets = [], []
    root_x = (total - 1) * LEAF_W / 2
    curr_off = 0
    
    for lvl in range(s + 1):
        offsets.append(curr_off)
        cnt = o ** lvl
        span = (total - 1) * LEAF_W / max(cnt - 1, 1) if cnt > 1 else 0
        
        for i in range(cnt):
            x = root_x - span * (cnt - 1) / 2 + i * span if cnt > 1 else root_x
            nodes.append({"lvl": lvl, "idx": i, "x": x, "y": lvl * LVL_H})
        curr_off += cnt
        
    fit_screen()

def fit_screen():
    """Zentriert den Baum und skaliert ihn so, dass er komplett sichtbar ist."""
    global scale, ox, oy
    if not nodes: return

    xs, ys = [n["x"] for n in nodes], [n["y"] for n in nodes]
    w = (max(xs) - min(xs)) + NODE_R * 4
    h = (max(ys) - min(ys)) + NODE_R * 4
    
    # Skalierung berechnen (mit etwas Rand)
    scale = max(0.01, min((py5.width - 40) / w, (py5.height - PANEL_H - 40) / h, 1.2))
    
    # Offset berechnen, um den Baum zu zentrieren
    ox = py5.width / 2 - ((min(xs) + max(xs)) / 2) * scale
    oy = (PANEL_H + (py5.height - PANEL_H) / 2) - ((min(ys) + max(ys)) / 2) * scale

def to_screen(x, y): return x * scale + ox, y * scale + oy
def to_world(x, y):  return (x - ox) / scale, (y - oy) / scale

# --- HOVER-LOGIK ---
def get_path_indices(leaf_idx):
    """Berechnet die globalen Indizes der Knoten auf dem Pfad zum Blatt."""
    k = len(m.outs)
    res = [offsets[0]]
    
    # Basis-k Zerlegung des Blatt-Index
    choices = []
    for _ in range(m.stufen):
        choices.append(leaf_idx % k)
        leaf_idx //= k
    choices.reverse()
    
    pos = 0
    for lvl, c in enumerate(choices):
        pos = pos * k + c
        res.append(offsets[lvl + 1] + pos)
    return res

def get_hover():
    """Findet den Pfad unter der Maus (optimiert für große Bäume)."""
    if not m or too_big or py5.mouse_y < PANEL_H: return None
    
    wx, wy = to_world(py5.mouse_x, py5.mouse_y)
    r2 = (max(NODE_R * 1.6, 5)) ** 2
    
    # Nur Blätter in der Nähe der Maus prüfen (Performance!)
    k, n_leaves = len(m.outs), len(m.outs) ** m.stufen
    start = max(0, int(wx / LEAF_W) - 10)
    end = min(n_leaves, int(wx / LEAF_W) + 10)

    for i in range(start, end):
        leaf = nodes[offsets[-1] + i]
        if (leaf["x"] - wx)**2 + (leaf["y"] - wy)**2 <= r2:
            idx = leaf["idx"]
            outs = []
            for _ in range(m.stufen):
                outs.append(m.outs[idx % k])
                idx //= k
            return outs[::-1], get_path_indices(leaf["idx"])
    return None

# --- ZEICHNEN ---
def setup():
    py5.size(1000, 780)
    py5.smooth()
    py5.text_font(py5.create_font("Arial", 14))
    build_tree(3, 2)

def draw():
    py5.background(*BG)
    if too_big:
        py5.fill(180, 60, 60); py5.text_size(18); py5.text_align(py5.CENTER, py5.CENTER)
        py5.text("Baum zu groß für flüssige Darstellung!\nMaximal 100.000 Pfade.", py5.width/2, py5.height/2)
        draw_panel(); return
    if not m: draw_panel(); return

    h_data = get_hover()
    h_path, h_set = (h_data[0], set(h_data[1])) if h_data else (None, set())

    draw_edges(h_set, h_path)
    draw_nodes(h_set)
    draw_panel()

    if h_path and not drag: draw_tooltip(h_path)

def draw_edges(h_set, h_path):
    py5.no_fill()
    for lvl in range(m.stufen):
        off_p, off_c = offsets[lvl], offsets[lvl + 1]
        for ci in range(len(m.outs) ** (lvl + 1)):
            child = nodes[off_c + ci]
            cx, cy = to_screen(child["x"], child["y"])
            
            # Culling: Überspringe Kanten außerhalb des Bildschirms
            if not (-50 < cx < py5.width + 50 and PANEL_H - 50 < cy < py5.height + 50):
                parent = nodes[off_p + ci // len(m.outs)]
                px, py = to_screen(parent["x"], parent["y"])
                if not (-50 < px < py5.width + 50 and PANEL_H - 50 < py < py5.height + 50): continue
            
            parent = nodes[off_p + ci // len(m.outs)]
            px, py = to_screen(parent["x"], parent["y"])
            is_hl = h_path is not None and (off_p + ci // len(m.outs)) in h_set and (off_c + ci) in h_set
            
            py5.stroke(*(HL if is_hl else LINE))
            py5.stroke_weight(max(0.5, (3.5 if is_hl else 1.0) * scale))
            py5.line(px, py, cx, cy)

def draw_nodes(h_set):
    for i, n in enumerate(nodes):
        x, y = to_screen(n["x"], n["y"])
        if not (-50 < x < py5.width + 50 and PANEL_H - 50 < y < py5.height + 50): continue
        
        r = max(NODE_R * scale, 1.5)
        c = TEXT if n["lvl"] == 0 else m.outs[n["idx"] % len(m.outs)].color
        
        py5.no_stroke(); py5.fill(*c); py5.circle(x, y, r * 2)
        if i in h_set:
            py5.no_fill(); py5.stroke(*HL); py5.stroke_weight(max(2, 4 * scale))
            py5.circle(x, y, r * 2 + max(4, 8 * scale))

def draw_panel():
    py5.no_stroke(); py5.fill(*PANEL); py5.rect(0, 0, py5.width, PANEL_H)
    py5.stroke(*LINE); py5.stroke_weight(1); py5.line(0, PANEL_H, py5.width, PANEL_H)
    
    # Button
    bx, by, bw, bh = 420, 20, 130, 30
    hover = bx < py5.mouse_x < bx + bw and by < py5.mouse_y < by + bh
    py5.fill(*(BTN if hover else (130, 160, 140)))
    py5.rect(bx, by, bw, bh, 6)
    py5.fill(255); py5.text_size(13); py5.text_align(py5.CENTER, py5.CENTER)
    py5.text("Fit to Window", bx + bw/2, by + bh/2)
    
    # Info-Text
    py5.fill(*TEXT); py5.text_align(py5.LEFT, py5.CENTER)
    py5.text(f"Pfade: {len(m.outs)**m.stufen if m else 0}", 420, PANEL_H / 2 + 18)
    py5.fill(100, 120, 105); py5.text_size(11)
    py5.text("R-Klick + Ziehen: Verschieben", 580, PANEL_H / 2 + 18)

def draw_tooltip(path):
    # Lösungsweg berechnen
    ps = [o.p for o in path]
    calc = " × ".join(f"{p:g}" for p in ps) + f" = {ps[0]:g}^{len(ps)} = {m.path_prob(get_path_indices(0)[-1]):.4f}"
    # Hinweis: m.path_prob braucht den Index, wir nehmen hier den Pfad-Wert direkt
    prob = 1.0
    for o in path: prob *= o.p
    calc = " × ".join(f"{p:g}" for p in ps) + f" = {prob:.4f} = {prob*100:.2f} %"

    names = " → ".join(o.name for o in path)
    w = max(py5.text_width(names), py5.text_width(calc), len(path) * 20) + 40
    
    x, y = min(py5.mouse_x + 18, py5.width - w - 10), max(py5.mouse_y - 100, PANEL_H + 10)
    
    py5.no_stroke(); py5.fill(255, 255, 255, 245); py5.rect(x, y, w, 90, 8)
    py5.no_fill(); py5.stroke(*HL); py5.stroke_weight(2); py5.rect(x, y, w, 90, 8)
    
    py5.no_stroke(); py5.fill(*TEXT); py5.text_align(py5.LEFT, py5.TOP)
    py5.text("Pfad: " + names, x + 12, y + 10)
    
    for i, o in enumerate(path):
        py5.fill(*o.color); py5.circle(x + 18 + i * 20, y + 41, 12)
        
    py5.fill(*TEXT); py5.text(calc, x + 12, y + 55)

# --- INTERAKTION ---
def mouse_pressed():
    global drag, mx, my
    bx, by, bw, bh = 420, 20, 130, 30
    if bx < py5.mouse_x < bx + bw and by < py5.mouse_y < by + bh:
        fit_screen(); return
    if py5.mouse_button == 39: # Rechtsklick
        drag, mx, my = True, py5.mouse_x, py5.mouse_y

def mouse_released():
    global drag
    if py5.mouse_button == 39: drag = False

def mouse_dragged():
    global ox, oy, mx, my
    if drag:
        ox, oy = ox + (py5.mouse_x - mx), oy + (py5.mouse_y - my)
        mx, my = py5.mouse_x, py5.mouse_y

def mouse_wheel(event):
    global scale, ox, oy
    c = event.get_count()
    if c == 0: return
    
    # Zoom-Faktor berechnen und anwenden
    ns = max(0.01, min(8.0, scale * (1.05 ** (1 if c > 0 else -1))))
    wx, wy = to_world(py5.mouse_x, py5.mouse_y)
    scale = ns
    ox, oy = py5.mouse_x - wx * scale, py5.mouse_y - wy * scale

def window_resized():
    fit_screen()

py5.run_sketch()