export interface ScoreBreakdown {
  objective_fulfillment: number;
  correctness_faithfulness: number;
  completeness: number;
  format_compliance: number;
  clarity_usability: number;
}

export interface IterationResult {
  iteration_number: number;
  candidate_prompt: string;
  candidate_output: string;
  score_total: number;
  score_breakdown: ScoreBreakdown;
  passed: boolean;
  issues: string[];
  recommendations: string[];
  is_best_so_far: boolean;
  refiner_action?: "stop" | "continue";
  refiner_reason?: string;
  changes_made?: string[];
}

export interface OptimizationRequest {
  data: string;
  objective: string;
  constraints?: Record<string, unknown>;
  max_iterations: number;
  score_threshold: number;
}

export interface OptimizationResponse {
  run_id: string;
  status: string;
  total_iterations: number;
  best_score: number | null;
  best_prompt: string | null;
  stop_reason: string | null;
  iterations: IterationResult[];
}

export interface IterationEvent {
  event: "iteration";
  run_id: string;
  iteration: IterationResult;
}

export interface CompletionEvent {
  event: "complete";
  run_id: string;
  best_score: number | null;
  best_prompt: string | null;
  stop_reason: string | null;
  total_iterations: number;
}

export type AgentStatus = "idle" | "active" | "done" | "error";

export interface WorkflowState {
  phase: "idle" | "generating" | "critiquing" | "refining" | "complete" | "error";
  generator: AgentStatus;
  critic: AgentStatus;
  refiner: AgentStatus;
  currentIteration: number;
  iterations: IterationResult[];
  bestScore: number | null;
  bestPrompt: string | null;
  stopReason: string | null;
  runId: string | null;
  error: string | null;
}
