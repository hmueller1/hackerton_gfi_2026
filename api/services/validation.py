"""M1-10 + M1-11: Validierungs-Gates V1 (Schema) und V2 (Numerische Konsistenz)."""
import logging

from jsonschema import validate, ValidationError

logger = logging.getLogger(__name__)

TOLERANZ = 1.0  # ±1% für Rundungsfehler

# ─────────────────────────────────────────────
# V1 — JSON-Schema-Gate
# ─────────────────────────────────────────────

_PFLICHT_SCHEMA = {
    "type": "object",
    "required": ["berufNr", "beschreibung", "prüfungsTyp", "prüfungsbereiche"],
    "properties": {
        "berufNr":          {"type": "array", "minItems": 1, "items": {"type": "string"}},
        "beschreibung":     {"type": "string", "minLength": 1},
        "prüfungsTyp":      {"type": "string", "minLength": 1},
        "prüfungsbereiche": {"type": "array",  "minItems": 1},
    },
}


def validate_schema(data: dict) -> tuple[bool, str | None]:
    """
    V1: Strukturelle Validierung gegen das Pflicht-Schema.

    Returns:
        (True, None) bei Erfolg
        (False, fehlermeldung) bei Fehler
    """
    try:
        validate(instance=data, schema=_PFLICHT_SCHEMA)
    except ValidationError as exc:
        return False, f"V1-Fehler: {exc.message} (Pfad: {list(exc.absolute_path)})"

    bereiche = data.get("prüfungsbereiche", [])
    typen = [b.get("typ", "") for b in bereiche]

    if "schriftlich" not in typen:
        return False, "V1-Fehler: Kein Prüfungsbereich mit typ='schriftlich' gefunden."
    if "praktisch" not in typen:
        return False, "V1-Fehler: Kein Prüfungsbereich mit typ='praktisch' gefunden."

    return True, None


# ─────────────────────────────────────────────
# V2 — Numerische Konsistenz-Check
# ─────────────────────────────────────────────

def validate_consistency(data: dict) -> tuple[bool, str | None]:
    """
    V2: Prüft numerische Plausibilität.
    - Gewichtungen pro Ebene summieren auf 100% (±TOLERANZ)
    - Zeitangaben im Bereich 1–1440 Minuten
    - BerufNr numerisch und positiv

    Returns:
        (True, None) bei Erfolg
        (False, fehlermeldung) bei erstem Fehler
    """
    bereiche = data.get("prüfungsbereiche", [])

    # BerufNr prüfen
    for nr in data.get("berufNr", []):
        try:
            val = int(nr)
            if val <= 0:
                return False, f"V2-Fehler: BerufNr '{nr}' ist nicht positiv."
        except (ValueError, TypeError):
            return False, f"V2-Fehler: BerufNr '{nr}' ist nicht numerisch."

    # Gewichtungen pro Ebene sammeln und prüfen.
    # imPrüfungsbereich: liegt auf Aufgaben-Ebene, nicht auf Bereich-Ebene → kein globaler Check.
    # gesamtergebnis: praktischer Bereich hat oft None → nur prüfen wenn alle Bereiche einen Wert haben.
    ebenen = ["schriftlichePrüfung", "teil2", "gesamtergebnis"]
    for ebene in ebenen:
        werte = []
        alle_gesetzt = True
        for b in bereiche:
            gew = b.get("gewichtung", {})
            val = gew.get(ebene) if isinstance(gew, dict) else None
            if val is not None:
                werte.append(val)
            else:
                alle_gesetzt = False

        # gesamtergebnis nur prüfen wenn ALLE Bereiche einen Wert haben
        if ebene == "gesamtergebnis" and not alle_gesetzt:
            continue

        if len(werte) > 1:  # nur prüfen wenn mehrere Werte für diese Ebene existieren
            summe = sum(werte)
            if not (100 - TOLERANZ <= summe <= 100 + TOLERANZ):
                return False, (
                    f"V2-Fehler: Gewichtungsebene '{ebene}': "
                    f"Summe={summe:.1f}% aus {werte} (erwartet: 100±{TOLERANZ}%)"
                )

    # Zeitangaben prüfen
    for b in bereiche:
        for aufgabe in b.get("aufgaben", []):
            zeit = aufgabe.get("zeitMinuten")
            if zeit is not None:
                if not (1 <= zeit <= 1440):
                    return False, (
                        f"V2-Fehler: Zeitangabe '{aufgabe.get('bezeichnung', '?')}': "
                        f"{zeit} Min (erwartet: 1–1440)"
                    )

        # Varianten ebenfalls prüfen
        for variante in (b.get("varianten") or []):
            for aufgabe in variante.get("aufgaben", []):
                zeit = aufgabe.get("zeitMinuten")
                if zeit is not None and not (1 <= zeit <= 1440):
                    return False, (
                        f"V2-Fehler: Zeitangabe in Variante '{variante.get('bezeichnung', '?')}': "
                        f"{zeit} Min (erwartet: 1–1440)"
                    )

    return True, None
