# MassCube Web Tools

Web utilities for MassCube metabolomics workflows:

- Aligned Feature Table Viewer
- Peak Shape Viewer
- MS/MS Mirror Plot + Cosine Similarity Viewer
- mzML EIC Viewer (requires local Python backend)

## Run locally

```bash
npm install
npm run dev
```

## Build

```bash
npm run build
npm run preview
```

## Start EIC backend (for mzML tool)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## Put the EIC tool online (for all users)

1. Deploy the backend API (recommended: Render)
   - Push this repo to GitHub.
   - In Render, create a Blueprint service from this repo (`render.yaml` is included).
   - After deploy, copy the public backend URL (example: `https://masscube-eic-api.onrender.com`).
2. Set frontend API URL in GitHub
   - In GitHub repo: `Settings -> Secrets and variables -> Actions -> Variables`
   - Add repository variable:
     - Name: `VITE_EIC_API_URL`
     - Value: your backend URL from step 1
3. Redeploy frontend
   - Push to `main` (or re-run the Pages workflow).
   - The website will use the backend URL as default in the mzML EIC Viewer.
4. Restrict CORS in backend (recommended)
   - Set backend env var `EIC_ALLOWED_ORIGINS=https://huaxuyu.github.io`

## Deploy

- Push to `main` to trigger `.github/workflows/deploy.yml`.
- The site is published to GitHub Pages at:
  `https://huaxuyu.github.io/masscube_webtools/`
