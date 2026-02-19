"use client";

import React, { useState } from 'react';
import { cn } from "@/lib/utils";
import { Clock, CheckCircle2, AlertCircle } from "lucide-react";
import {
    DndContext,
    closestCorners,
    KeyboardSensor,
    PointerSensor,
    useSensor,
    useSensors,
    DragOverlay,
    defaultDropAnimationSideEffects,
    DragStartEvent,
    DragOverEvent,
    DragEndEvent,
} from '@dnd-kit/core';
import {
    SortableContext,
    arrayMove,
    sortableKeyboardCoordinates,
    useSortable,
    verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

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
    status: string;
    priority?: string;
    estimated_hours: number;
    dependencies?: Dependency[];
}

interface Column {
    id: string;
    label: string;
    icon: any;
    color: string;
}

const columns: Column[] = [
    { id: 'not_started', label: 'Waiting / Pending', icon: Clock, color: 'border-muted-foreground/30' },
    { id: 'in_progress', label: 'Active / Execution', icon: AlertCircle, color: 'border-blue-500' },
    { id: 'stalled', label: 'Stalled / Paused', icon: AlertCircle, color: 'border-orange-500' },
    { id: 'completed', label: 'Finalized / Verified', icon: CheckCircle2, color: 'border-emerald-500' },
];

// --- Sortable Task Card ---

function SortableTaskCard({ task, isOverlay }: { task: Task, isOverlay?: boolean }) {
    const {
        attributes,
        listeners,
        setNodeRef,
        transform,
        transition,
        isDragging,
    } = useSortable({
        id: task.id,
        data: {
            type: 'Task',
            task,
        },
    });

    const style = {
        transform: CSS.Translate.toString(transform),
        transition,
    };

    if (isDragging) {
        return (
            <div
                ref={setNodeRef}
                style={style}
                className="bg-muted/20 border border-dashed border-primary/50 opacity-50 h-[120px] rounded-lg"
            />
        );
    }

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...attributes}
            {...listeners}
            className={cn(
                "bg-card border border-border p-3 hover:border-primary transition-colors cursor-grab active:cursor-grabbing group shadow-sm rounded-lg touch-none",
                isOverlay ? "shadow-xl scale-105 border-primary ring-2 ring-primary/20 rotate-2 z-50" : ""
            )}
        >
            <div className="flex items-center justify-between mb-1">
                <div className="text-[11px] font-mono text-muted-foreground font-bold">{task.wbs_code || `NODE-${task.id.toString().padStart(3, '0')}`}</div>
                <span className={cn(
                    "text-[9px] font-bold px-1.5 py-0.5 rounded-sm uppercase italic",
                    task.priority === 'Critical' ? "bg-red-500/20 text-red-600 dark:text-red-400" :
                        task.priority === 'High' ? "bg-orange-500/20 text-orange-600 dark:text-orange-400" :
                            task.priority === 'Medium' ? "bg-blue-500/20 text-blue-600 dark:text-blue-400" : "bg-muted text-muted-foreground"
                )}>
                    {task.priority || 'MED'}
                </span>
            </div>
            <h4 className="text-[12px] font-bold uppercase tracking-tight leading-tight text-foreground">{task.title}</h4>
            <div className="mt-3 flex items-center justify-between border-t border-border/50 pt-2">
                <span className="text-[9px] font-bold text-muted-foreground tabular-nums">{task.estimated_hours}H EST</span>
                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="w-2 h-2 rounded-full bg-primary/20 border border-primary/50" />
                    <div className="w-2 h-2 rounded-full bg-primary/20 border border-primary/50" />
                </div>
            </div>
        </div>
    );
}

// --- Kanban Column ---

