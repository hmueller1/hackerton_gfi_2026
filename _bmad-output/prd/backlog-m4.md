# Backlog M4 — Integration & Dual-View Verifikations-UX

**Meilenstein:** M4 — Next.js ↔ FastAPI vollständig integriert; Dual-View Verifikations-UX lauffähig
**Release:** Vollständig
**Datum:** 2026-02-24
**Voraussetzung:** M2 (KI-Konfig-Generierung) + M3 (Frontend-Grundstruktur) abgeschlossen
**Ziel:** Der menschliche Verifikationsschritt für KI-generierte Konfigs ist vollständig im Browser abbildbar — Result-First Dual-View, Inline-Editor, Dry-Run-Retry, Bestätigen-Gate. End-to-End-Lauf von PDF bis freigegebenem JSON ohne Terminal.

---

## Definition of Done (M4)

- [ ] Pending-Konfigs erscheinen im Dashboard unter "Zur Review"
- [ ] Dual-View zeigt Extraktions-Vorschau (primär) + YAML-Konfig (sekundär) nebeneinander
- [ ] YAML-Konfig ist direkt im Browser editierbar; Änderungen triggern neuen Dry-Run in < 5s
- [ ] "Bestätigen"-Button speichert Konfig dauerhaft; kein Bypass ohne explizite Aktion
- [ ] "Ablehnen"-Button verwirft Konfig; PDF landet in `/fehler/`
- [ ] Konfidenz-Score und Begründung sind in der Dual-View sichtbar
- [ ] Vollständiger End-to-End-Lauf (PDF → KI-Konfig → Dual-View → Bestätigung → JSON) im Browser möglich

---

## Epics

| Epic | Beschreibung | Stories |
|------|-------------|---------|
| E16 | Dual-View Verifikations-UI | M4-01 bis M4-04 |
| E17 | Inline-Editor & Dry-Run-Retry | M4-05 bis M4-06 |
| E18 | Bestätigen-Gate & Konfig-Freigabe | M4-07 bis M4-08 |
| E19 | End-to-End-Integration & Test | M4-09 bis M4-10 |

---

## E16 — Dual-View Verifikations-UI

---

### M4-01 · Pending-Konfig-Eintrag im Dashboard hervorheben

**Als** Datenkoordinator
**möchte ich**, dass Berufe mit Status "Zur Review" im Dashboard klar hervorgehoben werden,
**damit** ich sofort erkenne, welche Berufe meinen Verifikationsschritt benötigen.

**Akzeptanzkriterien:**
- [ ] Berufe mit Status `ZUR_REVIEW` erhalten eigene Sektion im Dashboard: "Zur Review (N)"
- [ ] Jeder Eintrag zeigt: Berufname, KI-Konfidenz-Score (Prozent + Farbskala), Begründung (Kurzform), Datum
- [ ] Score-Farbskala: < 70% rot, 70–84% orange, ≥ 85% grün
- [ ] "Prüfen"-Button pro Eintrag → navigiert zur Dual-View `/konfig/{beruf}/verify`
- [ ] Badge im Navigationsmenü zeigt Anzahl offener Reviews

**Priorität:** Must Have | **Aufwand:** S

---

### M4-02 · Dual-View Grundlayout: Vorschau links, YAML rechts

**Als** Datenkoordinator
**möchte ich** die extrahierten Daten (links) und die zugrundeliegende YAML-Konfig (rechts) nebeneinander sehen,
**damit** ich Datenfehler sofort im Ergebnis erkennen kann, ohne die Konfig interpretieren zu müssen.

**Akzeptanzkriterien:**
- [ ] `/konfig/{beruf}/verify`-Seite ist zweispaltig: 60% Vorschau (links), 40% Editor (rechts)
- [ ] Linke Spalte: strukturierte Datenvorschau (identisch mit Beruf-Einzelansicht aus M3-08)
- [ ] Rechte Spalte: YAML-Konfig als Code-Anzeige (read-only in dieser Story, editierbar in M4-05)
- [ ] Header zeigt: Berufname, Score-Badge, Begründung, Datum der KI-Generierung
- [ ] Auf schmalen Bildschirmen: Tab-basiertes Layout ("Vorschau" / "Konfig")
- [ ] Ladestate: Skeleton-UI während Daten geladen werden

**Priorität:** Must Have | **Aufwand:** M

