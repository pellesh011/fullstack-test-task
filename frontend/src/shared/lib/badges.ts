export function getLevelVariant(level: string) {
  if (level === "critical" || level === "failed") return "danger";
  if (level === "warning") return "warning";
  if (level === "pending" || level === "running") return "info";
  return "success";
}

export function getProcessingVariant(status: string) {
  if (status === "failed") return "danger";
  if (status === "warning") return "warning";
  if (status === "processing") return "info";
  if (status === "ok") return "success";
  if (status === "new") return "secondary";
  return "secondary";
}