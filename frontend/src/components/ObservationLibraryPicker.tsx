import React, { useState, useMemo } from 'react';
import type { Observation, BroadMorphology } from '../types';
import libraryData from '../data/observationLibrary.json';
import { Search, Filter, ChevronLeft, ChevronRight, Check } from 'lucide-react';

const LIBRARY_OBSERVATIONS = libraryData as Observation[];
const ITEMS_PER_PAGE = 12;

interface ObservationLibraryPickerProps {
  onSelectObservation: (obs: Observation) => void;
  selectedObservationId?: string | null;
}

export const ObservationLibraryPicker: React.FC<ObservationLibraryPickerProps> = ({
  onSelectObservation,
  selectedObservationId
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [morphologyFilter, setMorphologyFilter] = useState<'ALL' | BroadMorphology>('ALL');
  const [currentPage, setCurrentPage] = useState(1);

  const filteredObservations = useMemo(() => {
    return LIBRARY_OBSERVATIONS.filter((obs) => {
      const q = searchQuery.toLowerCase().trim();
      if (q) {
        const matchesId = obs.id.toLowerCase().includes(q);
        const matchesAsset = String(obs.asset_id).includes(q);
        const matchesObjId = obs.dr7objid.toLowerCase().includes(q);
        const matchesMorph = obs.broad_morphology.toLowerCase().includes(q) || obs.gz2class.toLowerCase().includes(q);
        if (!matchesId && !matchesAsset && !matchesObjId && !matchesMorph) {
          return false;
        }
      }

      if (morphologyFilter !== 'ALL' && obs.broad_morphology !== morphologyFilter) {
        return false;
      }

      return true;
    });
  }, [searchQuery, morphologyFilter]);

  const totalPages = Math.ceil(filteredObservations.length / ITEMS_PER_PAGE) || 1;
  const paginatedObservations = useMemo(() => {
    const start = (currentPage - 1) * ITEMS_PER_PAGE;
    return filteredObservations.slice(start, start + ITEMS_PER_PAGE);
  }, [filteredObservations, currentPage]);

  const handleFilterChange = (filter: 'ALL' | BroadMorphology) => {
    setMorphologyFilter(filter);
    setCurrentPage(1);
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
    setCurrentPage(1);
  };

  return (
    <div className="space-y-4 font-sans-ui selection:bg-[#C7CDD5]/30">
      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-[#0D1219] p-3 rounded-xl border border-[#252D37]">
        {/* Search Input */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-[#717985] absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={handleSearchChange}
            placeholder="Search DR7 ObjID, Asset ID, ID, or Morphology..."
            className="w-full bg-[#030508] border border-[#252D37] focus:border-[#C7CDD5] rounded-lg pl-9 pr-3 py-2 text-xs font-mono-tech text-[#F2F4F7] placeholder-[#717985] focus:outline-none transition-all"
          />
        </div>

        {/* Morphology Filters */}
        <div className="flex items-center gap-1 overflow-x-auto pb-1 sm:pb-0">
          <Filter className="w-3.5 h-3.5 text-[#717985] mr-1 shrink-0" />
          {(['ALL', 'SMOOTH', 'EDGE_ON', 'FEATURED_DISK', 'SPIRAL'] as const).map((m) => (
            <button
              key={m}
              onClick={() => handleFilterChange(m)}
              className={`px-2.5 py-1 rounded text-[10px] font-mono-tech font-bold transition-all cursor-pointer shrink-0 ${
                morphologyFilter === m
                  ? 'bg-[#151B23] text-[#D5DAE0] border border-[#C7CDD5]/40'
                  : 'text-[#717985] hover:text-[#D5DAE0]'
              }`}
            >
              {m === 'FEATURED_DISK' ? 'DISK' : m}
            </button>
          ))}
        </div>
      </div>

      {/* Grid List of Library Targets */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
        {paginatedObservations.map((obs) => {
          const isSelected = selectedObservationId === obs.id;
          return (
            <div
              key={obs.id}
              onClick={() => onSelectObservation(obs)}
              className={`glass-panel p-2.5 rounded-lg border transition-all duration-200 cursor-pointer group flex flex-col justify-between space-y-2 ${
                isSelected
                  ? 'border-[#5FC7A1] bg-[#0E241B]/40 ring-1 ring-[#5FC7A1]/50'
                  : 'border-[#252D37] hover:border-[#C7CDD5]/40 bg-[#070B11]'
              }`}
            >
              <div className="relative aspect-square rounded overflow-hidden bg-black border border-[#252D37]">
                <img
                  src={obs.image_url}
                  alt={obs.id}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
                <span className="absolute top-1.5 left-1.5 font-mono-tech text-[9px] px-1.5 py-0.5 rounded bg-[#030508]/90 text-[#D5DAE0] border border-[#252D37]">
                  {obs.id}
                </span>
                {isSelected && (
                  <span className="absolute top-1.5 right-1.5 p-1 rounded-full bg-[#5FC7A1] text-[#070B11]">
                    <Check className="w-3 h-3 stroke-[3]" />
                  </span>
                )}
              </div>

              <div className="space-y-1 font-mono-tech text-[10px]">
                <div className="flex justify-between items-center text-[#D5DAE0] font-bold">
                  <span>{obs.broad_morphology}</span>
                  <span className="text-[#717985] font-normal">{obs.gz2class}</span>
                </div>
                <div className="flex justify-between text-[#717985] text-[9px]">
                  <span>RA: {obs.ra.toFixed(1)}°</span>
                  <span>DEC: {obs.dec.toFixed(1)}°</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pagination Footer */}
      <div className="flex items-center justify-between border-t border-[#252D37] pt-3 font-mono-tech text-xs text-[#717985]">
        <span>
          Showing {paginatedObservations.length} of {filteredObservations.length} curated GZ2 targets
        </span>

        <div className="flex items-center gap-2">
          <button
            disabled={currentPage <= 1}
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            className="p-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] disabled:opacity-30 disabled:cursor-not-allowed border border-[#252D37] transition-all cursor-pointer"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <span>
            Page {currentPage} / {totalPages}
          </span>
          <button
            disabled={currentPage >= totalPages}
            onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
            className="p-1.5 rounded bg-[#151B23] hover:bg-[#252D37] text-[#D5DAE0] disabled:opacity-30 disabled:cursor-not-allowed border border-[#252D37] transition-all cursor-pointer"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
