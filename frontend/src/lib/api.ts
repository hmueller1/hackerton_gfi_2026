// Zentraler API-Client für FastAPI-Backend

import type {
  BerufListItem,
  FehlerEintrag,
  KonfigListe,
  PipelineJob,
} from "@/types/api";
import type { BerufSchema } from "@/types/schema";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30_000);
  try {
    const res = await fetch(`${BASE}${path}`, {
      ...init,
      signal: controller.signal,
    });
    if (!res.ok) {
      const detail = await res.text().catch(() => res.statusText);
      throw new Error(`API ${res.status}: ${detail}`);
    }
    return res.json() as Promise<T>;
  } finally {
    clearTimeout(timer);
  }
}

// ── Berufe ───────────────────────────────────────────────────────────

export async function getBerufe(): Promise<BerufListItem[]> {
  return apiFetch<BerufListItem[]>("/berufe");
}

export async function getBeruf(beruf: string): Promise<BerufSchema> {
  return apiFetch<BerufSchema>(`/berufe/${beruf}`);
}

// ── Fehler ───────────────────────────────────────────────────────────

export async function getFehler(): Promise<FehlerEintrag[]> {
  return apiFetch<FehlerEintrag[]>("/fehler");
}

export function getFehlerPdfUrl(pfadKey: string): string {
  return `${BASE}/fehler/download?pfad_key=${encodeURIComponent(pfadKey)}`;
}

// ── Konfig ───────────────────────────────────────────────────────────

export async function getKonfigs(): Promise<KonfigListe> {
  return apiFetch<KonfigListe>("/konfig");
}

export async function getKonfigYaml(beruf: string): Promise<string> {
  const res = await fetch(`${BASE}/konfig/${beruf}`);
  if (!res.ok) throw new Error(`Konfig nicht gefunden: ${beruf}`);
  return res.text();
}

export async function approveKonfig(beruf: string): Promise<void> {
  await apiFetch(`/konfig/${beruf}/approve`, { method: "POST" });
}

export async function rejectKonfig(beruf: string): Promise<void> {
  await apiFetch(`/konfig/${beruf}/pending`, { method: "DELETE" });
}

// ── Pipeline ─────────────────────────────────────────────────────────

export async function startPipeline(noAi = false): Promise<{ jobId: string }> {
  return apiFetch<{ jobId: string }>(
    `/pipeline/start?no_ai=${noAi}`,
    { method: "POST" }
  );
}

export async function getPipelineStatus(jobId: string): Promise<PipelineJob> {
  return apiFetch<PipelineJob>(`/pipeline/status/${jobId}`);
}

export async function getAktiverJob(): Promise<PipelineJob | null> {
  return apiFetch<PipelineJob | null>("/pipeline/aktiv");
}

export async function runSingle(beruf: string, jahr: number): Promise<{ jobId: string }> {
  return apiFetch<{ jobId: string }>(
    `/pipeline/run-single?beruf=${beruf}&jahr=${jahr}`,
    { method: "POST" }
  );
}
