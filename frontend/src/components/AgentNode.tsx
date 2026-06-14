import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import { Check, ClipboardList, Brain, Search, Sparkles, Trophy } from "lucide-react";
import type { AgentStatus } from "../types/api";

export type AgentNodeData = {
  label: string;
  role: string;
  status: AgentStatus;
  icon: string;
};

type AgentNode = Node<AgentNodeData, "agent">;

const STATUS_STYLES: Record<AgentStatus, string> = {
  idle: "border-gray-700 bg-gray-900/80",
  active: "border-indigo-500 bg-indigo-950/80 agent-node-active",
  done: "border-emerald-500 bg-emerald-950/60",
  error: "border-red-500 bg-red-950/60",
};

const STATUS_BADGE: Record<AgentStatus, { text: string; color: string }> = {
  idle: { text: "Idle", color: "text-gray-500" },
  active: { text: "Running", color: "text-indigo-400" },
  done: { text: "Done", color: "text-emerald-400" },
  error: { text: "Error", color: "text-red-400" },
};

const ICON_MAP: Record<string, React.ReactNode> = {
  clipboard: <ClipboardList className="w-6 h-6" />,
  brain: <Brain className="w-6 h-6" />,
  search: <Search className="w-6 h-6" />,
  sparkles: <Sparkles className="w-6 h-6" />,
  trophy: <Trophy className="w-6 h-6" />,
};

export function AgentNode({ data }: NodeProps<AgentNode>) {
  const badge = STATUS_BADGE[data.status];
  const Icon = ICON_MAP[data.icon];

  return (
    <div
      className={`rounded-xl border-2 px-6 py-4 min-w-[180px] transition-all duration-500 ${STATUS_STYLES[data.status]}`}
    >
      <Handle type="target" position={Position.Left} className="!bg-gray-500" />

      <div className="flex items-center gap-3 mb-2">
        <span className="text-indigo-400">{Icon}</span>
        <div>
          <div className="font-bold text-sm text-gray-100">{data.label}</div>
          <div className="text-xs text-gray-400">{data.role}</div>
        </div>
      </div>

      <div className={`text-xs font-medium flex items-center gap-1.5 ${badge.color}`}>
        {data.status === "active" && (
          <span className="inline-block w-2 h-2 rounded-full bg-indigo-400 animate-spin-slow" />
        )}
        {data.status === "done" && <Check className="w-3 h-3" />}
        {badge.text}
      </div>

      <Handle type="source" position={Position.Right} className="!bg-gray-500" />
    </div>
  );
}
