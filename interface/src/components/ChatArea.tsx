'use client';

import { useState, useEffect, useRef } from 'react';
import { useChat } from '@/context/ChatContext';
import { useWebSocket } from '@/context/WebSocketContext';
import MessageBubble from './MessageBubble';
import ModelSelector from './ModelSelector';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Send, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ChatArea() {
  const { currentConversation, selectedDocuments, documents, refreshCurrentConversation } = useChat();
  const { socket, isConnected, sendMessage } = useWebSocket();
  const [message, setMessage] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt-4');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [currentConversation?.messages, streamingContent]);

  useEffect(() => {
    if (!socket) return;

    const handleChatResponseStart = () => {
      setIsStreaming(true);
      setStreamingContent('');
    };

    const handleChatResponseChunk = (data: { chunk: string }) => {
      setStreamingContent((prev) => prev + data.chunk);
    };

    const handleChatResponseEnd = () => {
      setIsStreaming(false);
      setStreamingContent('');
      refreshCurrentConversation();
    };

    const handleError = (data: { message: string }) => {
      console.error('Chat error:', data.message);
      setIsStreaming(false);
      alert(`Error: ${data.message}`);
    };

    socket.on('chat_response_start', handleChatResponseStart);
    socket.on('chat_response_chunk', handleChatResponseChunk);
    socket.on('chat_response_end', handleChatResponseEnd);
    socket.on('error', handleError);

    return () => {
      socket.off('chat_response_start', handleChatResponseStart);
      socket.off('chat_response_chunk', handleChatResponseChunk);
      socket.off('chat_response_end', handleChatResponseEnd);
      socket.off('error', handleError);
    };
  }, [socket, refreshCurrentConversation]);

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!message.trim() || !currentConversation || isStreaming) return;

    const messageToSend = message.trim();
    setMessage('');

    sendMessage({
      conversation_id: currentConversation.id,
      message: messageToSend,
      model: selectedModel,
      selected_doc_ids: selectedDocuments,
    });

    // Refresh to show user message
    setTimeout(() => refreshCurrentConversation(), 100);
  };

  const selectedDocNames = documents
    .filter((doc) => selectedDocuments.includes(doc.id))
    .map((doc) => doc.filename)
    .join(', ');

  if (!currentConversation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="text-center space-y-4">
          <h2 className="text-2xl font-semibold">No conversation selected</h2>
          <p className="text-muted-foreground">
            Select a conversation from the sidebar or create a new one
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-background">
      {/* Header */}
      <div className="border-b p-4 flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold">{currentConversation.title}</h2>
          {selectedDocNames && (
            <p className="text-sm text-muted-foreground">
              Documents: {selectedDocNames}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <ModelSelector value={selectedModel} onChange={setSelectedModel} />
          <div
            className={cn(
              'w-2 h-2 rounded-full',
              isConnected ? 'bg-green-500' : 'bg-red-500'
            )}
            title={isConnected ? 'Connected' : 'Disconnected'}
          />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {currentConversation.messages?.map((msg) => (
          <MessageBubble
            key={msg.id}
            role={msg.role}
            content={msg.content}
            model={msg.model_used}
            timestamp={msg.timestamp}
          />
        ))}
        
        {isStreaming && streamingContent && (
          <MessageBubble
            role="assistant"
            content={streamingContent}
            model={selectedModel}
          />
        )}
        
        {isStreaming && !streamingContent && (
          <div className="flex items-center gap-2 text-muted-foreground">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Thinking...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t p-4">
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <Input
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Type your message..."
            disabled={isStreaming || !isConnected}
            className="flex-1"
          />
          <Button type="submit" disabled={isStreaming || !isConnected || !message.trim()}>
            <Send className="w-4 h-4" />
          </Button>
        </form>
      </div>
    </div>
  );
}

