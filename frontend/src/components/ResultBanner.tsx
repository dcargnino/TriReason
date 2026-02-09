import { useState } from "react";
import type { WorkflowState } from "../types/api";

interface Props {
  workflow: WorkflowState;
}

const STOP_LABELS: Record<string, string> = {
  threshold_reached: "Score threshold reached",
  max_iterations_reached: "Maximum iterations reached",
  no_improvement: "No further improvement detected",
};

export function ResultBanner({ workflow }: Props) {
  const [copied, setCopied] = useState(false);

  if (workflow.phase !== "complete" || !workflow.bestPrompt) return null;

  const handleCopy = async () => {
    await navigator.clipboard.writeText(workflow.bestPrompt!);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-emerald-500/40 bg-emerald-950/20 p-5 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl">{"\u{1F3C6}"}</span>
          <h3 className="font-bold text-emerald-400">Optimization Complete</h3>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="text-gray-400">
            {STOP_LABELS[workflow.stopReason || ""] || workflow.stopReason}
          </span>
          <span className="font-mono font-bold text-emerald-400">
            {workflow.bestScore?.toFixed(1)}/100
          </span>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs font-medium text-gray-400">Best Prompt</span>
          <button
            onClick={handleCopy}
            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
          >
            {copied ? "\u2713 Copied!" : "Copy"}
          </button>
        </div>
        <pre className="text-sm bg-gray-950 border border-gray-800 rounded-lg p-4 whitespace-pre-wrap text-gray-200 max-h-60 overflow-y-auto">
          {workflow.bestPrompt}
        </pre>
      </div>
    </div>
  );
}
