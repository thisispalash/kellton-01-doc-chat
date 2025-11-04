'use client';

import { useAuth } from '@/context/AuthContext';
import { useChat } from '@/context/ChatContext';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import ConversationList from './ConversationList';
import DocumentList from './DocumentList';
import DocumentUpload from './DocumentUpload';
import { Plus, LogOut } from 'lucide-react';
import { useRouter } from 'next/navigation';

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { createConversation, selectConversation } = useChat();
  const router = useRouter();

  const handleNewConversation = async () => {
    try {
      const newConv = await createConversation();
      selectConversation(newConv.id);
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push('/');
  };

  return (
    <div className="w-80 border-r bg-muted/10 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-xl font-bold">Doc Chat</h1>
          <Button variant="ghost" size="sm" onClick={handleLogout}>
            <LogOut className="w-4 h-4" />
          </Button>
        </div>
        <p className="text-sm text-muted-foreground">
          Welcome, {user?.username}
        </p>
      </div>

      {/* Actions */}
      <div className="p-4 space-y-2">
        <Button onClick={handleNewConversation} className="w-full">
          <Plus className="w-4 h-4 mr-2" />
          New Conversation
        </Button>
        <DocumentUpload />
      </div>

      <Separator />

      {/* Lists */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6">
        <ConversationList />
        <Separator />
        <DocumentList />
      </div>
    </div>
  );
}

