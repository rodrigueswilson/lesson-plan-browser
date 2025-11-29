// Shared API client that works in both Tauri and browser environments

// Utility to safely read Vite env vars even when import.meta is undefined (tests)
const importMetaEnv: Record<string, any> =
  typeof import.meta !== 'undefined' && import.meta.env ? import.meta.env : {};

const STANDALONE_DB_ENABLED = importMetaEnv.VITE_ENABLE_STANDALONE_DB === 'true';

let networkBaseOverride: string | null = null;
let cachedNetworkBaseUrl: string | null = null;

const stringOrNull = (value: unknown): string | null => {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
};

const resolveNetworkApiBaseUrl = (): string => {
  if (networkBaseOverride) {
    return networkBaseOverride;
  }
  if (cachedNetworkBaseUrl) {
    return cachedNetworkBaseUrl;
  }

  const envAndroidUrl = stringOrNull(importMetaEnv.VITE_ANDROID_API_BASE_URL);
  const envDefaultUrl = stringOrNull(importMetaEnv.VITE_API_BASE_URL);
  if (envAndroidUrl) {
    cachedNetworkBaseUrl = envAndroidUrl;
    return cachedNetworkBaseUrl;
  }
  if (envDefaultUrl) {
    cachedNetworkBaseUrl = envDefaultUrl;
    return cachedNetworkBaseUrl;
  }

  const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';
  const defaultAndroidUrl = 'http://10.0.2.2:8000/api';
  const defaultDesktopUrl = 'http://localhost:8000/api';

  cachedNetworkBaseUrl = userAgent.includes('Android') ? defaultAndroidUrl : defaultDesktopUrl;
  return cachedNetworkBaseUrl;
};

const isStandaloneMode = (): boolean => {
  if (typeof window === 'undefined') return false;

  const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';

  const isTauri =
    '__TAURI_INTERNALS__' in window ||
    '__TAURI__' in window ||
    (window as any).__TAURI_INTERNALS__ !== undefined ||
    (window as any).__TAURI__ !== undefined;

  const isAndroid =
    userAgent.includes('Android') ||
    userAgent.includes('android') ||
    /Android/i.test(userAgent);

  return isAndroid && isTauri;
};

let NETWORK_API_BASE_URL = resolveNetworkApiBaseUrl();
let API_BASE_URL = computeApiBaseUrl();

function computeApiBaseUrl(): string {
  if (isStandaloneMode()) {
    if (STANDALONE_DB_ENABLED) {
      return 'standalone://local';
    }
    return NETWORK_API_BASE_URL;
  }

  return NETWORK_API_BASE_URL;
}

const refreshBaseUrls = () => {
  cachedNetworkBaseUrl = null;
  NETWORK_API_BASE_URL = resolveNetworkApiBaseUrl();
  API_BASE_URL = computeApiBaseUrl();
};

export const getNetworkApiBaseUrl = (): string => NETWORK_API_BASE_URL;
export const getEffectiveApiBaseUrl = (): string => API_BASE_URL;

export const setNetworkApiBaseUrlOverride = (url?: string | null) => {
  if (typeof url === 'string' && url.trim().length > 0) {
    networkBaseOverride = url.trim();
  } else {
    networkBaseOverride = null;
  }
  refreshBaseUrls();
};

// Helper to query local database via Tauri commands (for standalone mode)
async function queryLocalDatabase<T>(sql: string, params: any[] = []): Promise<T[]> {
  try {
    console.log('[API] Querying local database:', sql, params);
    const tauriApi = await import('@tauri-apps/api/core');
    console.log('[API] Tauri API imported successfully');

    const jsonParams = params.map((p) => {
      if (typeof p === 'string') return p;
      if (typeof p === 'number') return p;
      if (typeof p === 'boolean') return p;
      if (p === null || p === undefined) return null;
      return JSON.parse(JSON.stringify(p));
    });

    console.log('[API] Invoking sql_query command...');
    const result = await tauriApi.invoke<Array<Record<string, any>>>('sql_query', {
      sql,
      params: jsonParams,
    });

    console.log('[API] Local database query result:', result);
    console.log('[API] Found', result.length, 'rows');
    return result as T[];
  } catch (error: any) {
    const errorMsg = error.message || String(error);
    console.error('[API] Local database query failed:', {
      error: errorMsg,
      errorType: typeof error,
      errorObject: error,
      stack: error.stack,
    });
    throw new Error(`Database query failed: ${errorMsg}`);
  }
}

