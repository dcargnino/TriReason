import { useEffect, useMemo } from "react";
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  type Edge,
  type Node,
  MarkerType,
  useNodesState,
  useEdgesState,
} from "@xyflow/react";
import { AgentNode, type AgentNodeData } from "./AgentNode";
import type { WorkflowState } from "../types/api";

const nodeTypes = { agent: AgentNode };

interface Props {
  workflow: WorkflowState;
}

function buildNodes(workflow: WorkflowState): Node<AgentNodeData>[] {
  return [
    {
      id: "user",
      type: "agent",
      position: { x: 0, y: 140 },
      data: {
        label: "User Input",
        role: "Data + Objective",
        status: workflow.phase === "idle" ? "idle" : "done",
        icon: "\u{1F4CB}",
      },
    },
    {
      id: "generator",
      type: "agent",
      position: { x: 280, y: 50 },
      data: {
        label: "Generator",
        role: "Prompt Designer",
        status: workflow.generator,
        icon: "\u{1F9E0}",
      },
    },
    {
      id: "critic",
      type: "agent",
      position: { x: 560, y: 50 },
      data: {
        label: "Critic",
        role: "Output Validator",
        status: workflow.critic,
        icon: "\u{1F50D}",
      },
    },
    {
      id: "refiner",
      type: "agent",
      position: { x: 420, y: 250 },
      data: {
        label: "Refiner",
        role: "Prompt Optimizer",
        status: workflow.refiner,
        icon: "\u{2728}",
      },
    },
    {
      id: "result",
      type: "agent",
      position: { x: 840, y: 140 },
      data: {
        label: "Best Prompt",
        role: workflow.bestScore != null ? `Score: ${workflow.bestScore.toFixed(1)}` : "Waiting...",
        status: workflow.phase === "complete" ? "done" : "idle",
        icon: "\u{1F3C6}",
      },
    },
  ];
}

function buildEdges(workflow: WorkflowState): Edge[] {
  const activeColor = "#6366f1";
  const doneColor = "#10b981";
  const idleColor = "#374151";

  function edgeColor(source: string): string {
    if (workflow.phase === "complete") return doneColor;
    if (source === "user" && workflow.phase !== "idle") return doneColor;
    if (source === "generator" && (workflow.critic !== "idle" || workflow.refiner !== "idle"))
      return doneColor;
    if (source === "generator" && workflow.generator === "active") return activeColor;
    if (source === "critic" && workflow.refiner === "active") return activeColor;
    if (source === "critic" && workflow.phase === "complete") return doneColor;
    if (source === "refiner" && workflow.generator === "active" && workflow.currentIteration > 0)
      return activeColor;
    return idleColor;
  }

  const base = {
    markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
    style: { strokeWidth: 2 },
  };

  return [
    {
      id: "e-user-gen",
      source: "user",
      target: "generator",
      ...base,
      style: { ...base.style, stroke: edgeColor("user") },
      animated: workflow.generator === "active",
    },
    {
      id: "e-gen-crit",
      source: "generator",
      target: "critic",
      ...base,
      style: { ...base.style, stroke: edgeColor("generator") },
      animated: workflow.critic === "active",
    },
    {
      id: "e-crit-ref",
      source: "critic",
      target: "refiner",
      ...base,
      style: { ...base.style, stroke: edgeColor("critic") },
      animated: workflow.refiner === "active",
      label: workflow.refiner === "active" ? "FAIL" : "",
      labelStyle: { fill: "#ef4444", fontWeight: 700, fontSize: 11 },
    },
    {
      id: "e-ref-gen",
      source: "refiner",
      target: "generator",
      ...base,
      style: { ...base.style, stroke: edgeColor("refiner") },
      animated: workflow.generator === "active" && workflow.currentIteration > 0,
      label: workflow.currentIteration > 0 ? `Iter ${workflow.currentIteration + 1}` : "",
      labelStyle: { fill: "#a78bfa", fontWeight: 600, fontSize: 10 },
    },
    {
      id: "e-crit-result",
      source: "critic",
      target: "result",
      ...base,
      style: { ...base.style, stroke: workflow.phase === "complete" ? doneColor : idleColor },
      animated: false,
      label: workflow.phase === "complete" ? "PASS" : "",
      labelStyle: { fill: "#10b981", fontWeight: 700, fontSize: 11 },
    },
  ];
}

export function WorkflowGraph({ workflow }: Props) {
  const initialNodes = useMemo(() => buildNodes(workflow), []);
  const initialEdges = useMemo(() => buildEdges(workflow), []);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(buildNodes(workflow));
    setEdges(buildEdges(workflow));
  }, [workflow, setNodes, setEdges]);

  return (
    <div className="h-full w-full rounded-xl border border-gray-800 bg-gray-900/50 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.3 }}
        proOptions={{ hideAttribution: true }}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={false}
        minZoom={0.5}
        maxZoom={1.5}
      >
        <Background variant={BackgroundVariant.Dots} color="#1e293b" gap={20} size={1} />
        <Controls
          showInteractive={false}
          className="!bg-gray-800 !border-gray-700 !rounded-lg [&>button]:!bg-gray-800 [&>button]:!border-gray-700 [&>button]:!text-gray-300 [&>button:hover]:!bg-gray-700"
        />
      </ReactFlow>
    </div>
  );
}
