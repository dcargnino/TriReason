import { useCallback, useRef, useState } from "react";
import type {
  CompletionEvent,
  IterationEvent,
  OptimizationRequest,
  WorkflowState,
} from "../types/api";

const INITIAL_STATE: WorkflowState = {
  phase: "idle",
  generator: "idle",
  critic: "idle",
  refiner: "idle",
  currentIteration: 0,
  iterations: [],
  bestScore: null,
  bestPrompt: null,
  stopReason: null,
  runId: null,
  error: null,
};

export function useOptimization() {
  const [state, setState] = useState<WorkflowState>(INITIAL_STATE);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    abortRef.current = null;
    setState(INITIAL_STATE);
  }, []);

  const start = useCallback(async (request: OptimizationRequest) => {
    reset();

    setState((s) => ({
      ...s,
      phase: "generating",
      generator: "active",
      critic: "idle",
      refiner: "idle",
    }));

    const abort = new AbortController();
    abortRef.current = abort;

    try {
      const response = await fetch("/api/v1/optimize/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(request),
        signal: abort.signal,
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        let currentData = "";

        for (const line of lines) {
          if (line.startsWith("event:")) {
            currentEvent = line.slice(6).trim();
          } else if (line.startsWith("data:")) {
            currentData = line.slice(5).trim();
          } else if (line === "" && currentData) {
            handleSSEMessage(currentEvent, currentData);
            currentEvent = "";
            currentData = "";
          }
        }
      }
    } catch (err) {
      if ((err as Error).name === "AbortError") return;
      setState((s) => ({
        ...s,
        phase: "error",
        generator: "error",
        critic: "error",
        refiner: "error",
        error: err instanceof Error ? err.message : "Unknown error",
      }));
    }
  }, [reset]);

  function handleSSEMessage(event: string, data: string) {
    try {
      const parsed = JSON.parse(data);

      if (event === "iteration" || parsed.event === "iteration") {
        const iterEvent = parsed as IterationEvent;
        const iteration = iterEvent.iteration;

        setState((s) => {
          const iterations = [...s.iterations, iteration];
          const needsRefine = !iteration.passed;

          return {
            ...s,
            phase: needsRefine ? "refining" : "critiquing",
            generator: "done",
            critic: "done",
            refiner: needsRefine ? "active" : "idle",
            currentIteration: iteration.iteration_number,
            iterations,
            bestScore: iteration.is_best_so_far
              ? iteration.score_total
              : s.bestScore,
            bestPrompt: iteration.is_best_so_far
              ? iteration.candidate_prompt
              : s.bestPrompt,
            runId: iterEvent.run_id,
          };
        });

        if (!iteration.passed) {
          setTimeout(() => {
            setState((s) => {
              if (s.phase === "complete" || s.phase === "error") return s;
              return {
                ...s,
                phase: "generating",
                generator: "active",
                critic: "idle",
                refiner: "done",
              };
            });
          }, 600);
        }
      } else if (event === "complete" || parsed.event === "complete") {
        const complEvent = parsed as CompletionEvent;
        setState((s) => ({
          ...s,
          phase: "complete",
          generator: "done",
          critic: "done",
          refiner: "done",
          bestScore: complEvent.best_score,
          bestPrompt: complEvent.best_prompt,
          stopReason: complEvent.stop_reason,
          runId: complEvent.run_id,
        }));
      }
    } catch {
      // ignore malformed SSE
    }
  }

  return { state, start, reset };
}
