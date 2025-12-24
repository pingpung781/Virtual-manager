'use client';

import { useEffect, useState, useRef } from 'react';

type LogEntry = {
    id: string;
    timestamp: string;
    agent: string;
    message: string;
    type: 'info' | 'decision' | 'warning';
};

export default function AgentActivityLog() {
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const scrollRef = useRef<HTMLDivElement>(null);

    // Mock Data Stream
    useEffect(() => {
        const interval = setInterval(() => {
            const newLog: LogEntry = {
                id: Math.random().toString(36).substr(2, 9),
                timestamp: new Date().toLocaleTimeString(),
                agent: Math.random() > 0.5 ? 'Orchestrator' : 'Planning Agent',
                message: Math.random() > 0.5 ? 'Decomposing new user objective...' : 'Updating task dependency graph.',
                type: Math.random() > 0.8 ? 'decision' : 'info'
            };
            setLogs(prev => [...prev.slice(-20), newLog]); // Keep last 20
        }, 3500);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [logs]);

    return (
        <div className="flex-1 overflow-y-auto p-6 space-y-4 font-mono text-sm" ref={scrollRef}>
            {logs.map((log) => (
                <div key={log.id} className="flex gap-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                    <span className="text-slate-500 whitespace-nowrap">{log.timestamp}</span>
                    <div className="flex-1">
                        <span className={`font-bold mr-2 ${log.agent === 'Orchestrator' ? 'text-purple-400' : 'text-blue-400'
                            }`}>[{log.agent}]</span>
                        <span className={log.type === 'decision' ? 'text-amber-300' : 'text-slate-300'}>
                            {log.type === 'decision' ? '➔ ' : ''}{log.message}
                        </span>
                    </div>
                </div>
            ))}
            {logs.length === 0 && (
                <div className="text-center text-slate-600 mt-20">Waiting for system signals...</div>
            )}
        </div>
    );
}
