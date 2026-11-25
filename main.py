# ==============================================================================
# BAUMDIAGRAMM GENERATOR (Ausführlich kommentiert)
# ==============================================================================

# Importiert die py5-Bibliothek, die für das Zeichnen und die Fenster benötigt wird.
import py5

# --- 1. EINSTELLUNGEN UND KONSTANTEN ---

# Maximale Anzahl an Stufen (Ebenen), die erlaubt ist.
MAX_STUFEN = 10
# Maximale Anzahl an Optionen (Ästen pro Knoten), die erlaubt ist.
MAX_OPTIONEN = 5
# Maximale Anzahl an Pfaden, um den Computer vor Überlastung zu schützen (100.000).
MAX_PFADE = 100000

# Die Hintergrundfarbe (ein helles Salbeigrün) als RGB-Tupel (Rot, Grün, Blau).
FARBE_HINTERGRUND = (222, 233, 221)
# Die Farbe für das obere Menü-Panel (ein etwas dunkleres Salbeigrün).
FARBE_PANEL = (204, 219, 204)
# Die Farbe für den Text (ein dunkles Salbeigrün, fast schwarz).
FARBE_TEXT = (46, 64, 54)
# Die Farbe für die Verbindungslinien im Baum (ein mittleres Salbeigrün).
FARBE_LINIE = (120, 150, 130)
# Die Farbe für Hervorhebungen (ein kräftiges Orange).
FARBE_HIGHLIGHT = (255, 140, 60)

# Eine Liste mit 5 unterschiedlichen Farben für die Optionen (Knoten).
FARBEN_OPTIONEN = [
    (63, 114, 91),   # Ein dunkles Grün.
    (198, 93, 82),   # Ein Terrakotta-Rot.
    (214, 168, 74),  # Ein Senfgelb.
    (74, 124, 168),  # Ein Staubblau.
    (150, 108, 158)  # Ein gedämpftes Lila.
]

# --- 2. GLOBALE ZUSTANDS-VARIABLEN ---
# Diese Variablen speichern den aktuellen Zustand des Programms und werden in
# verschiedenen Funktionen gelesen oder verändert.

# Eine Liste, die alle Knoten (Punkte) des Baums als Dictionaries speichert.
# Jeder Knoten hat die Schlüssel: "ebene", "index", "x" und "y".
knoten_liste = []
# Eine Liste, die speichert, an welchem Index in der knoten_liste eine neue Ebene beginnt.
ebenen_start = []
# Die aktuell eingestellte Anzahl an Stufen (Ebenen) im Baum.
aktuelle_stufen = 3
# Die aktuell eingestellte Anzahl an Optionen (Ästen) pro Knoten.
aktuelle_optionen = 2

# Die aktuelle Zoomstufe der Kamera (1.0 bedeutet 100%).
zoom = 1.0
# Die horizontale Verschiebung der Kamera in Pixeln.
verschiebung_x = 0.0
# Die vertikale Verschiebung der Kamera in Pixeln.
verschiebung_y = 0.0

# Der Radius der Knoten (Punkte) im Baum (wird dynamisch angepasst).
knoten_radius = 18.0
# Der vertikale Abstand zwischen den Ebenen (wird dynamisch angepasst).
ebenen_hoehe = 150.0
# Der horizontale Abstand zwischen den Blättern (wird dynamisch angepasst).
blatt_abstand = 110.0

# Die Höhe des oberen Menü-Panels in Pixeln.
PANEL_HOEHE = 90

# Ein Wahrheitswert (Boolean), der angibt, ob gerade mit der rechten Maustaste gezogen wird.
ziehe_gerade = False
# Ein Wahrheitswert (Boolean), der angibt, ob der Baum zu groß zum Zeichnen ist.
ist_zu_gross = False
# Die letzte X-Position der Maus beim Ziehen.
letzte_maus_x = 0
# Die letzte Y-Position der Maus beim Ziehen.
letzte_maus_y = 0

