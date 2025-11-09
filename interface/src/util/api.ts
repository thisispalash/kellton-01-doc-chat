/**
 * API client for making requests to the backend using axios.
 */

import apiClient, { apiHelpers, ApiError, AuthError, NetworkError } from '../lib/axios';

interface ApiOptions {
  token?: string;
  headers?: Record<string, string>;
}

// Re-export error types for backward compatibility
export { ApiError, AuthError, NetworkError };

// Helper function for API requests (maintaining similar interface for easier migration)
async function apiRequest<T>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const { token, headers = {} } = options;

  const config = {
    headers: {
      ...headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  };

  try {
    const response = await apiClient.get(endpoint, config);
    return response.data;
  } catch (error) {
    if (error instanceof ApiError || error instanceof AuthError || error instanceof NetworkError) {
      throw error;
    }
    throw new Error('Request failed');
  }
}

// Helper function for POST requests
async function apiPost<T>(
  endpoint: string,
  data?: any,
  options: ApiOptions = {}
): Promise<T> {
  const { token, headers = {} } = options;

  const config = {
    headers: {
      ...headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  };

  try {
    const response = await apiClient.post(endpoint, data, config);
    return response.data;
  } catch (error) {
    if (error instanceof ApiError || error instanceof AuthError || error instanceof NetworkError) {
      throw error;
    }
    throw new Error('Request failed');
  }
}

// Helper function for PUT requests
async function apiPut<T>(
  endpoint: string,
  data?: any,
  options: ApiOptions = {}
): Promise<T> {
  const { token, headers = {} } = options;

  const config = {
    headers: {
      ...headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  };

  try {
    const response = await apiClient.put(endpoint, data, config);
    return response.data;
  } catch (error) {
    if (error instanceof ApiError || error instanceof AuthError || error instanceof NetworkError) {
      throw error;
    }
    throw new Error('Request failed');
  }
}

// Helper function for DELETE requests
async function apiDelete<T>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const { token, headers = {} } = options;

  const config = {
    headers: {
      ...headers,
      ...(token && { Authorization: `Bearer ${token}` }),
    },
  };

  try {
    const response = await apiClient.delete(endpoint, config);
    return response.data;
  } catch (error) {
    if (error instanceof ApiError || error instanceof AuthError || error instanceof NetworkError) {
      throw error;
    }
    throw new Error('Request failed');
  }
}

// Auth API
export const authApi = {
  checkPassword: (password: string) =>
    apiPost<{ exists: boolean; user_id?: number }>('/api/auth/check-password', { password }),

  login: (username: string, password: string) =>
    apiPost<{ session_token: string; user: any; expires_at: string }>('/api/auth/login', { username, password }),

  register: (username: string, password: string) =>
    apiPost<{ session_token: string; user: any; expires_at: string }>('/api/auth/register', { username, password }),

  logout: (token: string) =>
    apiPost('/api/auth/logout', undefined, { token }),

  me: (token: string) =>
    apiRequest<any>('/api/auth/me', { token }),
};

// Conversations API
export const conversationsApi = {
  list: (token: string) =>
    apiRequest<any[]>('/api/conversations', { token }),

  create: (token: string, title?: string) =>
    apiPost<any>('/api/conversations', { title }, { token }),

  get: (token: string, conversationId: number) =>
    apiRequest<any>(`/api/conversations/${conversationId}`, { token }),

  update: (token: string, conversationId: number, title: string) =>
    apiPut<any>(`/api/conversations/${conversationId}`, { title }, { token }),

  delete: (token: string, conversationId: number) =>
    apiDelete<{ message: string }>(`/api/conversations/${conversationId}`, { token }),

  attachDocument: (token: string, conversationId: number, documentId: number) =>
    apiPost<any>(`/api/conversations/${conversationId}/documents`, { document_id: documentId }, { token }),

  detachDocument: (token: string, conversationId: number, documentId: number) =>
    apiDelete<{ message: string }>(`/api/conversations/${conversationId}/documents/${documentId}`, { token }),
};

// Settings API
export const settingsApi = {
  getApiKeys: (token: string) =>
    apiRequest<any[]>('/api/settings/api-keys', { token }),

  saveApiKey: (token: string, provider: string, apiKey: string) =>
    apiPost<{ message: string }>('/api/settings/api-keys', { provider, api_key: apiKey }, { token }),

  deleteApiKey: (token: string, provider: string) =>
    apiDelete<{ message: string }>(`/api/settings/api-keys/${provider}`, { token }),
};

// Documents API
export const documentsApi = {
  list: (token: string) =>
    apiRequest<any[]>('/api/documents', { token }),

  upload: async (token: string, file: File) => {
    try {
      const response = await apiHelpers.uploadFile('/api/documents/upload', file, token);
      return response.data;
    } catch (error) {
      if (error instanceof ApiError || error instanceof AuthError || error instanceof NetworkError) {
        throw error;
      }
      throw new Error('Upload failed');
    }
  },

  get: (token: string, documentId: number) =>
    apiRequest<any>(`/api/documents/${documentId}`, { token }),

  delete: (token: string, documentId: number) =>
    apiDelete<{ message: string }>(`/api/documents/${documentId}`, { token }),
};

