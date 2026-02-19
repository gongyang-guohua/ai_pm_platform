"use client";

import React, { useState, useEffect } from 'react';
import {
    ArrowLeft, List, Kanban as KanbanIcon, GanttChartSquare, Package,
    FileText, Calculator, Settings, Play, CheckCircle2,
    Clock, AlertTriangle, MoreHorizontal, Pencil, Trash2, X, Calendar as CalendarIcon,
    ChevronRight, Filter, Download, Plus
} from "lucide-react";
import { cn } from "@/lib/utils";
import axios from 'axios';
import { AgGridReact } from 'ag-grid-react';
import { ModuleRegistry, AllCommunityModule, ColDef, ValueFormatterParams, ValueGetterParams, ICellRendererParams } from 'ag-grid-community';
import "ag-grid-community/styles/ag-grid.css";
import "ag-grid-community/styles/ag-theme-quartz.css";


import KanbanBoard from './KanbanBoard';
import GanttChart from './GanttChart';
import RiskManagement from './RiskManagement';
import ProjectNetworkView from './ProjectNetworkView';
import CalendarView from './CalendarView';
import { Calendar, Network, ShieldAlert } from "lucide-react";
import { Button } from './ui/Button';
import { Badge } from './ui/Badge';

ModuleRegistry.registerModules([AllCommunityModule]);

// --- Types ---

interface Dependency {
    target_id: number;
    relation: string;
    lag: number;
}

interface Task {
    id: number;
    wbs_code?: string;
    title: string;
    description: string;
    priority: string; // Low, Medium, High, Critical
    task_type: string; // task, milestone
    estimated_hours: number; // Keep for compatibility if needed, but original_duration is primary
    actual_hours: number;
    status: string; // not_started, in_progress, stalled, completed, cancelled
    planned_start?: string;
    planned_end?: string;
    actual_start?: string;
    actual_end?: string;
    responsible_party?: string;
    helper_party?: string;
    dependencies: Dependency[];
    materials?: Material[];
    notes?: string;
    // P6 Fields
    is_summary?: boolean;
    outline_level?: number;
    original_duration?: number;
    remaining_duration?: number;
    total_float?: number;
    free_float?: number;
    early_start?: string;
    early_finish?: string;
    late_start?: string;
    late_finish?: string;
    // Engineering Fields
    is_deliverable?: boolean;
    discipline?: string;
}

interface TaskUpdateInput {
    wbs_code?: string;
    title?: string;
    description?: string;
    priority?: string;
    task_type?: string;
    status?: string;
    estimated_hours?: number;
    actual_hours?: number;
    planned_start?: string;
    planned_end?: string;
    actual_start?: string;
    actual_end?: string;
    responsible_party?: string;
    helper_party?: string;
    dependencies?: Dependency[];
    notes?: string;
    // Engineering Fields
    is_deliverable?: boolean;
    discipline?: string;
}

interface Material {
    id: number;
    name: string;
    category: string;
    quantity: number;
    unit: string;
    unit_price: number;
    total_price: number;
}

interface Project {
    id: number;
    title: string;
    description: string;
    industry: string;
    summary: string;
    status: string;
    tasks: Task[];
    materials?: Material[];
}

interface ProjectStats {
    performance?: {
        cpi?: number;
        spi?: number;
    };
}


// --- Helper Components ---
const StatusBadge = ({ status }: { status: string }) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
        completed: "success",
        in_progress: "outline",
        stalled: "destructive",
        cancelled: "destructive",
        not_started: "secondary",
    };
    const label = status?.replace('_', ' ') || 'Todo';
    return (
        <Badge variant={variants[status] || "outline"} className="px-2 py-0 h-4 min-w-[60px] justify-center">
            {label}
        </Badge>
    );
};

const PriorityBadge = ({ priority }: { priority: string }) => {
    const variants: Record<string, "default" | "secondary" | "destructive" | "outline" | "success" | "warning"> = {
        Critical: "destructive",
        High: "warning",
        Medium: "outline",
        Low: "secondary",
    };
    return (
        <Badge variant={variants[priority] || "outline"} className="px-2 py-0 h-4 border-opacity-50">
            {priority}
        </Badge>
    );
};

type TabType = 'list' | 'kanban' | 'gantt' | 'mto' | 'reports' | 'risks' | 'calendar' | 'network' | 'templates';