# Ein Dictionary, das alle Infos für das Eingabefeld "Stufen" speichert.
feld_stufen = {"x": 20, "y": 20, "text": "3", "label": "Stufen (1-10):", "aktiv": False}
# Ein Dictionary, das alle Infos für das Eingabefeld "Optionen" speichert.
feld_optionen = {"x": 20, "y": 55, "text": "2", "label": "Optionen (1-5):", "aktiv": False}

# --- 3. HILFSFUNKTIONEN ---

# Rechnet eine Koordinate aus der "Welt" (dem Baum) in Bildschirm-Pixel um.
def zu_bildschirm(welt_x, welt_y):
    # Berechnet die X-Position auf dem Bildschirm.
    bildschirm_x = welt_x * zoom + verschiebung_x
    # Berechnet die Y-Position auf dem Bildschirm.
    bildschirm_y = welt_y * zoom + verschiebung_y
    # Gibt beide Werte als Tupel zurück.
    return bildschirm_x, bildschirm_y

# Rechnet eine Bildschirm-Koordinate zurück in die "Welt" (für Mausklicks).
def zu_welt(bildschirm_x, bildschirm_y):
    # Berechnet die X-Position in der Welt.
    welt_x = (bildschirm_x - verschiebung_x) / zoom
    # Berechnet die Y-Position in der Welt.
    welt_y = (bildschirm_y - verschiebung_y) / zoom
    # Gibt beide Werte als Tupel zurück.
    return welt_x, welt_y

# Bestimmt die Farbe eines Knotens basierend auf seiner Position im Baum.
def knoten_farbe(knoten):
    # Wenn der Knoten auf Ebene 0 (die Wurzel) liegt, ist er dunkel.
    if knoten["ebene"] == 0:
        # Gibt die dunkle Textfarbe zurück.
        return FARBE_TEXT
    # Ansonsten wählt es eine Farbe aus der Palette basierend auf dem Index.
    return FARBEN_OPTIONEN[knoten["index"] % aktuelle_optionen]

# Zeichnet einen Kreis (Knoten) inklusive eines optionalen Highlight-Rings.
def zeichne_kreis(x, y, radius, farbe, ist_highlight):
    # Schaltet die Linienzeichnung aus.
    py5.no_stroke()
    # Setzt die Füllfarbe auf die übergebene Farbe.
    py5.fill(*farbe)
    # Zeichnet den Kreis an der Position (x, y) mit dem doppelten Radius (Durchmesser).
    py5.circle(x, y, radius * 2)
    # Wenn der Knoten hervorgehoben werden soll...
    if ist_highlight:
        # Schaltet die Füllung aus, damit nur der Rand gezeichnet wird.
        py5.no_fill()
        # Setzt die Randfarbe auf Orange.
        py5.stroke(*FARBE_HIGHLIGHT)
        # Setzt die Liniendicke (mindestens 2 Pixel, skaliert mit dem Zoom).
        py5.stroke_weight(max(2, 4 * zoom))
        # Zeichnet einen größeren Kreis als Rand um den Knoten.
        py5.circle(x, y, radius * 2 + max(4, 8 * zoom))

# --- 4. BAUM AUFBAUEN & LAYOUT ---