---

### M4-03 · Konfidenz-Score und unsichere Felder hervorheben

**Als** Datenkoordinator
**möchte ich** im Dual-View sehen, welche spezifischen Felder die KI als unsicher markiert hat,
**damit** ich meine Prüfaufmerksamkeit gezielt auf die kritischen Stellen lenken kann.

**Akzeptanzkriterien:**
- [ ] `konfidenz.unsichereFelder[]` werden in der YAML-Ansicht farblich markiert (gelber Hintergrund)
- [ ] Tooltip an markierten Feldern: "KI unsicher — bitte prüfen"
- [ ] Entsprechende Datenwerte in der linken Vorschau ebenfalls markiert (gelber Rahmen)
- [ ] Info-Banner unter dem Header: "3 Felder zur Prüfung: tabellenMapping[1].transponiert, ..."

**Priorität:** Must Have | **Aufwand:** M

---

### M4-04 · Dry-Run Vorschau beim ersten Öffnen der Dual-View

**Als** Datenkoordinator
**möchte ich**, dass beim Öffnen der Dual-View bereits ein Extraktionsergebnis vorliegt,
**damit** ich sofort beurteilen kann, was die aktuelle Konfig liefern würde.

**Akzeptanzkriterien:**
- [ ] Beim Laden wird automatisch `POST /api/konfig/{beruf}/dry-run` aufgerufen
- [ ] Ergebnis: vollständige JSON-Vorschau oder Fehlerhinweis (V1/V2-Fehler mit Details)
- [ ] V1/V2-Fehler werden prominent angezeigt (roter Banner mit Fehlerbeschreibung)
- [ ] Dry-Run-Dauer wird angezeigt: "Vorschau generiert in 0.8s"
- [ ] Fehlerfreier Dry-Run: grüner Banner "V1 ✓ | V2 ✓ — Daten sehen korrekt aus"

**FastAPI-Endpoint (Referenz):**
```python
@router.post("/konfig/{beruf}/dry-run")
async def dry_run(beruf: str, konfig_override: dict | None = None):
    konfig = konfig_override or load_pending_config(beruf)
    raw_tables = extract_tables(get_pdf_path(beruf))
    result_json = apply_config(raw_tables, konfig)
    v1_ok, v1_msg = validate_schema(result_json)
    v2_ok, v2_msg = validate_consistency(result_json)
    return {
        "vorschau": result_json,
        "validierung": {
            "v1": {"ok": v1_ok, "meldung": v1_msg},
            "v2": {"ok": v2_ok, "meldung": v2_msg}
        },
        "dauerMs": ...
    }
```

**Priorität:** Must Have | **Aufwand:** M

---

## E17 — Inline-Editor & Dry-Run-Retry

---

### M4-05 · YAML-Konfig direkt im Browser editieren

**Als** Datenkoordinator
**möchte ich** die YAML-Konfig direkt in der rechten Spalte bearbeiten können,
**damit** ich Korrekturen ohne externen Editor vornehmen kann.

**Akzeptanzkriterien:**
- [ ] Rechte Spalte wechselt in Edit-Modus per "Bearbeiten"-Button
- [ ] Code-Editor mit YAML-Syntax-Highlighting (Monaco Editor oder CodeMirror)
- [ ] Syntaxfehler werden inline angezeigt (rote Unterwellung, Fehlermeldung in Tooltip)
- [ ] "Änderungen verwerfen"-Button stellt ursprüngliche KI-Konfig wieder her
- [ ] Ungespeicherte Änderungen durch visuellen Indikator markiert ("● Ungespeichert")
- [ ] Tastaturkürzel: `Ctrl+Z` Undo, `Ctrl+Shift+Z` Redo

**Priorität:** Must Have | **Aufwand:** L

---

### M4-06 · Dry-Run bei YAML-Änderung neu starten

**Als** Datenkoordinator
**möchte ich** nach einer Konfig-Änderung per Klick einen neuen Dry-Run starten können,
**damit** ich das aktualisierte Extraktionsergebnis sofort sehe.

