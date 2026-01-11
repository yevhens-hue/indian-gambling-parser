/**
 * Custom hook для WebSocket подключения
 */
import { useEffect, useRef, useState, useCallback } from 'react';
import { useQueryClient } from '@tanstack/react-query';

// Определяем WebSocket URL на основе API URL
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';
const WS_URL = import.meta.env.VITE_WS_URL || (API_URL.replace(/^http/, 'ws') + '/ws/updates');

export interface WebSocketMessage {
  type: 'initial_data' | 'data_updated' | 'manual_update' | 'pong';
  timestamp: string;
  statistics?: any;
  total_providers?: number;
}

export function useWebSocket() {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    // Проверяем, не пытаемся ли мы уже подключиться
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    // Закрываем предыдущее соединение, если оно в состоянии CONNECTING
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      wsRef.current.close();
      wsRef.current = null;
    }

    try {
      console.log(`🔌 Попытка подключения к WebSocket: ${WS_URL}`);
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;
      let pingInterval: number | null = null;

      ws.onopen = () => {
        console.log('✅ WebSocket подключен');
        setIsConnected(true);
        reconnectAttempts.current = 0;
        
        // Отправляем ping каждые 30 секунд
        pingInterval = window.setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            try {
              ws.send('ping');
            } catch (e) {
              console.warn('Не удалось отправить ping:', e);
              if (pingInterval) clearInterval(pingInterval);
            }
          } else {
            if (pingInterval) clearInterval(pingInterval);
          }
        }, 30000);
      };

      ws.onmessage = (event) => {
        try {
          // Игнорируем pong ответы
          if (event.data === 'pong') {
            return;
          }
          
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastUpdate(new Date());
          
          // Автоматически обновляем данные при получении обновлений
          if (message.type === 'data_updated' || message.type === 'initial_data' || message.type === 'manual_update') {
            // Инвалидируем кеш для обновления данных
            queryClient.invalidateQueries({ queryKey: ['providers'] });
            queryClient.invalidateQueries({ queryKey: ['statistics'] });
          }
        } catch (error) {
          console.warn('Ошибка парсинга WebSocket сообщения:', error, event.data);
        }
      };

      ws.onerror = (error) => {
        console.warn('WebSocket ошибка (это нормально при первом подключении):', error);
        // Не устанавливаем isConnected в false здесь, пусть onclose это делает
      };

      ws.onclose = (event) => {
        if (pingInterval) {
          clearInterval(pingInterval);
          pingInterval = null;
        }
        
        console.log(`❌ WebSocket отключен (код: ${event.code}, причина: ${event.reason || 'не указана'})`);
        setIsConnected(false);
        wsRef.current = null;
        
        // Пытаемся переподключиться только если это не было намеренное закрытие
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          
          reconnectTimeoutRef.current = window.setTimeout(() => {
            console.log(`🔄 Попытка переподключения ${reconnectAttempts.current}/${maxReconnectAttempts} через ${delay}ms...`);
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          console.warn('⚠️ Превышено количество попыток переподключения. WebSocket будет отключен.');
        }
      };
    } catch (error) {
      console.error('❌ Ошибка создания WebSocket:', error);
      setIsConnected(false);
      wsRef.current = null;
      
      // Пытаемся переподключиться
      if (reconnectAttempts.current < maxReconnectAttempts) {
        reconnectAttempts.current++;
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectTimeoutRef.current = window.setTimeout(() => {
          console.log(`🔄 Повторная попытка подключения ${reconnectAttempts.current}/${maxReconnectAttempts}...`);
          connect();
        }, delay);
      }
    }
  }, [queryClient]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      try {
        // Закрываем с кодом 1000 (нормальное закрытие) чтобы не пытаться переподключаться
        wsRef.current.close(1000, 'Manual disconnect');
      } catch (e) {
        console.warn('Ошибка при закрытии WebSocket:', e);
      }
      wsRef.current = null;
    }
    setIsConnected(false);
    reconnectAttempts.current = 0; // Сбрасываем счетчик попыток
  }, []);

  useEffect(() => {
    // Небольшая задержка перед первым подключением, чтобы убедиться что страница загружена
    const timeoutId = window.setTimeout(() => {
      connect();
    }, 1000);
    
    return () => {
      clearTimeout(timeoutId);
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    lastUpdate,
    reconnect: connect,
    disconnect,
  };
}
