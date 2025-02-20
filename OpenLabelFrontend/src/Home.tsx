import { Container, Row, Col, Button } from 'react-bootstrap';
import { Link } from "react-router-dom";

const Home = () => {
  return (
    <Container className="text-center mt-5">
      <Row>
        <Col>
          <h1>Welcome to OpenLabel</h1>
          <p>Your platform for managing projects efficiently.</p>
          <Button color="primary" className="mr-2">Create Account</Button>
          <Link to="/login">
          <Button color="secondary">Login</Button>
          </Link>
        </Col>
      </Row>
    </Container>
  );
};

export default Home;
