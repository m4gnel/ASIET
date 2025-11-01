import { GoogleGenerativeAI } from '@google/generative-ai';
import { AIGenerationRequest, AIGenerationResponse } from '@/types';

const genAI = new GoogleGenerativeAI(process.env.GOOGLE_GEMINI_API_KEY || '');

export async function generateWithGemini(request: AIGenerationRequest): Promise<AIGenerationResponse> {
  try {
    const model = genAI.getGenerativeModel({ model: 'gemini-pro' });
    
    let prompt = '';
    
    switch (request.type) {
      case 'caption':
        prompt = buildCaptionPrompt(request);
        break;
      case 'hashtags':
        prompt = buildHashtagPrompt(request);
        break;
      case 'ideas':
        prompt = buildIdeasPrompt(request);
        break;
      case 'posting-times':
        prompt = buildPostingTimesPrompt(request);
        break;
      case 'full-analysis':
        prompt = buildFullAnalysisPrompt(request);
        break;
      default:
        throw new Error('Invalid generation type');
    }

    const result = await model.generateContent(prompt);
    const response = await result.response;
    const text = response.text();
    
    // Parse JSON response
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    if (!jsonMatch) {
      throw new Error('Invalid JSON response from Gemini');
    }
    
    const data = JSON.parse(jsonMatch[0]);
    
    return {
      success: true,
      data,
    };
  } catch (error: any) {
    console.error('Gemini generation error:', error);
    return {
      success: false,
      data: {},
      error: error.message || 'Gemini generation failed',
    };
  }
}

function buildCaptionPrompt(request: AIGenerationRequest): string {
  const { content, options } = request;
  return `Generate ${options?.count || 5} engaging social media captions for:

Title: ${content.title || 'Untitled'}
Description: ${content.description || 'No description'}
Platform: ${content.platform || 'General'}
Tone: ${content.tone || 'Professional'}

Return ONLY valid JSON in this exact format:
{
  "captions": [
    {
      "text": "caption text here",
      "tone": "professional",
      "length": "medium",
      "score": 85
    }
  ]
}`;
}

function buildHashtagPrompt(request: AIGenerationRequest): string {
  const { content, options } = request;
  return `Generate ${options?.count || 20} trending hashtags for:

Title: ${content.title || 'Untitled'}
Platform: ${content.platform || 'General'}

Return ONLY valid JSON in this exact format:
{
  "hashtags": ["#hashtag1", "#hashtag2", ...]
}`;
}

function buildIdeasPrompt(request: AIGenerationRequest): string {
  const { content, options } = request;
  return `Generate ${options?.count || 10} viral content ideas for:

Topic: ${content.title || 'General'}
Platform: ${content.platform || 'All'}

Return ONLY valid JSON in this exact format:
{
  "ideas": ["idea 1", "idea 2", ...]
}`;
}

function buildPostingTimesPrompt(request: AIGenerationRequest): string {
  const { content } = request;
  return `Recommend 5 best posting times for:

Platform: ${content.platform || 'General'}
Audience: ${content.targetAudience || 'General'}

Return ONLY valid JSON in this exact format:
{
  "postingTimes": [
    {
      "dayOfWeek": 1,
      "hour": 18,
      "score": 95,
      "reason": "Peak engagement time"
    }
  ]
}`;
}

function buildFullAnalysisPrompt(request: AIGenerationRequest): string {
  const { content } = request;
  return `Analyze this content comprehensively:

Title: ${content.title || 'Untitled'}
Description: ${content.description || 'No description'}

Return ONLY valid JSON in this exact format:
{
  "analysis": {
    "viralPotential": 85,
    "targetAudience": ["audience1", "audience2"],
    "suggestedImprovements": ["improvement1", "improvement2"],
    "competitorInsights": ["insight1", "insight2"]
  },
  "captions": [...],
  "hashtags": [...],
  "postingTimes": [...]
}`;
}

export default generateWithGemini;
