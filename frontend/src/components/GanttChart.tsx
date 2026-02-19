"use client";

import React, { useState, useEffect } from 'react';
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

export default function GanttChart({ tasks, onEditTask }: { tasks: ProjectTask[], onEditTask?: (task: any) => void }) {
    const [viewMode, setViewMode] = useState<ViewMode>(ViewMode.Month);
    const [isChecked, setIsChecked] = useState(true);
    const [isQuarter, setIsQuarter] = useState(false);

    // Theme Detection Hook
    const useTheme = () => {
        const [isDark, setIsDark] = useState(true); // Default to dark as per layout
        useEffect(() => {
            const updateTheme = () => setIsDark(document.documentElement.classList.contains('dark'));
            updateTheme(); // Initial check

            const observer = new MutationObserver(updateTheme);
            observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

            return () => observer.disconnect();
        }, []);
        return isDark;
    };

    const isDark = useTheme();

    if (!tasks || tasks.length === 0) {
        return <div className="p-10 text-center text-muted-foreground">No tasks available for Gantt Chart.</div>;
    }

    // Map ProjectTask to Gantt Task
    const ganttTasks: Task[] = tasks.map(t => {
        const start = t.planned_start ? new Date(t.planned_start) : new Date();
        const end = t.planned_end ? new Date(t.planned_end) : new Date(start.getTime() + (t.original_duration || 1) * 3600 * 1000);

        // Ensure end > start
        if (end <= start) end.setTime(start.getTime() + 3600 * 1000);

        // Determine Task Type and Styles based on Hierarchy and Theme
        // Dark Mode: Background Dark -> Bars should be Light/Contrast
        // Light Mode: Background Light -> Bars should be Dark/Contrast

        let type: 'task' | 'milestone' | 'project' = 'task';

        // Default Colors (Will be overridden)
        let progressColor = '#4b5563';
        let backgroundColor = '#f3f4f6';
        let backgroundSelectedColor = '#e5e7eb';

        const level = t.outline_level || 1;

        if (isDark) {
            // DARK THEME PALETTE
            // Background is Dark (gray-900 etc)
            // Bars should be lighter / distinct

            if (t.task_type === 'milestone') {
                // Gold
                progressColor = '#FBBF24'; // amber-400
                backgroundColor = '#F59E0B'; // amber-500
                backgroundSelectedColor = '#D97706';
            } else if (t.is_summary) {
                // Bracket style usually, but here bar.
                // Summary: Dark grey but visible
                progressColor = '#A1A1AA'; // zinc-400
                backgroundColor = '#52525B'; // zinc-600
                backgroundSelectedColor = '#71717A';
            } else if (t.status === 'completed') {
                // Green, but maybe muted in dark mode? No, bright is good.
                progressColor = '#34D399'; // emerald-400
                backgroundColor = '#059669'; // emerald-600
                backgroundSelectedColor = '#10B981';
            } else {
                // Standard Task
                // Bar Background (Planned): Dark Grey/Blueish? 
                // We want "Progress" to be Light/Pale Grey as requested: "进度条/里程表，为亮色或淡灰"

                // Planned Period (Background of the bar):
                backgroundColor = '#4B5563'; // gray-600

                // Actual Progress (Foreground of the bar):
                progressColor = '#E5E7EB'; // gray-200 (Light Grey)

                backgroundSelectedColor = '#6B7280'; // gray-500
            }

        } else {
            // LIGHT THEME
            // Background Light
            // Bars Darker
            if (t.task_type === 'milestone') {
                progressColor = '#000000';
                backgroundColor = '#000000';
                backgroundSelectedColor = '#333333';
            } else if (t.is_summary) {
                progressColor = '#000000';
                backgroundColor = '#000000';
                backgroundSelectedColor = '#333333';
            } else if (t.status === 'completed') {
                progressColor = '#10B981';
                backgroundColor = '#D1FAE5';
                backgroundSelectedColor = '#A7F3D0';
            } else {
                // Standard: Dark bar on light bg
                // Progress: Dark
                // Planned: Light Grey
                backgroundColor = '#E5E7EB'; // gray-200
                progressColor = '#374151'; // gray-700
                backgroundSelectedColor = '#9CA3AF';
            }
        }

        if (t.task_type === 'milestone') type = 'milestone';
        else if (t.is_summary) type = 'project';

        return {
            start: start,
            end: end,
            name: t.title,
            id: t.id.toString(),
            type: type,
            progress: t.status === 'completed' ? 100 : t.status === 'in_progress' ? 50 : 0,
            isDisabled: false,
            styles: {
                progressColor: progressColor,
                progressSelectedColor: progressColor, // Keep same when selected
                backgroundColor: backgroundColor,
                backgroundSelectedColor: backgroundSelectedColor,
            },
            // Deduplicate dependencies to avoid Gantt key collision errors (Arrow from X to Y)
            dependencies: Array.from(new Set(t.dependencies?.map(d => d.target_id.toString()) || [])),
            project: t.project_id?.toString(),
            // Store original task data for editing
            originalTask: t
        } as Task & { originalTask: ProjectTask };
    });

    const handleTaskChange = (task: Task) => {
        console.log("On date change", task.id, task.start, task.end);
    };

    const handleProgressChange = async (task: Task) => {
        console.log("On progress change", task.id, task.progress);
    };

    const handleDblClick = (task: Task) => {
        // @ts-ignore
        if (onEditTask && task.originalTask) {
            // @ts-ignore
            onEditTask(task.originalTask);
        }
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
                    /* --- ClickUp Inspired Gantt Minimalist Theme --- */
                    
                    .gantt-container {
                        background-color: var(--background) !important;
                        color: var(--foreground) !important;
                        font-family: inherit;
                        border: none !important;
                    }

                    /* 1. WBS List Area - Clean & Single Color */
                    .gantt-container ._3af_6 { 
                        background-color: var(--background) !important; 
                        color: var(--foreground) !important; 
                        border-right: 1px solid var(--border) !important;
                        border-bottom: 1px solid var(--border) !important;
                        font-weight: 500;
                    }
                    
                    /* Remove Zebra Striping - force all rows to match background */
                    .gantt-container ._3af_6:nth-child(even),
                    .gantt-container ._3af_6:nth-child(odd) {
                        background-color: var(--background) !important;
                    }

                    /* 2. Header / Timeline Cells */
                    .gantt-container ._2uS_8 { 
                        background-color: var(--muted) !important; 
                        color: var(--muted-foreground) !important; 
                        border-bottom: 1px solid var(--border) !important;
                        border-right: 1px solid var(--border) !important;
                        text-transform: uppercase;
                        font-size: 10px;
                        font-weight: 700;
                        letter-spacing: 0.05em;
                    }

                    /* 3. Main Chart Background - No coord/dark uncoordinated blocks */
                    .gantt-container ._2rB_5 { 
                        fill: var(--background) !important; 
                    }
                    .gantt-container ._3_h_6 { 
                        fill: var(--background) !important; 
                        border-bottom: 1px solid var(--border) !important;
                    }

                    /* 4. Grid Lines - Minimalist & Low Contrast */
                    .gantt-container ._1_h_6 { 
                        fill: var(--border) !important;
                        opacity: 0.3; /* Make grid lines very subtle like ClickUp */
                    }
                    
                    /* Vertical lines across tasks */
                    .gantt-container line {
                        stroke: var(--border) !important;
                        stroke-opacity: 0.2;
                    }

                    /* 5. Timeline Text Label */
                    .gantt-container ._278_3 { 
                        fill: var(--muted-foreground) !important; 
                        font-weight: 600; 
                    }

                    /* 6. Task Bar Label Text - High Contrast */
                    .gantt-container ._3shz- {
                        fill: var(--foreground) !important;
                        font-weight: 600 !important;
                        font-size: 11px !important;
                    }

                    /* 7. Tooltip - Modern Overlay */
                    .gantt-container ._3m_7S {
                        background-color: var(--popover) !important;
                        color: var(--popover-foreground) !important;
                        border: 1px solid var(--border) !important;
                        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                        border-radius: 4px !important;
                        padding: 8px !important;
                    }
                    
                    /* 8. Today Highlight - Subtle Overlay */
                    .gantt-container ._3eS_5 {
                        fill: var(--primary) !important;
                        fill-opacity: 0.05 !important;
                    }

                    /* 9. Dark Mode Nuclear Overrides - Ensure no white text on light gray issues */
                    [data-theme='dark'] .gantt-container text {
                        fill: #E4E4E7 !important; /* Zinc-200 */
                    }
                    [data-theme='dark'] .gantt-container ._3af_6 {
                        color: #E4E4E7 !important;
                        border-bottom-color: #27272A !important; /* Zinc-800 */
                    }
                    
                    /* Ensure rects that act as task backgrounds are consistent */
                /* Force Dark Background for Gantt Container */
                .gantt-container {
                    background-color: #09090b !important; /* zinc-950 */
                    color: #fafafa !important;
                }

                /* Rows - Dark */
                .gantt-container ._3af_6 { 
                    background-color: #09090b !important;
                    color: #fafafa !important;
                    border-bottom: 1px solid #27272a !important; /* zinc-800 */
                    border-right: 1px solid #27272a !important;
                }

                /* Header - Slightly Lighter Dark */
                .gantt-container ._2uS_8 { 
                    background-color: #18181b !important; /* zinc-900 */
                    color: #a1a1aa !important; /* zinc-400 */
                    border-bottom: 1px solid #27272a !important;
                    border-right: 1px solid #27272a !important;
                }

                /* Grid Lines - Visible */
                .gantt-container ._1_h_6 { 
                    fill: #27272a !important;
                    opacity: 1 !important;
                }
                
                /* Vertical Lines */
                .gantt-container line {
                    stroke: #27272a !important;
                    stroke-opacity: 1 !important;
                }
                
                /* Text Labels */
                .gantt-container text {
                    fill: #e4e4e7 !important; /* zinc-200 */
                }
                
                /* Tasks Background area in Chart */
                .gantt-container ._2rB_5, 
                .gantt-container ._3_h_6 {
                    fill: #09090b !important;
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
