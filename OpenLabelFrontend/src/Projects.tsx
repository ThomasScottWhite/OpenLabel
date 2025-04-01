import { Card, Button, Row, Col, Container } from "react-bootstrap";
import { Link } from "react-router-dom";
import { BsTrash, BsGear } from "react-icons/bs";

const projects = [
  { id: 1, name: "Project One", description: "Description for project one" },
  { id: 2, name: "Project Two", description: "Description for project two" },
  {
    id: 3,
    name: "Project Three",
    description: "Description for project three",
  },
];

const ProjectList = () => {
  return (
    <Row className="g-4">
      {projects.map((project) => (
        <Col key={project.id} xs={12} md={6} lg={4}>
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
                  to={`/projects/${project.id}`}
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
