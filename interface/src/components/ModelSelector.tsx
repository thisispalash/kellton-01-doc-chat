'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

const MODELS = {
  'OpenAI': [
    { id: 'gpt-4', name: 'GPT-4' },
    { id: 'gpt-4-turbo', name: 'GPT-4 Turbo' },
    { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
  ],
  'Anthropic': [
    { id: 'claude-3-opus-20240229', name: 'Claude 3 Opus' },
    { id: 'claude-3-sonnet-20240229', name: 'Claude 3 Sonnet' },
    { id: 'claude-3-haiku-20240307', name: 'Claude 3 Haiku' },
  ],
  'Google': [
    { id: 'gemini-pro', name: 'Gemini Pro' },
    { id: 'gemini-pro-vision', name: 'Gemini Pro Vision' },
  ],
  'Grok': [
    { id: 'grok-beta', name: 'Grok Beta' },
  ],
};

interface ModelSelectorProps {
  value: string;
  onChange: (value: string) => void;
}

export default function ModelSelector({ value, onChange }: ModelSelectorProps) {
  // Find the current model name
  const currentModelName = Object.values(MODELS)
    .flat()
    .find((m) => m.id === value)?.name || value;

  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select model">
          {currentModelName}
        </SelectValue>
      </SelectTrigger>
      <SelectContent>
        {Object.entries(MODELS).map(([provider, models]) => (
          <div key={provider}>
            <div className="px-2 py-1.5 text-sm font-semibold text-muted-foreground">
              {provider}
            </div>
            {models.map((model) => (
              <SelectItem key={model.id} value={model.id}>
                {model.name}
              </SelectItem>
            ))}
          </div>
        ))}
      </SelectContent>
    </Select>
  );
}

