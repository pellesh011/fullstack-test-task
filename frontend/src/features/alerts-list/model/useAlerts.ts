"use client";

import { useState, useCallback } from "react";
import { fetchAlerts as fetchAlertsApi } from "../api/fetchAlerts";
import type { AlertItem } from "@/entities";

export function useAlerts() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchAlertsApi();
      setAlerts(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { alerts, isLoading, error, loadAlerts };
}