import type { WorkflowState } from "../types/api";

interface Props {
  workflow: WorkflowState;
}

const PHASE_LABELS: Record<WorkflowState["phase"], string> = {
  idle: "Ready to optimize",
  generating: "Generator is crafting a prompt...",
  critiquing: "Critic is evaluating output...",
  refining: "Refiner is improving the prompt...",
  complete: "Optimization complete",
  error: "An error occurred",
};

export function StatusHeader({ workflow }: Props) {
  const isRunning =
    workflow.phase !== "idle" &&
    workflow.phase !== "complete" &&
    workflow.phase !== "error";

  return (
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-3">
        {isRunning && (
          <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
        )}
        {workflow.phase === "complete" && (
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
        )}
        {workflow.phase === "error" && (
          <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
        )}
        <span className="text-sm text-gray-300">
          {PHASE_LABELS[workflow.phase]}
        </span>
      </div>

      {workflow.currentIteration > 0 && (
        <div className="flex items-center gap-4 text-xs text-gray-500">
          <span>
            Iteration{" "}
            <span className="font-mono text-gray-300">{workflow.currentIteration}</span>
          </span>
          {workflow.bestScore != null && (
            <span>
              Best score{" "}
              <span className="font-mono text-indigo-400">
                {workflow.bestScore.toFixed(1)}
              </span>
            </span>
          )}
        </div>
      )}
    </div>
  );
}
