"use client";

import React, { useState, useEffect } from 'react';

const API_BASE_URL = "http://localhost:8000/api";

interface GoalProgress {
    goal_id: string;
    objective: string;
    progress: number;
    status: string;
    linked_tasks: number;
    completed_tasks: number;
    blocked_tasks?: number;
}

interface ScopeCreepItem {
    id: string;
    name: string;
    project_id: string;
    owner: string;
    priority: string;
    recommendation: string;
}

export default function GoalTracker() {
    const [goals, setGoals] = useState<GoalProgress[]>([]);
    const [scopeCreep, setScopeCreep] = useState<ScopeCreepItem[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState<'goals' | 'alignment'>('goals');

    // New goal form
    const [showNewGoal, setShowNewGoal] = useState(false);
    const [newGoal, setNewGoal] = useState({
        objective: '',
        kpis: '',
        owner: '',
        time_horizon: 'quarterly'
    });

    useEffect(() => {
        fetchGoals();
        fetchScopeCreep();
    }, []);

    const fetchGoals = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/goals/`);
            const data = await res.json();
            setGoals(data);
        } catch (error) {
            console.error('Failed to fetch goals:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchScopeCreep = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/goals/scope-creep/detect`);
            const data = await res.json();
            setScopeCreep(data);
        } catch (error) {
            console.error('Failed to fetch scope creep:', error);
        }
    };

    const createGoal = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/goals/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    objective: newGoal.objective,
                    kpis: newGoal.kpis.split(',').map(k => k.trim()),
                    owner: newGoal.owner,
                    time_horizon: newGoal.time_horizon,
                    is_measurable: true
                })
            });
            if (res.ok) {
                setShowNewGoal(false);
                setNewGoal({ objective: '', kpis: '', owner: '', time_horizon: 'quarterly' });
                fetchGoals();
            }
        } catch (error) {
            console.error('Failed to create goal:', error);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'on_track': return 'bg-green-100 text-green-800';
            case 'at_risk': return 'bg-yellow-100 text-yellow-800';
            case 'off_track': return 'bg-red-100 text-red-800';
            case 'completed': return 'bg-blue-100 text-blue-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getProgressColor = (progress: number) => {
        if (progress >= 75) return 'bg-green-500';
        if (progress >= 50) return 'bg-blue-500';
        if (progress >= 25) return 'bg-yellow-500';
        return 'bg-red-500';
    };

    if (isLoading) {
        return (
            <div className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="space-y-3">
                    <div className="h-20 bg-gray-200 rounded"></div>
                    <div className="h-20 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white p-5">
                <h2 className="text-xl font-bold">Strategic Goal Tracker</h2>
                <p className="text-indigo-200 text-sm">Align tasks with organizational objectives</p>
            </div>

            {/* Tabs */}
            <div className="flex border-b">
                <button
                    onClick={() => setActiveTab('goals')}
                    className={`flex-1 py-3 text-center font-medium transition-colors ${activeTab === 'goals'
                            ? 'border-b-2 border-indigo-600 text-indigo-600'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                >
                    Goals ({goals.length})
                </button>
                <button
                    onClick={() => setActiveTab('alignment')}
                    className={`flex-1 py-3 text-center font-medium transition-colors ${activeTab === 'alignment'
                            ? 'border-b-2 border-indigo-600 text-indigo-600'
                            : 'text-gray-500 hover:text-gray-700'
                        }`}
                >
                    Scope Creep ({scopeCreep.length})
                </button>
            </div>

            <div className="p-6">
                {/* Goals Tab */}
                {activeTab === 'goals' && (
                    <div className="space-y-4">
                        <button
                            onClick={() => setShowNewGoal(!showNewGoal)}
                            className="w-full py-2 border-2 border-dashed border-gray-300 rounded-lg text-gray-500 hover:border-indigo-400 hover:text-indigo-600 transition-colors"
                        >
                            + Add New Goal
                        </button>

                        {showNewGoal && (
                            <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                                <input
                                    type="text"
                                    placeholder="Goal objective..."
                                    className="w-full p-2 border rounded"
                                    value={newGoal.objective}
                                    onChange={(e) => setNewGoal({ ...newGoal, objective: e.target.value })}
                                />
                                <input
                                    type="text"
                                    placeholder="KPIs (comma separated)"
                                    className="w-full p-2 border rounded"
                                    value={newGoal.kpis}
                                    onChange={(e) => setNewGoal({ ...newGoal, kpis: e.target.value })}
                                />
                                <div className="flex gap-2">
                                    <input
                                        type="text"
                                        placeholder="Owner"
                                        className="flex-1 p-2 border rounded"
                                        value={newGoal.owner}
                                        onChange={(e) => setNewGoal({ ...newGoal, owner: e.target.value })}
                                    />
                                    <select
                                        className="p-2 border rounded"
                                        value={newGoal.time_horizon}
                                        onChange={(e) => setNewGoal({ ...newGoal, time_horizon: e.target.value })}
                                    >
                                        <option value="monthly">Monthly</option>
                                        <option value="quarterly">Quarterly</option>
                                        <option value="yearly">Yearly</option>
                                    </select>
                                </div>
                                <button
                                    onClick={createGoal}
                                    className="w-full bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700"
                                >
                                    Create Goal
                                </button>
                            </div>
                        )}

                        {goals.length === 0 ? (
                            <p className="text-center text-gray-500 py-8">No goals defined yet</p>
                        ) : (
                            goals.map((goal) => (
                                <div key={goal.goal_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                                    <div className="flex justify-between items-start mb-3">
                                        <div className="flex-1">
                                            <h3 className="font-semibold text-gray-800">{goal.objective}</h3>
                                            <p className="text-sm text-gray-500">
                                                {goal.linked_tasks} tasks linked • {goal.completed_tasks} completed
                                            </p>
                                        </div>
                                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(goal.status)}`}>
                                            {goal.status.replace('_', ' ')}
                                        </span>
                                    </div>

                                    {/* Progress bar */}
                                    <div className="w-full bg-gray-200 rounded-full h-2">
                                        <div
                                            className={`h-2 rounded-full transition-all ${getProgressColor(goal.progress)}`}
                                            style={{ width: `${goal.progress}%` }}
                                        ></div>
                                    </div>
                                    <p className="text-right text-sm text-gray-500 mt-1">{goal.progress}% complete</p>
                                </div>
                            ))
                        )}
                    </div>
                )}

                {/* Scope Creep Tab */}
                {activeTab === 'alignment' && (
                    <div className="space-y-4">
                        {scopeCreep.length === 0 ? (
                            <div className="text-center py-8">
                                <div className="text-4xl mb-2">✅</div>
                                <p className="text-gray-500">All tasks are aligned with goals!</p>
                            </div>
                        ) : (
                            <>
                                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                                    <p className="text-yellow-800 font-medium">
                                        ⚠️ {scopeCreep.length} tasks are not linked to any goal
                                    </p>
                                    <p className="text-yellow-600 text-sm">
                                        Review these tasks and either align them with goals or consider deprioritizing.
                                    </p>
                                </div>

                                {scopeCreep.map((task) => (
                                    <div key={task.id} className="border border-yellow-200 rounded-lg p-4 bg-yellow-50">
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h4 className="font-medium text-gray-800">{task.name}</h4>
                                                <p className="text-sm text-gray-500">Owner: {task.owner}</p>
                                            </div>
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${task.priority === 'critical' ? 'bg-red-100 text-red-800' :
                                                    task.priority === 'high' ? 'bg-orange-100 text-orange-800' :
                                                        'bg-gray-100 text-gray-800'
                                                }`}>
                                                {task.priority}
                                            </span>
                                        </div>
                                        <p className="text-sm text-yellow-700 mt-2 italic">{task.recommendation}</p>
                                    </div>
                                ))}
                            </>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
