"use client";

import React, { useState, useEffect } from 'react';

const API_BASE_URL = "http://localhost:8000/api";

interface EscalationInfo {
    id: string;
    task_id: string | null;
    project_id: string | null;
    reason: string;
    escalated_to: string;
    type: string | null;
    status: string;
    suggested_action: string | null;
    created_at: string;
    acknowledged_at: string | null;
}

export default function EscalationAlerts() {
    const [escalations, setEscalations] = useState<EscalationInfo[]>([]);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchEscalations();

        // Poll for updates every 30 seconds
        const interval = setInterval(fetchEscalations, 30000);
        return () => clearInterval(interval);
    }, []);

    const fetchEscalations = async () => {
        try {
            const res = await fetch(`${API_BASE_URL}/execution/escalations`);
            const data = await res.json();
            setEscalations(data);
        } catch (error) {
            console.error('Failed to fetch escalations:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const acknowledgeEscalation = async (escalationId: string) => {
        try {
            const res = await fetch(`${API_BASE_URL}/execution/escalations/${escalationId}/acknowledge`, {
                method: 'POST'
            });
            if (res.ok) {
                fetchEscalations();
            }
        } catch (error) {
            console.error('Failed to acknowledge escalation:', error);
        }
    };

    const resolveEscalation = async (escalationId: string) => {
        const notes = prompt('Enter resolution notes:');
        if (!notes) return;

        try {
            const res = await fetch(`${API_BASE_URL}/execution/escalations/${escalationId}/resolve`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ resolution_notes: notes })
            });
            if (res.ok) {
                fetchEscalations();
            }
        } catch (error) {
            console.error('Failed to resolve escalation:', error);
        }
    };

    const getTypeIcon = (type: string | null) => {
        switch (type) {
            case 'overdue': return '⏰';
            case 'blocked': return '🚧';
            case 'no_update': return '📭';
            default: return '⚠️';
        }
    };

    const getTypeBadge = (type: string | null) => {
        switch (type) {
            case 'overdue': return 'bg-red-100 text-red-800';
            case 'blocked': return 'bg-orange-100 text-orange-800';
            case 'no_update': return 'bg-yellow-100 text-yellow-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const formatTimeAgo = (dateStr: string) => {
        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
        const diffDays = Math.floor(diffHours / 24);

        if (diffDays > 0) return `${diffDays}d ago`;
        if (diffHours > 0) return `${diffHours}h ago`;
        return 'Just now';
    };

    if (isLoading) {
        return (
            <div className="bg-white rounded-xl shadow-lg p-6 animate-pulse">
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
                <div className="space-y-3">
                    <div className="h-16 bg-gray-200 rounded"></div>
                    <div className="h-16 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    const openEscalations = escalations.filter(e => e.status === 'open');
    const acknowledgedEscalations = escalations.filter(e => e.status === 'acknowledged');

    return (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
            {/* Header */}
            <div className={`p-5 ${escalations.length > 0 ? 'bg-gradient-to-r from-red-600 to-orange-600' : 'bg-gradient-to-r from-green-600 to-emerald-600'} text-white`}>
                <div className="flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-bold">Escalation Alerts</h2>
                        <p className={`text-sm ${escalations.length > 0 ? 'text-red-200' : 'text-green-200'}`}>
                            {escalations.length > 0
                                ? `${escalations.length} issues require attention`
                                : 'All clear - no escalations'
                            }
                        </p>
                    </div>
                    {openEscalations.length > 0 && (
                        <div className="bg-white bg-opacity-20 rounded-full px-4 py-2 font-bold text-2xl">
                            {openEscalations.length}
                        </div>
                    )}
                </div>
            </div>

            <div className="p-6">
                {escalations.length === 0 ? (
                    <div className="text-center py-8">
                        <div className="text-4xl mb-2">✅</div>
                        <p className="text-gray-500">No escalations at this time</p>
                        <p className="text-gray-400 text-sm">All tasks are progressing normally</p>
                    </div>
                ) : (
                    <div className="space-y-4">
                        {/* Open Escalations */}
                        {openEscalations.length > 0 && (
                            <div>
                                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                                    Requires Attention ({openEscalations.length})
                                </h3>
                                {openEscalations.map((escalation) => (
                                    <div key={escalation.id} className="border-l-4 border-red-500 bg-red-50 p-4 rounded-r-lg mb-3">
                                        <div className="flex justify-between items-start">
                                            <div className="flex items-start gap-3">
                                                <span className="text-2xl">{getTypeIcon(escalation.type)}</span>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className={`px-2 py-0.5 rounded text-xs font-medium ${getTypeBadge(escalation.type)}`}>
                                                            {escalation.type || 'unknown'}
                                                        </span>
                                                        <span className="text-gray-400 text-xs">{formatTimeAgo(escalation.created_at)}</span>
                                                    </div>
                                                    <p className="font-medium text-gray-800 mt-1">{escalation.reason}</p>
                                                    {escalation.suggested_action && (
                                                        <p className="text-sm text-gray-600 mt-1">
                                                            💡 {escalation.suggested_action}
                                                        </p>
                                                    )}
                                                    <p className="text-xs text-gray-500 mt-1">
                                                        Escalated to: {escalation.escalated_to}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                        <div className="flex gap-2 mt-3 ml-9">
                                            <button
                                                onClick={() => acknowledgeEscalation(escalation.id)}
                                                className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                                            >
                                                Acknowledge
                                            </button>
                                            <button
                                                onClick={() => resolveEscalation(escalation.id)}
                                                className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                                            >
                                                Resolve
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Acknowledged Escalations */}
                        {acknowledgedEscalations.length > 0 && (
                            <div>
                                <h3 className="text-sm font-semibold text-gray-500 uppercase mb-2">
                                    In Progress ({acknowledgedEscalations.length})
                                </h3>
                                {acknowledgedEscalations.map((escalation) => (
                                    <div key={escalation.id} className="border-l-4 border-yellow-500 bg-yellow-50 p-4 rounded-r-lg mb-3">
                                        <div className="flex justify-between items-start">
                                            <div className="flex items-start gap-3">
                                                <span className="text-2xl">{getTypeIcon(escalation.type)}</span>
                                                <div>
                                                    <div className="flex items-center gap-2">
                                                        <span className="px-2 py-0.5 rounded text-xs font-medium bg-yellow-200 text-yellow-800">
                                                            Acknowledged
                                                        </span>
                                                        <span className="text-gray-400 text-xs">
                                                            {formatTimeAgo(escalation.acknowledged_at || escalation.created_at)}
                                                        </span>
                                                    </div>
                                                    <p className="font-medium text-gray-800 mt-1">{escalation.reason}</p>
                                                </div>
                                            </div>
                                            <button
                                                onClick={() => resolveEscalation(escalation.id)}
                                                className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                                            >
                                                Resolve
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}

export { EscalationAlerts };
