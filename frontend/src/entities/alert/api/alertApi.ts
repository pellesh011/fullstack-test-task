import { httpGet } from "@/shared/api";
import type { AlertItem } from "../model/types";

export async function getAlerts(): Promise<AlertItem[]> {
  return httpGet<AlertItem[]>("/alerts");
}