"use client";

import { useState, useCallback } from "react";
import { uploadFile as uploadFileApi } from "../api/uploadFile";

export function useFileUpload() {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const upload = useCallback(async (title: string, file: File) => {
    setIsSubmitting(true);
    setError(null);
    try {
      await uploadFileApi(title, file);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка загрузки");
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  return { upload, isSubmitting, error };
}