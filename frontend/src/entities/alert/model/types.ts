export type AlertItem = {
  id: number;
  file_id: string;
  processor: string;
  status: string;
  details: Record<string, unknown> | null;
  created_at: string;
};