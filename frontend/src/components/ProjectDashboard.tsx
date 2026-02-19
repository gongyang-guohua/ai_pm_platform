"use client";

import React, { useEffect, useState } from 'react';
import { LayoutDashboard, PlusCircle, LayoutGrid, List, Kanban, GanttChartSquare, Package, ChevronRight, TrendingUp } from "lucide-react";
import { cn } from "@/lib/utils";
import axios from 'axios';

interface Project {
    id: number;
    title: string;
    description: string;
    industry: string;
    status: string;
    created_at: string;
}

export default function ProjectDashboard({ onSelectProject, onCreateNew }: { onSelectProject: (id: number) => void, onCreateNew: () => void }) {
    const [projects, setProjects] = useState<Project[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchProjects = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001/api/v1';
                const res = await axios.get(`${apiUrl}/projects/`);
                setProjects(res.data);
            } catch (err) {
                console.error("Failed to fetch projects", err);
            } finally {
                setLoading(false);
            }
        };
        fetchProjects();
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
        );
    }

    return (
        <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto">
            <div className="flex justify-between items-end border-b border-border pb-6">
                <div>
                    <h2 className="text-4xl font-black tracking-tighter uppercase italic">Construction / Control Center</h2>
                    <p className="text-muted-foreground mt-1 font-mono text-xs uppercase tracking-widest">Live Project Inventory • {projects.length} Active Workfronts</p>
                </div>
                <button
                    onClick={onCreateNew}
                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-bold hover:opacity-90 transition-all uppercase text-xs tracking-tighter"
                >
                    <PlusCircle className="w-4 h-4" />
                    Init New Project
                </button>
            </div>

            {/* Bloomberg-style Stats Bar */}
            <div className="grid grid-cols-2 md:grid-cols-4 border border-border bg-card divide-x divide-y md:divide-y-0 divide-border overflow-hidden">
                {[
                    { label: "Total Committed Cost", value: "$4.2M", trend: "+2.4%", color: "text-emerald-500" },
                    { label: "Active Workfronts", value: projects.length.toString(), trend: "Stable", color: "text-blue-500" },
                    { label: "SPI (Schedule)", value: "1.02", trend: "On-Track", color: "text-emerald-500" },
                    { label: "CPI (Cost)", value: "0.98", trend: "Alert", color: "text-amber-500" },
                ].map((stat, i) => (
                    <div key={i} className="p-4 flex flex-col justify-between">
                        <span className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider">{stat.label}</span>
                        <div className="flex items-end justify-between mt-2">
                            <span className="text-2xl font-black tabular-nums tracking-tighter">{stat.value}</span>
                            <span className={cn("text-[10px] font-bold tabular-nums", stat.color)}>{stat.trend}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* Project Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-1">
                {projects.map((project) => (
                    <div
                        key={project.id}
                        onClick={() => onSelectProject(project.id)}
                        className="group bg-card border border-border p-5 hover:border-primary cursor-pointer transition-all flex flex-col justify-between min-h-[160px]"
                    >
                        <div className="space-y-2">
                            <div className="flex justify-between items-start">
                                <span className="text-[10px] font-bold px-2 py-0.5 border border-muted-foreground/30 text-muted-foreground uppercase tracking-widest">
                                    {project.industry || "General"}
                                </span>
                                <TrendingUp className="w-4 h-4 text-emerald-500 opacity-50" />
                            </div>
                            <h3 className="text-xl font-bold tracking-tight group-hover:text-primary transition-colors uppercase leading-tight">
                                {project.title}
                            </h3>
                            <p className="text-xs text-muted-foreground line-clamp-2 leading-relaxed">
                                {project.description}
                            </p>
                        </div>
                        <div className="flex justify-between items-center mt-4 pt-4 border-t border-border/50">
                            <div className="flex gap-2">
                                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500" title="Active" />
                                <span className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">{project.status}</span>
                            </div>
                            <ChevronRight className="w-4 h-4 text-muted-foreground group-hover:translate-x-1 transition-transform" />
                        </div>
                    </div>
                ))}

                {projects.length === 0 && (
                    <div className="col-span-full py-20 border border-dashed border-border flex flex-col items-center justify-center text-center space-y-4">
                        <div className="w-12 h-12 border border-border flex items-center justify-center">
                            <LayoutDashboard className="w-6 h-6 text-muted-foreground" />
                        </div>
                        <div className="space-y-1">
                            <p className="font-bold uppercase tracking-tighter">Empty Portfolio</p>
                            <p className="text-xs text-muted-foreground max-w-[240px]">No project vectors detected in the current terminal session.</p>
                        </div>
                        <button
                            onClick={onCreateNew}
                            className="bg-primary text-primary-foreground px-6 py-2 text-xs font-bold uppercase tracking-tighter hover:opacity-90"
                        >
                            Execute Initial Deployment
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
