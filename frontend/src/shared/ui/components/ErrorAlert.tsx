"use client";

import { Alert } from "react-bootstrap";

interface ErrorAlertProps {
  message: string;
  onDismiss?: () => void;
}

export function ErrorAlert({ message, onDismiss }: ErrorAlertProps) {
  return (
    <Alert variant="danger" onClose={onDismiss} dismissible={!!onDismiss} className="shadow-sm">
      {message}
    </Alert>
  );
}