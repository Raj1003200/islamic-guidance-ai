# Vercel Deployment Guide for MuslimGuideAI

This guide walks you through deploying the MuslimGuideAI application to Vercel with both the Python FastAPI backend and static frontend.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **GitHub Repository**: Push your code to GitHub
3. **Gemini API Key**: Obtain from [Google AI Studio](https://makersuite.google.com/app/apikey)

## Deployment Steps

### 1. Connect to Vercel

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Vercel will auto-detect the configuration from `vercel.json`

### 2. Configure Environment Variables

Before deploying, add your environment variables in Vercel dashboard:

1. In your Vercel project, go to **Settings** → **Environment Variables**
2. Add the following variable:
   - **Name**: `GEMINI_API_KEY`
   - **Value**: Your Google Gemini API key
   - **Environment**: Select all (Production, Preview, Development)
3. Click **Save**

### 3. Deploy

1. Click **Deploy** button
2. Vercel will:
   - Install Python dependencies from `requirements.txt`
   - Build serverless functions from `api/` directory
   - Serve static files from `frontend/` directory
3. Wait for deployment to complete (usually 1-2 minutes)

### 4. Verify Deployment

After deployment, test your application:

1. **Frontend**: Visit your Vercel URL (e.g., `https://your-app.vercel.app`)
2. **API Endpoints**: Test these endpoints:
   - `https://your-app.vercel.app/api/guidance` (POST)
   - `https://your-app.vercel.app/api/quran/search?keyword=faith` (GET)
   - `https://your-app.vercel.app/api/hadith/search?topic=prayer` (GET)

## Project Structure

```
MuslimGuideAI/
├── api/
│   └── index.py              # Vercel serverless function entry point
├── backend/
│   ├── main.py               # FastAPI application
│   ├── services.py           # Quran/Hadith search services
│   └── api_parsers.py        # API response parsers
├── frontend/
│   ├── index.html            # Main page
│   ├── settings.html         # Settings page
│   ├── styles.css            # Styles
│   ├── script.js             # Main app logic
│   └── settings.js           # Settings logic
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel configuration
└── .env.example             # Environment variable template
```

## How It Works

### Serverless Functions

Vercel converts your FastAPI app into serverless functions:
- Each API request creates a new function instance
- Functions are stateless and ephemeral
- Logs are available in Vercel dashboard under **Deployments** → **Functions**

### Static File Serving

- Frontend files are served from Vercel's global CDN
- Automatic SSL/HTTPS
- Optimized caching and compression

### Environment Variables

- Set in Vercel dashboard
- Automatically injected into serverless functions
- Not accessible from frontend (secure)

## Important Notes

### API Key Management

⚠️ **Production Environment**: The `/api/save-api-key` endpoint is **disabled** in production for security. You must set `GEMINI_API_KEY` in Vercel's environment variables dashboard.

### Logging

- File-based logging is disabled in serverless environment
- All logs go to Vercel's logging system
- View logs: Vercel Dashboard → Deployments → Functions → Runtime Logs

### Local Development

To run locally:

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variable
# Create .env file with: GEMINI_API_KEY=your_key_here

# Run the server
python -m uvicorn backend.main:app --reload --port 8000
```

## Troubleshooting

### API Returns 500 Error

**Cause**: Missing or invalid `GEMINI_API_KEY`

**Solution**: 
1. Go to Vercel Dashboard → Settings → Environment Variables
2. Verify `GEMINI_API_KEY` is set correctly
3. Redeploy the application

### Frontend Can't Connect to Backend

**Cause**: Frontend making requests to `localhost` instead of Vercel URL

**Solution**: Check `script.js` - API calls should be relative (e.g., `/api/guidance`)

### Import Errors in Serverless Function

**Cause**: Missing dependency in `requirements.txt`

**Solution**:
1. Add missing package to `requirements.txt`
2. Commit and push changes
3. Vercel will auto-deploy with new dependencies

### Function Timeout

**Cause**: Gemini API taking too long to respond

**Solution**: Vercel's default timeout is 10s (Hobby) or 60s (Pro). Consider:
- Optimizing prompts to reduce response time
- Upgrading to Pro plan for longer timeout
- Adding request timeout handling in code

## Advanced Configuration

### Custom Domain

1. Go to Vercel Dashboard → Settings → Domains
2. Add your custom domain
3. Follow DNS configuration instructions

### Preview Deployments

- Every Git push creates a preview deployment
- Test changes before merging to production
- Automatic deployment from `main` branch

### Monitoring

Enable monitoring in Vercel Dashboard:
- **Analytics**: Track page views and performance
- **Logs**: Real-time function logs
- **Speed Insights**: Core Web Vitals monitoring

## Security Best Practices

1. ✅ **Never commit API keys** to repository
2. ✅ **Use environment variables** for all secrets
3. ✅ **Enable CORS properly** (already configured in `main.py`)
4. ✅ **Validate user input** (already implemented)
5. ✅ **Rate limiting**: Consider adding rate limiting for production

## Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Python on Vercel**: [vercel.com/docs/functions/serverless-functions/runtimes/python](https://vercel.com/docs/functions/serverless-functions/runtimes/python)
- **FastAPI**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

## Next Steps

After successful deployment:

1. ✅ Test all features thoroughly
2. ✅ Set up custom domain (optional)
3. ✅ Enable analytics and monitoring
4. ✅ Configure automatic deployments from GitHub
5. ✅ Share your app URL!
