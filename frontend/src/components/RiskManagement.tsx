"use client";

import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldAlert, Plus, Save, Trash2, X } from "lucide-react";
import { cn } from "@/lib/utils";
import axios from 'axios';

interface Risk {
    id: number;
    title: string;
    description: string;
    probability: number;
    impact: number;
    mitigation_plan: string;
    status: string;
    task_id?: number;
}

interface RiskManagementProps {
    projectId: number;
    tasks: any[];
}

export default function RiskManagement({ projectId, tasks }: RiskManagementProps) {
    const [risks, setRisks] = useState<Risk[]>([]);
    const [loading, setLoading] = useState(true);
    const [isCreating, setIsCreating] = useState(false);
    const [newRisk, setNewRisk] = useState({
        title: '',
        description: '',
        probability: 3,
        impact: 3,
        mitigation_plan: '',
        status: 'identified'
    });

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

    const fetchRisks = async () => {
        try {
            const res = await axios.get(`${apiUrl}/risks/${projectId}`);
            setRisks(res.data);
        } catch (err) {
            console.error("Failed to fetch risks", err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchRisks();
    }, [projectId]);

    const handleCreateRisk = async () => {
        try {
            await axios.post(`${apiUrl}/risks/?project_id=${projectId}`, newRisk);
            setIsCreating(false);
            setNewRisk({ title: '', description: '', probability: 3, impact: 3, mitigation_plan: '', status: 'identified' });
            fetchRisks();
        } catch (err) {
            console.error("Failed to create risk", err);
        }
    };

    const handleDeleteRisk = async (id: number) => {
        if (!confirm("Delete this risk?")) return;
        try {
            await axios.delete(`${apiUrl}/risks/${id}`);
            fetchRisks();
        } catch (err) {
            console.error("Failed to delete risk", err);
        }
    };

    // Matrix calculation
    const matrix = Array(5).fill(null).map(() => Array(5).fill(0));
    risks.forEach(r => {
        const p = Math.min(Math.max(Math.floor(r.probability) - 1, 0), 4);
        const i = Math.min(Math.max(Math.floor(r.impact) - 1, 0), 4);
        matrix[p][i]++;
    });

    if (loading) return <div className="p-10 text-center font-mono text-[10px] uppercase">Accessing Risk Matrix...</div>;

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Heatmap Matrix */}
                <div className="lg:col-span-1 bg-card border border-border p-6">
                    <h3 className="text-sm font-black uppercase italic tracking-tighter mb-4 flex items-center gap-2">
                        <ShieldAlert className="w-4 h-4 text-primary" />
                        Probability x Impact Matrix
                    </h3>
                    <div className="grid grid-cols-5 gap-1 aspect-square border-l-2 border-b-2 border-border p-2">
                        {[4, 3, 2, 1, 0].map(p => (
                            <React.Fragment key={p}>
                                {[0, 1, 2, 3, 4].map(i => {
                                    const count = risks.filter(r => Math.floor(r.probability) === p + 1 && Math.floor(r.impact) === i + 1).length;
                                    const score = (p + 1) * (i + 1);
                                    let bgColor = "bg-muted/10";
                                    if (score >= 15) bgColor = "bg-red-500/40";
                                    else if (score >= 8) bgColor = "bg-amber-500/40";
                                    else if (score >= 1) bgColor = "bg-emerald-500/40";

                                    return (
                                        <div
                                            key={`${p}-${i}`}
                                            className={cn(
                                                "relative flex items-center justify-center border border-border/20 transition-all",
                                                bgColor,
                                                count > 0 ? "shadow-inner scale-95" : "opacity-30"
                                            )}
                                            title={`P:${p + 1} I:${i + 1}`}
                                        >
                                            {count > 0 && <span className="text-[10px] font-black">{count}</span>}
                                        </div>
                                    );
                                })}
                            </React.Fragment>
                        ))}
                    </div>
                    <div className="flex justify-between items-center mt-2 text-[8px] font-mono text-muted-foreground uppercase">
                        <span>Low Impact</span>
                        <span>High Impact</span>
                    </div>
                </div>

                {/* Risk List */}
                <div className="lg:col-span-2 bg-card border border-border overflow-hidden">
                    <div className="px-6 py-4 border-b border-border flex justify-between items-center">
                        <h3 className="text-sm font-black uppercase italic tracking-tighter">Project Contingency Registry</h3>
                        <button
                            onClick={() => setIsCreating(true)}
                            className="bg-primary text-primary-foreground text-[10px] font-bold px-3 py-1 flex items-center gap-1 hover:opacity-90 transition-all"
                        >
                            <Plus className="w-3 h-3" />
                            IDENTIFY NEW RISK
                        </button>
                    </div>

                    <div className="divide-y divide-border overflow-y-auto max-h-[500px]">
                        {isCreating && (
                            <div className="p-6 bg-muted/20 space-y-4 animate-in slide-in-from-top-2 duration-300">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="col-span-2">
                                        <label className="text-[9px] font-black uppercase text-muted-foreground block mb-1">Risk Title</label>
                                        <input
                                            type="text"
                                            value={newRisk.title}
                                            onChange={e => setNewRisk({ ...newRisk, title: e.target.value })}
                                            className="w-full bg-card border border-border p-2 text-xs uppercase focus:border-primary outline-none"
                                            placeholder="Potential Supply Chain Disruption"
                                        />
                                    </div>
                                    <div className="col-span-2">
                                        <label className="text-[9px] font-black uppercase text-muted-foreground block mb-1">Description</label>
                                        <textarea
                                            value={newRisk.description}
                                            onChange={e => setNewRisk({ ...newRisk, description: e.target.value })}
                                            className="w-full bg-card border border-border p-2 text-xs focus:border-primary outline-none h-20"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-[9px] font-black uppercase text-muted-foreground block mb-1">Probability (1-5)</label>
                                        <input
                                            type="range" min="1" max="5" step="1"
                                            value={newRisk.probability}
                                            onChange={e => setNewRisk({ ...newRisk, probability: parseInt(e.target.value) })}
                                            className="w-full accent-primary"
                                        />
                                        <div className="flex justify-between text-[8px] font-mono mt-1"><span>1</span><span>5</span></div>
                                    </div>
                                    <div>
                                        <label className="text-[9px] font-black uppercase text-muted-foreground block mb-1">Impact (1-5)</label>
                                        <input
                                            type="range" min="1" max="5" step="1"
                                            value={newRisk.impact}
                                            onChange={e => setNewRisk({ ...newRisk, impact: parseInt(e.target.value) })}
                                            className="w-full accent-primary"
                                        />
                                        <div className="flex justify-between text-[8px] font-mono mt-1"><span>1</span><span>5</span></div>
                                    </div>
                                    <div className="col-span-2">
                                        <label className="text-[9px] font-black uppercase text-muted-foreground block mb-1">Mitigation Strategy</label>
                                        <textarea
                                            value={newRisk.mitigation_plan}
                                            onChange={e => setNewRisk({ ...newRisk, mitigation_plan: e.target.value })}
                                            className="w-full bg-card border border-border p-2 text-xs focus:border-primary outline-none h-20"
                                            placeholder="Alternative vendors identified; safety stock increased by 20%."
                                        />
                                    </div>
                                </div>
                                <div className="flex justify-end gap-2">
                                    <button onClick={() => setIsCreating(false)} className="px-4 py-2 border border-border text-[10px] font-bold uppercase hover:bg-muted">Cancel</button>
                                    <button onClick={handleCreateRisk} className="px-4 py-2 bg-primary text-primary-foreground text-[10px] font-bold uppercase hover:opacity-90">Store Analysis</button>
                                </div>
                            </div>
                        )}

                        {risks.map(risk => {
                            const score = risk.probability * risk.impact;
                            const severity = score >= 15 ? 'Critical' : score >= 8 ? 'High' : 'Moderate';
                            const severityColor = score >= 15 ? 'text-red-500' : score >= 8 ? 'text-amber-500' : 'text-emerald-500';

                            return (
                                <div key={risk.id} className="p-4 hover:bg-muted/30 transition-colors group">
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-3">
                                            <div className={cn("px-1.5 py-0.5 border text-[8px] font-black uppercase", severityColor.replace('text', 'border'))}>
                                                {severity} ({score})
                                            </div>
                                            <h4 className="text-sm font-bold uppercase tracking-tight">{risk.title}</h4>
                                        </div>
                                        <div className="flex items-center gap-4">
                                            <span className="text-[10px] font-mono text-muted-foreground uppercase">{risk.status}</span>
                                            <button onClick={() => handleDeleteRisk(risk.id)} className="opacity-0 group-hover:opacity-100 text-red-500 transition-opacity">
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </div>
                                    <p className="text-xs text-muted-foreground mb-4">{risk.description}</p>
                                    <div className="bg-muted pb-3 pt-2 px-3 border-l-2 border-primary">
                                        <span className="text-[8px] font-black uppercase text-primary/70 block mb-1">Counter-Measure / Mitigation</span>
                                        <p className="text-[11px] font-medium italic">{risk.mitigation_plan || "No mitigation strategy defined."}</p>
                                    </div>
                                </div>
                            );
                        })}

                        {risks.length === 0 && !isCreating && (
                            <div className="p-20 text-center">
                                <AlertTriangle className="w-8 h-8 mx-auto text-muted-foreground/30 mb-2" />
                                <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">No active risk vectors detected in the environment.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