// Helper to transform database row to User object
function rowToUser(row: Record<string, any>): User {
  const name = row.name || `${row.first_name || ''} ${row.last_name || ''}`.trim() || 'Unknown';

  return {
    id: row.id,
    name: name,
    first_name: row.first_name || '',
    last_name: row.last_name || '',
    email: row.email || undefined,
    base_path_override: row.base_path_override || undefined,
    template_path: row.template_path || undefined,
    signature_image_path: row.signature_image_path || undefined,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

export interface User {
  id: string;
  name: string;
  first_name: string;
  last_name: string;
  email?: string;
  base_path_override?: string;
  template_path?: string;
  signature_image_path?: string;
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
  plan_group_label?: string | null;
  proficiency_levels?: string;
  primary_teacher_name?: string;
  primary_teacher_first_name?: string;
  primary_teacher_last_name?: string;
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

export interface ScheduleEntry {
  id: string;
  user_id: string;
  day_of_week: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday';
  start_time: string;
  end_time: string;
  subject: string;
  homeroom: string | null;
  grade: string | null;
  slot_number: number;
  plan_slot_group_id: string | null;
  week_of?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ScheduleEntryCreate {
  user_id: string;
  day_of_week: 'monday' | 'tuesday' | 'wednesday' | 'thursday' | 'friday';
  start_time: string;
  end_time: string;
  subject: string;
  homeroom?: string | null;
  grade?: string | null;
  slot_number: number;
  is_active?: boolean;
  plan_slot_group_id?: string | null;
}

const request = async <T>(
  method: string,
  url: string,
  body?: any,
  currentUserId?: string
): Promise<{ data: T }> => {
  try {
    console.log(`[API] ${method} ${url}`, body ? { body } : '', currentUserId ? `[User: ${currentUserId}]` : '');

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (currentUserId) {
      headers['X-Current-User-Id'] = currentUserId;
    }

    const fetchOptions: RequestInit = {
      method: method,
      headers,
    };

    if (body) {
      fetchOptions.body = JSON.stringify(body);
    }

    const response = await window.fetch(url, fetchOptions);

    console.log(`[API] Response status:`, response.status);
    console.log(`[API] Response ok:`, response.ok);
    console.log(`[API] Response headers:`, response.headers);

    let responseData: any;
    const contentType = response.headers.get('content-type');
    const text = await response.text();

    if (text && text.trim().startsWith('<!DOCTYPE html>')) {
      console.error(`[API] Received HTML instead of JSON. URL: ${url}`);
      console.error(`[API] Current API_BASE_URL: ${API_BASE_URL}`);
      throw new Error(
        `API returned HTML instead of JSON. Check API URL configuration. URL used: ${url}. Expected: ${API_BASE_URL}/users`
      );
    }

    if (text && contentType && contentType.includes('application/json')) {
      try {
        responseData = JSON.parse(text);
      } catch (parseError) {
        console.error(`[API] Failed to parse JSON response:`, parseError);
        console.error(`[API] Response text:`, text.substring(0, 500));
        throw new Error(`Invalid JSON response from API: ${parseError}`);
      }
    } else if (text) {
      console.error(`[API] Unexpected content type:`, contentType);
      console.error(`[API] Response preview:`, text.substring(0, 200));
      throw new Error(`API returned non-JSON response. Content-Type: ${contentType}`);
    } else {
      responseData = { detail: `HTTP ${response.status} Error` };
    }

    console.log(`[API] Response data:`, responseData);

    if (!response.ok) {
      if (response.status === 422 && responseData?.detail && Array.isArray(responseData.detail)) {
        console.error(`[API] Validation Error (422):`, responseData.detail);
        const validationErrors = responseData.detail
          .map(
            (err: any) => `${err.loc?.join('.') || 'field'}: ${err.msg || 'invalid'} (type: ${err.type || 'unknown'})`
          )
          .join('\n  - ');
        console.error(`[API] Validation details:\n  - ${validationErrors}`);
        throw new Error(`Validation Error: ${validationErrors}`);
      }

      const errorMsg =
        typeof responseData === 'object' ? responseData.detail || JSON.stringify(responseData) : String(responseData);
      console.error(`[API] HTTP Error ${response.status}:`, errorMsg);
      throw new Error(`HTTP ${response.status}: ${errorMsg}`);
    }

    return { data: responseData as T };
  } catch (error: any) {
    console.error(`[API] Request failed:`, error);
    console.error(`[API] Error type:`, typeof error);
    console.error(`[API] Error message:`, error.message);
    console.error(`[API] Error stack:`, error.stack);

    const errorMessage = error.message || error.toString() || 'Unknown error';
    throw new Error(`API request failed: ${errorMessage}`);
  }
};

export const userApi = {
  list: async () => {
    const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';
    const isAndroid = userAgent.includes('Android') || /Android/i.test(userAgent);
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;

    console.log('[API] userApi.list() called.', {
      isAndroid,
      standalone: isStandaloneMode(),
      canUseLocalDb,
      hasWindow: typeof window !== 'undefined',
      userAgent: userAgent.substring(0, 50),
    });

    if (canUseLocalDb) {
      console.log('[API] Standalone mode detected. Attempting local database query...');
      try {
        const rows = await queryLocalDatabase<Record<string, any>>(
          'SELECT id, email, first_name, last_name, name, base_path_override, template_path, signature_image_path, created_at, updated_at FROM users ORDER BY created_at DESC'
        );
        const users = rows.map(rowToUser);
        console.log('[API] Standalone mode query success. Found', users.length, 'users');
        return { data: users };
      } catch (error: any) {
        const errorMsg = error.message || String(error);
        console.error('[API] Standalone mode query failed, falling back to HTTP:', errorMsg);
      }
    }

    if (isAndroid) {
      console.log('[API] Using HTTP API over network (Android remote/bridge mode)');
    } else {
      console.log('[API] Using HTTP API (desktop/web mode)');
    }
    return request<User[]>('GET', `${API_BASE_URL}/users`);
  },

  get: (userId: string, currentUserId?: string) =>
    request<User>('GET', `${API_BASE_URL}/users/${userId}`, undefined, currentUserId || userId),

  create: (firstName: string, lastName: string, email?: string) =>
    request<User>('POST', `${API_BASE_URL}/users`, {
      first_name: firstName,
      last_name: lastName,
      email,
    }),

  update: (userId: string, data: { first_name?: string; last_name?: string; email?: string }, currentUserId?: string) =>
    request<User>('PUT', `${API_BASE_URL}/users/${userId}`, data, currentUserId || userId),

  updateBasePath: (userId: string, basePath: string, currentUserId?: string) =>
    request<User>(
      'PUT',
      `${API_BASE_URL}/users/${userId}/base-path?base_path=${encodeURIComponent(basePath)}`,
      undefined,
      currentUserId || userId
    ),

  updateTemplatePaths: (
    userId: string,
    templatePath?: string,
    signatureImagePath?: string,
    currentUserId?: string
  ) => {
    const params = new URLSearchParams();
    if (templatePath !== undefined) params.append('template_path', templatePath);
    if (signatureImagePath !== undefined) params.append('signature_image_path', signatureImagePath);
    return request<User>(
      'PUT',
      `${API_BASE_URL}/users/${userId}/template-paths?${params.toString()}`,
      undefined,
      currentUserId || userId
    );
  },

  getRecentWeeks: (userId: string, limit = 3, currentUserId?: string) =>
    request<Array<{ week_of: string; display: string; folder_name: string }>>(
      'GET',
      `${API_BASE_URL}/recent-weeks?user_id=${userId}&limit=${limit}`,
      undefined,
      currentUserId || userId
    ),
};

export const slotApi = {
  list: (userId: string, currentUserId?: string) =>
    request<ClassSlot[]>('GET', `${API_BASE_URL}/users/${userId}/slots`, undefined, currentUserId || userId),

  create: (
    userId: string,
    slot: Omit<ClassSlot, 'id' | 'user_id' | 'created_at' | 'updated_at'>,
    currentUserId?: string
  ) => request<ClassSlot>('POST', `${API_BASE_URL}/users/${userId}/slots`, slot, currentUserId || userId),

  update: (slotId: string, data: Partial<ClassSlot>, currentUserId?: string) =>
    request<ClassSlot>('PUT', `${API_BASE_URL}/slots/${slotId}`, data, currentUserId),

  delete: (slotId: string, currentUserId?: string) =>
    request<void>('DELETE', `${API_BASE_URL}/slots/${slotId}`, undefined, currentUserId),
};

export const planApi = {
  list: (userId: string, limit = 50, currentUserId?: string) =>
    request<WeeklyPlan[]>('GET', `${API_BASE_URL}/users/${userId}/plans?limit=${limit}`, undefined, currentUserId || userId),
};

export const healthCheck = () => request<{ status: string; version: string }>('GET', `${API_BASE_URL}/health`);

export interface SyncResult {
  pulled: number;
  pushed: number;
  conflicts?: Array<{ id: string; error: string }>;
}

export async function triggerSync(userId: string): Promise<SyncResult> {
  try {
    console.log('[API] Attempting sync via Tauri command...');
    const tauriApi = await import('@tauri-apps/api/core');
    console.log('[API] Tauri API imported successfully');

    console.log('[API] Invoking trigger_sync with userId:', userId);
    const result = await tauriApi.invoke<SyncResult>('trigger_sync', { userId });
    console.log('[API] Sync successful via Tauri:', result);
    return result;
  } catch (error: any) {
    const errorMsg = error.message || String(error);
    console.error('[API] Tauri command error:', {
      message: errorMsg,
      error: error,
      stack: error.stack,
    });

    if (errorMsg.includes('Cannot find module') || errorMsg.includes('Failed to fetch')) {
      throw new Error(
        'Tauri API not available. Make sure you are running the app via "npm run tauri:dev" and not opening it in a regular browser. Error: ' +
          errorMsg
      );
    }

    if (errorMsg.includes('not found') || errorMsg.includes('command')) {
      throw new Error(
        'Tauri command "trigger_sync" not found. Make sure the Rust backend is compiled and the command is registered. Error: ' +
          errorMsg
      );
    }

    throw new Error(`Sync failed via Tauri: ${errorMsg}`);
  }
}

export function createProgressStream(taskId: string, onProgress: (data: any) => void) {
  console.log('[API] Starting progress polling for task:', taskId);

  const pollInterval = setInterval(async () => {
    try {
      const response = await request<any>('GET', `${API_BASE_URL}/progress/${taskId}/poll`);
      const data = response.data;

      console.log('[API] Progress update:', data);

      onProgress({
        status: data.status,
        progress: data.progress || 0,
        message: data.message || 'Processing...',
        current: data.current || 0,
        total: data.total || 0,
      });

      if (
        data.status === 'complete' ||
        data.status === 'error' ||
        data.status === 'completed' ||
        data.status === 'failed'
      ) {
        console.log('[API] Progress polling complete, status:', data.status);
        clearInterval(pollInterval);
      }
    } catch (error) {
      console.error('[API] Polling error:', error);
    }
  }, 500);

  return {
    close: () => clearInterval(pollInterval),
  };
}

export const scheduleApi = {
  getSchedule: async (userId: string, dayOfWeek?: string, homeroom?: string, grade?: string) => {
    const params = new URLSearchParams();
    if (dayOfWeek) params.append('day_of_week', dayOfWeek);
    if (homeroom) params.append('homeroom', homeroom);
    if (grade) params.append('grade', grade);
    const query = params.toString() ? `?${params.toString()}` : '';
    const result = await request<ScheduleEntry[]>(
      'GET',
      `${API_BASE_URL}/schedules/${userId}${query}`,
      undefined,
      userId
    );
    return result.data;
  },

  getCurrentLesson: (userId: string) => {
    return request<ScheduleEntry | null>('GET', `${API_BASE_URL}/schedules/${userId}/current`);
  },

  createEntry: (entry: ScheduleEntryCreate) => {
    return request<ScheduleEntry>('POST', `${API_BASE_URL}/schedules`, entry);
  },

  updateEntry: (scheduleId: string, update: Partial<ScheduleEntryCreate>) => {
    return request<ScheduleEntry>('PUT', `${API_BASE_URL}/schedules/${scheduleId}`, update);
  },

  deleteEntry: (scheduleId: string) => {
    return request<{ success: boolean; message: string }>('DELETE', `${API_BASE_URL}/schedules/${scheduleId}`);
  },

  bulkCreate: async (userId: string, entries: ScheduleEntryCreate[]) => {
    const result = await request<{ success: boolean; created_count: number; errors?: string[] }>(
      'POST',
      `${API_BASE_URL}/schedules/${userId}/bulk`,
      { entries },
      userId
    );
    return result.data;
  },
};

export interface LessonStep {
  id: string;
  lesson_plan_id: string;
  day_of_week: string;
  slot_number: number;
  step_number: number;
  step_name: string;
  duration_minutes: number;
  start_time_offset: number;
  content_type: 'objective' | 'sentence_frames' | 'materials' | 'instruction' | 'assessment';
  display_content: string;
  hidden_content?: string[];
  sentence_frames?: Array<{
    portuguese: string;
    english: string;
    language_function: string;
    proficiency_level: 'levels_1_2' | 'levels_3_4' | 'levels_5_6';
    frame_type: 'frame' | 'stem' | 'open_question';
  }>;
  materials_needed?: string[];
  vocabulary_cognates?: Array<{
    english: string;
    portuguese: string;
    is_cognate?: boolean;
    relevance_note?: string;
  }>;
  created_at: string;
  updated_at: string;
}

export interface LessonPlanDetail {
  id: string;
  user_id: string;
  week_of: string;
  lesson_json: any;
  status: string;
  generated_at: string;
  output_file?: string;
}

export const lessonApi = {
  getPlanDetail: (planId: string, currentUserId?: string) =>
    request<LessonPlanDetail>('GET', `${API_BASE_URL}/plans/${planId}`, undefined, currentUserId),

  getLessonSteps: (planId: string, day: string, slot: number, currentUserId?: string) =>
    request<LessonStep[]>(
      'GET',
      `${API_BASE_URL}/lesson-steps/${planId}/${day}/${slot}`,
      undefined,
      currentUserId
    ),

  generateLessonSteps: (planId: string, day: string, slot: number, currentUserId?: string) =>
    request<LessonStep[]>(
      'POST',
      `${API_BASE_URL}/lesson-steps/generate?plan_id=${planId}&day=${day}&slot=${slot}`,
      undefined,
      currentUserId
    ),
};

export interface LessonModeSession {
  id: string;
  user_id: string;
  lesson_plan_id: string;
  schedule_entry_id?: string | null;
  day_of_week: string;
  slot_number: number;
  current_step_index: number;
  remaining_time: number;
  is_running: boolean;
  is_paused: boolean;
  is_synced: boolean;
  timer_start_time?: string | null;
  paused_at?: number | null;
  adjusted_durations?: Record<string, number> | null;
  session_start_time: string;
  last_updated: string;
  ended_at?: string | null;
}

export interface LessonModeSessionCreate {
  user_id: string;
  lesson_plan_id: string;
  schedule_entry_id?: string | null;
  day_of_week: string;
  slot_number: number;
  current_step_index?: number;
  remaining_time?: number;
  is_running?: boolean;
  is_paused?: boolean;
  is_synced?: boolean;
  timer_start_time?: string | null;
  paused_at?: number | null;
  adjusted_durations?: Record<string, number> | null;
}

export const lessonModeSessionApi = {
  create: (sessionData: LessonModeSessionCreate, currentUserId?: string) =>
    request<LessonModeSession>(
      'POST',
      `${API_BASE_URL}/lesson-mode/session`,
      sessionData,
      currentUserId || sessionData.user_id
    ),

  get: (sessionId: string, currentUserId?: string) =>
    request<LessonModeSession>('GET', `${API_BASE_URL}/lesson-mode/session/${sessionId}`, undefined, currentUserId),

  getActive: (
    userId: string,
    options?: { lesson_plan_id?: string; day_of_week?: string; slot_number?: number },
    currentUserId?: string
  ) => {
    const params = new URLSearchParams();
    if (options?.lesson_plan_id) params.append('lesson_plan_id', options.lesson_plan_id);
    if (options?.day_of_week) params.append('day_of_week', options.day_of_week);
    if (options?.slot_number !== undefined) params.append('slot_number', options.slot_number.toString());
    const query = params.toString() ? `?${params.toString()}&user_id=${userId}` : `?user_id=${userId}`;
    return request<LessonModeSession | null>(
      'GET',
      `${API_BASE_URL}/lesson-mode/session/active${query}`,
      undefined,
      currentUserId || userId
    );
  },

  update: (sessionId: string, updates: Partial<LessonModeSessionCreate>, currentUserId?: string) =>
    request<LessonModeSession>('PUT', `${API_BASE_URL}/lesson-mode/session/${sessionId}`, updates, currentUserId),

  end: (sessionId: string, currentUserId?: string) =>
    request<{ success: boolean; message: string }>('POST', `${API_BASE_URL}/lesson-mode/session/${sessionId}/end`, undefined, currentUserId),
};

export { API_BASE_URL, NETWORK_API_BASE_URL };

