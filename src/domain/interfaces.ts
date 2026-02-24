export interface Termin {
  readonly datum: string;
  readonly uhrzeitvon: string;
  readonly uhrzeitbis: string;
  readonly dauer: number;
}

export interface Aufgabe {
  readonly name: string;
  readonly struktur: string;
  readonly termin: Termin;
  readonly hilfmittel?: string;
}

export interface PruefungsBereich {
  readonly name: string;
  readonly aufgaben: readonly Aufgabe[];
}

export interface Beruf {
  readonly beschreibung: string;
  readonly berufNr: readonly number[];
  readonly pruefungsBereiche: readonly PruefungsBereich[];
}

export type BerufDocument = {
  readonly beruf: Beruf;
};
