# 🚀 Zebec AI - Complete Setup Guide

This guide will walk you through setting up Zebec AI from scratch, including all integrations and configurations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Initial Setup](#initial-setup)
3. [Firebase Configuration](#firebase-configuration)
4. [AI Services Setup](#ai-services-setup)
5. [Social Media Integrations](#social-media-integrations)
6. [Testing](#testing)
7. [Deployment](#deployment)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

- **Node.js** 18.0.0 or higher
- **pnpm** (recommended), npm, or yarn
- **Git**
- A code editor (VS Code recommended)

### Required Accounts

- Firebase account (free tier available)
- OpenAI account with API access
- Google Cloud Platform account
- Social media developer accounts (YouTube, Instagram, TikTok, etc.)

---

## Initial Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone https://github.com/yourusername/zebec-ai.git
cd zebec-ai

# Install dependencies
pnpm install

# Copy environment template
cp .env.example .env.local
```

### 2. Project Structure

```
zebec-ai/
├── app/                    # Next.js app directory
│   ├── api/               # API routes
│   │   ├── ai/           # AI generation endpoints
│   │   ├── upload/       # File upload handlers
│   │   ├── social/       # Social media integrations
│   │   └── analytics/    # Analytics endpoints
│   ├── dashboard/        # Dashboard pages
│   ├── auth/             # Authentication pages
│   └── page.tsx          # Landing page
├── components/            # React components
│   ├── ui/               # UI components
│   ├── dashboard/        # Dashboard components
│   ├── auth/             # Auth components
│   └── landing/          # Landing page components
├── lib/                   # Utility libraries
│   ├── firebase/         # Firebase configuration
│   ├── ai/               # AI service integrations
│   ├── social/           # Social media APIs
│   └── utils/            # Helper functions
├── types/                 # TypeScript type definitions
└── public/               # Static assets
```

---

## Firebase Configuration

### Step 1: Create Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com)
2. Click "Add project"
3. Enter project name: `zebec-ai-production`
4. Disable Google Analytics (optional)
5. Click "Create project"

### Step 2: Enable Authentication

1. In Firebase Console, go to **Authentication**
2. Click "Get started"
3. Enable the following sign-in methods:
   - **Email/Password**: Enable
   - **Google**: Enable (configure OAuth consent screen)
   - **Facebook**: Enable (requires Facebook App ID)
   - **Twitter**: Enable (requires Twitter API keys)

### Step 3: Create Firestore Database

1. Go to **Firestore Database**
2. Click "Create database"
3. Choose "Start in production mode"
4. Select your region (choose closest to your users)
5. Click "Enable"

### Step 4: Set Firestore Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Users collection
    match /users/{userId} {
      allow read: if request.auth != null && request.auth.uid == userId;
      allow write: if request.auth != null && request.auth.uid == userId;
    }
    
    // Content collection
    match /content/{contentId} {
      allow read: if request.auth != null && 
                     resource.data.userId == request.auth.uid;
      allow write: if request.auth != null && 
                      request.resource.data.userId == request.auth.uid;
    }
    
    // Analytics collection (read-only for users)
    match /analytics/{docId} {
      allow read: if request.auth != null;
      allow write: if false; // Only server can write
    }
  }
}
```

### Step 5: Enable Firebase Storage

1. Go to **Storage**
2. Click "Get started"
3. Use default security rules
4. Click "Done"

### Step 6: Set Storage Rules

```javascript
rules_version = '2';
service firebase.storage {
  match /b/{bucket}/o {
    match /uploads/{userId}/{allPaths=**} {
      allow read: if request.auth != null;
      allow write: if request.auth != null && 
                      request.auth.uid == userId &&
                      request.resource.size < 500 * 1024 * 1024; // 500MB limit
    }
  }
}
```

### Step 7: Get Firebase Config

1. Go to **Project Settings** (gear icon)
2. Scroll to "Your apps"
3. Click web icon (</>) to add web app
4. Register app with nickname: "Zebec AI Web"
5. Copy the config object

Add to `.env.local`:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=AIzaSy...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=zebec-ai.firebaseapp.com
NEXT_PUBLIC_FIREBASE_PROJECT_ID=zebec-ai
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=zebec-ai.appspot.com
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=123456789
NEXT_PUBLIC_FIREBASE_APP_ID=1:123456789:web:abc123
```

### Step 8: Generate Admin SDK Credentials

1. Go to **Project Settings** → **Service Accounts**
2. Click "Generate new private key"
3. Save the JSON file securely
4. Extract values and add to `.env.local`:

```env
FIREBASE_ADMIN_PROJECT_ID=zebec-ai
FIREBASE_ADMIN_CLIENT_EMAIL=firebase-adminsdk-xxxxx@zebec-ai.iam.gserviceaccount.com
FIREBASE_ADMIN_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYour_Private_Key_Here\n-----END PRIVATE KEY-----\n"
```

---

## AI Services Setup

### OpenAI (GPT-4)

1. Go to [OpenAI Platform](https://platform.openai.com)
2. Sign up or log in
3. Go to **API Keys**
4. Click "Create new secret key"
5. Name it "Zebec AI Production"
6. Copy the key (you won't see it again!)

Add to `.env.local`:

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
```

**Important**: Set up billing and usage limits to avoid unexpected charges.

### Google Gemini (Optional Alternative)

1. Go to [Google AI Studio](https://makersuite.google.com)
2. Click "Get API key"
3. Create new API key
4. Copy the key

Add to `.env.local`:

```env
GOOGLE_GEMINI_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx
```

---

## Social Media Integrations

### YouTube Data API

#### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create new project: "Zebec AI"
3. Enable **YouTube Data API v3**

#### Step 2: Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click "Create Credentials" → "OAuth client ID"
3. Configure OAuth consent screen:
   - User Type: External
   - App name: Zebec AI
   - Support email: your email
   - Scopes: Add YouTube scopes
4. Create OAuth client ID:
   - Application type: Web application
   - Name: Zebec AI Web Client
   - Authorized redirect URIs:
     - `http://localhost:3000/api/social/youtube/callback`
     - `https://yourdomain.com/api/social/youtube/callback`

#### Step 3: Get API Key

1. Click "Create Credentials" → "API key"
2. Restrict key to YouTube Data API v3
3. Copy the key

Add to `.env.local`:

```env
YOUTUBE_CLIENT_ID=123456789-xxxxxxxxxxxxx.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxx
YOUTUBE_API_KEY=AIzaSyxxxxxxxxxxxxxxxxx
```

### Instagram Graph API

#### Step 1: Create Facebook App

1. Go to [Facebook Developers](https://developers.facebook.com)
2. Click "Create App"
3. Choose "Business" type
4. App name: "Zebec AI"
5. Contact email: your email

#### Step 2: Add Instagram Products

1. In app dashboard, add products:
   - Instagram Basic Display
   - Instagram Graph API
2. Configure Instagram Basic Display:
   - Valid OAuth Redirect URIs:
     - `http://localhost:3000/api/social/instagram/callback`
     - `https://yourdomain.com/api/social/instagram/callback`

#### Step 3: Get Credentials

1. Go to **Settings** → **Basic**
2. Copy App ID and App Secret

Add to `.env.local`:

```env
INSTAGRAM_APP_ID=123456789012345
INSTAGRAM_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
```

### TikTok API

#### Step 1: Register as Developer

1. Go to [TikTok Developers](https://developers.tiktok.com)
2. Sign up with TikTok account
3. Complete developer registration

#### Step 2: Create App

1. Click "Manage apps" → "Create an app"
2. App name: "Zebec AI"
3. Select required permissions:
   - user.info.basic
   - video.list
   - video.upload
4. Add redirect URI:
   - `http://localhost:3000/api/social/tiktok/callback`

#### Step 3: Submit for Review

1. Fill out app details
2. Submit for TikTok review (may take 1-2 weeks)
3. Once approved, get credentials

Add to `.env.local`:

```env
TIKTOK_CLIENT_KEY=aw123456789
TIKTOK_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
```

### Twitter/X API

#### Step 1: Apply for Developer Account

1. Go to [Twitter Developer Portal](https://developer.twitter.com)
2. Apply for developer account
3. Wait for approval (usually instant)

#### Step 2: Create App

1. Create new project and app
2. App name: "Zebec AI"
3. Enable OAuth 2.0
4. Add callback URL:
   - `http://localhost:3000/api/social/twitter/callback`

#### Step 3: Get Credentials

1. Go to app settings
2. Copy API Key, API Secret, and Bearer Token

Add to `.env.local`:

```env
TWITTER_API_KEY=xxxxxxxxxxxxxxxxxxxxx
TWITTER_API_SECRET=xxxxxxxxxxxxxxxxxxxxx
TWITTER_BEARER_TOKEN=xxxxxxxxxxxxxxxxxxxxx
```

### Facebook Graph API

Use the same app from Instagram setup:

```env
FACEBOOK_APP_ID=123456789012345
FACEBOOK_APP_SECRET=xxxxxxxxxxxxxxxxxxxxxxxx
```

---

## Testing

### 1. Run Development Server

```bash
pnpm dev
```

Visit `http://localhost:3000`

### 2. Test Authentication

1. Click "Sign Up"
2. Create account with email/password
3. Verify email
4. Test social logins (Google, Facebook, Twitter)

### 3. Test File Upload

1. Go to Dashboard
2. Upload a test video (< 50MB for testing)
3. Verify file appears in Firebase Storage

### 4. Test AI Generation

1. Upload content
2. Click "Generate AI Caption"
3. Verify captions are generated
4. Test hashtag generation

### 5. Test Social Media Connection

1. Go to "Connect Platforms"
2. Connect YouTube account
3. Verify connection shows in dashboard
4. Test publishing (optional)

---

## Deployment

### Vercel (Recommended)

1. Push code to GitHub
2. Go to [Vercel](https://vercel.com)
3. Import repository
4. Add all environment variables
5. Deploy

### Environment Variables for Production

Update these in `.env.local` for production:

```env
NEXT_PUBLIC_APP_URL=https://yourdomain.com
NEXTAUTH_URL=https://yourdomain.com
```

### Post-Deployment Checklist

- [ ] Update Firebase authorized domains
- [ ] Update OAuth redirect URIs for all platforms
- [ ] Set up custom domain
- [ ] Configure CDN for media files
- [ ] Set up monitoring and error tracking
- [ ] Configure backup strategy
- [ ] Test all features in production

---

## Troubleshooting

### Common Issues

#### Firebase Authentication Errors

**Error**: "auth/unauthorized-domain"

**Solution**: Add your domain to Firebase authorized domains:
1. Firebase Console → Authentication → Settings
2. Add domain to "Authorized domains"

#### OpenAI API Errors

**Error**: "Insufficient quota"

**Solution**: 
1. Check OpenAI billing
2. Add payment method
3. Set usage limits

#### Social Media API Errors

**Error**: "Invalid redirect URI"

**Solution**: Ensure redirect URIs match exactly in:
- Your `.env.local` file
- Platform developer console
- No trailing slashes

#### File Upload Errors

**Error**: "File too large"

**Solution**: 
1. Check `next.config.js` body size limit
2. Verify Firebase Storage rules
3. Compress large files before upload

### Getting Help

- **Documentation**: [docs.zebec-ai.com](https://docs.zebec-ai.com)
- **Discord**: [Join community](https://discord.gg/zebec-ai)
- **Email**: support@zebec-ai.com
- **GitHub Issues**: [Report bugs](https://github.com/yourusername/zebec-ai/issues)

---

## Next Steps

After successful setup:

1. **Customize branding** - Update colors, logos, and text
2. **Configure pricing** - Set up Stripe for payments
3. **Add team features** - Implement collaboration tools
4. **Set up analytics** - Integrate Google Analytics
5. **Optimize performance** - Enable caching and CDN
6. **Security audit** - Review all security settings
7. **Launch marketing** - Prepare landing pages and content

---

## Security Best Practices

1. **Never commit `.env.local`** to version control
2. **Rotate API keys** regularly
3. **Use environment-specific keys** (dev, staging, prod)
4. **Enable 2FA** on all service accounts
5. **Monitor API usage** for unusual activity
6. **Set up rate limiting** on API endpoints
7. **Regular security audits** of dependencies

---

**Congratulations! Your Zebec AI instance is now fully configured and ready to dominate social media! 🚀**
