import { useState } from "react";
import { ChevronUp, ChevronDown } from "lucide-react";
import type { IterationResult } from "../types/api";
import { ScoreBar } from "./ScoreBar";

interface Props {
  iterations: IterationResult[];
}

export function IterationPanel({ iterations }: Props) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  if (iterations.length === 0) {
    return (
      <div className="text-center text-gray-600 py-10 text-sm">
        No iterations yet. Start an optimization to see results.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-2">
      {iterations.map((it, idx) => {
        const isExpanded = expandedIdx === idx;
        return (
          <div
            key={it.iteration_number}
            className={`rounded-lg border transition-colors ${
              it.is_best_so_far
                ? "border-indigo-500/50 bg-indigo-950/20"
                : "border-gray-800 bg-gray-900/50"
            }`}
          >
            {/* Header row */}
            <button
              onClick={() => setExpandedIdx(isExpanded ? null : idx)}
              className="w-full flex items-center justify-between px-4 py-3 text-left"
            >
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono text-gray-500">
                  #{it.iteration_number}
                </span>
                <span
                  className={`text-sm font-semibold ${
                    it.passed ? "text-emerald-400" : "text-amber-400"
                  }`}
                >
                  {it.score_total.toFixed(1)}
                </span>
                {it.passed && (
                  <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-900/60 text-emerald-400">
                    PASS
                  </span>
                )}
                {it.is_best_so_far && (
                  <span className="text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded bg-indigo-900/60 text-indigo-400">
                    BEST
                  </span>
                )}
              </div>
              <span className="text-gray-600 text-xs">{isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}</span>
            </button>

            {/* Expanded detail */}
            {isExpanded && (
              <div className="px-4 pb-4 space-y-4 border-t border-gray-800">
                {/* Score breakdown */}
                <div className="pt-3 space-y-1.5">
                  <ScoreBar
                    label="Objective fulfillment"
                    value={it.score_breakdown.objective_fulfillment}
                    weight="40%"
                  />
                  <ScoreBar
                    label="Correctness"
                    value={it.score_breakdown.correctness_faithfulness}
                    weight="25%"
                  />
                  <ScoreBar
                    label="Completeness"
                    value={it.score_breakdown.completeness}
                    weight="15%"
                  />
                  <ScoreBar
                    label="Format compliance"
                    value={it.score_breakdown.format_compliance}
                    weight="10%"
                  />
                  <ScoreBar
                    label="Clarity & usability"
                    value={it.score_breakdown.clarity_usability}
                    weight="10%"
                  />
                </div>

                {/* Prompt */}
                <div>
                  <div className="text-xs font-medium text-gray-400 mb-1">Candidate Prompt</div>
                  <pre className="text-xs bg-gray-950 border border-gray-800 rounded-lg p-3 whitespace-pre-wrap text-gray-300 max-h-40 overflow-y-auto">
                    {it.candidate_prompt}
                  </pre>
                </div>

                {/* Output */}
                <div>
                  <div className="text-xs font-medium text-gray-400 mb-1">Simulated Output</div>
                  <pre className="text-xs bg-gray-950 border border-gray-800 rounded-lg p-3 whitespace-pre-wrap text-gray-300 max-h-40 overflow-y-auto">
                    {it.candidate_output}
                  </pre>
                </div>

                {/* Issues & Recommendations */}
                {it.issues.length > 0 && (
                  <div>
                    <div className="text-xs font-medium text-red-400 mb-1">Issues</div>
                    <ul className="text-xs text-gray-400 space-y-0.5 list-disc list-inside">
                      {it.issues.map((issue, i) => (
                        <li key={i}>{issue}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {it.recommendations.length > 0 && (
                  <div>
                    <div className="text-xs font-medium text-amber-400 mb-1">Recommendations</div>
                    <ul className="text-xs text-gray-400 space-y-0.5 list-disc list-inside">
                      {it.recommendations.map((rec, i) => (
                        <li key={i}>{rec}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Refiner info */}
                {it.refiner_action && (
                  <div className="pt-2 border-t border-gray-800">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-gray-400">Refiner Decision:</span>
                      <span className={`text-[10px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                        it.refiner_action === "stop"
                          ? "bg-emerald-900/60 text-emerald-400"
                          : "bg-blue-900/60 text-blue-400"
                      }`}>
                        {it.refiner_action}
                      </span>
                    </div>
                    {it.refiner_reason && (
                      <p className="text-xs text-gray-400 italic">{it.refiner_reason}</p>
                    )}
                    {it.changes_made && it.changes_made.length > 0 && (
                      <div className="mt-2">
                        <div className="text-xs font-medium text-indigo-400 mb-1">Changes Made</div>
                        <ul className="text-xs text-gray-400 space-y-0.5 list-disc list-inside">
                          {it.changes_made.map((change, i) => (
                            <li key={i}>{change}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
