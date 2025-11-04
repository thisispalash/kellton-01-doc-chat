'use client';

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';

const MODELS = {
  'OpenAI': [
    { id: 'gpt-5-nano', name: 'GPT-5 Nano' }, // $0.05/1M, $0.40/1M
  ],
  'Anthropic': [
    { id: 'claude-sonnet-4-5-20250929', name: 'Claude Sonnet 4.5' }, // $3/MTok, $15/MTok
    { id: 'claude-haiku-4-5-20251001', name: 'Claude Haiku 4.5' }, // $1/MTok, $5/MTok
    { id: 'claude-3-5-haiku-20241022', name: 'Claude Haiku 3.5' }, // $0.80/MTok, $4/MTok
  ],
  'Google': [
    { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash' }, // $0.30/1M, $2.50/1M
    { id: 'gemini-2.5-flash-preview-09-2025', name: 'Gemini 2.5 Flash Preview 09/2025' }, // $0.30/1M, $2.50/1M
    { id: 'gemini-2.5-flash-lite', name: 'Gemini 2.5 Flash Lite' }, // $0.10/1M, $0.40/1M
    { id: 'gemini-2.5-flash-lite-preview-09-2025', name: 'Gemini 2.5 Flash Lite Preview 09/2025' }, // $0.10/1M, $0.40/1M
  ],
  'Grok': [
    { id: 'grok-4-fast-reasoning', name: 'Grok 4 Fast Reasoning' }, // $0.20/1M, $0.50/1M
    { id: 'grok-4-0709', name: 'Grok 4' }, // $3/1M, $15/1M
    { id: 'grok-3-mini', name: 'Grok 3 Mini' }, // $0.30/1M, $0.50/1M
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

