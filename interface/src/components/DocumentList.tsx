'use client';

import { useChat } from '@/context/ChatContext';
import { Button } from './ui/button';
import { FileText, Trash2 } from 'lucide-react';
import { cn } from '@/lib/utils';

export default function DocumentList() {
  const { documents, selectedDocuments, toggleDocumentSelection, deleteDocument } = useChat();

  const handleDelete = async (e: React.MouseEvent, documentId: number) => {
    e.stopPropagation();
    if (confirm('Delete this document and its embeddings?')) {
      await deleteDocument(documentId);
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
          documents.map((doc) => (
            <div
              key={doc.id}
              className={cn(
                'group flex items-center justify-between px-3 py-2 rounded-md cursor-pointer hover:bg-accent transition-colors',
                selectedDocuments.includes(doc.id) && 'bg-accent'
              )}
              onClick={() => toggleDocumentSelection(doc.id)}
            >
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <input
                  type="checkbox"
                  checked={selectedDocuments.includes(doc.id)}
                  onChange={() => {}}
                  className="flex-shrink-0"
                />
                <FileText className="w-4 h-4 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{doc.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {new Date(doc.uploaded_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={(e) => handleDelete(e, doc.id)}
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

