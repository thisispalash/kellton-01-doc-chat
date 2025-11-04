/**
 * API client for making requests to the backend.
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

interface ApiOptions extends RequestInit {
  token?: string;
}

async function apiRequest<T>(
  endpoint: string,
  options: ApiOptions = {}
): Promise<T> {
  const { token, ...fetchOptions } = options;

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Request failed' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
}

// Auth API
export const authApi = {
  checkPassword: (password: string) =>
    apiRequest<{ exists: boolean; user_id?: number }>('/api/auth/check-password', {
      method: 'POST',
      body: JSON.stringify({ password }),
    }),

  login: (username: string, password: string) =>
    apiRequest<{ session_token: string; user: any; expires_at: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  register: (username: string, password: string) =>
    apiRequest<{ session_token: string; user: any; expires_at: string }>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    }),

  logout: (token: string) =>
    apiRequest('/api/auth/logout', {
      method: 'POST',
      token,
    }),

  me: (token: string) =>
    apiRequest<any>('/api/auth/me', {
      method: 'GET',
      token,
    }),
};

// Conversations API
export const conversationsApi = {
  list: (token: string) =>
    apiRequest<any[]>('/api/conversations', {
      method: 'GET',
      token,
    }),

  create: (token: string, title?: string) =>
    apiRequest<any>('/api/conversations', {
      method: 'POST',
      token,
      body: JSON.stringify({ title }),
    }),

  get: (token: string, conversationId: number) =>
    apiRequest<any>(`/api/conversations/${conversationId}`, {
      method: 'GET',
      token,
    }),

  update: (token: string, conversationId: number, title: string) =>
    apiRequest<any>(`/api/conversations/${conversationId}`, {
      method: 'PUT',
      token,
      body: JSON.stringify({ title }),
    }),

  delete: (token: string, conversationId: number) =>
    apiRequest<{ message: string }>(`/api/conversations/${conversationId}`, {
      method: 'DELETE',
      token,
    }),
};

// Documents API
export const documentsApi = {
  list: (token: string) =>
    apiRequest<any[]>('/api/documents', {
      method: 'GET',
      token,
    }),

  upload: async (token: string, file: File) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/documents/upload`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'Upload failed' }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }

    return response.json();
  },

  get: (token: string, documentId: number) =>
    apiRequest<any>(`/api/documents/${documentId}`, {
      method: 'GET',
      token,
    }),

  delete: (token: string, documentId: number) =>
    apiRequest<{ message: string }>(`/api/documents/${documentId}`, {
      method: 'DELETE',
      token,
    }),
};

