"use client";

import React from 'react';
import {
    BarChart3, TrendingUp, AlertTriangle, Users,
    Calendar, CheckCircle2, Clock, DollarSign,
    ArrowUpRight, ArrowDownRight, Activity
} from "lucide-react";
import { cn } from "@/lib/utils";

import axios from 'axios';

export default function ManagementDashboard({ projects = [], onUpdateView, onSelectProject }: { projects: any[], onUpdateView: (view: "projects" | "tasks") => void, onSelectProject: (id: number) => void }) {
    // Calculate Stats from Projects
    const totalProjects = projects.length;
    const planningProjects = projects.filter(p => p.status === 'planning').length;
    const activeProjects = projects.filter(p => p.status === 'active' || p.status === 'in_progress').length;
    const completedProjects = projects.filter(p => p.status === 'completed').length;

    const totalValue = totalProjects * 1500000;
    const overallCpi = 0.98;

    return (
        <div className="space-y-8 animate-in fade-in duration-700 max-w-7xl mx-auto pb-20 selection:bg-primary/30">
            {/* Control Center Header */}
            <div className="flex justify-between items-end border-b border-border pb-8">
                <div>
                    <h2 className="text-5xl font-black tracking-tighter uppercase leading-none text-foreground">Control Center</h2>
                    <p className="text-muted-foreground mt-3 font-mono text-[10px] uppercase tracking-[0.4em] opacity-50">Portfolio Intelligence Unit • Multi-Workfront Monitoring</p>
                </div>
                <div className="text-right">
                    <p className="text-[10px] font-black text-muted-foreground uppercase tracking-widest opacity-40">System Operational Status</p>
                    <div className="flex items-center gap-3 mt-2 justify-end">
                        <div className="w-2.5 h-2.5 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)] animate-pulse" />
                        <span className="text-[11px] font-black uppercase tracking-widest font-mono text-emerald-500">Nominal</span>
                    </div>
                </div>
            </div>

            {/* Top Tier KPIs */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-border border border-border">
                <KPICard
                    label="Portfolio Exposure"
                    value={`$${(totalValue / 1000000).toFixed(1)}M`}
                    trend="+4.2%"
                    icon={DollarSign}
                    color="primary"
                />
                <KPICard
                    label="Active Nodes"
                    value={activeProjects.toString()}
                    trend={`${Math.round(activeProjects / (totalProjects || 1) * 100)}% Utilization`}
                    icon={Activity}
                    color="emerald"
                />
                <KPICard
                    label="Aggregate CPI"
                    value={overallCpi.toString()}
                    trend="Target: 1.0"
                    icon={TrendingUp}
                    color="amber"
                />
                <KPICard
                    label="Queue Latency"
                    value={planningProjects.toString()}
                    trend="Pending Start"
                    icon={Clock}
                    color="blue"
                />
            </div>

            {/* Middle Row: Visualizations */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Cost Distribution Chart Mockup */}
                <div className="lg:col-span-2 bg-background border border-border p-8 relative overflow-hidden group">
                    <div className="flex justify-between items-start mb-10">
                        <div>
                            <h3 className="text-xl font-black uppercase tracking-tighter">Cost Burn Topology</h3>
                            <p className="text-[10px] text-muted-foreground font-mono uppercase tracking-widest opacity-50">Cumulative Cashflow Performance</p>
                        </div>
                        <Activity className="w-5 h-5 text-primary opacity-30" />
                    </div>

                    {/* Chart Mockup */}
                    <div className="h-64 flex items-end gap-1.5 relative pt-10">
                        <div className="absolute inset-0 border-l border-b border-border/30" />
                        {[40, 55, 45, 70, 85, 95, 80, 110, 130, 120, 150, 180].map((h, i) => (
                            <div key={i} className="flex-1 flex flex-col items-center group/bar relative">
                                <div
                                    className="w-full bg-primary/10 border-t border-primary/30 transition-all duration-500 group-hover/bar:bg-primary/30"
                                    style={{ height: `${h}px` }}
                                />
                                <div
                                    className="absolute bottom-0 w-full bg-emerald-500/20 border-t border-emerald-500/50 group-hover/bar:bg-emerald-500/40"
                                    style={{ height: `${h * 0.85}px` }}
                                />
                                <span className="mt-3 text-[8px] font-mono text-muted-foreground uppercase opacity-40">Q{i + 1}</span>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Status Breakdown */}
                <div className="bg-background border border-border p-8 flex flex-col">
                    <h3 className="text-xl font-black uppercase tracking-tighter mb-8 text-foreground">Global Matrix</h3>
                    <div className="flex-1 flex flex-col justify-around gap-6">
                        <StatusLine
                            label="Phase: Planning"
                            percent={totalProjects ? Math.round(planningProjects / totalProjects * 100) : 0}
                            color="bg-blue-500"
                            onClick={() => onUpdateView("projects")}
                        />
                        <StatusLine
                            label="Phase: Execution"
                            percent={totalProjects ? Math.round(activeProjects / totalProjects * 100) : 0}
                            color="bg-emerald-500"
                            onClick={() => onUpdateView("projects")}
                        />
                        <StatusLine
                            label="Phase: Archive"
                            percent={totalProjects ? Math.round(completedProjects / totalProjects * 100) : 0}
                            color="bg-amber-500"
                            onClick={() => onUpdateView("projects")}
                        />
                    </div>
                    <div className="mt-10 pt-6">
                        <button className="w-full text-[10px] font-black uppercase tracking-[0.2em] py-3 border border-border bg-muted/20 hover:bg-primary hover:text-primary-foreground transition-all">
                            Export System Logs
                        </button>
                    </div>
                </div>
            </div>

            {/* Bottom Row: Project Portfolio List */}
            <div className="bg-background border border-border">
                <div className="px-8 py-4 border-b border-border flex justify-between items-center bg-muted/10">
                    <h3 className="text-[10px] font-black uppercase tracking-[0.3em]">Operational Cluster List</h3>
                    <span className="text-[8px] font-mono text-muted-foreground uppercase opacity-40 tracking-widest">Real-time sync active [0ms]</span>
                </div>
                <div className="divide-y divide-border">
                    {projects.slice(0, 5).map((p, i) => (
                        <div
                            key={i}
                            onClick={() => onSelectProject(p.id)}
                            className="px-8 py-5 flex items-center justify-between hover:bg-primary/5 transition-colors cursor-pointer group"
                        >
                            <div className="flex items-center gap-6">
                                <div className="w-10 h-10 border border-border bg-muted/20 flex items-center justify-center font-black text-xs text-muted-foreground group-hover:border-primary group-hover:text-primary transition-colors italic">
                                    {String(p.id).padStart(2, '0')}
                                </div>
                                <div>
                                    <p className="text-sm font-black uppercase tracking-tighter text-foreground/90 leading-none">{p.title}</p>
                                    <p className="text-[9px] text-muted-foreground uppercase tracking-widest mt-1.5 opacity-60 font-medium">{p.industry} // {p.status}</p>
                                </div>
                            </div>
                            <div className="flex items-center gap-16 text-right">
                                <div className="hidden md:block">
                                    <p className="text-[8px] font-black text-muted-foreground uppercase tracking-widest opacity-40 mb-1">Schedule Variance</p>
                                    <p className="text-[11px] font-black font-mono text-emerald-500">+1.02 SPI</p>
                                </div>
                                <div className="hidden md:block">
                                    <p className="text-[8px] font-black text-muted-foreground uppercase tracking-widest opacity-40 mb-1">Cost Variance</p>
                                    <p className="text-[11px] font-black font-mono text-blue-500">-0.97 CPI</p>
                                </div>
                                <ArrowUpRight className="w-4 h-4 text-emerald-500 opacity-20 group-hover:opacity-100 transition-opacity" />
                            </div>
                        </div>
                    ))}
                    {projects.length === 0 && (
                        <div className="p-16 text-center text-muted-foreground text-[10px] uppercase font-black tracking-[0.3em] opacity-40">No active operational clusters detected.</div>
                    )}
                </div>
            </div>
        </div>
    );
}

function KPICard({ label, value, trend, icon: Icon, color }: any) {
    return (
        <div className="bg-background p-6 hover:bg-primary/[0.02] transition-colors cursor-crosshair group relative">
            <div className="flex justify-between items-start">
                <span className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/60">{label}</span>
                <Icon className="w-4 h-4 opacity-20 group-hover:opacity-50 transition-all text-primary" />
            </div>
            <div className="flex items-end justify-between mt-6">
                <span className="text-4xl font-black tracking-tighter tabular-nums leading-none">{value}</span>
                <div className="text-[9px] font-black px-2 py-0.5 border border-border bg-muted/30 flex items-center gap-1 text-primary">
                    {trend.includes('+') ? <ArrowUpRight className="w-2.5 h-2.5" /> : trend.includes('-') ? <ArrowDownRight className="w-2.5 h-2.5" /> : null}
                    {trend}
                </div>
            </div>
        </div>
    );
}

function StatusLine({ label, percent, color, onClick }: any) {
    return (
        <div className="space-y-2.5 cursor-pointer group/line" onClick={onClick}>
            <div className="flex justify-between items-end">
                <span className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/70 group-hover/line:text-primary transition-colors">{label}</span>
                <span className="text-[10px] font-mono font-black text-foreground">{percent}%</span>
            </div>
            <div className="h-1 bg-muted/20 rounded-none overflow-hidden">
                <div
                    className={cn("h-full transition-all duration-1000", color)}
                    style={{ width: `${percent}%` }}
                />
            </div>
        </div>
    );
}
