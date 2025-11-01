// Core Types for Zebec AI

export interface User {
  uid: string;
  email: string | null;
  displayName: string | null;
  photoURL: string | null;
  emailVerified: boolean;
  createdAt: string;
}

export interface UserProfile {
  uid: string;
  name: string;
  email: string;
  plan: 'starter' | 'professional' | 'enterprise';
  connectedPlatforms: ConnectedPlatform[];
  uploadedContent: Content[];
  analytics: UserAnalytics;
  createdAt: string;
  updatedAt: string;
}

export interface ConnectedPlatform {
  id: string;
  name: string;
  type: 'youtube' | 'instagram' | 'tiktok' | 'twitter' | 'facebook' | 'linkedin';
  accessToken: string;
  refreshToken?: string;
  expiresAt?: string;
  accountId: string;
  accountName: string;
  followers: number;
  engagement: number;
  connectedAt: string;
  isActive: boolean;
}

export interface Content {
  id: string;
  userId: string;
  type: 'video' | 'image' | 'carousel';
  title: string;
  description?: string;
  fileUrl: string;
  thumbnailUrl: string;
  duration?: number;
  size: number;
  mimeType: string;
  status: 'processing' | 'ready' | 'scheduled' | 'published' | 'failed';
  aiGenerated: {
    captions: AICaption[];
    hashtags: string[];
    bestPostingTimes: PostingTime[];
    contentIdeas: string[];
    thumbnailSuggestions?: string[];
  };
  scheduledPosts: ScheduledPost[];
  analytics: ContentAnalytics;
  createdAt: string;
  updatedAt: string;
}

export interface AICaption {
  id: string;
  text: string;
  platform: string;
  tone: 'professional' | 'casual' | 'humorous' | 'inspirational' | 'educational';
  length: 'short' | 'medium' | 'long';
  score: number;
  hashtags: string[];
}

export interface PostingTime {
  platform: string;
  dayOfWeek: number;
  hour: number;
  score: number;
  reason: string;
}

export interface ScheduledPost {
  id: string;
  contentId: string;
  platform: string;
  scheduledFor: string;
  caption: string;
  hashtags: string[];
  status: 'pending' | 'publishing' | 'published' | 'failed';
  publishedAt?: string;
  postUrl?: string;
  error?: string;
}

export interface ContentAnalytics {
  views: number;
  likes: number;
  comments: number;
  shares: number;
  saves: number;
  reach: number;
  impressions: number;
  engagementRate: number;
  clickThroughRate: number;
  platformBreakdown: {
    [platform: string]: {
      views: number;
      likes: number;
      comments: number;
      shares: number;
    };
  };
}

export interface UserAnalytics {
  totalFollowers: number;
  totalViews: number;
  totalEngagement: number;
  averageEngagementRate: number;
  contentPublished: number;
  platformPerformance: {
    [platform: string]: {
      followers: number;
      engagement: number;
      topContent: string[];
    };
  };
  growthMetrics: {
    followersGrowth: number;
    engagementGrowth: number;
    viewsGrowth: number;
  };
  lastUpdated: string;
}

export interface AIGenerationRequest {
  type: 'caption' | 'hashtags' | 'ideas' | 'thumbnail' | 'posting-times' | 'full-analysis';
  content: {
    title?: string;
    description?: string;
    fileUrl?: string;
    platform?: string;
    targetAudience?: string;
    tone?: string;
  };
  options?: {
    count?: number;
    maxLength?: number;
    includeEmojis?: boolean;
    language?: string;
  };
}

export interface AIGenerationResponse {
  success: boolean;
  data: {
    captions?: AICaption[];
    hashtags?: string[];
    ideas?: string[];
    postingTimes?: PostingTime[];
    analysis?: {
      viralPotential: number;
      targetAudience: string[];
      suggestedImprovements: string[];
      competitorInsights: string[];
    };
  };
  error?: string;
  tokensUsed?: number;
}

export interface SocialMediaPost {
  platform: string;
  content: {
    text: string;
    mediaUrls: string[];
    hashtags: string[];
  };
  scheduling?: {
    publishAt: string;
    timezone: string;
  };
}

export interface UploadProgress {
  contentId: string;
  progress: number;
  stage: 'uploading' | 'processing' | 'analyzing' | 'complete' | 'error';
  message: string;
}

export interface Notification {
  id: string;
  userId: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  read: boolean;
  actionUrl?: string;
  createdAt: string;
}

export interface Plan {
  id: 'starter' | 'professional' | 'enterprise';
  name: string;
  price: number;
  features: string[];
  limits: {
    socialAccounts: number;
    postsPerMonth: number;
    aiGenerations: number;
    teamMembers: number;
    analyticsHistory: number; // days
  };
  recommended: boolean;
}

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}
