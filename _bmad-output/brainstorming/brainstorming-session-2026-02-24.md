---
stepsCompleted: [1, 2]
inputDocuments: []
session_topic: 'KI-gestützte Datenextraktions-Pipeline für heterogene Berufsprüfungs-PDFs mit einheitlichem Ausgabeformat und Validierung'
session_goals: 'Workflow & Pipeline-Architektur definieren, Tooling-Ansätze (AI + klassisch) erarbeiten, Halluzinations-Validierungsstrategie entwickeln'
selected_approach: 'ai-recommended'
techniques_used: ['Morphological Analysis', 'Cross-Pollination', 'Chaos Engineering']
ideas_generated: []
context_file: ''
---

# Brainstorming Session Results

**Facilitator:** Jonathan
**Date:** 2026-02-24

## Session Overview

**Thema:** KI-gestützte Datenextraktions-Pipeline für heterogene Berufsprüfungs-PDFs mit einheitlichem Ausgabeformat und Validierung gegen Ursprungsdaten
**Ziele:** Pipeline-Architektur (primär), Halluzinations-Validierung (sekundär), Tooling-Ideen (AI + klassisch)

### Session Setup

_Frische Session ohne Vorkenntnisse aus dem Projekt. Der Fokus liegt auf dem Workflow-Design und der Datenintegrität als höchster Priorität._

## Techniken-Auswahl

**Ansatz:** KI-Empfehlung
**Analyse-Kontext:** Heterogene PDFs → einheitliches Schema + KI-Extraktionspipeline + Validierung

**Empfohlene Techniken:**

- **Morphological Analysis:** Systematische Exploration aller Pipeline-Dimensionen als Fundament — kein Parameter bleibt unbeachtet
- **Cross-Pollination:** Lösungen aus ETL, Medizindokumentation, Gerichtsarchivierung übertragen — explizit für Tooling-Ideen jenseits von reinem AI-Einsatz
- **Chaos Engineering:** Systematisches "Kaputtmachen" der Pipeline zur Ableitung von Validierungsregeln und Anti-Halluzinations-Gates

**KI-Rationale:** Die Kombination deckt alle drei Zieldimensionen ab: strukturierte Architektur (Phase 1), Domain-Transfer für Tooling-Ideen (Phase 2), Robustheit durch Failure-First-Denken (Phase 3).

---

## Technik 1: Morphological Analysis — Ergebnisse

### Dimension 1 — Eingabe & Trigger

