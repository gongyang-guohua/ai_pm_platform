"use client";

import React from 'react';
import { CheckCircle2, Clock, AlertTriangle, MoreVertical, Link as LinkIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export default function TaskListView({ projects, onDeleteTask }: { projects: any[], onDeleteTask?: (id: number) => void }) {
    // Flatten tasks from all projects
    const allTasks = projects.flatMap(p => p.tasks.map((t: any) => ({ ...t, projectName: p.title })));

    return (
        <div className="space-y-6 animate-in fade-in duration-700 max-w-7xl mx-auto">
            <div className="flex justify-between items-center border-b border-border pb-6">
                <div>
                    <h2 className="text-2xl font-black tracking-tighter uppercase italic">Workfront Master Task List</h2>
                    <p className="text-muted-foreground text-[10px] uppercase font-mono tracking-widest">Global Operations Log • {allTasks.length} Live Tasks</p>
                </div>
            </div>

            <div className="bg-card border border-border">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-muted/50 border-b border-border text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground">
                            <th className="px-6 py-4">WBS</th>
                            <th className="px-6 py-4">Type</th>
                            <th className="px-6 py-4">Context & Title</th>
                            <th className="px-6 py-4">Pri</th>
                            <th className="px-6 py-4">Status</th>
                            <th className="px-6 py-4">Planned (S/E)</th>
                            <th className="px-6 py-4">Actual (S/E)</th>
                            <th className="px-6 py-4 text-right">Manage</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                        {allTasks.map((t: any, i: number) => (
                            <tr key={i} className="hover:bg-primary/[0.03] transition-colors group">
                                <td className="px-6 py-4 font-mono text-[10px] text-primary/70">{t.wbs_code || `T-${t.id?.toString().padStart(3, '0') || '000'}`}</td>
                                <td className="px-6 py-4">
                                    <span className={cn(
                                        "text-[8px] font-black px-1 py-0.5 border uppercase",
                                        t.task_type === 'milestone' ? "border-amber-500 text-amber-500 bg-amber-500/10" : "border-muted-foreground/30 text-muted-foreground"
                                    )}>
                                        {t.task_type === 'milestone' ? 'MS' : 'TSK'}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <div className="flex items-center gap-2 mb-1">
                                        <LinkIcon className="w-2.5 h-2.5 text-primary opacity-50" />
                                        <span className="text-[9px] font-bold text-primary uppercase truncate max-w-[120px]">{t.projectName}</span>
                                    </div>
                                    <p className="text-sm font-bold uppercase tracking-tight">{t.title}</p>
                                    <p className="text-[9px] text-muted-foreground line-clamp-1">{t.description}</p>
                                </td>
                                <td className="px-6 py-4">
                                    <span className={cn(
                                        "text-[9px] font-bold px-1.5 py-0.5 rounded-sm uppercase italic",
                                        t.priority === 'Critical' ? "bg-red-500/20 text-red-500" :
                                            t.priority === 'High' ? "bg-orange-500/20 text-orange-500" :
                                                t.priority === 'Medium' ? "bg-blue-500/20 text-blue-500" : "bg-muted text-muted-foreground"
                                    )}>
                                        {t.priority || 'MED'}
                                    </span>
                                </td>
                                <td className="px-6 py-4">
                                    <div className={cn(
                                        "inline-flex items-center gap-1.5 px-2 py-0.5 border text-[9px] font-black uppercase",
                                        t.status === 'completed' ? "border-emerald-500/50 text-emerald-500" :
                                            t.status === 'in_progress' ? "border-blue-500/50 text-blue-500" :
                                                t.status === 'stalled' ? "border-orange-500/50 text-orange-500" :
                                                    t.status === 'cancelled' ? "border-red-500/50 text-red-500" :
                                                        "border-muted-foreground/30 text-muted-foreground"
                                    )}>
                                        {t.status}
                                    </div>
                                </td>
                                <td className="px-6 py-4 font-mono text-[9px] tabular-nums leading-tight text-muted-foreground min-w-[100px]">
                                    <div>{t.planned_start ? new Date(t.planned_start).toLocaleDateString() : '---'}</div>
                                    <div>{t.planned_end ? new Date(t.planned_end).toLocaleDateString() : '---'}</div>
                                </td>
                                <td className="px-6 py-4 font-mono text-[9px] tabular-nums leading-tight text-primary/70 italic min-w-[100px]">
                                    <div>{t.actual_start ? new Date(t.actual_start).toLocaleDateString() : '---'}</div>
                                    <div>{t.actual_end ? new Date(t.actual_end).toLocaleDateString() : '---'}</div>
                                </td>
                                <td className="px-6 py-4 text-right flex items-center justify-end gap-2">
                                    <button
                                        onClick={() => onDeleteTask && onDeleteTask(t.id)}
                                        className="p-1.5 hover:bg-red-500/10 border border-red-500/30 text-red-500/50 transition-colors"
                                        title="Terminate Task"
                                    >
                                        <AlertTriangle className="w-3 h-3" />
                                    </button>
                                    <button className="p-1.5 hover:bg-muted border border-border transition-colors">
                                        <MoreVertical className="w-3 h-3" />
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
