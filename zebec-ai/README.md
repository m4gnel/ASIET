# 🚀 Zebec AI - AI-Powered Social Media Management Platform

<div align="center">

![Zebec AI](https://img.shields.io/badge/Zebec-AI-yellow?style=for-the-badge)
![Next.js](https://img.shields.io/badge/Next.js-14+-black?style=for-the-badge&logo=next.js)
![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-blue?style=for-the-badge&logo=typescript)
![Firebase](https://img.shields.io/badge/Firebase-10+-orange?style=for-the-badge&logo=firebase)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-green?style=for-the-badge&logo=openai)

**Dominate social media with AI-powered content creation, scheduling, and analytics**

[Features](#features) • [Installation](#installation) • [Configuration](#configuration) • [API Documentation](#api-documentation) • [Deployment](#deployment)

</div>

---

## ✨ Features

### 🎯 Core Capabilities

- **🤖 AI-Powered Content Generation**
  - Viral caption generation using GPT-4 and Gemini
  - Smart hashtag recommendations
  - Content idea generation
  - Optimal posting time analysis
  - Full content performance prediction

- **📱 Multi-Platform Support**
  - YouTube (Videos & Shorts)
  - Instagram (Posts, Reels, Stories)
  - TikTok (Videos)
  - Twitter/X (Posts & Threads)
  - Facebook (Posts & Stories)
  - LinkedIn (Posts & Articles)

- **📊 Advanced Analytics**
  - Real-time engagement tracking
  - Cross-platform performance metrics
  - Audience insights and demographics
  - Growth trend analysis
  - Competitor benchmarking

- **⏰ Smart Scheduling**
  - AI-optimized posting times
  - Bulk scheduling
  - Content calendar
  - Auto-publishing
  - Queue management

- **🔥 Additional Features**
  - Drag-and-drop file uploads
  - Video processing and optimization
  - Thumbnail generation
  - Team collaboration
  - White-label options (Enterprise)
  - API access
  - Webhook integrations

---

## 🛠️ Tech Stack

### Frontend
- **Next.js 14+** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Framer Motion** - Smooth animations
- **Lucide React** - Beautiful icons
- **Recharts** - Data visualization

### Backend
- **Next.js API Routes** - Serverless functions
- **Firebase** - Authentication & Database
- **Firestore** - Real-time NoSQL database
- **Firebase Storage** - File storage

### AI & ML
- **OpenAI GPT-4** - Advanced text generation
- **Google Gemini** - Alternative AI model
- **Custom algorithms** - Engagement prediction

### Social Media APIs
- **YouTube Data API v3**
- **Instagram Graph API**
- **TikTok API v2**
- **Twitter API v2**
- **Facebook Graph API**
- **LinkedIn API**

---

## 📦 Installation

### Prerequisites

- Node.js 18+ or Bun
- pnpm, npm, or yarn
- Firebase account
- OpenAI API key
- Social media developer accounts

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/zebec-ai.git
cd zebec-ai

# Install dependencies
pnpm install
# or
npm install
# or
yarn install

# Copy environment variables
cp .env.example .env.local

# Run development server
pnpm dev
# or
npm run dev
# or
yarn dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## ⚙️ Configuration

### 1. Firebase Setup

1. Create a new Firebase project at [console.firebase.google.com](https://console.firebase.google.com)
2. Enable Authentication (Email/Password, Google, Facebook, Twitter)
3. Create a Firestore database
4. Enable Firebase Storage
5. Get your Firebase config and add to `.env.local`:

```env
NEXT_PUBLIC_FIREBASE_API_KEY=your_api_key
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=your_auth_domain
NEXT_PUBLIC_FIREBASE_PROJECT_ID=your_project_id
NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=your_storage_bucket
NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
NEXT_PUBLIC_FIREBASE_APP_ID=your_app_id
```

6. Generate Firebase Admin SDK credentials:
   - Go to Project Settings → Service Accounts
   - Generate new private key
   - Add to `.env.local`:

```env
FIREBASE_ADMIN_PROJECT_ID=your_project_id
FIREBASE_ADMIN_CLIENT_EMAIL=your_client_email
FIREBASE_ADMIN_PRIVATE_KEY="your_private_key"
```

### 2. OpenAI Setup

1. Get API key from [platform.openai.com](https://platform.openai.com)
2. Add to `.env.local`:

```env
OPENAI_API_KEY=sk-your_openai_key
```

### 3. Google Gemini Setup (Optional)

1. Get API key from [makersuite.google.com](https://makersuite.google.com)
2. Add to `.env.local`:

```env
GOOGLE_GEMINI_API_KEY=your_gemini_key
```

### 4. Social Media API Setup

#### YouTube

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials
5. Add authorized redirect URI: `http://localhost:3000/api/social/youtube/callback`
6. Add to `.env.local`:

```env
YOUTUBE_CLIENT_ID=your_client_id
YOUTUBE_CLIENT_SECRET=your_client_secret
YOUTUBE_API_KEY=your_api_key
```

#### Instagram

1. Go to [Facebook Developers](https://developers.facebook.com)
2. Create a new app
3. Add Instagram Basic Display and Instagram Graph API
4. Add redirect URI: `http://localhost:3000/api/social/instagram/callback`
5. Add to `.env.local`:

```env
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
```

#### TikTok

1. Go to [TikTok Developers](https://developers.tiktok.com)
2. Create a new app
3. Request access to Content Posting API
4. Add redirect URI: `http://localhost:3000/api/social/tiktok/callback`
5. Add to `.env.local`:

```env
TIKTOK_CLIENT_KEY=your_client_key
TIKTOK_CLIENT_SECRET=your_client_secret
```

#### Twitter/X

1. Go to [Twitter Developer Portal](https://developer.twitter.com)
2. Create a new app
3. Enable OAuth 2.0
4. Add to `.env.local`:

```env
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
TWITTER_BEARER_TOKEN=your_bearer_token
```

#### Facebook

1. Use the same app from Instagram setup
2. Add Facebook Login product
3. Add to `.env.local`:

```env
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
```

### 5. Application Settings

```env
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXTAUTH_SECRET=your_random_secret_key
NEXTAUTH_URL=http://localhost:3000
```

---

## 📚 API Documentation

### AI Generation Endpoint

**POST** `/api/ai/generate`

Generate AI content (captions, hashtags, ideas, etc.)

```typescript
// Request
{
  "type": "caption" | "hashtags" | "ideas" | "posting-times" | "full-analysis",
  "content": {
    "title": "My Video Title",
    "description": "Video description",
    "platform": "youtube",
    "targetAudience": "tech enthusiasts",
    "tone": "professional"
  },
  "options": {
    "count": 5,
    "maxLength": 280,
    "includeEmojis": true
  }
}

// Response
{
  "success": true,
  "data": {
    "captions": [...],
    "hashtags": [...],
    "postingTimes": [...]
  }
}
```

### Upload Endpoint

**POST** `/api/upload`

Upload media files (videos, images)

```typescript
// Request (multipart/form-data)
{
  "file": File,
  "userId": "user_id"
}

// Response
{
  "success": true,
  "data": {
    "fileUrl": "/uploads/user_id/filename.mp4",
    "filename": "filename.mp4",
    "size": 1024000,
    "type": "video/mp4"
  }
}
```

### Social Media Publishing

**POST** `/api/social/publish`

Publish content to social platforms

```typescript
// Request
{
  "platform": "youtube" | "instagram" | "tiktok" | "twitter",
  "contentId": "content_id",
  "caption": "Post caption",
  "hashtags": ["#tag1", "#tag2"],
  "scheduledFor": "2024-01-01T12:00:00Z" // optional
}

// Response
{
  "success": true,
  "postId": "platform_post_id",
  "url": "https://platform.com/post/id"
}
```

---

## 🚀 Deployment

### Vercel (Recommended)

1. Push your code to GitHub
2. Import project in [Vercel](https://vercel.com)
3. Add environment variables
4. Deploy

```bash
# Or use Vercel CLI
vercel --prod
```

### Docker

```bash
# Build image
docker build -t zebec-ai .

# Run container
docker run -p 3000:3000 --env-file .env.local zebec-ai
```

### Manual Deployment

```bash
# Build for production
pnpm build

# Start production server
pnpm start
```

---

## 📊 Database Schema

### Users Collection

```typescript
{
  uid: string;
  name: string;
  email: string;
  plan: 'starter' | 'professional' | 'enterprise';
  connectedPlatforms: ConnectedPlatform[];
  analytics: UserAnalytics;
  createdAt: string;
  updatedAt: string;
}
```

### Content Collection

```typescript
{
  id: string;
  userId: string;
  type: 'video' | 'image' | 'carousel';
  title: string;
  fileUrl: string;
  status: 'processing' | 'ready' | 'scheduled' | 'published';
  aiGenerated: {
    captions: AICaption[];
    hashtags: string[];
    postingTimes: PostingTime[];
  };
  scheduledPosts: ScheduledPost[];
  analytics: ContentAnalytics;
  createdAt: string;
}
```

---

## 🎨 Customization

### Branding

Edit `tailwind.config.ts` to customize colors:

```typescript
colors: {
  primary: {
    // Your brand colors
  },
  secondary: {
    // Your secondary colors
  },
}
```

### Features

Enable/disable features in `lib/config.ts`:

```typescript
export const FEATURES = {
  AI_GENERATION: true,
  SOCIAL_PUBLISHING: true,
  ANALYTICS: true,
  TEAM_COLLABORATION: false, // Enterprise only
};
```

---

## 🧪 Testing

```bash
# Run tests
pnpm test

# Run tests with coverage
pnpm test:coverage

# E2E tests
pnpm test:e2e
```

---

## 📈 Performance

- **Lighthouse Score**: 95+
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Bundle Size**: < 200KB (gzipped)

---

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) first.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 API
- Google for Gemini AI
- Firebase team
- Next.js team
- All social media platforms for their APIs

---

## 📞 Support

- **Email**: support@zebec-ai.com
- **Discord**: [Join our community](https://discord.gg/zebec-ai)
- **Documentation**: [docs.zebec-ai.com](https://docs.zebec-ai.com)
- **Twitter**: [@ZebecAI](https://twitter.com/ZebecAI)

---

<div align="center">

**Made with ❤️ by the Zebec AI Team**

[Website](https://zebec-ai.com) • [Documentation](https://docs.zebec-ai.com) • [Blog](https://blog.zebec-ai.com)

</div>
