# Render Deployment Guide for HR Tech Platform

Complete step-by-step guide to deploy your HR Tech Platform on Render.

---

## Why Render?

✅ **Advantages:**
- Simple & beginner-friendly
- GitHub integration (auto-deploy on push)
- Free tier available
- Automatic SSL/TLS
- PostgreSQL & Redis included
- Easy scaling
- No credit card required for free tier
- Great dashboard & monitoring

---

## Prerequisites

- [ ] GitHub account (your project is already there!)
- [ ] Render account (free at https://render.com)
- [ ] Project pushed to GitHub (already done ✓)

---

## Pricing

| Service | Free Tier | Paid Tier |
|---------|-----------|-----------|
| Web Service | 0.5 CPU, 512MB RAM | $7-12+/month |
| PostgreSQL | 1GB storage (expires in 90 days) | $15+/month |
| Redis | Paid only | $15+/month |
| **Total** | Free (temporary) | $37-40+/month |

---

## Step-by-Step Deployment

### **Step 1: Create Render Account**

1. Go to https://render.com
2. Click "Sign up"
3. Choose "GitHub" or email
4. Verify email (if using email)
5. You'll land on the dashboard

---

### **Step 2: Create PostgreSQL Database**

1. From Render dashboard, click **"New +"** → **"PostgreSQL"**
2. Fill in details:
   - **Name:** `hrtech-db`
   - **Database:** `hrtech_db`
   - **User:** `hrtech_user`
   - **Region:** Choose closest to your location
   - **Plan:** Start with "Free" tier (can upgrade later)
3. Click **"Create Database"**
4. Wait 1-2 minutes for database to be ready
5. **Copy the Internal Database URL** (you'll need this)
   - Format: `postgresql://user:password@host:5432/database`

---

### **Step 3: Create Redis Cache** (Optional but Recommended)

1. Click **"New +"** → **"Redis"**
2. Fill in details:
   - **Name:** `hrtech-redis`
   - **Region:** Same as database
   - **Plan:** Start with paid tier (no free option)
3. Click **"Create Redis"**
4. **Copy the Redis URL** (format: `redis://...`)

---

### **Step 4: Create Web Service for Backend**

1. Click **"New +"** → **"Web Service"**
2. Select **"Build and deploy from a Git repository"**
3. Click **"Connect account"** → Connect your GitHub
4. Find your repository: `hrtech-platform`
5. Click **"Connect"**

**Configure the service:**
- **Name:** `hrtech-backend`
- **Environment:** `Docker`
- **Plan:** Start with "Starter" ($7/month) or free tier
- **Region:** Same as database
- **Branch:** `main`
- **Dockerfile path:** `backend/Dockerfile`

**Add Environment Variables:**
Click **"Environment"** tab and add:

```
DATABASE_URL=postgresql://hrtech_user:PASSWORD@hostname:5432/hrtech_db
REDIS_URL=redis://...
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
ENVIRONMENT=production
DEBUG=false
SPACY_MODEL=en_core_web_sm
SBERT_MODEL=all-MiniLM-L6-v2
```

**Replace with your actual values from Steps 2-3**

**Configure start command:**
- Keep default or use: `gunicorn -w 4 -b 0.0.0.0:8000 backend.app.main:app`

Click **"Create Web Service"**

Wait 5-10 minutes for deployment.

---

### **Step 5: Create Web Service for Frontend**

1. Click **"New +"** → **"Web Service"**
2. Select **"Build and deploy from a Git repository"**
3. Find your repository again: `hrtech-platform`
4. Click **"Connect"**

**Configure the service:**
- **Name:** `hrtech-frontend`
- **Environment:** `Python 3`
- **Plan:** Free tier (if available) or Starter
- **Region:** Same as backend
- **Branch:** `main`
- **Build command:** `pip install -r requirements.txt`
- **Start command:** `python flask_gateway.py`

**Add Environment Variables:**
```
API_BACKEND_URL=http://hrtech-backend:8000
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

Replace `hrtech-backend` with your actual backend service URL (visible after deployment).

Click **"Create Web Service"**

Wait 5-10 minutes for deployment.

---

### **Step 6: Update Configuration**

Once both services are deployed:

1. **Get Backend URL:** From Render dashboard → `hrtech-backend` → Copy the URL (e.g., `https://hrtech-backend.onrender.com`)

2. **Update Frontend Environment:**
   - Go to `hrtech-frontend` → Environment
   - Update `API_BACKEND_URL` to your backend URL
   - Click **"Save"**
   - Service will auto-redeploy

3. **Test the application:**
   - Go to your frontend URL (e.g., `https://hrtech-frontend.onrender.com`)
   - Upload a test resume
   - Create a test job
   - Run ranking

---

## Database Management

### **Connect to Database from CLI**

```bash
# Install psql if needed
# Windows: Download from https://www.postgresql.org/download/windows/
# Mac: brew install postgresql
# Linux: sudo apt install postgresql-client

# Connect to your database
psql "postgresql://hrtech_user:PASSWORD@hostname:5432/hrtech_db"
```

### **View Database URL**

From Render dashboard:
1. Click your PostgreSQL database
2. Scroll to **"Connections"**
3. Find **"Internal Database URL"** (for services on Render)
4. Or **"External Database URL"** (for external connections)

---

## Git-Based Auto-Deployment

Your project is now configured for **auto-deployment**:

1. Make code changes locally
2. Commit and push to GitHub
3. Render automatically detects changes
4. Services auto-deploy within 2-5 minutes

**To disable auto-deploy:**
- Go to service settings → uncheck "Auto-Deploy"

---

## Monitoring & Logs

### **View Live Logs:**
1. From Render dashboard
2. Click your service
3. Click **"Logs"** tab
4. See real-time logs

### **View Metrics:**
1. Click your service
2. Click **"Metrics"** tab
3. Monitor CPU, memory, requests

### **Alerts:**
Render automatically notifies you of:
- Service crashes
- Deployment failures
- High resource usage

---

## SSL/TLS Certificate

✅ **Automatic!**
Render provides free SSL certificates for all services.

Your URLs will be:
- Frontend: `https://hrtech-frontend.onrender.com`
- Backend: `https://hrtech-backend.onrender.com`
- API: `https://hrtech-backend.onrender.com/docs`

---

## Scaling & Upgrades

### **Upgrade Services:**
1. Go to service settings
2. Click **"Plan"**
3. Choose higher tier
4. Click **"Upgrade"**

Service automatically scales (no downtime).

### **Upgrade Database:**
1. Go to database
2. Click **"Settings"**
3. Increase storage/compute
4. Click **"Upgrade"**

---

## Database Backups

### **Automatic Backups:**
Render automatically backs up PostgreSQL daily.

### **Manual Backup:**
```bash
# Export database
pg_dump "postgresql://user:pass@host:5432/db" > backup.sql

# Import database
psql "postgresql://user:pass@host:5432/db" < backup.sql
```

---

## Custom Domain

### **Add Your Domain:**

1. Go to service settings
2. Click **"Custom Domain"**
3. Enter your domain (e.g., `hrtech.yourdomain.com`)
4. Follow DNS configuration steps
5. DNS usually updates in 5-30 minutes

**Example DNS Setup (for Route 53, Cloudflare, etc.):**
```
Type: CNAME
Name: hrtech
Value: hrtech-frontend.onrender.com
```

---

## Environment Variables

### **Where to Set:**

1. Service dashboard
2. Click **"Environment"**
3. Add/edit variables
4. Click **"Save"**
5. Service auto-redeploys

### **Important Variables:**

```env
# Database (from Step 2)
DATABASE_URL=postgresql://hrtech_user:password@host:5432/hrtech_db

# Redis (from Step 3)
REDIS_URL=redis://...

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
API_BACKEND_URL=https://hrtech-backend.onrender.com

# Environment
ENVIRONMENT=production
DEBUG=false

# ML Models
SPACY_MODEL=en_core_web_sm
SBERT_MODEL=all-MiniLM-L6-v2
```

---

## Troubleshooting

### **Service won't deploy?**

Check logs:
1. Go to service
2. Click **"Logs"**
3. Look for error messages

**Common issues:**
- Wrong Python version
- Missing dependencies
- Environment variables not set
- Port conflict

### **Can't connect to database?**

```bash
# Test connection
psql "postgresql://user:pass@host:5432/db" -c "SELECT 1;"
```

**Common issues:**
- Wrong DATABASE_URL format
- Database not ready yet (wait 2-3 min)
- Firewall blocking connection

### **Frontend can't reach backend?**

1. Verify backend is running (check logs)
2. Update `API_BACKEND_URL` in frontend environment
3. Check CORS settings in backend
4. Service redeploys after env update

### **Redis connection issues?**

```bash
# Test Redis connection
redis-cli -u "redis://..." ping
```

---

## Performance Optimization

### **On Free Tier:**
- May experience cold starts (5-10 sec first request)
- Limited to 0.5 CPU cores
- Best for: Testing, small production loads

### **Upgrade to Starter ($7/month):**
- Always-on, no cold starts
- Better performance
- Recommended for: Small to medium production

### **Recommended Setup:**
- **Frontend:** Starter tier ($7/month)
- **Backend:** Starter tier ($7/month)
- **PostgreSQL:** Starter tier ($15/month)
- **Redis:** Starter tier ($15/month)
- **Total:** ~$44/month

---

## Cost Estimation

| Service | Tier | Cost |
|---------|------|------|
| Frontend | Starter | $7/month |
| Backend | Starter | $7/month |
| PostgreSQL | Starter | $15/month |
| Redis | Starter | $15/month |
| **Total** | | **$44/month** |

**Free Option (For Testing):**
- 2 free web services (limited resources)
- Free PostgreSQL (expires in 90 days)
- Total: Free for 90 days, then $15/month for DB

---

## Deployment Checklist

- [ ] GitHub account connected
- [ ] Render account created
- [ ] PostgreSQL database created
- [ ] Redis cache created
- [ ] Backend service deployed
- [ ] Frontend service deployed
- [ ] Environment variables configured
- [ ] API backend URL updated in frontend
- [ ] Services tested (upload resume, rank candidates)
- [ ] Logs checked for errors
- [ ] Custom domain added (optional)
- [ ] Backups configured

---

## Useful Commands

### **SSH into Service (if needed):**
```bash
# From Render dashboard → Shell
# SSH access available for Starter+ plans
```

### **View Service Info:**
From Render dashboard, each service shows:
- Status
- Memory/CPU usage
- Deployment history
- Logs
- Metrics

---

## Getting Help

1. **Render Support:** https://support.render.com/
2. **Discord Community:** https://discord.gg/render
3. **Documentation:** https://render.com/docs
4. **Status Page:** https://status.render.com/

---

## Next Steps

1. ✅ Create Render account
2. ✅ Deploy backend service
3. ✅ Deploy frontend service
4. ✅ Configure environment variables
5. ✅ Test application
6. ✅ Monitor logs and metrics
7. ✅ Add custom domain (optional)
8. ✅ Scale services as needed

---

## Migration from Other Platforms

**From Heroku to Render?**
- Render is newer, more reliable
- Better pricing for long-term projects
- Similar deployment experience

**From Docker Local?**
- Render handles Docker containerization
- No need to manage infrastructure
- Auto-scaling included

---

## Summary

**Render Deployment is:**
- ✅ Simple and beginner-friendly
- ✅ Affordable ($7-44/month)
- ✅ Production-ready
- ✅ Auto-deploy on git push
- ✅ Great for HR Tech Platform

**Recommended for:** Most projects, including this HR Tech Platform

---

**Happy deploying on Render! 🚀**

For questions, see the Render documentation or support.
