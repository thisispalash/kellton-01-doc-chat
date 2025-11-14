import axios, { AxiosInstance, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

// Custom error types
export class ApiError extends Error {
  status: number;
  data?: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

export class NetworkError extends Error {
  constructor(message: string = 'Network request failed') {
    super(message);
    this.name = 'NetworkError';
  }
}

export class AuthError extends ApiError {
  constructor(message: string = 'Authentication failed') {
    super(message, 401);
    this.name = 'AuthError';
  }
}

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Check for token in localStorage (can be overridden by individual requests)
    const token = localStorage.getItem('session_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      // Server responded with error status
      const { status, data } = error.response;
      const message = (data as any)?.error || error.message || 'Request failed';

      if (status === 401) {
        throw new AuthError(message);
      }

      throw new ApiError(message, status, data);
    } else if (error.request) {
      // Network error
      throw new NetworkError('Network request failed. Please check your connection.');
    } else {
      // Something else happened
      throw new Error(error.message || 'An unexpected error occurred');
    }
  }
);

// Helper functions for common operations
export const apiHelpers = {
  setAuthToken: (token: string | null) => {
    if (token) {
      localStorage.setItem('session_token', token);
    } else {
      localStorage.removeItem('session_token');
    }
  },

  getAuthToken: (): string | null => {
    return localStorage.getItem('session_token');
  },

  clearAuthToken: () => {
    localStorage.removeItem('session_token');
  },

  // Helper for file uploads (returns FormData ready axios call)
  uploadFile: async (
    endpoint: string,
    file: File,
    token?: string,
    onProgress?: (progress: number) => void
  ) => {
    const formData = new FormData();
    formData.append('file', file);

    const config = {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...(token && { Authorization: `Bearer ${token}` }),
      },
      onUploadProgress: onProgress ? (progressEvent: any) => {
        const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        onProgress(percentCompleted);
      } : undefined,
    };

    return apiClient.post(endpoint, formData, config);
  },

  // Helper for downloading files as blob
  downloadFile: async (
    endpoint: string,
    token?: string,
    responseType: 'blob' | 'arraybuffer' = 'blob'
  ) => {
    const config = {
      responseType,
      headers: {
        ...(token && { Authorization: `Bearer ${token}` }),
      },
    };

    return apiClient.get(endpoint, config);
  },
};

export default apiClient;
