import axios from 'axios';
import { SocialMediaPost } from '@/types';

export class TikTokService {
  private accessToken: string;

  constructor(accessToken: string) {
    this.accessToken = accessToken;
  }

  async uploadVideo(videoBuffer: Buffer, post: SocialMediaPost) {
    try {
      // Step 1: Initialize upload
      const initResponse = await axios.post(
        'https://open.tiktokapis.com/v2/post/publish/video/init/',
        {
          post_info: {
            title: post.content.text.substring(0, 150),
            privacy_level: 'PUBLIC_TO_EVERYONE',
            disable_duet: false,
            disable_comment: false,
            disable_stitch: false,
            video_cover_timestamp_ms: 1000,
          },
          source_info: {
            source: 'FILE_UPLOAD',
            video_size: videoBuffer.length,
            chunk_size: videoBuffer.length,
            total_chunk_count: 1,
          },
        },
        {
          headers: {
            Authorization: `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      const { publish_id, upload_url } = initResponse.data.data;

      // Step 2: Upload video
      await axios.put(upload_url, videoBuffer, {
        headers: {
          'Content-Type': 'video/mp4',
          'Content-Length': videoBuffer.length,
        },
      });

      // Step 3: Publish
      const publishResponse = await axios.post(
        'https://open.tiktokapis.com/v2/post/publish/status/fetch/',
        {
          publish_id,
        },
        {
          headers: {
            Authorization: `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      return {
        success: true,
        postId: publish_id,
        url: publishResponse.data.data.share_url,
      };
    } catch (error: any) {
      console.error('TikTok upload error:', error);
      return {
        success: false,
        error: error.response?.data?.error?.message || error.message,
      };
    }
  }

  async getUserInfo() {
    try {
      const response = await axios.get('https://open.tiktokapis.com/v2/user/info/', {
        params: {
          fields: 'open_id,union_id,avatar_url,display_name,follower_count,following_count,likes_count,video_count',
        },
        headers: {
          Authorization: `Bearer ${this.accessToken}`,
        },
      });

      const user = response.data.data.user;

      return {
        followers: user.follower_count || 0,
        following: user.following_count || 0,
        likes: user.likes_count || 0,
        videos: user.video_count || 0,
        name: user.display_name,
      };
    } catch (error: any) {
      console.error('TikTok user info error:', error);
      throw error;
    }
  }

  async getVideoStats(videoId: string) {
    try {
      const response = await axios.post(
        'https://open.tiktokapis.com/v2/video/query/',
        {
          filters: {
            video_ids: [videoId],
          },
        },
        {
          headers: {
            Authorization: `Bearer ${this.accessToken}`,
            'Content-Type': 'application/json',
          },
        }
      );

      const video = response.data.data.videos[0];

      return {
        views: video.view_count || 0,
        likes: video.like_count || 0,
        comments: video.comment_count || 0,
        shares: video.share_count || 0,
      };
    } catch (error: any) {
      console.error('TikTok video stats error:', error);
      throw error;
    }
  }

  static getAuthUrl(): string {
    const clientKey = process.env.TIKTOK_CLIENT_KEY;
    const redirectUri = `${process.env.NEXT_PUBLIC_APP_URL}/api/social/tiktok/callback`;
    const scope = 'user.info.basic,video.list,video.upload';
    const state = Math.random().toString(36).substring(7);

    return `https://www.tiktok.com/v2/auth/authorize?client_key=${clientKey}&scope=${scope}&response_type=code&redirect_uri=${redirectUri}&state=${state}`;
  }

  static async getAccessToken(code: string) {
    try {
      const response = await axios.post('https://open.tiktokapis.com/v2/oauth/token/', {
        client_key: process.env.TIKTOK_CLIENT_KEY,
        client_secret: process.env.TIKTOK_CLIENT_SECRET,
        code,
        grant_type: 'authorization_code',
        redirect_uri: `${process.env.NEXT_PUBLIC_APP_URL}/api/social/tiktok/callback`,
      });

      return {
        accessToken: response.data.data.access_token,
        refreshToken: response.data.data.refresh_token,
        expiresIn: response.data.data.expires_in,
      };
    } catch (error: any) {
      console.error('TikTok token error:', error);
      throw error;
    }
  }
}

export default TikTokService;
