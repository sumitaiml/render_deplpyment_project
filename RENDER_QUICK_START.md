# 🚀 Render Deployment - Quick Start (15 Minutes)

Your HR Tech Platform can be deployed on Render in just 15 minutes!

---

## Why Choose Render?

✅ **Best Features:**
- Simple setup (no complex configs)
- Free tier available
- Auto-deploy from GitHub
- PostgreSQL included
- Built-in SSL/TLS
- Auto-scaling
- Great dashboards
- Affordable ($7-44/month for production)

---

## Pre-Deployment Checklist

- [ ] Render account created (free at https://render.com)
- [ ] Project pushed to GitHub ✅ (already done!)
- [ ] GitHub account connected to Render

---

## 5-Step Quick Deploy

### **Step 1: Create Database (2 min)**
1. Go to https://render.com/dashboard
2. Click **New +** → **PostgreSQL**
3. Name: `hrtech-db`
4. Click **Create Database**
5. **Copy the "Internal Database URL"** (you'll need this!)

---

### **Step 2: Create Backend Service (3 min)**
1. Click **New +** → **Web Service**
2. Connect GitHub → select `hrtech-platform` repo
3. Configure:
   - **Name:** `hrtech-backend`
   - **Environment:** Docker
   - **Dockerfile path:** `backend/Dockerfile`
   - **Plan:** Starter ($7/month) or free tier

4. Click **Environment** and add:
```
DATABASE_URL=postgresql://user:password@hostname:5432/hrtech_db
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
ENVIRONMENT=production
DEBUG=false
```
(Replace with your actual database credentials from Step 1)

5. Click **Create Web Service**
6. Wait 5 minutes for deployment
7. **Copy the backend URL** when ready

---

### **Step 3: Create Frontend Service (3 min)**
1. Click **New +** → **Web Service**
2. Connect GitHub → select `hrtech-platform` again
3. Configure:
   - **Name:** `hrtech-frontend`
   - **Environment:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `python flask_gateway.py`
   - **Plan:** Starter ($7/month) or free tier

4. Click **Environment** and add:
```
API_BACKEND_URL=https://hrtech-backend.onrender.com
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

5. Click **Create Web Service**
6. Wait 5 minutes for deployment

---

### **Step 4: Update Configuration (2 min)**
1. Go back to **hrtech-frontend** service
2. Click **Environment**
3. Update `API_BACKEND_URL` with your actual backend URL
4. Click **Save**
5. Service auto-redeploys

---

### **Step 5: Test Deployment (2 min)**
1. Open your **hrtech-frontend** URL in browser
2. Upload test resume
3. Create test job
4. Run ranking
5. ✅ Success!

---

## URLs After Deployment

- **Frontend:** `https://hrtech-frontend.onrender.com`
- **Backend:** `https://hrtech-backend.onrender.com`
- **API Docs:** `https://hrtech-backend.onrender.com/docs`

---

## Cost Breakdown

| Service | Tier | Cost/Month |
|---------|------|-----------|
| Frontend | Starter | $7 |
| Backend | Starter | $7 |
| PostgreSQL | Starter | $15 |
| Redis | (optional) | $15 |
| **Total** | | **$7-44/month** |

**Free Option Available:** Use free tier for testing (DB expires in 90 days)

---

## Auto-Deployment from GitHub

After this setup, whenever you:
1. Make code changes
2. Commit and push to GitHub
3. Render automatically deploys within 2-5 minutes

No manual deployment needed! 🎉

---

## Monitor Your Services

From Render dashboard:
- **Logs:** Click service → Logs tab
- **Metrics:** Click service → Metrics tab
- **Status:** Real-time service status
- **History:** Deployment history

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Service won't start | Check Logs tab for error messages |
| Can't connect to database | Verify DATABASE_URL in Environment |
| Frontend can't reach backend | Update API_BACKEND_URL in frontend environment |
| Deploy stuck | Wait 10 minutes, then check logs |

---

## Environment Variables Reference

**Backend needs:**
```env
DATABASE_URL=postgresql://...
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
FLASK_HOST=0.0.0.0
FLASK_PORT=8000
ENVIRONMENT=production
DEBUG=false
SPACY_MODEL=en_core_web_sm
SBERT_MODEL=all-MiniLM-L6-v2
```

**Frontend needs:**
```env
API_BACKEND_URL=https://your-backend.onrender.com
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
```

---

## Next Steps

1. **Monitor logs** - Check for any errors
2. **Test features** - Upload resumes, create jobs, rank candidates
3. **Add custom domain** (optional) - Point your domain to Render
4. **Setup backups** - Configure automated database backups
5. **Scale up** (optional) - Upgrade to higher tier as needed

---

## Recommended Setup for Production

| Service | Tier | Why |
|---------|------|-----|
| Frontend | Starter | Always-on, better performance |
| Backend | Starter | Handles concurrent requests |
| PostgreSQL | Starter | Reliability & backup |
| Redis | Starter | Better caching performance |

**Total:** ~$44/month for production-ready setup

---

## Support Resources

- 📖 **Full Guide:** See `RENDER_DEPLOYMENT.md`
- 🆘 **Render Support:** https://support.render.com/
- 💬 **Community:** https://discord.gg/render
- 📚 **Docs:** https://render.com/docs

---

**Ready to deploy? Start at Step 1! 🚀**

Time estimate: 15 minutes total
