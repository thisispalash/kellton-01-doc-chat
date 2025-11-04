'use client';

import { useChat } from '@/context/ChatContext';
import { Button } from './ui/button';
import { MessageSquare, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ConversationList() {
  const { conversations, currentConversation, selectConversation, deleteConversation, setViewingDocument } = useChat();

  const handleDelete = async (e: React.MouseEvent, conversationId: number) => {
    e.stopPropagation();
    if (confirm('Delete this conversation?')) {
      await deleteConversation(conversationId);
    }
  };

  const handleConversationClick = (conversationId: number) => {
    // Close document viewer when switching conversations
    setViewingDocument(null);
    selectConversation(conversationId);
  };

  return (
    <div className="space-y-1">
      <h3 className="text-sm font-semibold px-3 py-2 text-muted-foreground">
        Conversations
      </h3>
      <div className="space-y-1">
        {conversations.length === 0 ? (
          <p className="text-sm text-muted-foreground px-3 py-2">
            No conversations yet
          </p>
        ) : (
          conversations.map((conv) => (
              <div
                key={conv.id}
                className={cn(
                  'group flex items-center justify-between px-3 py-2 rounded-md cursor-pointer hover:bg-accent transition-colors',
                  currentConversation?.id === conv.id && 'bg-accent'
                )}
                onClick={() => handleConversationClick(conv.id)}
              >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <MessageSquare className="w-4 h-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{conv.title}</p>
                  <p className="text-xs text-muted-foreground">
                    {conv.message_count} messages
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => handleDelete(e, conv.id)}
              >
                <Trash2 className="w-4 h-4" />
              </Button>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

