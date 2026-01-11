/**
 * Hook для синхронизации фильтров с URL query параметрами
 */
import { useSearchParams } from 'react-router-dom';
import { useCallback, useMemo } from 'react';

export interface FilterState {
  merchant?: string;
  providerDomain?: string;
  accountType?: string;
  paymentMethod?: string;
  search?: string;
  page?: number;
  limit?: number;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
}

/**
 * Hook для работы с фильтрами через URL параметры
 */
export function useUrlFilters() {
  const [searchParams, setSearchParams] = useSearchParams();

  // Получить текущие фильтры из URL
  const filters = useMemo<FilterState>(() => {
    return {
      merchant: searchParams.get('merchant') || undefined,
      providerDomain: searchParams.get('providerDomain') || undefined,
      accountType: searchParams.get('accountType') || undefined,
      paymentMethod: searchParams.get('paymentMethod') || undefined,
      search: searchParams.get('search') || undefined,
      page: searchParams.get('page') ? parseInt(searchParams.get('page')!, 10) : undefined,
      limit: searchParams.get('limit') ? parseInt(searchParams.get('limit')!, 10) : undefined,
      sortBy: searchParams.get('sortBy') || undefined,
      sortOrder: (searchParams.get('sortOrder') as 'asc' | 'desc') || undefined,
    };
  }, [searchParams]);

  // Обновить фильтры в URL
  const updateFilters = useCallback(
    (newFilters: Partial<FilterState>, replace: boolean = false) => {
      const params = new URLSearchParams(searchParams);

      // Удаляем параметры, которые стали undefined
      Object.keys(newFilters).forEach((key) => {
        const value = newFilters[key as keyof FilterState];
        if (value === undefined || value === null || value === '') {
          params.delete(key);
        } else {
          params.set(key, String(value));
        }
      });

      // Удаляем page=1 (не показываем по умолчанию)
      if (params.get('page') === '1' || params.get('page') === '0') {
        params.delete('page');
      }

      setSearchParams(params, { replace });
    },
    [searchParams, setSearchParams]
  );

  // Сбросить все фильтры
  const resetFilters = useCallback(() => {
    setSearchParams({}, { replace: true });
  }, [setSearchParams]);

  // Обновить один фильтр
  const setFilter = useCallback(
    (key: keyof FilterState, value: string | number | undefined) => {
      updateFilters({ [key]: value });
    },
    [updateFilters]
  );

  return {
    filters,
    updateFilters,
    resetFilters,
    setFilter,
  };
}
