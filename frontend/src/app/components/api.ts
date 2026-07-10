import type { AlertItem, FileItem } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function fetchFiles(): Promise<FileItem[]> {
  const response = await fetch(`${API_BASE}/files`, { cache: "no-store" });
  if (!response.ok) throw new Error("Не удалось загрузить данные");
  return response.json() as Promise<FileItem[]>;
}

export async function fetchAlerts(): Promise<AlertItem[]> {
  const response = await fetch(`${API_BASE}/alerts`, { cache: "no-store" });
  if (!response.ok) throw new Error("Не удалось загрузить данные");
  return response.json() as Promise<AlertItem[]>;
}

export async function uploadFile(title: string, file: File): Promise<FileItem> {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/files`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) throw new Error("Не удалось загрузить файл");
  return response.json() as Promise<FileItem>;
}
