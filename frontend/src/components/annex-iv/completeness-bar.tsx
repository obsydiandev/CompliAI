import { cn } from "@/lib/utils";

interface CompletenessBarProps {
  pct: number;
  label?: string;
  showLabel?: boolean;
}

export function CompletenessBar({ pct, label, showLabel = true }: CompletenessBarProps) {
  const color =
    pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500";

  return (
    <div className="space-y-1">
      {(label || showLabel) && (
        <div className="flex items-center justify-between text-sm">
          {label && <span className="text-gray-600">{label}</span>}
          {showLabel && (
            <span
              className={cn(
                "font-medium",
                pct >= 80 ? "text-green-600" : pct >= 50 ? "text-yellow-600" : "text-red-600"
              )}
            >
              {pct.toFixed(1)}%
            </span>
          )}
        </div>
      )}
      <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-300", color)}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  );
}
