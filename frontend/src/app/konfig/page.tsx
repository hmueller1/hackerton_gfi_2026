"use client";
import { useEffect, useState } from "react";
import { getKonfigs, getKonfigYaml, approveKonfig, rejectKonfig } from "@/lib/api";
import type { KonfigEintrag, KonfigListe } from "@/types/api";
import { formatDatum } from "@/lib/utils";

function ScoreBadge({ score }: { score: number | null }) {
  if (score === null) return <span className="text-xs text-slate-400">—</span>;
  const color =
    score >= 85 ? "bg-green-100 text-green-700" :
    score >= 70 ? "bg-yellow-100 text-yellow-700" :
                  "bg-red-100 text-red-700";
  return <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${color}`}>{score}/100</span>;
}

function KonfigZeile({
  k,
  isPending,
  onApprove,
  onReject,
}: {
  k: KonfigEintrag;
  isPending: boolean;
  onApprove?: () => void;
  onReject?: () => void;
}) {
  const [yaml, setYaml] = useState<string | null>(null);
  const [loadingYaml, setLoadingYaml] = useState(false);
  const [acting, setActing] = useState(false);

  async function toggleYaml() {
    if (yaml !== null) { setYaml(null); return; }
    setLoadingYaml(true);
    try {
      setYaml(await getKonfigYaml(k.beruf));
    } catch { setYaml("Fehler beim Laden"); }
    setLoadingYaml(false);
  }

  async function handleApprove() {
    setActing(true);
    try { await approveKonfig(k.beruf); onApprove?.(); }
    catch (e) { alert(`Fehler: ${e}`); }
    setActing(false);
  }

  async function handleReject() {
    if (!confirm(`Konfig für „${k.beruf}" ablehnen?`)) return;
    setActing(true);
    try { await rejectKonfig(k.beruf); onReject?.(); }
    catch (e) { alert(`Fehler: ${e}`); }
    setActing(false);
  }

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden bg-white">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3 min-w-0">
          {isPending && (
            <span className="shrink-0 text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 font-medium">
              Pending
            </span>
          )}
          <span className="text-sm font-medium text-slate-800">{k.beruf}</span>
          <span className="text-xs text-slate-400">v{k.version}</span>
          <ScoreBadge score={k.score} />
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-xs text-slate-400">{formatDatum(k.erstelltAm)}</span>
          <span className="text-xs text-slate-400">{k.erstelltDurch}</span>
          <button
            onClick={toggleYaml}
            className="text-xs px-2 py-1 rounded border border-slate-200 hover:bg-slate-100 transition-colors"
          >
            {loadingYaml ? "…" : yaml !== null ? "Schließen" : "YAML"}
          </button>
          {isPending && (
            <>
              <button
                onClick={handleApprove}
                disabled={acting}
                className="text-xs px-2 py-1 rounded bg-green-600 text-white hover:bg-green-700
                  disabled:opacity-50 transition-colors"
              >
                Freigeben
              </button>
              <button
                onClick={handleReject}
                disabled={acting}
                className="text-xs px-2 py-1 rounded border border-red-300 text-red-600
                  hover:bg-red-50 disabled:opacity-50 transition-colors"
              >
                Ablehnen
              </button>
            </>
          )}
        </div>
      </div>

      {k.begruendung && (
        <div className="px-4 pb-2 text-xs text-slate-500 italic">
          {k.begruendung}
        </div>
      )}

      {yaml !== null && (
        <div className="border-t border-slate-100">
          <pre className="text-xs bg-slate-50 p-4 overflow-auto max-h-96 font-mono leading-relaxed">
            {yaml}
          </pre>
        </div>
      )}
    </div>
  );
}

export default function KonfigSeite() {
  const [data, setData] = useState<KonfigListe | null>(null);
  const [loading, setLoading] = useState(true);

  function reload() {
    setLoading(true);
    getKonfigs()
      .then(setData)
      .catch(() => {})
      .finally(() => setLoading(false));
  }

  useEffect(reload, []);

  if (loading) return <p className="text-sm text-slate-400">Lade…</p>;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-800">Konfig-Bibliothek</h2>
        <p className="text-sm text-slate-500">
          {data?.aktiv.length ?? 0} aktiv · {data?.pending.length ?? 0} ausstehend
        </p>
      </div>

      {/* Pending section */}
      {data && data.pending.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-yellow-700 flex items-center gap-2">
            <span className="inline-block w-2 h-2 rounded-full bg-yellow-500" />
            Warten auf Freigabe ({data.pending.length})
          </h3>
          {data.pending.map((k) => (
            <KonfigZeile
              key={k.beruf}
              k={k}
              isPending
              onApprove={reload}
              onReject={reload}
            />
          ))}
        </div>
      )}

      {/* Active section */}
      <div className="space-y-2">
        <h3 className="text-sm font-medium text-slate-600">
          Aktive Konfigurationen ({data?.aktiv.length ?? 0})
        </h3>
        {data && data.aktiv.length > 0 ? (
          data.aktiv.map((k) => (
            <KonfigZeile key={k.beruf} k={k} isPending={false} />
          ))
        ) : (
          <p className="text-sm text-slate-400">Keine aktiven Konfigurationen.</p>
        )}
      </div>
    </div>
  );
}
