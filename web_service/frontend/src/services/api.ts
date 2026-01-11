/**
 * API клиент для работы с backend
 */
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Provider {
  id?: number;
  merchant: string;
  merchant_domain: string;
  provider_domain: string;
  account_type?: string | null;
  provider_name?: string | null;
  provider_entry_url?: string | null;
  final_url?: string | null;
  cashier_url?: string | null;
  screenshot_path?: string | null;
  detected_in?: string | null;
  payment_method?: string | null;
  is_iframe?: boolean;
  requires_otp?: boolean;
  blocked_by_geo?: boolean;
  captcha_present?: boolean;
  timestamp_utc?: string | null;
}

export interface ProvidersResponse {
  items: Provider[];
  total: number;
  skip: number;
  limit: number;
  has_more: boolean;
}

export interface ProvidersQueryParams {
  merchant?: string;
  provider_domain?: string;
  account_type?: string;
  payment_method?: string;
  search?: string;
  skip?: number;
  limit?: number;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

export interface Statistics {
  total: number;
  merchants: Record<string, number>;
  account_types: Record<string, number>;
  payment_methods: Record<string, number>;
  providers: Record<string, number>;
}

/**
 * Получить список провайдеров с фильтрацией
 */
export async function getProviders(params: ProvidersQueryParams = {}): Promise<ProvidersResponse> {
  const response = await apiClient.get<ProvidersResponse>('/providers', { params });
  return response.data;
}

/**
 * Получить провайдера по ID
 */
export async function getProvider(id: number): Promise<Provider> {
  const response = await apiClient.get<Provider>(`/providers/${id}`);
  return response.data;
}

/**
 * Обновить провайдера
 */
export async function updateProvider(id: number, updates: Partial<Provider>): Promise<Provider> {
  const response = await apiClient.put<Provider>(`/providers/${id}`, updates);
  return response.data;
}

/**
 * Получить статистику
 */
export async function getStatistics(): Promise<Statistics> {
  const response = await apiClient.get<Statistics>('/providers/stats/statistics');
  return response.data;
}

/**
 * Экспорт в XLSX
 */
export function exportXLSX(): string {
  return `${API_URL}/export/xlsx`;
}

/**
 * Экспорт в CSV
 */
export function exportCSV(params: ProvidersQueryParams = {}): string {
  const queryString = new URLSearchParams(
    Object.entries(params).reduce((acc, [key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        acc[key] = String(value);
      }
      return acc;
    }, {} as Record<string, string>)
  ).toString();
  
  return `${API_URL}/export/csv?${queryString}`;
}

/**
 * Экспорт в JSON
 */
export async function exportJSON(params: ProvidersQueryParams = {}): Promise<ProvidersResponse> {
  const response = await apiClient.get<ProvidersResponse>('/export/json', { params });
  return response.data;
}

/**
 * Получить URL скриншота
 */
export function getScreenshotUrl(screenshotPath: string | null | undefined): string | null {
  if (!screenshotPath) return null;
  
  // Если путь уже полный URL, возвращаем как есть
  if (screenshotPath.startsWith('http')) {
    return screenshotPath;
  }
  
  // Иначе формируем URL через API
  const filename = screenshotPath.split('/').pop() || screenshotPath;
  return `${API_URL}/screenshots/${filename}`;
}
