"use client";

import { Badge, Card, CardHeader, CardBody } from "react-bootstrap";
import { FileTable } from "@/features/files-list";
import type { FileItem } from "@/entities";

interface FilesWidgetProps {
  files: FileItem[];
  isLoading: boolean;
}

export function FilesWidget({ files, isLoading }: FilesWidgetProps) {
  return (
    <Card className="shadow-sm border-0 mb-4">
      <Card.Header className="bg-white border-0 pt-4 px-4">
        <div className="d-flex justify-content-between align-items-center">
          <h2 className="h5 mb-0">Файлы</h2>
          <Badge bg="secondary">{files.length}</Badge>
        </div>
      </Card.Header>
      <Card.Body className="px-4 pb-4">
        <FileTable files={files} isLoading={isLoading} />
      </Card.Body>
    </Card>
  );
}