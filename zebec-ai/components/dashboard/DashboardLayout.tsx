'use client';

import { ReactNode, useState } from 'react';
import {
  Zap, Home, Upload, Calendar, BarChart3, Settings, 
  LogOut, Bell, Menu, X, Users, Video, TrendingUp
} from 'lucide-react';
import Link from 'next/link';

interface DashboardLayoutProps {
  children: ReactNode;
  user?: {
    name: string;
    email: string;
    photoURL?: string;
    plan: string;
  };
}

export default function DashboardLayout({ children, user }: DashboardLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notifications, setNotifications] = useState(3);

  const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: Home },
    { name: 'Upload Content', href: '/dashboard/upload', icon: Upload },
    { name: 'Content Library', href: '/dashboard/content', icon: Video },
    { name: 'Schedule', href: '/dashboard/schedule', icon: Calendar },
    { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
    { name: 'Platforms', href: '/dashboard/platforms', icon: Users },
    { name: 'Settings', href: '/dashboard/settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 z-50 h-full w-64 bg-gray-900 border-r border-white/10
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="flex items-center justify-between p-6 border-b border-white/10">
            <Link href="/" className="flex items-center space-x-2">
              <Zap className="w-8 h-8 text-yellow-400" />
              <span className="text-xl font-bold">Zebec AI</span>
            </Link>
            <button 
              onClick={() => setSidebarOpen(false)}
              className="lg:hidden"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
            {navigation.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="flex items-center space-x-3 px-4 py-3 rounded-lg hover:bg-white/5 transition group"
              >
                <item.icon className="w-5 h-5 text-purple-400 group-hover:text-yellow-400 transition" />
                <span className="font-medium">{item.name}</span>
              </Link>
            ))}
          </nav>

          {/* User section */}
          {user && (
            <div className="p-4 border-t border-white/10">
              <div className="flex items-center space-x-3 mb-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-yellow-400 to-pink-500 flex items-center justify-center font-bold">
                  {user.name.charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="font-semibold truncate">{user.name}</div>
                  <div className="text-xs text-purple-300 capitalize">{user.plan} Plan</div>
                </div>
              </div>
              <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 rounded-lg transition text-red-400">
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </div>
          )}
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:ml-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-gray-900/80 backdrop-blur-lg border-b border-white/10">
          <div className="flex items-center justify-between px-6 py-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="lg:hidden"
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="flex-1 max-w-2xl mx-4">
              <input
                type="search"
                placeholder="Search content, analytics, or settings..."
                className="w-full px-4 py-2 bg-gray-800 border border-white/10 rounded-lg focus:outline-none focus:border-yellow-400 transition"
              />
            </div>

            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <button className="relative p-2 hover:bg-white/5 rounded-lg transition">
                <Bell className="w-6 h-6" />
                {notifications > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-red-500 rounded-full text-xs flex items-center justify-center">
                    {notifications}
                  </span>
                )}
              </button>

              {/* Quick stats */}
              <div className="hidden md:flex items-center space-x-4 px-4 py-2 bg-white/5 rounded-lg">
                <div className="flex items-center space-x-2">
                  <TrendingUp className="w-4 h-4 text-green-400" />
                  <span className="text-sm font-semibold">+12.5%</span>
                </div>
                <div className="w-px h-6 bg-white/10" />
                <div className="text-sm text-purple-300">This Week</div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </div>
    </div>
  );
}
