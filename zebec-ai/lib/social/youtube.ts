import { google } from 'googleapis';
import { SocialMediaPost } from '@/types';

const youtube = google.youtube('v3');

export class YouTubeService {
  private oauth2Client: any;

  constructor(accessToken: string, refreshToken?: string) {
    this.oauth2Client = new google.auth.OAuth2(
      process.env.YOUTUBE_CLIENT_ID,
      process.env.YOUTUBE_CLIENT_SECRET,
      `${process.env.NEXT_PUBLIC_APP_URL}/api/social/youtube/callback`
    );

    this.oauth2Client.setCredentials({
      access_token: accessToken,
      refresh_token: refreshToken,
    });
  }

  async uploadVideo(videoFile: Buffer, post: SocialMediaPost) {
    try {
      const response = await youtube.videos.insert({
        auth: this.oauth2Client,
        part: ['snippet', 'status'],
        requestBody: {
          snippet: {
            title: post.content.text.substring(0, 100),
            description: post.content.text,
            tags: post.content.hashtags.map(tag => tag.replace('#', '')),
            categoryId: '22', // People & Blogs
          },
          status: {
            privacyStatus: 'public',
            publishAt: post.scheduling?.publishAt,
          },
        },
        media: {
          body: videoFile,
        },
      });

      return {
        success: true,
        postId: response.data.id,
        url: `https://youtube.com/watch?v=${response.data.id}`,
      };
    } catch (error: any) {
      console.error('YouTube upload error:', error);
      return {
        success: false,
        error: error.message,
      };
    }
  }

  async getChannelStats() {
    try {
      const response = await youtube.channels.list({
        auth: this.oauth2Client,
        part: ['statistics', 'snippet'],
        mine: true,
      });

      const channel = response.data.items?.[0];
      if (!channel) throw new Error('Channel not found');

      return {
        followers: parseInt(channel.statistics?.subscriberCount || '0'),
        views: parseInt(channel.statistics?.viewCount || '0'),
        videos: parseInt(channel.statistics?.videoCount || '0'),
        name: channel.snippet?.title,
      };
    } catch (error: any) {
      console.error('YouTube stats error:', error);
      throw error;
    }
  }

  async getVideoAnalytics(videoId: string) {
    try {
      const response = await youtube.videos.list({
        auth: this.oauth2Client,
        part: ['statistics', 'snippet'],
        id: [videoId],
      });

      const video = response.data.items?.[0];
      if (!video) throw new Error('Video not found');

      return {
        views: parseInt(video.statistics?.viewCount || '0'),
        likes: parseInt(video.statistics?.likeCount || '0'),
        comments: parseInt(video.statistics?.commentCount || '0'),
        shares: 0, // YouTube API doesn't provide share count
      };
    } catch (error: any) {
      console.error('YouTube analytics error:', error);
      throw error;
    }
  }

  static async getAuthUrl(): Promise<string> {
    const oauth2Client = new google.auth.OAuth2(
      process.env.YOUTUBE_CLIENT_ID,
      process.env.YOUTUBE_CLIENT_SECRET,
      `${process.env.NEXT_PUBLIC_APP_URL}/api/social/youtube/callback`
    );

    const scopes = [
      'https://www.googleapis.com/auth/youtube.upload',
      'https://www.googleapis.com/auth/youtube.readonly',
      'https://www.googleapis.com/auth/youtube.force-ssl',
    ];

    return oauth2Client.generateAuthUrl({
      access_type: 'offline',
      scope: scopes,
      prompt: 'consent',
    });
  }

  static async getTokensFromCode(code: string) {
    const oauth2Client = new google.auth.OAuth2(
      process.env.YOUTUBE_CLIENT_ID,
      process.env.YOUTUBE_CLIENT_SECRET,
      `${process.env.NEXT_PUBLIC_APP_URL}/api/social/youtube/callback`
    );

    const { tokens } = await oauth2Client.getToken(code);
    return tokens;
  }
}

export default YouTubeService;
