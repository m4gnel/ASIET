import { NextRequest, NextResponse } from 'next/server';
import { generateAIContent } from '@/lib/ai/openai';
import { AIGenerationRequest } from '@/types';

export async function POST(request: NextRequest) {
  try {
    const body: AIGenerationRequest = await request.json();

    // Validate request
    if (!body.type) {
      return NextResponse.json(
        { success: false, error: 'Generation type is required' },
        { status: 400 }
      );
    }

    // Generate AI content
    const result = await generateAIContent(body);

    return NextResponse.json(result);
  } catch (error: any) {
    console.error('AI generation error:', error);
    return NextResponse.json(
      {
        success: false,
        error: error.message || 'Failed to generate AI content',
      },
      { status: 500 }
    );
  }
}

export const runtime = 'nodejs';
export const dynamic = 'force-dynamic';
