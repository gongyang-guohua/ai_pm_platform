"use client";

import React from 'react';
import { ChevronLeft, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface CalendarViewProps {
    tasks: any[];
}

export default function CalendarView({ tasks }: CalendarViewProps) {
    const daysInMonth = 30; // Mock month
    const grid = Array(daysInMonth).fill(null);

    // Simple mock logic to place tasks on a calendar grid
    const tasksWithDays = tasks.map(t => {
        if (!t.planned_start) return null;
        const date = new Date(t.planned_start);
        return { ...t, day: (date.getDate() % 30) || 1 };
    }).filter(Boolean);

    return (
        <div className="bg-card border border-border h-full flex flex-col overflow-hidden">
            <div className="p-4 border-b border-border flex justify-between items-center bg-muted/20">
                <h3 className="text-sm font-black uppercase italic">Deployment Forecast / February 2026</h3>
                <div className="flex gap-2">
                    <button className="p-1 border border-border hover:bg-muted"><ChevronLeft className="w-4 h-4" /></button>
                    <button className="p-1 border border-border hover:bg-muted"><ChevronRight className="w-4 h-4" /></button>
                </div>
            </div>

            <div className="flex-1 overflow-auto p-4">
                <div className="grid grid-cols-7 gap-1 h-full min-h-[600px]">
                    {['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'].map(d => (
                        <div key={d} className="text-center text-[9px] font-black text-muted-foreground p-2 border-b border-border mb-2">{d}</div>
                    ))}
                    {grid.map((_, i) => {
                        const dayTasks = tasksWithDays.filter(t => t.day === i + 1);
                        return (
                            <div key={i} className="min-h-[100px] border border-border/50 p-2 hover:bg-muted/30 transition-colors relative">
                                <span className="text-[10px] font-mono text-muted-foreground opacity-50">{i + 1}</span>
                                <div className="mt-2 space-y-1">
                                    {dayTasks.map((t: any) => (
                                        <div
                                            key={t.id}
                                            className={cn(
                                                "text-[8px] font-bold uppercase p-1 truncate border-l-2",
                                                t.status === 'completed' ? "bg-emerald-500/10 border-emerald-500 text-emerald-700" :
                                                    t.status === 'in_progress' ? "bg-blue-500/10 border-blue-500 text-blue-700" : "bg-muted border-muted-foreground/30 text-muted-foreground"
                                            )}
                                        >
                                            {t.title}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
