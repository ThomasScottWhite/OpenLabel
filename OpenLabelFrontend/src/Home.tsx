// Home Page
import { Container, Row, Col, Button } from "react-bootstrap";
import { Link } from "react-router-dom";

const Home = () => {
  return (
    <Container className="text-center min-vh-100 d-flex flex-column justify-content-center align-items-center text-dark">
      <Row className="mb-4">
        <Col>
          <h1 className="display-3 fw-bold text-primary">OpenLabel</h1>
          <p className="lead text-muted">
            Open Source Local AI-Assisted Labeling Software.
          </p>
        </Col>
      </Row>
      <Row>
        <Col>
          <Link to="/login">
            <Button
              variant="primary"
              size="lg"
              className="me-3 rounded-pill px-4"
            >
              Login
            </Button>
          </Link>
          <Link to="/create-account">
            <Button
              variant="outline-primary"
              size="lg"
              className="rounded-pill px-4"
            >
              Create Account
            </Button>
          </Link>
        </Col>
      </Row>
    </Container>
  );
};

export default Home;