**[Eingabe #1]:** Watched Folder mit manuellem CLI-Trigger
_Concept:_ Kein dauerlaufender File-Watcher nötig — ein Skript/CLI-Befehl startet die Pipeline einmalig über den Eingabe-Ordner (z.B. `python run_pipeline.py --input ./eingang`). Passend für einen 1x/Jahr-Prozess.
_Novelty:_ Für seltene Batch-Prozesse ist ein dauerlaufender Watcher Over-Engineering. Einfachheit schlägt Automatisierung.

**[Eingabe #2]:** Fehler-Subfolder
_Concept:_ PDFs, die nicht verarbeitet werden konnten, landen automatisch in einem `/fehler/`-Ordner — sichtbar, ohne Datenverlust, ohne die Pipeline zu blockieren.
_Novelty:_ Transparente Fehlerbehandlung ohne Datenverlust im Ursprungsbestand.

**[Eingabe #3]:** Archiv-Subfolder
_Concept:_ Erfolgreich verarbeitete Original-PDFs werden unverändert in `/archiv/` verschoben. Die Ursprungsdaten bleiben immer erhalten und sind nie modifiziert.
_Novelty:_ Unveränderlichkeit der Quelldaten als architektonisches Prinzip, nicht als Konvention.

**[Eingabe #4]:** Unterordner als Semantik
_Concept:_ Der Ordnerpfad kodiert Metadaten (z.B. `/eingang/2026/elektrotechnik/`) — Beruf und Jahr werden aus dem Pfad abgeleitet, bevor das PDF analysiert wird.
_Novelty:_ Reduziert KI-Inferenzlast: je mehr Kontext aus der Struktur kommt, desto weniger muss erraten werden.

---

### Dimension 2 — PDF Parsing

**[Parsing #1]:** Klassisches Tabellen-Tooling (pdfplumber / Camelot)
_Concept:_ Da alle PDFs saubere Text-PDFs (kein Scan) sind, reicht klassisches Tooling vollständig. `pdfplumber` liefert zusätzlich Koordinaten und Bounding-Boxes — wichtig für die Mehrtabellen-Erkennung.
_Novelty:_ Keine KI im Parsing-Schritt → deterministische, reproduzierbare Rohextraktion. Fehler sind nachvollziehbar.

**[Parsing #2]:** Mehrtabellen-Erkennung via Bounding-Box-Analyse
_Concept:_ Pro Seite können eine oder zwei Tabellen vorkommen. pdfplumber liefert die Y-Koordinaten aller Tabellen — so lässt sich programmatisch erkennen: "Auf dieser Seite befinden sich 2 Tabellen, Tabelle 1 endet bei Y=400, Tabelle 2 beginnt bei Y=450."
_Novelty:_ Die Mehrtabellen-Problematik wird geometrisch gelöst, nicht semantisch erschlossen.

---

### Dimension 3 — Tabellen-Normalisierung

**[Normalisierung #1]:** Configure-Once, Run-Forever Pattern
_Concept:_ KI analysiert ein PDF einmalig und generiert eine Mapping-Konfig (YAML): "Tabelle 1 = Schriftlich, Spalte 2 = Gewichtung, Zeilen transponiert: ja". User prüft und bestätigt — danach ist diese Konfig deterministisch und fix für alle Folgejahre.
_Novelty:_ Das KI-Halluzinationsrisiko wird auf einen einmaligen, menschlich verifizierten Schritt reduziert. Der Jahres-Pipeline-Lauf läuft danach vollständig regelbasiert — kein LLM im kritischen Pfad.

**[Normalisierung #2]:** Konfig-Versionierung pro Beruf
_Concept:_ Jeder Beruf bekommt eine eigene Konfig-Datei (`elektrotechnik.yaml`, `kaufmann-bueromanagement.yaml`). Neue Berufe = neue Datei. Bekannte Berufe = keine KI-Beteiligung mehr.
_Novelty:_ Das System wird mit der Zeit stabiler, nicht fragiler. Die Konfig-Bibliothek ist das akkumulierte Wissen des Systems.

---

### Dimension 4 — Konfig-Generierung & Verifikations-UX

**[Verifikation #1]:** Result-First Dual-View
_Concept:_ Der Verifikations-Schritt zeigt primär die extrahierten Daten als strukturierte Vorschau (Tabelle/JSON), sekundär die zugrundeliegenden Regeln — aufklappbar oder daneben. User validiert am Ergebnis, nicht an der Abstraktion.
_Novelty:_ Menschen erkennen Datenfehler sofort im Ergebnis ("Gewichtung in falscher Spalte"), aber selten in abstraktem YAML.

**[Verifikation #2]:** Dry-Run Preview mit Konfig-Anzeige
_Concept:_ Die generierte Konfig wird sofort gegen das echte PDF ausgeführt und das Ergebnis als Vorschau angezeigt. User sieht gleichzeitig: "Das käme raus" (primär) + "Das sind die Regeln" (sekundär).
_Novelty:_ Ein Blick reicht zur Verifikation — kein Kontextwechsel zwischen Daten und Regeln nötig.

---

### Dimension 5 — Skalierungsstrategie (100–300 Berufe)

**[Skalierung #1]:** Format-Clustering vor Konfig-Generierung
_Concept:_ Bevor für jeden Beruf eine Konfig generiert wird, clustert die KI alle PDFs nach Struktur-Ähnlichkeit. Vermutlich gibt es nur 5–15 verschiedene Tabellen-Layouts über alle 300 Berufe — dann braucht es nur 15 Templates, nicht 300 individuelle Konfigs.
_Novelty:_ Skalierungslast wächst mit Anzahl der Layout-Typen, nicht mit Anzahl der Berufe.

**[Skalierung #2]:** Confidence-Triage mit expliziter KI-Unsicherheit
_Concept:_ Die KI gibt bei jeder Konfig-Generierung einen Konfidenz-Score + Begründung aus: "Ich bin 87% sicher — Spalte 3 könnte Gewichtung oder Punktzahl bedeuten, bitte prüfen." Unter Schwellwert (z.B. 85%) → automatisch zur manuellen Review geflaggt.
_Novelty:_ Die KI kommuniziert ihre eigene Unsicherheit mit Begründung — nicht nur ein Score. Gibt dem Prüfer den richtigen Fokuspunkt.

**[Skalierung #3]:** Layout-Typ-Bibliothek mit Sample-Validation
_Concept:_ Pro Layout-Typ wird nur ein repräsentatives Sample (z.B. 3 Berufe) manuell validiert. Alle anderen Berufe des gleichen Typs erben die Validierung. Neue unbekannte Typen werden automatisch isoliert.
_Novelty:_ 300 Berufe → ggf. nur 15–30 manuelle Prüfungen. Validierungsaufwand skaliert mit Layout-Komplexität, nicht mit Berufszahl.

---

### Dimension 6 — Ziel-Schema (JSON)

**[Schema #1]:** `berufNr` immer als Array
_Concept:_ Aus echten PDFs beobachtet: Anlagenmechaniker hat 6 Nummern `[4010–4015]`, ELAM hat `[1040]`, IM hat 5 Nummern. Das Schema muss immer ein Array erwarten.
_Novelty:_ Keine Sonderbehandlung für Einzel- vs. Mehrfachnummern nötig.

**[Schema #2]:** Explizites `prüfungsTyp`-Feld
_Concept:_ PDFs unterscheiden sich strukturell nach Prüfungsregime: "Abschlussprüfung Teil 2" (4 Gewichtungs-Ebenen) vs. eigenständiger Abschluss (2 Gewichtungs-Ebenen). Dieses Feld ist gleichzeitig Layout-Typ-Indikator.
_Novelty:_ Ein Feld, das sowohl semantische Information trägt als auch die Konfig-Auswahl steuert.

**[Schema #3]:** Flexible `gewichtung`-Struktur mit Null-Werten
_Concept:_ Manche Berufe haben 4 Gewichtungs-Ebenen (im Prüfungsbereich, schriftliche Prüfung, Teil 2, Gesamtergebnis), andere nur 2 (innerhalb Fach, Ergebnis). Nicht vorhandene Ebenen werden als `null` gespeichert, nicht weggelassen.
_Novelty:_ Schema-Konsistenz über alle Berufe trotz struktureller Unterschiede.

**[Schema #4]:** ODER-Varianten in der praktischen Prüfung als `varianten[]`-Array
_Concept:_ Berufe wie Anlagenmechaniker haben zwei alternative praktische Prüfungsformen ("Praktische Aufgabe ODER Betrieblicher Auftrag"). Beide Varianten werden vollständig im JSON gespeichert — kein Datenverlust in der Ersterfassung.
_Novelty:_ Das Schema ist verlustfreie Quelle der Wahrheit. Reduktion passiert downstream (HTML-Ansicht), nie im JSON selbst.

**[Schema #5]:** Sub-Aufgaben per `aufgaben[]`-Array pro Prüfungsbereich
_Concept:_ Ein Prüfungsbereich (z.B. WISO) kann mehrere Aufgabenzeilen haben (18 geb. Aufg. + 6 ungeb. Aufg.). Das `aufgaben[]`-Array pro Prüfungsbereich bildet das korrekt ab.
_Novelty:_ Keine künstliche Verdoppelung von Prüfungsbereichen — Sub-Aufgaben bleiben ihrem Elternelement zugeordnet.

**Beobachtete Layout-Typen aus echten PDFs (Stichprobe):**
- **Typ A:** Anlagenmechaniker, Industriemechaniker — "Abschlussprüfung Teil 2", 4 Gewichtungs-Ebenen, Phasen-basierte Praktische Prüfung, ODER-Varianten
- **Typ B:** Elektroanlagenmonteur — eigenständiger Abschluss, 2 Gewichtungs-Ebenen, Prüfungsstück + Arbeitsproben-Struktur

---

### Dimension 7 — Validierung gegen Ursprungsdaten

**[Validierung #1]:** V1 — JSON-Schema-Gate (Pflicht, deterministisch)
_Concept:_ Vor dem Speichern wird gegen ein definiertes JSON-Schema validiert: Pflichtfelder vorhanden (`berufNr`, `beschreibung`, min. 1 schriftlicher Bereich, min. 1 praktischer Bereich), Datentypen korrekt, Arrays nicht leer. Fehler → Beruf in `/fehler/`, kein Output.
_Novelty:_ Zero-Tolerance-Gate. Kein LLM, kein Rauschen, null Fehlertoleranz bei Strukturverletzungen.

**[Validierung #2]:** V2 — Numerische Konsistenz-Checks (Pflicht, deterministisch)
_Concept:_ Gewichtungen pro Prüfungsbereich summieren auf 100% (±1% Toleranz für Rundungsfehler). Zeitangaben > 0 und < 24h. BerufNr numerisch und positiv. Direkt aus den echten PDFs ableitbar: WISO 40%+60%=100% ✓, AFA 50%+50%=100% ✓.
_Novelty:_ Mathematische KI-Fehler werden deterministisch gefangen — unabhängig davon, wie überzeugend der extrahierte Text klingt.

**[Validierung #3]:** V3 — LLM Textuelle Rückverifikation (optional)
_Concept:_ Das LLM bekommt Original-PDF-Rohtext + extrahiertes JSON. Aufgabe: "Findest du im JSON einen Wert, der im PDF nicht vorkommt?" — engerer, überprüfbarer Prompt statt vagem "Ist das korrekt?".
_Novelty:_ Targeted-Diff-Prompt statt offener Validierungsfrage reduziert Halluzinationsrisiko der Verifikation selbst.

**[Validierung #4]:** V4 — Diff-Report als Audit-Trail (optional)
_Concept:_ Jeder Lauf erzeugt einen `validation-report-{beruf}.json`: welche Felder geprüft, welche Regeln bestanden/gefailed, ob KI-Verifikation lief und was sie fand. Persistent gespeichert neben dem JSON.
_Novelty:_ Vollständige Nachvollziehbarkeit jedes Extraktionslaufs — wichtig für Jahresvergleiche und Audit-Anforderungen.

---

---

### Dimension 8 — Tech-Stack (Architektur-Entscheidung)

**[Stack #1]:** Hybrid-Architektur Next.js + Python
_Concept:_ Next.js übernimmt Frontend (React-Anzeige, JSON-Verwaltung, Konfig-Verifikations-UX, HTML-Export) und API-Orchestrierung. Ein Python-Microservice (FastAPI) übernimmt ausschließlich die PDF-Tabellenextraktion (pdfplumber/Camelot) und V1+V2-Validierung. Next.js API Routes rufen den Python-Service per HTTP auf.
_Novelty:_ Maximale Tabellenqualität (Python) ohne Verzicht auf ein vollwertiges Frontend (Next.js). Klare Trennung: Python = Datenqualität, Next.js = Nutzererlebnis.

**Begründung:** JS-Ökosystem hat kein Äquivalent zu pdfplumber für Bounding-Box-basierte Mehrtabellen-Erkennung. Tabellenqualität hat höhere Priorität als Stack-Einheitlichkeit.

**Verantwortlichkeiten:**
- **Next.js:** UI/Frontend, Konfig-Management, Result-First Dual-View Verifikation, JSON-Anzeige, HTML-Export, Pipeline-Orchestrierung
- **Python (FastAPI):** PDF-Parsing, Tabellen-Extraktion, Layout-Typ-Erkennung, V1+V2-Validierung, Konfig-Generierung (KI-gestützt)

---

## Offene Dimensionen (noch nicht bearbeitet)

- **Ordnerstruktur der Outputs:** Wo leben generierte JSONs, Konfigs, Validation-Reports
- **Chaos Engineering:** Systematische Worst-Case-Analyse (fehlerhafte PDFs, 3 Tabellen pro Seite, fehlende Spalten, doppelte BerufNr)
