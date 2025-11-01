import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Zebec AI - AI-Powered Social Media Management',
  description: 'Dominate social media with AI-powered content creation, scheduling, and analytics. Streamline your workflow across YouTube, Instagram, TikTok, and more.',
  keywords: 'social media management, AI content creation, social media scheduling, content analytics, YouTube automation, Instagram marketing, TikTok growth',
  authors: [{ name: 'Zebec AI' }],
  openGraph: {
    title: 'Zebec AI - AI-Powered Social Media Management',
    description: 'Dominate social media with AI-powered growth',
    type: 'website',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
