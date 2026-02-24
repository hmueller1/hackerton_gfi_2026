// Hilfsfunktionen

export function formatDatum(iso: string | null | undefined): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString("de-DE", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

export function statusBadgeClass(status: string): string {
  switch (status) {
    case "ERFOLG":        return "bg-green-100 text-green-800";
    case "FEHLER":        return "bg-red-100 text-red-800";
    case "ZUR_REVIEW":    return "bg-yellow-100 text-yellow-800";
    case "UEBERSPRUNGEN": return "bg-gray-100 text-gray-600";
    default:              return "bg-slate-100 text-slate-600";
  }
}

export function statusLabel(status: string): string {
  switch (status) {
    case "ERFOLG":        return "Verarbeitet";
    case "FEHLER":        return "Fehlerhaft";
    case "ZUR_REVIEW":    return "Zur Review";
    case "UEBERSPRUNGEN": return "Übersprungen";
    default:              return status;
  }
}

export function fehlerBadgeClass(typ: string): string {
  switch (typ) {
    case "V1_SCHEMA_FEHLER":
    case "V2_KONSISTENZ_FEHLER": return "bg-orange-100 text-orange-800";
    case "KONFIG_FEHLT":         return "bg-yellow-100 text-yellow-800";
    case "KI_NICHT_VERFUEGBAR":  return "bg-gray-100 text-gray-600";
    default:                     return "bg-red-100 text-red-800";
  }
}
