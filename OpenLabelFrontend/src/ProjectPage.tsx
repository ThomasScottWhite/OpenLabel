import React from 'react';
import { useParams } from 'react-router-dom';
import { Container, Row, Col } from 'react-bootstrap';

const ProjectPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  
  // For now, we will use a static list of projects
  const projects = [
    { id: '1', name: 'Project One', description: 'Description for project one' },
    { id: '2', name: 'Project Two', description: 'Description for project two' },
    { id: '3', name: 'Project Three', description: 'Description for project three' },
  ];

  const project = projects.find(p => p.id === id);

  if (!project) {
    return <div>Project not found</div>;
  }

  return (
    <Container className="mt-5">
      <Row>
        <Col>
          <h1>{project.name}</h1>
          <p>{project.description}</p>
        </Col>
      </Row>
    </Container>
  );
};

export default ProjectPage;
