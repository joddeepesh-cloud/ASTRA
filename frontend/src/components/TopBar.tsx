import React, { useEffect, useState, useRef } from 'react';
import { Search, Bell, Satellite, Cpu, WifiOff, CheckCircle2, FileSearch, AlertOctagon, CheckCheck, Inbox, X } from 'lucide-react';
import { getHealth } from '../services/api';
import type { HealthResponse } from '../types/api';
import {
  getReviewEvents,
  getUnreadEventCount,
  markEventsAsRead,
  markSingleEventAsRead,
  REVIEW_EVENT_CUSTOM_TYPE,
  type ReviewEvent
} from '../services/reviewEventsService';

interface TopBarProps {
  title: string;
  subtitle?: string;
  onSearchClick?: () => void;
  onInspectObservationById?: (obsId: string) => void;
}

function formatRelativeTime(isoString: string): string {
  try {
    const now = new Date();
    const date = new Date(isoString);
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diffSec < 60) return 'Just now';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`;
    return date.toLocaleDateString([], { month: 'short', day: 'numeric' });
  } catch {
    return isoString;
  }
}

export const TopBar: React.FC<TopBarProps> = ({
  title,
  subtitle,
  onSearchClick,
  onInspectObservationById
}) => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [healthStatus, setHealthStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  
  // Notification State
  const [unreadCount, setUnreadCount] = useState<number>(() => getUnreadEventCount());
  const [events, setEvents] = useState<ReviewEvent[]>(() => getReviewEvents());
  const [isPopoverOpen, setIsPopoverOpen] = useState<boolean>(false);
  const popoverRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let isMounted = true;
    getHealth()
      .then((data) => {
        if (isMounted) {
          setHealth(data);
          setHealthStatus(data.ml_ready ? 'online' : 'offline');
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealthStatus('offline');
        }
      });
    return () => {
      isMounted = false;
    };
  }, []);

  // Real-time reactive updates from reviewEventsService
  useEffect(() => {
    const syncNotifications = () => {
      setEvents(getReviewEvents());
      setUnreadCount(getUnreadEventCount());
    };

    window.addEventListener(REVIEW_EVENT_CUSTOM_TYPE, syncNotifications);
    return () => {
      window.removeEventListener(REVIEW_EVENT_CUSTOM_TYPE, syncNotifications);
    };
  }, []);

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target as Node)) {
        setIsPopoverOpen(false);
      }
    };
    if (isPopoverOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isPopoverOpen]);

  const handleMarkAllRead = () => {
    markEventsAsRead();
    setEvents(getReviewEvents());
    setUnreadCount(0);
  };

  const handleNotificationClick = (evt: ReviewEvent) => {
    markSingleEventAsRead(evt.id);
    setEvents(getReviewEvents());
    setUnreadCount(getUnreadEventCount());

    if (onInspectObservationById && evt.observationId) {
      onInspectObservationById(evt.observationId);
    }
    setIsPopoverOpen(false);
  };

  return (
    <header className="h-16 bg-[#0B1422]/90 border-b border-[#1B2B3F] px-6 flex items-center justify-between sticky top-0 z-30 backdrop-blur-xl selection:bg-[#8FD3FF]/30">
      <div className="flex items-center gap-4">
        <div>
          <h1 className="text-base md:text-lg font-bold font-mono-tech text-[#E9EEF4] tracking-wider uppercase flex items-center gap-2">
            {title}
          </h1>
          {subtitle && (
            <p className="text-xs text-[#A9B7C7] font-sans-ui">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-4 font-mono-tech">
        {healthStatus === 'online' ? (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#0E241B] border border-[#58BFA7]/40 text-[#58BFA7] text-xs font-mono-tech tracking-wider shadow-sm">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#58BFA7] opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-[#58BFA7]"></span>
            </span>
            <span>ML API ONLINE ({health?.device?.toUpperCase() || 'GPU'})</span>
          </div>
        ) : healthStatus === 'offline' ? (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#3A2B15] border border-[#D6A84F]/40 text-[#D6A84F] text-xs font-mono-tech tracking-wider shadow-sm">
            <WifiOff className="w-3.5 h-3.5 text-[#D6A84F]" />
            <span>LIVE ANALYSIS OFFLINE</span>
          </div>
        ) : (
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#101C2D] border border-[#1B2B3F] text-[#A9B7C7] text-xs font-mono-tech">
            <Cpu className="w-3.5 h-3.5 animate-spin text-[#8FD3FF]" />
            <span>CONNECTING...</span>
          </div>
        )}

        <div className="h-5 w-px bg-[#1B2B3F] hidden md:block" />

        <div className="flex items-center gap-2 relative" ref={popoverRef}>
          <button
            onClick={onSearchClick}
            className="p-2 text-[#A9B7C7] hover:text-[#E9EEF4] hover:bg-[#101C2D] rounded-lg border border-transparent hover:border-[#1B2B3F] transition-all cursor-pointer"
            title="Search Observations"
          >
            <Search className="w-4 h-4 text-[#8FD3FF]" />
          </button>

          {/* Bell Button */}
          <button
            onClick={() => setIsPopoverOpen((prev) => !prev)}
            aria-label={`Notifications (${unreadCount} unread)`}
            className={`p-2 rounded-lg border transition-all relative cursor-pointer ${
              isPopoverOpen
                ? 'bg-[#14243A] border-[#8FD3FF]/40 text-[#E9EEF4]'
                : 'text-[#A9B7C7] hover:text-[#D6A84F] hover:bg-[#101C2D] border-transparent hover:border-[#1B2B3F]'
            }`}
            title="Notification Center"
          >
            <Bell className="w-4 h-4 text-[#8FD3FF]" />
            {/* Display Unread Badge ONLY if unreadCount > 0 */}
            {unreadCount > 0 && (
              <span className="absolute -top-1 -right-1 px-1.5 py-0.5 rounded-full bg-[#D6A84F] text-[#050811] font-mono-tech text-[10px] font-bold leading-none shadow-md flex items-center justify-center min-w-[18px]">
                {unreadCount > 9 ? '9+' : unreadCount}
              </span>
            )}
          </button>

          {/* Notification Popover Panel */}
          {isPopoverOpen && (
            <div className="absolute right-0 top-12 w-80 sm:w-96 glass-panel-elevated rounded-2xl border border-[#1B2B3F] bg-[#0B1422]/98 shadow-2xl z-50 overflow-hidden font-sans-ui animate-in fade-in slide-in-from-top-2">
              {/* Popover Header */}
              <div className="p-4 border-b border-[#1B2B3F] bg-[#08111F]/90 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="w-4 h-4 text-[#D6A84F]" />
                  <h3 className="text-xs font-bold font-mono-tech text-[#E9EEF4] tracking-wider uppercase">
                    NOTIFICATIONS
                  </h3>
                  {unreadCount > 0 && (
                    <span className="text-[10px] font-mono-tech bg-[#3A2B15] text-[#D6A84F] border border-[#D6A84F]/40 px-1.5 py-0.5 rounded font-bold">
                      {unreadCount} UNREAD
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  {unreadCount > 0 && (
                    <button
                      onClick={handleMarkAllRead}
                      className="text-[10px] font-mono-tech text-[#8FD3FF] hover:text-white flex items-center gap-1 transition-colors cursor-pointer font-bold"
                      title="Mark all as read"
                    >
                      <CheckCheck className="w-3 h-3" /> READ ALL
                    </button>
                  )}
                  <button
                    onClick={() => setIsPopoverOpen(false)}
                    className="p-1 text-[#718196] hover:text-[#E9EEF4] rounded transition-colors cursor-pointer"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Notification Events List */}
              <div className="max-h-80 overflow-y-auto divide-y divide-[#1B2B3F]/60">
                {events.length === 0 ? (
                  <div className="p-8 text-center space-y-2">
                    <div className="w-10 h-10 rounded-full bg-[#101C2D] border border-[#1B2B3F] flex items-center justify-center mx-auto text-[#718196]">
                      <Inbox className="w-5 h-5" />
                    </div>
                    <h4 className="text-xs font-mono-tech font-bold text-[#E9EEF4] uppercase tracking-wider">
                      NO NOTIFICATIONS
                    </h4>
                    <p className="text-xs text-[#718196] font-sans-ui max-w-[220px] mx-auto">
                      Nothing requiring your attention right now.
                    </p>
                  </div>
                ) : (
                  events.map((evt) => {
                    const isUnread = !evt.read;
                    return (
                      <div
                        key={evt.id}
                        onClick={() => handleNotificationClick(evt)}
                        className={`p-3.5 transition-all cursor-pointer flex items-start gap-3 relative ${
                          isUnread
                            ? 'bg-[#101C2D]/90 hover:bg-[#14243A]/90 border-l-2 border-[#D6A84F]'
                            : 'hover:bg-[#101C2D]/50 border-l-2 border-transparent'
                        }`}
                      >
                        {/* Event Action Icon */}
                        <div className="shrink-0 mt-0.5">
                          {evt.action === 'APPROVE' ? (
                            <span className="p-1.5 rounded-lg bg-[#0E241B] border border-[#58BFA7]/40 text-[#58BFA7] block">
                              <CheckCircle2 className="w-4 h-4" />
                            </span>
                          ) : evt.action === 'DEEP_ANALYSIS' ? (
                            <span className="p-1.5 rounded-lg bg-[#171B35] border border-[#8FD3FF]/40 text-[#8FD3FF] block">
                              <AlertOctagon className="w-4 h-4" />
                            </span>
                          ) : (
                            <span className="p-1.5 rounded-lg bg-[#3A2B15] border border-[#D6A84F]/40 text-[#D6A84F] block">
                              <FileSearch className="w-4 h-4" />
                            </span>
                          )}
                        </div>

                        {/* Event Content */}
                        <div className="flex-1 space-y-1 min-w-0">
                          <div className="flex items-center justify-between gap-2">
                            <h4 className={`text-xs font-mono-tech font-bold ${isUnread ? 'text-[#E9EEF4]' : 'text-[#A9B7C7]'}`}>
                              {evt.title}
                            </h4>
                            <span className="text-[10px] font-mono-tech text-[#718196] shrink-0">
                              {formatRelativeTime(evt.timestamp)}
                            </span>
                          </div>

                          <p className="text-xs text-[#A9B7C7] font-sans-ui leading-relaxed line-clamp-2">
                            {evt.message}
                          </p>

                          <div className="flex items-center justify-between pt-1">
                            <span className="text-[10px] font-mono-tech text-[#8FD3FF] font-semibold">
                              ID: {evt.observationId}
                            </span>
                            {isUnread && (
                              <span className="w-1.5 h-1.5 rounded-full bg-[#D6A84F]" />
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          )}

          <div className="hidden lg:flex items-center gap-2 px-3 py-1 bg-[#101C2D] rounded border border-[#1B2B3F] text-xs font-mono-tech text-[#D8E0E8]">
            <Satellite className="w-3.5 h-3.5 text-[#8FD3FF]" />
            <span>SAT-ORBIT 01</span>
          </div>
        </div>
      </div>
    </header>
  );
};
