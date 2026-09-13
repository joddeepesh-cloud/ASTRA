import { useState } from 'react';
import type { ActiveTab, Observation } from '../types';
import { Sidebar } from '../components/Sidebar';
import { TopBar } from '../components/TopBar';
import { MissionOverviewPage } from '../pages/MissionOverviewPage';
import { ObservationsPage } from '../pages/ObservationsPage';
import { ObservationLibraryPage } from '../pages/ObservationLibraryPage';
import { ObservationDetailPage } from '../pages/ObservationDetailPage';
import { ResearchModePage } from '../pages/ResearchModePage';
import { CopilotPage } from '../pages/CopilotPage';
import { MOCK_OBSERVATIONS } from '../data/mockData';

import type { TriageResponse } from '../types/api';

interface AppLayoutProps {
  onGoToLanding: () => void;
  initialTab?: ActiveTab;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ onGoToLanding, initialTab = 'overview' }) => {
  const [activeTab, setActiveTab] = useState<ActiveTab>(initialTab);
  const [selectedObservation, setSelectedObservation] = useState<Observation>(MOCK_OBSERVATIONS[0]);

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
    setActiveTab('detail');
  };

  const getPageTitle = () => {
    switch (activeTab) {
      case 'overview':
        return { title: 'Mission Overview', subtitle: 'Real-time observation triage stream' };
      case 'observations':
        return { title: 'Observations', subtitle: 'Monitor recent astronomical observations and mission priorities' };
      case 'library':
        return { title: 'Observation Library', subtitle: 'Explore astronomical observations and learn more about survey structures' };
      case 'anomalies':
        return { title: 'Anomaly Queue', subtitle: 'High out-of-distribution targets' };
      case 'detail':
        return { title: `Observation Detail: ${selectedObservation.id}`, subtitle: 'Diagnostic scientific analysis' };
      case 'research':
        return { title: 'Research & Experimental Mode', subtitle: 'Custom observation upload & domain validation' };
      case 'copilot':
        return { title: 'AI Mission Copilot', subtitle: 'Automated scientific explanation assistant' };
      default:
        return { title: 'Mission Control', subtitle: 'ASTRA Triage System' };
    }
  };

  const { title, subtitle } = getPageTitle();

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100 font-sans">
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
        />

        <main className="flex-1 overflow-y-auto">
          {activeTab === 'overview' && (
            <MissionOverviewPage
              onInvestigate={handleInspectObservation}
              onViewLibrary={() => setActiveTab('library')}
            />
          )}

          {activeTab === 'observations' && (
            <ObservationsPage onAnalyze={handleInspectObservation} />
          )}

          {activeTab === 'library' && (
            <ObservationLibraryPage onAnalyze={handleInspectObservation} />
          )}

          {activeTab === 'anomalies' && (
            <MissionOverviewPage
              onInvestigate={handleInspectObservation}
              onViewLibrary={() => setActiveTab('library')}
            />
          )}

          {activeTab === 'detail' && (
            <ObservationDetailPage
              observation={selectedObservation}
              onBack={() => setActiveTab('overview')}
            />
          )}

          {activeTab === 'research' && (
            <ResearchModePage onInspectResult={handleInspectLiveResult} />
          )}

          {activeTab === 'copilot' && (
            <CopilotPage activeObservation={selectedObservation} />
          )}
        </main>
      </div>
    </div>
  );
};
