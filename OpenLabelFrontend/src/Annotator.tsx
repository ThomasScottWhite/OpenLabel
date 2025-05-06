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
import { useEffect, useRef, useState, useCallback } from "react";
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
  filename: string;
  fileId: string;
  contentType: string;
  status: string;
  size: number;
}

export interface ProjectFileWithData extends ProjectFile {
  data: string; // base64 for images, raw string for text
  annotations?: Annotation[];
}

export interface BaseAnnotation {
  annotator: string;
  label: string;
  annotationId?: string;
  projectId?: string;
  fileId?: string;
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
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [isSaving, setIsSaving] = useState(false);

  const getAuthHeaders = () => {
    const token = localStorage.getItem("token");
    return {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };
  };

  useEffect(() => {
    if (!id) return;

    const fetchLayout = async () => {
      try {
        const projectRes = await fetch(`/api/projects/${id}`, {
          headers: getAuthHeaders(),
        });
        if (!projectRes.ok) {
          throw new Error(`Failed to fetch project: ${projectRes.statusText}`);
        }
        const projectData = await projectRes.json();

        const annotatorLayout: AnnotatorLayout = {
          type: projectData.settings.dataType,
          layout: projectData.settings.annotatationType,
          labels: projectData.settings.labels || [],
        };

        setLayout(annotatorLayout);
        setActiveLabel(annotatorLayout.labels[0] || "");
      } catch (error) {
        console.error("Error fetching layout:", error);
      }
    };

    const fetchFiles = async () => {
      try {
        const res = await fetch(`/api/projects/${id}/files`, {
          headers: getAuthHeaders(),
        });
        if (!res.ok) {
          throw new Error(`Failed to fetch files: ${res.statusText}`);
        }
        const data: ProjectFile[] = await res.json();
        setFiles(data);
        setAnnotations(Array(data.length).fill([]));
        setImageLabels(Array(data.length).fill("unknown"));
        setTextLabels(Array(data.length).fill("unknown"));
      } catch (error) {
        console.error("Error fetching files:", error);
      }
    };

    fetchLayout();
    fetchFiles();
  }, [id]);

