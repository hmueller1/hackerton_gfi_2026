---
stepsCompleted: ['step-01-discovery']
created: 2026-02-24
status: DISCOVERY
---

# Workflow Creation Plan

## Discovery Notes

**User's Vision:**
Ein geführter Pipeline-Workflow zur KI-gestützten Extraktion strukturierter Daten aus Berufsprüfungs-PDFs (heterogene Layouts). Der Workflow erkennt automatisch, ob für einen Beruf bereits eine Mapping-Konfig existiert und verzweigt entsprechend in Onboarding (Option A) oder direkten Pipeline-Lauf (Option B). Das System folgt dem "Configure-Once, Run-Forever"-Prinzip: KI ist nur einmalig bei der Konfig-Generierung involviert, alle Folgeläufe sind vollständig deterministisch.

**Who It's For:**
Alle Teammitglieder (inkl. nicht-technische Nutzer), kein paralleler Betrieb, einfache Bedienbarkeit als oberste UX-Priorität.

**What It Produces:**
- JSON pro Beruf (strukturierte Prüfungsdaten nach definiertem Schema)
- Validation Report (V1 JSON-Schema-Gate + V2 Numerische Konsistenz-Checks)
- Übersichtsansicht: Status aller bekannten Berufe + maximale Dateneinblicke aus den JSON-Daten

**Key Insights:**
- Zwei Modi in einem Workflow: Onboarding (neue Berufe, KI-gestützt, menschliche Verifikation) + Pipeline-Lauf (bekannte Berufe, deterministisch)
- Automatische Modus-Erkennung: "Gibt es eine Konfig für diesen Beruf?" → ja → Pipeline-Lauf / nein → Onboarding → Pipeline-Lauf
- Konfig-Bibliothek als akkumuliertes Systemwissen: Mit jedem neuen Beruf wird das System stabiler
- Result-First Dual-View für Verifikation: Nutzer validiert am Ergebnis, nicht an abstraktem YAML
- Confidence-Score + Begründung bei KI-Konfig-Generierung (Unsicherheit explizit kommunizieren)
- Tech-Stack: Next.js (Frontend/Orchestrierung) + Python FastAPI (PDF-Parsing, Extraktion, Validierung)

**Context Document:**
_bmad-output/brainstorming/brainstorming-session-2026-02-24.md
