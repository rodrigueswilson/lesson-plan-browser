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

const normalizeSqlParams = (params: any[]): any[] =>
  params.map((param) => {
    if (param === null || param === undefined) return null;
    if (typeof param === 'string' || typeof param === 'number') {
      return param;
    }
    if (typeof param === 'boolean') {
      return param ? 1 : 0;
    }
    try {
      return JSON.parse(JSON.stringify(param));
    } catch {
      return null;
    }
  });

const safeJsonParse = <T>(value: any): T | undefined => {
  if (value === null || value === undefined || value === '') {
    return undefined;
  }
  if (typeof value === 'object') {
    return value as T;
  }
  if (typeof value === 'string') {
    try {
      return JSON.parse(value) as T;
    } catch {
      return undefined;
    }
  }
  return undefined;
};

const toBoolean = (value: any): boolean => {
  if (typeof value === 'boolean') {
    return value;
  }
  if (typeof value === 'number') {
    return value !== 0;
  }
  if (typeof value === 'string') {
    return value === '1' || value.toLowerCase() === 'true';
  }
  return false;
};

const generateLocalId = (prefix = 'local'): string => {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 10)}`;
};

const resolveNetworkApiBaseUrl = (): string => {
  if (networkBaseOverride) {
    return networkBaseOverride;
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

  // Check if we're in a Tauri environment
  const isTauri = typeof window !== 'undefined' && ('__TAURI_INTERNALS__' in window || '__TAURI__' in window);

  // For Tauri environments, we can use cached value if available (stable environment)
  if (isTauri && cachedNetworkBaseUrl) {
    return cachedNetworkBaseUrl;
  }

  // For web browsers, always recalculate (don't use cache)
  // Check if we're in a Tauri Android environment
  const userAgent = typeof navigator !== 'undefined' ? navigator.userAgent || '' : '';
  const isAndroidTauri = isTauri && (userAgent.includes('Android') || /Android/i.test(userAgent));

  const defaultAndroidUrl = 'http://10.0.2.2:8000/api';
  const defaultDesktopUrl = 'http://localhost:8000/api';

  // Only use Android URL if we're actually in Android Tauri, otherwise use localhost
  const resolvedUrl = isAndroidTauri ? defaultAndroidUrl : defaultDesktopUrl;

  // Cache for Tauri environments (stable), but not for web browsers (recalculate each time)
  if (isTauri) {
    cachedNetworkBaseUrl = resolvedUrl;
  }

  return resolvedUrl;
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

const sanitizePathSegment = (segment: string): string => {
  if (!segment || typeof segment !== 'string') return 'default';
  return segment.replace(/[^a-zA-Z0-9._-]/g, '_');
};

const encodeFilenameToken = (value: string): string => encodeURIComponent(value ?? '');

const decodeFilenameToken = (token: string): string => {
  try {
    return decodeURIComponent(token);
  } catch {
    return token;
  }
};

let cachedAppDataDir: string | null = null;
let resolveAppDataDirPromise: Promise<string> | null = null;
const lessonPlanDirCache: Record<string, string> = {};
let pathModulePromise: Promise<typeof import('@tauri-apps/api/path')> | null = null;

const getPathModule = async () => {
  if (!pathModulePromise) {
    pathModulePromise = import('@tauri-apps/api/path');
  }
  return pathModulePromise;
};

async function getAppDataDirPath(): Promise<string> {
  if (!isStandaloneMode()) {
    return '';
  }
  if (cachedAppDataDir) {
    return cachedAppDataDir;
  }
  if (!resolveAppDataDirPromise) {
    resolveAppDataDirPromise = (async () => {
      try {
        const tauriApi = await import('@tauri-apps/api/core');
        const dir = await tauriApi.invoke<string>('get_app_data_dir');
        cachedAppDataDir = dir;
        return dir;
      } catch (error) {
        console.error('[API] Failed to resolve app data dir:', error);
        cachedAppDataDir = '';
        return '';
      }
    })();
  }
  return resolveAppDataDirPromise;
}

async function getLessonPlanDirectory(userId: string): Promise<string> {
  if (lessonPlanDirCache[userId]) {
    return lessonPlanDirCache[userId];
  }
  const appDir = await getAppDataDirPath();
  if (!appDir) {
    throw new Error('App data directory unavailable');
  }
  const sanitizedUserId = sanitizePathSegment(userId || 'default');
  const { join } = await getPathModule();
  const dir = await join(appDir, 'lesson-plans', sanitizedUserId);
  lessonPlanDirCache[userId] = dir;
  return dir;
}

// JSON file operations removed - using database lesson_json column as single source of truth
// Functions removed: listStoredLessonPlanFiles, readLessonPlanFile, writeLessonPlanFile,
// buildLessonPlanFileName, parseLessonPlanFileName

const stringifyJsonValue = (value: any): string | null => {
  if (value === undefined) {
    return null;
  }
  if (typeof value === 'string') {
    return value;
  }
  try {
    return JSON.stringify(value);
  } catch {
    return null;
  }
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

interface SqlExecResult {
  rows_affected?: number;
  rowsAffected?: number;
  last_insert_id?: number;
  lastInsertId?: number;
}

async function executeLocalDatabase(sql: string, params: any[] = []): Promise<{ rowsAffected: number; lastInsertId: string }> {
  try {
    const tauriApi = await import('@tauri-apps/api/core');
    const normalizedParams = normalizeSqlParams(params);
    const result = await tauriApi.invoke<SqlExecResult>('sql_execute', {
      sql,
      params: normalizedParams,
    });

    const rowsAffected =
      typeof result.rows_affected === 'number'
        ? result.rows_affected
        : typeof result.rowsAffected === 'number'
          ? result.rowsAffected
          : 0;

    const lastInsertIdValue =
      typeof result.last_insert_id === 'number'
        ? result.last_insert_id
        : typeof result.lastInsertId === 'number'
          ? result.lastInsertId
          : undefined;

    return {
      rowsAffected,
      lastInsertId: lastInsertIdValue !== undefined ? String(lastInsertIdValue) : '',
    };
  } catch (error: any) {
    const errorMsg = error.message || String(error);
    console.error('[API] Local database execute failed:', {
      sql,
      error: errorMsg,
      stack: error.stack,
    });
    throw new Error(`Database execute failed: ${errorMsg}`);
  }
}

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

    const jsonParams = normalizeSqlParams(params);

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

function rowToSlot(row: Record<string, any>): ClassSlot {
  return {
    id: row.id,
    user_id: row.user_id,
    slot_number: Number(row.slot_number ?? 0),
    subject: row.subject || '',
    grade: row.grade || '',
    homeroom: row.homeroom ?? null,
    plan_group_label: row.plan_group_label ?? null,
    proficiency_levels: row.proficiency_levels ?? undefined,
    primary_teacher_name: row.primary_teacher_name ?? undefined,
    primary_teacher_first_name: row.primary_teacher_first_name ?? undefined,
    primary_teacher_last_name: row.primary_teacher_last_name ?? undefined,
    primary_teacher_file_pattern: row.primary_teacher_file_pattern ?? undefined,
    display_order: Number(row.display_order ?? row.slot_number ?? 0),
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function rowToPlan(row: Record<string, any>): WeeklyPlan {
  return {
    id: row.id,
    user_id: row.user_id,
    week_of: row.week_of,
    generated_at: row.generated_at || row.created_at || row.updated_at || row.week_of,
    output_file: row.output_file ?? undefined,
    status: (row.status as WeeklyPlan['status']) ?? 'completed',
    error_message: row.error_message ?? undefined,
  };
}

function rowToScheduleEntry(row: Record<string, any>): ScheduleEntry {
  return {
    id: row.id,
    user_id: row.user_id,
    day_of_week: (row.day_of_week || '').toLowerCase() as ScheduleEntry['day_of_week'],
    start_time: row.start_time || '',
    end_time: row.end_time || '',
    subject: row.subject || '',
    homeroom: row.homeroom ?? null,
    grade: row.grade ?? null,
    slot_number: Number(row.slot_number ?? 0),
    plan_slot_group_id: row.plan_slot_group_id ?? null,
    week_of: row.week_of ?? undefined,
    is_active: row.is_active === undefined ? true : Boolean(row.is_active),
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

const WEEK_DISPLAY_FORMATTER = new Intl.DateTimeFormat('en-US', {
  month: 'long',
  day: 'numeric',
  year: 'numeric',
});

function formatWeekDisplayLabel(weekOf: string): string {
  if (!weekOf) {
    return 'Unknown Week';
  }

  // Remove any existing "Week of" prefix to process just the date part
  const cleanWeekOf = weekOf.replace(/^week of\s+/i, '').trim();

  // Try to match "MM-DD-MM-DD" or "MM/DD-MM/DD" patterns
  // Matches: 01-05-01-09, 09/15-09/19, 12-01-12-05, etc.
  const rangeMatch = cleanWeekOf.match(/^(\d{1,2})[-/](\d{1,2})[-/](\d{1,2})[-/](\d{1,2})$/);

  if (rangeMatch) {
    const [_, m1, d1, m2, d2] = rangeMatch;
    // Format as "MM/DD - MM/DD"
    return `${m1}/${d1} - ${m2}/${d2}`;
  }

  // Try single date format (YYYY-MM-DD)
  const dateMatch = cleanWeekOf.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (dateMatch) {
    const [_, y, m, d] = dateMatch;
    return `${m}/${d}/${y}`;
  }

  // Fallback: If it is a valid date string that Date() can parse
  const parsed = new Date(`${cleanWeekOf}T00:00:00Z`);
  if (!Number.isNaN(parsed.getTime())) {
    // If it was a single iso date, format it simply
    const weekFormatter = new Intl.DateTimeFormat('en-US', {
      month: '2-digit',
      day: '2-digit',
      year: 'numeric'
    });
    return weekFormatter.format(parsed);
  }

  // If no specific pattern matched, return the cleaned string
  return cleanWeekOf;
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

export interface RecentWeek {
  week_of: string;
  display: string;
  folder_name: string;
  latest_created_at?: string;
}

// getRecentWeeksFromLocalFiles removed - using database lesson_json column as single source of truth

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
  total_slots?: number;
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

export interface AnalyticsModelDistribution {
  llm_model: string | null;
  count: number;
  tokens?: number;
  tokens_input?: number;
  tokens_output?: number;
  cost?: number;
  cost_usd?: number;
}

export interface AnalyticsOperationBreakdown {
  operation_type: string;
  count: number;
  avg_duration_ms: number;
  total_duration_ms?: number;
  tokens?: number;
  cost_usd?: number;
}

export interface AnalyticsSummary {
  total_plans: number;
  total_operations: number;
  total_requests?: number;
  total_duration_ms?: number;
  avg_duration_ms?: number;
  avg_duration_per_plan_ms?: number;
  total_tokens: number;
  total_tokens_input?: number;
  total_tokens_output?: number;
  total_cost_usd: number;
  avg_cost_usd?: number;
  model_distribution: AnalyticsModelDistribution[];
  operation_breakdown: AnalyticsOperationBreakdown[];
}

export interface DailyAnalytics {
  date: string;
  plans?: number;
  requests?: number;
  operations?: number;
  duration_ms?: number;
  tokens?: number;
  cost?: number;
  cost_usd?: number;
}

export interface SessionAnalytics {
  plan_id?: string;
  timestamp?: string;
  session_start?: string;
  week_of?: string;
  status?: string;
  duration_ms?: number;
  operations?: number;
  tokens?: number;
  tokens_total?: number;
  cost?: number;
  cost_usd?: number;
  model?: string;
  models_used?: string[];
}

export interface AnalyticsErrorStats {
  total: number;
  success: number;
  failure: number;
  success_rate: number;
  error_breakdown: Record<string, number>;
}

export interface ParallelProcessingStats {
  total_operations: number;
  parallel_operations: number;
  sequential_operations: number;
  parallel_percentage: number;
  avg_duration_ms: number;
  avg_parallel_duration_ms: number;
  avg_sequential_duration_ms: number;
  avg_parallel_slot_count: number;
  avg_sequential_time_ms: number;
  time_savings_ms: number;
  time_savings_percent: number;
  total_rate_limit_errors: number;
  avg_concurrency_level: number;
  avg_tpm_usage: number;
  avg_rpm_usage: number;
}

export const analyticsApi = {
  getSummary: (days: number, userId?: string) => {
    const params = new URLSearchParams({ days: String(days) });
    if (userId) params.append('user_id', userId);
    return request<AnalyticsSummary>('GET', `${API_BASE_URL}/analytics/summary?${params.toString()}`);
  },

  getDaily: (days: number, userId?: string) => {
    const params = new URLSearchParams({ days: String(days) });
    if (userId) params.append('user_id', userId);
    return request<DailyAnalytics[]>('GET', `${API_BASE_URL}/analytics/daily?${params.toString()}`);
  },

  getSessions: (days: number, userId?: string) => {
    const params = new URLSearchParams({ days: String(days) });
    if (userId) params.append('user_id', userId);
    return request<SessionAnalytics[]>('GET', `${API_BASE_URL}/analytics/sessions?${params.toString()}`);
  },

  getOperations: (days: number, userId?: string) => {
    const params = new URLSearchParams({ days: String(days) });
    if (userId) params.append('user_id', userId);
    return request<AnalyticsOperationBreakdown[]>('GET', `${API_BASE_URL}/analytics/operations?${params.toString()}`);
  },

  getErrors: (days: number, userId?: string) => {
    const params = new URLSearchParams({ days: String(days) });
    if (userId) params.append('user_id', userId);
    return request<AnalyticsErrorStats>('GET', `${API_BASE_URL}/analytics/errors?${params.toString()}`);
  },

  getParallel: (days: number, userId?: string) => {
    const params = new URLSearchParams({ days: String(days) });
    if (userId) params.append('user_id', userId);
    return request<ParallelProcessingStats>('GET', `${API_BASE_URL}/analytics/parallel?${params.toString()}`);
  },

  exportCsv: async (days: number, userId?: string) => {
    const params = new URLSearchParams({ days: String(days) });
    if (userId) params.append('user_id', userId);
    const url = `${API_BASE_URL}/analytics/export?${params.toString()}`;

    try {
      const response = await window.fetch(url, { method: 'GET' });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
      }
      return response.text();
    } catch (error: any) {
      const message = error?.message || String(error);
      throw new Error(`Analytics CSV export failed: ${message}`);
    }
  },
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

    try {
      const response = await request<User[]>('GET', `${API_BASE_URL}/users`);
      console.log('[API] userApi.list() HTTP success:', {
        userCount: response.data?.length || 0,
        apiBaseUrl: API_BASE_URL
      });
      return response;
    } catch (error: any) {
      console.error('[API] userApi.list() HTTP failed:', {
        error: error.message || String(error),
        apiBaseUrl: API_BASE_URL,
        status: error.response?.status,
        detail: error.response?.data?.detail
      });
      throw error;
    }
  },

  get: async (userId: string, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const rows = await queryLocalDatabase<Record<string, any>>(
          'SELECT id, email, first_name, last_name, name, base_path_override, template_path, signature_image_path, created_at, updated_at FROM users WHERE id = ? LIMIT 1',
          [userId]
        );
        if (rows.length > 0) {
          return { data: rowToUser(rows[0]) };
        }
        console.warn('[API] Local user not found in database, falling back to HTTP:', userId);
      } catch (error: any) {
        console.error('[API] Local user query failed, falling back to HTTP:', error.message || error);
      }
    }
    return request<User>('GET', `${API_BASE_URL}/users/${userId}`, undefined, currentUserId || userId);
  },

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

  getRecentWeeks: async (userId: string, limit = 3, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    const combinedWeeks: RecentWeek[] = [];
    const seenWeeks = new Set<string>();
    const pushWeek = (week: RecentWeek) => {
      const key = week.week_of?.toLowerCase() || week.display.toLowerCase();
      if (!seenWeeks.has(key)) {
        combinedWeeks.push(week);
        seenWeeks.add(key);
      }
    };

    if (canUseLocalDb) {
      try {
        const rows = await queryLocalDatabase<Record<string, any>>(
          `SELECT week_of, MAX(generated_at) as latest_created_at
           FROM weekly_plans
           WHERE user_id = ?
             AND week_of IS NOT NULL
           GROUP BY week_of
           ORDER BY MAX(generated_at) DESC
           LIMIT ?`,
          [userId, limit]
        );

        return {
          data: rows.map((row) => {
            const weekOf = row.week_of as string;
            return {
              week_of: weekOf,
              display: formatWeekDisplayLabel(weekOf),
              folder_name: getLessonPlanDirectory(weekOf),
              latest_created_at: row.latest_created_at as string
            };
          }),
        };
      } catch (error: any) {
        console.error('[API] Local recent weeks query failed, falling back to HTTP:', error.message || error);
      }
    }

    // JSON file fallback removed - using database lesson_json column as single source of truth

    if (combinedWeeks.length > 0) {
      return { data: combinedWeeks.slice(0, limit) };
    }

    return request<RecentWeek[]>(
      'GET',
      `${API_BASE_URL}/recent-weeks?user_id=${userId}&limit=${limit}`,
      undefined,
      currentUserId || userId
    );
  },
};

export const slotApi = {
  list: async (userId: string, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const rows = await queryLocalDatabase<Record<string, any>>(
          `SELECT id, user_id, slot_number, subject, grade, homeroom, plan_group_label, proficiency_levels,
                  primary_teacher_name, primary_teacher_first_name, primary_teacher_last_name, primary_teacher_file_pattern,
                  display_order, created_at, updated_at
           FROM class_slots
           WHERE user_id = ?
           ORDER BY display_order ASC, slot_number ASC`,
          [userId]
        );
        return { data: rows.map(rowToSlot) };
      } catch (error: any) {
        console.error('[API] Local slot query failed, falling back to HTTP:', error.message || error);
      }
    }
    return request<ClassSlot[]>('GET', `${API_BASE_URL}/users/${userId}/slots`, undefined, currentUserId || userId);
  },

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
  list: async (userId: string, limit = 50, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const rows = await queryLocalDatabase<Record<string, any>>(
          `SELECT id, user_id, week_of, status, output_file, generated_at, error_message
           FROM weekly_plans
           WHERE user_id = ?
           ORDER BY generated_at DESC
           LIMIT ?`,
          [userId, limit]
        );
        const plans = rows.map(rowToPlan);
        console.log('[API] planApi.list (local):', {
          userId,
          limit,
          planCount: plans.length,
          weekOfValues: plans.map(p => p.week_of),
          firstPlanWeekOf: plans[0]?.week_of
        });
        return { data: plans };
      } catch (error: any) {
        console.error('[API] Local plan query failed, falling back to HTTP:', error.message || error);
      }
    }
    const response = await request<WeeklyPlan[]>(
      'GET',
      `${API_BASE_URL}/users/${userId}/plans?limit=${limit}`,
      undefined,
      currentUserId || userId
    );

    console.log('[API] planApi.list (HTTP):', {
      userId,
      limit,
      planCount: response.data?.length || 0,
      weekOfValues: response.data?.map(p => p.week_of) || [],
      firstPlanWeekOf: response.data?.[0]?.week_of
    });

    if (canUseLocalDb) {
      try {
        await cacheWeeklyPlanSummaries(response.data ?? []);
      } catch (error) {
        console.warn('[API] Failed to cache weekly plans locally:', error);
      }
    }
    return response;
  },
  process: async (
    userId: string,
    weekOf: string,
    provider: string = 'openai',
    slotIds?: string[],
    partial: boolean = false,
    missingOnly: boolean = false,
    forceSlots: number[] = [],
    currentUserId?: string
  ) => {
    const body = {
      user_id: userId,
      week_of: weekOf,
      provider: provider,
      slot_ids: slotIds || undefined,
      partial: partial,
      missing_only: missingOnly,
      force_slots: forceSlots,
    };
    return request<{
      success: boolean;
      plan_id: string;
      output_file?: string;
      processed_slots: number;
      failed_slots: number;
      errors?: Array<{ slot: number; subject: string; error: string }>;
    }>(
      'POST',
      `${API_BASE_URL}/process-week`,
      body,
      currentUserId || userId
    );
  },

  getWeekStatus: async (userId: string, weekOf: string, currentUserId?: string) => {
    // Local DB support removed for brevity, prioritizing HTTP for this new feature
    return request<{
      week_of: string;
      status: string | null;
      plan_id: string | null;
      done_slots: number[];
      missing_slots: number[];
      total_slots: number;
      generated_at: string | null;
    }>('GET', `${API_BASE_URL}/plans/status/${userId}/${weekOf}`, undefined, currentUserId || userId);
  },
};

export const healthCheck = () => request<{ status: string; version: string }>('GET', `${API_BASE_URL}/health`);

export interface SyncResult {
  pulled: number;
  pushed: number;
  conflicts?: Array<{ id: string; error: string }>;
}

export async function triggerSync(userId: string): Promise<SyncResult> {
  // Check if we're in a web browser (not Tauri)
  const isWeb = typeof window !== 'undefined' &&
    !('__TAURI_INTERNALS__' in window) &&
    !('__TAURI__' in window);

  if (isWeb) {
    console.log('[API] Sync not available in web browser. Tauri sync is only available in the desktop/mobile app.');
    return {
      pulled: 0,
      pushed: 0,
      conflicts: [],
    };
  }

  try {
    console.log('[API] Attempting sync via Tauri command...');
    const tauriApi = await import('@tauri-apps/api/core');

    // Check if invoke is available
    if (!tauriApi || typeof tauriApi.invoke !== 'function') {
      throw new Error('Tauri invoke method not available');
    }

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

    if (errorMsg.includes('Cannot find module') || errorMsg.includes('Failed to fetch') || errorMsg.includes('Cannot read properties')) {
      console.warn('[API] Tauri API not available - running in web browser mode');
      return {
        pulled: 0,
        pushed: 0,
        conflicts: [],
      };
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
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        let sql = `SELECT id, user_id, day_of_week, slot_number, start_time, end_time, subject, grade, homeroom, plan_slot_group_id, is_active, created_at, updated_at
                   FROM schedules
                   WHERE user_id = ?`;
        const params: any[] = [userId];
        if (dayOfWeek) {
          sql += ' AND lower(day_of_week) = lower(?)';
          params.push(dayOfWeek);
        }
        if (homeroom) {
          sql += ' AND homeroom = ?';
          params.push(homeroom);
        }
        if (grade) {
          sql += ' AND grade = ?';
          params.push(grade);
        }
        sql += ' ORDER BY slot_number ASC, start_time ASC';
        const rows = await queryLocalDatabase<Record<string, any>>(sql, params);
        return rows.map(rowToScheduleEntry);
      } catch (error: any) {
        console.error('[API] Local schedule query failed, falling back to HTTP:', error.message || error);
      }
    }

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

function rowToLessonStep(row: Record<string, any>): LessonStep {
  return {
    id: row.id,
    lesson_plan_id: row.lesson_plan_id,
    day_of_week: row.day_of_week,
    slot_number: Number(row.slot_number ?? 0),
    step_number: Number(row.step_number ?? 0),
    step_name: row.step_name || '',
    duration_minutes: Number(row.duration_minutes ?? 0),
    start_time_offset: Number(row.start_time_offset ?? 0),
    content_type: row.content_type,
    display_content: row.display_content || '',
    hidden_content: safeJsonParse<string[]>(row.hidden_content),
    sentence_frames: safeJsonParse<LessonStep['sentence_frames']>(row.sentence_frames),
    materials_needed: safeJsonParse<string[]>(row.materials_needed),
    vocabulary_cognates: safeJsonParse<LessonStep['vocabulary_cognates']>(row.vocabulary_cognates),
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
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

interface WeeklyPlanRecordInput {
  id: string;
  user_id: string;
  week_of: string;
  status?: WeeklyPlan['status'] | string;
  output_file?: string | null;
  generated_at?: string;
  lesson_json?: string | null;
  error_message?: string | null;
}

async function upsertWeeklyPlanRecord(record: WeeklyPlanRecordInput): Promise<void> {
  if (!isStandaloneMode() || !STANDALONE_DB_ENABLED) {
    return;
  }
  const generatedAt = record.generated_at || new Date().toISOString();
  const lessonJsonValue = record.lesson_json ?? null;
  try {
    await executeLocalDatabase(
      `INSERT INTO weekly_plans (id, user_id, week_of, status, output_file, generated_at, lesson_json, error_message)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(id) DO UPDATE SET
         user_id = excluded.user_id,
         week_of = excluded.week_of,
         status = excluded.status,
         output_file = excluded.output_file,
         generated_at = excluded.generated_at,
         lesson_json = COALESCE(excluded.lesson_json, lesson_json),
         error_message = excluded.error_message`,
      [
        record.id,
        record.user_id,
        record.week_of,
        record.status ?? 'completed',
        record.output_file ?? null,
        generatedAt,
        lessonJsonValue,
        record.error_message ?? null,
      ]
    );
  } catch (error) {
    console.warn('[API] Failed to upsert weekly plan record:', error);
  }
}

async function cacheWeeklyPlanSummaries(plans: WeeklyPlan[]): Promise<void> {
  if (!isStandaloneMode() || !STANDALONE_DB_ENABLED) {
    return;
  }
  for (const plan of plans) {
    await upsertWeeklyPlanRecord({
      id: plan.id,
      user_id: plan.user_id,
      week_of: plan.week_of,
      status: plan.status,
      output_file: plan.output_file ?? null,
      generated_at: plan.generated_at,
      error_message: plan.error_message ?? null,
    });
  }
}

async function cacheLessonPlanDetailLocally(plan: LessonPlanDetail): Promise<void> {
  if (!isStandaloneMode() || !STANDALONE_DB_ENABLED) {
    return;
  }
  // Save to database only - JSON file writing removed
  await upsertWeeklyPlanRecord({
    id: plan.id,
    user_id: plan.user_id,
    week_of: plan.week_of,
    status: plan.status,
    output_file: plan.output_file ?? null,
    generated_at: plan.generated_at,
    lesson_json: stringifyJsonValue(plan.lesson_json),
  });
  // JSON file writing removed - using database lesson_json column as single source of truth
}

// readLessonPlanFromStorage removed - using database lesson_json column as single source of truth

export const lessonApi = {
  getPlanDetail: async (planId: string, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const rows = await queryLocalDatabase<Record<string, any>>(
          `SELECT id, user_id, week_of, status, generated_at, output_file, lesson_json
           FROM weekly_plans
           WHERE id = ?
           LIMIT 1`,
          [planId]
        );
        if (rows.length > 0) {
          const row = rows[0];
          let lessonJson = row.lesson_json;
          if (typeof lessonJson === 'string') {
            try {
              lessonJson = JSON.parse(lessonJson);
            } catch {
              // leave as-is if parsing fails
            }
          }
          // JSON file fallback removed - using database lesson_json column as single source of truth
          // If lesson_json is null, return empty object (or could throw error)
          if (!lessonJson) {
            console.warn(`[API] Plan ${row.id} has null lesson_json - returning empty object`);
            lessonJson = {};
          }
          const planDetail = {
            id: row.id,
            user_id: row.user_id,
            week_of: row.week_of,
            lesson_json: lessonJson,
            status: row.status || 'completed',
            generated_at: row.generated_at || row.created_at || row.updated_at || '',
            output_file: row.output_file ?? undefined,
          };

          console.log('[API] planApi.getPlanDetail (local):', {
            planId,
            week_of: row.week_of,
            hasLessonJson: !!lessonJson,
            lessonJsonType: typeof lessonJson
          });

          return { data: planDetail };
        }
      } catch (error: any) {
        console.error('[API] Local plan detail query failed, falling back to HTTP:', error.message || error);
      }
    }
    const response = await request<LessonPlanDetail>('GET', `${API_BASE_URL}/plans/${planId}`, undefined, currentUserId);

    console.log('[API] planApi.getPlanDetail (HTTP):', {
      planId,
      week_of: response.data?.week_of,
      hasLessonJson: !!response.data?.lesson_json,
      lessonJsonType: typeof response.data?.lesson_json
    });

    if (canUseLocalDb && response.data) {
      try {
        await cacheLessonPlanDetailLocally(response.data);
      } catch (error) {
        console.warn('[API] Failed to cache lesson plan detail locally:', error);
      }
    }
    return response;
  },

  getLessonSteps: async (planId: string, day: string, slot: number, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const rows = await queryLocalDatabase<Record<string, any>>(
          `SELECT *
           FROM lesson_steps
           WHERE lesson_plan_id = ?
             AND lower(day_of_week) = lower(?)
             AND slot_number = ?
           ORDER BY step_number ASC`,
          [planId, day, slot]
        );
        return { data: rows.map(rowToLessonStep) };
      } catch (error: any) {
        console.error('[API] Local lesson steps query failed, falling back to HTTP:', error.message || error);
      }
    }

    return request<LessonStep[]>(
      'GET',
      `${API_BASE_URL}/lesson-steps/${planId}/${day}/${slot}`,
      undefined,
      currentUserId
    );
  },

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

function rowToLessonModeSession(row: Record<string, any>): LessonModeSession {
  return {
    id: row.id,
    user_id: row.user_id,
    lesson_plan_id: row.lesson_plan_id,
    schedule_entry_id: row.schedule_entry_id ?? undefined,
    day_of_week: row.day_of_week,
    slot_number: Number(row.slot_number ?? 0),
    current_step_index: Number(row.current_step_index ?? 0),
    remaining_time: Number(row.remaining_time ?? 0),
    is_running: toBoolean(row.is_running),
    is_paused: toBoolean(row.is_paused),
    is_synced: toBoolean(row.is_synced),
    timer_start_time: row.timer_start_time ?? undefined,
    paused_at: row.paused_at !== undefined && row.paused_at !== null ? Number(row.paused_at) : undefined,
    adjusted_durations: safeJsonParse<Record<string, number>>(row.adjusted_durations) ?? undefined,
    session_start_time: row.session_start_time || row.created_at || new Date().toISOString(),
    last_updated: row.last_updated || row.updated_at || row.session_start_time || new Date().toISOString(),
    ended_at: row.ended_at ?? undefined,
  };
}

async function fetchLocalLessonModeSession(sessionId: string): Promise<LessonModeSession | null> {
  const rows = await queryLocalDatabase<Record<string, any>>(
    `SELECT *
     FROM lesson_mode_sessions
     WHERE id = ?
     LIMIT 1`,
    [sessionId]
  );
  if (rows.length === 0) {
    return null;
  }
  return rowToLessonModeSession(rows[0]);
}

export interface LessonModeSessionCreate {
  id?: string;
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
  session_start_time?: string;
  last_updated?: string;
  ended_at?: string | null;
}

export const lessonModeSessionApi = {
  create: async (sessionData: LessonModeSessionCreate, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const nowIso = new Date().toISOString();
        const sessionId = sessionData.id || generateLocalId('lesson_session');
        const sessionStart = sessionData.session_start_time || nowIso;
        const lastUpdated = sessionData.last_updated || nowIso;

        await executeLocalDatabase(
          `INSERT INTO lesson_mode_sessions
           (id, user_id, lesson_plan_id, schedule_entry_id, day_of_week, slot_number, current_step_index, remaining_time,
            is_running, is_paused, is_synced, timer_start_time, paused_at, adjusted_durations, session_start_time, last_updated, ended_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
          [
            sessionId,
            sessionData.user_id,
            sessionData.lesson_plan_id,
            sessionData.schedule_entry_id ?? null,
            sessionData.day_of_week,
            sessionData.slot_number,
            sessionData.current_step_index ?? 0,
            sessionData.remaining_time ?? 0,
            sessionData.is_running ? 1 : 0,
            sessionData.is_paused ? 1 : 0,
            sessionData.is_synced ? 1 : 0,
            sessionData.timer_start_time ?? null,
            sessionData.paused_at ?? null,
            sessionData.adjusted_durations ? JSON.stringify(sessionData.adjusted_durations) : null,
            sessionStart,
            lastUpdated,
            sessionData.ended_at ?? null,
          ]
        );

        const created = await fetchLocalLessonModeSession(sessionId);
        if (!created) {
          throw new Error('Session not found after local insert');
        }
        return { data: created };
      } catch (error: any) {
        console.error('[API] Local lesson mode session create failed, falling back to HTTP:', error.message || error);
      }
    }

    return request<LessonModeSession>(
      'POST',
      `${API_BASE_URL}/lesson-mode/session`,
      sessionData,
      currentUserId || sessionData.user_id
    );
  },

  get: async (sessionId: string, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const session = await fetchLocalLessonModeSession(sessionId);
        if (session) {
          return { data: session };
        }
      } catch (error: any) {
        console.error('[API] Local lesson mode session get failed, falling back to HTTP:', error.message || error);
      }
    }

    return request<LessonModeSession>('GET', `${API_BASE_URL}/lesson-mode/session/${sessionId}`, undefined, currentUserId);
  },

  getActive: async (
    userId: string,
    options?: { lesson_plan_id?: string; day_of_week?: string; slot_number?: number },
    currentUserId?: string
  ) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        let sql = `SELECT *
                   FROM lesson_mode_sessions
                   WHERE user_id = ?
                     AND (ended_at IS NULL OR ended_at = '')`;
        const params: any[] = [userId];
        if (options?.lesson_plan_id) {
          sql += ' AND lesson_plan_id = ?';
          params.push(options.lesson_plan_id);
        }
        if (options?.day_of_week) {
          sql += ' AND lower(day_of_week) = lower(?)';
          params.push(options.day_of_week);
        }
        if (options?.slot_number !== undefined) {
          sql += ' AND slot_number = ?';
          params.push(options.slot_number);
        }
        sql += ' ORDER BY datetime(session_start_time) DESC LIMIT 1';

        const rows = await queryLocalDatabase<Record<string, any>>(sql, params);
        if (rows.length === 0) {
          return { data: null };
        }
        return { data: rowToLessonModeSession(rows[0]) };
      } catch (error: any) {
        console.error('[API] Local lesson mode session getActive failed, falling back to HTTP:', error.message || error);
      }
    }

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

  update: async (sessionId: string, updates: Partial<LessonModeSessionCreate>, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const setClauses: string[] = [];
        const params: any[] = [];
        const appendField = (column: string, value: any, transform?: (value: any) => any) => {
          if (value !== undefined) {
            setClauses.push(`${column} = ?`);
            params.push(transform ? transform(value) : value);
          }
        };

        appendField('lesson_plan_id', updates.lesson_plan_id);
        appendField('schedule_entry_id', updates.schedule_entry_id === undefined ? undefined : updates.schedule_entry_id ?? null);
        appendField('day_of_week', updates.day_of_week);
        appendField('slot_number', updates.slot_number);
        appendField('current_step_index', updates.current_step_index);
        appendField('remaining_time', updates.remaining_time);
        appendField('is_running', updates.is_running, (v) => (v ? 1 : 0));
        appendField('is_paused', updates.is_paused, (v) => (v ? 1 : 0));
        appendField('is_synced', updates.is_synced, (v) => (v ? 1 : 0));
        appendField('timer_start_time', updates.timer_start_time === undefined ? undefined : updates.timer_start_time ?? null);
        appendField('paused_at', updates.paused_at === undefined ? undefined : updates.paused_at ?? null);
        appendField(
          'adjusted_durations',
          updates.adjusted_durations === undefined ? undefined : updates.adjusted_durations ? JSON.stringify(updates.adjusted_durations) : null
        );
        appendField('ended_at', updates.ended_at === undefined ? undefined : updates.ended_at ?? null);

        if (setClauses.length === 0) {
          console.warn('[API] lessonModeSessionApi.update called with no mutable fields');
          const existing = await fetchLocalLessonModeSession(sessionId);
          if (existing) {
            return { data: existing };
          }
          throw new Error('No fields to update and session not found locally');
        }

        const nowIso = new Date().toISOString();
        setClauses.push('last_updated = ?');
        params.push(updates.last_updated || nowIso);

        params.push(sessionId);

        await executeLocalDatabase(
          `UPDATE lesson_mode_sessions
           SET ${setClauses.join(', ')}
           WHERE id = ?`,
          params
        );

        const updated = await fetchLocalLessonModeSession(sessionId);
        if (!updated) {
          throw new Error('Session not found after local update');
        }
        return { data: updated };
      } catch (error: any) {
        console.error('[API] Local lesson mode session update failed, falling back to HTTP:', error.message || error);
      }
    }

    return request<LessonModeSession>('PUT', `${API_BASE_URL}/lesson-mode/session/${sessionId}`, updates, currentUserId);
  },

  end: async (sessionId: string, currentUserId?: string) => {
    const canUseLocalDb = isStandaloneMode() && STANDALONE_DB_ENABLED;
    if (canUseLocalDb) {
      try {
        const timestamp = new Date().toISOString();
        await executeLocalDatabase(
          `UPDATE lesson_mode_sessions
           SET ended_at = ?, last_updated = ?, is_running = 0, is_paused = 0
           WHERE id = ?`,
          [timestamp, timestamp, sessionId]
        );
        return { data: { success: true, message: 'Session ended locally' } };
      } catch (error: any) {
        console.error('[API] Local lesson mode session end failed, falling back to HTTP:', error.message || error);
      }
    }

    return request<{ success: boolean; message: string }>(
      'POST',
      `${API_BASE_URL}/lesson-mode/session/${sessionId}/end`,
      undefined,
      currentUserId
    );
  },
};

