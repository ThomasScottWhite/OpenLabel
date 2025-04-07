// TextClassificationAnnotator.tsx
import React from "react";
import { Button } from "react-bootstrap";

interface Props {
  text: string;
  label: string;
  onLabelChange: (label: string) => void;
  labelOptions: string[];
}

const TextClassificationAnnotator = ({
  text,
  label,
  onLabelChange,
  labelOptions,
}: Props) => {
  return (
    <div className="d-flex flex-column align-items-center gap-4">
      <div
        className="border rounded p-3 text-center"
        style={{ maxWidth: "600px" }}
      >
        <p className="mb-0" style={{ fontSize: "1.2rem" }}>
          {text}
        </p>
      </div>

      <div className="d-flex flex-wrap justify-content-center gap-2">
        {labelOptions.map((opt) => (
          <Button
            key={opt}
            variant={opt === label ? "primary" : "outline-primary"}
            onClick={() => onLabelChange(opt)}
          >
            {opt}
          </Button>
        ))}
      </div>
    </div>
  );
};

export default TextClassificationAnnotator;
