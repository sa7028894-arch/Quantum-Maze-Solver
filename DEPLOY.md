# Deploying the Quantum Maze Solver Web App

This is a Flask backend + static frontend. The backend runs real Qiskit
circuits (Aer simulator) on every request; the frontend is plain HTML/JS
that calls it over a JSON API. To get a public URL, deploy the backend
somewhere that runs Python — the options below are all free for this
project's scale.

## Option A: Render (recommended — easiest free option)

1. Push this `webapp/` folder to a GitHub repo (or use a subfolder of your
   existing repo — Render lets you set a "Root Directory").
2. Go to https://render.com -> New -> Web Service -> connect your GitHub repo.
3. Settings:
   - **Root Directory**: `webapp` (if it's a subfolder of a bigger repo)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free
4. Click **Create Web Service**. Render builds and deploys automatically,
   and gives you a URL like `https://your-app.onrender.com`.
5. Every future `git push` redeploys automatically.

Note: Render's free tier spins down after inactivity, so the first request
after idling takes ~30-50s to wake up. Fine for demoing to judges, just
load the page a minute before you present.

## Option B: Railway

1. https://railway.app -> New Project -> Deploy from GitHub repo.
2. Railway auto-detects Python + the `Procfile` and deploys it.
3. Under Settings -> Networking, click "Generate Domain" to get a public URL.

## Option C: PythonAnywhere (good if you want zero cold-start delay)

1. https://www.pythonanywhere.com -> free account -> Bash console.
2. `git clone` your repo, `cd webapp`, `pip install -r requirements.txt --user`.
3. Go to the Web tab -> Add a new web app -> Manual configuration -> Python 3.10+.
4. Point the WSGI config file's `app` import at this `app.py`, set the
   working directory to the `webapp` folder, reload.
5. You get a URL like `https://yourusername.pythonanywhere.com`.

## Running locally first (do this before deploying)

```bash
cd webapp
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000 in your browser. Confirm "New maze" and "Play"
both work before deploying anywhere — it's much easier to debug locally.

## Architecture recap

```
Browser (static/index.html)
   |  fetch('/api/maze')   -> maze layout + BFS path (no quantum work)
   |  fetch('/api/grover') -> runs a real Qiskit Grover circuit on Aer,
   v                          returns round-by-round probabilities + histogram
Flask app (app.py)
   |
   +-- maze.py            (maze generation + classical BFS)
   +-- quantum_solver.py  (Grover oracle, diffuser, Qiskit/Aer execution)
```

The quantum computation happens entirely on the server. The frontend never
runs any quantum simulation itself -- it only renders JSON the backend
already computed with real Qiskit circuits.