export const settingsApi = {
  getSupabaseSync: async (): Promise<{ data: { enable_supabase_sync: boolean } }> => {
    return request<{ enable_supabase_sync: boolean }>(
      'GET',
      `${API_BASE_URL}/settings/supabase-sync`
    );
  },

  setSupabaseSync: async (enabled: boolean): Promise<{ data: { enable_supabase_sync: boolean; message: string } }> => {
    return request<{ enable_supabase_sync: boolean; message: string }>(
      'PUT',
      `${API_BASE_URL}/settings/supabase-sync`,
      { enabled }
    );
  },
};

// Tablet API (PC-only UI helpers)

export interface TabletExportDbCounts {
  users: number;
  class_slots: number;
  weekly_plans: number;
  schedules: number;
  lesson_steps: number;
  lesson_mode_sessions: number;
}

export interface TabletExportDbResponse {
  user_id: string;
  output_path: string;
  output_bytes: number;
  created_at: string;
  counts: TabletExportDbCounts;
}

export const tabletApi = {
  exportDb: (userId: string, currentUserId?: string) =>
    request<TabletExportDbResponse>(
      'POST',
      `${API_BASE_URL}/tablet/export-db`,
      { user_id: userId },
      currentUserId || userId
    ),
};

export { API_BASE_URL, NETWORK_API_BASE_URL };

