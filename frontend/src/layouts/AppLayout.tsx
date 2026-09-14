import { useState } from 'react';
import type { ActiveTab, Observation } from '../types';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';
import { ToastContainer } from '../components/ToastContainer';
import { MissionBriefingPage } from '../pages/MissionBriefingPage';
import { ObservationsPage } from '../pages/ObservationsPage';
import { ObservationLibraryPage } from '../pages/ObservationLibraryPage';
import { ObservationDetailPage } from '../pages/ObservationDetailPage';
import { ResearchModePage } from '../pages/ResearchModePage';
import { CopilotPage } from '../pages/CopilotPage';
import { HistoryPage } from '../pages/HistoryPage';
import { AnomalyQueuePage } from '../pages/AnomalyQueuePage';
import libraryData from '../data/observationLibrary.json';

import type { TriageResponse } from '../types/api';

import { recordLiveAnalysis, getAnalysisHistory } from '../services/analysisHistory';
import type { AnalysisHistoryRecord } from '../types';

interface AppLayoutProps {
  onGoToLanding: () => void;
  initialTab?: ActiveTab;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ onGoToLanding, initialTab = 'briefing' }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>(initialTab);
  const [selectedObservation, setSelectedObservation] = useState<Observation>(() => (libraryData as Observation[])[0]);

  const handleInspectObservation = (obs: Observation) => {
    setSelectedObservation(obs);
    setActiveTab('detail');
  };

  const handleInspectLiveResult = (result: TriageResponse, _file: File, previewUrl: string) => {
    const now = new Date();
    const dateStr = now.toISOString().replace(/[-:T.]/g, '').slice(0, 14);
    const broadMorph = (
      result.predicted_class === 'SPIRAL'
        ? 'SPIRAL'
        : result.predicted_class === 'FEATURED_DISK'
        ? 'DISK_FEATURE'
        : result.predicted_class === 'SMOOTH'
        ? 'SMOOTH'
        : 'OTHER'
    );

    const liveObs: Observation = {
      id: `LIVE-${dateStr}`,
      dr7objid: 'N/A (USER FILE)',
      asset_id: 999999,
      ra: 0.0,
      dec: 0.0,
      gz2class: result.predicted_class || 'SMOOTH',
      broad_morphology: broadMorph,
      object_type: 'Galaxy',
      confidence: result.class_confidence ?? 1.0,
      anomaly_score: result.experimental_triage_score ?? 0.0,
      ood_score: result.novelty_score ?? 0.0,
      priority: result.priority_level || 'LOW',
      catalog_status: 'UNCHECKED',
      catalog_name: 'Unregistered User Upload',
      observation_time: now.toISOString(),
      image_url: previewUrl,
      split: 'live',
      explanation: result.explanation,
      morphology_probs: result.class_probabilities
        ? Object.entries(result.class_probabilities).map(([label, probability]) => ({
            label,
            probability
          }))
        : [],
      is_demo: false,
      is_live: true,
      triage_response: result
    };

    setSelectedObservation(liveObs);
    recordLiveAnalysis(result, _file.name, liveObs.id);
    setActiveTab('detail');
  };

  const handleInspectObservationById = (obsId: string) => {
    // 1. Check Library dataset
    const libraryMatch = (libraryData as Observation[]).find((o) => o.id === obsId);
    if (libraryMatch) {
      handleInspectObservation(libraryMatch);
      return;
    }

    // 2. Check User Analysis History
    const historyRecords = getAnalysisHistory();
    const historyMatch = historyRecords.find((r: AnalysisHistoryRecord) => r.observation_id === obsId);
    if (historyMatch) {
      const obs: Observation = {
        id: historyMatch.observation_id,
        dr7objid: 'USER-UPLOAD',
        asset_id: 999999,
        ra: 0.0,
        dec: 0.0,
        gz2class: historyMatch.morphology,
        broad_morphology: historyMatch.morphology === 'SPIRAL' ? 'SPIRAL' : historyMatch.morphology === 'SMOOTH' ? 'SMOOTH' : 'DISK_FEATURE',
        object_type: 'Galaxy',
        confidence: historyMatch.confidence,
        anomaly_score: historyMatch.triage_score,
        ood_score: historyMatch.triage_score,
        priority: historyMatch.priority,
        catalog_status: 'UNCHECKED',
        catalog_name: historyMatch.filename,
        observation_time: historyMatch.timestamp,
        image_url: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100"><rect width="100" height="100" fill="%23070B11"/><text x="50%" y="50%" dominant-baseline="middle" text-anchor="middle" fill="%238FAFC2" font-size="10" font-family="monospace">USER FILE</text></svg>',
        explanation: `User observation cutout ${historyMatch.filename} analyzed in Research Mode.`,
        morphology_probs: [{ label: historyMatch.morphology, probability: historyMatch.confidence }],
        is_demo: false
      };
      handleInspectObservation(obs);
      return;
    }

    // 3. Graceful fallback Toast if missing
    if (typeof window !== 'undefined') {
      window.dispatchEvent(
        new CustomEvent('astra-toast', {
          detail: {
            title: 'Target Unavailable',
            message: `Observation payload for ${obsId} is no longer active in mission record.`,
            type: 'warning'
          }
        })
      );
    }
  };

  const getPageTitle = () => {
    switch (activeTab) {
      case 'briefing':
        return { title: 'Mission Briefing', subtitle: 'Launchpad for ASTRA astronomical triage & scientific discovery' };
      case 'observations':
        return { title: 'Observations', subtitle: 'Monitor recent astronomical observations and mission priorities' };
      case 'library':
        return { title: 'Observation Library', subtitle: 'Explore astronomical observations and learn more about survey structures' };
      case 'anomalies':
        return { title: 'Anomaly Queue', subtitle: 'High out-of-distribution targets prioritized for scientific review' };
      case 'detail':
        return { title: `Observation Detail: ${selectedObservation.id}`, subtitle: 'Diagnostic scientific analysis' };
      case 'research':
        return { title: 'Research & Experimental Mode', subtitle: 'Custom observation upload & domain validation' };
      case 'history':
        return { title: 'Analysis History', subtitle: 'Historical ledger of observation triage runs' };
      case 'copilot':
        return { title: 'AI Mission Copilot', subtitle: 'Automated scientific explanation assistant' };
      default:
        return { title: 'Mission Control', subtitle: 'ASTRA Triage System' };
    }
  };

  const { title, subtitle } = getPageTitle();

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans relative">
      <ToastContainer />
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onGoToLanding={onGoToLanding}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        <TopBar
          title={title}
          subtitle={subtitle}
          onSearchClick={() => setActiveTab('library')}
          onInspectObservationById={handleInspectObservationById}
        />

        <main className="flex-1 overflow-y-auto">
          {activeTab === 'briefing' && (
            <MissionBriefingPage onNavigateTab={(tab) => setActiveTab(tab)} />
          )}

          {activeTab === 'observations' && (
            <ObservationsPage onAnalyze={handleInspectObservation} />
          )}

          {activeTab === 'library' && (
            <ObservationLibraryPage onAnalyze={handleInspectObservation} />
          )}

          {activeTab === 'anomalies' && (
            <AnomalyQueuePage onInspectObservation={handleInspectObservation} />
          )}

          {activeTab === 'detail' && (
            <ObservationDetailPage
              observation={selectedObservation}
              onBack={() => setActiveTab('briefing')}
            />
          )}

          {activeTab === 'research' && (
            <ResearchModePage onInspectResult={handleInspectLiveResult} />
          )}

          {activeTab === 'history' && (
            <HistoryPage onInspectObservation={handleInspectObservation} />
          )}

          {activeTab === 'copilot' && (
            <CopilotPage activeObservation={selectedObservation} />
          )}
        </main>
      </div>
    </div>
  );
};