  // Fetch the file data when the current index changes
  useEffect(() => {
    if (!files[currentIndex] || !id) return;

    const fetchFileData = async () => {
      try {
        const fileId = files[currentIndex].fileId;
        // Using the download endpoint to get file data with annotations
        const res = await fetch(`/api/files/${fileId}/download`, {
          headers: getAuthHeaders(),
        });
        if (!res.ok) {
          throw new Error(`Failed to fetch file data: ${res.statusText}`);
        }
        const responseData = await res.json();

        // Map the response to our expected format
        const fileWithData: ProjectFileWithData = {
          ...files[currentIndex],
          data: responseData.data,
          annotations: responseData.annotations || [],
        };

        setFileData(fileWithData);
        // Reset unsaved changes flag when loading new file
        setHasUnsavedChanges(false);

        if (layout?.type === "image") {
          const img = new Image();
          img.src = `data:${fileWithData.contentType};base64,${fileWithData.data}`;
          img.onload = () => setImage(img);
        }

        const annotationsFromServer = responseData.annotations || [];

        if (layout?.layout === "classification") {
          const classificationAnnotations = annotationsFromServer.filter(
            (ann: any) => ann.type === "classification"
          );

          if (layout.type === "text") {
            // Text classification
            setTextLabels((prev) => {
              const newLabels = [...prev];
              newLabels[currentIndex] =
                classificationAnnotations[0]?.label || "unknown";
              return newLabels;
            });
          } else if (layout.type === "image") {
            // Image classification
            setImageLabels((prev) => {
              const newLabels = [...prev];
              newLabels[currentIndex] =
                classificationAnnotations[0]?.label || "unknown";
              return newLabels;
            });
          }
        } else if (layout?.layout === "object-detection") {
          // Object detection
          const objDetectionAnnotations = annotationsFromServer.filter(
            (ann: any) => ann.type === "object-detection"
          );

          const boxes: BoundingBox[] = objDetectionAnnotations.map(
            (ann: any, idx: number) => ({
              id: ann.annotationId || `box-${idx}`,
              label: ann.label,
              x: ann.bbox.x,
              y: ann.bbox.y,
              width: ann.bbox.width,
              height: ann.bbox.height,
            })
          );

          setAnnotations((prev) => {
            const newAnnotations = [...prev];
            newAnnotations[currentIndex] = boxes;
            return newAnnotations;
          });
        }
      } catch (error) {
        console.error("Failed to fetch file data:", error);
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
  const handleBoxChange = (updated: BoundingBox[]) => {
    const newAnnotations = [...annotations];
    newAnnotations[currentIndex] = updated;
    setAnnotations(newAnnotations);
    setHasUnsavedChanges(true);
  };

  // Handle label change for classification
  // This is called when the user selects a new label from the button group
  const handleLabelChange = (label: string) => {
    setActiveLabel(label);

    if (!fileData) return;

    if (layout?.layout === "object-detection" && selectedBoxId) {
      // For object detection, update the label of the selected box
      const updated = [...annotations];
      updated[currentIndex] = updated[currentIndex].map((box) =>
        box.id === selectedBoxId ? { ...box, label } : box
      );
      setAnnotations(updated);
      setHasUnsavedChanges(true);
    } else if (layout?.layout === "classification") {
      if (layout.type === "image") {
        const updated = [...imageLabels];
        updated[currentIndex] = label;
        setImageLabels(updated);
        setHasUnsavedChanges(true);
      } else if (layout.type === "text") {
        const updated = [...textLabels];
        updated[currentIndex] = label;
        setTextLabels(updated);
        setHasUnsavedChanges(true);
      }
    }
  };

  // Handle delete for object detection
  const handleDelete = () => {
    if (!selectedBoxId) return;

    // Update the local state
    const updated = [...annotations];
    updated[currentIndex] = updated[currentIndex].filter(
      (b) => b.id !== selectedBoxId
    );
    setAnnotations(updated);
    setSelectedBoxId(null);
    setHasUnsavedChanges(true);
  };

  // Handle saving annotations to the server
  const handleSaveAnnotations = async () => {
    if (!id || !fileData) return;

    setIsSaving(true);
    try {
      const fileId = fileData.fileId;

      if (layout?.layout === "object-detection") {
        // Delete all existing annotations for this file first
        const existingAnnotations = fileData.annotations || [];
        for (const ann of existingAnnotations) {
          if (ann.annotationId && ann.type === "object-detection") {
            await fetch(`/api/annotations/${ann.annotationId}`, {
              method: "DELETE",
              headers: getAuthHeaders(),
            });
          }
        }

        // Create new annotations for each bounding box
        const currentBoxes = annotations[currentIndex] || [];
        for (const box of currentBoxes) {
          const annotation = {
            type: "object-detection",
            label: box.label,
            bbox: {
              x: box.x,
              y: box.y,
              width: box.width,
              height: box.height,
            },
          };

          await fetch(`/api/files/${fileId}/annotations`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(annotation),
          });
        }
      } else if (layout?.layout === "classification") {
        // Delete existing classification annotations for this file
        const existingAnnotations = fileData.annotations || [];
        for (const ann of existingAnnotations) {
          if (ann.annotationId && ann.type === "classification") {
            await fetch(`/api/annotations/${ann.annotationId}`, {
              method: "DELETE",
              headers: getAuthHeaders(),
            });
          }
        }

        // Create a new classification annotation
        let label = "";
        if (layout.type === "image") {
          label = imageLabels[currentIndex];
        } else if (layout.type === "text") {
          label = textLabels[currentIndex];
        }

        if (label && label !== "unknown") {
          const annotation = {
            type: "classification",
            label,
          };

          await fetch(`/api/files/${fileId}/annotations`, {
            method: "POST",
            headers: getAuthHeaders(),
            body: JSON.stringify(annotation),
          });
        }
      }

      setHasUnsavedChanges(false);
      // Fetch updated annotations to refresh the view
      const res = await fetch(`/api/files/${fileId}/download`, {
        headers: getAuthHeaders(),
      });
      if (res.ok) {
        const responseData = await res.json();
        setFileData({
          ...fileData,
          annotations: responseData.annotations || [],
        });
      }
    } catch (error) {
      console.error("Failed to save annotations:", error);
    } finally {
      setIsSaving(false);
    }
  };

  // Handle saving and moving to next file
  const handleSaveAndNext = async () => {
    await handleSaveAnnotations();
    if (currentIndex < files.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      // If we're at the last file, go back to the first one
      setCurrentIndex(0);
    }
  };

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      // Ignore keyboard shortcuts when typing in input fields
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      // ~ key submits annotations and goes to the next file
      if (e.key === "`" || e.key === "~") {
        e.preventDefault();
        handleSaveAndNext();
      }

      // Number keys 1-9 select the corresponding label
      const num = parseInt(e.key);
      if (!isNaN(num) && num >= 1 && num <= 9) {
        e.preventDefault();
        const labelIndex = num - 1;
        if (layout?.labels && labelIndex < layout.labels.length) {
          handleLabelChange(layout.labels[labelIndex]);
        }
      }

      // Backspace/Delete key removes selected box in object detection mode
      if (
        (e.key === "Backspace" || e.key === "Delete") &&
        layout?.layout === "object-detection" &&
        selectedBoxId
      ) {
        e.preventDefault();
        handleDelete();
      }
    },
    [
      currentIndex,
      files.length,
      layout,
      selectedBoxId,
      handleDelete,
      handleSaveAndNext,
      handleLabelChange,
    ]
  );

  // Register and cleanup keyboard event listener
  useEffect(() => {
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [handleKeyDown]);

  // Display a confirmation dialog when navigating away with unsaved changes
  const handleFileChange = (index: number) => {
    if (hasUnsavedChanges) {
      if (
        window.confirm(
          "You have unsaved changes. Do you want to save before changing files?"
        )
      ) {
        handleSaveAnnotations().then(() => {
          setCurrentIndex(index);
        });
      } else {
        setCurrentIndex(index);
        setHasUnsavedChanges(false);
      }
    } else {
      setCurrentIndex(index);
    }
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
                  key={file.fileId}
                  active={index === currentIndex}
                  action
                  onClick={() => handleFileChange(index)}
                >
                  {isText ? `Text ${index + 1}` : file.filename}
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

            <div className="mt-3 d-flex justify-content-between align-items-center flex-wrap">
              <div className="d-flex align-items-center gap-2 flex-wrap">
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

              <Button
                variant="success"
                onClick={handleSaveAnnotations}
                disabled={isSaving || !hasUnsavedChanges}
              >
                {isSaving ? "Saving..." : "Save Annotations"}
              </Button>
            </div>
            {hasUnsavedChanges && (
              <div className="mt-2 text-warning">
                <small>You have unsaved changes</small>
              </div>
            )}
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

          <Card className="p-3 mb-3">
            <h5>Keyboard Shortcuts</h5>
            <ul
              className="mb-0"
              style={{ fontSize: "0.85rem", paddingLeft: "1rem" }}
            >
              <li>
                <strong>~</strong>: Submit and next
              </li>
              <li>
                <strong>1-9</strong>: Select label
              </li>
              {annotationType === "object-detection" && (
                <li>
                  <strong>Backspace</strong>: Delete selected box
                </li>
              )}
            </ul>
          </Card>
        </Col>
      </Row>
    </Container>
  );
};

export default Annotator;