**Akzeptanzkriterien:**
- [ ] "Neu testen"-Button erscheint sobald der YAML-Editor Änderungen enthält
- [ ] Klick auf "Neu testen": aktuelle YAML wird an `POST /api/konfig/{beruf}/dry-run` mit Body gesendet
- [ ] Vorschau-Bereich aktualisiert sich; alter Inhalt wird während Ladezeit durch Skeleton ersetzt
- [ ] Dry-Run-Dauer < 5 Sekunden (Backend-Performance-Anforderung)
- [ ] Syntaxfehler im YAML → "Neu testen" deaktiviert; Hinweis "YAML-Syntax ungültig"

**Priorität:** Must Have | **Aufwand:** M

---

## E18 — Bestätigen-Gate & Konfig-Freigabe

---

### M4-07 · Konfig bestätigen und Beruf vollständig verarbeiten

**Als** Datenkoordinator
**möchte ich** eine geprüfte Konfig explizit bestätigen müssen,
**damit** keine ungeprüfte KI-Konfig produktiv geht.

**Akzeptanzkriterien:**
- [ ] "Bestätigen & Verarbeiten"-Button ist nur aktiv wenn letzter Dry-Run V1+V2 bestanden hat
- [ ] Klick öffnet Bestätigungs-Dialog: "Konfig für {Beruf} freigeben und JSON erzeugen?" [Bestätigen] [Abbrechen]
- [ ] Nach Bestätigung: `POST /api/konfig/{beruf}/approve` → Konfig von `/pending/` nach `/konfig/` verschoben, Pipeline-Einzellauf gestartet
- [ ] Erfolg: Toast "Beruf {name} erfolgreich verarbeitet ✓", Redirect zum Dashboard
- [ ] Fehler: Fehler-Banner, kein Redirect

**Priorität:** Must Have | **Aufwand:** M

---

### M4-08 · Konfig ablehnen und Beruf in Fehler verschieben

**Als** Datenkoordinator
**möchte ich** eine Konfig explizit ablehnen können,
**damit** ich eine nicht korrigierbare Konfig sauber aus dem Review-Prozess entfernen kann.

**Akzeptanzkriterien:**
- [ ] "Ablehnen"-Button (destruktiv gestylt) immer sichtbar in Dual-View
- [ ] Klick öffnet Bestätigungs-Dialog mit Pflicht-Textfeld: "Grund für Ablehnung (Pflicht)"
- [ ] Nach Ablehnung: `POST /api/konfig/{beruf}/reject` → Konfig gelöscht, PDF → `/fehler/` mit Typ `KONFIG_ABGELEHNT`
- [ ] Toast: "Konfig abgelehnt — {Beruf} in /fehler/ verschoben"
- [ ] Redirect zum Dashboard; Beruf erscheint in Fehler-Liste

**Priorität:** Must Have | **Aufwand:** S

---

## E19 — End-to-End-Integration & Test

---

### M4-09 · FastAPI-Endpoints für Dual-View implementieren

**Als** Entwickler
**möchte ich** alle für den Verifikationsschritt benötigten FastAPI-Endpoints implementieren,
**damit** das Next.js-Frontend vollständig angebunden ist.

**Akzeptanzkriterien:**
- [ ] Alle Endpoints implementiert und geben typisiertes JSON zurück
- [ ] OpenAPI-Spec automatisch via FastAPI `/docs` verfügbar
- [ ] Fehler-Responses einheitlich: `{"fehler": "Beschreibung", "typ": "FEHLER_TYP"}`
- [ ] Alle Endpoints haben Integrationstests (pytest, Happy Path + 1 Fehlerfall)

**Endpoints für M4:**

| Endpoint | Methode | Beschreibung |
|---|---|---|
| `/konfig/pending` | GET | Liste aller Pending-Konfigs |
| `/konfig/{beruf}/pending` | GET | Einzelne Pending-Konfig (YAML + Score + Begründung) |
| `/konfig/{beruf}/dry-run` | POST | Dry-Run mit optionalem YAML-Body |
| `/konfig/{beruf}/approve` | POST | Konfig freigeben, Einzellauf starten |
| `/konfig/{beruf}/reject` | POST | Konfig ablehnen, PDF → /fehler/ |

**Priorität:** Must Have | **Aufwand:** L

---

### M4-10 · End-to-End-Smoke-Test: PDF → Dual-View → JSON

**Als** Entwickler
**möchte ich** einen vollständigen End-to-End-Lauf im Browser durchführen können,
**damit** ich sicher bin, dass alle Komponenten korrekt zusammenspielen.

