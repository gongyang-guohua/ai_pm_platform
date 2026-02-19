"use client";

import React, { useState } from 'react';
import { Send, Loader2, CheckCircle2, ListTodo, Package, DollarSign, ArrowRight, Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';
import axios from 'axios';

interface Dependency {
    target_id: number;
    relation: string;
    lag: number;
}

interface Task {
    title: string;
    description: string;
    estimated_hours: number;
    dependencies: Dependency[];
    wbs_code?: string;
    priority?: string;
    task_type?: string;
}

interface Material {
    name: string;
    category: string;
    quantity: number;
    unit: string;
    unit_price: number;
    total_price: number;
}

interface GeneratedPlan {
    project_title: string;
    summary: string;
    tasks: Task[];
    materials: Material[];
    recommended_tech_stack: string[];
}

export default function ProjectCreationWizard() {
    const [step, setStep] = useState(1);
    const [description, setDescription] = useState('');
    const [industry, setIndustry] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [generatedPlan, setGeneratedPlan] = useState<GeneratedPlan | null>(null);
    const [error, setError] = useState<string | null>(null);

    const handleGenerate = async () => {
        setIsGenerating(true);
        setError(null);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001/api/v1';
            const response = await axios.post(`${apiUrl}/projects/generate-plan`, {
                description,
                industry
            });
            setGeneratedPlan(response.data);
            setStep(2);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Failed to generate plan. Please try again.");
        } finally {
            setIsGenerating(false);
        }
    };

    const handleCreate = async () => {
        if (!generatedPlan) return;
        setIsGenerating(true);
        setError(null);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8001/api/v1';
            await axios.post(`${apiUrl}/projects/`, {
                title: generatedPlan.project_title,
                description,
                industry,
                summary: generatedPlan.summary,
                tech_stack: generatedPlan.recommended_tech_stack,
                tasks: generatedPlan.tasks.map(t => ({
                    ...t,
                    status: 'not_started',
                    priority: 'Medium',
                    materials: []
                })),
                materials: generatedPlan.materials
            });
            setStep(4);
        } catch (err: any) {
            console.error(err);
            setError(err.response?.data?.detail || "Failed to initialize project. Check backend connection.");
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <div className="w-full max-w-4xl mx-auto p-6 space-y-8 animate-in fade-in duration-500">
            {/* Header */}
            <div className="text-center space-y-2">
                <h2 className="text-3xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                    AI Project Architect
                </h2>
                <p className="text-muted-foreground">Transform your ideas into structured engineering plans</p>
            </div>

            {/* Progress Steps */}
            <div className="flex justify-between items-center px-12 relative">
                <div className="absolute top-1/2 left-12 right-12 h-0.5 bg-gray-200 -translate-y-1/2 z-0" />
                {[1, 2, 3].map((s) => (
                    <div key={s} className={cn(
                        "relative z-10 w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all duration-300",
                        step === s ? "bg-primary border-primary text-primary-foreground shadow-lg" :
                            step > s ? "bg-emerald-500 border-emerald-500 text-white" : "bg-card border-border text-muted-foreground"
                    )}>
                        {step > s ? <CheckCircle2 className="w-6 h-6" /> : s}
                    </div>
                ))}
            </div>

            {/* Step Content */}
            <div className="bg-card rounded-2xl shadow-xl border border-border p-8 min-h-[400px]">
                {step === 1 && (
                    <div className="space-y-6">
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-foreground">Project Industry</label>
                            <input
                                type="text"
                                placeholder="e.g., Construction, Software, Energy"
                                className="w-full p-3 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all placeholder:text-muted-foreground/50"
                                value={industry}
                                onChange={(e) => setIndustry(e.target.value)}
                            />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-semibold text-foreground">Project Description</label>
                            <textarea
                                rows={6}
                                placeholder="Describe your project goal, key requirements, and any specific constraints..."
                                className="w-full p-3 rounded-lg border border-border bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-transparent outline-none transition-all resize-none placeholder:text-muted-foreground/50"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                            />
                        </div>

                        {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded-lg border border-red-100">{error}</p>}

                        <button
                            onClick={handleGenerate}
                            disabled={isGenerating || !description}
                            className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-xl font-bold shadow-lg shadow-blue-200 hover:opacity-90 transition-all disabled:opacity-50"
                        >
                            {isGenerating ? (
                                <>
                                    <Loader2 className="w-5 h-5 animate-spin" />
                                    Analyzing Requirements...
                                </>
                            ) : (
                                <>
                                    <Sparkles className="w-5 h-5" />
                                    Generate AI Implementation Plan
                                </>
                            )}
                        </button>
                    </div>
                )}

                {step === 2 && generatedPlan && (
                    <div className="space-y-8 animate-in slide-in-from-right duration-500">
                        <div className="border-b pb-4">
                            <h3 className="text-2xl font-bold text-gray-800">{generatedPlan.project_title}</h3>
                            <p className="text-gray-600 mt-2">{generatedPlan.summary}</p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div className="space-y-4">
                                <div className="flex items-center gap-2 text-blue-600 font-bold">
                                    <ListTodo className="w-5 h-5" />
                                    Key Tasks
                                </div>
                                <div className="space-y-3">
                                    {generatedPlan.tasks.map((task, i) => (
                                        <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-100 hover:border-blue-200 transition-colors">
                                            <div className="font-semibold text-gray-800">{task.title}</div>
                                            <div className="text-xs text-gray-500 mt-1">{task.estimated_hours} Hours</div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center gap-2 text-amber-600 font-bold">
                                    <Package className="w-5 h-5" />
                                    Material Take-Off (MTO)
                                </div>
                                <div className="space-y-3">
                                    {generatedPlan.materials.map((mat, i) => (
                                        <div key={i} className="p-3 bg-gray-50 rounded-lg border border-gray-100 flex justify-between items-center transition-colors">
                                            <div>
                                                <div className="font-semibold text-gray-800">{mat.name}</div>
                                                <div className="text-xs text-gray-500 mt-1">{mat.category}</div>
                                            </div>
                                            <div className="text-right">
                                                <div className="text-sm font-bold text-gray-700">{mat.quantity} {mat.unit}</div>
                                                <div className="text-[10px] text-gray-400">Est. ${mat.total_price.toFixed(2)}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center gap-2 text-emerald-600 font-bold">
                                    <DollarSign className="w-5 h-5" />
                                    Initial BOQ Estimation
                                </div>
                                <div className="p-6 bg-emerald-50 rounded-2xl border border-emerald-100 space-y-4">
                                    <div className="flex justify-between items-end">
                                        <span className="text-sm text-emerald-700">Total Estimated Cost</span>
                                        <span className="text-3xl font-bold text-emerald-900">
                                            ${generatedPlan.materials.reduce((sum, m) => sum + m.total_price, 0).toLocaleString()}
                                        </span>
                                    </div>
                                    <div className="h-2 bg-emerald-200 rounded-full overflow-hidden">
                                        <div className="h-full bg-emerald-600 w-full animate-progress" />
                                    </div>
                                    <p className="text-[10px] text-emerald-600">Based on AI market analysis and requirement scale.</p>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <div className="flex items-center gap-2 text-indigo-600 font-bold">
                                    <Sparkles className="w-5 h-5" />
                                    Recommended Tech Stack
                                </div>
                                <div className="flex flex-wrap gap-2">
                                    {generatedPlan.recommended_tech_stack.map((tech, i) => (
                                        <span key={i} className="px-3 py-1 bg-indigo-50 text-indigo-600 rounded-full text-sm border border-indigo-100">
                                            {tech}
                                        </span>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-4 pt-6">
                            <button
                                onClick={() => setStep(1)}
                                className="flex-1 py-3 border border-gray-200 rounded-xl font-semibold hover:bg-gray-50 transition-all"
                            >
                                Back to Edit
                            </button>
                            <button
                                onClick={() => setStep(3)}
                                className="flex-[2] py-3 bg-blue-600 text-white rounded-xl font-semibold shadow-lg shadow-blue-200 hover:bg-blue-700 transition-all"
                            >
                                Review Full Logistics
                            </button>
                        </div>
                    </div>
                )}

                {step === 3 && (
                    <div className="space-y-8 text-center py-12">
                        <div className="flex justify-center">
                            <CheckCircle2 className="w-20 h-20 text-green-500" />
                        </div>
                        <div className="space-y-2">
                            <h3 className="text-2xl font-bold">Ready to Launch!</h3>
                            <p className="text-muted-foreground">AI has structured {generatedPlan?.materials?.length || 0} materials, {generatedPlan?.tasks?.length || 0} tasks, and a full BOQ.</p>
                        </div>
                        {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded-lg border border-red-100">{error}</p>}
                        <button
                            onClick={handleCreate}
                            disabled={isGenerating}
                            className="px-12 py-4 bg-green-600 text-white rounded-xl font-bold text-lg shadow-xl shadow-green-100 hover:bg-green-700 transition-all disabled:opacity-50"
                        >
                            {isGenerating ? "Initializing DB..." : "Initialize Project & DB"}
                        </button>
                    </div>
                )}

                {step === 4 && (
                    <div className="space-y-8 text-center py-12 animate-in zoom-in duration-500">
                        <div className="flex justify-center">
                            <div className="w-24 h-24 bg-green-100 rounded-full flex items-center justify-center">
                                <CheckCircle2 className="w-12 h-12 text-green-600" />
                            </div>
                        </div>
                        <div className="space-y-2">
                            <h3 className="text-3xl font-bold text-gray-900">Project Activated!</h3>
                            <p className="text-gray-500">The implementation plan has been written to the database.</p>
                        </div>
                        <button
                            onClick={() => window.location.href = '/'}
                            className="px-8 py-3 bg-gray-900 text-white rounded-xl font-bold hover:bg-gray-800 transition-all"
                        >
                            Go to Dashboard
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
