// Annotator.tsx
import {
  Container,
  Row,
  Col,
  Card,
  ListGroup,
  Button,
  ButtonGroup,
} from "react-bootstrap";
import { useParams } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import ObjectDetectionAnnotator, {
  BoundingBox,
} from "./annotators/ObjectDetectionAnnotator";
import ImageClassificationAnnotator from "./annotators/ImageClassificationAnnotator";
import TextClassificationAnnotator from "./annotators/TextClassificationAnnotator";

const mockFiles = [
  "/images/sample1.jpg",
  "/images/sample2.jpg",
  "/images/sample3.jpg",
];

const mockTexts = [
  "The quick brown fox jumps over the lazy dog.",
  "React is a JavaScript library for building user interfaces.",
  "Artificial intelligence is transforming the world.",
];

const LABELS = ["person", "car", "tree", "animal", "unknown"];
const CANVAS_HEIGHT = 600;

const Annotator = () => {
  const { id } = useParams();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [annotations, setAnnotations] = useState<BoundingBox[][]>([[], [], []]);
  const [imageLabels, setImageLabels] = useState<string[]>(
    Array(mockFiles.length).fill("unknown")
  );
  const [textLabels, setTextLabels] = useState<string[]>(
    Array(mockTexts.length).fill("unknown")
  );
  const [activeLabel, setActiveLabel] = useState("person");
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const [canvasDims, setCanvasDims] = useState({
    width: 0,
    height: CANVAS_HEIGHT,
  });

  const currentFile = mockFiles[currentIndex];
  const currentText = mockTexts[currentIndex];
  const currentBoxes = annotations[currentIndex] || [];
  const annotationType = "text"; // Change to "classification" or "text" to test other modes

  useEffect(() => {
    if (
      annotationType === "object-detection" ||
      annotationType === "classification"
    ) {
      const img = new Image();
      img.src = currentFile;
      img.onload = () => setImage(img);
    }
  }, [currentFile, annotationType]);

  useEffect(() => {
    const updateCanvasSize = () => {
      if (canvasContainerRef.current) {
        setCanvasDims({
          width: canvasContainerRef.current.clientWidth,
          height: CANVAS_HEIGHT,
        });
      }
    };
    updateCanvasSize();
    window.addEventListener("resize", updateCanvasSize);
    return () => window.removeEventListener("resize", updateCanvasSize);
  }, []);

  const handleBoxChange = (updated: BoundingBox[]) => {
    const newAnnotations = [...annotations];
    newAnnotations[currentIndex] = updated;
    setAnnotations(newAnnotations);
  };

  const handleLabelChange = (label: string) => {
    setActiveLabel(label);
    if (annotationType === "object-detection" && selectedBoxId) {
      const updated = [...annotations];
      updated[currentIndex] = updated[currentIndex].map((box) =>
        box.id === selectedBoxId ? { ...box, label } : box
      );
      setAnnotations(updated);
    } else if (annotationType === "classification") {
      const updated = [...imageLabels];
      updated[currentIndex] = label;
      setImageLabels(updated);
    } else if (annotationType === "text") {
      const updated = [...textLabels];
      updated[currentIndex] = label;
      setTextLabels(updated);
    }
  };

  const handleDelete = () => {
    if (!selectedBoxId) return;
    const updated = [...annotations];
    updated[currentIndex] = updated[currentIndex].filter(
      (b) => b.id !== selectedBoxId
    );
    setAnnotations(updated);
    setSelectedBoxId(null);
  };

  return (
    <Container fluid className="py-4">
      <Row>
        <Col md={2}>
          <Card className="p-3 mb-3">
            <h5>{annotationType === "text" ? "Texts" : "Files"}</h5>
            <ListGroup>
              {(annotationType === "text" ? mockTexts : mockFiles).map(
                (item, index) => (
                  <ListGroup.Item
                    key={item}
                    active={index === currentIndex}
                    action
                    onClick={() => setCurrentIndex(index)}
                  >
                    {annotationType === "text" ? `Text ${index + 1}` : item}
                  </ListGroup.Item>
                )
              )}
            </ListGroup>
          </Card>
        </Col>

        <Col md={8}>
          <Card className="p-3 mb-3 text-center" ref={canvasContainerRef}>
            {image && annotationType === "object-detection" && (
              <ObjectDetectionAnnotator
                image={image}
                width={canvasDims.width}
                height={canvasDims.height}
                annotations={currentBoxes}
                onChange={handleBoxChange}
                selectedId={selectedBoxId}
                onSelect={setSelectedBoxId}
                activeLabel={activeLabel}
              />
            )}
            {image && annotationType === "classification" && (
              <ImageClassificationAnnotator
                image={image}
                width={canvasDims.width}
                height={canvasDims.height}
                label={imageLabels[currentIndex]}
                onLabelChange={handleLabelChange}
                labelOptions={LABELS}
              />
            )}
            {annotationType === "text" && (
              <TextClassificationAnnotator
                text={currentText}
                label={textLabels[currentIndex]}
                onLabelChange={handleLabelChange}
                labelOptions={LABELS}
              />
            )}

            <div className="mt-3 d-flex justify-content-center align-items-center gap-2 flex-wrap">
              <strong>Label:</strong>
              <ButtonGroup>
                {LABELS.map((label) => (
                  <Button
                    key={label}
                    variant={
                      activeLabel === label ? "primary" : "outline-primary"
                    }
                    onClick={() => handleLabelChange(label)}
                  >
                    {label}
                  </Button>
                ))}
              </ButtonGroup>
              {annotationType === "object-detection" && (
                <Button
                  variant="danger"
                  onClick={handleDelete}
                  disabled={!selectedBoxId}
                >
                  Delete Selected
                </Button>
              )}
            </div>
          </Card>
        </Col>

        <Col md={2}>
          <Card className="p-3 mb-3">
            <h5>
              {annotationType === "object-detection"
                ? "Boxes"
                : annotationType === "text"
                ? "Text Label"
                : "Label"}
            </h5>
            {annotationType === "object-detection" ? (
              <ul style={{ fontSize: "0.85rem" }}>
                {currentBoxes.map((box) => (
                  <li key={box.id}>
                    <strong>{box.label}</strong> — x:{box.x.toFixed(2)} y:
                    {box.y.toFixed(2)}
                  </li>
                ))}
              </ul>
            ) : annotationType === "text" ? (
              <p style={{ fontSize: "1rem" }}>
                <strong>{textLabels[currentIndex]}</strong>
              </p>
            ) : (
              <p style={{ fontSize: "1rem" }}>
                <strong>{imageLabels[currentIndex]}</strong>
              </p>
            )}
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Annotator;