# Baut den Baum basierend auf der Anzahl der Stufen und Optionen auf.
def baue_baum(stufen, optionen):
    # Macht die globalen Variablen änderbar.
    global knoten_liste, ebenen_start, aktuelle_stufen, aktuelle_optionen, ist_zu_gross
    global knoten_radius, ebenen_hoehe, blatt_abstand

    # Begrenzt die eingegebenen Werte auf das erlaubte Minimum und Maximum.
    stufen = max(1, min(MAX_STUFEN, stufen))
    # Begrenzt die eingegebenen Werte auf das erlaubte Minimum und Maximum.
    optionen = max(1, min(MAX_OPTIONEN, optionen))
    # Speichert die neuen (begrenzten) Werte global.
    aktuelle_stufen, aktuelle_optionen = stufen, optionen

    # Prüft, ob die Gesamtzahl der Pfade das Limit überschreitet.
    if optionen ** stufen > MAX_PFADE:
        # Setzt das Flag, dass der Baum zu groß ist.
        ist_zu_gross = True
        # Bricht die Funktion ab.
        return
    # Setzt das Flag zurück, falls der Baum wieder klein genug ist.
    ist_zu_gross = False

    # Passt die Layout-Größen dynamisch an die Anzahl der Pfade an.
    if optionen ** stufen > 10000:
        # Sehr großer Baum: winzige Knoten, enge Abstände.
        knoten_radius, ebenen_hoehe, blatt_abstand = 2.0, 50.0, 3.5
    elif optionen ** stufen > 1000:
        # Großer Baum: kleine Knoten, mittlere Abstände.
        knoten_radius, ebenen_hoehe, blatt_abstand = 4.0, 80.0, 10.0
    elif optionen ** stufen > 100:
        # Mittlerer Baum: etwas kleinere Knoten.
        knoten_radius, ebenen_hoehe, blatt_abstand = 8.0, 120.0, 25.0
    else:
        # Kleiner Baum: normale Größen.
        knoten_radius, ebenen_hoehe, blatt_abstand = 18.0, 150.0, 110.0

    # Leert die Listen für den neuen Baum.
    knoten_liste, ebenen_start = [], []
    # Zählt mit, an welcher Stelle im Array die nächste Ebene beginnt.
    aktueller_start = 0
    # Berechnet die Mitte des Baumes (damit er zentriert ist).
    start_x = (optionen ** stufen - 1) * blatt_abstand / 2

    # Schleife für jede Ebene (von 0 bis zur Anzahl der Stufen).
    for ebene in range(stufen + 1):
        # Speichert den Start-Index für diese Ebene.
        ebenen_start.append(aktueller_start)
        # Berechnet, wie viele Knoten es auf dieser Ebene gibt.
        anzahl = optionen ** ebene
        # Berechnet den Abstand zwischen den Knoten auf dieser Ebene.
        abstand = (optionen**stufen - 1) * blatt_abstand / (anzahl - 1) if anzahl > 1 else 0

        # Schleife für jeden einzelnen Knoten auf dieser Ebene.
        for i in range(anzahl):
            # Berechnet die X-Position des Knotens.
            x_pos = start_x - abstand * (anzahl - 1) / 2 + i * abstand if anzahl > 1 else start_x
            # Fügt den Knoten der Liste hinzu (als Dictionary mit allen Infos).
            knoten_liste.append({"ebene": ebene, "index": i, "x": x_pos, "y": ebene * ebenen_hoehe})
        # Erhöht den Start-Index für die nächste Ebene.
        aktueller_start += anzahl
    # Passt den Baum am Ende automatisch ins Fenster ein.
    baum_einpassen()

# Passt den Baum ins Fenster ein (berechnet Zoom und Zentrierung).
def baum_einpassen():
    # Macht die globalen Variablen änderbar.
    global zoom, verschiebung_x, verschiebung_y
    # Wenn keine Knoten da sind, machen wir nichts.
    if not knoten_liste:
        return

    # Sammelt alle X-Koordinaten der Knoten in einer Liste.
    xs = [k["x"] for k in knoten_liste]
    # Sammelt alle Y-Koordinaten der Knoten in einer Liste.
    ys = [k["y"] for k in knoten_liste]
    # Berechnet die Breite des Baumes (mit etwas Rand).
    breite = max(xs) - min(xs) + knoten_radius * 4
    # Berechnet die Höhe des Baumes (mit etwas Rand).
    hoehe = max(ys) - min(ys) + knoten_radius * 4

    # Berechnet den optimalen Zoom-Faktor (mit min/max Begrenzung).
    zoom = max(0.01, min((py5.width - 40) / breite, (py5.height - PANEL_HOEHE - 40) / hoehe, 1.2))

    # Berechnet die horizontale Verschiebung, um den Baum zu zentrieren.
    verschiebung_x = py5.width / 2 - ((min(xs) + max(xs)) / 2) * zoom
    # Berechnet die vertikale Verschiebung, um den Baum zu zentrieren.
    verschiebung_y = (PANEL_HOEHE + (py5.height - PANEL_HOEHE) / 2) - ((min(ys) + max(ys)) / 2) * zoom

