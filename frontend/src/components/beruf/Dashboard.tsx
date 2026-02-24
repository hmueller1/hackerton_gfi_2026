"use client";
import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  getBerufe,
  getFehler,
  getKonfigs,
  startPipeline,
  getPipelineStatus,
  getAktiverJob,
} from "@/lib/api";
import type { BerufListItem, FehlerEintrag, KonfigListe, PipelineJob } from "@/types/api";
import { statusBadgeClass, statusLabel } from "@/lib/utils";

function StatCard({ label, value, sub, color }: { label: string; value: number | string; sub?: string; color?: string }) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color ?? "text-slate-800"}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

function JobProgress({ job }: { job: PipelineJob }) {
  const pct = job.gesamt > 0 ? Math.round((job.verarbeitet / job.gesamt) * 100) : 0;
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium text-slate-700">Pipeline läuft…</span>
        <span className="text-xs text-slate-500">{job.verarbeitet}/{job.gesamt} ({pct}%)</span>
      </div>
      <div className="w-full bg-slate-100 rounded-full h-2">
        <div
          className="bg-blue-500 h-2 rounded-full transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="mt-2 flex gap-3 text-xs text-slate-500">
        {["ERFOLG", "FEHLER", "ZUR_REVIEW", "UEBERSPRUNGEN"].map((s) => {
          const n = job.ergebnisse.filter((r) => r.status === s).length;
          return n > 0 ? (
            <span key={s} className={`px-1.5 py-0.5 rounded ${statusBadgeClass(s)}`}>
              {statusLabel(s)}: {n}
            </span>
          ) : null;
        })}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [berufe, setBerufe] = useState<BerufListItem[]>([]);
  const [fehler, setFehler] = useState<FehlerEintrag[]>([]);
  const [konfigs, setKonfigs] = useState<KonfigListe | null>(null);
  const [job, setJob] = useState<PipelineJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [noAi, setNoAi] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const [b, f, k] = await Promise.all([getBerufe(), getFehler(), getKonfigs()]);
      setBerufe(b);
      setFehler(f);
      setKonfigs(k);
    } catch { /* ignore */ }
    setLoading(false);
  }, []);

  // Poll for active job
  const pollJob = useCallback(async () => {
    try {
      const aktiv = await getAktiverJob();
      setJob(aktiv);
      if (aktiv && aktiv.status !== "abgeschlossen") {
        setTimeout(pollJob, 2000);
      } else if (aktiv?.status === "abgeschlossen") {
        loadData();
      }
    } catch {
      setJob(null);
    }
  }, [loadData]);

  useEffect(() => {
    loadData();
    pollJob();
  }, [loadData, pollJob]);

  async function handleStart() {
    setStarting(true);
    try {
      const { jobId } = await startPipeline(noAi);
      // Start polling
      const pollNew = async () => {
        try {
          const j = await getPipelineStatus(jobId);
          setJob(j);
          if (j.status !== "abgeschlossen") setTimeout(pollNew, 2000);
          else loadData();
        } catch { /* ignore */ }
      };
      pollNew();
    } catch (e) {
      alert(`Fehler beim Starten: ${e}`);
    }
    setStarting(false);
  }

  const verarbeitet = berufe.filter((b) => b.verarbeitetAm).length;
  const pending = konfigs?.pending.length ?? 0;
  const aktiv = konfigs?.aktiv.length ?? 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-slate-800">Dashboard</h2>
          <p className="text-sm text-slate-500">BPÜ Datenextraktion — Übersicht</p>
        </div>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-sm text-slate-600 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={noAi}
              onChange={(e) => setNoAi(e.target.checked)}
              className="rounded"
            />
            Ohne KI
          </label>
          <button
            onClick={handleStart}
            disabled={starting || (job !== null && job.status !== "abgeschlossen")}
            className="px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium
              hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {starting ? "Startet…" : "Pipeline starten"}
          </button>
        </div>
      </div>

      {/* Active job progress */}
      {job && job.status !== "abgeschlossen" && <JobProgress job={job} />}

      {/* Stats */}
      {loading ? (
        <p className="text-sm text-slate-400">Lade…</p>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard label="Berufe gesamt" value={berufe.length} />
          <StatCard label="Verarbeitet" value={verarbeitet} color="text-green-600" />
          <StatCard
            label="Fehler offen"
            value={fehler.length}
            color={fehler.length > 0 ? "text-red-600" : "text-slate-800"}
          />
          <StatCard
            label="Konfig pending"
            value={pending}
            sub={`${aktiv} aktiv`}
            color={pending > 0 ? "text-yellow-600" : "text-slate-800"}
          />
        </div>
      )}

      {/* Recent results */}
      {job?.status === "abgeschlossen" && job.ergebnisse.length > 0 && (
        <div className="bg-white rounded-lg border border-slate-200">
          <div className="px-4 py-3 border-b border-slate-100">
            <h3 className="text-sm font-medium text-slate-700">Letzter Pipeline-Lauf</h3>
          </div>
          <div className="divide-y divide-slate-100">
            {job.ergebnisse.slice(0, 10).map((r, i) => (
              <div key={i} className="flex items-center justify-between px-4 py-2.5">
                <span className="text-sm text-slate-700 truncate max-w-xs">{r.datei}</span>
                <div className="flex items-center gap-3">
                  {r.konfidenzScore !== null && (
                    <span className="text-xs text-slate-400">{r.konfidenzScore}/100</span>
                  )}
                  <span className={`text-xs px-2 py-0.5 rounded-full ${statusBadgeClass(r.status)}`}>
                    {statusLabel(r.status)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quick links */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {[
          { href: "/berufe",  label: "Berufe ansehen",      desc: `${berufe.length} Einträge` },
          { href: "/fehler",  label: "Fehler prüfen",       desc: `${fehler.length} offen`,  warn: fehler.length > 0 },
          { href: "/konfig",  label: "Konfig-Bibliothek",   desc: `${pending} ausstehend`,   warn: pending > 0 },
        ].map((l) => (
          <Link
            key={l.href}
            href={l.href}
            className="bg-white border border-slate-200 rounded-lg p-4 hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            <p className={`text-sm font-medium ${l.warn ? "text-red-600" : "text-slate-800"}`}>{l.label}</p>
            <p className="text-xs text-slate-500 mt-0.5">{l.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
