"use client";
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { getBeruf, runSingle } from "@/lib/api";
import type { BerufSchema, Prüfungsbereich } from "@/types/schema";
import { formatDatum } from "@/lib/utils";

function Gewichtungstabelle({ gew }: { gew: BerufSchema["prüfungsbereiche"][0]["gewichtung"] }) {
  const felder: [string, keyof typeof gew][] = [
    ["Im Prüfungsbereich", "imPrüfungsbereich"],
    ["Schriftliche Prüfung", "schriftlichePrüfung"],
    ["Teil 2", "teil2"],
    ["Gesamtergebnis", "gesamtergebnis"],
  ];
  return (
    <div className="flex gap-4 flex-wrap">
      {felder.map(([label, key]) =>
        gew[key] !== null ? (
          <div key={key} className="text-center">
            <p className="text-lg font-bold text-slate-800">{gew[key]}%</p>
            <p className="text-xs text-slate-500">{label}</p>
          </div>
        ) : null
      )}
    </div>
  );
}

function BereichKarte({ b }: { b: Prüfungsbereich }) {
  const [offen, setOffen] = useState(false);
  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <button
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-50 transition-colors"
        onClick={() => setOffen((v) => !v)}
      >
        <div className="flex items-center gap-3">
          <span
            className={`text-xs px-2 py-0.5 rounded-full font-medium ${
              b.typ === "schriftlich"
                ? "bg-blue-100 text-blue-700"
                : "bg-purple-100 text-purple-700"
            }`}
          >
            {b.typ === "schriftlich" ? "Schriftlich" : "Praktisch"}
          </span>
          <span className="text-sm font-medium text-slate-800">{b.name}</span>
        </div>
        <span className="text-slate-400 text-xs">{offen ? "▲" : "▼"}</span>
      </button>

      {offen && (
        <div className="px-4 pb-4 border-t border-slate-100 space-y-4">
          <div className="pt-3">
            <p className="text-xs text-slate-500 mb-2 uppercase tracking-wide">Gewichtung</p>
            <Gewichtungstabelle gew={b.gewichtung} />
          </div>

          {/* Varianten */}
          {b.varianten && b.varianten.length > 0 ? (
            <div>
              <p className="text-xs text-slate-500 mb-2 uppercase tracking-wide">Varianten</p>
              <div className="space-y-3">
                {b.varianten.map((v, vi) => (
                  <div key={vi} className="border border-slate-100 rounded p-3">
                    <p className="text-sm font-medium text-slate-700 mb-2">{v.bezeichnung}</p>
                    <AufgabenTabelle aufgaben={v.aufgaben} />
                  </div>
                ))}
              </div>
            </div>
          ) : b.aufgaben && b.aufgaben.length > 0 ? (
            <div>
              <p className="text-xs text-slate-500 mb-2 uppercase tracking-wide">Aufgaben</p>
              <AufgabenTabelle aufgaben={b.aufgaben} />
            </div>
          ) : null}
        </div>
      )}
    </div>
  );
}

function AufgabenTabelle({ aufgaben }: { aufgaben: BerufSchema["prüfungsbereiche"][0]["aufgaben"] }) {
  if (!aufgaben || aufgaben.length === 0) return null;
  return (
    <table className="w-full text-xs">
      <thead>
        <tr className="text-slate-400 border-b border-slate-100">
          <th className="text-left pb-1">Bezeichnung</th>
          <th className="text-right pb-1">Zeit (min)</th>
          <th className="text-right pb-1">Gewichtung</th>
          <th className="text-right pb-1">Punkte</th>
        </tr>
      </thead>
      <tbody>
        {aufgaben.map((a, i) => (
          <tr key={i} className="border-b border-slate-50">
            <td className="py-1 text-slate-700">{a.bezeichnung}</td>
            <td className="py-1 text-right text-slate-500">{a.zeitMinuten ?? "—"}</td>
            <td className="py-1 text-right text-slate-500">{a.gewichtungImBereich !== null ? `${a.gewichtungImBereich}%` : "—"}</td>
            <td className="py-1 text-right text-slate-500">{a.punkte ?? "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export default function BerufDetailSeite() {
  const params = useParams();
  const beruf = params.beruf as string;
  const [data, setData] = useState<BerufSchema | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rerunning, setRerunning] = useState(false);

  useEffect(() => {
    getBeruf(beruf)
      .then(setData)
      .catch((e) => setError(String(e)))
      .finally(() => setLoading(false));
  }, [beruf]);

  async function handleRerun() {
    if (!data) return;
    setRerunning(true);
    try {
      await runSingle(beruf, data.metadaten.jahr);
      alert("Job gestartet. Bitte Seite nach kurzer Zeit neu laden.");
    } catch (e) {
      alert(`Fehler: ${e}`);
    }
    setRerunning(false);
  }

  if (loading) return <p className="text-sm text-slate-400">Lade…</p>;
  if (error || !data)
    return (
      <div className="space-y-3">
        <Link href="/berufe" className="text-sm text-blue-600 hover:underline">← Zurück</Link>
        <p className="text-sm text-red-600">{error ?? "Daten nicht gefunden."}</p>
      </div>
    );

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <Link href="/berufe" className="text-xs text-blue-600 hover:underline">← Berufe</Link>
          <h2 className="text-xl font-semibold text-slate-800 mt-1 capitalize">{beruf}</h2>
          <p className="text-sm text-slate-500">{data.beschreibung}</p>
          <div className="flex gap-3 mt-1 text-xs text-slate-400">
            <span>Typ: {data.prüfungsTyp}</span>
            <span>Jahr: {data.metadaten.jahr}</span>
            <span>Version: {data.metadaten.konfigVersion}</span>
            <span>Verarbeitet: {formatDatum(data.metadaten.verarbeitetAm)}</span>
          </div>
        </div>
        <button
          onClick={handleRerun}
          disabled={rerunning}
          className="px-3 py-1.5 text-xs rounded border border-slate-200 hover:bg-slate-100
            disabled:opacity-50 transition-colors"
        >
          {rerunning ? "Läuft…" : "Neu verarbeiten"}
        </button>
      </div>

      <div>
        <h3 className="text-sm font-medium text-slate-600 mb-3">
          Prüfungsbereiche ({data.prüfungsbereiche.length})
        </h3>
        <div className="space-y-2">
          {data.prüfungsbereiche.map((b, i) => (
            <BereichKarte key={i} b={b} />
          ))}
        </div>
      </div>
    </div>
  );
}