**Akzeptanzkriterien:**
- [ ] Test-PDF eines unbekannten Berufs in `/eingang/` ablegen
- [ ] Pipeline per UI starten → Beruf erscheint als "Zur Review"
- [ ] Dual-View öffnen → Vorschau korrekt, Score sichtbar, unsichere Felder markiert
- [ ] YAML editieren → Dry-Run neu starten → aktualisierte Vorschau erscheint
- [ ] "Bestätigen" klicken → JSON in `/ausgabe/` erzeugt, Beruf im Dashboard als "Verarbeitet ✓"
- [ ] Gesamtdauer (ohne KI-API-Zeit) < 10 Sekunden

**Priorität:** Must Have | **Aufwand:** M

---

## Story-Übersicht M4

| ID | Titel | Epic | Priorität | Aufwand | PRD-Ref |
|----|-------|------|-----------|---------|---------|
| M4-01 | Pending-Konfig im Dashboard hervorheben | E16 | Must Have | S | F-30, F-13 |
| M4-02 | Dual-View Grundlayout | E16 | Must Have | M | F-17 |
| M4-03 | Konfidenz-Score und unsichere Felder hervorheben | E16 | Must Have | M | F-13, F-17 |
| M4-04 | Dry-Run Vorschau beim Öffnen | E16 | Must Have | M | F-17 |
| M4-05 | YAML-Konfig im Browser editieren | E17 | Must Have | L | F-18 |
| M4-06 | Dry-Run bei YAML-Änderung neu starten | E17 | Must Have | M | F-18 |
| M4-07 | Konfig bestätigen und Beruf verarbeiten | E18 | Must Have | M | F-19 |
| M4-08 | Konfig ablehnen und Beruf in Fehler | E18 | Must Have | S | F-19 |
| M4-09 | FastAPI-Endpoints für Dual-View | E19 | Must Have | L | F-17–F-19 |
| M4-10 | End-to-End-Smoke-Test | E19 | Must Have | M | — |

**Gesamtaufwand M4:** 10 Must Have Stories (kompaktester Meilenstein — alles Pflicht)

---

## Abhängigkeiten

| M4-Story | Benötigt |
|----------|----------|
| M4-01 | M2-09 (ZUR_REVIEW-Status), M3-04 (Dashboard) |
| M4-02 bis M4-04 | M3-03 (API-Client), M2-08 (Score im Backend) |
| M4-05 bis M4-06 | M4-02 (Dual-View Grundlayout) |
| M4-07 bis M4-08 | M4-06 (Dry-Run-Retry), M4-09 (Endpoints) |
| M4-10 | Alle M4-Stories abgeschlossen |

---

## Empfohlene Implementierungsreihenfolge

```
Phase 1 — Backend-Endpoints zuerst (E19)
  M4-09   ← ermöglicht paralleles Frontend-Entwickeln

Phase 2 — Dual-View Grundstruktur (E16)
  M4-01 → M4-02 → M4-03 → M4-04

Phase 3 — Interaktivität (E17)
  M4-05 → M4-06

Phase 4 — Gate-Logik (E18)
  M4-07 → M4-08

Phase 5 — Integration & Test (E19)
  M4-10   ← erst wenn alle anderen Stories abgeschlossen
```

---

## Test-Szenarien M4

| Szenario | Erwartetes Ergebnis |
|----------|---------------------|
| Dashboard mit 2 Pending-Konfigs | Eigene Sektion "Zur Review" mit 2 Einträgen |
| Dual-View für Beruf mit Score 72% | Score-Badge orange, unsichere Felder gelb markiert |
| Dual-View lädt — Dry-Run V2-Fehler | Roter Banner mit Fehlerbeschreibung |
| YAML editieren, Syntaxfehler einbauen | "Neu testen" deaktiviert, rote Unterwellung |
| YAML korrigieren, "Neu testen" klicken | Neue Vorschau in < 5s, V1+V2 grün |
| "Bestätigen" ohne vorherigen Dry-Run | Button bleibt deaktiviert |
| "Bestätigen" nach erfolgreichem Dry-Run | Dialog öffnet, nach Klick JSON erzeugt |
| "Ablehnen" ohne Grund-Text | Bestätigungs-Button im Dialog deaktiviert |
| "Ablehnen" mit Grund | Beruf in Fehler-Liste mit eingetragenem Grund |
