"use client";

import React from 'react';
import { ArrowRight, Circle, PlayCircle, CheckCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Task {
    id: number;
    wbs_code?: string;
    title: string;
    status: string;
    dependencies: { target_id: number; relation: string; lag: number }[];
}

interface ProjectNetworkViewProps {
    tasks: Task[];
}

export default function ProjectNetworkView({ tasks }: ProjectNetworkViewProps) {
    if (tasks.length === 0) return <div className="p-20 text-center text-muted-foreground uppercase font-black text-[10px] tracking-[0.3em]">No topology detected in current deployment</div>;

    // Helper to format date
    const formatDate = (d: any) => d ? new Date(d).toLocaleDateString([], { month: 'short', day: 'numeric' }) : '--';

    return (
        <div className="p-6 bg-background h-full overflow-auto selection:bg-primary/30">
            <div className="flex flex-col gap-10">
                <div className="flex flex-wrap gap-10 items-start">
                    {tasks.map(task => {
                        const isCritical = (task as any).total_float === 0;
                        return (
                            <div key={task.id} className="relative">
                                {/* Card Node */}
                                <div className={cn(
                                    "w-64 border transition-all hover:ring-2 hover:ring-primary/50 cursor-crosshair bg-background/50 backdrop-blur-sm overflow-hidden",
                                    isCritical ? "border-red-500/50 shadow-[0_0_15px_rgba(239,68,68,0.1)]" : "border-border shadow-sm",
                                    task.status === 'completed' ? "border-emerald-500/30" :
                                        task.status === 'in_progress' ? "border-blue-500/50" : ""
                                )}>
                                    <div className={cn(
                                        "px-3 py-1.5 border-b text-[8px] font-black flex justify-between uppercase tracking-widest",
                                        isCritical ? "bg-red-500/10 text-red-500" : "bg-muted/30 text-muted-foreground/50"
                                    )}>
                                        <span className="flex items-center gap-2">
                                            <div className={cn("w-1 h-1 rounded-full", isCritical ? "bg-red-500 animate-pulse" : "bg-muted-foreground/50")} />
                                            {task.wbs_code || `LOG-${task.id}`}
                                        </span>
                                        {isCritical && <span>CRITICAL PATH</span>}
                                    </div>
                                    <div className="p-4">
                                        <h4 className="text-[11px] font-black uppercase tracking-tight mb-4 text-foreground/90 leading-tight h-8 line-clamp-2">{task.title}</h4>
                                        <div className="grid grid-cols-2 gap-1.5 font-mono text-[7px] font-bold uppercase">
                                            <div className="p-1 px-2 border border-border/50 bg-muted/10 flex justify-between">
                                                <span className="opacity-40">ES:</span>
                                                <span>{formatDate((task as any).early_start)}</span>
                                            </div>
                                            <div className="p-1 px-2 border border-border/50 bg-muted/10 flex justify-between">
                                                <span className="opacity-40">EF:</span>
                                                <span>{formatDate((task as any).early_finish)}</span>
                                            </div>
                                            <div className="p-1 px-2 border border-border/50 bg-muted/10 flex justify-between">
                                                <span className="opacity-40">LS:</span>
                                                <span>{formatDate((task as any).late_start)}</span>
                                            </div>
                                            <div className="p-1 px-2 border border-border/50 bg-muted/10 flex justify-between">
                                                <span className="opacity-40">LF:</span>
                                                <span>{formatDate((task as any).late_finish)}</span>
                                            </div>
                                        </div>
                                        <div className={cn(
                                            "mt-3 text-[9px] font-black uppercase tracking-widest text-center py-1 border-t border-border/50",
                                            isCritical ? "text-red-400" : "text-primary/70"
                                        )}>
                                            Float Segment: {(task as any).total_float?.toFixed(1) || '0.0'}H
                                        </div>
                                    </div>
                                </div>

                                {/* Link Indicator */}
                                {task.dependencies?.length > 0 && (
                                    <div className="absolute -left-7 top-1/2 -translate-y-1/2 opacity-20 group">
                                        <ArrowRight className="w-5 h-5 text-primary transition-transform group-hover:translate-x-1" />
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            </div>

            <div className="mt-24 border-t border-border/20 pt-10 text-center select-none opacity-20 hover:opacity-40 transition-opacity">
                <p className="text-[10px] font-black uppercase tracking-[0.5em] text-primary">System Topology Trace Log</p>
                <div className="h-40 flex items-center justify-center">
                    <div className="w-full max-w-2xl flex justify-around items-end gap-1.5 h-16">
                        {Array(32).fill(0).map((_, i) => (
                            <div key={i} className="bg-primary/40 w-0.5 rounded-t-full" style={{ height: `${20 + ((i * 13) % 80)}%` }} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
