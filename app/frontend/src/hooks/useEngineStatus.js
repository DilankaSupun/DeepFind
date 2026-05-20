/**
 * DeepFind — useEngineStatus Hook
 *
 * Polls the FastAPI /health endpoint and returns live engine status.
 *
 * Usage:
 *   const { status, version, lastChecked } = useEngineStatus();
 *
 * Returns:
 *   status      — 'checking' | 'online' | 'offline'
 *   version     — string like "0.1.0" when online, null otherwise
 *   lastChecked — Date object of last successful or failed check
 *
 * Behavior:
 *   - Runs an initial check immediately when the component mounts
 *   - Polls every POLL_INTERVAL_MS (15 seconds) in the background
 *   - Never throws — all errors are caught and set status to 'offline'
 *   - Cleans up the interval when the component unmounts
 */

import { useState, useEffect, useCallback } from 'react';
import { checkHealth } from '../services/api.js';

/** How often to re-check engine status (milliseconds) */
const POLL_INTERVAL_MS = 15_000;

export function useEngineStatus() {
  const [status, setStatus]           = useState('checking');  // 'checking' | 'online' | 'offline'
  const [version, setVersion]         = useState(null);
  const [lastChecked, setLastChecked] = useState(null);

  const check = useCallback(async () => {
    try {
      const data = await checkHealth();
      setStatus('online');
      setVersion(data.version ?? null);
    } catch {
      // Backend unreachable or returned an error — do not crash
      setStatus('offline');
      setVersion(null);
    } finally {
      setLastChecked(new Date());
    }
  }, []);

  useEffect(() => {
    // Check immediately on mount
    check();

    // Then poll on a fixed interval
    const interval = setInterval(check, POLL_INTERVAL_MS);

    // Clean up on unmount
    return () => clearInterval(interval);
  }, [check]);

  return { status, version, lastChecked };
}
