import { httpGet } from "@/shared/api";
import type { FileItem } from "../model/types";

export async function getFiles(): Promise<FileItem[]> {
  return httpGet<FileItem[]>("/files");
}

export async function getFile(id: string): Promise<FileItem> {
  return httpGet<FileItem>(`/files/${id}`);
}