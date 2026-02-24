"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { getBerufe } from "@/lib/api";
import type { BerufListItem } from "@/types/api";
import { formatDatum, statusBadgeClass, statusLabel } from "@/lib/utils";

export default function BerufeSeite() {
  const [berufe, setBerufe] = useState<BerufListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [suche, setSuche] = useState("");

  useEffect(() => {
    getBerufe()
      .then(setBerufe)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const gefiltert = berufe.filter(
    (b) =>
      b.beruf.toLowerCase().includes(suche.toLowerCase()) ||
      b.beschreibung.toLowerCase().includes(suche.toLowerCase())
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Berufe</h2>
          <p className="text-sm text-slate-500">{berufe.length} Berufe insgesamt</p>
        </div>
        <input
          type="search"
          placeholder="Suche…"
          value={suche}
          onChange={(e) => setSuche(e.target.value)}
          className="border border-slate-200 rounded-md px-3 py-1.5 text-sm w-48
            focus:outline-none focus:ring-1 focus:ring-blue-400"
        />
      </div>

      {loading ? (
        <p className="text-sm text-slate-400">Lade…</p>
      ) : gefiltert.length === 0 ? (
        <p className="text-sm text-slate-400">Keine Einträge gefunden.</p>
      ) : (
        <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50 text-xs text-slate-500 uppercase tracking-wide">
                <th className="px-4 py-2.5 text-left">Beruf</th>
                <th className="px-4 py-2.5 text-left">Typ</th>
                <th className="px-4 py-2.5 text-left">Bereiche</th>
                <th className="px-4 py-2.5 text-left">Jahr</th>
                <th className="px-4 py-2.5 text-left">Verarbeitet am</th>
                <th className="px-4 py-2.5 text-left">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {gefiltert.map((b) => (
                <tr key={b.beruf} className="hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-2.5">
                    <Link
                      href={`/berufe/${b.beruf}`}
                      className="font-medium text-blue-600 hover:underline"
                    >
                      {b.beruf}
                    </Link>
                    {b.beschreibung && (
                      <p className="text-xs text-slate-400 truncate max-w-xs">{b.beschreibung}</p>
                    )}
                  </td>
                  <td className="px-4 py-2.5 text-slate-600">{b.prüfungsTyp || "—"}</td>
                  <td className="px-4 py-2.5 text-slate-600">{b.anzahlBereiche}</td>
                  <td className="px-4 py-2.5 text-slate-600">{b.jahr ?? "—"}</td>
                  <td className="px-4 py-2.5 text-slate-500 text-xs">{formatDatum(b.verarbeitetAm)}</td>
                  <td className="px-4 py-2.5">
                    {b.verarbeitetAm ? (
                      <span className={`px-2 py-0.5 rounded-full text-xs ${statusBadgeClass("ERFOLG")}`}>
                        {statusLabel("ERFOLG")}
                      </span>
                    ) : (
                      <span className="text-xs text-slate-400">Ausstehend</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
