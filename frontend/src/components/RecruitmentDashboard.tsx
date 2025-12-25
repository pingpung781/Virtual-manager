'use client';

import React, { useState, useEffect } from 'react';

interface JobRole {
    id: string;
    title: string;
    team: string;
    seniority_level: string;
    work_mode: string;
    candidate_count: number;
    created_at: string;
}

interface Pipeline {
    applied: Candidate[];
    screening: Candidate[];
    interviewing: Candidate[];
    offer: Candidate[];
    hired: Candidate[];
    rejected: Candidate[];
}

interface Candidate {
    id: string;
    name: string;
    email: string;
    source: string;
    updated_at: string;
    days_in_stage: number;
}

interface OnboardingPlan {
    id: string;
    employee_id: string;
    role: string;
    status: string;
    completion_percentage: number;
}

const API_BASE = 'http://localhost:8000/api/v1/growth';

export function RecruitmentDashboard() {
    const [activeTab, setActiveTab] = useState<'roles' | 'pipeline' | 'onboarding' | 'knowledge'>('roles');
    const [roles, setRoles] = useState<JobRole[]>([]);
    const [pipeline, setPipeline] = useState<{ pipeline: Pipeline; stale_candidates: any[] } | null>(null);
    const [onboardingPlans, setOnboardingPlans] = useState<OnboardingPlan[]>([]);
    const [loading, setLoading] = useState(true);
    const [showNewRole, setShowNewRole] = useState(false);

    const [newRole, setNewRole] = useState({
        title: '',
        team: '',
        responsibilities: '',
        required_skills: '',
        experience_years: 2,
        seniority_level: 'mid',
        work_mode: 'hybrid'
    });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [rolesRes, pipelineRes, onboardingRes] = await Promise.allSettled([
                fetch(`${API_BASE}/jobs`),
                fetch(`${API_BASE}/candidates/pipeline`),
                fetch(`${API_BASE}/onboarding`)
            ]);

            if (rolesRes.status === 'fulfilled' && rolesRes.value.ok) {
                setRoles(await rolesRes.value.json());
            }
            if (pipelineRes.status === 'fulfilled' && pipelineRes.value.ok) {
                setPipeline(await pipelineRes.value.json());
            }
            if (onboardingRes.status === 'fulfilled' && onboardingRes.value.ok) {
                setOnboardingPlans(await onboardingRes.value.json());
            }
        } catch (err) {
            console.error('Failed to fetch data:', err);
        } finally {
            setLoading(false);
        }
    };

    const createRole = async () => {
        try {
            const response = await fetch(`${API_BASE}/jobs`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ...newRole,
                    responsibilities: newRole.responsibilities.split('\n').filter(r => r.trim()),
                    required_skills: newRole.required_skills.split('\n').filter(s => s.trim())
                })
            });

            if (response.ok) {
                setShowNewRole(false);
                setNewRole({
                    title: '',
                    team: '',
                    responsibilities: '',
                    required_skills: '',
                    experience_years: 2,
                    seniority_level: 'mid',
                    work_mode: 'hybrid'
                });
                fetchData();
            }
        } catch (err) {
            console.error('Failed to create role:', err);
        }
    };

    const getStageColor = (stage: string) => {
        const colors: Record<string, string> = {
            applied: 'bg-blue-500/20 border-blue-500/50',
            screening: 'bg-yellow-500/20 border-yellow-500/50',
            interviewing: 'bg-purple-500/20 border-purple-500/50',
            offer: 'bg-green-500/20 border-green-500/50',
            hired: 'bg-emerald-500/20 border-emerald-500/50',
            rejected: 'bg-red-500/20 border-red-500/50'
        };
        return colors[stage] || 'bg-gray-500/20 border-gray-500/50';
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-400"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Growth & Scaling</h1>
                        <p className="text-indigo-300 mt-1">
                            Hiring • Onboarding • Knowledge Management
                        </p>
                    </div>
                    <button
                        onClick={fetchData}
                        className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors flex items-center gap-2"
                    >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                        </svg>
                        Refresh
                    </button>
                </div>

                {/* Tabs */}
                <div className="flex gap-2 bg-slate-800/50 p-1 rounded-lg w-fit">
                    {(['roles', 'pipeline', 'onboarding', 'knowledge'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2 rounded-md transition-colors capitalize ${activeTab === tab
                                    ? 'bg-indigo-600 text-white'
                                    : 'text-indigo-300 hover:bg-indigo-600/20'
                                }`}
                        >
                            {tab === 'roles' ? 'Open Roles' : tab}
                        </button>
                    ))}
                </div>

                {/* Open Roles Tab */}
                {activeTab === 'roles' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center">
                            <h2 className="text-xl font-semibold text-white">Open Positions</h2>
                            <button
                                onClick={() => setShowNewRole(true)}
                                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm"
                            >
                                + New Role
                            </button>
                        </div>

                        {roles.length === 0 ? (
                            <div className="bg-slate-800/50 rounded-xl border border-indigo-500/20 p-12 text-center">
                                <div className="text-4xl mb-4">📋</div>
                                <p className="text-indigo-300">No open positions. Create a new role to start hiring.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                {roles.map((role) => (
                                    <div key={role.id} className="bg-slate-800/50 rounded-xl border border-indigo-500/20 p-5 hover:border-indigo-500/40 transition-colors">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <h3 className="text-lg font-medium text-white">{role.title}</h3>
                                                <p className="text-indigo-300 text-sm">{role.team}</p>
                                            </div>
                                            <span className="px-2 py-1 bg-green-500/20 text-green-300 text-xs rounded-full">
                                                Open
                                            </span>
                                        </div>

                                        <div className="mt-4 flex flex-wrap gap-2">
                                            <span className="px-2 py-1 bg-indigo-500/20 text-indigo-300 text-xs rounded">
                                                {role.seniority_level}
                                            </span>
                                            <span className="px-2 py-1 bg-indigo-500/20 text-indigo-300 text-xs rounded">
                                                {role.work_mode}
                                            </span>
                                        </div>

                                        <div className="mt-4 pt-4 border-t border-indigo-500/20 flex justify-between items-center">
                                            <span className="text-indigo-300 text-sm">
                                                {role.candidate_count} candidates
                                            </span>
                                            <button className="text-indigo-400 hover:text-white text-sm">
                                                View →
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Pipeline Tab */}
                {activeTab === 'pipeline' && pipeline && (
                    <div className="space-y-6">
                        <h2 className="text-xl font-semibold text-white">Candidate Pipeline</h2>

                        {pipeline.stale_candidates.length > 0 && (
                            <div className="bg-orange-500/20 border border-orange-500/50 rounded-lg p-4">
                                <div className="text-orange-300 font-medium">⚠️ Stale Candidates</div>
                                <div className="text-white text-sm mt-1">
                                    {pipeline.stale_candidates.length} candidate(s) haven't been updated in 14+ days
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                            {Object.entries(pipeline.pipeline).map(([stage, candidates]) => (
                                <div key={stage} className={`rounded-xl border p-4 ${getStageColor(stage)}`}>
                                    <div className="flex items-center justify-between mb-3">
                                        <h3 className="text-white font-medium capitalize text-sm">{stage}</h3>
                                        <span className="text-white text-xs bg-white/20 px-2 py-0.5 rounded-full">
                                            {candidates.length}
                                        </span>
                                    </div>
                                    <div className="space-y-2">
                                        {candidates.slice(0, 5).map((c: Candidate) => (
                                            <div key={c.id} className="bg-slate-800/50 rounded p-2">
                                                <div className="text-white text-sm font-medium truncate">{c.name}</div>
                                                <div className="text-indigo-300 text-xs">{c.days_in_stage}d in stage</div>
                                            </div>
                                        ))}
                                        {candidates.length > 5 && (
                                            <div className="text-indigo-300 text-xs text-center">
                                                +{candidates.length - 5} more
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Onboarding Tab */}
                {activeTab === 'onboarding' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center">
                            <h2 className="text-xl font-semibold text-white">Onboarding Plans</h2>
                            <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm">
                                + New Plan
                            </button>
                        </div>

                        {onboardingPlans.length === 0 ? (
                            <div className="bg-slate-800/50 rounded-xl border border-indigo-500/20 p-12 text-center">
                                <div className="text-4xl mb-4">🎯</div>
                                <p className="text-indigo-300">No onboarding plans. Create one when a new hire joins.</p>
                            </div>
                        ) : (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                {onboardingPlans.map((plan) => (
                                    <div key={plan.id} className="bg-slate-800/50 rounded-xl border border-indigo-500/20 p-5">
                                        <div className="flex items-center justify-between">
                                            <div>
                                                <h3 className="text-lg font-medium text-white">{plan.role}</h3>
                                                <p className="text-indigo-300 text-sm capitalize">{plan.status.replace('_', ' ')}</p>
                                            </div>
                                            <div className="text-2xl font-bold text-white">
                                                {plan.completion_percentage}%
                                            </div>
                                        </div>
                                        <div className="mt-4 bg-slate-700 rounded-full h-2">
                                            <div
                                                className="bg-indigo-500 h-2 rounded-full transition-all"
                                                style={{ width: `${plan.completion_percentage}%` }}
                                            />
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Knowledge Tab */}
                {activeTab === 'knowledge' && (
                    <div className="bg-slate-800/50 backdrop-blur-sm rounded-xl border border-indigo-500/20 p-6">
                        <div className="flex justify-between items-center mb-6">
                            <h2 className="text-xl font-semibold text-white">Knowledge Base</h2>
                            <button className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm">
                                + New Article
                            </button>
                        </div>

                        <div className="text-indigo-300 text-center py-8">
                            Search and manage internal knowledge articles, FAQs, and best practices.
                        </div>
                    </div>
                )}

                {/* New Role Modal */}
                {showNewRole && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                        <div className="bg-slate-800 rounded-xl border border-indigo-500/30 p-6 w-full max-w-lg">
                            <h3 className="text-xl font-semibold text-white mb-4">Define New Role</h3>

                            <div className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-indigo-300 text-sm mb-1">Job Title</label>
                                        <input
                                            type="text"
                                            value={newRole.title}
                                            onChange={(e) => setNewRole({ ...newRole, title: e.target.value })}
                                            className="w-full px-3 py-2 bg-slate-700 border border-indigo-500/30 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                                            placeholder="Software Engineer"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-indigo-300 text-sm mb-1">Team</label>
                                        <input
                                            type="text"
                                            value={newRole.team}
                                            onChange={(e) => setNewRole({ ...newRole, team: e.target.value })}
                                            className="w-full px-3 py-2 bg-slate-700 border border-indigo-500/30 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                                            placeholder="Engineering"
                                        />
                                    </div>
                                </div>

                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-indigo-300 text-sm mb-1">Experience (years)</label>
                                        <input
                                            type="number"
                                            value={newRole.experience_years}
                                            onChange={(e) => setNewRole({ ...newRole, experience_years: parseInt(e.target.value) })}
                                            className="w-full px-3 py-2 bg-slate-700 border border-indigo-500/30 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-indigo-300 text-sm mb-1">Level</label>
                                        <select
                                            value={newRole.seniority_level}
                                            onChange={(e) => setNewRole({ ...newRole, seniority_level: e.target.value })}
                                            className="w-full px-3 py-2 bg-slate-700 border border-indigo-500/30 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                                        >
                                            <option value="junior">Junior</option>
                                            <option value="mid">Mid-Level</option>
                                            <option value="senior">Senior</option>
                                            <option value="lead">Lead</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-indigo-300 text-sm mb-1">Work Mode</label>
                                        <select
                                            value={newRole.work_mode}
                                            onChange={(e) => setNewRole({ ...newRole, work_mode: e.target.value })}
                                            className="w-full px-3 py-2 bg-slate-700 border border-indigo-500/30 rounded-lg text-white focus:outline-none focus:border-indigo-500"
                                        >
                                            <option value="remote">Remote</option>
                                            <option value="hybrid">Hybrid</option>
                                            <option value="onsite">Onsite</option>
                                        </select>
                                    </div>
                                </div>

                                <div>
                                    <label className="block text-indigo-300 text-sm mb-1">Responsibilities (one per line)</label>
                                    <textarea
                                        value={newRole.responsibilities}
                                        onChange={(e) => setNewRole({ ...newRole, responsibilities: e.target.value })}
                                        rows={3}
                                        className="w-full px-3 py-2 bg-slate-700 border border-indigo-500/30 rounded-lg text-white focus:outline-none focus:border-indigo-500 resize-none"
                                        placeholder="Build and maintain features&#10;Collaborate with team&#10;Code reviews"
                                    />
                                </div>

                                <div>
                                    <label className="block text-indigo-300 text-sm mb-1">Required Skills (one per line)</label>
                                    <textarea
                                        value={newRole.required_skills}
                                        onChange={(e) => setNewRole({ ...newRole, required_skills: e.target.value })}
                                        rows={3}
                                        className="w-full px-3 py-2 bg-slate-700 border border-indigo-500/30 rounded-lg text-white focus:outline-none focus:border-indigo-500 resize-none"
                                        placeholder="Python&#10;React&#10;PostgreSQL"
                                    />
                                </div>
                            </div>

                            <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3 mt-4">
                                <div className="text-yellow-300 text-sm">
                                    ⚠️ Job postings require human approval before publishing
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    onClick={() => setShowNewRole(false)}
                                    className="px-4 py-2 text-indigo-300 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={createRole}
                                    disabled={!newRole.title || !newRole.team}
                                    className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-600/50 text-white rounded-lg transition-colors"
                                >
                                    Create Role
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default RecruitmentDashboard;
