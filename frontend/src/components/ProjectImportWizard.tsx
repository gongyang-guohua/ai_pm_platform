"use client";

import React, { useState, useCallback } from 'react';
import {
    Upload, FileText, FileSpreadsheet, Code2,
    CheckCircle2, AlertTriangle, Loader2, X,
    ArrowRight, Download
} from "lucide-react";
import { cn } from "@/lib/utils";
import axios from 'axios';

type ImportStep = 'select' | 'configure' | 'importing' | 'success' | 'error';

interface ImportResult {
    id: number;
    title: string;
    tasks: any[];
}

export default function ProjectImportWizard({ onImportComplete }: { onImportComplete?: (project: any) => void }) {
    const [step, setStep] = useState<ImportStep>('select');
    const [file, setFile] = useState<File | null>(null);
    const [dragOver, setDragOver] = useState(false);
    const [projectTitle, setProjectTitle] = useState('');
    const [industry, setIndustry] = useState('');
    const [result, setResult] = useState<ImportResult | null>(null);
    const [error, setError] = useState('');
    const [preview, setPreview] = useState<string[]>([]);

    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';

    const supportedFormats = [
        { ext: 'csv', label: 'CSV', desc: 'Comma-separated values', icon: FileSpreadsheet, color: 'text-emerald-500' },
        { ext: 'json', label: 'JSON', desc: 'Structured JSON data', icon: Code2, color: 'text-blue-500' },
        { ext: 'xml', label: 'XML', desc: 'MS Project XML format', icon: FileText, color: 'text-amber-500' },
    ];

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setDragOver(false);
        const dropped = e.dataTransfer.files[0];
        if (dropped) handleFileSelect(dropped);
    }, []);

    const handleFileSelect = async (f: File) => {
        setFile(f);
        setError('');

        // Preview first few lines
        try {
            const text = await f.text();
            const lines = text.split('\n').slice(0, 8);
            setPreview(lines);
        } catch {
            setPreview([]);
        }

        // Auto-generate project title from filename
        const name = f.name.replace(/\.[^/.]+$/, '').replace(/[_-]/g, ' ');
        if (!projectTitle) setProjectTitle(name);

        setStep('configure');
    };

    const handleImport = async () => {
        if (!file) return;
        setStep('importing');
        setError('');

        try {
            const formData = new FormData();
            formData.append('file', file);
            if (projectTitle) formData.append('project_title', projectTitle);
            if (industry) formData.append('industry', industry);

            const res = await axios.post(`${apiUrl}/projects/import`, formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });

            setResult(res.data);
            setStep('success');
            onImportComplete?.(res.data);
        } catch (err: any) {
            const detail = err.response?.data?.detail || err.message || 'Import failed';
            setError(detail);
            setStep('error');
        }
    };

    const reset = () => {
        setStep('select');
        setFile(null);
        setProjectTitle('');
        setIndustry('');
        setResult(null);
        setError('');
        setPreview([]);
    };

    const getFileIcon = () => {
        if (!file) return FileText;
        const ext = file.name.split('.').pop()?.toLowerCase();
        const fmt = supportedFormats.find(f => f.ext === ext);
        return fmt?.icon || FileText;
    };

    const FileIcon = getFileIcon();

    return (
        <div className="max-w-3xl mx-auto animate-in fade-in duration-500">
            {/* Header */}
            <div className="border-b border-border pb-6 mb-8">
                <h2 className="text-3xl font-black tracking-tighter uppercase italic">Import Project Plan</h2>
                <p className="text-muted-foreground mt-1 font-mono text-xs uppercase tracking-widest">
                    Ingest external schedule data • CSV / JSON / XML (MS Project)
                </p>
            </div>

            {/* Step: Select File */}
            {step === 'select' && (
                <div className="space-y-6">
                    {/* Drop Zone */}
                    <div
                        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
                        onDragLeave={() => setDragOver(false)}
                        onDrop={handleDrop}
                        className={cn(
                            "border-2 border-dashed p-16 text-center transition-all cursor-pointer group",
                            dragOver
                                ? "border-primary bg-primary/5 scale-[1.01]"
                                : "border-border hover:border-primary/50 hover:bg-muted/30"
                        )}
                        onClick={() => document.getElementById('file-input')?.click()}
                    >
                        <Upload className={cn(
                            "w-12 h-12 mx-auto mb-4 transition-all",
                            dragOver ? "text-primary scale-110" : "text-muted-foreground/30 group-hover:text-primary/50"
                        )} />
                        <p className="text-sm font-bold uppercase tracking-tight">
                            {dragOver ? "Release to Upload" : "Drop project file here or click to browse"}
                        </p>
                        <p className="text-[10px] text-muted-foreground mt-2 uppercase tracking-widest">
                            Supported: CSV, JSON, XML (MS Project)
                        </p>
                        <input
                            id="file-input"
                            type="file"
                            accept=".csv,.json,.xml,.mpp"
                            className="hidden"
                            onChange={(e) => {
                                const f = e.target.files?.[0];
                                if (f) handleFileSelect(f);
                            }}
                        />
                    </div>

                    {/* Format Cards */}
                    <div className="grid grid-cols-3 gap-3">
                        {supportedFormats.map(fmt => (
                            <div key={fmt.ext} className="bg-card border border-border p-4 hover:border-primary/30 transition-all">
                                <fmt.icon className={cn("w-5 h-5 mb-2", fmt.color)} />
                                <p className="text-xs font-black uppercase">.{fmt.ext}</p>
                                <p className="text-[9px] text-muted-foreground mt-1">{fmt.desc}</p>
                            </div>
                        ))}
                    </div>

                    {/* Sample Template Download */}
                    <div className="bg-muted/30 border border-border p-4 flex items-center justify-between">
                        <div>
                            <p className="text-[10px] font-black uppercase tracking-widest">Need a template?</p>
                            <p className="text-[9px] text-muted-foreground mt-0.5">Download a sample CSV with the expected column format.</p>
                        </div>
                        <a
                            href={`data:text/csv;charset=utf-8,WBS,Title,Description,EstimatedHours,Start,End,Priority,Status,Dependencies,Responsible,Type%0A1.1,Site%20Preparation,Clear%20and%20grade%20site,40,2026-03-01,2026-03-05,High,not_started,,Team%20A,task%0A1.2,Foundation%20Work,Pour%20concrete%20foundations,80,2026-03-06,2026-03-15,Critical,not_started,Site%20Preparation,Team%20B,task%0A1.3,Structural%20Steel,Erect%20steel%20framework,120,2026-03-16,2026-04-05,High,not_started,Foundation%20Work,Team%20C,task%0A2.0,Electrical%20Rough-In,Install%20conduit%20and%20wiring,60,2026-04-06,2026-04-15,Medium,not_started,Structural%20Steel,Team%20D,task%0A3.0,Inspection%20Milestone,Final%20site%20inspection,0,2026-04-16,2026-04-16,Critical,not_started,Electrical%20Rough-In,PM,milestone`}
                            download="project_template.csv"
                            className="flex items-center gap-2 px-4 py-2 border border-border hover:bg-muted text-[10px] font-bold uppercase transition-colors"
                        >
                            <Download className="w-3 h-3" />
                            Download CSV Template
                        </a>
                    </div>
                </div>
            )}

            {/* Step: Configure */}
            {step === 'configure' && file && (
                <div className="space-y-6 animate-in slide-in-from-right-4 duration-300">
                    {/* File Info */}
                    <div className="flex items-center gap-4 p-4 bg-card border border-border">
                        <FileIcon className="w-8 h-8 text-primary" />
                        <div className="flex-1 min-w-0">
                            <p className="text-sm font-bold uppercase tracking-tight truncate">{file.name}</p>
                            <p className="text-[9px] text-muted-foreground font-mono">
                                {(file.size / 1024).toFixed(1)} KB • .{file.name.split('.').pop()?.toUpperCase()}
                            </p>
                        </div>
                        <button onClick={reset} className="p-1 hover:bg-muted border border-border"><X className="w-4 h-4" /></button>
                    </div>

                    {/* Preview */}
                    {preview.length > 0 && (
                        <div className="bg-card border border-border overflow-hidden">
                            <div className="px-4 py-2 border-b border-border bg-muted/30 text-[9px] font-black uppercase tracking-widest text-muted-foreground">
                                File Preview (first 8 lines)
                            </div>
                            <pre className="p-4 text-[10px] font-mono text-muted-foreground overflow-x-auto max-h-40 leading-relaxed">
                                {preview.map((line, i) => (
                                    <div key={i} className="hover:bg-muted/30">
                                        <span className="text-primary/30 mr-3 select-none">{String(i + 1).padStart(2, '0')}</span>
                                        {line}
                                    </div>
                                ))}
                            </pre>
                        </div>
                    )}

                    {/* Configuration Fields */}
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-[9px] font-black uppercase text-muted-foreground block mb-1.5">Project Title (Override)</label>
                            <input
                                type="text"
                                value={projectTitle}
                                onChange={e => setProjectTitle(e.target.value)}
                                className="w-full bg-card border border-border p-2.5 text-sm uppercase focus:border-primary outline-none transition-colors"
                                placeholder="Auto-detected from file"
                            />
                        </div>
                        <div>
                            <label className="text-[9px] font-black uppercase text-muted-foreground block mb-1.5">Industry Classification</label>
                            <select
                                value={industry}
                                onChange={e => setIndustry(e.target.value)}
                                className="w-full bg-card border border-border p-2.5 text-sm uppercase focus:border-primary outline-none transition-colors"
                            >
                                <option value="">Auto-Detect</option>
                                <option value="Construction">Construction</option>
                                <option value="Engineering">Engineering</option>
                                <option value="Software">Software</option>
                                <option value="Manufacturing">Manufacturing</option>
                                <option value="Energy">Energy / Oil & Gas</option>
                                <option value="General">General</option>
                            </select>
                        </div>
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end gap-3 pt-4 border-t border-border">
                        <button onClick={reset} className="px-6 py-2.5 border border-border text-[10px] font-bold uppercase hover:bg-muted transition-colors">
                            Cancel
                        </button>
                        <button
                            onClick={handleImport}
                            className="px-8 py-2.5 bg-primary text-primary-foreground text-[10px] font-bold uppercase hover:opacity-90 transition-all flex items-center gap-2"
                        >
                            <ArrowRight className="w-3 h-3" />
                            Import & Create Project
                        </button>
                    </div>
                </div>
            )}

            {/* Step: Importing */}
            {step === 'importing' && (
                <div className="p-20 text-center animate-in fade-in duration-300">
                    <Loader2 className="w-12 h-12 mx-auto text-primary animate-spin mb-4" />
                    <p className="text-sm font-black uppercase tracking-tight">Processing Import Pipeline</p>
                    <p className="text-[10px] text-muted-foreground mt-1 font-mono uppercase">Parsing • Validating • Creating Database Entries</p>
                </div>
            )}

            {/* Step: Success */}
            {step === 'success' && result && (
                <div className="p-12 text-center animate-in slide-in-from-bottom-4 duration-500 space-y-6">
                    <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/30 mx-auto flex items-center justify-center">
                        <CheckCircle2 className="w-8 h-8 text-emerald-500" />
                    </div>
                    <div>
                        <p className="text-lg font-black uppercase tracking-tighter">Import Successful</p>
                        <p className="text-[10px] text-muted-foreground mt-1 font-mono uppercase">
                            {result.tasks?.length || 0} tasks ingested into the system
                        </p>
                    </div>
                    <div className="bg-card border border-border p-4 max-w-sm mx-auto text-left">
                        <p className="text-[9px] font-black uppercase text-muted-foreground mb-1">Created Project</p>
                        <p className="font-bold uppercase tracking-tight">{result.title}</p>
                        <p className="text-[10px] text-muted-foreground font-mono mt-1">ID: {result.id} • Status: Planning</p>
                    </div>
                    <button
                        onClick={reset}
                        className="px-8 py-2.5 bg-primary text-primary-foreground text-[10px] font-bold uppercase hover:opacity-90 transition-all"
                    >
                        Import Another
                    </button>
                </div>
            )}

            {/* Step: Error */}
            {step === 'error' && (
                <div className="p-12 text-center animate-in slide-in-from-bottom-4 duration-500 space-y-6">
                    <div className="w-16 h-16 bg-red-500/10 border border-red-500/30 mx-auto flex items-center justify-center">
                        <AlertTriangle className="w-8 h-8 text-red-500" />
                    </div>
                    <div>
                        <p className="text-lg font-black uppercase tracking-tighter text-red-500">Import Failed</p>
                        <p className="text-xs text-muted-foreground mt-2 max-w-md mx-auto break-words">{error}</p>
                    </div>
                    <button
                        onClick={reset}
                        className="px-8 py-2.5 border border-border text-[10px] font-bold uppercase hover:bg-muted transition-colors"
                    >
                        Try Again
                    </button>
                </div>
            )}
        </div>
    );
}
