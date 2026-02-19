"use client";

import React, { useState } from 'react';
import { Gantt, Task, ViewMode } from 'gantt-task-react';
import "gantt-task-react/dist/index.css";
import { cn } from "@/lib/utils";

interface Dependency {
    target_id: number;
    relation: string;
    lag: number;
}

interface ProjectTask {
    id: number;
    wbs_code?: string;
    title: string;
    description: string;
    status: string;
    priority?: string;
    task_type?: string;
    planned_start?: string;
    planned_end?: string;
    original_duration?: number; // Renamed from estimated_hours
    dependencies: Dependency[];
    project_id?: number;
    // Hierarchy
    is_summary?: boolean;
    outline_level?: number;
}

export default function GanttChart({ tasks }: { tasks: ProjectTask[] }) {
    const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Month);
    const [isChecked, setIsChecked] = useState(true);
    const [isQuarter, setIsQuarter] = useState(false);

    if (!tasks || tasks.length === 0) {
        return <div className="p-10 text-center text-muted-foreground">No tasks available for Gantt Chart.</div>;
    }

    // Map ProjectTask to Gantt Task
    const ganttTasks: Task[] = tasks.map(t => {
        const start = t.planned_start ? new Date(t.planned_start) : new Date();
        const end = t.planned_end ? new Date(t.planned_end) : new Date(start.getTime() + (t.original_duration || 1) * 3600 * 1000);

        // Ensure end > start
        if (end <= start) end.setTime(start.getTime() + 3600 * 1000);

        return {
            start: start,
            end: end,
            name: t.title,
            id: t.id.toString(),
            type: t.task_type === 'milestone' ? 'milestone' : 'task',
            progress: t.status === 'completed' ? 100 : t.status === 'in_progress' ? 50 : 0,
            isDisabled: false,
            styles: {
                progressColor: t.status === 'completed' ? '#10b981' : '#3b82f6',
                progressSelectedColor: '#2563eb',
            },
            dependencies: t.dependencies?.map(d => d.target_id.toString()),
            project: t.project_id?.toString()
        };
    });

    const handleTaskChange = (task: Task) => {
        console.log("On date change", task.id, task.start, task.end);
    };

    const handleProgressChange = async (task: Task) => {
        console.log("On progress change", task.id, task.progress);
    };

    const handleDblClick = (task: Task) => {
        console.log("On Double Click", task);
    };

    const handleSelect = (_task: Task, isSelected: boolean) => {
        console.log(_task.name + " has " + (isSelected ? "selected" : "unselected"));
    };

    const handleExpanderClick = (_task: Task) => {
        console.log("On expander click");
    };

    const setMode = (mode: ViewMode) => {
        setIsQuarter(false);
        setViewMode(mode);
    };

    const setQuarterMode = () => {
        setIsQuarter(true);
        setViewMode(ViewMode.Month);
    };

    return (
        <div className="flex flex-col h-full bg-background border border-border overflow-hidden">
            {/* Toolbar */}
            <div className="flex items-center justify-between p-2 border-b border-border bg-background">
                <div className="text-[11px] font-black uppercase tracking-[0.2em] text-muted-foreground px-3">Timeline Topology</div>
                <div className="flex bg-muted/30 border border-border rounded-none p-0.5 gap-1">
                    <button onClick={() => setMode(ViewMode.Day)} className={cn("px-4 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-none transition-all", (!isQuarter && viewMode === ViewMode.Day) ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted")}>Day</button>
                    <button onClick={() => setMode(ViewMode.Week)} className={cn("px-4 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-none transition-all", (!isQuarter && viewMode === ViewMode.Week) ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted")}>Week</button>
                    <button onClick={() => setMode(ViewMode.Month)} className={cn("px-4 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-none transition-all", (!isQuarter && viewMode === ViewMode.Month) ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted")}>Month</button>
                    <button onClick={setQuarterMode} className={cn("px-4 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-none transition-all", isQuarter ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted")}>Quarter</button>
                    <button onClick={() => setMode(ViewMode.Year)} className={cn("px-4 py-1.5 text-[10px] font-black uppercase tracking-widest rounded-none transition-all", (!isQuarter && viewMode === ViewMode.Year) ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-muted")}>Year</button>
                </div>
                <div className="flex items-center gap-4 px-2">
                    <label className="text-[11px] font-bold uppercase tracking-widest flex items-center gap-2 cursor-pointer text-muted-foreground hover:text-foreground">
                        <input
                            type="checkbox"
                            checked={isChecked}
                            onChange={e => setIsChecked(e.target.checked)}
                            className="w-3.5 h-3.5 accent-primary"
                        />
                        WBS List
                    </label>
                </div>
            </div>

            <div className="flex-1 overflow-auto bg-background gantt-container">
                <style jsx global>{`
                    /* General Gantt Container Fixes */
                    .gantt-container {
                        background-color: var(--background) !important;
                        color: var(--foreground) !important;
                    }

                    /* WBS List Area - Coordinate with background */
                    .gantt-container ._3af_6 { 
                        background-color: var(--background) !important; 
                        color: var(--foreground) !important; 
                        border-right: 1px solid var(--border) !important; /* Region Separator Vertical Line */
                        font-weight: 700;
                        font-family: inherit;
                        display: flex;
                        align-items: center;
                    }

                    /* Header / Timeline Cells */
                    .gantt-container ._2uS_8 { 
                        background-color: var(--background) !important; /* Changed from muted to sync background */
                        color: var(--muted-foreground) !important; 
                        border-bottom: 1px solid var(--border) !important;
                        border-right: 1px solid var(--border) !important;
                    }

                    /* Grid Lines / Zebra Striping */
                    .gantt-container ._3_h_6 { 
                        border-bottom: 1px solid var(--border) !important; 
                        border-right: 1px solid var(--border) !important; 
                    }
                    
                    /* SVG Grid Line colors for dark mode context */
                    [data-theme='dark'] .gantt-container ._1_h_6 { fill: #1a1a1e !important; }
                    [data-theme='dark'] .gantt-container ._2rB_5 { fill: #09090b !important; }
                    [data-theme='dark'] .gantt-container ._3_h_6 { fill: #09090b !important; }

                    /* Timeline Text Label */
                    .gantt-container ._278_3 { 
                        fill: var(--muted-foreground) !important; 
                        font-weight: 800; 
                        font-size: 10px; 
                        text-transform: uppercase; 
                        letter-spacing: 0.1em;
                    }

                    /* Task Bar Label Text - Critical for contrast */
                    .gantt-container ._3shz- {
                        fill: var(--foreground) !important;
                        font-weight: 800 !important;
                        font-size: 11px !important;
                    }

                    /* SVG Backgrounds */
                    .gantt-container ._3eS_5 { fill: var(--muted) !important; } /* Today highlight */
                    .gantt-container ._1_h_6 { fill: var(--border) !important; } /* Grid lines fill */
                    .gantt-container ._2rB_5 { fill: var(--background) !important; } /* Main chart background */
                    .gantt-container ._3_h_6 { fill: var(--background) !important; } /* Ensure grid area background matches */
                    
                    /* Tooltip Styling */
                    .gantt-container ._3m_7S {
                        background-color: var(--popover) !important;
                        color: var(--popover-foreground) !important;
                        border: 1px solid var(--border) !important;
                        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                        border-radius: 0 !important;
                    }
                    
                    /* Enforce text contrast based on theme */
                    :root {
                        --gantt-text: var(--foreground);
                    }
                    
                    [data-theme='light'] .gantt-container ._3af_6,
                    [data-theme='light'] .gantt-container ._3shz- {
                        color: #000000 !important;
                        fill: #000000 !important;
                    }

                    /* Dark Mode Zebra Striping & Text overrides */
                    [data-theme='dark'] .gantt-container ._3af_6,
                    [data-theme='dark'] .gantt-container ._3shz- {
                        color: #ffffff !important;
                        fill: #ffffff !important;
                    }

                    /* NUCLEAR OVERRIDE for Gantt Dark Mode */
                    [data-theme='dark'] .gantt-container rect,
                    [data-theme='dark'] .gantt-container path,
                    [data-theme='dark'] .gantt-container circle,
                    [data-theme='dark'] .gantt-container foreignObject,
                    [data-theme='dark'] .gantt-container ._3af_6, 
                    [data-theme='dark'] .gantt-container ._3af_6:nth-child(even),
                    [data-theme='dark'] .gantt-container ._3af_6:nth-child(odd),
                    [data-theme='dark'] .gantt-container ._2rB_5,
                    [data-theme='dark'] .gantt-container ._3_h_6 {
                        fill: var(--background) !important;
                        background-color: var(--background) !important;
                    }

                    /* Force Text Color */
                    [data-theme='dark'] .gantt-container text,
                    [data-theme='dark'] .gantt-container ._3af_6 {
                         fill: #ffffff !important;
                         color: #ffffff !important;
                    }

                    /* Keep Bars Colored (override the global rect override above for bars) */
                    [data-theme='dark'] .gantt-container ._35nLX {
                        fill: #3b82f6 !important; /* Blue for bars */
                    }
                    [data-theme='dark'] .gantt-container ._35nLX:hover {
                         fill: #2563eb !important;
                    }
                    [data-theme='dark'] .gantt-container ._2eZzS {
                        fill: #10b981 !important; /* Green for completed */
                    }

                    /* Grid Lines - subtle */
                    [data-theme='dark'] .gantt-container ._1_h_6 {
                        fill: #27272a !important; /* Zinc-900 line */
                    }
                    
                    /* Today Highlight */
                     [data-theme='dark'] .gantt-container ._3eS_5 {
                        fill: rgba(255, 255, 255, 0.05) !important;
                     }
                `}</style>
                <Gantt
                    tasks={ganttTasks}
                    viewMode={viewMode}
                    onDateChange={handleTaskChange}
                    onDelete={handleTaskChange}
                    onProgressChange={handleProgressChange}
                    onDoubleClick={handleDblClick}
                    onSelect={handleSelect}
                    onExpanderClick={handleExpanderClick}
                    listCellWidth={isChecked ? "200px" : ""}
                    columnWidth={isQuarter ? 40 : viewMode === ViewMode.Month ? 100 : 70}
                    rowHeight={40}
                    barCornerRadius={0}
                    barFill={70}
                    projectBackgroundColor="var(--primary)"
                    projectBackgroundSelectedColor="var(--primary)"
                    headerHeight={50}
                    handleWidth={8}
                    fontFamily="inherit"
                    fontSize="13px"
                    todayColor="rgba(var(--primary-rgb), 0.1)"
                />
            </div>
        </div>
    );
}
