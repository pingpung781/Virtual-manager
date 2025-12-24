"use client";

import React, { useState, useEffect } from 'react';

const API_BASE_URL = "http://localhost:8000/api";

interface ProjectHealth {
    health: string;
    reason: string;
    metrics: {
        total_tasks: number;
        completed_tasks: number;
        blocked_tasks: number;
        overdue_tasks: number;
        completion_rate: number;
        expected_progress: number;
    };
}

interface Project {
    id: string;
    name: string;
    owner: string;
    objective: string | null;
    priority: string;
    health: string;
}

interface Props {
    projectId?: string;
}

export default function ProjectHealthDashboard({ projectId }: Props) {
    const [projects, setProjects] = useState<Project[]>([]);
    const [selectedProject, setSelectedProject] = useState<string | null>(projectId || null);
    const [healthData, setHealthData] = useState<ProjectHealth | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchProjects();
    }, []);

    useEffect(() => {
        if (selectedProject) {
            fetchProjectHealth(selectedProject);
        }
    }, [selectedProject]);

    const fetchProjects = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/v1/projects`);
            const data = await res.json();
            setProjects(data);
            if (data.length > 0 && !selectedProject) {
                setSelectedProject(data[0].id);
            }
        } catch (error) {
            console.error('Failed to fetch projects:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchProjectHealth = async (id: string) => {
        try {
            const res = await fetch(`${API_BASE_URL}/v1/projects/${id}/health`);
            const data = await res.json();
            setHealthData(data);
        } catch (error) {
            console.error('Failed to fetch project health:', error);
        }
    };

    const getHealthColor = (health: string) => {
        switch (health) {
            case 'on_track': return { bg: 'bg-green-500', text: 'text-green-500', light: 'bg-green-100' };
            case 'at_risk': return { bg: 'bg-yellow-500', text: 'text-yellow-500', light: 'bg-yellow-100' };
            case 'delayed': return { bg: 'bg-red-500', text: 'text-red-500', light: 'bg-red-100' };
            default: return { bg: 'bg-gray-500', text: 'text-gray-500', light: 'bg-gray-100' };
        }
    };

    const getHealthIcon = (health: string) => {
        switch (health) {
            case 'on_track': return '✓';
            case 'at_risk': return '⚠';
            case 'delayed': return '✕';
            default: return '?';
        }
    };

    if (isLoading) {
        return (
            <div className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
                <div className="h-8 bg-gray-200 rounded w-1/3 mb-6"></div>
                <div className="grid grid-cols-3 gap-4">
                    <div className="h-24 bg-gray-200 rounded"></div>
                    <div className="h-24 bg-gray-200 rounded"></div>
                    <div className="h-24 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-slate-800 to-slate-900 text-white p-5">
                <h2 className="text-xl font-bold">Project Health Dashboard</h2>
                <p className="text-slate-400 text-sm">Real-time health monitoring and metrics</p>
            </div>

            <div className="p-6">
                {/* Project Selector */}
                <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">Select Project</label>
                    <select
                        className="w-full p-3 border rounded-lg bg-gray-50 font-medium"
                        value={selectedProject || ''}
                        onChange={(e) => setSelectedProject(e.target.value)}
                    >
                        {projects.map((project) => (
                            <option key={project.id} value={project.id}>
                                {project.name} ({project.health.replace('_', ' ')})
                            </option>
                        ))}
                    </select>
                </div>

                {healthData && (
                    <>
                        {/* Health Status */}
                        <div className={`${getHealthColor(healthData.health).light} rounded-xl p-6 mb-6`}>
                            <div className="flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className={`w-16 h-16 rounded-full ${getHealthColor(healthData.health).bg} flex items-center justify-center text-white text-3xl font-bold`}>
                                        {getHealthIcon(healthData.health)}
                                    </div>
                                    <div>
                                        <h3 className={`text-2xl font-bold ${getHealthColor(healthData.health).text}`}>
                                            {healthData.health.replace('_', ' ').toUpperCase()}
                                        </h3>
                                        <p className="text-gray-600">{healthData.reason}</p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="text-4xl font-bold text-gray-800">
                                        {healthData.metrics.completion_rate}%
                                    </div>
                                    <div className="text-gray-500 text-sm">Complete</div>
                                </div>
                            </div>
                        </div>

                        {/* Metrics Grid */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                            <div className="bg-gray-50 rounded-lg p-4 text-center">
                                <div className="text-3xl font-bold text-gray-800">
                                    {healthData.metrics.total_tasks}
                                </div>
                                <div className="text-gray-500 text-sm">Total Tasks</div>
                            </div>
                            <div className="bg-green-50 rounded-lg p-4 text-center">
                                <div className="text-3xl font-bold text-green-600">
                                    {healthData.metrics.completed_tasks}
                                </div>
                                <div className="text-green-600 text-sm">Completed</div>
                            </div>
                            <div className="bg-orange-50 rounded-lg p-4 text-center">
                                <div className="text-3xl font-bold text-orange-600">
                                    {healthData.metrics.blocked_tasks}
                                </div>
                                <div className="text-orange-600 text-sm">Blocked</div>
                            </div>
                            <div className="bg-red-50 rounded-lg p-4 text-center">
                                <div className="text-3xl font-bold text-red-600">
                                    {healthData.metrics.overdue_tasks}
                                </div>
                                <div className="text-red-600 text-sm">Overdue</div>
                            </div>
                        </div>

                        {/* Progress Comparison */}
                        <div className="bg-gray-50 rounded-lg p-4">
                            <h4 className="font-semibold text-gray-700 mb-3">Progress vs Expected</h4>
                            <div className="space-y-3">
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-gray-600">Actual Progress</span>
                                        <span className="font-medium">{healthData.metrics.completion_rate}%</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-3">
                                        <div
                                            className="bg-blue-500 h-3 rounded-full transition-all"
                                            style={{ width: `${healthData.metrics.completion_rate}%` }}
                                        ></div>
                                    </div>
                                </div>
                                <div>
                                    <div className="flex justify-between text-sm mb-1">
                                        <span className="text-gray-600">Expected Progress</span>
                                        <span className="font-medium">{healthData.metrics.expected_progress}%</span>
                                    </div>
                                    <div className="w-full bg-gray-200 rounded-full h-3">
                                        <div
                                            className="bg-gray-400 h-3 rounded-full transition-all"
                                            style={{ width: `${healthData.metrics.expected_progress}%` }}
                                        ></div>
                                    </div>
                                </div>
                            </div>

                            {healthData.metrics.expected_progress > healthData.metrics.completion_rate && (
                                <div className="mt-3 text-sm text-orange-600 bg-orange-50 p-2 rounded">
                                    ⚠️ Project is {(healthData.metrics.expected_progress - healthData.metrics.completion_rate).toFixed(1)}% behind schedule
                                </div>
                            )}
                        </div>
                    </>
                )}
            </div>
        </div>
    );
}

export { ProjectHealthDashboard };