export default function ProjectDetailView({ projectId, onBack }: { projectId: number, onBack: () => void }) {
    const [project, setProject] = useState<Project | null>(null);
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1'; // Define here
    const [activeTab, setActiveTab] = useState<TabType>('list');
    const [loading, setLoading] = useState(true);

    // Side Panel State
    const [isEditPanelOpen, setIsEditPanelOpen] = useState(false);
    const [editingTaskId, setEditingTaskId] = useState<number | null>(null);
    const [editTaskData, setEditTaskData] = useState<TaskUpdateInput>({});

    const [stats, setStats] = useState<ProjectStats | null>(null);
    const [reportContent, setReportContent] = useState<string | null>(null);
    const [collapsedWbs, setCollapsedWbs] = useState<Set<string>>(new Set());
    const [templates, setTemplates] = useState<any>(null);

    const [generatingReport, setGeneratingReport] = useState(false);
    const [isSimulating, setIsSimulating] = useState(false);

    const boqList = templates?.BOQ || [];
    const vdrRotatingList = templates?.VDR_Rotating || [];
    const vdrVesselList = templates?.VDR_Vessel || [];
    const itpList = templates?.ITP || [];

    const renderItpRow = (item: any, i: number) => (
        <tr key={i} className="group">
            <td className="px-4 py-2 font-medium">{item.activity}</td>
            <td className="px-4 py-2">{item.check}</td>
            <td className="px-4 py-2 text-muted-foreground">{item.acceptance_criteria}</td>
            <td className="px-4 py-2 font-mono text-xs flex items-center justify-between">
                {item.verifier}
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleAddTemplateItem('ITP', item)}
                    className="h-6 w-6 p-0 opacity-0 group-hover:opacity-100 transition-opacity hover:text-primary"
                    title="Add to Project"
                >
                    <Plus className="w-3.5 h-3.5" />
                </Button>
            </td>
        </tr>
    );

    const renderBoqCard = (item: any, i: number) => (
        <div key={i} className="p-3 border border-border rounded-md hover:bg-muted/30 transition-colors relative group">
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleAddTemplateItem('BOQ', item)}
                    className="h-6 w-6 p-0 hover:text-primary"
                    title="Add to Project"
                >
                    <Plus className="w-4 h-4" />
                </Button>
            </div>
            <div className="text-xs font-bold uppercase text-muted-foreground mb-1">{item.category}</div>
            <div className="font-medium text-sm pr-6">{item.item}</div>
            <div className="text-xs text-muted-foreground mt-1">{item.description} ({item.unit})</div>
        </div>
    );

    const renderVdrRow = (item: any, i: number) => (
        <div key={i} className="flex items-center justify-between p-2 border border-border rounded-md text-sm bg-muted/10">
            <div className="flex items-center gap-3">
                <span className="font-mono text-xs text-primary">{item.code}</span>
                <span>{item.title}</span>
            </div>
            <div className="flex items-center gap-2">
                <Badge variant="outline">{item.stage}</Badge>
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleAddTemplateItem('MH', item)}
                    className="h-6 w-6 p-0 hover:text-primary"
                    title="Add to Project"
                >
                    <Plus className="w-3.5 h-3.5" />
                </Button>
            </div>
        </div>
    );

    // --- Fetch Data ---

    useEffect(() => {
        const fetchStats = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
                const res = await axios.get(`${apiUrl}/analytics/projects/${projectId}/stats`);
                setStats(res.data);
            } catch (err) {
                console.error("Failed to fetch project stats", err);
            }
        };

        const fetchTemplates = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
                const res = await axios.get(`${apiUrl}/templates`);
                setTemplates(res.data);
            } catch (err) {
                console.error("Failed to fetch templates", err);
            }
        };

        if (project) {
            fetchStats();
            fetchTemplates();
        }
    }, [projectId, project]);



    useEffect(() => {
        const fetchProject = async () => {
            try {
                const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
                const res = await axios.get(`${apiUrl}/projects/`);
                const found = res.data.find((p: Project) => p.id === projectId);
                setProject(found);
            } catch (err) {
                console.error("Failed to fetch project detail", err);
            } finally {
                setLoading(false);
            }
        };
        fetchProject();
    }, [projectId]);

    // --- Handlers ---

    const openEditPanel = React.useCallback((task: Task) => {
        setEditingTaskId(task.id);
        setEditTaskData({
            wbs_code: task.wbs_code,
            title: task.title,
            description: task.description,
            priority: task.priority,
            task_type: task.task_type || 'task',
            status: task.status,
            estimated_hours: task.estimated_hours,
            planned_start: task.planned_start,
            planned_end: task.planned_end,
            actual_start: task.actual_start,
            actual_end: task.actual_end,
            responsible_party: task.responsible_party,
            dependencies: task.dependencies || [],
            notes: task.notes,
            is_deliverable: task.is_deliverable,
            discipline: task.discipline
        });
        setIsEditPanelOpen(true);
    }, []);

    const closeEditPanel = () => {
        setIsEditPanelOpen(false);
        setEditingTaskId(null);
        setEditTaskData({});
    };

    const handleSaveTask = async () => {
        if (!editingTaskId) return;
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
            const res = await axios.put(`${apiUrl}/tasks/${editingTaskId}`, editTaskData);
            if (project) {
                const newTasks = project.tasks.map(t => t.id === editingTaskId ? res.data : t);
                setProject({ ...project, tasks: newTasks });
            }
            closeEditPanel();
        } catch (err) {
            console.error("Failed to update task", err);
            alert("Update failed. Check console for details.");
        }
    };

    const handleDeleteTask = async (taskId: number) => {
        if (!confirm("Are you sure you want to delete this task? This action cannot be undone.")) return;
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
            await axios.delete(`${apiUrl}/tasks/${taskId}`);
            if (project) {
                setProject({ ...project, tasks: project.tasks.filter(t => t.id !== taskId) });
            }
            if (editingTaskId === taskId) closeEditPanel();
        } catch (err) {
            console.error("Failed to delete task", err);
        }
    };

    const handleUpdateTaskStatus = async (taskId: number, newStatus: string) => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
            const res = await axios.put(`${apiUrl}/tasks/${taskId}`, { status: newStatus });
            if (project) {
                const newTasks = project.tasks.map(t => t.id === taskId ? res.data : t);
                setProject({ ...project, tasks: newTasks });
            }
        } catch (err) {
            console.error("Failed to update task status", err);
        }
    };

    const handleGenerateReport = async () => {
        setGeneratingReport(true);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
            const res = await axios.post(`${apiUrl}/reports/${projectId}/generate-summary`);
            setReportContent(res.data.report || "No report generated.");
        } catch (err) {
            console.error("Failed to generate report", err);
            setReportContent("Error generating report. Please check the backend connection.");
        } finally {
            setGeneratingReport(false);
        }
    };

    const handleDeleteProject = async () => {
        if (!confirm("DANGER: Permanently delete this project and all data?")) return;
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
            await axios.delete(`${apiUrl}/projects/${projectId}`);
            onBack();
        } catch (err) {
            console.error("Failed to delete project", err);
        }
    };

    const handleRunSimulation = async () => {
        setIsSimulating(true);
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
            await axios.post(`${apiUrl}/projects/${projectId}/schedule`);
            // Refresh project data
            const res = await axios.get(`${apiUrl}/projects/${projectId}`);
            setProject(res.data);
            alert("CPM Scheduling Complete: Critical Path identified and dates updated.");
        } catch (err) {
            console.error("Failed to run simulation", err);
            alert("Error running simulation. Check task logic for cycles.");
        } finally {
            setIsSimulating(false);
        }
    };

    const handleAddTemplateItem = async (type: string, item: any) => {
        try {
            const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000/api/v1';
            let payload: any = {};
            let endpoint = 'tasks';

            if (type === 'BOQ') {
                // Determine category for logistics or just add as explicit material task
                // For simplicity, we add as a Material to the General Logistics task if it exists, roughly
                // Or create a new task for this BOQ item
                payload = {
                    project_id: projectId,
                    title: `${item.item} (Supply)`,
                    description: `${item.description}. Qty: 1 (Placeholder). Unit: ${item.unit}`,
                    task_type: 'task',
                    status: 'not_started',
                    estimated_hours: 8,
                    discipline: 'Procurement',
                    is_deliverable: true
                };
            } else if (type === 'MH') { // VDR / Manhours placeholder
                payload = {
                    project_id: projectId,
                    title: `${item.code}: ${item.title}`,
                    description: `Deliverable for stage: ${item.stage}`,
                    task_type: 'milestone',
                    status: 'not_started',
                    estimated_hours: 0,
                    discipline: 'Engineering',
                    is_deliverable: true
                };
            } else if (type === 'ITP') {
                payload = {
                    project_id: projectId,
                    title: `Inspection: ${item.activity}`,
                    description: `Check: ${item.check}. Criteria: ${item.acceptance_criteria}. Verifier: ${item.verifier}`,
                    task_type: 'task',
                    status: 'not_started',
                    estimated_hours: 4,
                    discipline: 'Quality',
                    is_deliverable: false
                };
            }


            // Send request to create task
            await axios.post(`${apiUrl}/tasks/`, { ...payload, project_id: projectId });

            // Refresh
            const res = await axios.get(`${apiUrl}/projects/`);
            const found = res.data.find((p: Project) => p.id === projectId);
            setProject(found);

            alert(`Added ${type} item to project!`);

        } catch (err) {
            console.error("Failed to add template item", err);
            alert("Failed to add item. Ensure backend supports creating individual tasks.");
        }
    };

    const toggleWbs = React.useCallback((wbs: string) => {
        setCollapsedWbs(prev => {
            const next = new Set(prev);
            if (next.has(wbs)) {
                next.delete(wbs);
            } else {
                next.add(wbs);
            }
            return next;
        });
    }, []);

    // Derived state for Hierarchical View
    const visibleTasks = React.useMemo(() => {
        if (!project?.tasks) return [];

        // 1. Sort by WBS to ensure proper tree order
        // helper to sort naturally: 1.1, 1.2, 1.10
        const sorted = [...project.tasks].sort((a, b) => {
            return (a.wbs_code || '').localeCompare(b.wbs_code || '', undefined, { numeric: true, sensitivity: 'base' });
        });

        // 2. Filter based on collapsed state
        return sorted.filter(t => {
            if (!t.wbs_code) return true;
            // Check all ancestors
            // ancestor of 1.2.1 is 1.2, and 1.
            let code = t.wbs_code;
            while (code.includes('.')) {
                code = code.substring(0, code.lastIndexOf('.'));
                if (collapsedWbs.has(code)) return false;
            }
            return true;
        });
    }, [project?.tasks, collapsedWbs]);

    const columnDefs: ColDef<Task>[] = React.useMemo(() => [
        { field: 'wbs_code', headerName: 'WBS', width: 100, pinned: 'left' },
        {
            field: 'title', headerName: 'Task Name', width: 300, pinned: 'left', cellRenderer: (params: ICellRendererParams) => {
                const task = params.data as Task;
                const level = task.outline_level || 1;
                // Check if this task is a parent (has children in the full dataset)
                // A simplified check: does any other task start with this WBS + "."?
                // Or use is_summary if reliable. Let's try is_summary first, if not, fallback to WBS check.
                // Actually, let's look at the full list to detect children for the chevron.
                const hasChildren = project?.tasks.some(t => t.wbs_code?.startsWith(task.wbs_code + '.') && t.wbs_code !== task.wbs_code);
                const isCollapsed = task.wbs_code ? collapsedWbs.has(task.wbs_code) : false;

                return (
                    <div style={{ paddingLeft: (level - 1) * 15, display: 'flex', alignItems: 'center' }}>
                        {hasChildren ? (
                            <button
                                onClick={(e) => {
                                    e.stopPropagation(); // Prevent row selection logic if any
                                    if (task.wbs_code) toggleWbs(task.wbs_code);
                                }}
                                className="mr-1 p-0.5 hover:bg-muted/50 rounded"
                            >
                                <ChevronRight className={cn("w-3.5 h-3.5 transition-transform", !isCollapsed && "rotate-90")} />
                            </button>
                        ) : <span className="w-5" />} {/* Spacer for alignment */}

                        <span className={cn("truncate", hasChildren && "font-bold")}>{params.value}</span>
                    </div>
                );
            }
        },
        { field: 'status', headerName: 'Status', width: 120, cellRenderer: (params: ICellRendererParams) => <StatusBadge status={params.value} /> },
        { field: 'planned_start', headerName: 'Planned Start', width: 120, valueFormatter: (p: ValueFormatterParams) => p.value ? new Date(p.value).toLocaleDateString() : '' },
        { field: 'planned_end', headerName: 'Planned Finish', width: 120, valueFormatter: (p: ValueFormatterParams) => p.value ? new Date(p.value).toLocaleDateString() : '' },
        { field: 'actual_start', headerName: 'Actual Start', width: 120, valueFormatter: (p: ValueFormatterParams) => p.value ? new Date(p.value).toLocaleDateString() : '' },
        { field: 'actual_end', headerName: 'Actual Finish', width: 120, valueFormatter: (p: ValueFormatterParams) => p.value ? new Date(p.value).toLocaleDateString() : '' },
        { field: 'original_duration', headerName: 'Dur (h)', width: 100, editable: true },
        {
            headerName: 'Predecessors',
            width: 150,
            valueGetter: (params: ValueGetterParams) => {
                if (!params.data.dependencies || params.data.dependencies.length === 0) return '';
                return params.data.dependencies.map((d: Dependency) => {
                    return `${d.target_id}${d.relation === 'FS' ? '' : d.relation}${d.lag > 0 ? '+' + (d.lag).toFixed(1) + 'h' : ''}`;
                }).join(', ');
            }
        },
        { field: 'total_float', headerName: 'Total Float', width: 100, valueFormatter: (p: ValueFormatterParams) => p.value !== undefined ? (p.value).toFixed(1) + 'h' : '' },
        { field: 'responsible_party', headerName: 'Owner', width: 150, editable: true },
        {
            headerName: 'Actions',
            width: 100, // Slightly wider for icon buttons
            pinned: 'right',
            cellRenderer: (params: ICellRendererParams) => (
                <div className="flex gap-3 items-center justify-center h-full">
                    <button
                        onClick={() => openEditPanel(params.data)}
                        className="text-muted-foreground hover:text-primary transition-colors p-1 rounded-md hover:bg-muted"
                        title="Edit Task"
                    >
                        <Pencil className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => handleDeleteTask(params.data.id)}
                        className="text-muted-foreground hover:text-destructive transition-colors p-1 rounded-md hover:bg-muted"
                        title="Delete Task"
                    >
                        <Trash2 className="w-4 h-4" />
                    </button>
                </div>
            )
        }
    ], [openEditPanel, collapsedWbs, project?.tasks, toggleWbs]);



    if (loading || !project) {
        return (
            <div className="flex flex-col items-center justify-center h-full space-y-4">
                <div className="w-8 h-8 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
                <div className="text-sm text-muted-foreground font-medium animate-pulse">Loading Project Data...</div>
            </div>
        );
    }

    return (
        <div className="flex flex-col h-full bg-background text-foreground animate-in fade-in duration-300 relative">

            {/* --- Top Navigation Bar --- */}
            <div className="flex items-center justify-between px-6 py-3 border-b border-border bg-background sticky top-0 z-10 transition-colors">
                <div className="flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={onBack} className="rounded-full h-8 w-8">
                        <ArrowLeft className="w-4 h-4" />
                    </Button>
                    <div>
                        <div className="flex items-center gap-2 text-[11px] font-black uppercase text-muted-foreground tracking-widest mb-0.5">
                            <span className="opacity-70">Projects</span>
                            <ChevronRight className="w-2.5 h-2.5 opacity-50" />
                            <span className="opacity-100">{project.industry || 'General Engineering'}</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <h1 className="text-lg font-black uppercase tracking-tighter text-foreground leading-none">{project.title}</h1>
                            <Badge variant={project.status === 'active' ? "success" : "outline"} className="h-4">
                                {project.status}
                            </Badge>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-4">
                    <div className="flex text-[11px] font-black uppercase tracking-widest text-muted-foreground bg-muted/20 px-4 py-1.5 border border-border h-10 items-center gap-6">
                        <div className="flex flex-col">
                            <span className="opacity-60 text-[8px] leading-tight">PERF Index / CPI</span>
                            <span className={cn("font-mono font-bold leading-none", (stats?.performance?.cpi || 1) < 1 ? "text-red-600" : "text-emerald-600")}>{(stats?.performance?.cpi || 1.0).toFixed(2)}</span>
                        </div>
                        <div className="w-px h-5 bg-border"></div>
                        <div className="flex flex-col">
                            <span className="opacity-60 text-[8px] leading-tight">PERF Index / SPI</span>
                            <span className={cn("font-mono font-bold leading-none", (stats?.performance?.spi || 1) < 1 ? "text-red-600" : "text-emerald-600")}>{(stats?.performance?.spi || 1.0).toFixed(2)}</span>
                        </div>
                    </div>

                    <div className="flex flex-col items-end">
                        <Button
                            variant="primary"
                            size="sm"
                            onClick={handleRunSimulation}
                            disabled={isSimulating}
                            className="bg-primary hover:bg-primary/90 text-primary-foreground font-black uppercase tracking-widest text-[11px] h-10 px-6 rounded-none border border-border shadow-none"
                        >
                            {isSimulating ? <div className="w-3 h-3 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" /> : <Play className="w-3.5 h-3.5 fill-current mr-2" />}
                            {isSimulating ? "PROCESSING..." : "AUTO-SCHEDULE"}
                        </Button>
                    </div>

                    <Button variant="ghost" size="icon" onClick={handleDeleteProject} className="text-muted-foreground/50 hover:text-red-500 h-8 w-8 hover:bg-transparent">
                        <Trash2 className="w-4 h-4" />
                    </Button>
                </div>
            </div>

            {/* --- View Tabs --- */}
            <div className="px-6 border-b border-border bg-background flex items-center gap-1 overflow-x-auto h-12">
                {[
                    { id: 'list', label: 'TASK GRID', icon: List },
                    { id: 'kanban', label: 'PIPELINE', icon: KanbanIcon },
                    { id: 'gantt', label: 'TIMELINE', icon: GanttChartSquare },
                    { id: 'network', label: 'TOPOLOGY', icon: Network },
                    { id: 'calendar', label: 'CALENDAR', icon: Calendar },
                    { id: 'risks', label: 'RISK LOG', icon: ShieldAlert },
                    { id: 'mto', label: 'QUANTITIES', icon: Package },
                    { id: 'reports', label: 'INSIGHTS', icon: FileText },
                    { id: 'templates', label: 'TEMPLATES', icon: Calculator },
                ].map((tab) => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as TabType)}
                        className={cn(
                            "flex items-center gap-2 px-6 h-full text-[11px] font-black uppercase tracking-[0.15em] border-b-2 transition-all whitespace-nowrap",
                            activeTab === tab.id
                                ? "border-primary text-primary bg-primary/5"
                                : "border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/10 opacity-70"
                        )}
                    >
                        <tab.icon className="w-3.5 h-3.5" />
                        {tab.label}
                    </button>
                ))}
            </div>

            {/* --- Main Content Area --- */}
            <div className="flex-1 overflow-y-auto overflow-x-hidden bg-background relative scrollbar-thin">
                <div className="p-6 min-h-full flex flex-col">

                    {activeTab === 'list' && (
                        <div className="bg-background border border-border flex-1 flex flex-col ag-theme-quartz-dark shadow-sm min-h-[500px]">
                            {/* AG Grid Container */}
                            <div className="flex-1 w-full" style={{ height: '100%' }}>
                                <AgGridReact
                                    theme="legacy"
                                    rowData={visibleTasks}
                                    columnDefs={columnDefs}
                                    onCellValueChanged={async (event) => {
                                        try {
                                            const field = event.colDef.field;
                                            if (!field) return;

                                            // eslint-disable-next-line @typescript-eslint/no-explicit-any
                                            const updatedTask: any = {};
                                            updatedTask[field] = event.newValue;

                                            // Auto-calc logic: If Duration or Start changes, update End
                                            // Assuming original_duration is in DAYS (or standard units)
                                            if (field === 'original_duration' || field === 'planned_start') {
                                                const dur = field === 'original_duration' ? parseFloat(event.newValue) : event.data.original_duration;
                                                const startStr = field === 'planned_start' ? event.newValue : event.data.planned_start;

                                                if (dur && startStr) {
                                                    const startDate = new Date(startStr);
                                                    if (!isNaN(startDate.getTime())) {
                                                        // Simple calc: Add hours to start date
                                                        const endDate = new Date(startDate);
                                                        endDate.setHours(endDate.getHours() + dur);
                                                        updatedTask.planned_end = endDate.toISOString();

                                                        // Update grid locally for immediate feedback
                                                        event.node.setDataValue('planned_end', updatedTask.planned_end);
                                                    }
                                                }
                                            }

                                            // Call API to update task
                                            await axios.put(`${apiUrl}/tasks/${event.data.id}`, updatedTask);
                                            console.log("Task updated:", event.data.id);
                                        } catch (error) {
                                            console.error("Failed to update task:", error);
                                            // Revert change?
                                            event.node.setDataValue(event.colDef.field as string, event.oldValue);
                                        }
                                    }}
                                    defaultColDef={{
                                        sortable: true,
                                        filter: true,
                                        resizable: true,
                                        editable: true,
                                    }}
                                    rowClassRules={{
                                        'font-bold bg-muted/20': (params) => params.data?.is_summary === true
                                    }}
                                />
                            </div>
                            {project.tasks.length === 0 && (
                                <div className="p-12 text-center text-muted-foreground absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
                                    <List className="w-12 h-12 mx-auto mb-4 opacity-20" />
                                    <p>No tasks found.</p>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'kanban' && (
                        <div className="h-[calc(100vh-250px)] min-h-[500px] border border-border shadow-sm bg-muted/10">
                            <KanbanBoard tasks={project.tasks} onUpdateStatus={handleUpdateTaskStatus} />
                        </div>
                    )}
                    {activeTab === 'gantt' && (
                        <div className="h-[calc(100vh-250px)] min-h-[500px] border border-border shadow-sm">
                            <GanttChart tasks={project.tasks} />
                        </div>
                    )}
                    {activeTab === 'risks' && <RiskManagement projectId={projectId} tasks={project.tasks} />}
                    {activeTab === 'calendar' && <CalendarView tasks={project.tasks} />}
                    {activeTab === 'network' && <ProjectNetworkView tasks={project.tasks} />}

                    {activeTab === 'mto' && (
                        <div className="bg-card border border-border rounded-lg shadow-sm">
                            <table className="w-full text-left">
                                <thead className="bg-muted/50 border-b border-border text-xs uppercase font-semibold text-muted-foreground">
                                    <tr>
                                        <th className="px-4 py-3">Asset Name</th>
                                        <th className="px-4 py-3">Category</th>
                                        <th className="px-4 py-3 text-right">Quantity</th>
                                        <th className="px-4 py-3 text-right">Unit Price</th>
                                        <th className="px-4 py-3 text-right">Total</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                    {project.tasks.flatMap(t => t.materials || []).concat(project.materials || []).map((mat, i) => (
                                        <tr key={i} className="hover:bg-muted/50">
                                            <td className="px-4 py-3 text-sm font-medium">{mat.name}</td>
                                            <td className="px-4 py-3 text-xs text-muted-foreground">{mat.category}</td>
                                            <td className="px-4 py-3 text-sm tabular-nums text-right font-mono">{mat.quantity} {mat.unit}</td>
                                            <td className="px-4 py-3 text-sm tabular-nums text-right font-mono">${mat.unit_price.toFixed(2)}</td>
                                            <td className="px-4 py-3 text-sm tabular-nums text-right font-mono font-bold">${mat.total_price.toFixed(2)}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {activeTab === 'reports' && (
                        <div className="h-full flex flex-col p-6 overflow-hidden">
                            {!reportContent ? (
                                <div className="flex-1 flex flex-col items-center justify-center border-2 border-dashed border-border rounded-lg bg-muted/5">
                                    <FileText className="w-12 h-12 text-muted-foreground mb-4" />
                                    <h3 className="text-lg font-medium">AI Report Generator</h3>
                                    <p className="text-sm text-muted-foreground max-w-sm text-center mt-2 mb-6">
                                        Generate comprehensive project status reports, risk assessments, and executive summaries using our neural engine.
                                    </p>
                                    <button
                                        onClick={handleGenerateReport}
                                        disabled={generatingReport}
                                        className="px-4 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-md hover:opacity-90 disabled:opacity-50 flex items-center gap-2"
                                    >
                                        {generatingReport ? (
                                            <>
                                                <div className="w-4 h-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
                                                Generating Analysis...
                                            </>
                                        ) : (
                                            "Generate Report"
                                        )}
                                    </button>
                                </div>
                            ) : (
                                <div className="flex-1 flex flex-col bg-card border border-border rounded-lg shadow-sm overflow-hidden">
                                    <div className="flex items-center justify-between px-6 py-4 border-b border-border bg-muted/30">
                                        <h2 className="text-lg font-bold">Project Intelligence Report</h2>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => setReportContent(null)}
                                                className="text-xs px-3 py-1.5 border border-border rounded hover:bg-muted"
                                            >
                                                Back
                                            </button>
                                            <button className="text-xs px-3 py-1.5 bg-primary text-primary-foreground rounded hover:opacity-90 flex items-center gap-1">
                                                <Download className="w-3 h-3" /> Export PDF
                                            </button>
                                        </div>
                                    </div>
                                    <div className="flex-1 overflow-y-auto p-8 prose prose-sm max-w-none dark:prose-invert">
                                        <div className="whitespace-pre-wrap font-sans text-sm leading-relaxed text-muted-foreground">
                                            {reportContent}
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {activeTab === 'templates' && (
                        <div className="space-y-8">
                            {!templates ? (
                                <div className="text-center text-muted-foreground py-10">Loading Templates...</div>
                            ) : (
                                <>
                                    <div className="bg-card border border-border rounded-lg p-6">
                                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                            <Package className="w-5 h-5 text-primary" /> Bill of Quantities (BOQ)
                                        </h3>
                                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                            {boqList.map(renderBoqCard)}
                                        </div>
                                    </div>

                                    <div className="bg-card border border-border rounded-lg p-6">
                                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                            <Settings className="w-5 h-5 text-primary" /> Vendor Data Requirements (VDR)
                                        </h3>
                                        <div className="space-y-6">
                                            <div>
                                                <h4 className="text-sm font-semibold uppercase text-muted-foreground mb-3">Rotating Equipment</h4>
                                                <div className="space-y-2">
                                                    {vdrRotatingList.map(renderVdrRow)}
                                                </div>
                                            </div>
                                            <div>
                                                <h4 className="text-sm font-semibold uppercase text-muted-foreground mb-3">Pressure Vessels</h4>
                                                <div className="space-y-2">
                                                    {vdrVesselList.map(renderVdrRow)}
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="bg-card border border-border rounded-lg p-6">
                                        <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                                            <CheckCircle2 className="w-5 h-5 text-primary" /> Inspection & Test Plan (ITP)
                                        </h3>
                                        <div className="overflow-x-auto">
                                            <table className="w-full text-sm">
                                                <thead className="bg-muted/50 text-xs uppercase text-muted-foreground">
                                                    <tr>
                                                        <th className="px-4 py-2 text-left">Activity</th>
                                                        <th className="px-4 py-2 text-left">Check/Test</th>
                                                        <th className="px-4 py-2 text-left">Acceptance Criteria</th>
                                                        <th className="px-4 py-2 text-left">Verifier</th>
                                                    </tr>
                                                </thead>
                                                <tbody className="divide-y divide-border">
                                                    {itpList.map(renderItpRow)}
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>

            {/* --- Slide-out Edit Panel --- */}
            {isEditPanelOpen && (
                <div className="fixed inset-0 z-50 flex justify-end bg-black/20 backdrop-blur-[1px]">
                    <div className="w-[450px] bg-background border-l border-border shadow-2xl h-full flex flex-col animate-in slide-in-from-right duration-300">
                        <div className="px-6 py-4 border-b border-border flex items-center justify-between">
                            <h2 className="text-lg font-bold">Edit Task</h2>
                            <button onClick={closeEditPanel} className="p-2 hover:bg-muted rounded-full">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-5">
                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold uppercase text-muted-foreground">Title</label>
                                <input
                                    type="text"
                                    value={editTaskData.title || ''}
                                    onChange={(e) => setEditTaskData({ ...editTaskData, title: e.target.value })}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded-md text-sm font-medium focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">WBS Code</label>
                                    <input
                                        type="text"
                                        value={editTaskData.wbs_code || ''}
                                        onChange={(e) => setEditTaskData({ ...editTaskData, wbs_code: e.target.value })}
                                        className="w-full px-3 py-2 bg-muted/50 border border-border rounded-md text-sm"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Status</label>
                                    <select
                                        value={editTaskData.status || 'not_started'}
                                        onChange={(e) => setEditTaskData({ ...editTaskData, status: e.target.value })}
                                        className="w-full px-3 py-2 bg-muted/50 border border-border rounded-md text-sm"
                                    >
                                        <option value="not_started">Not Started</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="stalled">Stalled</option>
                                        <option value="completed">Completed</option>
                                        <option value="cancelled">Cancelled</option>
                                    </select>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Type</label>
                                    <select
                                        value={editTaskData.task_type || 'task'}
                                        onChange={(e) => setEditTaskData({ ...editTaskData, task_type: e.target.value })}
                                        className="w-full px-3 py-2 bg-muted/50 border border-border rounded-md text-sm"
                                    >
                                        <option value="task">Standard Task</option>
                                        <option value="milestone">Milestone</option>
                                        <option value="summary">Summary</option>
                                    </select>
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Discipline</label>
                                    <select
                                        value={editTaskData.discipline || 'General'}
                                        onChange={(e) => setEditTaskData({ ...editTaskData, discipline: e.target.value })}
                                        className="w-full px-3 py-2 bg-muted/50 border border-border rounded-md text-sm"
                                    >
                                        <option value="General">General</option>
                                        <option value="Design">Design</option>
                                        <option value="Procurement">Procurement</option>
                                        <option value="Construction">Construction</option>
                                        <option value="Commissioning">Commissioning</option>
                                    </select>
                                </div>
                            </div>

                            {editTaskData.discipline === 'Design' && (
                                <div className="flex items-center gap-2 p-3 bg-primary/10 border border-primary/20 rounded-md">
                                    <input
                                        type="checkbox"
                                        id="is_deliverable"
                                        checked={editTaskData.is_deliverable || false}
                                        onChange={(e) => setEditTaskData({ ...editTaskData, is_deliverable: e.target.checked })}
                                        className="w-4 h-4 rounded border-primary"
                                    />
                                    <label htmlFor="is_deliverable" className="text-sm font-medium cursor-pointer select-none">
                                        Mark as Deliverable (Document/Drawing)
                                    </label>
                                </div>
                            )}



                            <div className="space-y-1.5">
                                <label className="text-xs font-semibold uppercase text-muted-foreground">Description</label>
                                <textarea
                                    value={editTaskData.description || ''}
                                    onChange={(e) => setEditTaskData({ ...editTaskData, description: e.target.value })}
                                    className="w-full px-3 py-2 bg-muted/50 border border-border rounded-md text-sm min-h-[80px]"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">Start Date</label>
                                    <input
                                        type="date"
                                        value={editTaskData.planned_start?.split('T')[0] || ''}
                                        onChange={(e) => setEditTaskData({ ...editTaskData, planned_start: e.target.value })}
                                        className="w-full px-3 py-2 bg-muted/50 border border-border rounded-md text-sm"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="text-xs font-semibold uppercase text-muted-foreground">End Date</label>
                                    <input
                                        type="date"
                                        value={editTaskData.planned_end?.split('T')[0] || ''}
                                        onChange={(e) => setEditTaskData({ ...editTaskData, planned_end: e.target.value })}
                                        className="w-full px-3 py-2 bg-muted/50 border border-border rounded-md text-sm"
                                    />
                                </div>
                            </div>

                            {/* Dependencies Section */}
                            <div className="pt-4 border-t border-border">
                                <label className="text-xs font-semibold uppercase text-muted-foreground mb-3 block">Dependencies</label>
                                <div className="space-y-2">
                                    {editTaskData.dependencies?.map((dep, idx) => (
                                        <div key={idx} className="flex gap-2 items-center">
                                            <select
                                                value={dep.target_id}
                                                onChange={(e) => {
                                                    const newDeps = [...(editTaskData.dependencies || [])];
                                                    newDeps[idx].target_id = parseInt(e.target.value);
                                                    setEditTaskData({ ...editTaskData, dependencies: newDeps });
                                                }}
                                                className="flex-1 bg-muted/50 border border-border rounded px-2 py-1 text-xs"
                                            >
                                                {project.tasks.filter(t => t.id !== editingTaskId).map(t => (
                                                    <option key={t.id} value={t.id}>{t.title.substring(0, 30)}...</option>
                                                ))}
                                            </select>
                                            <select
                                                value={dep.relation}
                                                onChange={(e) => {
                                                    const newDeps = [...(editTaskData.dependencies || [])];
                                                    newDeps[idx].relation = e.target.value;
                                                    setEditTaskData({ ...editTaskData, dependencies: newDeps });
                                                }}
                                                className="w-16 bg-muted/50 border border-border rounded px-2 py-1 text-xs"
                                            >
                                                <option value="FS">FS</option>
                                                <option value="SS">SS</option>
                                                <option value="FF">FF</option>
                                                <option value="SF">SF</option>
                                            </select>
                                            <button
                                                onClick={() => {
                                                    const newDeps = editTaskData.dependencies?.filter((_, i) => i !== idx);
                                                    setEditTaskData({ ...editTaskData, dependencies: newDeps });
                                                }}
                                                className="text-red-500 hover:bg-red-50 p-1 rounded"
                                            >
                                                <X className="w-3 h-3" />
                                            </button>
                                        </div>
                                    ))}
                                    <button
                                        onClick={() => {
                                            const otherTask = project.tasks.find(t => t.id !== editingTaskId);
                                            if (otherTask) {
                                                setEditTaskData({
                                                    ...editTaskData,
                                                    dependencies: [
                                                        ...(editTaskData.dependencies || []),
                                                        { target_id: otherTask.id, relation: 'FS', lag: 0 }
                                                    ]
                                                });
                                            }
                                        }}
                                        className="text-xs font-semibold text-primary hover:underline flex items-center gap-1 mt-2"
                                    >
                                        <Plus className="w-3 h-3" /> Add Dependency
                                    </button>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-border bg-muted/20 flex items-center justify-between">
                            <button
                                onClick={() => { if (editingTaskId) handleDeleteTask(editingTaskId); }}
                                className="flex items-center text-destructive hover:bg-destructive/10 hover:text-destructive-foreground px-3 py-2 rounded-md transition-colors text-sm font-medium"
                            >
                                <Trash2 className="w-4 h-4 mr-2" />
                                Delete Task
                            </button>
                            <div className="flex gap-3">
                                <button
                                    onClick={closeEditPanel}
                                    className="px-4 py-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded-md transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleSaveTask}
                                    className="px-6 py-2 bg-primary text-primary-foreground text-sm font-medium rounded-md shadow-sm hover:opacity-90 transition-all transform active:scale-95"
                                >
                                    Save Changes
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
