# 🚀 ARIA Deployment Guide

## Quick Deployment Checklist

### ✅ Pre-Deployment
- [ ] GitHub repository created
- [ ] All files uploaded to GitHub
- [ ] OpenAI API key ready
- [ ] Supabase project created (optional)

### ✅ Streamlit Cloud Setup
- [ ] Streamlit Cloud account created
- [ ] Repository connected
- [ ] App deployed
- [ ] Environment variables configured

### ✅ Database Setup (Optional)
- [ ] Supabase SQL migration executed
- [ ] Database credentials added to secrets
- [ ] Connection tested

## 📋 Detailed Steps

### 1. GitHub Repository Setup

```bash
# Create new repository on GitHub
# Upload all files from aria-streamlit-deploy folder
# Ensure .gitignore is included
```

### 2. Streamlit Cloud Deployment

1. **Visit**: [share.streamlit.io](https://share.streamlit.io)
2. **Click**: "New app"
3. **Repository**: Select your GitHub repo
4. **Branch**: main (or master)
5. **Main file path**: `app.py`
6. **Click**: "Deploy!"

### 3. Environment Variables Configuration

In Streamlit Cloud **Advanced Settings** → **Secrets**, add:

```toml
# Required for basic functionality
[general]
OPENAI_API_KEY = "sk-proj-your-actual-openai-key-here"

# Optional for conversation storage
SUPABASE_URL = "https://your-project-ref.supabase.co"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Supabase Database Setup (Optional)

1. **Create Project**: Go to [supabase.com](https://supabase.com)
2. **SQL Editor**: Navigate to SQL Editor in dashboard
3. **Run Migration**: Execute the SQL from `supabase/migrations/001_create_conversations_table.sql`
4. **Get Credentials**: 
   - Project URL: Settings → API → Project URL
   - Anon Key: Settings → API → Project API keys → anon public

### 5. Testing Deployment

1. **Access App**: Use the Streamlit Cloud URL
2. **Test Chat**: Send a message to ARIA
3. **Check Logs**: Monitor Streamlit Cloud logs for errors
4. **Verify Database**: Check Supabase if configured

## 🔧 Configuration Details

### Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API access key | ✅ Yes |
| `SUPABASE_URL` | Supabase project URL | ❌ Optional |
| `SUPABASE_ANON_KEY` | Supabase anonymous key | ❌ Optional |

### File Structure Verification

Ensure your repository contains:
```
├── app.py                    # ✅ Main app file
├── requirements.txt          # ✅ Dependencies
├── scripts/                  # ✅ Core logic
├── embeddings/              # ✅ Course data
├── supabase/migrations/     # ✅ Database schema
├── .streamlit/secrets.toml.example  # ✅ Config template
├── .gitignore               # ✅ Security
└── README.md                # ✅ Documentation
```

## 🚨 Common Issues & Solutions

### Issue: App Won't Start
**Solution**: Check Streamlit Cloud logs for missing environment variables

### Issue: OpenAI API Errors
**Solutions**:
- Verify API key format (starts with `sk-proj-`)
- Check OpenAI account has available credits
- Ensure key has proper permissions

### Issue: Database Connection Failed
**Solutions**:
- Verify Supabase URL format
- Check anon key is complete
- Ensure SQL migration was executed
- Verify table permissions in Supabase

### Issue: Slow Initial Load
**Explanation**: Normal behavior - embeddings are loading on first startup

### Issue: Memory Errors
**Solutions**:
- Streamlit Cloud has memory limits
- Consider optimizing embedding files
- Monitor resource usage in logs

## 📊 Post-Deployment Monitoring

### Streamlit Cloud Dashboard
- Monitor app health
- Check resource usage
- Review error logs
- Track user activity

### Supabase Dashboard (if configured)
- View conversation data
- Monitor database performance
- Check API usage
- Export analytics data

## 🔄 Updates & Maintenance

### Code Updates
1. Push changes to GitHub repository
2. Streamlit Cloud auto-deploys from main branch
3. Monitor deployment logs

### Environment Variables Updates
1. Go to Streamlit Cloud app settings
2. Update secrets in Advanced Settings
3. Restart app if needed

### Database Schema Updates
1. Create new migration file
2. Execute in Supabase SQL Editor
3. Update application code if needed

## 🎯 Success Indicators

✅ **Deployment Successful When**:
- App loads without errors
- ARIA responds to messages
- No error messages in logs
- Database stores conversations (if configured)

✅ **Ready for Production When**:
- All features tested
- Error handling verified
- Performance acceptable
- Monitoring configured

---

🚀 **Your ARIA Teaching Assistant is now live and ready to help students!**