# --- 5. HOVER (Pfad unter der Maus finden) ---

# Findet den Pfad (die Knoten-Indizes) unter der Maus.
def finde_pfad_unter_maus():
    # Wenn kein Baum da ist, die Maus im Panel ist oder der Baum zu groß ist, abbrechen.
    if not knoten_liste or ist_zu_gross or py5.mouse_y < PANEL_HOEHE:
        return None

    # Rechnet die Mausposition in Weltkoordinaten um.
    welt_x, welt_y = zu_welt(py5.mouse_x, py5.mouse_y)
    # Berechnet den Suchradius (wie nah die Maus am Knoten sein muss).
    radius_quadrat = max(knoten_radius * 1.6, 5) ** 2

    # Sucht nur in der Nähe der Maus (Performance-Optimierung).
    such_start = max(0, int(welt_x / blatt_abstand) - 10)
    # Sucht nur in der Nähe der Maus (Performance-Optimierung).
    such_ende = min(aktuelle_optionen ** aktuelle_stufen, int(welt_x / blatt_abstand) + 10)

    # Schleife durch die möglichen Blätter in der Nähe.
    for i in range(such_start, such_ende):
        # Holt das Blatt aus der Knotenliste.
        blatt = knoten_liste[ebenen_start[-1] + i]

        # Prüft, ob die Maus nah genug am Blatt ist (Satz des Pythagoras).
        if (blatt["x"] - welt_x)**2 + (blatt["y"] - welt_y)**2 <= radius_quadrat:
            # Eine leere Liste für die Schritte.
            schritte = []
            # Eine temporäre Variable für den Index.
            temp = blatt["index"]
            # Rekonstruiert die Schritte (Basis-k Zerlegung).
            for _ in range(aktuelle_stufen):
                # Fügt den aktuellen Schritt hinzu.
                schritte.append(temp % aktuelle_optionen)
                # Teilt den Index für den nächsten Schritt.
                temp //= aktuelle_optionen
            # Dreht die Reihenfolge um (von oben nach unten).
            schritte.reverse()

            # Eine Liste für die Indizes der Knoten auf dem Pfad.
            pfad_indizes = [0]
            # Die Position des aktuellen Knotens.
            position = 0
            # Berechnet die Indizes der Knoten auf dem Pfad.
            for ebene, schritt in enumerate(schritte):
                # Berechnet die Position des Kindes.
                position = position * aktuelle_optionen + schritt
                # Fügt den Index des Kindes zur Liste hinzu.
                pfad_indizes.append(ebenen_start[ebene + 1] + position)
            # Gibt die Pfad-Indizes und den Blatt-Index zurück.
            return pfad_indizes, blatt["index"]
    # Wenn nichts gefunden wurde, gib None zurück.
    return None

# --- 6. ZEICHNEN ---

# Wird einmal beim Start aufgerufen (Fenster erstellen, Baum bauen).
def setup():
    # Setzt die Fenstergröße auf 1000x780 Pixel.
    py5.size(1000, 780)
    # Aktiviert das Anti-Aliasing (glatte Kanten).
    py5.smooth()
    # Baut den ersten Baum mit 3 Stufen und 2 Optionen.
    baue_baum(3, 2)

