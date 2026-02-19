"use client";

import React from 'react';
import { Search, Filter, ArrowUpDown, ChevronRight, LayoutGrid, List as ListIcon, AlertTriangle, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

export default function ProjectListView({ projects, onSelectProject, onDeleteProject }: { projects: any[], onSelectProject: (id: number) => void, onDeleteProject?: (id: number) => void }) {
    return (
        <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto selection:bg-primary/30">
            <div className="flex justify-between items-center border-b border-border pb-8">
                <div>
                    <h2 className="text-3xl font-black tracking-tighter uppercase text-foreground leading-none">Project Inventory</h2>
                    <p className="text-muted-foreground text-[10px] uppercase font-mono tracking-[0.3em] mt-3 opacity-50">Operational Database Matrix • {String(projects.length).padStart(3, '0')} ACTIVE_ENTRIES</p>
                </div>
                <div className="flex items-center gap-4">
                    <div className="relative group">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-muted-foreground group-focus-within:text-primary transition-colors" />
                        <input
                            type="text"
                            placeholder="SEARCH_REGISTRY..."
                            className="pl-10 pr-4 py-2 bg-muted/10 border border-border text-[10px] font-mono tracking-widest focus:outline-none focus:border-primary/50 focus:bg-muted/20 w-64 transition-all"
                        />
                    </div>
                </div>
            </div>

            <div className="bg-background border border-border overflow-hidden">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="bg-muted/10 border-b border-border text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">
                            <th className="px-8 py-5 font-black"># REGISTRY_ID</th>
                            <th className="px-8 py-5 font-black">OS_TITLE / SCOPE_SPEC</th>
                            <th className="px-8 py-5 font-black">SECTOR_ID</th>
                            <th className="px-8 py-5 font-black">OPS_STATUS</th>
                            <th className="px-8 py-5 font-black">PERF_SPI</th>
                            <th className="px-8 py-5 font-black">ALLOC_LOAD</th>
                            <th className="px-8 py-5 text-right font-black">OP_CMD</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border/50">
                        {projects.map((p) => (
                            <tr
                                key={p.id}
                                onClick={() => onSelectProject(p.id)}
                                className="group hover:bg-primary/5 transition-colors cursor-pointer"
                            >
                                <td className="px-8 py-5 font-mono text-[11px] text-muted-foreground/40 italic">P-X{p.id.toString().padStart(5, '0')}</td>
                                <td className="px-8 py-5">
                                    <p className="text-sm font-black uppercase tracking-tighter text-foreground/90 group-hover:text-primary transition-colors leading-none">{p.title}</p>
                                    <p className="text-[9px] text-muted-foreground/50 tracking-widest uppercase mt-2 line-clamp-1 truncate max-w-xs">{p.description || "NO_DESCRIPTION_PROVIDED"}</p>
                                </td>
                                <td className="px-8 py-5">
                                    <span className="text-[9px] font-black px-2 py-0.5 border border-border bg-muted/10 text-muted-foreground uppercase tracking-widest group-hover:border-primary/30 group-hover:text-primary/70 transition-colors">
                                        {p.industry || "GENERAL"}
                                    </span>
                                </td>
                                <td className="px-8 py-5">
                                    <div className="flex items-center gap-3">
                                        <div className={cn("w-1.5 h-1.5 rounded-none",
                                            p.status === 'planning' ? "bg-blue-500" :
                                                p.status === 'active' ? "bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]" : "bg-muted-foreground/30"
                                        )} />
                                        <span className="text-[10px] font-black uppercase tracking-widest text-foreground/80">{p.status}</span>
                                    </div>
                                </td>
                                <td className="px-8 py-5 font-mono text-[11px]">
                                    <div className="flex items-center gap-2 text-emerald-500 font-black">
                                        <Activity className="w-3 h-3 opacity-40" />
                                        1.02
                                    </div>
                                </td>
                                <td className="px-8 py-5">
                                    <div className="w-20 h-0.5 bg-muted/20 overflow-hidden">
                                        <div className="h-full bg-primary/40 w-3/4 group-hover:bg-primary transition-all duration-500" />
                                    </div>
                                </td>
                                <td className="px-8 py-5 text-right flex items-center justify-end gap-5">
                                    <button
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            if (onDeleteProject) onDeleteProject(p.id);
                                        }}
                                        className="p-2 border border-border text-muted-foreground/30 hover:text-red-500 hover:border-red-500/50 hover:bg-red-500/5 transition-all"
                                        title="Terminate Record"
                                    >
                                        <AlertTriangle className="w-3.5 h-3.5" />
                                    </button>
                                    <ChevronRight className="w-4 h-4 text-muted-foreground/20 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {projects.length === 0 && (
                    <div className="p-20 text-center text-muted-foreground text-[10px] uppercase font-black tracking-[0.5em] opacity-30">Registry Empty: Initialize New Deployment Cluster</div>
                )}
            </div>
        </div>
    );
}
