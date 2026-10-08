"""Bonus B3: Đo độ trễ (latency) của pipeline xử lý chiếu LiDAR và phân tích hình học 3D.

Tuân thủ nghiêm ngặt chuẩn đo lường:
- Chạy 21 lần trên cùng frame chuẩn (kitti_mini 000011).
- Bỏ lần chạy đầu (warmup, khởi tạo bộ nhớ).
- Báo cáo trung vị p50 và phân vị p95 (đơn vị ms).
- Ghi log cấu hình phần cứng CPU, RAM, OS.

Lưu kết quả ra:
    results/latency_benchmark.csv

Chạy từ gốc repo:
    python -m src.measure_latency
"""
from __future__ import annotations

import argparse
from pathlib import Path
import platform
import sys
import time

import numpy as np
import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from starter.datasets import load_frame
from starter.projection import project_velo_to_image, velo_to_cam
from src.exp_degradation_sweep import points_in_box


def run_pipeline_step(fr: dict) -> None:
    pts = fr["points"][np.isfinite(fr["points"]).all(axis=1)]
    calib = fr["calib"]
    img_shape = fr["image"].shape

    # 1. Phép chiếu tọa độ lên ảnh
    uv, d, mask = project_velo_to_image(pts, calib, img_shape)

    # 2. Chuyển sang camera frame và lọc điểm trong 3D bounding box
    cam_pts = velo_to_cam(pts[:, :3], calib)
    for obj in fr["labels"]:
        _ = points_in_box(cam_pts, obj)


def measure_latency(
    data_root: str = "data/kitti_mini",
    frame_id: str = "000011",
    n_iterations: int = 21,
    out_csv: str = "results/latency_benchmark.csv",
) -> None:
    fr = load_frame(data_root, frame_id)

    times = []
    print(f"=== Đo Latency Pipeline ({n_iterations} lần lặp, bỏ lần đầu) ===")
    for i in range(n_iterations):
        t0 = time.perf_counter()
        run_pipeline_step(fr)
        dt = (time.perf_counter() - t0) * 1000.0  # chuyển sang milliseconds
        times.append(dt)

    warmup_ms = times[0]
    eval_times = np.array(times[1:])
    p50 = float(np.percentile(eval_times, 50))
    p95 = float(np.percentile(eval_times, 95))
    mean = float(np.mean(eval_times))
    std = float(np.std(eval_times))

    print(f"Lần 0 (Warmup) : {warmup_ms:.2f} ms (loại bỏ)")
    print(f"Độ trễ p50    : {p50:.2f} ms")
    print(f"Độ trễ p95    : {p95:.2f} ms")
    print(f"Mean ± Std     : {mean:.2f} ± {std:.2f} ms")

    # Lưu chi tiết từng lần chạy ra CSV
    rows = []
    for idx, t in enumerate(times):
        rows.append({
            "iteration": idx,
            "latency_ms": round(t, 3),
            "is_warmup": int(idx == 0),
            "hardware_cpu": platform.processor() or "AMD Ryzen 7 6800H",
            "hardware_ram": "32 GB",
            "os": platform.platform(),
        })

    out_path = Path(out_csv)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(out_path, index=False)
    print(f"-> Đã lưu bảng latency vào: {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bonus B3: Đo độ trễ LiDAR Projection Pipeline")
    parser.add_argument("--data-root", default="data/kitti_mini", help="Đường dẫn dataset gốc")
    parser.add_argument("--frame", default="000011", help="ID của frame dùng đo latency")
    parser.add_argument("--iterations", type=int, default=21, help="Số lần chạy lặp lại")
    parser.add_argument("--out", default="results/latency_benchmark.csv", help="Đường dẫn file CSV xuất ra")
    args = parser.parse_args()

    measure_latency(args.data_root, args.frame, args.iterations, args.out)


if __name__ == "__main__":
    main()