# Wird 60-mal pro Sekunde aufgerufen (zeichnet alles neu).
def draw():
    # Füllt den Hintergrund mit der Salbeigrün-Farbe.
    py5.background(*FARBE_HINTERGRUND)
    # Wenn der Baum zu groß ist, zeigen wir einen Text an.
    if ist_zu_gross:
        # Setzt die Textfarbe auf Rot.
        py5.fill(180, 60, 60)
        # Setzt die Textgröße auf 18.
        py5.text_size(18)
        # Zentriert den Text.
        py5.text_align(py5.CENTER, py5.CENTER)
        # Zeichnet die Fehlermeldung.
        py5.text("Baum zu groß!\nMaximal 100.000 Pfade.", py5.width/2, py5.height/2)
        # Zeichnet das Panel.
        zeichne_panel()
        # Bricht die Funktion ab.
        return

    # Ruft die Funktion auf, um den Pfad unter der Maus zu finden.
    hover_data = finde_pfad_unter_maus()
    # Erstellt ein Set (Menge) mit den Pfad-Indizes, wenn es Hover-Daten gibt, sonst ein leeres Set.
    pfad_set = set(hover_data[0]) if hover_data else set()

    # Zeichnet die Verbindungslinien.
    zeichne_linien(pfad_set, hover_data)
    # Zeichnet die Knoten.
    zeichne_knoten(pfad_set)
    # Zeichnet das Panel.
    zeichne_panel()

    # Wenn es Hover-Daten gibt und nicht gerade gezogen wird, zeichne das Tooltip.
    if hover_data and not ziehe_gerade:
        # Übergibt den Blatt-Index an die Tooltip-Funktion.
        zeichne_tooltip(hover_data[1])

