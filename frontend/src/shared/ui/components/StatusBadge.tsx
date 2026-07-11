"use client";

import { Badge } from "react-bootstrap";

interface StatusBadgeProps {
  status: string;
  variant?: "processing" | "level";
}

export function StatusBadge({ status, variant = "processing" }: StatusBadgeProps) {
  const getVariant = () => {
    if (variant === "level") {
      if (status === "critical") return "danger";
      if (status === "warning") return "warning";
      return "success";
    }
    if (status === "failed") return "danger";
    if (status === "processing") return "warning";
    if (status === "processed") return "success";
    return "secondary";
  };

  return <Badge bg={getVariant()}>{status}</Badge>;
}