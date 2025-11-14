'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { useAuth } from './AuthContext';
import { conversationsApi, documentsApi } from '@/util/api';

interface Message {
  id: number;
  conversation_id: number;
  role: 'user' | 'assistant';
  content: string;
  model_used?: string;
  timestamp: string;
}

interface Conversation {
  id: number;
  user_id: number;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
  messages?: Message[];
  attached_documents?: Document[];
}

interface Document {
  id: number;
  user_id: number;
  filename: string;
  chroma_collection_id: string;
  uploaded_at: string;
}

interface ChatContextType {
  conversations: Conversation[];
  documents: Document[];
  currentConversation: Conversation | null;
  selectedDocuments: number[];
  isLoading: boolean;
  viewingDocument: { id: number; filename: string } | null;
  setViewingDocument: (doc: { id: number; filename: string } | null) => void;
  loadConversations: () => Promise<void>;
  loadDocuments: () => Promise<void>;
  createConversation: (title?: string) => Promise<Conversation>;
  selectConversation: (conversationId: number) => Promise<void>;
  deleteConversation: (conversationId: number) => Promise<void>;
  uploadDocument: (file: File) => Promise<void>;
  deleteDocument: (documentId: number) => Promise<void>;
  toggleDocumentSelection: (documentId: number) => void;
  clearDocumentSelection: () => void;
  refreshCurrentConversation: () => Promise<void>;
  attachDocument: (conversationId: number, documentId: number) => Promise<void>;
  detachDocument: (conversationId: number, documentId: number) => Promise<void>;
  memoryEnabled: boolean;
  setMemoryEnabled: (enabled: boolean) => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [currentConversation, setCurrentConversation] = useState<Conversation | null>(null);
  const [selectedDocuments, setSelectedDocuments] = useState<number[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [viewingDocument, setViewingDocument] = useState<{ id: number; filename: string } | null>(null);
  const [memoryPreferences, setMemoryPreferences] = useState<Record<number, boolean>>({});

  const loadConversations = useCallback(async () => {
    if (!token) return;
    
    try {
      const convs = await conversationsApi.list(token);
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
    }
  }, [token]);

  const loadDocuments = useCallback(async () => {
    if (!token) return;
    
    try {
      const docs = await documentsApi.list(token);
      setDocuments(docs);
    } catch (error) {
      console.error('Failed to load documents:', error);
    }
  }, [token]);

  // Load conversations and documents when token is available
  useEffect(() => {
    if (token) {
      loadConversations();
      loadDocuments();
    } else {
      setConversations([]);
      setDocuments([]);
      setCurrentConversation(null);
      setSelectedDocuments([]);
      setMemoryPreferences({});
    }
  }, [token, loadConversations, loadDocuments]);

  const createConversation = async (title?: string): Promise<Conversation> => {
    if (!token) throw new Error('Not authenticated');
    
    const newConv = await conversationsApi.create(token, title);
    setConversations((prev) => [newConv, ...prev]);
    return newConv;
  };

  const selectConversation = async (conversationId: number) => {
    if (!token) return;
    
    // Clean up empty conversations before switching
    if (currentConversation && currentConversation.id !== conversationId) {
      const messageCount = currentConversation.messages?.length || currentConversation.message_count || 0;
      if (messageCount === 0) {
        try {
          await conversationsApi.delete(token, currentConversation.id);
          setConversations((prev) => prev.filter((c) => c.id !== currentConversation.id));
        } catch (error) {
          console.error('Failed to delete empty conversation:', error);
        }
      }
    }
    
    setIsLoading(true);
    try {
      const conv = await conversationsApi.get(token, conversationId);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to load conversation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const refreshCurrentConversation = async () => {
    if (!token || !currentConversation) return;
    
    try {
      const conv = await conversationsApi.get(token, currentConversation.id);
      setCurrentConversation(conv);
    } catch (error) {
      console.error('Failed to refresh conversation:', error);
    }
  };

  const deleteConversation = async (conversationId: number) => {
    if (!token) return;
    
    try {
      await conversationsApi.delete(token, conversationId);
      setConversations((prev) => prev.filter((c) => c.id !== conversationId));
      setMemoryPreferences((prev) => {
        const updated = { ...prev };
        delete updated[conversationId];
        return updated;
      });
      
      if (currentConversation?.id === conversationId) {
        setCurrentConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
      throw error;
    }
  };

  const uploadDocument = async (file: File) => {
    if (!token) throw new Error('Not authenticated');
    
    setIsLoading(true);
    try {
      const newDoc = await documentsApi.upload(token, file);
      setDocuments((prev) => [newDoc, ...prev]);
    } catch (error) {
      console.error('Failed to upload document:', error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const deleteDocument = async (documentId: number) => {
    if (!token) return;
    
    try {
      await documentsApi.delete(token, documentId);
      setDocuments((prev) => prev.filter((d) => d.id !== documentId));
      setSelectedDocuments((prev) => prev.filter((id) => id !== documentId));
    } catch (error) {
      console.error('Failed to delete document:', error);
      throw error;
    }
  };

  const toggleDocumentSelection = (documentId: number) => {
    setSelectedDocuments((prev) =>
      prev.includes(documentId)
        ? prev.filter((id) => id !== documentId)
        : [...prev, documentId]
    );
  };

  const clearDocumentSelection = () => {
    setSelectedDocuments([]);
  };

  const attachDocument = async (conversationId: number, documentId: number) => {
    if (!token) throw new Error('Not authenticated');
    
    try {
      await conversationsApi.attachDocument(token, conversationId, documentId);
      // Refresh conversation to get updated attached documents
      if (currentConversation?.id === conversationId) {
        await refreshCurrentConversation();
      }
    } catch (error) {
      console.error('Failed to attach document:', error);
      throw error;
    }
  };

  const detachDocument = async (conversationId: number, documentId: number) => {
    if (!token) throw new Error('Not authenticated');
    
    try {
      await conversationsApi.detachDocument(token, conversationId, documentId);
      // Refresh conversation to get updated attached documents
      if (currentConversation?.id === conversationId) {
        await refreshCurrentConversation();
      }
    } catch (error) {
      console.error('Failed to detach document:', error);
      throw error;
    }
  };

  const memoryEnabled = currentConversation
    ? memoryPreferences[currentConversation.id] ?? true
    : true;

  const setMemoryEnabled = (enabled: boolean) => {
    if (!currentConversation) return;
    setMemoryPreferences((prev) => ({
      ...prev,
      [currentConversation.id]: enabled,
    }));
  };

  return (
    <ChatContext.Provider
      value={{
        conversations,
        documents,
        currentConversation,
        selectedDocuments,
        isLoading,
        viewingDocument,
        setViewingDocument,
        loadConversations,
        loadDocuments,
        createConversation,
        selectConversation,
        deleteConversation,
        uploadDocument,
        deleteDocument,
        toggleDocumentSelection,
        clearDocumentSelection,
        refreshCurrentConversation,
        attachDocument,
        detachDocument,
        memoryEnabled,
        setMemoryEnabled,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error('useChat must be used within a ChatProvider');
  }
  return context;
}

