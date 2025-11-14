'use client';

import { useState, useEffect, useRef } from 'react';
import { useChat } from '@/context/ChatContext';
import { useWebSocket } from '@/context/WebSocketContext';
import MessageBubble from './MessageBubble';
import ModelSelector from './ModelSelector';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Send, Loader2, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function ChatArea() {
  const {
    currentConversation,
    refreshCurrentConversation,
    setViewingDocument,
    memoryEnabled,
    setMemoryEnabled,
  } = useChat();
  const { socket, isConnected, sendMessage } = useWebSocket();
  const [message, setMessage] = useState('');
  const [selectedModel, setSelectedModel] = useState('gpt-5-nano');
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
      memory_enabled: memoryEnabled,
    });

    // Refresh to show user message
    setTimeout(() => refreshCurrentConversation(), 100);
  };

  const attachedDocs = currentConversation?.attached_documents || [];
  const attachedDocNames = attachedDocs.map((doc) => doc.filename).join(', ');

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
    <div className="h-full flex flex-col bg-background">
      {/* Header */}
      <div className="border-b p-4 flex-shrink-0">
        <div className="flex items-center justify-between mb-2">
          <h2 className="text-lg font-semibold">{currentConversation.title}</h2>
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
        {attachedDocs.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {attachedDocs.map((doc) => (
              <div
                key={doc.id}
                className="inline-flex items-center gap-1 px-2 py-1 bg-accent rounded-md text-xs cursor-pointer hover:bg-accent/80 transition-colors"
                onClick={() => setViewingDocument({ id: doc.id, filename: doc.filename })}
                title="Click to view document"
              >
                <FileText className="w-3 h-3" />
                <span>{doc.filename}</span>
              </div>
            ))}
          </div>
        )}
        {attachedDocs.length === 0 && (
          <p className="text-xs text-muted-foreground mt-1">
            No documents attached. Attach documents from the sidebar to use RAG.
          </p>
        )}
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
      <div className="border-t p-4 flex-shrink-0 space-y-3">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <input
            type="checkbox"
            id="memory-toggle"
            className="h-4 w-4 accent-primary"
            checked={memoryEnabled}
            onChange={(e) => setMemoryEnabled(e.target.checked)}
            disabled={!currentConversation}
          />
          <label htmlFor="memory-toggle" className="cursor-pointer select-none">
            Include memory (adds ~0.5s latency but improves recall)
          </label>
        </div>
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

