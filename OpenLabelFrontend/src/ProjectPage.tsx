import React from "react";
import { useParams } from "react-router-dom";
import { Container, Row, Col, Dropdown, Button } from "react-bootstrap";
import Table from "react-bootstrap/Table";

const ProjectPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  // For now, we will use a static list of projects
  const inputs = [
    {
      id: "1",
      name: "Image 1",
      description: "Description for input one",
    },
    {
      id: "2",
      name: "Image 2",
      description: "Description for input two",
    },
    {
      id: "3",
      name: "Image 3",
      description: "Description for input three",
    },
  ];
  const projects = [
    {
      id: "1",
      name: "Project One",
      description: "Description for project one",
    },
    {
      id: "2",
      name: "Project Two",
      description: "Description for project two",
    },
    {
      id: "3",
      name: "Project Three",
      description: "Description for project three",
    },
  ];

  const project = projects.find((p) => p.id === id);

  if (!project) {
    return <div>Project not found</div>;
  }

  return (
    <Container className="mt-5 bg-secondary">
      <h1>{project.name}</h1>
      <p>{project.description}</p>
      <Row>
        <Col>
          <Dropdown>
            <Dropdown.Toggle variant="success" id="dropdown-basic">
              Actions
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <Dropdown.Item href="#/action-1">Action</Dropdown.Item>
              <Dropdown.Item href="#/action-2">Another action</Dropdown.Item>
              <Dropdown.Item href="#/action-3">Something else</Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
        </Col>
        <Col>
          <Dropdown>
            <Dropdown.Toggle variant="success" id="dropdown-basic">
              Columns
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <Dropdown.Item href="#/action-1">Action</Dropdown.Item>
              <Dropdown.Item href="#/action-2">Another action</Dropdown.Item>
              <Dropdown.Item href="#/action-3">Something else</Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
        </Col>
        <Col>
          <Dropdown>
            <Dropdown.Toggle variant="success" id="dropdown-basic">
              Filters
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <Dropdown.Item href="#/action-1">Action</Dropdown.Item>
              <Dropdown.Item href="#/action-2">Another action</Dropdown.Item>
              <Dropdown.Item href="#/action-3">Something else</Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
        </Col>
        <Col>
          <Dropdown>
            <Dropdown.Toggle variant="success" id="dropdown-basic">
              Sort
            </Dropdown.Toggle>
            <Dropdown.Menu>
              <Dropdown.Item href="#/action-1">Action</Dropdown.Item>
              <Dropdown.Item href="#/action-2">Another action</Dropdown.Item>
              <Dropdown.Item href="#/action-3">Something else</Dropdown.Item>
            </Dropdown.Menu>
          </Dropdown>
          <Button>Label All Tasks</Button>
        </Col>
        <Col>
          <Button>Export</Button>
        </Col>
        <Col>
          <Button>Import</Button>
        </Col>
        <Col>
          <Button>Refresh</Button>
        </Col>
      </Row>
      <Row>
        <Table striped bordered hover>
          <thead>
            <tr>
              <th>#</th>
              <th>Name</th>
              <th>Description</th>
            </tr>
          </thead>
          <tbody>
            {inputs.map((input) => (
              <tr key={input.id}>
                <td>{input.id}</td>
                <td>{input.name}</td>
                <td>{input.description}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      </Row>
    </Container>
  );
};

export default ProjectPage;
