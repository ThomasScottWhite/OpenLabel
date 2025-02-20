import { Container, Button } from "react-bootstrap";

function NotFound() {
  return (
    <Container className="text-center mt-5">
      <h1>404</h1>
      <p>Page Not Found</p>
      <Button href="/" variant="primary">
        Go to Home
      </Button>
    </Container>
  );
}

export default NotFound;
