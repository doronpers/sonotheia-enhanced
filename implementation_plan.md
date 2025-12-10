# Implementation Plan - Integrate Demo Features

## Goal
Integrate the "Compliance Hero" (PDF SAR Generation) and "Forensic Viewer" (Spectrogram Analysis) features from the demo scripts into the core Sonotheia Enhanced platform.

## Proposed Changes

### Backend
1.  **Dependencies**:
    *   Add `fpdf2` to `backend/requirements.txt`.
2.  **SAR Module (Compliance Hero)**:
    *   Create `backend/sar/pdf_generator.py` adapting the logic from `demo/compliance_hero.py` to be a reusable class.
    *   Update `backend/sar/generator.py` to optionally trigger PDF generation.
    *   Update `backend/api/main.py` to include:
        *   `POST /api/sar/{id}/generate-pdf`: Trigger manual PDF generation.
        *   `GET /api/sar/{id}/pdf`: Download the generated PDF.
3.  **Forensics Module**:
    *   Create `backend/static/forensics/` directory.
    *   Move `demo/artifact_sample.wav` and `demo/artifact_metadata.json` to this directory.
    *   Update `backend/api/main.py` to mount `StaticFiles` at `/api/static`.

### Frontend
1.  **Forensic Viewer Component**:
    *   Create `frontend/src/components/ForensicViewer.jsx`.
    *   Port the Web Audio API + Canvas logic from `demo/forensic_viewer.html` into a React component using `useRef` and `useEffect`.
    *   Accept `audioUrl` and `metadataUrl` as props.
2.  **Integration**:
    *   Update `frontend/src/App.js` to include a route `/forensics` for the viewer.
    *   (Optional) Embed `ForensicViewer` into `Laboratory.jsx` or a new "Forensics" tab in the Dashboard.

## Verification Plan

### Automated Tests
*   **Backend**: 
    *   Run `pip install -r backend/requirements.txt`.
    *   Test endpoint `GET /api/static/forensics/artifact_sample.wav` returns 200.
    *   Trigger `POST /api/sar/{mock_id}/generate-pdf` and verify PDF file creation.

### Manual Verification
*   **Frontend**:
    *   Start the frontend (`npm start`).
    *   Navigate to `localhost:3000/forensics`.
    *   Verify the spectrogram renders, audio plays, and "Red Box" artifacts appear correctly.
