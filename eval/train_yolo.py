"""Train the floor-plan symbol detector on the CubiCasa train split (val split for early stopping)."""

import sys
from pathlib import Path

from ultralytics import YOLO

ROOT = Path(__file__).resolve().parent.parent

if __name__ == "__main__":
    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    imgsz = int(sys.argv[2]) if len(sys.argv) > 2 else 1024
    model = YOLO("yolo11s.pt")
    model.train(
        data=str(ROOT / "data_cache/yolo_cubicasa/data.yaml"),
        epochs=epochs, imgsz=imgsz, batch=8, device="mps", workers=4,
        project=str(ROOT / "data_cache/runs"), name="cubicasa_s", exist_ok=True,
        patience=10, cache=False, plots=True,
        # plans come in any orientation; no colour jitter needed for line drawings
        degrees=0, fliplr=0.5, flipud=0.5, mosaic=0.5, hsv_h=0, hsv_s=0, hsv_v=0.2,
    )
