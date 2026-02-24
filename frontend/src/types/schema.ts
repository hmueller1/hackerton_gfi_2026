// Typen für das BPÜ JSON-Schema

export interface Aufgabe {
  bezeichnung: string;
  zeitMinuten: number | null;
  gewichtungImBereich: number | null;
  punkte: number | null;
}

export interface Gewichtung {
  imPrüfungsbereich: number | null;
  schriftlichePrüfung: number | null;
  teil2: number | null;
  gesamtergebnis: number | null;
}

export interface Variante {
  bezeichnung: string;
  aufgaben: Aufgabe[];
  gewichtung: Gewichtung;
}

export interface Prüfungsbereich {
  name: string;
  typ: "schriftlich" | "praktisch";
  varianten: Variante[] | null;
  aufgaben: Aufgabe[];
  gewichtung: Gewichtung;
}

export interface Metadaten {
  beruf: string;
  jahr: number;
  quelldatei: string;
  verarbeitetAm: string;
  konfigVersion: string;
}

export interface BerufSchema {
  berufNr: string[];
  beschreibung: string;
  prüfungsTyp: string;
  prüfungsbereiche: Prüfungsbereich[];
  metadaten: Metadaten;
}