function KanbanColumn({ column, tasks }: { column: Column, tasks: Task[] }) {
    const { setNodeRef } = useSortable({
        id: column.id,
        data: {
            type: 'Column',
            column,
        },
    });

    return (
        <div className="flex-1 flex flex-col min-w-[300px] border border-border bg-muted/10 rounded-lg overflow-hidden h-full">
            <div className={cn("p-3 border-b-2 flex items-center justify-between bg-card", column.color)}>
                <div className="flex items-center gap-2">
                    <column.icon className="w-3.5 h-3.5 text-muted-foreground" />
                    <span className="text-[11px] font-black uppercase tracking-widest">{column.label}</span>
                </div>
                <span className="text-[11px] font-mono text-muted-foreground font-bold bg-muted px-1.5 rounded">{tasks.length}</span>
            </div>

            <div ref={setNodeRef} className="flex-1 overflow-y-auto p-2 scrollbar-thin">
                <SortableContext items={tasks.map(t => t.id)} strategy={verticalListSortingStrategy}>
                    <div className="flex flex-col gap-2 min-h-[50px]">
                        {tasks.map((task) => (
                            <SortableTaskCard key={task.id} task={task} />
                        ))}
                    </div>
                </SortableContext>
            </div>
        </div>
    );
}

// --- Main Board Component ---

export default function KanbanBoard({ tasks: initialTasks, onUpdateStatus }: { tasks: Task[], onUpdateStatus: (id: number, status: string) => void }) {
    const [activeId, setActiveId] = useState<number | null>(null);
    const [paramsTasks, setParamsTasks] = useState<Task[]>(initialTasks);

    // Sync state when props change
    React.useEffect(() => {
        setParamsTasks(initialTasks);
    }, [initialTasks]);

    // Sensors
    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 5, // Prevent accidental drags
            },
        }),
        useSensor(KeyboardSensor, {
            coordinateGetter: sortableKeyboardCoordinates,
        })
    );

    const handleDragStart = (event: DragStartEvent) => {
        const { active } = event;
        setActiveId(active.id as number);
    };

    const handleDragOver = (event: DragOverEvent) => {
        // Optional: Implement real-time reordering across columns if strictly needed
        // For simple Kanban, we mostly care about the final drop container
    };

    const handleDragEnd = (event: DragEndEvent) => {
        const { active, over } = event;

        if (!over) {
            setActiveId(null);
            return;
        }

        const taskId = active.id as number;
        // The over.id could be a Column ID or a Task ID (if dropped on another task)
        // If dropped on a task, we need to find that task's column

        let newStatus = '';
        const overId = over.id;

        // Check if overId is a column ID
        const isColumn = columns.some(c => c.id === overId);

        if (isColumn) {
            newStatus = overId as string;
        } else {
            // Dropped on another task -> find its status
            const overTask = paramsTasks.find(t => t.id === overId);
            if (overTask) {
                newStatus = overTask.status;
            }
        }

        if (newStatus) {
            // Update local state optimistically
            setParamsTasks((tasks) => {
                return tasks.map(t => {
                    if (t.id === taskId && t.status !== newStatus) {
                        // Trigger update
                        onUpdateStatus(taskId, newStatus);
                        return { ...t, status: newStatus };
                    }
                    return t;
                });
            });
        }

        setActiveId(null);
    };

    const activeTask = activeId ? paramsTasks.find(t => t.id === activeId) : null;

    return (
        <DndContext
            sensors={sensors}
            collisionDetection={closestCorners}
            onDragStart={handleDragStart}
            onDragOver={handleDragOver}
            onDragEnd={handleDragEnd}
        >
            <div className="flex gap-4 h-full overflow-x-auto pb-4 scrollbar-thin">
                {columns.map((column) => (
                    <KanbanColumn
                        key={column.id}
                        column={column}
                        tasks={paramsTasks.filter(t => t.status === column.id)}
                    />
                ))}
            </div>

            <DragOverlay dropAnimation={{
                sideEffects: defaultDropAnimationSideEffects({
                    styles: {
                        active: {
                            opacity: '0.5',
                        },
                    },
                }),
            }}>
                {activeTask ? <SortableTaskCard task={activeTask} isOverlay /> : null}
            </DragOverlay>
        </DndContext>
    );
}
