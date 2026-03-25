# 🚀 Mistral AI Setup Guide - 100% Working Configuration

## ❌ Current Status
Your Mistral AI is **OFFLINE** - showing "Connection timeout" error on port 1234.
This means **LM Studio is not running** or not properly configured.

---

## ✅ Quick Fix (5 Minutes)

### Step 1: Download LM Studio
1. Visit: **https://lmstudio.ai/**
2. Download the latest version for your OS (Windows/Mac/Linux)
3. Install following the on-screen instructions
4. Launch LM Studio application

### Step 2: Load Mistral Model
1. In LM Studio, go to **"Search models"** on the left sidebar
2. Search for: **`mistral-7b-instruct-v0.2`** (or any Mistral model)
3. Click **"Download"** button
4. Wait for download to complete (~4-8 GB, depends on internet)
   - Progress bar will show download status
   - Takes 5-30 minutes depending on your internet speed

### Step 3: Start the Server
1. Once model is loaded, go to **"Local Server"** tab (left sidebar)
2. Click **"Start Server"** button
3. You should see: **"Server is running on http://127.0.0.1:1234/v1"**
4. Status indicator should turn **green** ✓

### Step 4: Verify Connection
In your backend terminal, you should see:
```
✓ Mistral AI ONLINE and READY!
```

If still offline, see troubleshooting section below.

---

## 🔍 Verification Checklist

- [ ] LM Studio app is open and running
- [ ] A Mistral model is loaded (download complete)
- [ ] Local server is started (green status indicator)
- [ ] URL shows: `http://127.0.0.1:1234/v1`
- [ ] Backend app shows "✓ Mistral AI ONLINE"
- [ ] Health endpoint shows: `mistral_available: true`

---

## 🛠️ Troubleshooting

### Issue 1: "Connection Refused" Error
**Cause**: LM Studio server is not running on port 1234

**Fix**:
1. Open LM Studio app
2. Go to **"Local Server"** tab
3. Click **"Start Server"** button (should turn green)
4. Wait 5-10 seconds for server to initialize
5. Application will auto-reconnect within 5 seconds

### Issue 2: "Request Timed Out" Error
**Cause**: Server is running but not responding (model might be loading)

**Fix**:
1. Check LM Studio status indicator (should be green ✓)
2. Check that a model is fully loaded (download % = 100%)
3. Wait 10-20 seconds and try again
4. Application will automatically retry

### Issue 3: Model Not Found
**Cause**: Model name in config doesn't match loaded model

**Fix**:
1. Check `.env` file for `MISTRAL_MODEL_NAME`
2. In LM Studio, check the **exact model name** that's loaded
3. Update `.env` to match exactly (case-sensitive)
4. Restart backend application

**Example**:
```
.env file should have:
MISTRAL_MODEL_NAME=mistral-7b-instruct-v0.2
```

### Issue 4: Port 1234 Already in Use
**Cause**: Another service is using port 1234

**Fix Option A** (Recommended):
1. Kill the existing process on port 1234
2. Restart LM Studio

**Fix Option B**:
1. Edit `.env` file:
   ```
   MISTRAL_BASE_URL=http://127.0.0.1:8000/v1
   ```
2. Reconfigure LM Studio to use a different port
3. Restart backend application

### Issue 5: Internet Issues During Download
**Cause**: Network disconnection while downloading model

**Fix**:
1. Check your internet connection
2. Go back to model search in LM Studio
3. Click Download again (should resume from where it left off)
4. Wait for 100% completion

---

## 📊 How It Works

### When Mistral AI is ONLINE ✓
```
User starts interview
    ↓
AI generates smart question
    ↓
AI generates 5 semantic MC options with correct answer
    ↓
User submits answer
    ↓
AI provides detailed feedback with 6-dimension scoring
    ↓
Analytics updated with AI insights
```

### When Mistral AI is OFFLINE ❌
```
User starts interview
    ↓
Fallback: Static high-quality questions used
    ↓
Fallback: 5 MC options generated locally
    ↓
User submits answer
    ↓
Fallback: Basic evaluation (word count + patterns)
    ↓
Analytics updated with fallback scores
```

**Application continues working!** Users can still practice, just without AI intelligence.

---

## 🔧 Advanced Configuration

### Use Cloud Mistral API Instead of Local

If you prefer cloud-hosted Mistral instead of LM Studio:

1. Sign up at **Mistral AI API**: https://console.mistral.ai/
2. Get your API key
3. Edit `.env`:
   ```
   MISTRAL_BASE_URL=https://api.mistral.ai/v1
   MISTRAL_API_KEY=your_api_key_here
   MISTRAL_MODEL_NAME=mistral-small
   ```
4. Restart backend
5. Application will connect to cloud ☁️

**Cost**: Pay-per-use (very affordable for small usage)

---

## 📋 System Requirements

- **RAM**: 8 GB minimum (16 GB recommended)
- **Storage**: 10-15 GB free (for model download)
- **Internet**: ~30 minutes for initial download
- **OS**: Windows 10+, macOS 10.14+, Linux (Ubuntu 18+)
- **GPU** (Optional): NVIDIA/AMD/Apple Silicon for faster inference

---

## ✅ Success Indicators

When everything is working correctly:

1. **Backend Terminal Output**:
   ```
   ================================================================================
     MISTRAL AI AGENT - INITIALIZATION
   ================================================================================
     Base URL:  http://127.0.0.1:1234/v1
     Model:     mistral-7b-instruct-v0.2
     Config:    LM Studio (Local Offline Model)
   ================================================================================

   ✓ Mistral AI ONLINE and READY!
   ```

2. **Browser Console** (F12):
   ```javascript
   GET /api/health
   Response: { mistral: { available: true, ... } }
   ```

3. **Interview Start**:
   - Questions load quickly with detailed content
   - MC options are semantically related to questions
   - Feedback after answer submission is detailed and contextual

---

## 🆘 Still Not Working?

### Check These Steps:

1. **Verify LM Studio Process**:
   ```powershell
   # Windows
   Get-Process | Where-Object {$_.Name -like "*studio*"}
   ```

2. **Check Port 1234 Listening**:
   ```powershell
   # Windows
   netstat -ano | findstr :1234
   ```

3. **Manual Connection Test**:
   ```powershell
   # Test if server is running
   Invoke-WebRequest http://127.0.0.1:1234/v1 -TimeoutSec 5
   ```

4. **Check Application Logs**:
   - Backend logs in: `logs/interview_coach.log`
   - Look for [Mistral] entries

5. **Health Endpoint Debug**:
   ```
   GET http://localhost:5000/api/health
   Check: mistral.connection_error details
   ```

---

## 📞 Support Resources

- **LM Studio Docs**: https://lmstudio.ai/docs
- **Mistral AI Docs**: https://docs.mistral.ai/
- **OpenAI SDK Docs**: https://github.com/openai/python-sdk

---

## ⚡ Performance Tips

- **First Load**: 10-30 seconds (model initialization)
- **Subsequent Loads**: 2-5 seconds (cached in memory)
- **Optimize**: Keep 1-2 models loaded, unload unused ones
- **Monitor**: Watch "Local Server" tab for CPU/RAM usage

---

## 🎯 Key Takeaway

**Mistral timeout error = LM Studio not running or not properly configured**

**99% of cases fixed by**:
1. Opening LM Studio
2. Loading a Mistral model
3. Starting the local server
4. Waiting 5-10 seconds for auto-reconnect

Your application will automatically detect when Mistral comes online! ✅

---

*Last Updated: March 7, 2026*
*Status: Production Ready (with full fallback support)*
