"use client";

import React, { useState, useEffect } from 'react';

const API_BASE_URL = "http://localhost:8000/api";

interface MilestoneStatus {
    id: string;
    name: string;
    target_date: string | null;
    completion_percentage: number;
    is_completed: boolean;
    at_risk: boolean;
    risk_reason: string | null;
    task_breakdown: {
        total: number;
        not_started: number;
        in_progress: number;
        blocked: number;
        completed: number;
        cancelled: number;
    };
}

interface MilestoneViewProps {
    projectId: string;
}

export default function MilestoneView({ projectId }: MilestoneViewProps) {
    const [milestones, setMilestones] = useState<MilestoneStatus[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showNewMilestone, setShowNewMilestone] = useState(false);
    const [newMilestone, setNewMilestone] = useState({
        name: '',
        description: '',
        target_date: ''
    });

    useEffect(() => {
        if (projectId) {
            fetchMilestones();
        }
    }, [projectId]);

    const fetchMilestones = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/milestones/project/${projectId}`);
            const data = await res.json();
            setMilestones(data);
        } catch (error) {
            console.error('Failed to fetch milestones:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const createMilestone = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/milestones/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    project_id: projectId,
                    name: newMilestone.name,
                    description: newMilestone.description,
                    target_date: newMilestone.target_date || null
                })
            });
            if (res.ok) {
                setShowNewMilestone(false);
                setNewMilestone({ name: '', description: '', target_date: '' });
                fetchMilestones();
            }
        } catch (error) {
            console.error('Failed to create milestone:', error);
        }
    };

    const getProgressColor = (percentage: number, atRisk: boolean) => {
        if (atRisk) return 'bg-red-500';
        if (percentage === 100) return 'bg-green-500';
        if (percentage >= 75) return 'bg-blue-500';
        if (percentage >= 50) return 'bg-yellow-500';
        return 'bg-gray-400';
    };

    const formatDate = (dateStr: string | null) => {
        if (!dateStr) return 'No date set';
        const date = new Date(dateStr);
        return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
    };

    if (isLoading) {
        return (
            <div className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="space-y-3">
                    <div className="h-24 bg-gray-200 rounded"></div>
                    <div className="h-24 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white p-5">
                <h2 className="text-xl font-bold">Milestones</h2>
                <p className="text-emerald-200 text-sm">Track project progress through key deliverables</p>
            </div>

            <div className="p-6">
                {/* Add Milestone Button */}
                <button
                    onClick={() => setShowNewMilestone(!showNewMilestone)}
                    className="w-full py-2 mb-4 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-emerald-400 hover:text-emerald-600 transition-colors"
                >
                    + Add Milestone
                </button>

                {/* New Milestone Form */}
                {showNewMilestone && (
                    <div className="bg-gray-50 p-4 rounded-lg mb-4 space-y-3">
                        <input
                            type="text"
                            placeholder="Milestone name..."
                            className="w-full p-2 border rounded"
                            value={newMilestone.name}
                            onChange={(e) => setNewMilestone({ ...newMilestone, name: e.target.value })}
                        />
                        <input
                            type="text"
                            placeholder="Description (optional)"
                            className="w-full p-2 border rounded"
                            value={newMilestone.description}
                            onChange={(e) => setNewMilestone({ ...newMilestone, description: e.target.value })}
                        />
                        <input
                            type="date"
                            className="w-full p-2 border rounded"
                            value={newMilestone.target_date}
                            onChange={(e) => setNewMilestone({ ...newMilestone, target_date: e.target.value })}
                        />
                        <button
                            onClick={createMilestone}
                            className="w-full bg-emerald-600 text-white py-2 rounded hover:bg-emerald-700"
                        >
                            Create Milestone
                        </button>
                    </div>
                )}

                {/* Milestones List */}
                {milestones.length === 0 ? (
                    <div className="text-center py-8">
                        <div className="text-4xl mb-2">🎯</div>
                        <p className="text-gray-500">No milestones defined yet</p>
                        <p className="text-gray-400 text-sm">Add milestones to track major project deliverables</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {milestones.map((milestone) => (
                            <div
                                key={milestone.id}
                                className={`border rounded-lg p-4 transition-shadow hover:shadow-md ${milestone.at_risk ? 'border-red-200 bg-red-50' :
                                        milestone.is_completed ? 'border-green-200 bg-green-50' : ''
                                    }`}
                            >
                                {/* Header */}
                                <div className="flex justify-between items-start mb-3">
                                    <div className="flex items-center gap-2">
                                        {milestone.is_completed ? (
                                            <span className="text-green-500 text-xl">✓</span>
                                        ) : milestone.at_risk ? (
                                            <span className="text-red-500 text-xl">⚠</span>
                                        ) : (
                                            <span className="text-gray-400 text-xl">○</span>
                                        )}
                                        <div>
                                            <h3 className="font-semibold text-gray-800">{milestone.name}</h3>
                                            <p className="text-sm text-gray-500">Due: {formatDate(milestone.target_date)}</p>
                                        </div>
                                    </div>
                                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${milestone.is_completed ? 'bg-green-100 text-green-800' :
                                            milestone.at_risk ? 'bg-red-100 text-red-800' :
                                                'bg-blue-100 text-blue-800'
                                        }`}>
                                        {milestone.completion_percentage}%
                                    </span>
                                </div>

                                {/* Progress Bar */}
                                <div className="w-full bg-gray-200 rounded-full h-3 mb-3">
                                    <div
                                        className={`h-3 rounded-full transition-all ${getProgressColor(milestone.completion_percentage, milestone.at_risk)}`}
                                        style={{ width: `${milestone.completion_percentage}%` }}
                                    ></div>
                                </div>

                                {/* Risk Warning */}
                                {milestone.at_risk && milestone.risk_reason && (
                                    <div className="bg-red-100 text-red-700 text-sm p-2 rounded mb-3">
                                        ⚠️ {milestone.risk_reason}
                                    </div>
                                )}

                                {/* Task Breakdown */}
                                <div className="grid grid-cols-5 gap-2 text-center text-xs">
                                    <div className="bg-gray-100 rounded p-2">
                                        <div className="font-bold text-gray-700">{milestone.task_breakdown.not_started}</div>
                                        <div className="text-gray-500">Not Started</div>
                                    </div>
                                    <div className="bg-blue-100 rounded p-2">
                                        <div className="font-bold text-blue-700">{milestone.task_breakdown.in_progress}</div>
                                        <div className="text-blue-500">In Progress</div>
                                    </div>
                                    <div className="bg-red-100 rounded p-2">
                                        <div className="font-bold text-red-700">{milestone.task_breakdown.blocked}</div>
                                        <div className="text-red-500">Blocked</div>
                                    </div>
                                    <div className="bg-green-100 rounded p-2">
                                        <div className="font-bold text-green-700">{milestone.task_breakdown.completed}</div>
                                        <div className="text-green-500">Done</div>
                                    </div>
                                    <div className="bg-gray-100 rounded p-2">
                                        <div className="font-bold text-gray-600">{milestone.task_breakdown.total}</div>
                                        <div className="text-gray-500">Total</div>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export { MilestoneView };
