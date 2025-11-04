'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { useChat } from '@/context/ChatContext';
import Sidebar from '@/components/Sidebar';
import ChatArea from '@/components/ChatArea';
import DocumentViewer from '@/components/DocumentViewer';
import { ResizableHandle, ResizablePanel, ResizablePanelGroup } from '@/components/ui/resizable';

export default function HomePage() {
  const { user, isLoading } = useAuth();
  const { currentConversation, createConversation, selectConversation, conversations, viewingDocument, setViewingDocument } = useChat();
  const router = useRouter();
  const [isInitialized, setIsInitialized] = useState(false);

  useEffect(() => {
    if (!isLoading && !user) {
      router.push('/');
    }
  }, [user, isLoading, router]);

  // Auto-create conversation if none selected
  useEffect(() => {
    if (user && !isLoading && !isInitialized && !currentConversation) {
      // If there are existing conversations, select the most recent one
      if (conversations.length > 0) {
        selectConversation(conversations[0].id);
      } else {
        // Otherwise, create a new conversation
        createConversation().then((conv) => {
          selectConversation(conv.id);
        }).catch((err) => {
          console.error('Failed to create initial conversation:', err);
        });
      }
      setIsInitialized(true);
    }
  }, [user, isLoading, currentConversation, conversations, isInitialized, createConversation, selectConversation]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="h-screen flex overflow-hidden">
      <Sidebar />
      <div className="flex-1 h-full overflow-hidden">
        {viewingDocument ? (
          <ResizablePanelGroup direction="horizontal" className="h-full">
            <ResizablePanel defaultSize={40} minSize={30}>
              <DocumentViewer
                documentId={viewingDocument.id}
                filename={viewingDocument.filename}
                onClose={() => setViewingDocument(null)}
              />
            </ResizablePanel>
            <ResizableHandle withHandle />
            <ResizablePanel defaultSize={60}>
              <ChatArea />
            </ResizablePanel>
          </ResizablePanelGroup>
        ) : (
          <ChatArea />
        )}
      </div>
    </div>
  );
}

