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
  id: number;
  name: string;
  description: string;
  size: number;
  type: string;
  uploaded_at: string;
}

export interface Project {
  id: number;
  name: string;
  description: string;
  type: string;
  annotator_layout: string;
  num_files: number;
  num_annotated: number;
  files: ProjectFile[];
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
        const res = await fetch(`http://localhost:8000/projects/${id}`);
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

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selected = event.target.files;
    if (!selected) return;

    const newFiles = Array.from(selected).map((f) => ({
      name: f.name,
      size: f.size,
      type: f.type || "Unknown",
      uploadedAt: new Date().toISOString(),
    }));

    setFiles((prev) => [...prev, ...newFiles]);
  };

  const handleDeleteSelected = () => {
    const selectedNames = selectedFiles.map((f) => f.name);
    setFiles(files.filter((f) => !selectedNames.includes(f.name)));
    setSelectedFiles([]);
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
          label={`${project.num_annotated}/${project.num_files} Annotated`}
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
