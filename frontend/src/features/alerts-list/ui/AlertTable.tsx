"use client";

import { Badge, Table } from "react-bootstrap";
import { formatDate, getLevelVariant } from "@/shared/lib";
import type { AlertItem } from "@/entities";

function getDetailMessage(details: Record<string, unknown> | null): string {
  if (!details) return "—";
  if (typeof details.message === "string" && details.message) return details.message;
  if (typeof details.error === "string" && details.error) return details.error;
  if (typeof details.infected === "boolean" && details.infected) return "Обнаружена угроза";
  if (typeof details.is_suspicious === "boolean" && details.is_suspicious) return "Подозрительное расширение";
  if (typeof details.is_mismatch === "boolean" && details.is_mismatch) return "Несоответствие MIME";
  return "—";
}

interface AlertTableProps {
  alerts: AlertItem[];
  isLoading: boolean;
}

export function AlertTable({ alerts, isLoading }: AlertTableProps) {
  if (isLoading) {
    return (
      <div className="d-flex justify-content-center py-5">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="table-responsive">
      <Table hover bordered className="align-middle mb-0">
        <thead className="table-light">
          <tr>
            <th>ID</th>
            <th>File ID</th>
            <th>Processor</th>
            <th>Статус</th>
            <th>Сообщение</th>
            <th>Создан</th>
          </tr>
        </thead>
        <tbody>
          {alerts.length === 0 ? (
            <tr>
              <td colSpan={6} className="text-center py-4 text-secondary">
                Проблемных записей нет
              </td>
            </tr>
          ) : (
            alerts.map((item) => (
              <tr key={item.id}>
                <td>{item.id}</td>
                <td className="small">{item.file_id}</td>
                <td>{item.processor}</td>
                <td>
                  <Badge bg={getLevelVariant(item.status)}>{item.status}</Badge>
                </td>
                <td>{getDetailMessage(item.details)}</td>
                <td>{formatDate(item.created_at)}</td>
              </tr>
            ))
          )}
        </tbody>
      </Table>
    </div>
  );
}