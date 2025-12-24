"use client";

import React, { useState, useEffect } from 'react';

const API_BASE_URL = "http://localhost:8000/api";

interface WeeklyReport {
    period: {
        start: string;
        end: string;
    };
    completed: {
        count: number;
        tasks: Array<{ id: string; name: string; owner: string }>;
    };
    blocked: {
        count: number;
        tasks: Array<{ id: string; name: string; owner: string }>;
    };
    overdue: {
        count: number;
        tasks: Array<{ id: string; name: string; owner: string; deadline: string }>;
    };
    next_week_priorities: {
        count: number;
        tasks: Array<{ id: string; name: string; owner: string; deadline: string; priority: string }>;
    };
    velocity: number;
    health_indicators: {
        blocked_rate: number;
        overdue_rate: number;
    };
}

interface DailySummary {
    date: string;
    total_active: number;
    in_progress: Array<any>;
    blocked: Array<any>;
    not_started: Array<any>;
    needs_attention: Array<any>;
}

export default function ExecutionDashboard() {
    const [weeklyReport, setWeeklyReport] = useState<WeeklyReport | null>(null);
    const [dailySummary, setDailySummary] = useState<DailySummary | null>(null);
    const [activeTab, setActiveTab] = useState<'weekly' | 'daily'>('weekly');
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [weeklyRes, dailyRes] = await Promise.all([
                fetch(`${API_BASE_URL}/execution/weekly-report`),
                fetch(`${API_BASE_URL}/execution/daily-summary`)
            ]);

            setWeeklyReport(await weeklyRes.json());
            setDailySummary(await dailyRes.json());
        } catch (error) {
            console.error('Failed to fetch execution data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const formatDate = (dateStr: string) => {
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    };

    if (isLoading) {
        return (
            <div className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
                <div className="grid grid-cols-4 gap-4">
                    <div className="h-20 bg-gray-200 rounded"></div>
                    <div className="h-20 bg-gray-200 rounded"></div>
                    <div className="h-20 bg-gray-200 rounded"></div>
                    <div className="h-20 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-cyan-600 to-blue-600 text-white p-5">
                <h2 className="text-xl font-bold">Execution Monitor</h2>
                <p className="text-cyan-200 text-sm">Track progress and identify issues</p>
            </div>

            {/* Tabs */}
            <div className="flex border-b">
                <button
                    onClick={() => setActiveTab('weekly')}
                    className={`flex-1 py-3 text-center font-medium transition-colors ${activeTab === 'weekly'
                            ? 'border-b-2 border-blue-600 text-blue-600'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                >
                    Weekly Report
                </button>
                <button
                    onClick={() => setActiveTab('daily')}
                    className={`flex-1 py-3 text-center font-medium transition-colors ${activeTab === 'daily'
                            ? 'border-b-2 border-blue-600 text-blue-600'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                >
                    Daily Summary
                </button>
            </div>

            <div className="p-6">
                {/* Weekly Report Tab */}
                {activeTab === 'weekly' && weeklyReport && (
                    <div className="space-y-6">
                        {/* Period Header */}
                        <div className="text-center text-gray-500 text-sm">
                            {formatDate(weeklyReport.period.start)} - {formatDate(weeklyReport.period.end)}
                        </div>

                        {/* Key Metrics */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-green-50 rounded-lg p-4 text-center">
                                <div className="text-3xl font-bold text-green-600">{weeklyReport.completed.count}</div>
                                <div className="text-green-600 text-sm">Completed</div>
                            </div>
                            <div className="bg-blue-50 rounded-lg p-4 text-center">
                                <div className="text-3xl font-bold text-blue-600">{weeklyReport.velocity}</div>
                                <div className="text-blue-600 text-sm">Velocity</div>
                            </div>
                            <div className="bg-orange-50 rounded-lg p-4 text-center">
                                <div className="text-3xl font-bold text-orange-600">{weeklyReport.blocked.count}</div>
                                <div className="text-orange-600 text-sm">Blocked</div>
                            </div>
                            <div className="bg-red-50 rounded-lg p-4 text-center">
                                <div className="text-3xl font-bold text-red-600">{weeklyReport.overdue.count}</div>
                                <div className="text-red-600 text-sm">Overdue</div>
                            </div>
                        </div>

                        {/* Health Indicators */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-700 mb-3">Health Indicators</h4>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span>Blocked Rate</span>
                                        <span className={weeklyReport.health_indicators.blocked_rate > 15 ? 'text-red-600 font-medium' : 'text-gray-600'}>
                                            {weeklyReport.health_indicators.blocked_rate}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full ${weeklyReport.health_indicators.blocked_rate > 15 ? 'bg-red-500' : 'bg-orange-400'}`}
                                            style={{ width: `${Math.min(weeklyReport.health_indicators.blocked_rate, 100)}%` }}
                                        ></div>
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span>Overdue Rate</span>
                                        <span className={weeklyReport.health_indicators.overdue_rate > 10 ? 'text-red-600 font-medium' : 'text-gray-600'}>
                                            {weeklyReport.health_indicators.overdue_rate}%
                                        </span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full ${weeklyReport.health_indicators.overdue_rate > 10 ? 'bg-red-500' : 'bg-yellow-400'}`}
                                            style={{ width: `${Math.min(weeklyReport.health_indicators.overdue_rate, 100)}%` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Completed Tasks */}
                        {weeklyReport.completed.count > 0 && (
                            <div>
                                <h4 className="font-semibold text-gray-700 mb-2">✅ Completed This Week</h4>
                                <div className="bg-green-50 rounded-lg p-3 space-y-2">
                                    {weeklyReport.completed.tasks.slice(0, 5).map((task) => (
                                        <div key={task.id} className="flex justify-between text-sm">
                                            <span className="text-gray-700">{task.name}</span>
                                            <span className="text-gray-500">{task.owner}</span>
                                        </div>
                                    ))}
                                    {weeklyReport.completed.count > 5 && (
                                        <div className="text-sm text-gray-500 text-center">
                                            +{weeklyReport.completed.count - 5} more
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}

                        {/* Next Week Priorities */}
                        {weeklyReport.next_week_priorities.count > 0 && (
                            <div>
                                <h4 className="font-semibold text-gray-700 mb-2">📋 Next Week Priorities</h4>
                                <div className="bg-blue-50 rounded-lg p-3 space-y-2">
                                    {weeklyReport.next_week_priorities.tasks.slice(0, 5).map((task) => (
                                        <div key={task.id} className="flex justify-between items-center text-sm">
                                            <div className="flex items-center gap-2">
                                                <span className={`w-2 h-2 rounded-full ${task.priority === 'critical' ? 'bg-red-500' :
                                                        task.priority === 'high' ? 'bg-orange-500' :
                                                            'bg-blue-500'
                                                    }`}></span>
                                                <span className="text-gray-700">{task.name}</span>
                                            </div>
                                            <span className="text-gray-500">{formatDate(task.deadline)}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Daily Summary Tab */}
                {activeTab === 'daily' && dailySummary && (
                    <div className="space-y-6">
                        {/* Date Header */}
                        <div className="text-center text-gray-500 text-sm">
                            {new Date(dailySummary.date).toLocaleDateString('en-US', {
                                weekday: 'long',
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric'
                            })}
                        </div>

                        {/* Active Tasks Summary */}
                        <div className="grid grid-cols-3 gap-4">
                            <div className="bg-blue-50 rounded-lg p-4 text-center">
                                <div className="text-2xl font-bold text-blue-600">{dailySummary.in_progress.length}</div>
                                <div className="text-blue-600 text-sm">In Progress</div>
                            </div>
                            <div className="bg-orange-50 rounded-lg p-4 text-center">
                                <div className="text-2xl font-bold text-orange-600">{dailySummary.blocked.length}</div>
                                <div className="text-orange-600 text-sm">Blocked</div>
                            </div>
                            <div className="bg-gray-50 rounded-lg p-4 text-center">
                                <div className="text-2xl font-bold text-gray-600">{dailySummary.not_started.length}</div>
                                <div className="text-gray-600 text-sm">Not Started</div>
                            </div>
                        </div>

                        {/* Needs Attention */}
                        {dailySummary.needs_attention.length > 0 && (
                            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                <h4 className="font-semibold text-red-700 mb-2">⚠️ Needs Attention</h4>
                                <div className="space-y-2">
                                    {dailySummary.needs_attention.map((task: any) => (
                                        <div key={task.id} className="flex justify-between items-center text-sm">
                                            <span className="text-gray-700">{task.name}</span>
                                            <span className={`px-2 py-0.5 rounded text-xs font-medium ${task.reason === 'overdue' ? 'bg-red-200 text-red-800' : 'bg-yellow-200 text-yellow-800'
                                                }`}>
                                                {task.reason}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* In Progress Tasks */}
                        {dailySummary.in_progress.length > 0 && (
                            <div>
                                <h4 className="font-semibold text-gray-700 mb-2">🔄 In Progress</h4>
                                <div className="space-y-2">
                                    {dailySummary.in_progress.slice(0, 5).map((task: any) => (
                                        <div key={task.id} className="bg-gray-50 rounded p-3 flex justify-between items-center">
                                            <div>
                                                <div className="font-medium text-gray-800">{task.name}</div>
                                                <div className="text-xs text-gray-500">{task.owner}</div>
                                            </div>
                                            <span className={`text-xs px-2 py-1 rounded ${task.priority === 'critical' ? 'bg-red-100 text-red-800' :
                                                    task.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                                        'bg-gray-100 text-gray-800'
                                                }`}>
                                                {task.priority}
                                            </span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export { ExecutionDashboard };
