'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { settingsApi } from '@/util/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './ui/dialog';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Settings, Check, X } from 'lucide-react';

interface ProviderStatus {
  provider: string;
  configured: boolean;
  updated_at: string | null;
}

const PROVIDER_LABELS: Record<string, string> = {
  openai: 'OpenAI',
  anthropic: 'Anthropic',
  google: 'Google',
  grok: 'Grok (xAI)',
};

export default function SettingsDialog() {
  const { token } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const [providers, setProviders] = useState<ProviderStatus[]>([]);
  const [apiKeys, setApiKeys] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    if (isOpen && token) {
      loadApiKeys();
    }
  }, [isOpen, token]);

  const loadApiKeys = async () => {
    if (!token) return;

    setIsLoading(true);
    try {
      const data = await settingsApi.getApiKeys(token);
      setProviders(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load API keys');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSaveApiKey = async (provider: string) => {
    if (!token || !apiKeys[provider]) return;

    setIsSaving(true);
    setError('');
    setSuccess('');

    try {
      await settingsApi.saveApiKey(token, provider, apiKeys[provider]);
      setSuccess(`${PROVIDER_LABELS[provider]} API key saved successfully`);
      await loadApiKeys();
      setApiKeys((prev) => ({ ...prev, [provider]: '' }));
    } catch (err: any) {
      setError(err.message || 'Failed to save API key');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteApiKey = async (provider: string) => {
    if (!token) return;

    if (!confirm(`Delete ${PROVIDER_LABELS[provider]} API key?`)) return;

    setIsSaving(true);
    setError('');
    setSuccess('');

    try {
      await settingsApi.deleteApiKey(token, provider);
      setSuccess(`${PROVIDER_LABELS[provider]} API key deleted successfully`);
      await loadApiKeys();
    } catch (err: any) {
      setError(err.message || 'Failed to delete API key');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" size="sm">
          <Settings className="w-4 h-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
          <DialogDescription>
            Manage your API keys for different LLM providers. Your keys are encrypted and stored securely.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <p className="text-center py-4">Loading...</p>
        ) : (
          <div className="space-y-6">
            {providers.map((providerStatus) => (
              <div key={providerStatus.provider} className="space-y-2">
                <div className="flex items-center justify-between">
                  <Label htmlFor={providerStatus.provider} className="text-base">
                    {PROVIDER_LABELS[providerStatus.provider]}
                  </Label>
                  {providerStatus.configured ? (
                    <div className="flex items-center gap-2">
                      <Check className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-green-500">Configured</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => handleDeleteApiKey(providerStatus.provider)}
                        disabled={isSaving}
                      >
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ) : (
                    <span className="text-sm text-muted-foreground">Not configured</span>
                  )}
                </div>
                <div className="flex gap-2">
                  <Input
                    id={providerStatus.provider}
                    type="password"
                    placeholder={`Enter ${PROVIDER_LABELS[providerStatus.provider]} API key`}
                    value={apiKeys[providerStatus.provider] || ''}
                    onChange={(e) =>
                      setApiKeys((prev) => ({
                        ...prev,
                        [providerStatus.provider]: e.target.value,
                      }))
                    }
                    disabled={isSaving}
                  />
                  <Button
                    onClick={() => handleSaveApiKey(providerStatus.provider)}
                    disabled={isSaving || !apiKeys[providerStatus.provider]}
                  >
                    Save
                  </Button>
                </div>
                {providerStatus.updated_at && (
                  <p className="text-xs text-muted-foreground">
                    Last updated: {new Date(providerStatus.updated_at).toLocaleString()}
                  </p>
                )}
              </div>
            ))}

            {error && <p className="text-sm text-red-500">{error}</p>}
            {success && <p className="text-sm text-green-500">{success}</p>}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}

