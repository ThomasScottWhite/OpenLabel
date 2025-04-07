// ObjectDetectionAnnotator.tsx
import { useEffect, useRef } from "react";
import { v4 as uuidv4 } from "uuid";

export interface BoundingBox {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  label: string;
}

interface Props {
  image: HTMLImageElement | null;
  width: number;
  height: number;
  annotations: BoundingBox[];
  onChange: (updated: BoundingBox[]) => void;
  selectedId: string | null;
  onSelect: (id: string | null) => void;
  activeLabel: string;
}

const HANDLE_SIZE = 8;

const ObjectDetectionAnnotator = ({
  image,
  width,
  height,
  annotations,
  onChange,
  selectedId,
  onSelect,
  activeLabel,
}: Props) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const startPoint = useRef<{ x: number; y: number } | null>(null);
  const imageDrawData = useRef<any>(null);

  useEffect(() => {
    drawCanvas();
  }, [image, annotations, width, height, selectedId]);

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas || !image) return;
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, width, height);

    const scale = Math.min(width / image.width, height / image.height);
    const imgW = image.width * scale;
    const imgH = image.height * scale;
    const offsetX = (width - imgW) / 2;
    const offsetY = (height - imgH) / 2;

    imageDrawData.current = {
      x: offsetX,
      y: offsetY,
      width: imgW,
      height: imgH,
      scale,
    };
    ctx.drawImage(image, offsetX, offsetY, imgW, imgH);

    for (const box of annotations) {
      const absX = offsetX + box.x * imgW;
      const absY = offsetY + box.y * imgH;
      const absW = box.width * imgW;
      const absH = box.height * imgH;

      ctx.strokeStyle = box.id === selectedId ? "cyan" : "red";
      ctx.lineWidth = box.id === selectedId ? 3 : 2;
      ctx.strokeRect(absX, absY, absW, absH);

      ctx.fillStyle = "rgba(0,0,0,0.6)";
      ctx.fillRect(absX, absY - 20, ctx.measureText(box.label).width + 10, 18);
      ctx.fillStyle = "white";
      ctx.font = "14px sans-serif";
      ctx.fillText(box.label, absX + 5, absY - 6);
    }
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getCanvasCoords(e);
    startPoint.current = pos;
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!startPoint.current || !imageDrawData.current) return;

    const end = getCanvasCoords(e);
    const {
      x: offsetX,
      y: offsetY,
      width: imgW,
      height: imgH,
    } = imageDrawData.current;

    const relStartX = Math.min(
      Math.max(startPoint.current.x - offsetX, 0),
      imgW
    );
    const relStartY = Math.min(
      Math.max(startPoint.current.y - offsetY, 0),
      imgH
    );
    const relEndX = Math.min(Math.max(end.x - offsetX, 0), imgW);
    const relEndY = Math.min(Math.max(end.y - offsetY, 0), imgH);

    const newBox: BoundingBox = {
      id: uuidv4(),
      x: Math.min(relStartX, relEndX) / imgW,
      y: Math.min(relStartY, relEndY) / imgH,
      width: Math.abs(relEndX - relStartX) / imgW,
      height: Math.abs(relEndY - relStartY) / imgH,
      label: activeLabel,
    };

    onChange([...annotations, newBox]);
    startPoint.current = null;
  };

  const getCanvasCoords = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current!;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;

    return {
      x: (e.clientX - rect.left) * scaleX,
      y: (e.clientY - rect.top) * scaleY,
    };
  };

  return (
    <canvas
      ref={canvasRef}
      style={{ width: "100%", height: `${height}px`, border: "1px solid #ccc" }}
      onMouseDown={handleMouseDown}
      onMouseUp={handleMouseUp}
    />
  );
};

export default ObjectDetectionAnnotator;
