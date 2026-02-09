import { useState } from "react";
import type { OptimizationRequest, WorkflowState } from "../types/api";

interface Props {
  onSubmit: (request: OptimizationRequest) => void;
  onReset: () => void;
  workflow: WorkflowState;
}

export function InputForm({ onSubmit, onReset, workflow }: Props) {
  const [data, setData] = useState("");
  const [objective, setObjective] = useState("");
  const [maxIterations, setMaxIterations] = useState(5);
  const [scoreThreshold, setScoreThreshold] = useState(85);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const isRunning = workflow.phase !== "idle" && workflow.phase !== "complete" && workflow.phase !== "error";

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!data.trim() || !objective.trim()) return;
    onSubmit({
      data: data.trim(),
      objective: objective.trim(),
      max_iterations: maxIterations,
      score_threshold: scoreThreshold,
    });
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          Data / Context
        </label>
        <textarea
          value={data}
          onChange={(e) => setData(e.target.value)}
          placeholder="Paste your input data, content, or context here..."
          rows={5}
          disabled={isRunning}
          className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none disabled:opacity-50 resize-y"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-1.5">
          Objective
        </label>
        <textarea
          value={objective}
          onChange={(e) => setObjective(e.target.value)}
          placeholder="Describe the desired outcome..."
          rows={3}
          disabled={isRunning}
          className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-2 text-sm text-gray-100 placeholder-gray-600 focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 outline-none disabled:opacity-50 resize-y"
        />
      </div>

      <button
        type="button"
        onClick={() => setShowAdvanced(!showAdvanced)}
        className="text-xs text-gray-500 hover:text-gray-300 text-left transition-colors w-fit"
      >
        {showAdvanced ? "\u25B2" : "\u25BC"} Advanced settings
      </button>

      {showAdvanced && (
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs text-gray-400 mb-1">
              Max iterations
            </label>
            <input
              type="number"
              min={1}
              max={20}
              value={maxIterations}
              onChange={(e) => setMaxIterations(Number(e.target.value))}
              disabled={isRunning}
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm text-gray-100 focus:border-indigo-500 outline-none disabled:opacity-50"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">
              Score threshold
            </label>
            <input
              type="number"
              min={0}
              max={100}
              value={scoreThreshold}
              onChange={(e) => setScoreThreshold(Number(e.target.value))}
              disabled={isRunning}
              className="w-full rounded-lg border border-gray-700 bg-gray-900 px-3 py-1.5 text-sm text-gray-100 focus:border-indigo-500 outline-none disabled:opacity-50"
            />
          </div>
        </div>
      )}

      <div className="flex gap-2 pt-1">
        <button
          type="submit"
          disabled={isRunning || !data.trim() || !objective.trim()}
          className="flex-1 rounded-lg bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
        >
          {isRunning ? (
            <span className="flex items-center justify-center gap-2">
              <span className="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin-slow" />
              Optimizing...
            </span>
          ) : (
            "Optimize Prompt"
          )}
        </button>

        {(workflow.phase === "complete" || workflow.phase === "error") && (
          <button
            type="button"
            onClick={onReset}
            className="rounded-lg border border-gray-600 px-4 py-2.5 text-sm text-gray-300 hover:bg-gray-800 transition-colors"
          >
            Reset
          </button>
        )}
      </div>
    </form>
  );
}
