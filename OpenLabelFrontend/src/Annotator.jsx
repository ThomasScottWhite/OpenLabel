import { Stage, Layer, Image } from "react-konva";
import useImage from "use-image";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import Button from "react-bootstrap/Button";
import { useState, useEffect } from "react";

const LocalImage = () => {
  const [image] = useImage("/pexels-pixabay-210019.jpg");
  const [imgSize, setImgSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (image) {
      const imgWidth = image.width;
      const imgHeight = image.height;
      const stageWidth = window.innerWidth;
      const stageHeight = window.innerHeight;

      const scale = Math.min(stageWidth / imgWidth, stageHeight / imgHeight);

      setImgSize({
        width: imgWidth * scale,
        height: imgHeight * scale,
      });
    }
  }, [image]);

  return image ? (
    <Image image={image} width={imgSize.width} height={imgSize.height} />
  ) : null;
};

const Modes = {
  Category: "Category",
  Box: "Box",
  Polygon: "Polygon",
};

const Categorys = {
  Car: "Car",
  NotCar: "NoCar",
};

export const Annotator = () => {
  const [dataType, setCurrentDataType] = useState("Image");
  const [currentCatagory, setCurrentCatagory] = useState("Car");
  const [currentMode, setCurrentMode] = useState("Category");

  return (
    <Container
      fluid
      className="h-100 w-100 dflex flex-column p-0 justify-content-center bg-secondary"
    >
      <Row className="w-100 m-0 p-2">
        <Col className="d-flex justify-content-center">
          {Object.values(Modes).map((mode) => (
            <Button
              className="mx-2"
              onClick={() => setCurrentMode(mode)}
              variant={currentMode === mode ? "primary" : "secondary"}
            >
              {mode}
            </Button>
          ))}
        </Col>
      </Row>

      <Row className="flex-grow-1 w-100 m-0 p-0">
        <Col className="p-0 content-center">
          <Stage width={window.innerWidth} height={window.innerHeight}>
            <Layer>
              <LocalImage />
            </Layer>
          </Stage>
        </Col>
      </Row>

      <Row className="w-100 m-0 p-2">
        <Col className="d-flex justify-content-center">
          {Object.values(Categorys).map((cat) => (
            <Button
              className="mx-2"
              onClick={() => setCurrentCatagory(cat)}
              variant={currentCatagory === cat ? "primary" : "secondary"}
            >
              {cat}
            </Button>
          ))}
        </Col>
      </Row>
    </Container>
  );
};

export default Annotator;
