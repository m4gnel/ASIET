'use client';

import { useState, useEffect } from 'react';
import { 
  Zap, Video, TrendingUp, BarChart3, Calendar, Upload, 
  Sparkles, Target, Rocket, Shield, Users, Globe 
} from 'lucide-react';
import Link from 'next/link';

export default function HomePage() {
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    setIsVisible(true);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-950 to-indigo-950 text-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Zap className="w-8 h-8 text-yellow-400" />
            <span className="text-2xl font-bold">Zebec AI</span>
          </div>
          <div className="hidden md:flex items-center space-x-8">
            <a href="#features" className="hover:text-yellow-400 transition">Features</a>
            <a href="#pricing" className="hover:text-yellow-400 transition">Pricing</a>
            <a href="#demo" className="hover:text-yellow-400 transition">Demo</a>
          </div>
          <div className="flex items-center space-x-4">
            <Link href="/auth/login" className="px-4 py-2 hover:text-yellow-400 transition">
              Login
            </Link>
            <Link 
              href="/auth/signup" 
              className="px-6 py-2 bg-yellow-400 text-gray-900 rounded-full font-semibold hover:bg-yellow-300 transition shadow-lg"
            >
              Get Started
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className={`max-w-7xl mx-auto text-center transition-all duration-1000 ${isVisible ? 'opacity-100 translate-y-0' : 'opacity-0 translate-y-10'}`}>
          <div className="inline-block px-4 py-2 bg-yellow-400/20 border border-yellow-400 rounded-full text-yellow-400 text-sm font-semibold mb-6 animate-pulse">
            🚀 The Future of Content Monetization
          </div>
          
          <h1 className="text-6xl md:text-7xl lg:text-8xl font-extrabold mb-6 leading-tight">
            Dominate Social Media<br />
            <span className="gradient-text">with AI Power</span>
          </h1>
          
          <p className="text-xl md:text-2xl text-purple-200 mb-10 max-w-4xl mx-auto">
            Zebec AI enables creators and businesses to streamline content creation, 
            schedule across platforms, and maximize engagement using predictive analytics 
            and viral caption generation.
          </p>
          
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            <Link 
              href="/auth/signup"
              className="px-8 py-4 bg-yellow-400 text-gray-900 rounded-full font-bold text-lg hover:bg-yellow-300 transition transform hover:scale-105 shadow-xl shadow-yellow-400/30"
            >
              Start Your 7-Day Free Trial
            </Link>
            <button className="px-8 py-4 border-2 border-white/20 rounded-full font-bold text-lg hover:bg-white/10 transition">
              Watch Demo
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 max-w-4xl mx-auto">
            {[
              { value: '10M+', label: 'Content Pieces' },
              { value: '50K+', label: 'Active Creators' },
              { value: '99.9%', label: 'Uptime' },
              { value: '4.9/5', label: 'User Rating' },
            ].map((stat, index) => (
              <div key={index} className="glass rounded-xl p-6">
                <div className="text-3xl font-bold text-yellow-400 mb-2">{stat.value}</div>
                <div className="text-sm text-purple-300">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-6 bg-black/20">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-5xl font-bold mb-4">Powerful Features</h2>
            <p className="text-xl text-purple-200">Everything you need to dominate social media</p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {[
              {
                icon: <Video className="w-12 h-12 text-yellow-400" />,
                title: 'One-Click Publishing',
                description: 'Upload once, distribute instantly across all connected platforms: TikTok, YouTube Shorts, Instagram Reels, and X.',
              },
              {
                icon: <Sparkles className="w-12 h-12 text-yellow-400" />,
                title: 'AI Caption Generator',
                description: 'Generate viral captions, optimized hashtags, and compelling CTAs using advanced AI models.',
              },
              {
                icon: <BarChart3 className="w-12 h-12 text-yellow-400" />,
                title: 'Real-Time Analytics',
                description: 'Unified dashboard for tracking engagement, reach, and monetization performance across all channels.',
              },
              {
                icon: <Calendar className="w-12 h-12 text-yellow-400" />,
                title: 'Smart Scheduling',
                description: 'AI-powered posting time optimization based on your audience behavior and engagement patterns.',
              },
              {
                icon: <Target className="w-12 h-12 text-yellow-400" />,
                title: 'Audience Insights',
                description: 'Deep analytics on your audience demographics, interests, and engagement patterns.',
              },
              {
                icon: <Rocket className="w-12 h-12 text-yellow-400" />,
                title: 'Growth Automation',
                description: 'Automated engagement strategies to grow your following and increase reach organically.',
              },
            ].map((feature, index) => (
              <div 
                key={index}
                className="glass rounded-2xl p-8 hover:shadow-2xl hover:shadow-indigo-500/20 transition duration-300 transform hover:-translate-y-2"
              >
                <div className="mb-4">{feature.icon}</div>
                <h3 className="text-2xl font-bold mb-3">{feature.title}</h3>
                <p className="text-purple-200">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Platform Support */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto text-center">
          <h2 className="text-5xl font-bold mb-4">Supported Platforms</h2>
          <p className="text-xl text-purple-200 mb-12">Connect and manage all your social accounts in one place</p>
          
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-6">
            {[
              { name: 'YouTube', icon: '▶️', color: '#FF0000' },
              { name: 'Instagram', icon: '📷', color: '#E4405F' },
              { name: 'TikTok', icon: '🎵', color: '#000000' },
              { name: 'Twitter/X', icon: '🐦', color: '#1DA1F2' },
              { name: 'LinkedIn', icon: '💼', color: '#0A66C2' },
              { name: 'Facebook', icon: '👥', color: '#1877F2' },
            ].map((platform, index) => (
              <div 
                key={index}
                className="glass rounded-xl p-6 hover:scale-110 transition transform"
                style={{ borderColor: platform.color + '40' }}
              >
                <div className="text-4xl mb-2">{platform.icon}</div>
                <div className="font-semibold">{platform.name}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 bg-gradient-to-r from-yellow-400 to-pink-500">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-5xl font-bold text-gray-900 mb-6">
            Ready to Transform Your Social Media?
          </h2>
          <p className="text-xl text-gray-800 mb-8">
            Join thousands of creators and businesses using Zebec AI to grow their online presence
          </p>
          <Link 
            href="/auth/signup"
            className="inline-block px-10 py-5 bg-gray-900 text-white rounded-full font-bold text-xl hover:bg-gray-800 transition transform hover:scale-105 shadow-2xl"
          >
            Start Free Trial - No Credit Card Required
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Zap className="w-6 h-6 text-yellow-400" />
                <span className="text-xl font-bold">Zebec AI</span>
              </div>
              <p className="text-purple-300 text-sm">
                AI-powered social media management for the modern creator.
              </p>
            </div>
            
            <div>
              <h4 className="font-bold mb-4">Product</h4>
              <ul className="space-y-2 text-purple-300 text-sm">
                <li><a href="#" className="hover:text-yellow-400">Features</a></li>
                <li><a href="#" className="hover:text-yellow-400">Pricing</a></li>
                <li><a href="#" className="hover:text-yellow-400">API</a></li>
                <li><a href="#" className="hover:text-yellow-400">Integrations</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-bold mb-4">Company</h4>
              <ul className="space-y-2 text-purple-300 text-sm">
                <li><a href="#" className="hover:text-yellow-400">About</a></li>
                <li><a href="#" className="hover:text-yellow-400">Blog</a></li>
                <li><a href="#" className="hover:text-yellow-400">Careers</a></li>
                <li><a href="#" className="hover:text-yellow-400">Contact</a></li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-bold mb-4">Legal</h4>
              <ul className="space-y-2 text-purple-300 text-sm">
                <li><a href="#" className="hover:text-yellow-400">Privacy</a></li>
                <li><a href="#" className="hover:text-yellow-400">Terms</a></li>
                <li><a href="#" className="hover:text-yellow-400">Security</a></li>
              </ul>
            </div>
          </div>
          
          <div className="border-t border-white/10 pt-8 text-center text-purple-300 text-sm">
            © 2024 Zebec AI. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
