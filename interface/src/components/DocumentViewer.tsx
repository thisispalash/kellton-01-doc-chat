'use client';

import { useState, useEffect } from 'react';
import { Button } from './ui/button';
import { X, FileText, Loader2 } from 'lucide-react';
import { apiHelpers, ApiError, AuthError, NetworkError } from '../lib/axios';

interface DocumentViewerProps {
  documentId: number;
  filename: string;
  onClose: () => void;
}

export default function DocumentViewer({ documentId, filename, onClose }: DocumentViewerProps) {
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchPdf = async () => {
      const token = localStorage.getItem('session_token');
      if (!token) {
        setError(true);
        setIsLoading(false);
        return;
      }

      try {
        const response = await apiHelpers.downloadFile(`/api/documents/${documentId}/view`, token);
        const blob = new Blob([response.data], { type: 'application/pdf' });
        const url = URL.createObjectURL(blob);
        setPdfUrl(url);
        setIsLoading(false);
      } catch (err) {
        console.error('Error loading PDF:', err);
        if (err instanceof AuthError) {
          // Token might be invalid, clear it
          localStorage.removeItem('session_token');
        }
        setError(true);
        setIsLoading(false);
      }
    };

    fetchPdf();

    // Cleanup blob URL on unmount
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [documentId]);

  return (
    <div className="h-full flex flex-col bg-background border-r">
      <div className="p-3 border-b flex items-center justify-between bg-muted/30">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <FileText className="w-4 h-4 flex-shrink-0" />
          <h3 className="font-semibold truncate text-sm">{filename}</h3>
        </div>
        <Button variant="ghost" size="sm" onClick={onClose}>
          <X className="w-4 h-4" />
        </Button>
      </div>
      <div className="flex-1 overflow-hidden bg-muted/10">
        {isLoading ? (
          <div className="w-full h-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 animate-spin text-muted-foreground" />
          </div>
        ) : pdfUrl && !error ? (
          <iframe
            src={pdfUrl}
            className="w-full h-full border-0"
            title={filename}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center">
            <div className="text-center space-y-4 p-8 max-w-md">
              <FileText className="w-12 h-12 mx-auto text-muted-foreground" />
              <div>
                <p className="font-semibold mb-2">Document Attached</p>
                <p className="text-sm text-muted-foreground mb-1">
                  {filename}
                </p>
                <p className="text-xs text-muted-foreground">
                  This document is attached to the conversation and will be used for RAG when you send messages.
                </p>
              </div>
              <div className="text-xs text-muted-foreground pt-4 border-t">
                <p>Note: PDF preview may require additional browser configuration.</p>
                <p>The document embeddings are already loaded and ready for search.</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

