"use client";

import { Badge, Card, CardHeader, CardBody } from "react-bootstrap";
import { AlertTable } from "@/features/alerts-list";
import type { AlertItem } from "@/entities";

interface AlertsWidgetProps {
  alerts: AlertItem[];
  isLoading: boolean;
}

export function AlertsWidget({ alerts, isLoading }: AlertsWidgetProps) {
  return (
    <Card className="shadow-sm border-0">
      <Card.Header className="bg-white border-0 pt-4 px-4">
        <div className="d-flex justify-content-between align-items-center">
          <h2 className="h5 mb-0">Алерты</h2>
          <Badge bg="secondary">{alerts.length}</Badge>
        </div>
      </Card.Header>
      <Card.Body className="px-4 pb-4">
        <AlertTable alerts={alerts} isLoading={isLoading} />
      </Card.Body>
    </Card>
  );
}