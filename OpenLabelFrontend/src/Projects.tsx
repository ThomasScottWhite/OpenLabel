import { useEffect, useState } from "react";
import { Card, Button, Row, Col, Spinner, Container } from "react-bootstrap";
import { Link } from "react-router-dom";
import { BsTrash } from "react-icons/bs";

import { Modal, Form, Alert } from "react-bootstrap";

interface ProjectSettings {
  dataType: "image" | "text";
  annotatationType: "object-detection" | "classification";
  isPublic: boolean;
}

interface ProjectMember {
  userId: string;
  joinedAt: string;
}

interface Project {
  projectId: string;
  name: string;
  description: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  members: ProjectMember[];
  settings: ProjectSettings;
}

const ProjectList = ({ reloadFlag }: { reloadFlag: boolean }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const token = localStorage.getItem("token");

        const response = await fetch("/api/projects", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          throw new Error("Failed to fetch projects");
        }

        const data = await response.json();
        setProjects(data);
      } catch (error) {
        console.error("Error fetching projects:", error);
        alert("Failed to load projects");
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, [reloadFlag]);

  if (loading) {
    return <Spinner animation="border" />;
  }

  return (
    <Row className="g-4">
      {projects.map((project) => (
        <Col key={project.projectId} xs={12} md={6} lg={4}>
          <Card className="h-100 shadow-sm border-0 rounded-4">
            <Card.Body>
              <div className="d-flex justify-content-between align-items-start mb-2">
                <div>
                  <Card.Title className="mb-1">{project.name}</Card.Title>
                  <Card.Text
                    className="text-muted"
                    style={{ fontSize: "0.9rem" }}
                  >
                    {project.description}
                  </Card.Text>
                  <Card.Text
                    className="text-muted"
                    style={{ fontSize: "0.8rem" }}
                  >
                    {project.settings.dataType} /{" "}
                    {project.settings.annotatationType}
                  </Card.Text>
                </div>
              </div>
              <div className="d-flex gap-2 mt-3">
                <Link
                  to={`/projects/${project.projectId}`}
                  className="btn btn-primary btn-sm w-100"
                >
                  Open
                </Link>
                {/* <Button variant="outline-danger" size="sm" className="w-100">
                  <BsTrash size={16} className="me-1" />
                  Delete
                </Button> */}
              </div>
            </Card.Body>
          </Card>
        </Col>
      ))}
    </Row>
  );
};

const Projects = () => {
  const [show, setShow] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    data_type: "image",
    annotation_type: "object-detection",
    is_public: true,
  });
  const [error, setError] = useState<string | null>(null);
  const [reloadFlag, setReloadFlag] = useState(false); // to trigger reload

  type FormElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

  const handleInputChange = (e: React.ChangeEvent<FormElement>) => {
    const { name, value, type } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]:
        type === "checkbox" && "checked" in e.target
          ? (e.target as HTMLInputElement).checked
          : value,
    }));
  };

  const handleSubmit = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("/api/projects", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const err = await response.text();
        throw new Error(err);
      }

      setReloadFlag(!reloadFlag); // trigger project list reload
      setShow(false);
      setFormData({
        name: "",
        description: "",
        data_type: "image",
        annotation_type: "object-detection",
        is_public: true,
      });
    } catch (err: any) {
      setError(err.message || "Failed to create project");
    }
  };

  return (
    <Container className="py-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="fw-bold">Projects</h1>
        <Button
          variant="success"
          className="rounded-pill px-4"
          onClick={() => setShow(true)}
        >
          + New Project
        </Button>
      </div>

      <ProjectList reloadFlag={reloadFlag} />

      <Modal show={show} onHide={() => setShow(false)} centered>
        <Modal.Header closeButton>
          <Modal.Title>Create New Project</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {error && <Alert variant="danger">{error}</Alert>}
          <Form>
            <Form.Group className="mb-3">
              <Form.Label>Project Name</Form.Label>
              <Form.Control
                type="text"
                name="name"
                value={formData.name}
                onChange={handleInputChange}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Description</Form.Label>
              <Form.Control
                as="textarea"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
              />
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Data Type</Form.Label>
              <Form.Select
                name="data_type"
                value={formData.data_type}
                onChange={handleInputChange}
              >
                <option value="image">Image</option>
                <option value="text">Text</option>
              </Form.Select>
            </Form.Group>
            <Form.Group className="mb-3">
              <Form.Label>Annotation Type</Form.Label>
              <Form.Select
                name="annotation_type"
                value={formData.annotation_type}
                onChange={handleInputChange}
              >
                <option value="object-detection">Object Detection</option>
                <option value="classification">Classification</option>
              </Form.Select>
            </Form.Group>
            <Form.Check
              type="checkbox"
              label="Public Project"
              name="is_public"
              checked={formData.is_public}
              onChange={handleInputChange}
            />
          </Form>
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShow(false)}>
            Cancel
          </Button>
          <Button variant="primary" onClick={handleSubmit}>
            Create
          </Button>
        </Modal.Footer>
      </Modal>
    </Container>
  );
};

export default Projects;
