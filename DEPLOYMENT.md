# Vercel Deployment Instructions

## Current Issue: 500 Internal Server Error

The 500 error is caused by missing environment variables in Vercel.

## Fix Steps:

### 1. Add Environment Variables in Vercel

Go to your Vercel project dashboard:
- Navigate to: https://vercel.com/dashboard
- Select your project: `skystream-airplane-management`
- Go to **Settings** → **Environment Variables**
- Add these two variables:

**DATABASE_URL:**
```
postgresql://neondb_owner:npg_AL7NPoyUz8bV@ep-holy-sky-aonypf4n-pooler.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

**SECRET_KEY:**
```
your-secret-key-here-change-this-to-random-string
```

### 2. Redeploy

After adding the environment variables:
- Vercel will automatically redeploy
- OR manually trigger a redeploy from the Deployments tab

### 3. Verify Deployment

Visit these URLs to verify:
- Main site: https://skystream-airplane-management.vercel.app/
- Health check: https://skystream-airplane-management.vercel.app/health
- Diagnostic: https://skystream-airplane-management.vercel.app/api/diagnostic

## Alternative: Local Development

If you want to run locally instead:

```bash
cd backend
source ../venv/bin/activate
python3 app.py
```

Then visit: http://localhost:5000

## Database Status

The database is already set up and populated with:
- 440 flights
- 10 users (including admin accounts)
- Multiple planes and routes

No database initialization is needed - just add the environment variables!
