import { useParams } from "react-router-dom";
import { Container, Row, Col, Button, Card, ListGroup } from "react-bootstrap";
import { useEffect, useRef, useState } from "react";

const mockFiles = [
  "/images/sample1.jpg",
  "/images/sample2.jpg",
  "/images/sample3.jpg",
];

interface RelativeBox {
  x: number; // left (0-1)
  y: number; // top (0-1)
  width: number;
  height: number;
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

    // Compute scale and offset
    const scale = Math.min(
      canvas.width / image.width,
      canvas.height / image.height
    );
    const imgWidth = image.width * scale;
    const imgHeight = image.height * scale;
    const offsetX = (canvas.width - imgWidth) / 2;
    const offsetY = (canvas.height - imgHeight) / 2;

    // Save draw info for reverse transforms
    setImageDrawData({
      x: offsetX,
      y: offsetY,
      width: imgWidth,
      height: imgHeight,
      scale,
    });

    ctx.drawImage(image, offsetX, offsetY, imgWidth, imgHeight);

    // Draw boxes (relative -> absolute)
    ctx.strokeStyle = "red";
    ctx.lineWidth = 2;
    for (const box of currentBoxes) {
      const absX = offsetX + box.x * imgWidth;
      const absY = offsetY + box.y * imgHeight;
      const absW = box.width * imgWidth;
      const absH = box.height * imgHeight;
      ctx.strokeRect(absX, absY, absW, absH);
    }
  };

  useEffect(() => {
    drawCanvas();
  }, [image, currentBoxes, canvasDims]);

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const rect = canvasRef.current!.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    setStartPoint(getCanvasCoords(e));
    setDrawing(true);
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!startPoint || !imageDrawData) return;
    const end = getCanvasCoords(e);

    const { x: offsetX, y: offsetY, width: imgW, height: imgH } = imageDrawData;

    // Clamp inside canvas
    const relStartX = Math.min(Math.max(startPoint.x - offsetX, 0), imgW);
    const relStartY = Math.min(Math.max(startPoint.y - offsetY, 0), imgH);
    const relEndX = Math.min(Math.max(end.x - offsetX, 0), imgW);
    const relEndY = Math.min(Math.max(end.y - offsetY, 0), imgH);

    const relBox: RelativeBox = {
      x: Math.min(relStartX, relEndX) / imgW,
      y: Math.min(relStartY, relEndY) / imgH,
      width: Math.abs(relEndX - relStartX) / imgW,
      height: Math.abs(relEndY - relStartY) / imgH,
    };

    const updated = [...annotations];
    updated[currentIndex] = [...(updated[currentIndex] || []), relBox];
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

    // Preview blue box
    ctx.strokeStyle = "blue";
    ctx.lineWidth = 1;
    ctx.strokeRect(
      Math.min(startPoint.x, curr.x),
      Math.min(startPoint.y, curr.y),
      Math.abs(curr.x - startPoint.x),
      Math.abs(curr.y - startPoint.y)
    );
  };

  const handleNext = () => {
    if (currentIndex < mockFiles.length - 1) setCurrentIndex(currentIndex + 1);
  };

  const handlePrev = () => {
    if (currentIndex > 0) setCurrentIndex(currentIndex - 1);
  };

  const handleFileSelect = (index: number) => {
    setCurrentIndex(index);
  };

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
          </Card>
        </Col>

        {/* Annotation List */}
        <Col md={2}>
          <Card className="p-3 mb-3 h-100">
            <h5>Annotations</h5>
            <ul style={{ fontSize: "0.85rem" }}>
              {currentBoxes.map((box, i) => (
                <li key={i}>
                  Box #{i + 1} — x:{box.x.toFixed(2)} y:{box.y.toFixed(2)} w:
                  {box.width.toFixed(2)} h:{box.height.toFixed(2)}
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
