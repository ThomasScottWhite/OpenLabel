import { useEffect, useState } from "react";
import { Card, Button, Row, Col, Spinner, Container } from "react-bootstrap";
import { Link } from "react-router-dom";
import { BsTrash, BsGear } from "react-icons/bs";

interface ProjectSettings {
  dateType: "image" | "text";
  annotationType: "object-detection" | "classification";
  isPublic: boolean;
}

interface ProjectMember {
  userId: string;
  joinedAt: string;
}

interface Project {
  _id: string;
  name: string;
  description: string;
  createdBy: string;
  createdAt: string;
  updatedAt: string;
  members: ProjectMember[];
  settings: ProjectSettings;
}

const ProjectList = () => {
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
        setProjects(data); // assuming response is { projects: [...] }
      } catch (error) {
        console.error("Error fetching projects:", error);
        alert("Failed to load projects");
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  if (loading) {
    return <Spinner animation="border" />;
  }

  return (
    <Row className="g-4">
      {projects.map((project) => (
        <Col key={project._id} xs={12} md={6} lg={4}>
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
                    {project.settings.data_type} /{" "}
                    {project.settings.annotation_type}
                  </Card.Text>
                </div>
                <Button
                  variant="outline-secondary"
                  size="sm"
                  className="rounded-circle"
                  title="Settings"
                >
                  <BsGear size={16} />
                </Button>
              </div>
              <div className="d-flex gap-2 mt-3">
                <Link
                  to={`/projects/${project._id}`}
                  className="btn btn-primary btn-sm w-100"
                >
                  Open
                </Link>
                <Button variant="outline-danger" size="sm" className="w-100">
                  <BsTrash size={16} className="me-1" />
                  Delete
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>
      ))}
    </Row>
  );
};

const Projects = () => {
  return (
    <Container className="py-5">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="fw-bold">Projects</h1>
        <Button variant="success" className="rounded-pill px-4">
          + New Project
        </Button>
      </div>
      <ProjectList />
    </Container>
  );
};

export default Projects;
