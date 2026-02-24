"use client";
import { useEffect, useState } from "react";
import { getFehler, getFehlerPdfUrl } from "@/lib/api";
import type { FehlerEintrag } from "@/types/api";
import { formatDatum, fehlerBadgeClass } from "@/lib/utils";

const FEHLER_LABELS: Record<string, string> = {
  V1_SCHEMA_FEHLER:        "Schema-Fehler",
  V2_KONSISTENZ_FEHLER:    "Konsistenz-Fehler",
  KONFIG_FEHLT:            "Konfig fehlt",
  KI_NICHT_VERFUEGBAR:     "KI nicht verfügbar",
  KI_ANTWORT_UNGUELTIG:    "KI-Antwort ungültig",
  KI_KONFIG_UNVOLLSTAENDIG:"KI-Konfig unvollständig",
};

export default function FehlerSeite() {
  const [fehler, setFehler] = useState<FehlerEintrag[]>([]);
  const [loading, setLoading] = useState(true);
  const [offen, setOffen] = useState<string | null>(null);

  useEffect(() => {
    getFehler()
      .then(setFehler)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="text-sm text-slate-400">Lade…</p>;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">Fehler</h2>
        <p className="text-sm text-slate-500">{fehler.length} fehlgeschlagene Extraktionen</p>
      </div>

      {fehler.length === 0 ? (
        <div className="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <p className="text-green-700 font-medium">Keine Fehler vorhanden</p>
          <p className="text-xs text-green-600 mt-1">Alle PDFs wurden erfolgreich verarbeitet.</p>
        </div>
      ) : (
        <div className="space-y-2">
          {fehler.map((f) => {
            const key = `${f.beruf}-${f.zeitstempel}`;
            const istOffen = offen === key;
            return (
              <div key={key} className="bg-white border border-slate-200 rounded-lg overflow-hidden">
                <button
                  className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors text-left"
                  onClick={() => setOffen(istOffen ? null : key)}
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full ${fehlerBadgeClass(f.fehlerTyp)}`}>
                      {FEHLER_LABELS[f.fehlerTyp] ?? f.fehlerTyp}
                    </span>
                    <span className="text-sm font-medium text-slate-800 truncate">{f.beruf}</span>
                    <span className="text-xs text-slate-400 shrink-0">{f.datei}</span>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    <span className="text-xs text-slate-400">{formatDatum(f.zeitstempel)}</span>
                    <span className="text-slate-400 text-xs">{istOffen ? "▲" : "▼"}</span>
                  </div>
                </button>

                {istOffen && (
                  <div className="px-4 pb-4 border-t border-slate-100 space-y-3 pt-3">
                    <div>
                      <p className="text-xs text-slate-500 mb-1 uppercase tracking-wide">Fehlermeldung</p>
                      <p className="text-sm text-red-700 bg-red-50 rounded p-2">{f.meldung}</p>
                    </div>

                    {f.details && Object.keys(f.details).length > 0 && (
                      <div>
                        <p className="text-xs text-slate-500 mb-1 uppercase tracking-wide">Details</p>
                        <pre className="text-xs bg-slate-50 border border-slate-100 rounded p-2 overflow-auto max-h-40">
                          {JSON.stringify(f.details, null, 2)}
                        </pre>
                      </div>
                    )}

                    <div className="flex items-center gap-3">
                      <span className="text-xs text-slate-500">Jahr: {f.jahr}</span>
                      {f.hatPdf && (
                        <a
                          href={getFehlerPdfUrl(f.pfadKey)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs px-2 py-1 rounded border border-slate-200 hover:bg-slate-100 transition-colors"
                        >
                          PDF herunterladen
                        </a>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
