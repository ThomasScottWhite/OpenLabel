import { useParams } from "react-router-dom";
import {
  Container,
  Row,
  Col,
  Button,
  Card,
  ListGroup,
  ButtonGroup,
} from "react-bootstrap";
import { useEffect, useRef, useState } from "react";
import { v4 as uuidv4 } from "uuid";

const mockFiles = [
  "/images/sample1.jpg",
  "/images/sample2.jpg",
  "/images/sample3.jpg",
];

const LABELS = ["person", "car", "tree", "animal", "unknown"];

interface RelativeBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
}

const CANVAS_HEIGHT = 600;

const Annotator = () => {
  const { id } = useParams();
  const [currentIndex, setCurrentIndex] = useState(0);
  const [annotations, setAnnotations] = useState<RelativeBox[][]>([[], [], []]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(
    null
  );
  const [activeLabel, setActiveLabel] = useState("person");
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);

  const currentFile = mockFiles[currentIndex];
  const currentBoxes = annotations[currentIndex] || [];

  const [canvasDims, setCanvasDims] = useState<{
    width: number;
    height: number;
  }>({
    width: 0,
    height: CANVAS_HEIGHT,
  });

  const [imageDrawData, setImageDrawData] = useState<{
    x: number;
    y: number;
    width: number;
    height: number;
    scale: number;
  } | null>(null);

  useEffect(() => {
    const img = new Image();
    img.src = currentFile;
    img.onload = () => setImage(img);
  }, [currentFile]);

  useEffect(() => {
    const updateCanvasSize = () => {
      const container = canvasRef.current?.parentElement;
      if (container) {
        setCanvasDims({
          width: container.clientWidth,
          height: CANVAS_HEIGHT,
        });
      }
    };
    updateCanvasSize();
    window.addEventListener("resize", updateCanvasSize);
    return () => window.removeEventListener("resize", updateCanvasSize);
  }, []);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas || !image) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const scale = Math.min(
      canvas.width / image.width,
      canvas.height / image.height
    );
    const imgWidth = image.width * scale;
    const imgHeight = image.height * scale;
    const offsetX = (canvas.width - imgWidth) / 2;
    const offsetY = (canvas.height - imgHeight) / 2;

    setImageDrawData({
      x: offsetX,
      y: offsetY,
      width: imgWidth,
      height: imgHeight,
      scale,
    });

    ctx.drawImage(image, offsetX, offsetY, imgWidth, imgHeight);

    for (const box of currentBoxes) {
      const absX = offsetX + box.x * imgWidth;
      const absY = offsetY + box.y * imgHeight;
      const absW = box.width * imgWidth;
      const absH = box.height * imgHeight;

      ctx.strokeStyle = box.id === selectedBoxId ? "cyan" : "red";
      ctx.lineWidth = box.id === selectedBoxId ? 3 : 2;
      ctx.strokeRect(absX, absY, absW, absH);

      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(absX, absY - 20, ctx.measureText(box.label).width + 10, 18);
      ctx.fillStyle = "white";
      ctx.font = "14px sans-serif";
      ctx.fillText(box.label, absX + 5, absY - 6);
    }
  };

  useEffect(() => {
    drawCanvas();
  }, [image, currentBoxes, canvasDims, selectedBoxId]);

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const click = getCanvasCoords(e);
    const found = findClickedBox(click.x, click.y);
    if (found) {
      setSelectedBoxId(found.id);
      return;
    }

    setStartPoint(click);
    setDrawing(true);
    setSelectedBoxId(null);
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!startPoint || !imageDrawData) return;
    const end = getCanvasCoords(e);

    const { x: offsetX, y: offsetY, width: imgW, height: imgH } = imageDrawData;

    const relStartX = Math.min(Math.max(startPoint.x - offsetX, 0), imgW);
    const relStartY = Math.min(Math.max(startPoint.y - offsetY, 0), imgH);
    const relEndX = Math.min(Math.max(end.x - offsetX, 0), imgW);
    const relEndY = Math.min(Math.max(end.y - offsetY, 0), imgH);

    const newBox: RelativeBox = {
      id: uuidv4(),
      x: Math.min(relStartX, relEndX) / imgW,
      y: Math.min(relStartY, relEndY) / imgH,
      width: Math.abs(relEndX - relStartX) / imgW,
      height: Math.abs(relEndY - relStartY) / imgH,
      label: activeLabel,
    };

    const updated = [...annotations];
    updated[currentIndex] = [...(updated[currentIndex] || []), newBox];
    setAnnotations(updated);
    setStartPoint(null);
    setDrawing(false);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!drawing || !startPoint || !imageDrawData) return;
    const curr = getCanvasCoords(e);
    const ctx = canvasRef.current?.getContext("2d");
    if (!ctx) return;

    drawCanvas();

    ctx.strokeStyle = "blue";
    ctx.lineWidth = 1;
    ctx.strokeRect(
      Math.min(startPoint.x, curr.x),
      Math.min(startPoint.y, curr.y),
      Math.abs(curr.x - startPoint.x),
      Math.abs(curr.y - startPoint.y)
    );
  };

  const findClickedBox = (x: number, y: number): RelativeBox | null => {
    if (!imageDrawData) return null;
    const { x: offsetX, y: offsetY, width: imgW, height: imgH } = imageDrawData;

    for (const box of currentBoxes) {
      const absX = offsetX + box.x * imgW;
      const absY = offsetY + box.y * imgH;
      const absW = box.width * imgW;
      const absH = box.height * imgH;
      if (x >= absX && x <= absX + absW && y >= absY && y <= absY + absH) {
        return box;
      }
    }
    return null;
  };

  const handleLabelChange = (label: string) => {
    setActiveLabel(label);

    if (selectedBoxId) {
      const updated = [...annotations];
      const updatedBoxes = updated[currentIndex].map((box) =>
        box.id === selectedBoxId ? { ...box, label } : box
      );
      updated[currentIndex] = updatedBoxes;
      setAnnotations(updated);
    }
  };

  const handleNext = () =>
    setCurrentIndex((i) => Math.min(i + 1, mockFiles.length - 1));
  const handlePrev = () => setCurrentIndex((i) => Math.max(i - 1, 0));
  const handleFileSelect = (index: number) => setCurrentIndex(index);

  return (
    <Container fluid className="py-4">
      <Row className="mb-3">
        <Col>
          <h3>Annotator — Project #{id}</h3>
          <p>
            Current File: <strong>{currentFile}</strong>
          </p>
        </Col>
        <Col className="text-end">
          <Button
            variant="secondary"
            onClick={handlePrev}
            disabled={currentIndex === 0}
          >
            Previous
          </Button>{" "}
          <Button
            variant="secondary"
            onClick={handleNext}
            disabled={currentIndex === mockFiles.length - 1}
          >
            Next
          </Button>{" "}
          <Button variant="success">Save Annotations</Button>
        </Col>
      </Row>

      <Row>
        {/* File List */}
        <Col md={2}>
          <Card className="p-3 mb-3 h-100">
            <h5 className="mb-3">Files</h5>
            <ListGroup>
              {mockFiles.map((file, index) => (
                <ListGroup.Item
                  key={file}
                  active={index === currentIndex}
                  action
                  onClick={() => handleFileSelect(index)}
                  style={{ fontSize: "0.9rem", cursor: "pointer" }}
                >
                  {file}
                </ListGroup.Item>
              ))}
            </ListGroup>
          </Card>
        </Col>

        {/* Canvas Area */}
        <Col md={8}>
          <Card className="p-3 mb-3 h-100 text-center">
            <canvas
              ref={canvasRef}
              width={canvasDims.width}
              height={canvasDims.height}
              style={{
                width: "100%",
                height: `${CANVAS_HEIGHT}px`,
                backgroundColor: "transparent",
                border: "1px solid #ccc",
                cursor: "crosshair",
              }}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
            />
            <div className="mt-3">
              <h6>Active Label:</h6>
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
            </div>
          </Card>
        </Col>

        {/* Annotation List */}
        <Col md={2}>
          <Card className="p-3 mb-3 h-100">
            <h5>Annotations</h5>
            <ul style={{ fontSize: "0.85rem" }}>
              {currentBoxes.map((box, i) => (
                <li key={box.id}>
                  <strong>{box.label}</strong> — x:{box.x.toFixed(2)} y:
                  {box.y.toFixed(2)}
                </li>
              ))}
            </ul>
            <Button
              variant="outline-danger"
              className="mt-3"
              onClick={() => {
                const updated = [...annotations];
                updated[currentIndex] = [];
                setAnnotations(updated);
              }}
            >
              Clear Annotations
            </Button>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Annotator;
