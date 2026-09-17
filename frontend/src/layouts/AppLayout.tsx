import { useState, useEffect } from 'react';
import type { ActiveTab, Observation } from '../types';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';
import { ToastContainer } from '../components/ToastContainer';
import { MissionBriefingPage } from '../pages/MissionBriefingPage';
import { ObservationLibraryPage } from '../pages/ObservationLibraryPage';
import { ObservationDetailPage } from '../pages/ObservationDetailPage';
import { ResearchModePage } from '../pages/ResearchModePage';
import { CopilotPage } from '../pages/CopilotPage';
import { HistoryPage } from '../pages/HistoryPage';
import { AnomalyQueuePage } from '../pages/AnomalyQueuePage';
import { SettingsPage } from '../pages/SettingsPage';
import libraryData from '../data/observationLibrary.json';
import { CosmicBackground } from '../components/CosmicBackground';

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

  const navigateToTab = (tab: ActiveTab, obs?: Observation, replace = false) => {
    const targetTab: ActiveTab = (tab as string) === 'observations' ? 'anomalies' : tab;
    setActiveTab(targetTab);
    if (obs) {
      setSelectedObservation(obs);
    }

    if (typeof window !== 'undefined') {
      const currentIndex = window.history.state?.index ?? 0;
      const nextIndex = replace ? currentIndex : currentIndex + 1;
      const stateObj = { tab: targetTab, obsId: obs?.id || (targetTab === 'detail' ? selectedObservation.id : undefined), index: nextIndex };
      const hash = `#${targetTab}${targetTab === 'detail' ? '/' + (obs?.id || selectedObservation.id) : ''}`;

      if (replace) {
        window.history.replaceState(stateObj, '', hash);
      } else {
        window.history.pushState(stateObj, '', hash);
      }
    }
  };

  useEffect(() => {
    const parseHash = () => {
      if (typeof window === 'undefined') return;
      const hash = window.location.hash.replace(/^#\/?/, '');
      if (!hash) return;

      const [rawTab, obsId] = hash.split('/');
      let tab: ActiveTab = 'briefing';
      if (rawTab === 'observations' || rawTab === 'anomalies') tab = 'anomalies';
      else if (rawTab === 'library') tab = 'library';
      else if (rawTab === 'detail') tab = 'detail';
      else if (rawTab === 'research') tab = 'research';
      else if (rawTab === 'history') tab = 'history';
      else if (rawTab === 'copilot') tab = 'copilot';
      else if (rawTab === 'settings') tab = 'settings';
      else if (rawTab === 'briefing') tab = 'briefing';

      setActiveTab(tab);

      if (obsId) {
        const match = (libraryData as Observation[]).find((o) => o.id === obsId);
        if (match) {
          setSelectedObservation(match);
        }
      }
    };

    if (typeof window !== 'undefined') {
      if (window.location.hash) {
        parseHash();
      } else {
        window.history.replaceState({ tab: initialTab, index: 0 }, '', `#${initialTab}`);
      }
    }

    const handlePopState = (e: PopStateEvent) => {
      if (e.state && e.state.tab) {
        const tab: ActiveTab = e.state.tab === 'observations' ? 'anomalies' : e.state.tab;
        setActiveTab(tab);
        if (e.state.obsId) {
          const match = (libraryData as Observation[]).find((o) => o.id === e.state.obsId);
          if (match) {
            setSelectedObservation(match);
          }
        }
      } else {
        parseHash();
      }
    };

    window.addEventListener('popstate', handlePopState);
    return () => {
      window.removeEventListener('popstate', handlePopState);
    };
  }, [initialTab]);

  const handleGoBack = () => {
    if (typeof window !== 'undefined' && window.history.state && window.history.state.index > 0) {
      window.history.back();
    } else {
      // Safe internal fallback navigation
      if (activeTab === 'detail') {
        navigateToTab('anomalies', undefined, true);
      } else {
        navigateToTab('briefing', undefined, true);
      }
    }
  };

  const handleInspectObservation = (obs: Observation) => {
    navigateToTab('detail', obs);
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
      object_type: (result.object_type === 'GALAXY' || result.object_type === 'Galaxy') ? 'Galaxy' : 'Unresolved astronomical source',
      confidence: result.class_confidence ?? 0.0,
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

    recordLiveAnalysis(result, _file.name, liveObs.id);
    navigateToTab('detail', liveObs);
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
        object_type: (historyMatch.object_type === 'GALAXY' || historyMatch.object_type === 'Galaxy' || historyMatch.filename?.startsWith('LIB-')) ? 'Galaxy' : 'Unresolved astronomical source',
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
      case 'settings':
        return { title: 'System Settings', subtitle: 'Workstation diagnostics & mission console preferences' };
      default:
        return { title: 'Mission Control', subtitle: 'ASTRA Triage System' };
    }
  };

  const { title, subtitle } = getPageTitle();

  return (
    <div className="flex h-screen w-screen bg-[#03040A] text-[#ECEAF2] font-sans relative overflow-hidden">
      <CosmicBackground variant="dashboard" />
      <ToastContainer />
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={(tab) => navigateToTab(tab)}
        onGoToLanding={onGoToLanding}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        <TopBar
          title={title}
          subtitle={subtitle}
          onSearchClick={() => navigateToTab('library')}
          onInspectObservationById={handleInspectObservationById}
        />

        <main className="flex-1 min-h-0 overflow-y-auto relative">
          {activeTab === 'briefing' && (
            <MissionBriefingPage onNavigateTab={(tab) => navigateToTab(tab)} />
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
              onBack={handleGoBack}
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

          {activeTab === 'settings' && (
            <SettingsPage />
          )}
        </main>
      </div>
    </div>
  );
};
