interface Props {
  label: string;
  value: number;
  weight?: string;
}

function barColor(value: number): string {
  if (value >= 85) return "bg-emerald-500";
  if (value >= 70) return "bg-amber-500";
  return "bg-red-500";
}

export function ScoreBar({ label, value, weight }: Props) {
  return (
    <div className="flex items-center gap-2 text-xs">
      <div className="w-36 text-gray-400 truncate flex items-center justify-between">
        <span>{label}</span>
        {weight && <span className="text-gray-600 ml-1">{weight}</span>}
      </div>
      <div className="flex-1 h-2 rounded-full bg-gray-800 overflow-hidden">
        <div
          className={`h-full rounded-full score-bar-animate ${barColor(value)}`}
          style={{ width: `${value}%` }}
        />
      </div>
      <div className="w-8 text-right font-mono text-gray-300">{value}</div>
    </div>
  );
}
