import { ReactFlowProvider } from "@xyflow/react";
import { FlaskConical } from "lucide-react";
import { Link } from "react-router-dom";
import { useOptimization } from "./hooks/useOptimization";
import { InputForm } from "./components/InputForm";
import { WorkflowGraph } from "./components/WorkflowGraph";
import { StatusHeader } from "./components/StatusHeader";
import { IterationPanel } from "./components/IterationPanel";
import { ResultBanner } from "./components/ResultBanner";

export default function App() {
  const { state: workflow, start, reset } = useOptimization();

  return (
    <ReactFlowProvider>
      <div className="min-h-screen flex flex-col">
        {/* Top bar */}
        <header className="border-b border-gray-800 px-6 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-2.5">
            <FlaskConical className="w-5 h-5 text-indigo-500" />
            <h1 className="text-lg font-bold tracking-tight text-gray-100">
              TriReason
            </h1>
            <span className="text-xs text-gray-600 ml-1">
              Prompt Optimization System
            </span>
          </div>
          {workflow.runId && (
            <span className="text-[10px] font-mono text-gray-700">
              {workflow.runId}
            </span>
          )}
          <Link
            to="/prompts"
            className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors ml-4"
          >
            View Agent Prompts
          </Link>
        </header>

        {/* Main layout */}
        <div className="flex-1 flex overflow-hidden">
          {/* Left sidebar - Input */}
          <aside className="w-96 shrink-0 border-r border-gray-800 p-5 overflow-y-auto flex flex-col gap-5">
            <div>
              <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                Configuration
              </h2>
              <InputForm
                onSubmit={start}
                onReset={reset}
                workflow={workflow}
              />
            </div>

            {/* Error display */}
            {workflow.error && (
              <div className="rounded-lg border border-red-500/40 bg-red-950/20 p-3">
                <p className="text-xs text-red-400">{workflow.error}</p>
              </div>
            )}
          </aside>

          {/* Center + Right */}
          <main className="flex-1 flex flex-col overflow-hidden">
            {/* Status bar */}
            <div className="px-5 py-3 border-b border-gray-800 shrink-0">
              <StatusHeader workflow={workflow} />
            </div>

            {/* Workflow graph */}
            <div className="h-[340px] shrink-0 p-4">
              <WorkflowGraph workflow={workflow} />
            </div>

            {/* Bottom section - Results */}
            <div className="flex-1 overflow-y-auto border-t border-gray-800 p-5 space-y-4">
              <ResultBanner workflow={workflow} />

              <div>
                <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider mb-3">
                  Iterations
                </h2>
                <IterationPanel iterations={workflow.iterations} />
              </div>
            </div>
          </main>
        </div>
      </div>
    </ReactFlowProvider>
  );
}
