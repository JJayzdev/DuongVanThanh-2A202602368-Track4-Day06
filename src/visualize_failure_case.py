"""Minh hoạ Failure Case: Hiện tượng Đói điểm (Point Starvation) ở người đi bộ.

Lớp debug liên quan:
1. Geometry: Mật độ góc (angular resolution) giảm làm khoảng cách giữa 2 tia kế tiếp lớn hơn kích thước vật thể.
2. Preprocess / Sensor: Số điểm rơi vào 3D box < 10 điểm, không đủ trích xuất đặc trưng hình học.

Tạo ra file:
    results/figures/fail_01_pedestrian_starvation.png

Chạy từ gốc repo:
    python -m src.visualize_failure_case
"""
from __future__ import annotations

from pathlib import Path
import sys

import cv2
import matplotlib.pyplot as plt
import numpy as np

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from starter.datasets import load_frame
from starter.perturb import beam_dropout
from starter.projection import project_velo_to_image, velo_to_cam
from src.exp_degradation_sweep import points_in_box


def generate_failure_visualization(out_path: Path) -> None:
    # Chọn frame 000011 có người đi bộ ở khoảng cách 14.5m (Obj index 1)
    fr = load_frame("data/kitti_mini", "000011")
    pts_clean = fr["points"][np.isfinite(fr["points"]).all(axis=1)]
    calib = fr["calib"]
    img_bgr = fr["image"]
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    ped = fr["labels"][1]  # Pedestrian ở 14.5m

    # 1. Clean frame
    cam_clean = velo_to_cam(pts_clean[:, :3], calib)
    mask_in_box_clean = points_in_box(cam_clean, ped)
    pts_ped_clean = pts_clean[mask_in_box_clean]
    uv_clean, d_clean, mask_clean = project_velo_to_image(pts_ped_clean, calib, img_rgb.shape)

    # 2. Degraded frame (16 Beams - keep_every=4)
    pts_deg = beam_dropout(pts_clean, keep_every=4, n_beams=64)
    cam_deg = velo_to_cam(pts_deg[:, :3], calib)
    mask_in_box_deg = points_in_box(cam_deg, ped)
    pts_ped_deg = pts_deg[mask_in_box_deg]
    uv_deg, d_deg, mask_deg = project_velo_to_image(pts_ped_deg, calib, img_rgb.shape)

    # Crop vùng quanh người đi bộ (2D bbox mở rộng 40 pixel biên)
    x1, y1, x2, y2 = [int(v) for v in ped.bbox]
    pad = 40
    crop_x1 = max(0, x1 - pad)
    crop_y1 = max(0, y1 - pad)
    crop_x2 = min(img_rgb.shape[1], x2 + pad)
    crop_y2 = min(img_rgb.shape[0], y2 + pad)

    img_crop_clean = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2].copy()
    img_crop_deg = img_rgb[crop_y1:crop_y2, crop_x1:crop_x2].copy()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 6))

    # Vẽ panel Clean
    ax1.imshow(img_crop_clean)
    rect_x = x1 - crop_x1
    rect_y = y1 - crop_y1
    rect_w = x2 - x1
    rect_h = y2 - y1
    ax1.add_patch(plt.Rectangle((rect_x, rect_y), rect_w, rect_h, edgecolor="lime", facecolor="none", lw=2))
    if len(uv_clean) > 0:
        ax1.scatter(uv_clean[:, 0] - crop_x1, uv_clean[:, 1] - crop_y1, c="yellow", s=35, edgecolors="black", label=f"Điểm LiDAR ({len(uv_clean)} pts)")
    ax1.set_title(f"Baseline: 64 Beams (Đủ điểm)\n{len(pts_ped_clean)} điểm trong 3D box -> PASS", fontsize=11, fontweight="bold", color="darkgreen")
    ax1.axis("off")
    ax1.legend(loc="lower right")

    # Vẽ panel Degraded (Failure)
    ax2.imshow(img_crop_deg)
    ax2.add_patch(plt.Rectangle((rect_x, rect_y), rect_w, rect_h, edgecolor="red", facecolor="none", lw=2, linestyle="--"))
    if len(uv_deg) > 0:
        ax2.scatter(uv_deg[:, 0] - crop_x1, uv_deg[:, 1] - crop_y1, c="red", s=45, edgecolors="white", label=f"Điểm LiDAR ({len(uv_deg)} pts)")
    ax2.set_title(f"Degraded: 16 Beams (Đói điểm - Starvation)\nChỉ còn {len(pts_ped_deg)} điểm -> FAIL (< 10 pts)", fontsize=11, fontweight="bold", color="darkred")
    ax2.axis("off")
    ax2.legend(loc="lower right")

    fig.suptitle(
        f"Failure Case: Hiện tượng Đói điểm (Point Starvation) ở Người đi bộ (d = 14.5m)\n"
        f"Lớp lỗi: Geometry (Resolution sụt giảm) & Preprocess/Model (< 10 điểm -> False Negative)",
        fontsize=12,
        fontweight="bold",
        y=0.98,
    )
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"-> Đã lưu ảnh minh hoạ failure case: {out_path}")


def main() -> None:
    out_file = Path("results/figures/fail_01_pedestrian_starvation.png")
    generate_failure_visualization(out_file)


if __name__ == "__main__":
    main()
