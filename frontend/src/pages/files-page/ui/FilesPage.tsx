"use client";

import { useEffect, useState } from "react";
import { Alert, Button, Card, Col, Container, Row } from "react-bootstrap";
import { uploadFile } from "@/features/file-upload";
import { FilesWidget } from "@/widgets/files-widget";
import { AlertsWidget } from "@/widgets/alerts-widget";
import { type FileItem, type AlertItem, getAlerts, getFiles } from "@/entities";
import { UploadModal } from "@/features/file-upload";

export default function FilesPage() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  async function loadData() {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const [filesData, alertsData] = await Promise.all([getFiles(), getAlerts()]);
      setFiles(filesData);
      setAlerts(alertsData);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Произошла ошибка");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    void loadData();
  }, []);

  async function handleUpload(title: string, file: File) {
    await uploadFile(title, file);
    await loadData();
  }

  return (
    <Container fluid className="py-4 px-4 bg-light min-vh-100">
      <Row className="justify-content-center">
        <Col xxl={10} xl={11}>
          <Card className="shadow-sm border-0 mb-4">
            <Card.Body className="p-4">
              <div className="d-flex justify-content-between align-items-start gap-3 flex-wrap">
                <div>
                  <h1 className="h3 mb-2">Управление файлами</h1>
                  <p className="text-secondary mb-0">
                    Загрузка файлов, просмотр статусов обработки и ленты алертов.
                  </p>
                </div>
                <div className="d-flex gap-2">
                  <Button variant="outline-secondary" onClick={() => void loadData()}>
                    Обновить
                  </Button>
                  <Button variant="primary" onClick={() => setShowModal(true)}>
                    Добавить файл
                  </Button>
                </div>
              </div>
            </Card.Body>
          </Card>

          {errorMessage ? (
            <Alert variant="danger" className="shadow-sm">
              {errorMessage}
            </Alert>
          ) : null}

          <FilesWidget files={files} isLoading={isLoading} />
          <AlertsWidget alerts={alerts} isLoading={isLoading} />
        </Col>
      </Row>

      <UploadModal show={showModal} onHide={() => setShowModal(false)} onSubmit={handleUpload} />
    </Container>
  );
}