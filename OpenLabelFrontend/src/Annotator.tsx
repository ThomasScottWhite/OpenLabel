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

// This defines the structure of the annotator layout, and is fetched from the backend
export interface AnnotatorLayout {
  type: "image" | "text" | "video";
  layout: "classification" | "object-detection" | "segmentation" | string;
  labels: string[];
}

// This defines the structure of the project file, and is fetched from the backend
// This does not include the data, which is fetched separately
export interface ProjectFile {
  id: number;
  name: string;
}

export interface ProjectFileWithData extends ProjectFile {
  data: string; // base64 for images, raw string for text
  annotations?: Annotation[];
}
export interface BaseAnnotation {
  annotator: string;
  label: string;
}

export interface ClassificationAnnotation extends BaseAnnotation {
  type: "classification";
}

export interface ObjectDetectionAnnotation extends BaseAnnotation {
  type: "object-detection";
  bbox: [number, number, number, number];
}

export type Annotation = ClassificationAnnotation | ObjectDetectionAnnotation;

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

  // Fetch the layout and files when the component mounts
  useEffect(() => {
    if (!id) return;

    const fetchLayout = async () => {
      const res = await fetch(`/api/projects/${id}/annotator_layout`);
      const data: AnnotatorLayout = await res.json();
      setLayout(data);
      setActiveLabel(data.labels[0] || "");
    };

    const fetchFiles = async () => {
      const res = await fetch(`/api/projects/${id}/files`);
      const data: ProjectFile[] = await res.json();
      setFiles(data);
      setAnnotations(Array(data.length).fill([]));
      setImageLabels(Array(data.length).fill("unknown"));
      setTextLabels(Array(data.length).fill("unknown"));
    };

    fetchLayout();
    fetchFiles();
  }, [id]);

  // Fetch the file data when the current index changes
  useEffect(() => {
    if (!files[currentIndex] || !id) return;

    const fetchFileData = async () => {
      const fileId = files[currentIndex].id;
      const res = await fetch(`/api/projects/${id}/files/${fileId}`);
      const data: ProjectFileWithData = await res.json();
      setFileData(data);

      if (layout?.type === "image") {
        const img = new Image();
        img.src = `data:${data.type};base64,${data.data}`;
        img.onload = () => setImage(img);
      }

      const annotationsFromServer: Annotation[] = data.annotations || [];

      if (layout?.layout === "classification") {
        if (layout.type === "text") {
          // Text classification
          setTextLabels((prev) => {
            const newLabels = [...prev];
            newLabels[currentIndex] =
              annotationsFromServer[0]?.label || "unknown";
            return newLabels;
          });
        } else if (layout.type === "image") {
          // Image classification
          setImageLabels((prev) => {
            const newLabels = [...prev];
            newLabels[currentIndex] =
              annotationsFromServer[0]?.label || "unknown";
            return newLabels;
          });
        }
      } else if (layout?.layout === "object-detection") {
        // Object detection
        const boxes: BoundingBox[] = annotationsFromServer
          .filter((ann) => "bbox" in ann)
          .map((ann, idx) => ({
            id: `box-${idx}`,
            label: ann.label,
            x: ann.bbox[0],
            y: ann.bbox[1],
            width: ann.bbox[2],
            height: ann.bbox[3],
          }));

        setAnnotations((prev) => {
          const newAnnotations = [...prev];
          newAnnotations[currentIndex] = boxes;
          return newAnnotations;
        });
      }
    };

    fetchFileData();
  }, [currentIndex, files, id, layout]);

  // Update the canvas size when the window is resized
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

  // Handle box change for object detection
  // This is called when the user draws a new box or moves an existing one
  const handleBoxChange = async (updated: BoundingBox[]) => {
    const newAnnotations = [...annotations];
    newAnnotations[currentIndex] = updated;
    setAnnotations(newAnnotations);

    if (!id || !files[currentIndex]) return;

    try {
      await fetch(
        `/api/projects/${id}/files/${files[currentIndex].id}/annotations`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ annotations: updated }),
        }
      );
    } catch (error) {
      console.error("Failed to update annotations:", error);
    }
  };

  // Handle label change for classification
  // This is called when the user selects a new label from the button group
  const handleLabelChange = async (label: string) => {
    setActiveLabel(label);

    if (layout?.layout === "object-detection" && selectedBoxId) {
      const updated = [...annotations];
      updated[currentIndex] = updated[currentIndex].map((box) =>
        box.id === selectedBoxId ? { ...box, label } : box
      );
      setAnnotations(updated);

      if (!id || !files[currentIndex]) return;

      try {
        await fetch(
          `/api/projects/${id}/files/${files[currentIndex].id}/annotations`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({ annotations: updated[currentIndex] }),
          }
        );
      } catch (error) {
        console.error("Failed to update label:", error);
      }
    } else if (
      layout?.layout === "classification" &&
      layout?.type === "image"
    ) {
      const updated = [...imageLabels];
      updated[currentIndex] = label;
      setImageLabels(updated);

      if (!id || !files[currentIndex]) return;

      try {
        await fetch(
          `/api/projects/${id}/files/${files[currentIndex].id}/annotations`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              annotations: [{ annotator: "user@example.com", label }],
            }),
          }
        );
      } catch (error) {
        console.error("Failed to update image classification label:", error);
      }
    } else if (layout?.layout === "classification" && layout?.type === "text") {
      const updated = [...textLabels];
      updated[currentIndex] = label;
      setTextLabels(updated);

      if (!id || !files[currentIndex]) return;

      try {
        await fetch(
          `/api/projects/${id}/files/${files[currentIndex].id}/annotations`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              annotations: [{ annotator: "user@example.com", label }],
            }),
          }
        );
      } catch (error) {
        console.error("Failed to update text classification label:", error);
      }
    }
  };

  // Handle delete for object detection
  // This is called when the user clicks the delete button
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
