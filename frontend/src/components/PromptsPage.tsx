import { FlaskConical } from "lucide-react";
import { Link } from "react-router-dom";

interface AgentPrompt {
  name: string;
  role: string;
  prompt: string;
}

const AGENT_PROMPTS: AgentPrompt[] = [
  {
    name: "Generator",
    role: "Candidate Prompt Generator",
    prompt: `You are a prompt engineering expert. Your task is to generate an improved prompt based on the provided data, objective, and constraints.

Data: {data}
Objective: {objective}
Constraints: {constraints}

Generate a clear, specific, and actionable prompt that will help achieve the stated objective while respecting all constraints.`,
  },
  {
    name: "Critic",
    role: "Quality Assurance Critic",
    prompt: `You are a critical evaluator. Your task is to analyze the candidate prompt and its output against the objective and constraints.

Evaluate on the following dimensions:
1. Objective Fulfillment - Does the prompt address the stated goal?
2. Correctness & Faithfulness - Is the output accurate and grounded in the data?
3. Completeness - Are all required aspects covered?
4. Format Compliance - Does the output follow the required format?
5. Clarity & Usability - Is the output clear and actionable?

Provide a score (0-10) for each dimension and detailed feedback on issues and recommendations for improvement.`,
  },
  {
    name: "Refiner",
    role: "Prompt Refinement Specialist",
    prompt: `You are a prompt refinement specialist. Your task is to improve the candidate prompt based on the critic's feedback.

Original Prompt: {candidate_prompt}
Critic Feedback: {critic_feedback}
Issues: {issues}
Recommendations: {recommendations}

Generate an improved version of the prompt that addresses all identified issues and incorporates the recommendations while maintaining clarity and focus.`,
  },
];

export default function PromptsPage() {
  return (
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
        <Link
          to="/"
          className="text-xs text-indigo-400 hover:text-indigo-300 transition-colors"
        >
          ← Back to App
        </Link>
      </header>

      {/* Main content */}
      <main className="flex-1 p-6">
        <h2 className="text-xl font-bold text-gray-100 mb-6">
          Agent Prompts
        </h2>

        <div className="grid grid-cols-3 gap-4">
          {AGENT_PROMPTS.map((agent) => (
            <div
              key={agent.name}
              className="rounded-xl border border-gray-800 bg-gray-950/50 overflow-hidden flex flex-col"
            >
              {/* Header */}
              <div className="px-4 py-3 border-b border-gray-800 bg-gray-900/50">
                <h3 className="text-sm font-semibold text-indigo-400">
                  {agent.name}
                </h3>
                <p className="text-xs text-gray-500 mt-0.5">
                  {agent.role}
                </p>
              </div>

              {/* Prompt content */}
              <div className="flex-1 p-4">
                <pre className="text-xs text-gray-300 whitespace-pre-wrap font-mono leading-relaxed">
                  {agent.prompt}
                </pre>
              </div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}
