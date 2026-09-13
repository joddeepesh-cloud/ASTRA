import type { Observation, SystemTelemetry, CopilotMessage } from '../types';

export const MOCK_TELEMETRY: SystemTelemetry = {
  observations_received: 12481,
  onboard_processed: 11930,
  anomalies_flagged: 127,
  priority_observations: 23,
  downlink_saved_percent: 86.4,
  is_demo: true
};

export const MOCK_OBSERVATIONS: Observation[] = [
  {
    id: "OBS-004271",
    dr7objid: "587738569780428805",
    asset_id: 192410,
    ra: 192.41083,
    dec: 15.164207,
    gz2class: "Ser",
    broad_morphology: "DISK_FEATURE",
    object_type: "Galaxy",
    confidence: 0.917,
    anomaly_score: 0.94,
    ood_score: 0.89,
    priority: "HIGH",
    catalog_status: "NO_MATCH",
    catalog_name: "SDSS DR16 / Simbad Cross-Match Failed",
    observation_time: "2026-09-10T08:14:22Z",
    image_url: "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?auto=format&fit=crop&w=600&q=80",
    split: "test",
    is_demo: true,
    explanation: "High statistical divergence in asymmetric disk light distribution. The optical profile exhibits unexpected non-symmetric tidal structures outside learned GZ2 manifold.",
    morphology_probs: [
      { label: "Spiral Arms", probability: 0.91 },
      { label: "Smooth Elliptical", probability: 0.06 },
      { label: "Disk / Edge-on", probability: 0.03 }
    ]
  },
  {
    id: "OBS-001092",
    dr7objid: "588017703996096547",
    asset_id: 160990,
    ra: 160.99040,
    dec: 11.703790,
    gz2class: "SBb?t",
    broad_morphology: "SPIRAL",
    object_type: "Galaxy",
    confidence: 0.955,
    anomaly_score: 0.78,
    ood_score: 0.72,
    priority: "HIGH",
    catalog_status: "WEAK_MATCH",
    catalog_name: "SDSS J104357.69+114213.6",
    observation_time: "2026-09-10T07:42:01Z",
    image_url: "https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&w=600&q=80",
    split: "val",
    is_demo: true,
    explanation: "Strong central bar structure with tight spiral arm winding. High probability of barred spiral morphology with minor tidal disturbances.",
    morphology_probs: [
      { label: "Barred Spiral", probability: 0.88 },
      { label: "Unbarred Spiral", probability: 0.09 },
      { label: "Smooth", probability: 0.03 }
    ]
  },
  {
    id: "OBS-003819",
    dr7objid: "587735695913320507",
    asset_id: 210802,
    ra: 210.80220,
    dec: 54.348953,
    gz2class: "Ei",
    broad_morphology: "SMOOTH",
    object_type: "Galaxy",
    confidence: 0.962,
    anomaly_score: 0.12,
    ood_score: 0.08,
    priority: "LOW",
    catalog_status: "MATCHED",
    catalog_name: "NGC 5406 Candidate Cluster Member",
    observation_time: "2026-09-10T06:20:15Z",
    image_url: "https://images.unsplash.com/photo-1543722530-d2c3201371e7?auto=format&fit=crop&w=600&q=80",
    split: "train",
    is_demo: true,
    explanation: "Symmetric, completely round elliptical galaxy. High conformity with standard GZ2 smooth morphology baseline.",
    morphology_probs: [
      { label: "Smooth Elliptical", probability: 0.96 },
      { label: "Disk / Feature", probability: 0.03 },
      { label: "Spiral", probability: 0.01 }
    ]
  },
  {
    id: "OBS-005114",
    dr7objid: "587742775634624545",
    asset_id: 185303,
    ra: 185.30342,
    dec: 18.382704,
    gz2class: "SBc(r)",
    broad_morphology: "SPIRAL",
    object_type: "Galaxy",
    confidence: 0.822,
    anomaly_score: 0.88,
    ood_score: 0.85,
    priority: "HIGH",
    catalog_status: "NO_MATCH",
    catalog_name: "Unidentified Ringed Spiral Structure",
    observation_time: "2026-09-10T05:55:40Z",
    image_url: "https://images.unsplash.com/photo-1502134249126-9f3755a50d78?auto=format&fit=crop&w=600&q=80",
    split: "test",
    is_demo: true,
    explanation: "Distinct inner ring structure enclosing central bar. Statistically unusual feature prominence for targeted scientific review.",
    morphology_probs: [
      { label: "Spiral + Inner Ring", probability: 0.82 },
      { label: "Standard Spiral", probability: 0.14 },
      { label: "Irregular", probability: 0.04 }
    ]
  },
  {
    id: "OBS-008912",
    dr7objid: "587732769983889439",
    asset_id: 187366,
    ra: 187.36679,
    dec: 8.749928,
    gz2class: "Sen",
    broad_morphology: "DISK_FEATURE",
    object_type: "Galaxy",
    confidence: 0.735,
    anomaly_score: 0.65,
    ood_score: 0.61,
    priority: "MEDIUM",
    catalog_status: "WEAK_MATCH",
    catalog_name: "VCC 1120 Candidate",
    observation_time: "2026-09-10T04:11:09Z",
    image_url: "https://images.unsplash.com/photo-1451187580459-43490279c0fa?auto=format&fit=crop&w=600&q=80",
    split: "train",
    is_demo: true,
    explanation: "Faint disk feature with edge-on inclination. Intermediate confidence score requiring ground catalog verification.",
    morphology_probs: [
      { label: "Disk / Edge-on", probability: 0.74 },
      { label: "Smooth Elliptical", probability: 0.21 },
      { label: "Spiral", probability: 0.05 }
    ]
  },
  {
    id: "OBS-009401",
    dr7objid: "588015509825716307",
    asset_id: 293833,
    ra: 215.11294,
    dec: -1.042851,
    gz2class: "Merger / Disturbed",
    broad_morphology: "OTHER",
    object_type: "Galaxy",
    confidence: 0.891,
    anomaly_score: 0.97,
    ood_score: 0.95,
    priority: "HIGH",
    catalog_status: "NO_MATCH",
    catalog_name: "Interacting Galaxy System (Uncataloged)",
    observation_time: "2026-09-10T02:08:50Z",
    image_url: "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?auto=format&fit=crop&w=600&q=80",
    split: "test",
    is_demo: true,
    explanation: "Severe tidal disruption indicating ongoing galaxy merger. Exceptionally high OOD score prioritizing immediate Earth-side downlink.",
    morphology_probs: [
      { label: "Merger / Irregular", probability: 0.89 },
      { label: "Spiral Disturbed", probability: 0.08 },
      { label: "Artifact", probability: 0.03 }
    ]
  }
];

export const MOCK_COPILOT_SUGGESTIONS = [
  "Why was OBS-004271 flagged as high priority?",
  "Explain the OOD anomaly score for OBS-009401.",
  "What is the estimated downlink bandwidth savings?",
  "How does ASTRA handle catalog cross-matching?"
];

export const MOCK_COPILOT_INITIAL_MESSAGES: CopilotMessage[] = [
  {
    id: "msg-1",
    sender: "system",
    timestamp: "12:00:00",
    content: "ASTRA Mission Control Copilot initialized. Ready to assist with telemetry interpretation, anomaly diagnostics, and catalog cross-match explanations.",
    is_demo: true
  },
  {
    id: "msg-2",
    sender: "copilot",
    timestamp: "12:00:05",
    content: "Greetings Commander. Currently monitoring 12,481 simulated observations. OBS-004271 is our highest anomaly alert today (Anomaly Score: 0.94). Would you like a breakdown of why onboard triage flagged it?",
    observation_id: "OBS-004271",
    suggested_actions: [
      "Analyze OBS-004271 divergence",
      "Show downlink priority queue",
      "Explain OOD detection method"
    ],
    is_demo: true
  }
];
