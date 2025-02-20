import { Card, CardBody, CardTitle, CardText } from "react-bootstrap";
import { Link } from "react-router-dom";
const ProjectList = () => {
  const projects = [
    { id: 1, name: "Project One", description: "Description for project one" },
    { id: 2, name: "Project Two", description: "Description for project two" },
    {
      id: 3,
      name: "Project Three",
      description: "Description for project three",
    },
  ];

  return (
    <div>
      {projects.map((project) => (
        <Link to={`/projects/${project.id}`}>
        <Card key={project.id} className="mb-3">
          <CardBody>
            <CardTitle tag="h5">{project.name}</CardTitle>
            <CardText>{project.description}</CardText>
          </CardBody>
        </Card>
        </Link>
      ))}
    </div>
  );
};

export default ProjectList;
