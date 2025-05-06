import { useParams } from "react-router-dom";
import {
  Container,
  Button,
  ProgressBar,
  Card,
  Row,
  Col,
  Form,
  InputGroup,
  Spinner,
  Alert,
  Tabs,
  Tab,
  Badge,
} from "react-bootstrap";
import { useRef, useState, useEffect } from "react";
import ProjectFileTable from "./ProjectFileTable";
export interface ProjectFile {
  fileId: string;
  projectId: string;
  createdAt: string;
  createdBy: string;
  filename: string;
  size: number;
  contentType: string;
  type: "image" | "text";
  status: "unannotated" | "annotated" | string;
  width?: number;
  height?: number;
}

export interface ProjectSettings {
  dataType: "image" | "text";
  annotationType: "object-detection" | "classification";
  isPublic: boolean;
  labels: string[];
}

export interface ProjectMember {
  userId: string;
  roleId: string;
  joinedAt: string;
}

export interface Project {
  projectId: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  settings: ProjectSettings;
  members: ProjectMember[];
  files: ProjectFile[];
  numFiles: number;
  numAnnotated: number;
}

const ProjectPage = () => {
  const { id } = useParams();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [project, setProject] = useState<any>(null);
  const [files, setFiles] = useState<any[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<any[]>([]);
  const [filterColumn, setFilterColumn] = useState("size");
  const [filterCondition, setFilterCondition] = useState(">");
  const [filterValue, setFilterValue] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("files");
  const [editedSettings, setEditedSettings] = useState<ProjectSettings | null>(
    null
  );
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState("");
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [newLabel, setNewLabel] = useState("");
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState("");

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const res = await fetch(`/api/projects/${id}`, {
          method: "GET",
          headers: {
            Authorization: `Bearer ${localStorage.getItem("token")}`,
          },
        });
        if (!res.ok) throw new Error("Failed to fetch project");
        const data = await res.json();
        setProject(data);
        setFiles(data.files || []);
        setEditedSettings(data.settings);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    fetchProject();
  }, [id]);

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selectedFiles = event.target.files;
    if (!selectedFiles || selectedFiles.length === 0) return;

    const formData = new FormData();
    for (const file of selectedFiles) {
      formData.append("files", file);
    }

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`/api/projects/${id}/files`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("Upload failed:", errorData);
        return;
      }

      const result = await response.json();
      console.log("Uploaded files:", result);
    } catch (err) {
      console.error("Error uploading files:", err);
    }
  };

  const handleDeleteSelected = async () => {
    if (selectedFiles.length === 0) return;

    try {
      const token = localStorage.getItem("token");
      // This is bad, this need a single request
      for (const file of selectedFiles) {
        const response = await fetch(`/api/files/${file.fileId}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error(`Failed to delete file ${file.fileId}:`, errorData);
          alert(`Failed to delete file: ${file.filename}`);
          return;
        }
      }

      const res = await fetch(`/api/projects/${id}`);
      if (!res.ok) throw new Error("Failed to fetch project after deletion");
      const data = await res.json();
      setProject(data);
      setFiles(data.files || []);
      setSelectedFiles([]);
    } catch (err) {
      console.error("Error deleting files:", err);
      alert("An error occurred while deleting files.");
    }
  };

  const handleDownloadSelected = () => {
    alert(
      `Pretending to download: ${selectedFiles.map((f) => f.name).join(", ")}`
    );
  };

  const applyAdvancedFilter = (file: any) => {
    if (filterColumn === "size") {
      const sizeKB = file.size / 1024;
      const filterNum = parseFloat(filterValue);
      if (isNaN(filterNum)) return true;

      switch (filterCondition) {
        case ">":
          return sizeKB > filterNum;
        case "<":
          return sizeKB < filterNum;
        case "=":
          return sizeKB === filterNum;
        default:
          return true;
      }
    } else if (filterColumn === "type") {
      return file.type.toLowerCase().includes(filterValue.toLowerCase());
    } else if (filterColumn === "name") {
      return file.name.toLowerCase().includes(filterValue.toLowerCase());
    }
    return true;
  };

  const filteredFiles = files.filter(applyAdvancedFilter);

  const handleSaveSettings = async () => {
    if (!editedSettings) return;

    setSaving(true);
    setSaveError("");
    setSaveSuccess(false);

    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`/api/projects/${id}`, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ settings: editedSettings }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail || "Failed to update project settings"
        );
      }

      // Update the project state with new settings
      setProject({
        ...project,
        settings: editedSettings,
      });
      setSaveSuccess(true);

      // Reset success message after 3 seconds
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err: any) {
      setSaveError(err.message);
      console.error("Error updating project settings:", err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddLabel = () => {
    if (!newLabel.trim() || !editedSettings) return;

    const updatedLabels = [...editedSettings.labels, newLabel.trim()];
    setEditedSettings({
      ...editedSettings,
      labels: updatedLabels,
    });
    setNewLabel("");
  };

  const handleRemoveLabel = (labelToRemove: string) => {
    if (!editedSettings) return;

    const updatedLabels = editedSettings.labels.filter(
      (label) => label !== labelToRemove
    );
    setEditedSettings({
      ...editedSettings,
      labels: updatedLabels,
    });
  };

  const handleExportProject = async () => {
    try {
      setExporting(true);
      setExportError("");

      const token = localStorage.getItem("token");
      const response = await fetch(`/api/projects/${id}/export`, {
        method: "GET",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to export project");
      }

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers.get("Content-Disposition");
      let filename = `project-${id}-export.zip`;
      if (contentDisposition) {
        const filenameMatch = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(
          contentDisposition
        );
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1].replace(/['"]/g, "");
        }
      }

      // Create a blob from the response
      const blob = await response.blob();

      // Create a download link and trigger the download
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err: any) {
      console.error("Error exporting project:", err);
      setExportError(err.message);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <Container className="py-5 text-center">
        <Spinner animation="border" />
      </Container>
    );
  }

  if (error) {
    return (
      <Container className="py-5">
        <Alert variant="danger">Error: {error}</Alert>
      </Container>
    );
  }

  return (
    <Container className="py-5">
      <h1 className="mb-4">{project.name}</h1>

      <Card className="mb-4 p-3">
        <div className="d-flex justify-content-between align-items-start">
          <div>
            <h4>Project Overview</h4>
            <p>{project.description}</p>
            <ProgressBar
              now={(project.numAnnotated / project.numFiles) * 100}
              label={`${project.numAnnotated}/${project.numFiles} Annotated`}
            />
          </div>
          <div>
            <Button
              variant="outline-success"
              onClick={handleExportProject}
              disabled={exporting || project.numFiles === 0}
              className="ms-2"
            >
              {exporting ? (
                <>
                  <Spinner
                    as="span"
                    animation="border"
                    size="sm"
                    role="status"
                    aria-hidden="true"
                    className="me-2"
                  />
                  Exporting...
                </>
              ) : (
                "Export Project"
              )}
            </Button>
            {exportError && (
              <div className="text-danger mt-2 small">{exportError}</div>
            )}
          </div>
        </div>
      </Card>

      <Tabs
        activeKey={activeTab}
        onSelect={(k) => k && setActiveTab(k)}
        className="mb-3"
      >
        <Tab eventKey="files" title="Files">
          {/* Action Bar */}
          <div className="d-flex justify-content-between flex-wrap align-items-end gap-2 mb-3">
            <div className="d-flex gap-2 flex-wrap align-items-end">
              <Button
                variant="outline-primary"
                onClick={() => fileInputRef.current?.click()}
              >
                Upload File
              </Button>
              <Button
                variant="outline-danger"
                disabled={selectedFiles.length === 0}
                onClick={handleDeleteSelected}
              >
                Delete Selected
              </Button>
              <Button
                variant="outline-secondary"
                disabled={selectedFiles.length === 0}
                onClick={handleDownloadSelected}
              >
                Download Selected
              </Button>
            </div>

            {/* Advanced Filter */}
            <InputGroup className="w-auto">
              <Form.Select
                value={filterColumn}
                onChange={(e) => setFilterColumn(e.target.value)}
              >
                <option value="size">Size (KB)</option>
                <option value="name">Name</option>
                <option value="type">Type</option>
              </Form.Select>
              <Form.Select
                value={filterCondition}
                onChange={(e) => setFilterCondition(e.target.value)}
              >
                <option value=">">&gt;</option>
                <option value="<">&lt;</option>
                <option value="=">=</option>
              </Form.Select>
              <Form.Control
                placeholder="Filter value"
                value={filterValue}
                onChange={(e) => setFilterValue(e.target.value)}
              />
            </InputGroup>

            <Button variant="success" href={`/projects/${id}/annotator`}>
              Launch Annotator
            </Button>
          </div>

          {/* Hidden File Input */}
          <Form.Control
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            multiple
            style={{ display: "none" }}
          />

          {/* File Table */}
          <ProjectFileTable
            files={filteredFiles}
            onSelectionChange={setSelectedFiles}
          />
        </Tab>

        <Tab eventKey="settings" title="Settings">
          <Card className="p-3">
            <h4 className="mb-4">Project Settings</h4>

            {saveSuccess && (
              <Alert variant="success">Settings saved successfully!</Alert>
            )}

            {saveError && <Alert variant="danger">Error: {saveError}</Alert>}

            {editedSettings && (
              <Form>
                <Form.Group className="mb-3">
                  <Form.Label>Data Type</Form.Label>
                  <Form.Select
                    value={editedSettings.dataType}
                    onChange={(e) =>
                      setEditedSettings({
                        ...editedSettings,
                        dataType: e.target.value as "image" | "text",
                      })
                    }
                  >
                    <option value="image">Image</option>
                    <option value="text">Text</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Annotation Type</Form.Label>
                  <Form.Select
                    value={editedSettings.annotationType}
                    onChange={(e) =>
                      setEditedSettings({
                        ...editedSettings,
                        annotationType: e.target.value as
                          | "object-detection"
                          | "classification",
                      })
                    }
                  >
                    <option value="object-detection">Object Detection</option>
                    <option value="classification">Classification</option>
                  </Form.Select>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Check
                    type="switch"
                    id="public-switch"
                    label="Public Project"
                    checked={editedSettings.isPublic}
                    onChange={(e) =>
                      setEditedSettings({
                        ...editedSettings,
                        isPublic: e.target.checked,
                      })
                    }
                  />
                  <Form.Text className="text-muted">
                    Public projects can be seen by anyone.
                  </Form.Text>
                </Form.Group>

                <Form.Group className="mb-3">
                  <Form.Label>Labels</Form.Label>
                  <div className="mb-2">
                    {editedSettings.labels.length === 0 ? (
                      <p className="text-muted">No labels defined yet.</p>
                    ) : (
                      <div className="d-flex flex-wrap gap-2">
                        {editedSettings.labels.map((label, idx) => (
                          <Badge
                            key={idx}
                            bg="primary"
                            className="p-2 d-flex align-items-center"
                          >
                            {label}
                            <Button
                              variant="link"
                              className="p-0 ps-2 text-white"
                              onClick={() => handleRemoveLabel(label)}
                            >
                              ✕
                            </Button>
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  <InputGroup>
                    <Form.Control
                      placeholder="Add new label"
                      value={newLabel}
                      onChange={(e) => setNewLabel(e.target.value)}
                      onKeyPress={(e) =>
                        e.key === "Enter" &&
                        (e.preventDefault(), handleAddLabel())
                      }
                    />
                    <Button
                      variant="outline-secondary"
                      onClick={handleAddLabel}
                    >
                      Add
                    </Button>
                  </InputGroup>
                </Form.Group>

                <div className="d-flex justify-content-end mt-4">
                  <Button
                    variant="primary"
                    onClick={handleSaveSettings}
                    disabled={saving}
                  >
                    {saving ? (
                      <>
                        <Spinner
                          as="span"
                          animation="border"
                          size="sm"
                          role="status"
                          aria-hidden="true"
                          className="me-2"
                        />
                        Saving...
                      </>
                    ) : (
                      "Save Settings"
                    )}
                  </Button>
                </div>
              </Form>
            )}
          </Card>
        </Tab>
      </Tabs>
    </Container>
  );
};

export default ProjectPage;
