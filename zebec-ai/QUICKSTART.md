# ⚡ Zebec AI - Quick Start Guide

Get Zebec AI up and running in 5 minutes!

## 🚀 Super Fast Setup

### 1. Install Dependencies (1 minute)

```bash
cd zebec-ai
pnpm install
```

### 2. Configure Environment (2 minutes)

```bash
# Copy the environment template
cp .env.example .env.local

# Edit .env.local with your credentials
nano .env.local  # or use your favorite editor
```

**Minimum Required Variables** (for basic functionality):

```env
# Firebase (Required)
NEXT_PUBLIC_FIREBASE_API_KEY=your_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id

# OpenAI (Required for AI features)
OPENAI_API_KEY=sk-your_key

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000
```

### 3. Run Development Server (30 seconds)

```bash
pnpm dev
```

### 4. Open Browser (30 seconds)

Visit: **http://localhost:3000**

---

## 🎯 First Steps After Setup

### 1. Create Your Account
- Click "Get Started" or "Sign Up"
- Use email/password or social login
- Verify your email

### 2. Connect Your First Platform
- Go to Dashboard → Connect Platforms
- Choose YouTube, Instagram, or TikTok
- Follow OAuth flow to connect

### 3. Upload Your First Content
- Click "Upload Content"
- Drag and drop a video or image
- Wait for processing

### 4. Generate AI Content
- Click "Generate AI Caption"
- Review generated captions
- Select hashtags
- Choose optimal posting time

### 5. Schedule or Publish
- Select target platforms
- Choose "Publish Now" or "Schedule"
- Watch your content go live!

---

## 🔧 Troubleshooting

### Issue: "Firebase not configured"
**Solution**: Make sure all Firebase environment variables are set correctly.

### Issue: "OpenAI API error"
**Solution**: 
1. Check your API key is valid
2. Ensure you have credits in your OpenAI account
3. Verify billing is set up

### Issue: "Social media connection failed"
**Solution**:
1. Check redirect URIs match in platform developer console
2. Ensure app is approved (for TikTok, Twitter)
3. Verify API credentials are correct

### Issue: "Upload failed"
**Solution**:
1. Check file size (max 500MB)
2. Verify file format is supported
3. Ensure Firebase Storage is enabled

---

## 📚 Next Steps

1. **Read Full Documentation**: Check `README.md` for comprehensive guide
2. **Setup Guide**: Follow `SETUP_GUIDE.md` for detailed configuration
3. **Features**: Explore `FEATURES.md` to see all capabilities
4. **API Docs**: Review API endpoints for integrations

---

## 🆘 Need Help?

- **Documentation**: All `.md` files in project root
- **Discord**: Join our community
- **Email**: support@zebec-ai.com
- **GitHub Issues**: Report bugs

---

## 🎉 You're Ready!

Your Zebec AI instance is now running. Start creating amazing content and dominating social media!

**Pro Tip**: Start with the Starter plan features and upgrade as you grow. The platform scales with your needs.

---

## 📊 Quick Reference

### Common Commands

```bash
# Development
pnpm dev              # Start dev server
pnpm build            # Build for production
pnpm start            # Start production server
pnpm lint             # Run linter
pnpm type-check       # Check TypeScript

# Testing
pnpm test             # Run tests
pnpm test:watch       # Watch mode
pnpm test:coverage    # Coverage report
```

### Project Structure

```
zebec-ai/
├── app/              # Next.js pages and API routes
├── components/       # React components
├── lib/              # Utilities and integrations
├── types/            # TypeScript types
├── public/           # Static assets
└── *.md              # Documentation
```

### Key Files

- `README.md` - Main documentation
- `SETUP_GUIDE.md` - Detailed setup instructions
- `FEATURES.md` - Complete feature list
- `.env.example` - Environment variable template
- `package.json` - Dependencies and scripts

---

**Happy Creating! 🚀**