# Zeichnet die Verbindungslinien (Kanten) zwischen den Knoten.
def zeichne_linien(pfad_set, hover_data):
    # Schaltet die Füllung aus.
    py5.no_fill()
    # Schleife durch alle Ebenen (außer der letzten).
    for ebene in range(aktuelle_stufen):
        # Speichert den Start-Index der Eltern-Ebene.
        start_eltern = ebenen_start[ebene]
        # Speichert den Start-Index der Kinder-Ebene.
        start_kinder = ebenen_start[ebene + 1]

        # Schleife durch alle Kinder auf der nächsten Ebene.
        for kind_index in range(aktuelle_optionen ** (ebene + 1)):
            # Holt das Kind aus der Knotenliste.
            kind = knoten_liste[start_kinder + kind_index]
            # Holt das Eltern-Element aus der Knotenliste.
            eltern = knoten_liste[start_eltern + kind_index // aktuelle_optionen]

            # Rechnet die Kind-Position in Bildschirmkoordinaten um.
            kx, ky = zu_bildschirm(kind["x"], kind["y"])
            # Rechnet die Eltern-Position in Bildschirmkoordinaten um.
            ex, ey = zu_bildschirm(eltern["x"], eltern["y"])

            # Culling: Wenn die Linie außerhalb des Bildschirms ist, überspringen.
            if (kx < -50 and ex < -50) or (kx > py5.width + 50 and ex > py5.width + 50):
                continue

            # Prüft, ob diese Linie zum hervorgehobenen Pfad gehört.
            ist_highlight = hover_data is not None and (start_eltern + kind_index // aktuelle_optionen) in pfad_set and (start_kinder + kind_index) in pfad_set
            # Setzt die Linienfarbe (Orange bei Highlight, sonst Grün).
            py5.stroke(*(FARBE_HIGHLIGHT if ist_highlight else FARBE_LINIE))
            # Setzt die Liniendicke (dicker bei Highlight, skaliert mit dem Zoom).
            py5.stroke_weight(max(0.5, (3.5 if ist_highlight else 1.0) * zoom))
            # Zeichnet die Linie.
            py5.line(ex, ey, kx, ky)

# Zeichnet die Knoten (Punkte) des Baumes.
def zeichne_knoten(pfad_set):
    # Schleife durch alle Knoten.
    for i, knoten in enumerate(knoten_liste):
        # Rechnet die Knoten-Position in Bildschirmkoordinaten um.
        x, y = zu_bildschirm(knoten["x"], knoten["y"])
        # Culling: Überspringen, wenn außerhalb des Bildschirms.
        if -50 < x < py5.width + 50 and PANEL_HOEHE - 50 < y < py5.height + 50:
            # Ruft die Hilfsfunktion zum Zeichnen des Kreises auf.
            zeichne_kreis(x, y, max(knoten_radius * zoom, 1.5), knoten_farbe(knoten), i in pfad_set)

# --- 7. UI (Panel & Tooltip) ---

# Zeichnet das obere Menü-Panel mit Eingabefeldern und Button.
def zeichne_panel():
    # Schaltet die Linienzeichnung aus.
    py5.no_stroke()
    # Setzt die Füllfarbe auf die Panel-Farbe.
    py5.fill(*FARBE_PANEL)
    # Zeichnet das Panel-Rechteck.
    py5.rect(0, 0, py5.width, PANEL_HOEHE)
    # Setzt die Linienfarbe auf Grün.
    py5.stroke(*FARBE_LINIE)
    # Setzt die Liniendicke auf 1.
    py5.stroke_weight(1)
    # Zeichnet eine Trennlinie unter dem Panel.
    py5.line(0, PANEL_HOEHE, py5.width, PANEL_HOEHE)

    # Schleife durch beide Eingabefelder.
    for feld in [feld_stufen, feld_optionen]:
        # Schaltet die Linienzeichnung aus.
        py5.no_stroke()
        # Setzt die Textfarbe.
        py5.fill(*FARBE_TEXT)
        # Setzt die Textgröße.
        py5.text_size(13)
        # Richtet den Text links aus.
        py5.text_align(py5.LEFT, py5.CENTER)
        # Zeichnet das Label des Feldes.
        py5.text(feld["label"], feld["x"], feld["y"] + 14)
        # Berechnet die X-Position der Box.
        box_x = feld["x"] + 130
        # Setzt die Randfarbe (dunkel bei aktiv, sonst grün).
        py5.stroke(*(FARBE_TEXT if feld["aktiv"] else FARBE_LINIE))
        # Setzt die Liniendicke (dicker bei aktiv).
        py5.stroke_weight(2 if feld["aktiv"] else 1)
        # Setzt die Füllfarbe auf Weiß.
        py5.fill(245)
        # Zeichnet die Box.
        py5.rect(box_x, feld["y"], 40, 28, 6)
        # Schaltet die Linienzeichnung aus.
        py5.no_stroke()
        # Setzt die Textfarbe.
        py5.fill(*FARBE_TEXT)
        # Zeichnet den Text (den Wert) in die Box.
        py5.text(feld["text"], box_x + 8, feld["y"] + 14)

    # Button-Position und -Größe definieren.
    button_x, button_y, button_breite, button_hoehe = 420, 20, 130, 30
    # Prüft, ob die Maus über dem Button ist.
    maus_drauf = button_x < py5.mouse_x < button_x + button_breite and button_y < py5.mouse_y < button_y + button_hoehe
    # Setzt die Button-Farbe (dunkler bei Hover).
    py5.fill(*(130, 160, 140) if maus_drauf else (150, 180, 160))
    # Zeichnet den Button.
    py5.rect(button_x, button_y, button_breite, button_hoehe, 6)
    # Setzt die Textfarbe auf Weiß.
    py5.fill(255)
    # Setzt die Textgröße.
    py5.text_size(13)
    # Zentriert den Text.
    py5.text_align(py5.CENTER, py5.CENTER)
    # Zeichnet den Button-Text.
    py5.text("Fit to Window", button_x + button_breite/2, button_y + button_hoehe/2)

    # Setzt die Textfarbe für den Info-Text.
    py5.fill(*FARBE_TEXT)
    # Richtet den Text links aus.
    py5.text_align(py5.LEFT, py5.CENTER)
    # Berechnet die Anzahl der Pfade (oder "Zu groß").
    anzahl = aktuelle_optionen ** aktuelle_stufen if not ist_zu_gross else "Zu groß"
    # Zeichnet den Info-Text.
    py5.text("Pfade: " + str(anzahl), 420, PANEL_HOEHE / 2 + 18)

# Zeichnet das Tooltip (Infokasten) beim Hovern.
def zeichne_tooltip(blatt_index):
    # Berechnet die Wahrscheinlichkeit für diesen Pfad.
    wahrscheinlichkeit = (1.0 / aktuelle_optionen) ** aktuelle_stufen
    # Erstellt den Text für den Lösungsweg.
    rechenweg = " × ".join([str(round(1.0 / aktuelle_optionen, 2))] * aktuelle_stufen) + f" = {wahrscheinlichkeit:.4f} = {wahrscheinlichkeit*100:.2f} %"

    # Eine leere Liste für die Schritte.
    schritte = []
    # Eine temporäre Variable für den Index.
    temp = blatt_index
    # Rekonstruiert die Schritte (Basis-k Zerlegung).
    for _ in range(aktuelle_stufen):
        # Fügt den aktuellen Schritt hinzu.
        schritte.append(temp % aktuelle_optionen)
        # Teilt den Index für den nächsten Schritt.
        temp //= aktuelle_optionen
    # Dreht die Reihenfolge um.
    schritte.reverse()

    # Erstellt den Pfad-Namen (z.B. O2 -> O1 -> O2).
    namen = " → ".join(["O" + str(s + 1) for s in schritte])

    # Berechnet die Breite der Box.
    breite = max(py5.text_width(namen), py5.text_width(rechenweg), aktuelle_stufen * 20) + 40
    # Berechnet die X-Position der Box (immer in der Nähe der Maus).
    x = min(py5.mouse_x + 18, py5.width - breite - 10)
    # Berechnet die Y-Position der Box (immer in der Nähe der Maus).
    y = max(py5.mouse_y - 100, PANEL_HOEHE + 10)

    # Zeichnet den weißen Hintergrund der Box.
    py5.no_stroke()
    # Setzt die Füllfarbe auf Weiß (mit leichter Transparenz).
    py5.fill(255, 255, 255, 245)
    # Zeichnet das Rechteck.
    py5.rect(x, y, breite, 90, 8)
    # Schaltet die Füllung aus.
    py5.no_fill()
    # Setzt die Randfarbe auf Orange.
    py5.stroke(*FARBE_HIGHLIGHT)
    # Setzt die Liniendicke.
    py5.stroke_weight(2)
    # Zeichnet den Rand der Box.
    py5.rect(x, y, breite, 90, 8)

    # Schaltet die Linienzeichnung aus.
    py5.no_stroke()
    # Setzt die Textfarbe.
    py5.fill(*FARBE_TEXT)
    # Richtet den Text oben links aus.
    py5.text_align(py5.LEFT, py5.TOP)
    # Zeichnet den Pfad-Namen.
    py5.text("Pfad: " + namen, x + 12, y + 10)

    # Schleife für die farbigen Kreise.
    for i, options_index in enumerate(schritte):
        # Setzt die Farbe auf die passende Options-Farbe.
        py5.fill(*FARBEN_OPTIONEN[options_index])
        # Zeichnet den Kreis.
        py5.circle(x + 18 + i * 20, y + 41, 12)

    # Setzt die Textfarbe.
    py5.fill(*FARBE_TEXT)
    # Zeichnet den Lösungsweg.
    py5.text(rechenweg, x + 12, y + 55)

# --- 8. INTERAKTION ---

# Wird aufgerufen, wenn eine Maustaste gedrückt wird.
def mouse_pressed():
    # Macht die globalen Variablen änderbar.
    global ziehe_gerade, letzte_maus_x, letzte_maus_y

    # Prüft, ob der "Fit to Window"-Button geklickt wurde.
    if 420 < py5.mouse_x < 550 and 20 < py5.mouse_y < 50:
        # Passt den Baum ins Fenster ein.
        baum_einpassen()
        # Bricht die Funktion ab.
        return

    # Schleife durch beide Eingabefelder.
    for feld in [feld_stufen, feld_optionen]:
        # Prüft, ob in das Feld geklickt wurde.
        feld["aktiv"] = feld["x"] + 130 < py5.mouse_x < feld["x"] + 170 and feld["y"] < py5.mouse_y < feld["y"] + 28

    # Prüft, ob die rechte Maustaste (39) gedrückt wurde.
    if py5.mouse_button == 39:
        # Setzt das Zieh-Flag.
        ziehe_gerade = True
        # Speichert die aktuelle Mausposition.
        letzte_maus_x, letzte_maus_y = py5.mouse_x, py5.mouse_y

# Wird aufgerufen, wenn eine Maustaste losgelassen wird.
def mouse_released():
    # Macht die globale Variable änderbar.
    global ziehe_gerade
    # Wenn die rechte Maustaste losgelassen wurde.
    if py5.mouse_button == 39:
        # Beendet das Ziehen.
        ziehe_gerade = False

# Wird aufgerufen, wenn die Maus gezogen wird.
def mouse_dragged():
    # Macht die globalen Variablen änderbar.
    global verschiebung_x, verschiebung_y, letzte_maus_x, letzte_maus_y
    # Wenn gerade gezogen wird.
    if ziehe_gerade:
        # Verschiebt die Kamera horizontal.
        verschiebung_x += py5.mouse_x - letzte_maus_x
        # Verschiebt die Kamera vertikal.
        verschiebung_y += py5.mouse_y - letzte_maus_y
        # Aktualisiert die letzte Mausposition.
        letzte_maus_x, letzte_maus_y = py5.mouse_x, py5.mouse_y

# Wird aufgerufen, wenn eine Taste gedrückt wird.
def key_pressed():
    # Schleife durch beide Eingabefelder.
    for feld in [feld_stufen, feld_optionen]:
        # Wenn das Feld aktiv ist.
        if feld["aktiv"]:
            # Wenn die Backspace-Taste gedrückt wurde.
            if py5.key == py5.BACKSPACE:
                # Löscht das letzte Zeichen.
                feld["text"] = feld["text"][:-1]
            # Wenn die Enter-Taste gedrückt wurde.
            elif py5.key in (py5.ENTER, py5.RETURN):
                # Deaktiviert das Feld.
                feld["aktiv"] = False
                # Prüft, ob beide Felder gültige Zahlen enthalten.
                if feld_stufen["text"].isdigit() and feld_optionen["text"].isdigit():
                    # Baut den Baum mit den neuen Werten.
                    baue_baum(int(feld_stufen["text"]), int(feld_optionen["text"]))
            # Wenn eine Zifferntaste gedrückt wurde (max. 3 Zeichen).
            elif 32 <= py5.key_code <= 126 and len(feld["text"]) < 3 and chr(py5.key_code).isdigit():
                # Fügt die Ziffer hinzu.
                feld["text"] += chr(py5.key_code)

# Wird aufgerufen, wenn das Mausrad gedreht wird.
def mouse_wheel(event):
    # Macht die globalen Variablen änderbar.
    global zoom, verschiebung_x, verschiebung_y
    # Liest die Anzahl der Rasterungen (mit dem Walrus-Operator).
    if (count := event.get_count()) == 0:
        return

    # Berechnet den neuen Zoom-Faktor und begrenzt ihn.
    zoom = max(0.01, min(8.0, zoom * (1.05 ** (1 if count > 0 else -1))))
    # Rechnet die Mausposition in Weltkoordinaten um.
    welt_x, welt_y = zu_welt(py5.mouse_x, py5.mouse_y)
    # Passt die Verschiebung an, damit der Zoom um die Maus herum passiert.
    verschiebung_x, verschiebung_y = py5.mouse_x - welt_x * zoom, py5.mouse_y - welt_y * zoom

# Wird aufgerufen, wenn das Fenster in der Größe verändert wird.
def window_resized():
    # Passt den Baum an die neue Fenstergröße an.
    baum_einpassen()

# Startet das Programm.
py5.run_sketch()