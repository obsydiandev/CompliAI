import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-GB", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function capitalize(str: string): string {
  return str.charAt(0).toUpperCase() + str.slice(1);
}

export function sectionLabel(key: string): string {
  return key
    .split("_")
    .map((w) => capitalize(w))
    .join(" ");
}

export function riskLevelColor(level: string): string {
  const map: Record<string, string> = {
    minimal: "bg-green-100 text-green-800",
    limited: "bg-yellow-100 text-yellow-800",
    high: "bg-red-100 text-red-800",
    unacceptable: "bg-gray-900 text-white",
  };
  return map[level] ?? "bg-gray-100 text-gray-800";
}

export function completenessColor(pct: number): string {
  if (pct >= 80) return "text-green-600";
  if (pct >= 50) return "text-yellow-600";
  return "text-red-600";
}
