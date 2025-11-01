import OpenAI from 'openai';
import { AIGenerationRequest, AIGenerationResponse, AICaption, PostingTime } from '@/types';

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
});

export async function generateCaptions(request: AIGenerationRequest): Promise<AICaption[]> {
  const { content, options } = request;
  
  const prompt = `Generate ${options?.count || 5} engaging social media captions for the following content:
  
Title: ${content.title || 'Untitled'}
Description: ${content.description || 'No description'}
Platform: ${content.platform || 'General'}
Target Audience: ${content.targetAudience || 'General audience'}
Tone: ${content.tone || 'Professional'}

Requirements:
- Make them attention-grabbing and viral-worthy
- Include relevant emojis ${options?.includeEmojis ? 'YES' : 'NO'}
- Maximum length: ${options?.maxLength || 280} characters
- Optimize for engagement and reach
- Vary the tone and style across captions

Return the captions in JSON format as an array of objects with: text, tone, length, score (0-100 for viral potential)`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: [
        {
          role: 'system',
          content: 'You are an expert social media content strategist specializing in viral content creation. Always respond with valid JSON.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.8,
      max_tokens: 2000,
      response_format: { type: 'json_object' },
    });

    const result = JSON.parse(response.choices[0].message.content || '{}');
    
    return (result.captions || []).map((caption: any, index: number) => ({
      id: `caption-${Date.now()}-${index}`,
      text: caption.text,
      platform: content.platform || 'general',
      tone: caption.tone || 'professional',
      length: caption.length || 'medium',
      score: caption.score || 75,
      hashtags: extractHashtags(caption.text),
    }));
  } catch (error) {
    console.error('Error generating captions:', error);
    throw error;
  }
}

export async function generateHashtags(request: AIGenerationRequest): Promise<string[]> {
  const { content, options } = request;
  
  const prompt = `Generate ${options?.count || 20} highly relevant and trending hashtags for:
  
Title: ${content.title || 'Untitled'}
Description: ${content.description || 'No description'}
Platform: ${content.platform || 'General'}

Requirements:
- Mix of popular and niche hashtags
- Include trending hashtags
- Optimize for discoverability
- Platform-specific best practices
- Return as a JSON array of strings`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: [
        {
          role: 'system',
          content: 'You are a social media hashtag expert. Always respond with valid JSON.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.7,
      max_tokens: 500,
      response_format: { type: 'json_object' },
    });

    const result = JSON.parse(response.choices[0].message.content || '{}');
    return result.hashtags || [];
  } catch (error) {
    console.error('Error generating hashtags:', error);
    throw error;
  }
}

export async function generateContentIdeas(request: AIGenerationRequest): Promise<string[]> {
  const { content, options } = request;
  
  const prompt = `Generate ${options?.count || 10} viral content ideas based on:
  
Current Content: ${content.title || 'General'}
Platform: ${content.platform || 'All platforms'}
Target Audience: ${content.targetAudience || 'General'}

Requirements:
- Highly engaging and shareable
- Trending topics and formats
- Platform-specific best practices
- Actionable and specific
- Return as a JSON array of strings`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: [
        {
          role: 'system',
          content: 'You are a viral content strategist. Always respond with valid JSON.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.9,
      max_tokens: 1000,
      response_format: { type: 'json_object' },
    });

    const result = JSON.parse(response.choices[0].message.content || '{}');
    return result.ideas || [];
  } catch (error) {
    console.error('Error generating content ideas:', error);
    throw error;
  }
}

export async function analyzeBestPostingTimes(request: AIGenerationRequest): Promise<PostingTime[]> {
  const { content } = request;
  
  const prompt = `Analyze and recommend the best posting times for:
  
Platform: ${content.platform || 'All platforms'}
Target Audience: ${content.targetAudience || 'General'}
Content Type: Video/Image

Provide 5 optimal posting times with:
- Day of week (0-6, 0=Sunday)
- Hour (0-23)
- Score (0-100)
- Reason for recommendation

Return as JSON with array of objects: dayOfWeek, hour, score, reason`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: [
        {
          role: 'system',
          content: 'You are a social media analytics expert. Always respond with valid JSON.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.5,
      max_tokens: 800,
      response_format: { type: 'json_object' },
    });

    const result = JSON.parse(response.choices[0].message.content || '{}');
    
    return (result.postingTimes || []).map((time: any, index: number) => ({
      platform: content.platform || 'general',
      dayOfWeek: time.dayOfWeek,
      hour: time.hour,
      score: time.score,
      reason: time.reason,
    }));
  } catch (error) {
    console.error('Error analyzing posting times:', error);
    throw error;
  }
}

export async function performFullContentAnalysis(request: AIGenerationRequest): Promise<any> {
  const { content } = request;
  
  const prompt = `Perform a comprehensive content analysis for:
  
Title: ${content.title || 'Untitled'}
Description: ${content.description || 'No description'}
Platform: ${content.platform || 'All platforms'}

Provide:
1. Viral potential score (0-100)
2. Target audience segments (array)
3. Suggested improvements (array)
4. Competitor insights (array)
5. Engagement predictions

Return as JSON with: viralPotential, targetAudience, suggestedImprovements, competitorInsights`;

  try {
    const response = await openai.chat.completions.create({
      model: 'gpt-4-turbo-preview',
      messages: [
        {
          role: 'system',
          content: 'You are an expert content analyst. Always respond with valid JSON.',
        },
        {
          role: 'user',
          content: prompt,
        },
      ],
      temperature: 0.6,
      max_tokens: 1500,
      response_format: { type: 'json_object' },
    });

    const result = JSON.parse(response.choices[0].message.content || '{}');
    return result;
  } catch (error) {
    console.error('Error performing content analysis:', error);
    throw error;
  }
}

// Helper functions
function extractHashtags(text: string): string[] {
  const hashtagRegex = /#[\w]+/g;
  const matches = text.match(hashtagRegex);
  return matches || [];
}

export async function generateAIContent(request: AIGenerationRequest): Promise<AIGenerationResponse> {
  try {
    let data: any = {};

    switch (request.type) {
      case 'caption':
        data.captions = await generateCaptions(request);
        break;
      case 'hashtags':
        data.hashtags = await generateHashtags(request);
        break;
      case 'ideas':
        data.ideas = await generateContentIdeas(request);
        break;
      case 'posting-times':
        data.postingTimes = await analyzeBestPostingTimes(request);
        break;
      case 'full-analysis':
        data.analysis = await performFullContentAnalysis(request);
        data.captions = await generateCaptions(request);
        data.hashtags = await generateHashtags(request);
        data.postingTimes = await analyzeBestPostingTimes(request);
        break;
      default:
        throw new Error('Invalid generation type');
    }

    return {
      success: true,
      data,
    };
  } catch (error: any) {
    return {
      success: false,
      data: {},
      error: error.message || 'AI generation failed',
    };
  }
}
