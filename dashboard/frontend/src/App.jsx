import React, { useState } from 'react';
import Navbar from './components/Navbar';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import SystemFlowPage from './pages/SystemFlowPage';
import AboutPage from './pages/AboutPage';

export default function App() {
  const [activePage, setActivePage] = useState('landing');
  const [selectedCaseForFlow, setSelectedCaseForFlow] = useState('CB_IN_2026_00431');

  const handleInspectCaseInFlow = (caseId) => {
    setSelectedCaseForFlow(caseId);
    setActivePage('flow');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex flex-col font-sans">
      {/* Sleek Minimalist Navbar */}
      <Navbar activePage={activePage} setActivePage={setActivePage} />

      {/* Main Multi-Page Container */}
      <main className="flex-1 pt-4">
        {activePage === 'landing' && (
          <LandingPage onNavigate={(page) => setActivePage(page)} />
        )}

        {activePage === 'dashboard' && (
          <DashboardPage onSelectCaseForFlow={handleInspectCaseInFlow} />
        )}

        {activePage === 'flow' && (
          <SystemFlowPage initialCaseId={selectedCaseForFlow} />
        )}

        {activePage === 'about' && (
          <AboutPage onNavigateToFlow={() => setActivePage('flow')} />
        )}
      </main>

      {/* Minimalist, Clean Footer (Zero Buzzword Jargon) */}
      <footer className="border-t border-slate-200/80 bg-white py-6 text-center text-xs text-slate-400">
        AI Chargeback Evidence Responder • Built for Razorpay Hackathon
      </footer>
    </div>
  );
}
