# ⚓ Glimmora Aegis Navy Backend: Render Deployment Guide

This guide details how to configure and deploy the **Glimmora Aegis Navy Backend** on [Render](https://render.com).

We have fully refactored the deployment configs, resolved schema bugs in the original blueprint, and added zero-touch startup capabilities. You can now deploy the entire platform seamlessly using one of two methods:

1. **Option A: Paid Self-Hosted Blueprint (`render.yaml`)** — Deploys all services (API, Postgres, Redis, Qdrant, MinIO) directly in your Render cluster using Render's managed instances.
2. **Option B: 100% Free-Tier Blueprint (`render.free.yaml`)** — Deploys the FastAPI application and PostgreSQL database on Render's Free tiers, and routes cache/storage/vectors to free-tier SaaS providers (Upstash, Qdrant Cloud, Cloudflare R2).

---

## 🛠️ Key Upgrades Made

To make the backend ready for Render, we implemented several advanced production features:
* **Zero-Touch DB Provisioning & Seeding:** Added an `AUTO_SEED=true` environment handler to `app/main.py`. Upon successful boot on Render, the backend automatically builds the PostgreSQL schema and seeds it with default users (Trainees, Admins, Instructors), naval scenarios, and doctrine manuals.
* **Blueprint Validation Fixes:** Cleaned up the invalid `runtime: docker` properties, replaced them with correct `env: docker` schemas, and added `healthCheckPath: /health` for zero-downtime routing.
* **Secured API Integrations:** Prompts the user dynamically for Google Gemini and OpenAI secret keys during the deployment phase without exposing keys in Git.

---

## 🚀 Option A: Paid Self-Hosted Blueprint (`render.yaml`)
Use this if you want all services private, managed, and hosted inside Render without external sign-ups.

### 💰 Cost Breakdown
* **FastAPI Web Service:** Free Tier (shuts down when idle) or Starter ($7/mo)
* **PostgreSQL Database:** Free Tier (expires in 90 days)
* **Redis Cache:** Micro Tier ($7/mo — Render does not offer Free Redis)
* **Qdrant Vector Database:** Private Service Starter + 1GB Disk ($7/mo)
* **MinIO Object Storage:** Private Service Starter + 1GB Disk ($7/mo)
* **Total Estimated Cost:** **$21.00 / month**

### 📋 Setup Steps
1. Push your updated backend code to your GitHub or GitLab repository.
2. Go to the **[Render Dashboard](https://dashboard.render.com)**.
3. Click **New +** and select **Blueprint**.
4. Connect your Git repository containing the backend code.
5. Render will automatically detect the `render.yaml` file.
6. Provide the following inputs when prompted:
   * **GOOGLE_API_KEY**: Your Google Gemini API Key.
   * **OPENAI_API_KEY**: Your OpenAI API Key (optional, can be empty).
   * **CORS_ORIGINS**: Leave as `["*"]` or update with your frontend domain.
7. Click **Apply**. Render will orchestrate and deploy all 5 services!

---

## 💸 Option B: 100% Free-Tier Blueprint (`render.free.yaml`)
**Highly Recommended for Staging/Hobby Use.** Runs the core API and PostgreSQL on Render's 100% Free tier, and connects to dedicated external SaaS free tiers for auxiliary services.

### 🧩 Recommended Free Services
* **Caching:** Sign up for a free serverless Redis database at [Upstash](https://upstash.com) (provides 10,000 commands/day for free).
* **Vector DB:** Sign up for a free cluster at [Qdrant Cloud](https://cloud.qdrant.io) (provides a perpetual free 1GB cluster).
* **Object Storage:** Use [Cloudflare R2](https://www.cloudflare.com/developer-platform/products/r2/) (provides 10GB free storage, fully S3 compatible).

### 📋 Setup Steps
1. Push your updated backend code to your GitHub/GitLab repository.
2. Go to the **[Render Dashboard](https://dashboard.render.com)**.
3. Click **New +** and select **Blueprint**.
4. Connect your Git repository.
5. In the **Blueprint Config File Path** setting, change `render.yaml` to:
   ```text
   render.free.yaml
   ```
6. Render will read the free tier setup and prompt you for:
   * **GOOGLE_API_KEY**: Your Gemini key.
   * **REDIS_URL**: The connection string from Upstash (`redis://...`).
   * **QDRANT_HOST**: Your Qdrant Cloud cluster endpoint hostname (e.g. `xxxx.gcp.qdrant.tech`).
   * **MINIO_ENDPOINT**: Cloudflare R2 endpoint or AWS S3 endpoint.
   * **MINIO_ACCESS_KEY** / **SECRET_KEY**: Credentials for R2/S3.
7. Click **Apply**. Your app deploys completely for free!

---

## ⚡ Post-Deployment Verification

Once Render displays **`Deploy Live ✅`**:
1. Visit your public web service URL (e.g. `https://aegis-api.onrender.com/health`).
2. You should receive a healthy status response:
   ```json
   {
     "status": "ok",
     "service": "aegis-api"
   }
   ```
3. Visit `https://aegis-api.onrender.com/docs` to verify that the Interactive OpenAPI documentation loads successfully.

---

## 🖥️ Frontend Integration

To connect the Next.js frontend (`GLIMMORA-Aegis----Navy-Frontend`) to your deployed Render backend:

1. Open your frontend's environment configuration file (e.g., [.env.local](file:///d:/Glimmora/Navy/GLIMMORA-Aegis----Navy-Frontend/.env.local)).
2. Update the environment variables to point to your new Render service:
   ```env
   # Replace aegis-api.onrender.com with your actual Render URL
   NEXT_PUBLIC_API_BASE_URL=https://aegis-api.onrender.com
   NEXT_PUBLIC_WS_BASE_URL=wss://aegis-api.onrender.com
   ```
   > [!NOTE]
   > Ensure that the WebSocket protocol is updated from `ws://` to `wss://` to enable secure SSL connections, which Render manages automatically!

3. Restart your frontend server, and you will be completely connected to your cloud-deployed sovereign Navy training backend!
