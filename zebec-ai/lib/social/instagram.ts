import axios from 'axios';
import { SocialMediaPost } from '@/types';

export class InstagramService {
  private accessToken: string;
  private accountId: string;

  constructor(accessToken: string, accountId: string) {
    this.accessToken = accessToken;
    this.accountId = accountId;
  }

  async publishPost(post: SocialMediaPost, mediaUrl: string) {
    try {
      // Step 1: Create media container
      const containerResponse = await axios.post(
        `https://graph.facebook.com/v18.0/${this.accountId}/media`,
        {
          image_url: mediaUrl,
          caption: `${post.content.text}\n\n${post.content.hashtags.join(' ')}`,
          access_token: this.accessToken,
        }
      );

      const creationId = containerResponse.data.id;

      // Step 2: Publish the container
      const publishResponse = await axios.post(
        `https://graph.facebook.com/v18.0/${this.accountId}/media_publish`,
        {
          creation_id: creationId,
          access_token: this.accessToken,
        }
      );

      return {
        success: true,
        postId: publishResponse.data.id,
        url: `https://www.instagram.com/p/${publishResponse.data.id}`,
      };
    } catch (error: any) {
      console.error('Instagram publish error:', error);
      return {
        success: false,
        error: error.response?.data?.error?.message || error.message,
      };
    }
  }

  async publishReel(post: SocialMediaPost, videoUrl: string) {
    try {
      // Create reel container
      const containerResponse = await axios.post(
        `https://graph.facebook.com/v18.0/${this.accountId}/media`,
        {
          media_type: 'REELS',
          video_url: videoUrl,
          caption: `${post.content.text}\n\n${post.content.hashtags.join(' ')}`,
          share_to_feed: true,
          access_token: this.accessToken,
        }
      );

      const creationId = containerResponse.data.id;

      // Wait for processing
      await this.waitForMediaProcessing(creationId);

      // Publish the reel
      const publishResponse = await axios.post(
        `https://graph.facebook.com/v18.0/${this.accountId}/media_publish`,
        {
          creation_id: creationId,
          access_token: this.accessToken,
        }
      );

      return {
        success: true,
        postId: publishResponse.data.id,
        url: `https://www.instagram.com/reel/${publishResponse.data.id}`,
      };
    } catch (error: any) {
      console.error('Instagram reel error:', error);
      return {
        success: false,
        error: error.response?.data?.error?.message || error.message,
      };
    }
  }

  private async waitForMediaProcessing(containerId: string, maxAttempts = 30) {
    for (let i = 0; i < maxAttempts; i++) {
      const response = await axios.get(
        `https://graph.facebook.com/v18.0/${containerId}`,
        {
          params: {
            fields: 'status_code',
            access_token: this.accessToken,
          },
        }
      );

      if (response.data.status_code === 'FINISHED') {
        return true;
      }

      if (response.data.status_code === 'ERROR') {
        throw new Error('Media processing failed');
      }

      // Wait 2 seconds before next check
      await new Promise(resolve => setTimeout(resolve, 2000));
    }

    throw new Error('Media processing timeout');
  }

  async getAccountStats() {
    try {
      const response = await axios.get(
        `https://graph.facebook.com/v18.0/${this.accountId}`,
        {
          params: {
            fields: 'followers_count,media_count,username',
            access_token: this.accessToken,
          },
        }
      );

      return {
        followers: response.data.followers_count || 0,
        posts: response.data.media_count || 0,
        name: response.data.username,
      };
    } catch (error: any) {
      console.error('Instagram stats error:', error);
      throw error;
    }
  }

  async getPostInsights(postId: string) {
    try {
      const response = await axios.get(
        `https://graph.facebook.com/v18.0/${postId}/insights`,
        {
          params: {
            metric: 'engagement,impressions,reach,saved',
            access_token: this.accessToken,
          },
        }
      );

      const insights = response.data.data.reduce((acc: any, item: any) => {
        acc[item.name] = item.values[0].value;
        return acc;
      }, {});

      return {
        engagement: insights.engagement || 0,
        impressions: insights.impressions || 0,
        reach: insights.reach || 0,
        saves: insights.saved || 0,
      };
    } catch (error: any) {
      console.error('Instagram insights error:', error);
      throw error;
    }
  }

  static getAuthUrl(): string {
    const appId = process.env.INSTAGRAM_APP_ID;
    const redirectUri = `${process.env.NEXT_PUBLIC_APP_URL}/api/social/instagram/callback`;
    const scope = 'instagram_basic,instagram_content_publish,pages_read_engagement';

    return `https://www.facebook.com/v18.0/dialog/oauth?client_id=${appId}&redirect_uri=${redirectUri}&scope=${scope}&response_type=code`;
  }

  static async getAccessToken(code: string) {
    try {
      const response = await axios.get('https://graph.facebook.com/v18.0/oauth/access_token', {
        params: {
          client_id: process.env.INSTAGRAM_APP_ID,
          client_secret: process.env.INSTAGRAM_APP_SECRET,
          redirect_uri: `${process.env.NEXT_PUBLIC_APP_URL}/api/social/instagram/callback`,
          code,
        },
      });

      return response.data.access_token;
    } catch (error: any) {
      console.error('Instagram token error:', error);
      throw error;
    }
  }
}

export default InstagramService;
