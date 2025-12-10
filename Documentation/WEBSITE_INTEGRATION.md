# Website Integration Instructions

Code analysis shows your frontend (`Website-Sonotheia`) is already set up to make API calls, but needs a slight configuration adjustment to match the currently running backend (`sonotheia-enhanced`).

## 1. Update the Endpoint Path in `Demo.jsx`

Your frontend is currently trying to hit `/api/v2/detect/quick`. The active backend exposes `/api/detect/quick` (v1).

**File:** `frontend/src/components/Demo.jsx`

**Change:**
```javascript
// Line 76: Remove 'v2' from the path
fetch(`${apiBase}/api/detect/quick`, { method: "POST", body: formData }) // WAS: /api/v2/detect/quick
```

## 2. Configure the API Base URL

The `src/config.js` file reads from `import.meta.env.VITE_API_BASE_URL`. You need to set this to your local backend address.

**File:** `frontend/.env` (Create if missing)

**Content:**
```env
VITE_API_BASE_URL=http://localhost:8000
```

## 3. Enable CORS on Backend (Already Done!)

I verified `backend/api/main.py` and it already allows `http://localhost:5173` (Vite's default port):

```python
ALLOWED_ORIGINS = [
    # ...
    "http://localhost:5173", # Website-Sonotheia Vite Dev Server
]
```

## 4. Run the Dev Servers

You will need two terminals running simultaneously:

**Terminal 1 (Backend - sonotheia-enhanced):**
```bash
cd /Volumes/Treehorn/Gits/sonotheia-enhanced
./start_sonotheia.sh
# OR manually:
# source .venv/bin/activate
# uvicorn backend.api.main:app --reload --port 8000
```

**Terminal 2 (Frontend - Website-Sonotheia):**
```bash
cd /Volumes/Treehorn/Gits/Website-Sonotheia-v251120/frontend
npm install  # If not installed yet
npm run dev
```

## 5. (Optional) Full Pipeline Integration

The `Demo.jsx` currently calls `/quick` (Stages 1-3). To use the **Neural Network (RawNet3)** and **AI Ensemble** (Stages 4-6), you should create a toggle or separate button to call the full endpoint:

```javascript
// Full analysis (slower, ~2-5s)
fetch(`${apiBase}/api/detect`, { method: "POST", body: formData })
```
