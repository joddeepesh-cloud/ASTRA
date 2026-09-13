import React, { useState, useMemo } from 'react';
import type { Observation, BroadMorphology } from '../types';
import libraryData from '../data/observationLibrary.json';
import { PriorityBadge } from '../components/PriorityBadge';
import { EmptyState } from '../components/EmptyState';
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
  Info,
  X,
  Bot
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

  // "Know More" modal state
  const [knowMoreObs, setKnowMoreObs] = useState<Observation | null>(null);

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

      // Confidence Filter
      if (confidenceFilter === 'HIGH' && obs.confidence < 0.90) return false;
      if (confidenceFilter === 'MED' && (obs.confidence < 0.80 || obs.confidence >= 0.90)) return false;
      if (confidenceFilter === 'LOW' && obs.confidence >= 0.80) return false;

      // Anomaly Filter
      if (anomalyFilter === 'ANOMALOUS' && obs.anomaly_score < 0.65) return false;
      if (anomalyFilter === 'STANDARD' && obs.anomaly_score >= 0.65) return false;

      return true;
    });

    // Sorting
    result.sort((a, b) => {
      if (sortBy === 'newest') {
        return new Date(b.observation_time).getTime() - new Date(a.observation_time).getTime();
      }
      if (sortBy === 'oldest') {
        return new Date(a.observation_time).getTime() - new Date(b.observation_time).getTime();
      }
      if (sortBy === 'priority') {
        const pMap: Record<string, number> = { CRITICAL: 4, HIGH: 3, MEDIUM: 2, LOW: 1 };
        return (pMap[b.priority] || 0) - (pMap[a.priority] || 0);
      }
      if (sortBy === 'anomaly') {
        return b.anomaly_score - a.anomaly_score;
      }
      if (sortBy === 'confidence') {
        return b.confidence - a.confidence;
      }
      return 0;
    });

    return result;
  }, [searchQuery, morphologyFilter, priorityFilter, confidenceFilter, anomalyFilter, sortBy]);

  // Pagination logic for scalability
  const totalItems = filteredAndSortedObservations.length;
  const totalPages = Math.ceil(totalItems / itemsPerPage) || 1;
  const paginatedObservations = useMemo(() => {
    const start = (currentPage - 1) * itemsPerPage;
    return filteredAndSortedObservations.slice(start, start + itemsPerPage);
  }, [filteredAndSortedObservations, currentPage, itemsPerPage]);

  const handleResetFilters = () => {
    setSearchQuery('');
    setMorphologyFilter('ALL');
    setPriorityFilter('ALL');
    setConfidenceFilter('ALL');
    setAnomalyFilter('ALL');
    setSortBy('newest');
    setCurrentPage(1);
  };

  return (
    <div className="p-6 md:p-8 space-y-6 max-w-7xl mx-auto">
      {/* Header Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold font-mono text-white tracking-wider">
              OBSERVATION LIBRARY
            </h1>
            <span className="text-xs font-mono bg-cyan-950/80 text-cyan-400 border border-cyan-500/30 px-2.5 py-0.5 rounded-full flex items-center gap-1">
              <Sparkles className="w-3 h-3" /> SCIENTIFIC ARCHIVE
            </span>
          </div>
          <p className="text-xs text-slate-400 font-sans mt-1">
            Explore 2,000 genuine Galaxy Zoo 2 astronomical survey observations and morphological classifications.
          </p>
        </div>

        {/* View Layout Switcher */}
        <div className="flex items-center gap-2 bg-slate-900/90 p-1.5 rounded-lg border border-slate-800 self-start">
          <button
            onClick={() => setViewMode('grid')}
            className={`p-2 rounded font-mono text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
              viewMode === 'grid'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700/60 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Grid3X3 className="w-4 h-4" /> GRID
          </button>
          <button
            onClick={() => setViewMode('list')}
            className={`p-2 rounded font-mono text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
              viewMode === 'list'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700/60 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <List className="w-4 h-4" /> LIST
          </button>
        </div>
      </div>

      {/* Discovery & Multi-Filter Console */}
      <div className="glass-panel p-5 rounded-xl border border-slate-800/80 space-y-4">
        {/* Main Search Input */}
        <div className="relative">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Search by Library ID (e.g. LIB-000042), Asset ID, SDSS ObjID, morphology, or description..."
            className="w-full bg-slate-950/90 border border-slate-800 rounded-lg pl-10 pr-4 py-2.5 text-xs font-mono text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50 transition-all shadow-inner"
          />
        </div>

        {/* Filter Toolbar */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 pt-1">
          {/* Morphology Dropdown */}
          <div className="space-y-1 font-mono text-[11px]">
            <label className="text-slate-400 block text-[10px] uppercase tracking-wider">Morphology</label>
            <select
              value={morphologyFilter}
              onChange={(e) => {
                setMorphologyFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500/50 cursor-pointer"
            >
              <option value="ALL">All Morphologies (4-Class)</option>
              <option value="SMOOTH">Smooth (Elliptical)</option>
              <option value="EDGE_ON">Edge-on Disk</option>
              <option value="FEATURED_DISK">Featured Disk / Bar</option>
              <option value="SPIRAL">Spiral Arms</option>
            </select>
          </div>

          {/* Priority Dropdown */}
          <div className="space-y-1 font-mono text-[11px]">
            <label className="text-slate-400 block text-[10px] uppercase tracking-wider">Priority Level</label>
            <select
              value={priorityFilter}
              onChange={(e) => {
                setPriorityFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500/50 cursor-pointer"
            >
              <option value="ALL">All Priorities</option>
              <option value="HIGH">High Priority</option>
              <option value="MEDIUM">Medium Priority</option>
              <option value="LOW">Low Priority</option>
            </select>
          </div>

          {/* Confidence Dropdown */}
          <div className="space-y-1 font-mono text-[11px]">
            <label className="text-slate-400 block text-[10px] uppercase tracking-wider">Confidence Level</label>
            <select
              value={confidenceFilter}
              onChange={(e) => {
                setConfidenceFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500/50 cursor-pointer"
            >
              <option value="ALL">All Confidences</option>
              <option value="HIGH">High (&ge;90%)</option>
              <option value="MED">Medium (80-90%)</option>
              <option value="LOW">Low (&lt;80%)</option>
            </select>
          </div>

          {/* Anomaly Status Dropdown */}
          <div className="space-y-1 font-mono text-[11px]">
            <label className="text-slate-400 block text-[10px] uppercase tracking-wider">ASTRA Triage Priority</label>
            <select
              value={anomalyFilter}
              onChange={(e) => {
                setAnomalyFilter(e.target.value as any);
                setCurrentPage(1);
              }}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500/50 cursor-pointer"
            >
              <option value="ALL">All Prioritizations</option>
              <option value="ANOMALOUS">Elevated Prioritization (&ge;0.65)</option>
              <option value="STANDARD">Standard Prioritization (&lt;0.65)</option>
            </select>
          </div>

          {/* Sort By Dropdown */}
          <div className="space-y-1 font-mono text-[11px]">
            <label className="text-slate-400 block text-[10px] uppercase tracking-wider">Sort Order</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="w-full bg-slate-950 border border-slate-800 rounded-md px-2.5 py-1.5 text-slate-200 focus:outline-none focus:border-cyan-500/50 cursor-pointer"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="priority">Highest Priority</option>
              <option value="anomaly">Highest Prioritization Signal</option>
              <option value="confidence">Highest Confidence</option>
            </select>
          </div>
        </div>

        {/* Results Bar */}
        <div className="flex flex-col sm:flex-row justify-between items-center text-xs font-mono text-slate-400 pt-3 border-t border-slate-800/60 gap-2">
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-3.5 h-3.5 text-cyan-400" />
            <span>
              Showing <strong className="text-white">{paginatedObservations.length}</strong> of{' '}
              <strong className="text-white">{totalItems}</strong> matching records (Total Archive Size: {LIBRARY_OBSERVATIONS.length})
            </span>
          </div>

          {(searchQuery || morphologyFilter !== 'ALL' || priorityFilter !== 'ALL' || confidenceFilter !== 'ALL' || anomalyFilter !== 'ALL') && (
            <button
              onClick={handleResetFilters}
              className="text-cyan-400 hover:text-cyan-300 underline cursor-pointer text-xs"
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Library Grid or List */}
      {paginatedObservations.length === 0 ? (
        <EmptyState
          title="No Archive Match Found"
          description="Try broadening your search term or clearing multi-filter constraints."
          onReset={handleResetFilters}
        />
      ) : viewMode === 'grid' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
          {paginatedObservations.map((obs) => (
            <div
              key={obs.id}
              className="glass-panel glass-panel-hover rounded-xl border border-slate-800/90 overflow-hidden flex flex-col justify-between group transition-all"
            >
              {/* Image Banner */}
              <div className="relative aspect-square bg-black overflow-hidden">
                <img
                  src={obs.image_url}
                  alt={obs.id}
                  loading="lazy"
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 opacity-90 group-hover:opacity-100"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-transparent opacity-80" />
                
                <div className="absolute top-2.5 left-2.5 flex items-center gap-1.5">
                  <PriorityBadge priority={obs.priority} />
                  {obs.anomaly_score >= 0.65 && (
                    <span className="text-[9px] font-mono bg-amber-950/90 text-amber-300 border border-amber-800/80 px-1.5 py-0.5 rounded font-bold">
                      PRIORITY SIGNAL
                    </span>
                  )}
                </div>

                <div className="absolute top-2.5 right-2.5 text-[10px] font-mono bg-slate-950/80 text-cyan-300 px-2 py-0.5 rounded border border-cyan-900/50 backdrop-blur-sm">
                  {obs.broad_morphology}
                </div>

                <div className="absolute bottom-2.5 left-2.5 right-2.5 flex justify-between items-end">
                  <div>
                    <span className="text-xs font-mono text-white font-bold block">{obs.id}</span>
                    <span className="text-[10px] font-mono text-slate-400 truncate max-w-[140px] block">
                      Asset: {obs.asset_id}
                    </span>
                  </div>
                  <span className="text-[10px] font-mono text-emerald-400 bg-slate-900/80 px-1.5 py-0.5 rounded">
                    {(obs.confidence * 100).toFixed(0)}% CONF
                  </span>
                </div>
              </div>

              {/* Card Body */}
              <div className="p-3.5 space-y-2.5 flex-1 flex flex-col justify-between">
                <div className="space-y-2">
                  {/* Metadata coordinates & GZ2 class */}
                  <div className="flex justify-between items-center text-[10px] font-mono text-slate-400 bg-slate-950/60 px-2 py-1 rounded border border-slate-900">
                    <span>RA: {obs.ra.toFixed(2)}°</span>
                    <span>DEC: {obs.dec.toFixed(2)}°</span>
                    <span className="text-cyan-400 font-semibold">{obs.gz2class}</span>
                  </div>

                  {/* Scientific Description */}
                  <p className="text-[11px] font-sans text-slate-300 line-clamp-2 leading-relaxed">
                    {obs.explanation}
                  </p>
                </div>

                {/* Card Footer Provenance & Actions */}
                <div className="pt-2.5 border-t border-slate-800/70 space-y-2">
                  <div className="text-[9px] font-mono text-slate-500 truncate">
                    Source: {obs.provenance || 'Galaxy Zoo 2 / SDSS DR7'}
                  </div>

                  <div className="flex items-center justify-between gap-1.5">
                    <button
                      onClick={() => setKnowMoreObs(obs)}
                      className="px-2.5 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 hover:text-white font-mono text-[11px] font-medium border border-slate-700/60 transition-all flex items-center gap-1 cursor-pointer"
                      title="Information & AI context preview"
                    >
                      <Info className="w-3 h-3 text-indigo-400" />
                      Know More
                    </button>

                    <button
                      onClick={() => onAnalyze(obs)}
                      className="px-3 py-1.5 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 hover:text-white font-mono text-[11px] font-semibold border border-cyan-800/60 transition-all flex items-center gap-1 cursor-pointer"
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
        <div className="glass-panel rounded-xl border border-slate-800/80 overflow-hidden">
          <div className="divide-y divide-slate-800/80">
            {paginatedObservations.map((obs) => (
              <div
                key={obs.id}
                className="p-3.5 flex flex-col md:flex-row items-center justify-between gap-4 hover:bg-slate-900/50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <img
                    src={obs.image_url}
                    alt={obs.id}
                    loading="lazy"
                    className="w-14 h-14 rounded-lg object-cover border border-cyan-900/40 bg-black shrink-0"
                  />
                  <div className="space-y-1 font-mono">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-bold text-white">{obs.id}</span>
                      <span className="text-xs text-slate-400">(Asset: {obs.asset_id})</span>
                      <PriorityBadge priority={obs.priority} />
                      <span className="text-xs text-cyan-400 font-semibold">{obs.broad_morphology}</span>
                    </div>
                    <p className="text-xs text-slate-400 font-sans line-clamp-1 max-w-xl">
                      {obs.explanation}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <div className="text-right font-mono text-xs hidden lg:block">
                    <span className="text-slate-500 block text-[10px]">CONFIDENCE</span>
                    <span className="text-emerald-400 font-semibold">{(obs.confidence * 100).toFixed(1)}%</span>
                  </div>

                  <button
                    onClick={() => setKnowMoreObs(obs)}
                    className="px-3 py-1.5 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-xs border border-slate-700/60 transition-all flex items-center gap-1 cursor-pointer"
                  >
                    <Info className="w-3.5 h-3.5 text-indigo-400" />
                    Know More
                  </button>

                  <button
                    onClick={() => onAnalyze(obs)}
                    className="px-3 py-1.5 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 font-mono text-xs font-semibold border border-cyan-800/60 transition-all flex items-center gap-1 cursor-pointer"
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
        <div className="flex justify-between items-center pt-4 border-t border-slate-800/80 font-mono text-xs text-slate-400">
          <span>
            Page <strong className="text-white">{currentPage}</strong> of <strong className="text-white">{totalPages}</strong> ({totalItems} records)
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setCurrentPage((p) => Math.max(p - 1, 1));
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              disabled={currentPage === 1}
              className="px-3 py-1.5 rounded bg-slate-900 border border-slate-800 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 text-slate-200 transition-all flex items-center gap-1 cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" /> Previous
            </button>
            <button
              onClick={() => {
                setCurrentPage((p) => Math.min(p + 1, totalPages));
                window.scrollTo({ top: 0, behavior: 'smooth' });
              }}
              disabled={currentPage === totalPages}
              className="px-3 py-1.5 rounded bg-slate-900 border border-slate-800 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-800 text-slate-200 transition-all flex items-center gap-1 cursor-pointer"
            >
              Next <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Know More Modal (Honest Space Help AI Placeholder with real observation parameters) */}
      {knowMoreObs && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-950 border border-cyan-800/60 rounded-xl max-w-lg w-full p-6 space-y-5 shadow-2xl relative">
            <button
              onClick={() => setKnowMoreObs(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-900 cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-3 border-b border-slate-800 pb-4">
              <div className="w-10 h-10 rounded-lg bg-indigo-950 border border-indigo-500/40 flex items-center justify-center text-indigo-400">
                <Bot className="w-6 h-6" />
              </div>
              <div>
                <h3 className="text-base font-bold font-mono text-white">Space Help AI</h3>
                <span className="text-[10px] font-mono text-cyan-400">TARGET: {knowMoreObs.id} (Asset {knowMoreObs.asset_id})</span>
              </div>
            </div>

            <div className="space-y-3 font-sans">
              <div className="p-3 bg-indigo-950/40 border border-indigo-500/30 rounded-lg flex items-start gap-2.5 text-xs text-indigo-300">
                <Info className="w-4 h-4 shrink-0 text-indigo-400 mt-0.5" />
                <div>
                  <strong className="block font-mono text-indigo-200">Space Help AI coming in next feature</strong>
                  The astronomy-specific AI Assistant for deep morphological breakdown and literature synthesis will be activated in the upcoming release.
                </div>
              </div>

              {/* Factual GZ2 Scientific Parameters */}
              <div className="bg-slate-900/60 p-3 rounded-lg border border-slate-800 text-xs space-y-2 font-mono">
                <div className="flex justify-between text-slate-400 border-b border-slate-800/60 pb-1">
                  <span>Observation ID:</span>
                  <span className="text-white font-bold">{knowMoreObs.id}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>SDSS ObjID:</span>
                  <span className="text-slate-300">{knowMoreObs.dr7objid}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Target Morphology:</span>
                  <span className="text-cyan-400 font-bold">{knowMoreObs.broad_morphology}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>GZ2 Taxonomy:</span>
                  <span className="text-slate-300">{knowMoreObs.gz2class}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Classification Confidence:</span>
                  <span className="text-emerald-400 font-semibold">{(knowMoreObs.confidence * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Coordinates:</span>
                  <span className="text-slate-300">RA {knowMoreObs.ra.toFixed(2)}°, DEC {knowMoreObs.dec.toFixed(2)}°</span>
                </div>
                <div className="flex justify-between text-slate-400 border-t border-slate-800/60 pt-1">
                  <span>Survey Provenance:</span>
                  <span className="text-indigo-300">{knowMoreObs.provenance || 'Galaxy Zoo 2 / SDSS DR7'}</span>
                </div>
              </div>

              <p className="text-xs text-slate-400">
                You can currently inspect full scientific parameters, raw morphology probability distributions, and triage metrics on the detail view.
              </p>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setKnowMoreObs(null)}
                className="px-4 py-2 rounded bg-slate-900 hover:bg-slate-800 text-slate-300 font-mono text-xs cursor-pointer border border-slate-800"
              >
                Close
              </button>
              <button
                onClick={() => {
                  const target = knowMoreObs;
                  setKnowMoreObs(null);
                  onAnalyze(target);
                }}
                className="px-4 py-2 rounded bg-cyan-950 hover:bg-cyan-900 text-cyan-300 font-mono text-xs font-semibold border border-cyan-700/60 flex items-center gap-1.5 cursor-pointer"
              >
                <Eye className="w-3.5 h-3.5" /> View Analysis →
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
