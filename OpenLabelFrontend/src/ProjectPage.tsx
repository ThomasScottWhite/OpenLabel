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

  useEffect(() => {
    const fetchProject = async () => {
      try {
        const res = await fetch(`/api/projects/${id}`);
        if (!res.ok) throw new Error("Failed to fetch project");
        const data = await res.json();
        setProject(data);
        setFiles(data.files || []);
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
        <h4>Project Overview</h4>
        <p>{project.description}</p>
        <ProgressBar
          now={(project.num_annotated / project.num_files) * 100}
          label={`${project.numAnnotated}/${project.numFiles} Annotated`}
        />
      </Card>

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
    </Container>
  );
};

export default ProjectPage;
