"use client";

import { useState, useCallback } from "react";
import { fetchFiles } from "../api/fetchFiles";
import type { FileItem } from "@/entities";

export function useFiles() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadFiles = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchFiles();
      setFiles(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
    } finally {
      setIsLoading(false);
    }
  }, []);

  return { files, isLoading, error, loadFiles };
}