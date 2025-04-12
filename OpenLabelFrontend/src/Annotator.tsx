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

export interface AnnotatorLayout {
  type: "image" | "text" | "video";
  layout: "classification" | "object-detection" | "segmentation" | string;
  labels: string[];
}

export interface ProjectFile {
  id: number;
  name: string;
  description: string;
  size: number;
  type: string;
  uploaded_at: string;
}

export interface ProjectFileWithData extends ProjectFile {
  data: string;
}

const CANVAS_HEIGHT = 600;

const Annotator = () => {
  const { id } = useParams<{ id: string }>();
  const [layout, setLayout] = useState<AnnotatorLayout | null>(null);
  const [files, setFiles] = useState<ProjectFile[]>([]);
  const [fileData, setFileData] = useState<ProjectFileWithData | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [annotations, setAnnotations] = useState<BoundingBox[][]>([]);
  const [imageLabels, setImageLabels] = useState<string[]>([]);
  const [textLabels, setTextLabels] = useState<string[]>([]);
  const [activeLabel, setActiveLabel] = useState<string>("");
  const [selectedBoxId, setSelectedBoxId] = useState<string | null>(null);
  const [image, setImage] = useState<HTMLImageElement | null>(null);
  const canvasContainerRef = useRef<HTMLDivElement>(null);
  const [canvasDims, setCanvasDims] = useState({
    width: 0,
    height: CANVAS_HEIGHT,
  });

  useEffect(() => {
    if (!id) return;

    const fetchLayout = async () => {
      const res = await fetch(
        `http://localhost:8000/projects/${id}/annotator_layout`
      );
      const data: AnnotatorLayout = await res.json();
      setLayout(data);
      setActiveLabel(data.labels[0] || "");
    };

    const fetchFiles = async () => {
      const res = await fetch(`http://localhost:8000/projects/${id}/files`);
      const data: ProjectFile[] = await res.json();
      setFiles(data);
      setAnnotations(Array(data.length).fill([]));
      setImageLabels(Array(data.length).fill("unknown"));
      setTextLabels(Array(data.length).fill("unknown"));
    };

    fetchLayout();
    fetchFiles();
  }, [id]);

  useEffect(() => {
    if (!files[currentIndex] || !id) return;
    const fetchFileData = async () => {
      const fileId = files[currentIndex].id;
      const res = await fetch(
        `http://localhost:8000/projects/${id}/files/${fileId}`
      );
      const data: ProjectFileWithData = await res.json();
      setFileData(data);

      if (layout?.type === "image") {
        const img = new Image();
        img.src = `data:${data.type};base64,${data.data}`;
        img.onload = () => setImage(img);
      }
    };
    fetchFileData();
  }, [currentIndex, files, id, layout?.type]);

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
    if (layout?.layout === "object-detection" && selectedBoxId) {
      const updated = [...annotations];
      updated[currentIndex] = updated[currentIndex].map((box) =>
        box.id === selectedBoxId ? { ...box, label } : box
      );
      setAnnotations(updated);
    } else if (
      layout?.layout === "classification" &&
      layout?.type === "image"
    ) {
      const updated = [...imageLabels];
      updated[currentIndex] = label;
      setImageLabels(updated);
    } else if (layout?.layout === "classification" && layout?.type === "text") {
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

  const currentBoxes = annotations[currentIndex] || [];
  const annotationType = layout?.layout;
  const labelOptions = layout?.labels || [];
  const isText = layout?.type === "text";

  return (
    <Container fluid className="py-4">
      <Row>
        <Col md={2}>
          <Card className="p-3 mb-3">
            <h5>{isText ? "Texts" : "Files"}</h5>
            <ListGroup>
              {files.map((file, index) => (
                <ListGroup.Item
                  key={file.id}
                  active={index === currentIndex}
                  action
                  onClick={() => setCurrentIndex(index)}
                >
                  {isText ? `Text ${index + 1}` : file.name}
                </ListGroup.Item>
              ))}
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
            {image &&
              annotationType === "classification" &&
              layout?.type === "image" && (
                <ImageClassificationAnnotator
                  image={image}
                  width={canvasDims.width}
                  height={canvasDims.height}
                  label={imageLabels[currentIndex]}
                  onLabelChange={handleLabelChange}
                  labelOptions={labelOptions}
                />
              )}
            {annotationType === "classification" &&
              layout?.type === "text" &&
              fileData && (
                <TextClassificationAnnotator
                  text={fileData.data}
                  label={textLabels[currentIndex]}
                  onLabelChange={handleLabelChange}
                  labelOptions={labelOptions}
                />
              )}

            <div className="mt-3 d-flex justify-content-center align-items-center gap-2 flex-wrap">
              <strong>Label:</strong>
              <ButtonGroup>
                {labelOptions.map((label) => (
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
                : isText
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
            ) : isText ? (
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
