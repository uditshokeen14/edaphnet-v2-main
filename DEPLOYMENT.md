# EdaphNet v2: Complete Deployment Guide

This guide covers all deployment options for **EdaphNet v2**, comparing **Streamlit** vs. the **Native Web App**, with step-by-step instructions for 100% free cloud hosting and mobile field deployment.

---

## 1. Streamlit vs. Native Web App: Which Should You Use?

You do **not** have to use Streamlit; both options are now fully implemented and ready to deploy:

| Feature | Option A: Streamlit (`streamlit_app.py`) | Option B: Native Web App (`app/server.py` + `app/web/index.html`) |
|---|---|---|
| **Best For** | Academic presentations, thesis viva, fast sharing with faculty | Real-world farmer/field use, mobile phone camera capture |
| **Hosting** | Streamlit Community Cloud (Free, 1-click), Hugging Face Spaces | Render, Railway, Fly.io, Hugging Face Docker, GCP Cloud Run |
| **Deployment Effort**| **Zero setup** (point to GitHub repo) | 1 click with `render.yaml` or `Dockerfile` |
| **Mobile Experience**| Standard responsive web layout | Built specifically for touch screens with direct camera trigger (`capture="environment"`) |
| **Startup Speed**| ~5–10 seconds (loads Streamlit server) | **Instant (< 1 second)**, zero framework overhead (Python standard library) |
| **Resource Usage** | Moderate (~300 MB RAM) | Minimal (~120 MB RAM) |

> [!TIP]
> **Recommendation:**
> - If you are presenting to your **guide, professor, or conference**, use **Streamlit Community Cloud** (Option 1).
> - If you are conducting **field trials or user testing on phones**, deploy the **Native Web App** on Render or on your local Wi-Fi (Option 2 or Option 4).

---

## 2. Option 1: Deploy on Streamlit Community Cloud (100% Free)

Streamlit Community Cloud gives you a permanent, public HTTPS link (e.g., `https://edaphnet.streamlit.app`) connected to your GitHub repository.

### Steps:
1. **Push your code to GitHub:**
   ```bash
   git add streamlit_app.py requirements-deploy.txt models/
   git commit -m "Add Streamlit app and models"
   git push origin main
   ```
2. **Open Streamlit Cloud:**
   - Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. **New App:**
   - Click **"Create app"** $\rightarrow$ **"I already have an app"**.
   - Select your GitHub repository (`edaphnet-v2`).
   - Set **Main file path** to: `streamlit_app.py`.
   - In **Advanced settings**, set Python version to **3.11**.
4. **Deploy:**
   - Click **Deploy!** Within 2 minutes, your app is live on a public URL with SSL.

---

## 3. Option 2: Deploy on Hugging Face Spaces (100% Free)

Hugging Face Spaces provides free 16 GB RAM CPU instances with automatic HTTPS.

### Steps:
1. Go to [huggingface.co/spaces](https://huggingface.co/spaces) and click **"Create new Space"**.
2. **Choose Space SDK:**
   - Select **Streamlit** (to run `streamlit_app.py`), **OR**
   - Select **Docker** (to run the native web app using the provided `Dockerfile`).
3. Push your repository to the Hugging Face Space git remote.
4. The Space will automatically build the container and provide a persistent public URL.

---

## 4. Option 3: Deploy on Render / Railway (Free Tier PaaS)

Render and Railway can host the lightweight native app or the Streamlit app using the provided `render.yaml` or `Procfile`.

### Render Deployment:
1. Log into [render.com](https://render.com) and link your GitHub account.
2. Click **New +** $\rightarrow$ **Blueprint**.
3. Select your repository. Render will automatically detect [`render.yaml`](render.yaml) and offer both:
   - `edaphnet-field-assistant` (Native Web App on port 8001)
   - `edaphnet-streamlit-dashboard` (Streamlit on port 8501)
4. Click **Apply**. Render builds and deploys your free web service.

---

## 5. Option 4: Local Farm / Wi-Fi Deployment (Mobile Phone Camera)

You can run the app on your laptop and access it from any smartphone connected to the same Wi-Fi router or mobile hotspot, with the camera buttons directly opening the phone's native camera.

1. **Start the server on `0.0.0.0`:**
   ```powershell
   python app/server.py --host 0.0.0.0 --port 8001
   ```
2. **Find your laptop's local IP address:**
   ```powershell
   ipconfig
   # Look for "IPv4 Address", e.g. 192.168.1.15
   ```
3. **Open on your phone:**
   Open Chrome or Safari on your phone and navigate to:
   ```
   http://192.168.1.15:8001
   ```
   *(Replace with your actual laptop IP address. If Windows Firewall prompts, allow Python on private networks).*

---

## 6. Option 5: Docker Container Deployment

A multi-platform production [`Dockerfile`](Dockerfile) is included.

### Build and Run:
```bash
# Build container
docker build -t edaphnet .

# Run Native Web App (port 8001)
docker run -p 8001:8001 edaphnet

# Run Streamlit Dashboard (port 8501)
docker run -p 8501:8501 -e APP_MODE=streamlit -e PORT=8501 edaphnet
```
