import type { Metadata } from 'next';
import { Geist, Geist_Mono } from 'next/font/google';
import './globals.css';

import { cn } from '@/lib/utils';
import { AuthProvider } from '@/context/AuthContext';
import { WebSocketProvider } from '@/context/WebSocketContext';
import { ChatProvider } from '@/context/ChatContext';

const geistSans = Geist({
  variable: '--font-geist-sans',
  subsets: ['latin'],
});

const geistMono = Geist_Mono({
  variable: '--font-geist-mono',
  subsets: ['latin'],
});

export const metadata: Metadata = {
  title: 'Doc Chat',
  description: 'Chat with your documents using AI',
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body
        className={cn(
          geistSans.variable,
          geistMono.variable,
          'antialiased',
          'bg-background text-foreground',
          'min-h-screen w-full',
        )}
      >
        <AuthProvider>
          <WebSocketProvider>
            <ChatProvider>
              {children}
            </ChatProvider>
          </WebSocketProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
