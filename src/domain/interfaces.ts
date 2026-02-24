export interface Termin {
  start: string;
  ende: string;
}

export interface Aufgabe {
  nummer: number;
  titel: string;
  beschreibung: string;
  punkte: number;
}

export interface PruefungsBereich {
  bezeichnung: string;
  aufgaben: Aufgabe[];
  gesamtpunkte: number;
}

export interface Beruf {
  name: string;
  kennung: string;
  pruefungsart: string;
  termin: Termin;
  bereiche: PruefungsBereich[];
}
