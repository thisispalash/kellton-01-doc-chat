"""LLM provider integrations with streaming support."""

from abc import ABC, abstractmethod
import openai
from anthropic import Anthropic
import google.generativeai as genai
from ..config import Config


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""
    
    @abstractmethod
    def stream_chat(self, messages, model):
        """Stream chat completion.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model name string
            
        Yields:
            Chunks of the response text
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI API provider."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def stream_chat(self, messages, model):
        """Stream OpenAI chat completion."""
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error with OpenAI: {str(e)}"


class AnthropicProvider(LLMProvider):
    """Anthropic API provider."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.ANTHROPIC_API_KEY
        self.client = Anthropic(api_key=self.api_key)
    
    def stream_chat(self, messages, model):
        """Stream Anthropic chat completion."""
        try:
            # Convert messages to Anthropic format
            # Anthropic requires system messages to be separate
            system_message = None
            anthropic_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    anthropic_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            kwargs = {
                'model': model,
                'messages': anthropic_messages,
                'max_tokens': 4096,
                'stream': True
            }
            
            if system_message:
                kwargs['system'] = system_message
            
            with self.client.messages.stream(**kwargs) as stream:
                for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            yield f"Error with Anthropic: {str(e)}"


class GoogleProvider(LLMProvider):
    """Google Gemini API provider."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.GOOGLE_API_KEY
        genai.configure(api_key=self.api_key)
    
    def stream_chat(self, messages, model):
        """Stream Google Gemini chat completion."""
        try:
            # Convert messages to Gemini format
            gemini_model = genai.GenerativeModel(model)
            
            # Gemini requires a specific format
            # Combine system and user messages into the prompt
            prompt_parts = []
            for msg in messages:
                if msg['role'] == 'system':
                    prompt_parts.append(f"System: {msg['content']}")
                elif msg['role'] == 'user':
                    prompt_parts.append(f"User: {msg['content']}")
                elif msg['role'] == 'assistant':
                    prompt_parts.append(f"Assistant: {msg['content']}")
            
            prompt = "\n\n".join(prompt_parts)
            
            response = gemini_model.generate_content(prompt, stream=True)
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
                    
        except Exception as e:
            yield f"Error with Google: {str(e)}"


class GrokProvider(LLMProvider):
    """Grok (xAI) API provider - uses OpenAI-compatible API."""
    
    def __init__(self, api_key=None):
        self.api_key = api_key or Config.GROK_API_KEY
        # Grok uses OpenAI-compatible API
        self.client = openai.OpenAI(
            api_key=self.api_key,
            base_url="https://api.x.ai/v1"
        )
    
    def stream_chat(self, messages, model):
        """Stream Grok chat completion."""
        try:
            stream = self.client.chat.completions.create(
                model=model,
                messages=messages,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            yield f"Error with Grok: {str(e)}"


# Provider registry
PROVIDERS = {
    'openai': OpenAIProvider,
    'anthropic': AnthropicProvider,
    'google': GoogleProvider,
    'grok': GrokProvider
}


def get_provider(provider_name):
    """Get an LLM provider by name.
    
    Args:
        provider_name: Name of the provider ('openai', 'anthropic', 'google', 'grok')
        
    Returns:
        LLMProvider instance
        
    Raises:
        ValueError if provider name is not recognized
    """
    provider_class = PROVIDERS.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}")
    return provider_class()


def get_provider_from_model(model):
    """Detect provider from model name.
    
    Args:
        model: Model name string (e.g., 'gpt-4', 'claude-3-opus')
        
    Returns:
        Provider name string
    """
    model_lower = model.lower()
    
    if 'gpt' in model_lower or 'o1' in model_lower:
        return 'openai'
    elif 'claude' in model_lower:
        return 'anthropic'
    elif 'gemini' in model_lower:
        return 'google'
    elif 'grok' in model_lower:
        return 'grok'
    else:
        # Default to OpenAI
        return 'openai'


def stream_llm_response(messages, model):
    """Stream a response from the appropriate LLM.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model name string
        
    Yields:
        Chunks of the response text
    """
    provider_name = get_provider_from_model(model)
    provider = get_provider(provider_name)
    
    yield from provider.stream_chat(messages, model)

