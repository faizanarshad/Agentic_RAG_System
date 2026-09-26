'use client';

import dynamic from 'next/dynamic';

// Workspaces read browser storage during initial render, so they are client-only.
const loading = () => <div className="ws-loading">Loading workspace…</div>;

export const MedicalLoader = dynamic(() => import('./MedicalWorkspace'), { ssr: false, loading });
export const LegalLoader = dynamic(() => import('./LegalSynthesis'), { ssr: false, loading });
export const EngineeringLoader = dynamic(() => import('./EngineeringWorkspace'), { ssr: false, loading });
export const StatusLoader = dynamic(() => import('./StatusPanel'), { ssr: false, loading });
