# 🚀 SkyStream Deployment Recovery Plan

## Current Status
The application is experiencing "FUNCTION_INVOCATION_FAILED" errors on Vercel. I've created a minimal version to get it working first.

## 📋 Recovery Steps

### Phase 1: Get Basic App Working ✅
- [x] Created minimal Flask app (`backend/api/index.py`)
- [x] Simplified requirements.txt to just Flask
- [x] Removed all complex dependencies
- [x] Added basic routes: `/`, `/health`, `/test`

### Phase 2: Add Back Core Functionality (Once Phase 1 works)
1. **Restore requirements.txt**
   ```bash
   cp backend/requirements_backup.txt backend/requirements.txt
   ```

2. **Restore full app.py**
   - Add back database configuration
   - Add back models import
   - Test each addition

3. **Add back routes gradually**
   ```bash
   cp backend/routes_backup.py backend/routes.py
   ```

4. **Test each major feature**
   - Home page ✅
   - User registration
   - User login
   - Flight search
   - Admin dashboard

### Phase 3: Optimize Performance
1. **Database optimization**
   - Add back seat generation (optimized)
   - Add back flight search (simplified)
   - Add back admin features

2. **Template optimization**
   - Ensure all templates load correctly
   - Fix any template syntax issues

## 🔧 Current Minimal Setup

### Files Modified:
- `backend/api/index.py` → Minimal Flask app
- `backend/requirements.txt` → Only Flask dependency

### What Works Now:
- ✅ Basic Flask application
- ✅ Home page with SkyStream branding
- ✅ Health check endpoint
- ✅ Error handling
- ✅ JSON API responses

### Test URLs:
- `/` - Home page
- `/health` - Health check
- `/test` - Basic functionality test

## 🎯 Success Criteria

**Phase 1 Success**: No more "FUNCTION_INVOCATION_FAILED" errors
**Phase 2 Success**: User can register, login, and search flights
**Phase 3 Success**: Full application functionality restored

## 🔄 Rollback Plan

If any phase fails:
1. Revert to previous working version
2. Identify specific issue
3. Fix incrementally
4. Test thoroughly before proceeding

## 📝 Notes

- Keep backups of all working versions
- Test each change on Vercel before proceeding
- Monitor Vercel function logs for specific errors
- Use minimal changes between deployments