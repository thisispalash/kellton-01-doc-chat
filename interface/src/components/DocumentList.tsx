'use client';

import { useState } from 'react';
import { useChat } from '@/context/ChatContext';
import { Button } from './ui/button';
import { FileText, Trash2, Plus, X, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function DocumentList() {
  const { documents, deleteDocument, currentConversation, attachDocument, detachDocument, setViewingDocument, createConversation, selectConversation, deleteConversation } = useChat();
  const [isAttaching, setIsAttaching] = useState<number | null>(null);

  const handleDelete = async (e: React.MouseEvent, documentId: number) => {
    e.stopPropagation();
    if (confirm('Delete this document and its embeddings?')) {
      await deleteDocument(documentId);
    }
  };

  const handleAttach = async (e: React.MouseEvent, documentId: number) => {
    e.stopPropagation();
    if (!currentConversation) return;

    setIsAttaching(documentId);
    try {
      await attachDocument(currentConversation.id, documentId);
    } catch (error) {
      console.error('Failed to attach document:', error);
    } finally {
      setIsAttaching(null);
    }
  };

  const handleDetach = async (e: React.MouseEvent, documentId: number) => {
    e.stopPropagation();
    if (!currentConversation) return;

    setIsAttaching(documentId);
    try {
      await detachDocument(currentConversation.id, documentId);
    } catch (error) {
      console.error('Failed to detach document:', error);
    } finally {
      setIsAttaching(null);
    }
  };

  const isAttached = (documentId: number) => {
    return currentConversation?.attached_documents?.some((doc) => doc.id === documentId) || false;
  };

  const handleDocumentClick = async (doc: { id: number; filename: string }) => {
    // Clean up empty current conversation before creating new one
    if (currentConversation) {
      const messageCount = currentConversation.messages?.length || currentConversation.message_count || 0;
      if (messageCount === 0) {
        try {
          await deleteConversation(currentConversation.id);
        } catch (error) {
          console.error('Failed to delete empty conversation:', error);
        }
      }
    }
    
    // Create a new conversation with this document attached
    try {
      const newConv = await createConversation(`Chat with ${doc.filename}`);
      await attachDocument(newConv.id, doc.id);
      await selectConversation(newConv.id);
      setViewingDocument({ id: doc.id, filename: doc.filename });
    } catch (error) {
      console.error('Failed to create conversation with document:', error);
    }
  };

  return (
    <div className="space-y-1">
      <h3 className="text-sm font-semibold px-3 py-2 text-muted-foreground">
        Documents
      </h3>
      <div className="space-y-1">
        {documents.length === 0 ? (
          <p className="text-sm text-muted-foreground px-3 py-2">
            No documents uploaded
          </p>
        ) : (
          documents.map((doc) => {
            const attached = isAttached(doc.id);
            return (
              <div
                key={doc.id}
                className={cn(
                  'group flex items-center justify-between px-3 py-2 rounded-md hover:bg-accent transition-colors cursor-pointer',
                  attached && 'bg-accent/50'
                )}
              >
                <div 
                  className="flex items-center gap-2 flex-1 min-w-0"
                  onClick={() => handleDocumentClick(doc)}
                >
                  {attached && <Check className="w-4 h-4 text-green-500 flex-shrink-0" />}
                  <FileText className="w-4 h-4 flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{doc.filename}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(doc.uploaded_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {currentConversation && (
                    <Button
                      variant="ghost"
                      size="sm"
                      className="opacity-0 group-hover:opacity-100 transition-opacity"
                      onClick={(e) => attached ? handleDetach(e, doc.id) : handleAttach(e, doc.id)}
                      disabled={isAttaching === doc.id}
                    >
                      {attached ? (
                        <X className="w-4 h-4" />
                      ) : (
                        <Plus className="w-4 h-4" />
                      )}
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="sm"
                    className="opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => handleDelete(e, doc.id)}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

