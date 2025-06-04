import { useEffect, useRef } from "react";
import QRCode from "qrcode";

interface QrProps {
  value: string;
  size?: number;
  className?: string;
}

export function QrCode({ value, size = 128, className = "" }: QrProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    if (canvasRef.current && value) {
      QRCode.toCanvas(canvasRef.current, value, {
        width: size,
        margin: 2,
        color: {
          dark: "#000000",
          light: "#FFFFFF",
        },
      }).catch((err) => {
        console.error("QR Code generation failed:", err);
      });
    }
  }, [value, size]);

  return (
    <canvas
      ref={canvasRef}
      className={`border rounded-lg ${className}`}
      width={size}
      height={size}
    />
  );
}
