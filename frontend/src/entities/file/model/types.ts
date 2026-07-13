export type FileItem = {
  id: string;
  title: string;
  original_name: string;
  mime_type: string;
  original_mime_type: string | null;
  size: number;
  status: string;
  metadata: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};