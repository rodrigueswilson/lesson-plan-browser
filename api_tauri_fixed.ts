// Fixed API client for Tauri
// Replace frontend/src/lib/api.ts with this

import { fetch } from '@tauri-apps/api/http';

const API_BASE_URL = 'http://10.0.2.2:8000/api';

// Types
export interface User {
  id: string;
  name: string;
  email?: string;
  base_path_override?: string;
  created_at: string;
  updated_at: string;
}

export interface ClassSlot {
  id: string;
  user_id: string;
  slot_number: number;
  subject: string;
  grade: string;
  homeroom?: string;
  proficiency_levels?: string;
  primary_teacher_name?: string;
  primary_teacher_file_pattern?: string;
  display_order?: number;
  created_at: string;
  updated_at: string;
}

export interface WeeklyPlan {
  id: string;
  user_id: string;
  week_of: string;
  generated_at: string;
  output_file?: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string;
}

export interface BatchProcessResult {
  success: boolean;
  plan_id?: string;
  output_file?: string;
  processed_slots: number;
  failed_slots: number;
  errors?: Array<{ slot: number; subject: string; error: string }>;
}

// Helper to make HTTP requests using Tauri's fetch
async function request<T>(method: string, url: string, body?: any): Promise<{ data: T }> {
  try {
    console.log(`[API] ${method} ${url}`, body ? { body } : '');
    
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
      },
      body: body ? JSON.stringify(body) : undefined,
      timeout: 120,
    });

    console.log(`[API] Response status:`, response.status);
    console.log(`[API] Response ok:`, response.ok);
    console.log(`[API] Response data:`, response.data);

    if (!response.ok) {
      const errorMsg = typeof response.data === 'object' 
        ? JSON.stringify(response.data) 
        : String(response.data);
      console.error(`[API] HTTP Error ${response.status}:`, errorMsg);
      throw new Error(`HTTP ${response.status}: ${errorMsg}`);
    }

    return { data: response.data as T };
  } catch (error: any) {
    console.error(`[API] Request failed:`, error);
    console.error(`[API] Error type:`, typeof error);
    console.error(`[API] Error message:`, error.message);
    console.error(`[API] Error stack:`, error.stack);
    
    // Re-throw with more context
    const errorMessage = error.message || error.toString() || 'Unknown error';
    throw new Error(`API request failed: ${errorMessage}`);
  }
}

// User API
export const userApi = {
  list: () => request<User[]>('GET', `${API_BASE_URL}/users`),
  
  get: (userId: string) => request<User>('GET', `${API_BASE_URL}/users/${userId}`),
  
  create: (name: string, email?: string) => 
    request<User>('POST', `${API_BASE_URL}/users`, { name, email }),
  
  update: (userId: string, data: Partial<User>) =>
    request<User>('PUT', `${API_BASE_URL}/users/${userId}`, data),
  
  updateBasePath: (userId: string, basePath: string) =>
    request<User>('PUT', `${API_BASE_URL}/users/${userId}?base_path_override=${encodeURIComponent(basePath)}`),
};

// Class Slots API
export const slotApi = {
  list: (userId: string) => 
    request<ClassSlot[]>('GET', `${API_BASE_URL}/users/${userId}/slots`),
  
  create: (userId: string, slot: Omit<ClassSlot, 'id' | 'user_id' | 'created_at' | 'updated_at'>) =>
    request<ClassSlot>('POST', `${API_BASE_URL}/users/${userId}/slots`, slot),
  
  update: (slotId: string, data: Partial<ClassSlot>) =>
    request<ClassSlot>('PUT', `${API_BASE_URL}/slots/${slotId}`, data),
  
  delete: (slotId: string) =>
    request<void>('DELETE', `${API_BASE_URL}/slots/${slotId}`),
};

// Weekly Plans API
export const planApi = {
  list: (userId: string, limit = 50) =>
    request<WeeklyPlan[]>('GET', `${API_BASE_URL}/users/${userId}/plans?limit=${limit}`),
  
  process: (userId: string, weekOf: string, provider = 'openai') =>
    request<BatchProcessResult>('POST', `${API_BASE_URL}/process-week`, {
      user_id: userId,
      week_of: weekOf,
      provider,
    }),
};

// Health check
export const healthCheck = () => request<{ status: string; version: string }>('GET', `${API_BASE_URL}/health`);

// SSE Progress Stream (Note: SSE might need special handling in Tauri)
export function createProgressStream(taskId: string, onProgress: (data: any) => void) {
  // For now, use polling as a fallback
  // TODO: Implement proper SSE support for Tauri
  console.warn('[API] SSE not fully supported in Tauri, using polling');
  
  const pollInterval = setInterval(async () => {
    try {
      // This would need a polling endpoint on the backend
      // For now, just log
      console.log('[API] Polling for progress:', taskId);
    } catch (error) {
      console.error('[API] Polling error:', error);
    }
  }, 1000);

  return {
    close: () => clearInterval(pollInterval),
  };
}
