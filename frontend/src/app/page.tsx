'use client';

import { useState } from 'react';
import AgentActivityLog from '@/components/AgentActivityLog';
import InterventionModal from '@/components/InterventionModal';

export default function Dashboard() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalContent, setModalContent] = useState('');

  return (
    <main className="min-h-screen bg-slate-900 text-white p-8">
      <header className="mb-8 flex justify-between items-center bg-slate-800 p-6 rounded-2xl shadow-lg border border-slate-700/50 backdrop-blur-md">
        <div>
          <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">Virtual AI Manager</h1>
          <p className="text-slate-400 mt-2">Control Plane & Orchestrator</p>
        </div>
        <div className="flex gap-4">
          <div className="bg-emerald-500/10 text-emerald-400 px-4 py-2 rounded-full border border-emerald-500/20 shadow-[0_0_15px_rgba(16,185,129,0.2)]">
            Only System: Online
          </div>
          <button 
            onClick={() => { setModalContent('System Override Initiated'); setIsModalOpen(true); }}
            className="px-6 py-2 bg-red-500 hover:bg-red-600 rounded-full font-semibold transition-all shadow-[0_0_20px_rgba(239,68,68,0.3)]"
          >
            Emergency Override
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Stats / Overview */}
        <section className="col-span-1 space-y-6">
           <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-lg">
              <h2 className="text-xl font-semibold mb-4 text-blue-300">System Pulse</h2>
              <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span>Active Agents</span>
                    <span className="font-mono text-purple-400">5</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Tasks Pending</span>
                    <span className="font-mono text-yellow-400">12</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Decisions Logged</span>
                    <span className="font-mono text-green-400">1,240</span>
                  </div>
              </div>
           </div>
           
           <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 shadow-lg">
              <h2 className="text-xl font-semibold mb-4 text-blue-300">Active Goals</h2>
              <ul className="space-y-3 text-slate-300 text-sm">
                <li className="flex items-start gap-2">
                  <span className="w-2 h-2 mt-1.5 rounded-full bg-blue-500"></span>
                  <span>Optimize Q4 Hiring Pipeline</span>
                </li>
                <li className="flex items-start gap-2">
                  <span className="w-2 h-2 mt-1.5 rounded-full bg-purple-500"></span>
                  <span>Monitor "Project Alpha" Deadlines</span>
                </li>
              </ul>
           </div>
        </section>

        {/* Activity Log */}
        <section className="col-span-2">
           <div className="bg-slate-800 rounded-2xl border border-slate-700 shadow-lg overflow-hidden h-[600px] flex flex-col">
              <div className="p-6 border-b border-slate-700 bg-slate-800/50">
                 <h2 className="text-xl font-semibold text-blue-300">Live Agent Activity</h2>
              </div>
              <AgentActivityLog />
           </div>
        </section>
      </div>

      <InterventionModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} content={modalContent} />
    </main>
  );
}
