import { httpPost } from "@/shared/api/client";

export async function uploadFile(title: string, file: File) {
  const formData = new FormData();
  formData.append("title", title);
  formData.append("file", file);

  return httpPost<{ id: string }>("/files", formData);
}