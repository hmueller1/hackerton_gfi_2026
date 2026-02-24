// API-Response-Typen

export interface BerufListItem {
  beruf: string;
  beschreibung: string;
  prüfungsTyp: string;
  berufNr: string[];
  anzahlBereiche: number;
  jahr: number | null;
  verarbeitetAm: string | null;
  konfigVersion: string | null;
}

export interface FehlerEintrag {
  datei: string;
  beruf: string;
  jahr: number;
  zeitstempel: string;
  fehlerTyp: string;
  meldung: string;
  details: Record<string, unknown>;
  hatPdf: boolean;
  pfadKey: string;
}

export interface KonfigEintrag {
  beruf: string;
  version: string;
  erstelltDurch: string;
  erstelltAm: string | null;
  score: number | null;
  begruendung?: string | null;
  pending: boolean;
}

export interface KonfigListe {
  aktiv: KonfigEintrag[];
  pending: KonfigEintrag[];
}

export interface PipelineJob {
  jobId: string;
  status: "gestartet" | "läuft" | "abgeschlossen";
  gesamt: number;
  verarbeitet: number;
  ergebnisse: PipelineErgebnis[];
}

export interface PipelineErgebnis {
  datei: string;
  status: "ERFOLG" | "FEHLER" | "UEBERSPRUNGEN" | "ZUR_REVIEW";
  fehlerTyp: string | null;
  meldung: string | null;
  dauerMs: number;
  ausgabePfad: string | null;
  konfidenzScore: number | null;
}
