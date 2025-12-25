'use client';

import React, { useState, useEffect } from 'react';

interface ProjectAnalytics {
    project_id: string;
    project_name: string;
    health_score: number;
    trend: string;
    metrics: {
        total_tasks: number;
        completed: number;
        in_progress: number;
        blocked: number;
        overdue: number;
        completion_rate: number;
    };
    contributing_factors: string[];
}

interface Risk {
    task_id: string;
    task_name: string;
    risk_probability: number;
    impact: string;
    time_to_risk: string;
    risk_factors: string[];
    suggested_action: string;
}

interface Warning {
    severity: string;
    type: string;
    title: string;
    cause: string;
    suggested_action: string;
}

interface Suggestion {
    type: string;
    priority: string;
    title: string;
    action: string;
    rationale: string;
    expected_impact: string;
}

interface ExecutiveDashboard {
    summary: {
        goals: { total: number; on_track: number; at_risk: number; completed: number };
        projects: { total: number; average_health: number; declining: number };
        risks: { level: string; high_risk_items: number };
        capacity: { overloaded_count: number; underutilized_count: number; balanced_count: number };
    };
    key_insights: string[];
    recommended_actions: any[];
}

const API_BASE = 'http://localhost:8000/api/v1/analytics';

export function AnalyticsDashboard() {
    const [activeTab, setActiveTab] = useState<'executive' | 'projects' | 'risks' | 'trends'>('executive');
    const [executiveDashboard, setExecutiveDashboard] = useState<ExecutiveDashboard | null>(null);
    const [projectAnalytics, setProjectAnalytics] = useState<any>(null);
    const [risks, setRisks] = useState<{ risks: Risk[]; overall_risk_level: string } | null>(null);
    const [warnings, setWarnings] = useState<Warning[]>([]);
    const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [execRes, projectsRes, risksRes, warningsRes, suggestionsRes] = await Promise.allSettled([
                fetch(`${API_BASE}/executive-dashboard`),
                fetch(`${API_BASE}/projects`),
                fetch(`${API_BASE}/risks`),
                fetch(`${API_BASE}/warnings`),
                fetch(`${API_BASE}/suggestions`)
            ]);

            if (execRes.status === 'fulfilled' && execRes.value.ok) {
                setExecutiveDashboard(await execRes.value.json());
            }
            if (projectsRes.status === 'fulfilled' && projectsRes.value.ok) {
                setProjectAnalytics(await projectsRes.value.json());
            }
            if (risksRes.status === 'fulfilled' && risksRes.value.ok) {
                setRisks(await risksRes.value.json());
            }
            if (warningsRes.status === 'fulfilled' && warningsRes.value.ok) {
                setWarnings(await warningsRes.value.json());
            }
            if (suggestionsRes.status === 'fulfilled' && suggestionsRes.value.ok) {
                setSuggestions(await suggestionsRes.value.json());
            }
        } catch (err) {
            console.error('Failed to fetch analytics:', err);
        } finally {
            setLoading(false);
        }
    };

    const getHealthColor = (score: number) => {
        if (score >= 80) return 'text-green-400';
        if (score >= 60) return 'text-yellow-400';
        if (score >= 40) return 'text-orange-400';
        return 'text-red-400';
    };

    const getRiskLevelColor = (level: string) => {
        switch (level) {
            case 'low': return 'bg-green-500/20 text-green-300 border-green-500/30';
            case 'medium': return 'bg-yellow-500/20 text-yellow-300 border-yellow-500/30';
            case 'high': return 'bg-red-500/20 text-red-300 border-red-500/30';
            default: return 'bg-gray-500/20 text-gray-300 border-gray-500/30';
        }
    };

    const getSeverityColor = (severity: string) => {
        switch (severity) {
            case 'critical': return 'bg-red-600';
            case 'high': return 'bg-orange-500';
            case 'medium': return 'bg-yellow-500';
            default: return 'bg-blue-500';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-cyan-900 to-slate-900 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-cyan-400"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-cyan-900 to-slate-900 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Analytics & Automation</h1>
                        <p className="text-cyan-300 mt-1">
                            Data-driven insights • Risk forecasting • Proactive intelligence
                        </p>
                    </div>
                    <button
                        onClick={fetchData}
                        className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Refresh
                    </button>
                </div>

                {/* Early Warnings Banner */}
                {warnings.length > 0 && (
                    <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-red-300 font-medium mb-2">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            {warnings.length} Early Warning(s)
                        </div>
                        <div className="space-y-2">
                            {warnings.slice(0, 3).map((w, i) => (
                                <div key={i} className="flex items-center gap-2">
                                    <span className={`w-2 h-2 rounded-full ${getSeverityColor(w.severity)}`}></span>
                                    <span className="text-white text-sm">{w.title}</span>
                                    <span className="text-cyan-400 text-xs">→ {w.suggested_action}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Tabs */}
                <div className="flex gap-2 bg-slate-800/50 p-1 rounded-lg w-fit">
                    {(['executive', 'projects', 'risks', 'trends'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2 rounded-md transition-colors capitalize ${activeTab === tab
                                    ? 'bg-cyan-600 text-white'
                                    : 'text-cyan-300 hover:bg-cyan-600/20'
                                }`}
                        >
                            {tab}
                        </button>
                    ))}
                </div>

                {/* Executive Tab */}
                {activeTab === 'executive' && executiveDashboard && (
                    <div className="space-y-6">
                        {/* KPI Cards */}
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-4">
                                <div className="text-cyan-300 text-sm">Goals On Track</div>
                                <div className="text-3xl font-bold text-white mt-1">
                                    {executiveDashboard.summary.goals.on_track}/{executiveDashboard.summary.goals.total}
                                </div>
                                <div className="text-yellow-400 text-xs mt-1">
                                    {executiveDashboard.summary.goals.at_risk} at risk
                                </div>
                            </div>
                            <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-4">
                                <div className="text-cyan-300 text-sm">Project Health</div>
                                <div className={`text-3xl font-bold mt-1 ${getHealthColor(executiveDashboard.summary.projects.average_health)}`}>
                                    {executiveDashboard.summary.projects.average_health}%
                                </div>
                                <div className="text-red-400 text-xs mt-1">
                                    {executiveDashboard.summary.projects.declining} declining
                                </div>
                            </div>
                            <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-4">
                                <div className="text-cyan-300 text-sm">Risk Level</div>
                                <div className={`text-2xl font-bold mt-1 capitalize ${executiveDashboard.summary.risks.level === 'high' ? 'text-red-400' :
                                        executiveDashboard.summary.risks.level === 'medium' ? 'text-yellow-400' : 'text-green-400'
                                    }`}>
                                    {executiveDashboard.summary.risks.level}
                                </div>
                                <div className="text-gray-400 text-xs mt-1">
                                    {executiveDashboard.summary.risks.high_risk_items} high-risk items
                                </div>
                            </div>
                            <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-4">
                                <div className="text-cyan-300 text-sm">Team Capacity</div>
                                <div className="text-3xl font-bold text-white mt-1">
                                    {executiveDashboard.summary.capacity.balanced_count}
                                </div>
                                <div className="text-orange-400 text-xs mt-1">
                                    {executiveDashboard.summary.capacity.overloaded_count} overloaded
                                </div>
                            </div>
                        </div>

                        {/* Key Insights */}
                        <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-6">
                            <h2 className="text-xl font-semibold text-white mb-4">Key Insights</h2>
                            <div className="space-y-2">
                                {executiveDashboard.key_insights.map((insight, i) => (
                                    <div key={i} className="text-white bg-slate-700/50 rounded-lg p-3">
                                        {insight}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Proactive Suggestions */}
                        {suggestions.length > 0 && (
                            <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-6">
                                <h2 className="text-xl font-semibold text-white mb-4">Proactive Suggestions</h2>
                                <div className="space-y-3">
                                    {suggestions.map((s, i) => (
                                        <div key={i} className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-4">
                                            <div className="flex items-center justify-between">
                                                <span className="text-white font-medium">{s.title}</span>
                                                <span className={`px-2 py-0.5 rounded text-xs ${s.priority === 'high' ? 'bg-red-500/30 text-red-300' : 'bg-yellow-500/30 text-yellow-300'
                                                    }`}>
                                                    {s.priority}
                                                </span>
                                            </div>
                                            <p className="text-cyan-300 text-sm mt-2">{s.action}</p>
                                            <div className="flex justify-between mt-2 text-xs">
                                                <span className="text-gray-400">Rationale: {s.rationale}</span>
                                                <span className="text-green-400">Impact: {s.expected_impact}</span>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                )}

                {/* Projects Tab */}
                {activeTab === 'projects' && projectAnalytics && (
                    <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-6">
                        <h2 className="text-xl font-semibold text-white mb-4">Project Performance</h2>

                        {projectAnalytics.projects ? (
                            <div className="space-y-4">
                                {projectAnalytics.projects.map((p: ProjectAnalytics) => (
                                    <div key={p.project_id} className="bg-slate-700/50 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-3">
                                            <h3 className="text-white font-medium">{p.project_name}</h3>
                                            <div className="flex items-center gap-3">
                                                <span className={`text-2xl font-bold ${getHealthColor(p.health_score)}`}>
                                                    {p.health_score}%
                                                </span>
                                                <span className={`px-2 py-1 rounded text-xs capitalize ${p.trend === 'improving' ? 'bg-green-500/20 text-green-300' :
                                                        p.trend === 'declining' ? 'bg-red-500/20 text-red-300' : 'bg-gray-500/20 text-gray-300'
                                                    }`}>
                                                    {p.trend}
                                                </span>
                                            </div>
                                        </div>
                                        <div className="grid grid-cols-5 gap-2 text-center text-sm">
                                            <div className="bg-slate-600/50 rounded p-2">
                                                <div className="text-cyan-300">Total</div>
                                                <div className="text-white font-bold">{p.metrics.total_tasks}</div>
                                            </div>
                                            <div className="bg-slate-600/50 rounded p-2">
                                                <div className="text-green-300">Done</div>
                                                <div className="text-white font-bold">{p.metrics.completed}</div>
                                            </div>
                                            <div className="bg-slate-600/50 rounded p-2">
                                                <div className="text-blue-300">In Progress</div>
                                                <div className="text-white font-bold">{p.metrics.in_progress}</div>
                                            </div>
                                            <div className="bg-slate-600/50 rounded p-2">
                                                <div className="text-red-300">Blocked</div>
                                                <div className="text-white font-bold">{p.metrics.blocked}</div>
                                            </div>
                                            <div className="bg-slate-600/50 rounded p-2">
                                                <div className="text-orange-300">Overdue</div>
                                                <div className="text-white font-bold">{p.metrics.overdue}</div>
                                            </div>
                                        </div>
                                        {p.contributing_factors.length > 0 && (
                                            <div className="mt-3 text-sm text-cyan-300">
                                                {p.contributing_factors.join(' • ')}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="text-cyan-300">
                                {projectAnalytics.project_name ? (
                                    <div className="bg-slate-700/50 rounded-lg p-4">
                                        <div className="flex justify-between items-center">
                                            <span className="text-white font-medium">{projectAnalytics.project_name}</span>
                                            <span className={`text-2xl font-bold ${getHealthColor(projectAnalytics.health_score)}`}>
                                                {projectAnalytics.health_score}%
                                            </span>
                                        </div>
                                    </div>
                                ) : (
                                    'No project data available'
                                )}
                            </div>
                        )}
                    </div>
                )}

                {/* Risks Tab */}
                {activeTab === 'risks' && risks && (
                    <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-6">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-semibold text-white">Risk Forecast</h2>
                            <span className={`px-3 py-1 rounded-full text-sm border ${getRiskLevelColor(risks.overall_risk_level)}`}>
                                Overall: {risks.overall_risk_level}
                            </span>
                        </div>

                        {risks.risks.length === 0 ? (
                            <div className="text-green-400 text-center py-8">
                                ✅ No significant risks detected
                            </div>
                        ) : (
                            <div className="space-y-3">
                                {risks.risks.map((risk) => (
                                    <div key={risk.task_id} className="bg-slate-700/50 rounded-lg p-4">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-white font-medium">{risk.task_name}</span>
                                            <div className="flex items-center gap-2">
                                                <span className={`px-2 py-0.5 rounded text-xs ${risk.impact === 'high' ? 'bg-red-500/30 text-red-300' :
                                                        risk.impact === 'medium' ? 'bg-yellow-500/30 text-yellow-300' : 'bg-gray-500/30 text-gray-300'
                                                    }`}>
                                                    {risk.impact} impact
                                                </span>
                                                <span className="text-red-400 font-bold">
                                                    {(risk.risk_probability * 100).toFixed(0)}%
                                                </span>
                                            </div>
                                        </div>
                                        <div className="text-cyan-300 text-sm mb-2">
                                            {risk.risk_factors.join(' • ')}
                                        </div>
                                        <div className="flex justify-between text-xs">
                                            <span className="text-gray-400">Time to risk: {risk.time_to_risk}</span>
                                            <span className="text-green-400">→ {risk.suggested_action}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Trends Tab */}
                {activeTab === 'trends' && (
                    <div className="bg-slate-800/50 rounded-xl border border-cyan-500/20 p-6">
                        <h2 className="text-xl font-semibold text-white mb-4">Delivery Trends</h2>
                        <div className="text-cyan-300 text-center py-8">
                            Delivery trend analysis and pattern insights coming soon
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AnalyticsDashboard;
