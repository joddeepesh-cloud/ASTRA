import React, { useState, useMemo } from 'react';
import type { Observation, BroadMorphology } from '../types';
import libraryData from '../data/observationLibrary.json';
import { PriorityBadge } from '../components/PriorityBadge';
import { EmptyState } from '../components/EmptyState';
import { ObservationDossierModal } from '../components/ObservationDossierModal';
import { AskAstraModal } from '../components/AskAstraModal';
import {
  Search,
  SlidersHorizontal,
  Grid3X3,
  List,
  Sparkles,
  ArrowRight,
  Eye,
  ChevronLeft,
  ChevronRight,
  Info
} from 'lucide-react';

const LIBRARY_OBSERVATIONS = libraryData as Observation[];

interface ObservationLibraryPageProps {
  onAnalyze: (obs: Observation) => void;
}

export const ObservationLibraryPage: React.FC<ObservationLibraryPageProps> = ({ onAnalyze }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [morphologyFilter, setMorphologyFilter] = useState<'ALL' | BroadMorphology>('ALL');
  const [priorityFilter, setPriorityFilter] = useState<'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'>('ALL');
  const [confidenceFilter, setConfidenceFilter] = useState<'ALL' | 'HIGH' | 'MED' | 'LOW'>('ALL');
  const [anomalyFilter, setAnomalyFilter] = useState<'ALL' | 'ANOMALOUS' | 'STANDARD'>('ALL');
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'priority' | 'anomaly' | 'confidence'>('newest');
  
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 24; // Scalable pagination for 2,000+ observations

  // Dossier and Ask Astra modal states
  const [dossierObs, setDossierObs] = useState<Observation | null>(null);
  const [askAstraObs, setAskAstraObs] = useState<Observation | null>(null);

  const filteredAndSortedObservations = useMemo(() => {
    let result = LIBRARY_OBSERVATIONS.filter((obs) => {
      // Text Search across ID, ObjID, asset ID, morphology, catalog name, and explanation
      const q = searchQuery.toLowerCase().trim();
      if (q) {
        const matchesId = obs.id.toLowerCase().includes(q);
        const matchesAsset = String(obs.asset_id).includes(q);
        const matchesObjId = obs.dr7objid.toLowerCase().includes(q);
        const matchesMorph = obs.broad_morphology.toLowerCase().includes(q) || obs.gz2class.toLowerCase().includes(q);
        const matchesCatalog = obs.catalog_name ? obs.catalog_name.toLowerCase().includes(q) : false;
        const matchesExplanation = obs.explanation ? obs.explanation.toLowerCase().includes(q) : false;

        if (!matchesId && !matchesAsset && !matchesObjId && !matchesMorph && !matchesCatalog && !matchesExplanation) {
          return false;
        }
      }

      // Morphology Filter
      if (morphologyFilter !== 'ALL' && obs.broad_morphology !== morphologyFilter) {
        return false;
      }

      // Priority Filter
      if (priorityFilter !== 'ALL' && obs.priority !== priorityFilter) {
        return false;
      }

      // Anomaly Score Filter (High anomaly triage >= 0.60)
      if (anomalyFilter === 'ANOMALOUS' && obs.anomaly_score < 0.60) {
        return false;
      }
      if (anomalyFilter === 'STANDARD' && obs.anomaly_score >= 0.60) {
        return false;
      }

      // Confidence Filter
      const conf = obs.confidence ?? 0;
      if (confidenceFilter === 'HIGH' && conf < 0.90) return false;
      if (confidenceFilter === 'MED' && (conf < 0.80 || conf >= 0.90)) return false;
      if (confidenceFilter === 'LOW' && conf >= 0.80) return false;

      return true;
    });

    // Sorting Logic
    return result.sort((a, b) => {
      if (sortBy === 'newest') return b.id.localeCompare(a.id);
      if (sortBy === 'oldest') return a.id.localeCompare(b.id);
      if (sortBy === 'priority') {
        const pOrder: Record<string, number> = { HIGH: 3, MEDIUM: 2, LOW: 1 };
        return (pOrder[b.priority] || 0) - (pOrder[a.priority] || 0);
      }
      if (sortBy === 'anomaly') return b.anomaly_score - a.anomaly_score;
      if (sortBy === 'confidence') return (b.confidence ?? 0) - (a.confidence ?? 0);
      return 0;
    });
  }, [searchQuery, morphologyFilter, priorityFilter, confidenceFilter, anomalyFilter, sortBy]);

  // Pagination calculation
  const totalItems = filteredAndSortedObservations.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedObservations = filteredAndSortedObservations.slice(startIndex, startIndex + itemsPerPage);

  const resetFilters = () => {
    setSearchQuery('');
    setMorphologyFilter('ALL');
    setPriorityFilter('ALL');
    setConfidenceFilter('ALL');
    setAnomalyFilter('ALL');
    setSortBy('newest');
    setCurrentPage(1);
  };

  return (
    <div className="p-4 md:p-8 space-y-6 max-w-6xl mx-auto font-sans-ui text-[#F2F4F7] selection:bg-[#C7CDD5]/30">
      
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#252D37] pb-4">
        <div>
          <div className="flex items-center gap-2 font-mono-tech">
            <h1 className="text-2xl font-bold font-serif-display text-[#F2F4F7] tracking-wider uppercase">
              OBSERVATION LIBRARY
            </h1>
            <span className="text-xs font-mono-tech bg-[#151B23] text-[#D5DAE0] border border-[#C7CDD5]/30 px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-[#D6A84F]" /> SCIENTIFIC ARCHIVE
            </span>
          </div>
          <p className="text-xs text-[#A8B0BA] font-sans-ui mt-1">
            Explore 2,000 genuine Galaxy Zoo 2 astronomical survey observations and morphological classifications.
          </p>
        </div>

        {/* View Layout Switcher */}
        <div className="flex items-center gap-2 bg-[#0D1219] p-1.5 rounded-lg border border-[#252D37] self-start font-mono-tech">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
              viewMode === 'grid'
                ? 'bg-[#252D37] text-[#F2F4F7] border border-[#C7CDD5]/50 shadow-sm'
                : 'text-[#717985] hover:text-[#D5DAE0]'
            }`}
          >
            <Grid3X3 className="w-4 h-4" /> GRID
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
              viewMode === 'list'
                ? 'bg-[#252D37] text-[#F2F4F7] border border-[#C7CDD5]/50 shadow-sm'
                : 'text-[#717985] hover:text-[#D5DAE0]'
            }`}
          >
            <List className="w-4 h-4" /> LIST
          </button>
        </div>
      </div>

      {/* Discovery & Multi-Filter Console */}
      <div className="glass-panel p-5 rounded-xl border border-[#252D37] space-y-4 font-mono-tech">
        {/* Main Search Input */}
        <div className="relative font-mono-tech">
          <Search className="w-4 h-4 text-[#717985] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Search by Library ID (e.g. LIB-000042), Asset ID, SDSS ObjID, morphology, or description..."
            className="w-full bg-[#030508] border border-[#252D37] rounded-lg pl-10 pr-4 py-2.5 text-xs text-[#F2F4F7] placeholder-[#717985] focus:outline-none focus:border-[#C7CDD5] transition-all shadow-inner"
          />
        </div>

        {/* Filter Toolbar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-1">
          {/* Morphology Dropdown */}
          <div className="space-y-1 text-[11px]">
            <label className="text-[#717985] block text-[10px] uppercase tracking-wider">Morphology</label>
            <select
              value={morphologyFilter}
              onChange={(e) => {
                setMorphologyFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-[#030508] border border-[#252D37] rounded-md px-2.5 py-1.5 text-[#F2F4F7] focus:outline-none focus:border-[#C7CDD5] cursor-pointer"
            >
              <option value="ALL">All Morphologies (4-Class)</option>
              <option value="SMOOTH">Smooth (Elliptical)</option>
              <option value="EDGE_ON">Edge-on Disk</option>
              <option value="FEATURED_DISK">Featured Disk / Bar</option>
              <option value="SPIRAL">Spiral Arms</option>
            </select>
          </div>

          {/* Priority Level */}
          <div className="space-y-1 text-[11px]">
            <label className="text-[#717985] block text-[10px] uppercase tracking-wider">Triage Priority</label>
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-[#030508] border border-[#252D37] rounded-md px-2.5 py-1.5 text-[#F2F4F7] focus:outline-none focus:border-[#C7CDD5] cursor-pointer"
            >
              <option value="ALL">All Priority Levels</option>
              <option value="HIGH">High Priority Only</option>
              <option value="MEDIUM">Medium Priority Only</option>
              <option value="LOW">Low Priority Only</option>
            </select>
          </div>

          {/* Anomaly Signal Filter */}
          <div className="space-y-1 text-[11px]">
            <label className="text-[#717985] block text-[10px] uppercase tracking-wider">Anomaly Score</label>
            <select
              value={anomalyFilter}
              onChange={(e) => {
                setAnomalyFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-[#030508] border border-[#252D37] rounded-md px-2.5 py-1.5 text-[#F2F4F7] focus:outline-none focus:border-[#C7CDD5] cursor-pointer"
            >
              <option value="ALL">All Anomaly Scores</option>
              <option value="ANOMALOUS">Priority Signal (Score ≥ 0.60)</option>
              <option value="STANDARD">Standard Baseline (Score &lt; 0.60)</option>
            </select>
          </div>

          {/* Confidence Filter */}
          <div className="space-y-1 text-[11px]">
            <label className="text-[#717985] block text-[10px] uppercase tracking-wider">Confidence Level</label>
            <select
              value={confidenceFilter}
              onChange={(e) => {
                setConfidenceFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-[#030508] border border-[#252D37] rounded-md px-2.5 py-1.5 text-[#F2F4F7] focus:outline-none focus:border-[#C7CDD5] cursor-pointer"
            >
              <option value="ALL">All Confidence Levels</option>
              <option value="HIGH">High Confidence (≥ 90%)</option>
              <option value="MED">Moderate (80% – 89%)</option>
              <option value="LOW">Lower (&lt; 80%)</option>
            </select>
          </div>

          {/* Sorting Dropdown */}
          <div className="space-y-1 text-[11px]">
            <label className="text-[#717985] block text-[10px] uppercase tracking-wider">Sort Archive By</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="w-full bg-[#030508] border border-[#252D37] rounded-md px-2.5 py-1.5 text-[#F2F4F7] focus:outline-none focus:border-[#C7CDD5] cursor-pointer"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="priority">Highest Priority Level</option>
              <option value="anomaly">Highest Anomaly Score</option>
              <option value="confidence">Highest Confidence</option>
            </select>
          </div>
        </div>

        {/* Results Counter & Active Filters Summary */}
        <div className="flex flex-wrap items-center justify-between gap-2 pt-2 border-t border-[#252D37] text-xs text-[#A8B0BA]">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-[#8FAFC2]" />
            <span>Showing <strong className="text-white font-mono-tech">{paginatedObservations.length}</strong> of <strong className="text-white font-mono-tech">{totalItems.toLocaleString()}</strong> cataloged observations</span>
          </div>

          {(searchQuery || morphologyFilter !== 'ALL' || priorityFilter !== 'ALL' || confidenceFilter !== 'ALL' || anomalyFilter !== 'ALL') && (
            <button
              onClick={resetFilters}
              className="text-[#8FAFC2] hover:text-white underline cursor-pointer text-xs"
            >
              Reset Filter Criteria
            </button>
          )}
        </div>
      </div>

      {/* Dataset Render Area */}
      {paginatedObservations.length === 0 ? (
        <EmptyState
          title="No Archive Observations Found"
          description="No observations matched your search term or active filter settings in the Galaxy Zoo 2 dataset."
          onReset={resetFilters}
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
          {paginatedObservations.map((obs) => (
            <div
              key={obs.id}
              className="glass-panel glass-panel-hover rounded-xl border border-[#252D37] overflow-hidden flex flex-col justify-between group font-sans-ui"
            >
              {/* Thumbnail Header */}
              <div className="relative aspect-square bg-[#030508] overflow-hidden">
                <img
                  src={obs.image_url}
                  alt={obs.id}
                  loading="lazy"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-90 group-hover:opacity-100"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#030508] via-transparent to-transparent opacity-80" />

                <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5 font-mono-tech">
                  <PriorityBadge priority={obs.priority} />
                  {obs.anomaly_score >= 0.65 && (
                    <span className="text-[9px] bg-[#3A2B15] text-[#D6A84F] border border-[#D6A84F]/40 px-1.5 py-0.5 rounded font-bold">
                      PRIORITY SIGNAL
                    </span>
                  )}
                </div>

                <div className="absolute top-2.5 right-2.5 text-[10px] font-mono-tech bg-[#030508]/90 text-[#D5DAE0] px-2 py-0.5 rounded border border-[#252D37] backdrop-blur-sm">
                  {obs.broad_morphology}
                </div>

                <div className="absolute bottom-2.5 left-2.5 right-2.5 flex justify-between items-end font-mono-tech">
                  <div>
                    <span className="text-xs text-white font-bold block">{obs.id}</span>
                    <span className="text-[10px] text-[#717985] truncate max-w-[140px] block">
                      Asset: {obs.asset_id}
                    </span>
                  </div>
                  <span className="text-[10px] text-[#5FC7A1] bg-[#0E241B] px-1.5 py-0.5 rounded border border-[#5FC7A1]/30">
                    {obs.confidence != null && (obs.object_type === 'Galaxy' || obs.object_type === 'GALAXY')
                      ? `${(obs.confidence * 100).toFixed(0)}% CONF`
                      : 'N/A CONF'}
                  </span>
                </div>
              </div>

              {/* Card Body */}
              <div className="p-3.5 space-y-2.5 flex-1 flex flex-col justify-between">
                <div className="space-y-2 font-mono-tech">
                  {/* Metadata coordinates & GZ2 class */}
                  <div className="flex justify-between items-center text-[10px] text-[#717985] bg-[#030508] px-2 py-1 rounded border border-[#252D37]">
                    <span>RA: {obs.ra.toFixed(2)}°</span>
                    <span>DEC: {obs.dec.toFixed(2)}°</span>
                    <span className="text-[#D5DAE0] font-semibold">{obs.gz2class}</span>
                  </div>

                  {/* Scientific Description */}
                  <p className="text-[11px] font-sans-ui text-[#A8B0BA] line-clamp-2 leading-relaxed">
                    {obs.explanation}
                  </p>
                </div>

                {/* Card Footer Provenance & Actions */}
                <div className="pt-2.5 border-t border-[#252D37] space-y-2 font-mono-tech">
                  <div className="text-[9px] text-[#717985] truncate">
                    Source: {obs.provenance || 'Galaxy Zoo 2 / SDSS DR7'}
                  </div>

                  <div className="flex items-center justify-between gap-1.5">
                    <button
                      onClick={() => setDossierObs(obs)}
                      className="px-2.5 py-1.5 rounded bg-[#15232E] hover:bg-[#252D37] text-[#8FAFC2] hover:text-white text-[11px] font-semibold border border-[#8FAFC2]/40 transition-all flex items-center gap-1 cursor-pointer"
                      title="Open Observation Science Dossier"
                    >
                      <Info className="w-3.5 h-3.5 text-[#8FAFC2]" />
                      KNOW MORE
                    </button>

                    <button
                      onClick={() => onAnalyze(obs)}
                      className="px-3 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] hover:text-white text-[11px] font-semibold border border-[#C7CDD5]/30 transition-all flex items-center gap-1 cursor-pointer"
                    >
                      <Eye className="w-3 h-3" />
                      Explore <ArrowRight className="w-3 h-3" />
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="glass-panel rounded-xl border border-[#252D37] overflow-hidden font-mono-tech">
          <div className="divide-y divide-[#252D37]">
            {paginatedObservations.map((obs) => (
              <div
                key={obs.id}
                className="p-3.5 flex flex-col md:flex-row items-center justify-between gap-4 hover:bg-[#0D1219]/60 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <img
                    src={obs.image_url}
                    alt={obs.id}
                    loading="lazy"
                    className="w-14 h-14 rounded-lg object-cover border border-[#252D37] bg-black shrink-0"
                  />
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{obs.id}</span>
                      <span className="text-xs text-[#717985]">(Asset: {obs.asset_id})</span>
                      <PriorityBadge priority={obs.priority} />
                      <span className="text-xs text-[#D5DAE0] font-semibold">{obs.broad_morphology}</span>
                    </div>
                    <p className="text-xs text-[#A8B0BA] font-sans-ui line-clamp-1 max-w-xl">
                      {obs.explanation}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right text-xs hidden lg:block">
                    <span className="text-[#717985] block text-[10px]">CONFIDENCE</span>
                    <span className="text-[#5FC7A1] font-semibold">
                      {obs.confidence != null && (obs.object_type === 'Galaxy' || obs.object_type === 'GALAXY')
                        ? `${(obs.confidence * 100).toFixed(1)}%`
                        : 'N/A'}
                    </span>
                  </div>

                  <button
                    onClick={() => setDossierObs(obs)}
                    className="px-3 py-1.5 rounded bg-[#15232E] hover:bg-[#252D37] text-[#8FAFC2] text-xs border border-[#8FAFC2]/40 transition-all flex items-center gap-1 cursor-pointer font-semibold"
                  >
                    <Info className="w-3.5 h-3.5 text-[#8FAFC2]" />
                    KNOW MORE
                  </button>

                  <button
                    onClick={() => onAnalyze(obs)}
                    className="px-3 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] font-xs font-semibold border border-[#C7CDD5]/30 transition-all flex items-center gap-1 cursor-pointer"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Explore →
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Pagination Controls for 2,000+ dataset scalability */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center pt-4 border-t border-[#252D37] font-mono-tech text-xs text-[#A8B0BA]">
          <span>
            Page <strong className="text-white">{currentPage}</strong> of <strong className="text-white">{totalPages}</strong> ({totalItems.toLocaleString()} total observations)
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] disabled:opacity-40 border border-[#252D37] transition-all flex items-center gap-1 cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>

            <button
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] disabled:opacity-40 border border-[#252D37] transition-all flex items-center gap-1 cursor-pointer"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Observation Science Dossier Modal */}
      {dossierObs && (
        <ObservationDossierModal
          observation={dossierObs}
          onClose={() => setDossierObs(null)}
          onAskAstra={(obs) => {
            setDossierObs(null);
            setAskAstraObs(obs);
          }}
          onAnalyze={(obs) => {
            setDossierObs(null);
            onAnalyze(obs);
          }}
        />
      )}

      {/* Ask ASTRA Dedicated Target QA Modal */}
      {askAstraObs && (
        <AskAstraModal
          observation={askAstraObs}
          onClose={() => setAskAstraObs(null)}
          onOpenDossier={(obs) => {
            setAskAstraObs(null);
            setDossierObs(obs);
          }}
        />
      )}
    </div>
  );
};

export default ObservationLibraryPage;
