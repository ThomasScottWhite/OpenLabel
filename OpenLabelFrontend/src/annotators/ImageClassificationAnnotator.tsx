import { useEffect, useRef } from "react";

interface Props {
  image: HTMLImageElement | null;
  width: number;
  height: number;
  label: string;
  onLabelChange: (newLabel: string) => void;
  labelOptions: string[];
}

const ImageClassificationAnnotator = ({
  image,
  width,
  height,
  label,
  onLabelChange,
  labelOptions,
}: Props) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    drawCanvas();
  }, [image, width, height]);

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

    ctx.drawImage(image, offsetX, offsetY, imgW, imgH);
  };

  return (
    <div className="d-flex flex-column align-items-center">
      <canvas
        ref={canvasRef}
        style={{
          width: "100%",
          height: `${height}px`,
          border: "1px solid #ccc",
        }}
      />
    </div>
  );
};

export default ImageClassificationAnnotator;
