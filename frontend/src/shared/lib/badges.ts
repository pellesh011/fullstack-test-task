export function getLevelVariant(level: string) {
  if (level === "critical") return "danger";
  if (level === "warning") return "warning";
  return "success";
}

export function getProcessingVariant(status: string) {
  if (status === "failed") return "danger";
  if (status === "processing") return "warning";
  if (status === "processed") return "success";
  return "secondary";
}