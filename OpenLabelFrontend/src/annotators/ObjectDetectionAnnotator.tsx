// ObjectDetectionAnnotator.tsx
import { useEffect, useRef, useState } from "react";
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

  const [mode, setMode] = useState<"none" | "drawing" | "moving" | "resizing">(
    "none"
  );
  const [dragOffset, setDragOffset] = useState<{ x: number; y: number } | null>(
    null
  );
  const [resizingCorner, setResizingCorner] = useState<number | null>(null);

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

      // Draw handles
      drawHandle(ctx, absX, absY);
      drawHandle(ctx, absX + absW, absY);
      drawHandle(ctx, absX, absY + absH);
      drawHandle(ctx, absX + absW, absY + absH);
    }
  };

  const drawHandle = (ctx: CanvasRenderingContext2D, x: number, y: number) => {
    ctx.fillStyle = "white";
    ctx.strokeStyle = "black";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(x, y, HANDLE_SIZE, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
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

  const findClickedBox = (x: number, y: number) => {
    if (!imageDrawData.current) return null;
    const {
      x: offsetX,
      y: offsetY,
      width: imgW,
      height: imgH,
    } = imageDrawData.current;

    for (const box of annotations) {
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

  const findClickedHandle = (x: number, y: number) => {
    if (!imageDrawData.current) return null;
    const {
      x: offsetX,
      y: offsetY,
      width: imgW,
      height: imgH,
    } = imageDrawData.current;

    for (const box of annotations) {
      const absX = offsetX + box.x * imgW;
      const absY = offsetY + box.y * imgH;
      const absW = box.width * imgW;
      const absH = box.height * imgH;

      const corners = [
        { x: absX, y: absY }, // top-left
        { x: absX + absW, y: absY }, // top-right
        { x: absX, y: absY + absH }, // bottom-left
        { x: absX + absW, y: absY + absH }, // bottom-right
      ];

      for (let i = 0; i < corners.length; i++) {
        const corner = corners[i];
        if (Math.hypot(x - corner.x, y - corner.y) < HANDLE_SIZE * 1.5) {
          return { box, corner: i };
        }
      }
    }
    return null;
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getCanvasCoords(e);

    const handle = findClickedHandle(pos.x, pos.y);
    if (handle) {
      onSelect(handle.box.id);
      setResizingCorner(handle.corner);
      setMode("resizing");
      return;
    }

    const clickedBox = findClickedBox(pos.x, pos.y);
    if (clickedBox) {
      onSelect(clickedBox.id);
      setDragOffset({
        x: pos.x,
        y: pos.y,
      });
      setMode("moving");
      return;
    }

    startPoint.current = pos;
    setMode("drawing");
    onSelect(null);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const pos = getCanvasCoords(e);

    if (mode === "moving" && selectedId && dragOffset) {
      const dx = pos.x - dragOffset.x;
      const dy = pos.y - dragOffset.y;
      const {
        width: imgW,
        height: imgH,
        x: offsetX,
        y: offsetY,
      } = imageDrawData.current;

      onChange(
        annotations.map((box) => {
          if (box.id !== selectedId) return box;
          return {
            ...box,
            x: (offsetX + box.x * imgW + dx - offsetX) / imgW,
            y: (offsetY + box.y * imgH + dy - offsetY) / imgH,
          };
        })
      );
      setDragOffset(pos);
    }

    if (mode === "resizing" && selectedId && resizingCorner !== null) {
      const {
        width: imgW,
        height: imgH,
        x: offsetX,
        y: offsetY,
      } = imageDrawData.current;
      onChange(
        annotations.map((box) => {
          if (box.id !== selectedId) return box;

          const absX = offsetX + box.x * imgW;
          const absY = offsetY + box.y * imgH;
          const absW = box.width * imgW;
          const absH = box.height * imgH;

          let x0 = absX;
          let y0 = absY;
          let x1 = absX + absW;
          let y1 = absY + absH;

          if (resizingCorner === 0) {
            // top-left
            x0 = pos.x;
            y0 = pos.y;
          } else if (resizingCorner === 1) {
            // top-right
            x1 = pos.x;
            y0 = pos.y;
          } else if (resizingCorner === 2) {
            // bottom-left
            x0 = pos.x;
            y1 = pos.y;
          } else if (resizingCorner === 3) {
            // bottom-right
            x1 = pos.x;
            y1 = pos.y;
          }

          const newX = Math.min(x0, x1);
          const newY = Math.min(y0, y1);
          const newW = Math.abs(x1 - x0);
          const newH = Math.abs(y1 - y0);

          return {
            ...box,
            x: (newX - offsetX) / imgW,
            y: (newY - offsetY) / imgH,
            width: newW / imgW,
            height: newH / imgH,
          };
        })
      );
    }
  };

  const handleMouseUp = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (mode === "drawing" && startPoint.current) {
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
    }

    setMode("none");
    startPoint.current = null;
    setDragOffset(null);
    setResizingCorner(null);
  };

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: "100%",
        height: `${height}px`,
        border: "1px solid #ccc",
        cursor: "crosshair",
      }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
    />
  );
};

export default ObjectDetectionAnnotator;
