import { API_BASE } from "@/shared/config/api";

export async function httpGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, { cache: "no-store" });
  if (!response.ok) throw new Error("Не удалось загрузить данные");
  return response.json() as Promise<T>;
}

export async function httpPost<T>(path: string, body: FormData): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    body,
  });
  if (!response.ok) throw new Error("Не удалось выполнить запрос");
  return response.json() as Promise<T>;
}