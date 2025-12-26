"use client";

import SettingsPage from '@/components/SettingsPage';

export default function Settings() {
    return (
        <main className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 p-4 md:p-8">
            <div className="max-w-4xl mx-auto">
                <div className="flex items-center gap-4 mb-8">
                    <a
                        href="/"
                        className="text-slate-400 hover:text-white transition-colors"
                    >
                        ← Back to Dashboard
                    </a>
                </div>
                <SettingsPage />
            </div>
        </main>
    );
}
