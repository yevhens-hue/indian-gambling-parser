/**
 * Custom hook для работы с провайдерами
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getProviders, getProvider, updateProvider, getStatistics } from '../services/api';
import type { ProvidersQueryParams, Provider } from '../services/api';

const QUERY_KEYS = {
  providers: (params: ProvidersQueryParams) => ['providers', params],
  provider: (id: number) => ['provider', id],
  statistics: ['statistics'],
};

/**
 * Hook для получения списка провайдеров
 */
export function useProviders(params: ProvidersQueryParams = {}) {
  return useQuery({
    queryKey: QUERY_KEYS.providers(params),
    queryFn: () => getProviders(params),
    staleTime: 30000, // Данные считаются свежими 30 секунд
    placeholderData: (previousData) => previousData, // Сохраняем предыдущие данные во время загрузки новых
  });
}

/**
 * Hook для получения провайдера по ID
 */
export function useProvider(id: number) {
  return useQuery({
    queryKey: QUERY_KEYS.provider(id),
    queryFn: () => getProvider(id),
    enabled: !!id, // Запрос выполняется только если ID задан
  });
}

/**
 * Hook для обновления провайдера
 */
export function useUpdateProvider() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: Partial<Provider> }) =>
      updateProvider(id, updates),
    onSuccess: (updatedProvider) => {
      // Инвалидируем кеш для обновленного провайдера
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.provider(updatedProvider.id!) });
      
      // Инвалидируем кеш для списка провайдеров (все варианты параметров)
      queryClient.invalidateQueries({ queryKey: ['providers'] });
      
      // Инвалидируем статистику
      queryClient.invalidateQueries({ queryKey: QUERY_KEYS.statistics });
    },
  });
}

/**
 * Hook для получения статистики
 */
export function useStatistics() {
  return useQuery({
    queryKey: QUERY_KEYS.statistics,
    queryFn: getStatistics,
    staleTime: 60000, // Статистика обновляется реже
  });
}
