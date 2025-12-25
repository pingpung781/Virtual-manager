'use client';

import React, { useState, useEffect } from 'react';

interface User {
    id: string;
    email: string;
    name: string;
    role: string;
    is_active: boolean;
    last_login: string | null;
}

interface ApprovalRequest {
    id: string;
    action_type: string;
    action_summary: string;
    sensitivity: string;
    requester_name: string;
    requested_at: string;
    expires_at: string;
    is_reversible: boolean;
}

interface AuditLog {
    id: string;
    timestamp: string;
    actor_id: string;
    actor_name: string;
    action: string;
    resource_type: string;
    resource_id: string;
    outcome: string;
    reason: string;
}

interface HealthCheck {
    status: string;
    timestamp: string;
    checks: {
        database: { status: string };
        approvals: { status: string; expired_count: number };
        operations: { status: string; stale_locks: number };
    };
}

const API_BASE = 'http://localhost:8000/api/v1/platform';

export function AdminDashboard() {
    const [activeTab, setActiveTab] = useState<'users' | 'approvals' | 'audit' | 'health'>('users');
    const [users, setUsers] = useState<User[]>([]);
    const [approvals, setApprovals] = useState<ApprovalRequest[]>([]);
    const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
    const [health, setHealth] = useState<HealthCheck | null>(null);
    const [loading, setLoading] = useState(true);
    const [showNewUser, setShowNewUser] = useState(false);
    const [newUser, setNewUser] = useState({ email: '', name: '', role: 'viewer' });

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [usersRes, approvalsRes, auditRes, healthRes] = await Promise.allSettled([
                fetch(`${API_BASE}/users`),
                fetch(`${API_BASE}/approvals`),
                fetch(`${API_BASE}/audit?limit=20`),
                fetch(`${API_BASE}/health`)
            ]);

            if (usersRes.status === 'fulfilled' && usersRes.value.ok) {
                setUsers(await usersRes.value.json());
            }
            if (approvalsRes.status === 'fulfilled' && approvalsRes.value.ok) {
                setApprovals(await approvalsRes.value.json());
            }
            if (auditRes.status === 'fulfilled' && auditRes.value.ok) {
                setAuditLogs(await auditRes.value.json());
            }
            if (healthRes.status === 'fulfilled' && healthRes.value.ok) {
                setHealth(await healthRes.value.json());
            }
        } catch (err) {
            console.error('Failed to fetch data:', err);
        } finally {
            setLoading(false);
        }
    };

    const createUser = async () => {
        try {
            const response = await fetch(`${API_BASE}/users`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(newUser)
            });

            if (response.ok) {
                setShowNewUser(false);
                setNewUser({ email: '', name: '', role: 'viewer' });
                fetchData();
            }
        } catch (err) {
            console.error('Failed to create user:', err);
        }
    };

    const processApproval = async (approvalId: string, approved: boolean) => {
        const reason = prompt(`Enter reason for ${approved ? 'approval' : 'rejection'}:`);
        if (!reason) return;

        try {
            const response = await fetch(`${API_BASE}/approvals/${approvalId}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-User-Id': 'admin'  // Would come from auth in production
                },
                body: JSON.stringify({ approved, reason })
            });

            if (response.ok) {
                fetchData();
            }
        } catch (err) {
            console.error('Failed to process approval:', err);
        }
    };

    const getRoleColor = (role: string) => {
        const colors: Record<string, string> = {
            admin: 'bg-red-500/20 text-red-300 border-red-500/30',
            manager: 'bg-purple-500/20 text-purple-300 border-purple-500/30',
            contributor: 'bg-blue-500/20 text-blue-300 border-blue-500/30',
            viewer: 'bg-gray-500/20 text-gray-300 border-gray-500/30'
        };
        return colors[role] || colors.viewer;
    };

    const getSensitivityColor = (sensitivity: string) => {
        const colors: Record<string, string> = {
            critical: 'bg-red-500',
            high: 'bg-orange-500',
            medium: 'bg-yellow-500',
            low: 'bg-green-500'
        };
        return colors[sensitivity] || 'bg-gray-500';
    };

    const getHealthStatusColor = (status: string) => {
        switch (status) {
            case 'healthy': return 'text-green-400';
            case 'degraded': return 'text-yellow-400';
            case 'unhealthy': return 'text-red-400';
            default: return 'text-gray-400';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-red-900/20 to-slate-900 flex items-center justify-center">
                <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-red-400"></div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-red-900/20 to-slate-900 p-6">
            <div className="max-w-7xl mx-auto space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Platform Administration</h1>
                        <p className="text-red-300 mt-1">
                            Security • Access Control • Audit Trail
                        </p>
                    </div>
                    <div className="flex items-center gap-4">
                        {health && (
                            <div className={`flex items-center gap-2 ${getHealthStatusColor(health.status)}`}>
                                <span className={`w-2 h-2 rounded-full ${health.status === 'healthy' ? 'bg-green-400' : health.status === 'degraded' ? 'bg-yellow-400' : 'bg-red-400'}`}></span>
                                System: {health.status}
                            </div>
                        )}
                        <button
                            onClick={fetchData}
                            className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                {/* Pending Approvals Alert */}
                {approvals.length > 0 && (
                    <div className="bg-orange-500/10 border border-orange-500/30 rounded-xl p-4">
                        <div className="flex items-center gap-2 text-orange-300 font-medium">
                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                            </svg>
                            {approvals.length} Pending Approval(s) Require Action
                        </div>
                    </div>
                )}

                {/* Tabs */}
                <div className="flex gap-2 bg-slate-800/50 p-1 rounded-lg w-fit">
                    {(['users', 'approvals', 'audit', 'health'] as const).map((tab) => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={`px-4 py-2 rounded-md transition-colors capitalize ${activeTab === tab
                                    ? 'bg-red-600 text-white'
                                    : 'text-red-300 hover:bg-red-600/20'
                                }`}
                        >
                            {tab}
                            {tab === 'approvals' && approvals.length > 0 && (
                                <span className="ml-2 bg-orange-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                                    {approvals.length}
                                </span>
                            )}
                        </button>
                    ))}
                </div>

                {/* Users Tab */}
                {activeTab === 'users' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center">
                            <h2 className="text-xl font-semibold text-white">User Management</h2>
                            <button
                                onClick={() => setShowNewUser(true)}
                                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-lg text-sm"
                            >
                                + Add User
                            </button>
                        </div>

                        <div className="bg-slate-800/50 rounded-xl border border-red-500/20 overflow-hidden">
                            <table className="w-full">
                                <thead className="bg-slate-700/50">
                                    <tr>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">User</th>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Role</th>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Status</th>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Last Login</th>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.map((user) => (
                                        <tr key={user.id} className="border-t border-slate-700">
                                            <td className="px-4 py-3">
                                                <div className="text-white font-medium">{user.name}</div>
                                                <div className="text-gray-400 text-sm">{user.email}</div>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`px-2 py-1 rounded border text-xs capitalize ${getRoleColor(user.role)}`}>
                                                    {user.role}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`px-2 py-1 rounded text-xs ${user.is_active ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'}`}>
                                                    {user.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                            </td>
                                            <td className="px-4 py-3 text-gray-400 text-sm">
                                                {user.last_login ? new Date(user.last_login).toLocaleDateString() : 'Never'}
                                            </td>
                                            <td className="px-4 py-3">
                                                <button className="text-red-400 hover:text-white text-sm">Edit</button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Approvals Tab */}
                {activeTab === 'approvals' && (
                    <div className="space-y-6">
                        <h2 className="text-xl font-semibold text-white">Pending Approvals</h2>

                        {approvals.length === 0 ? (
                            <div className="bg-slate-800/50 rounded-xl border border-red-500/20 p-12 text-center">
                                <div className="text-4xl mb-4">✅</div>
                                <p className="text-red-300">No pending approvals</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {approvals.map((approval) => (
                                    <div key={approval.id} className="bg-slate-800/50 rounded-xl border border-red-500/20 p-5">
                                        <div className="flex items-start justify-between">
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className={`w-2 h-2 rounded-full ${getSensitivityColor(approval.sensitivity)}`}></span>
                                                    <span className="text-white font-medium">{approval.action_summary}</span>
                                                </div>
                                                <div className="text-gray-400 text-sm mt-1">
                                                    Requested by {approval.requester_name} • {approval.action_type}
                                                </div>
                                            </div>
                                            <span className={`px-2 py-1 rounded text-xs capitalize ${getSensitivityColor(approval.sensitivity)} text-white`}>
                                                {approval.sensitivity}
                                            </span>
                                        </div>

                                        <div className="mt-4 flex items-center justify-between">
                                            <div className="text-gray-400 text-sm">
                                                Expires: {new Date(approval.expires_at).toLocaleString()}
                                                {approval.is_reversible && <span className="ml-2 text-green-400">(Reversible)</span>}
                                            </div>
                                            <div className="flex gap-2">
                                                <button
                                                    onClick={() => processApproval(approval.id, false)}
                                                    className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded text-sm"
                                                >
                                                    Reject
                                                </button>
                                                <button
                                                    onClick={() => processApproval(approval.id, true)}
                                                    className="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded text-sm"
                                                >
                                                    Approve
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {/* Audit Tab */}
                {activeTab === 'audit' && (
                    <div className="space-y-6">
                        <h2 className="text-xl font-semibold text-white">Audit Trail</h2>

                        <div className="bg-slate-800/50 rounded-xl border border-red-500/20 overflow-hidden">
                            <table className="w-full">
                                <thead className="bg-slate-700/50">
                                    <tr>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Timestamp</th>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Actor</th>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Action</th>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Resource</th>
                                        <th className="text-left text-red-300 text-sm font-medium px-4 py-3">Outcome</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {auditLogs.map((log) => (
                                        <tr key={log.id} className="border-t border-slate-700">
                                            <td className="px-4 py-3 text-gray-400 text-sm">
                                                {new Date(log.timestamp).toLocaleString()}
                                            </td>
                                            <td className="px-4 py-3 text-white text-sm">
                                                {log.actor_name || log.actor_id}
                                            </td>
                                            <td className="px-4 py-3 text-white text-sm">
                                                {log.action}
                                            </td>
                                            <td className="px-4 py-3 text-gray-400 text-sm">
                                                {log.resource_type}{log.resource_id ? `:${log.resource_id.slice(0, 8)}` : ''}
                                            </td>
                                            <td className="px-4 py-3">
                                                <span className={`px-2 py-0.5 rounded text-xs ${log.outcome === 'success' ? 'bg-green-500/20 text-green-300' :
                                                        log.outcome === 'denied' ? 'bg-red-500/20 text-red-300' :
                                                            'bg-gray-500/20 text-gray-300'
                                                    }`}>
                                                    {log.outcome}
                                                </span>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                )}

                {/* Health Tab */}
                {activeTab === 'health' && health && (
                    <div className="space-y-6">
                        <h2 className="text-xl font-semibold text-white">System Health</h2>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div className="bg-slate-800/50 rounded-xl border border-red-500/20 p-5">
                                <div className="flex items-center justify-between">
                                    <span className="text-gray-400">Database</span>
                                    <span className={`${getHealthStatusColor(health.checks.database.status)} capitalize`}>
                                        {health.checks.database.status}
                                    </span>
                                </div>
                            </div>
                            <div className="bg-slate-800/50 rounded-xl border border-red-500/20 p-5">
                                <div className="flex items-center justify-between">
                                    <span className="text-gray-400">Approvals</span>
                                    <span className={`${getHealthStatusColor(health.checks.approvals.status)} capitalize`}>
                                        {health.checks.approvals.status}
                                    </span>
                                </div>
                                {health.checks.approvals.expired_count > 0 && (
                                    <div className="text-yellow-400 text-sm mt-2">
                                        {health.checks.approvals.expired_count} expired
                                    </div>
                                )}
                            </div>
                            <div className="bg-slate-800/50 rounded-xl border border-red-500/20 p-5">
                                <div className="flex items-center justify-between">
                                    <span className="text-gray-400">Operations</span>
                                    <span className={`${getHealthStatusColor(health.checks.operations.status)} capitalize`}>
                                        {health.checks.operations.status}
                                    </span>
                                </div>
                                {health.checks.operations.stale_locks > 0 && (
                                    <div className="text-yellow-400 text-sm mt-2">
                                        {health.checks.operations.stale_locks} stale locks
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="bg-slate-800/50 rounded-xl border border-red-500/20 p-6">
                            <h3 className="text-lg font-medium text-white mb-4">System Overview</h3>
                            <div className="flex items-center gap-4">
                                <div className={`text-4xl font-bold ${getHealthStatusColor(health.status)}`}>
                                    {health.status.toUpperCase()}
                                </div>
                                <div className="text-gray-400 text-sm">
                                    Last checked: {new Date(health.timestamp).toLocaleString()}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {/* New User Modal */}
                {showNewUser && (
                    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
                        <div className="bg-slate-800 rounded-xl border border-red-500/30 p-6 w-full max-w-md">
                            <h3 className="text-xl font-semibold text-white mb-4">Add New User</h3>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-red-300 text-sm mb-1">Email</label>
                                    <input
                                        type="email"
                                        value={newUser.email}
                                        onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                                        className="w-full px-3 py-2 bg-slate-700 border border-red-500/30 rounded-lg text-white focus:outline-none focus:border-red-500"
                                        placeholder="user@example.com"
                                    />
                                </div>
                                <div>
                                    <label className="block text-red-300 text-sm mb-1">Name</label>
                                    <input
                                        type="text"
                                        value={newUser.name}
                                        onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                                        className="w-full px-3 py-2 bg-slate-700 border border-red-500/30 rounded-lg text-white focus:outline-none focus:border-red-500"
                                        placeholder="John Doe"
                                    />
                                </div>
                                <div>
                                    <label className="block text-red-300 text-sm mb-1">Role</label>
                                    <select
                                        value={newUser.role}
                                        onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                                        className="w-full px-3 py-2 bg-slate-700 border border-red-500/30 rounded-lg text-white focus:outline-none focus:border-red-500"
                                    >
                                        <option value="viewer">Viewer</option>
                                        <option value="contributor">Contributor</option>
                                        <option value="manager">Manager</option>
                                        <option value="admin">Admin</option>
                                    </select>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 mt-6">
                                <button
                                    onClick={() => setShowNewUser(false)}
                                    className="px-4 py-2 text-red-300 hover:text-white transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={createUser}
                                    disabled={!newUser.email || !newUser.name}
                                    className="px-4 py-2 bg-red-600 hover:bg-red-700 disabled:bg-red-600/50 text-white rounded-lg transition-colors"
                                >
                                    Create User
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

export default AdminDashboard;
