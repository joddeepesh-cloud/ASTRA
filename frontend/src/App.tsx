import { useState } from 'react';
import { LandingPage } from './pages/LandingPage';
import { AppLayout } from './layouts/AppLayout';

export function App() {
  const [currentView, setCurrentView] = useState<'landing' | 'app'>('landing');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      {currentView === 'landing' ? (
        <LandingPage onExplore={() => setCurrentView('app')} />
      ) : (
        <AppLayout onGoToLanding={() => setCurrentView('landing')} />
      )}
    </div>
  );
}

export default App;
