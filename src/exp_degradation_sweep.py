"""Topic C: Stress Test Suy Giảm Cảm Biến LiDAR và Đánh Giá Ngưỡng Suy Sụp Nhận Diện 3D.

Đo đạc sự thay đổi số điểm phản xạ trên vật thể (points on object) và tỉ lệ đói điểm
(starvation rate: < 10 điểm) dưới các dạng suy giảm cảm biến:
1. Random Dropout: Giả lập thời tiết xấu (mưa, bụi, sương mù) hoặc cảm biến rẻ tiền.
2. Beam Dropout: Giả lập hạ độ phân giải góc từ 64 chùm tia xuống 32, 16, 8 tia.
3. Range Cutoff: Giả lập cảm biến LiDAR tầm ngắn hoặc hấp thụ tia laser tầm xa.

Cách chạy:
    python -m src.exp_degradation_sweep --data-root data/kitti_mini --frames 000001 000010 000011 000021 000049
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys
from typing import Any

import numpy as np
import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from starter.datasets import load_frame
from starter.perturb import beam_dropout, random_dropout, range_dropout
from starter.projection import velo_to_cam

CLASSES = ("Car", "Van", "Pedestrian", "Cyclist", "Truck")
STARVATION_THRESHOLD = 10  # Dưới 10 điểm, 3D detector mất khả năng nhận diện tin cậy


def points_in_box(points_cam: np.ndarray, obj: Any) -> np.ndarray:
    """Trả về boolean mask (N,) các điểm (trong rectified camera frame) nằm trong 3D bounding box."""
    h, w, l = obj.dimensions
    c, s = np.cos(obj.rotation_y), np.sin(obj.rotation_y)
    # Rotation ma trận quanh trục Y (downwards) của camera frame
    R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], dtype=np.float64)
    # obj.location là đáy giữa (bottom center) của 3D box trong KITTI
    local = (points_cam - obj.location) @ R
    # Kiểm tra biên x (chiều dài l), y (chiều cao h: y đi từ -h đến 0), z (chiều rộng w)
    return (
        (np.abs(local[:, 0]) <= l / 2.0)
        & (local[:, 1] <= 0.0)
        & (local[:, 1] >= -h)
        & (np.abs(local[:, 2]) <= w / 2.0)
    )


def evaluate_frame_objects(
    frame_id: str,
    raw_points: np.ndarray,
    degraded_points: np.ndarray,
    calib: Any,
    labels: list[Any],
    perturb_type: str,
    perturb_param: str,
    perturb_value: float,
) -> list[dict[str, Any]]:
    """Tính toán số điểm phản xạ trên từng vật thể trước và sau khi suy giảm."""
    # Lọc điểm hợp lệ
    pts_clean = degraded_points[np.isfinite(degraded_points).all(axis=1)]
    cam_pts = velo_to_cam(pts_clean[:, :3], calib)

    # Điểm gốc mốc chuẩn (baseline)
    raw_clean = raw_points[np.isfinite(raw_points).all(axis=1)]
    cam_raw = velo_to_cam(raw_clean[:, :3], calib)

    results = []
    for idx, obj in enumerate(labels):
        if obj.type not in CLASSES:
            continue

        dist_2d = float(np.hypot(obj.location[0], obj.location[2]))
        if dist_2d < 15.0:
            dist_bin = "<15m"
        elif dist_2d <= 30.0:
            dist_bin = "15-30m"
        else:
            dist_bin = ">30m"

        pts_baseline = int(points_in_box(cam_raw, obj).sum())
        pts_curr = int(points_in_box(cam_pts, obj).sum())
        retention = round(pts_curr / pts_baseline, 4) if pts_baseline > 0 else 1.0

        results.append({
            "frame": frame_id,
            "object_id": idx,
            "type": obj.type,
            "distance_m": round(dist_2d, 2),
            "distance_bin": dist_bin,
            "perturb_type": perturb_type,
            "perturb_param": perturb_param,
            "perturb_value": perturb_value,
            "points_baseline": pts_baseline,
            "points_degraded": pts_curr,
            "retention_ratio": retention,
            "is_starved": int(pts_curr < STARVATION_THRESHOLD),
        })
    return results


def run_experiment(
    data_root: str,
    frames: list[str],
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Chạy toàn bộ sweep thí nghiệm suy giảm trên tập frame."""
    all_rows: list[dict[str, Any]] = []

    # 1. Random Dropout: keep_ratio từ 1.0 xuống 0.3
    random_keep_ratios = [1.0, 0.85, 0.7, 0.5, 0.3]
    # 2. Beam Dropout: keep_every = 1, 2, 4, 8 (tương đương 64, 32, 16, 8 beams)
    beam_reductions = [(1, 64), (2, 32), (4, 16), (8, 8)]
    # 3. Range Cutoff: max_range từ 100m xuống 20m
    range_cutoffs = [100.0, 50.0, 30.0, 20.0]

    for frame_id in frames:
        fr = load_frame(data_root, frame_id)
        raw_pts = fr["points"]
        calib = fr["calib"]
        labels = fr["labels"]

        # 1. Random Dropout sweep
        for keep in random_keep_ratios:
            deg_pts = random_dropout(raw_pts, keep_ratio=keep, seed=seed)
            rows = evaluate_frame_objects(
                frame_id, raw_pts, deg_pts, calib, labels,
                perturb_type="random_dropout",
                perturb_param="keep_ratio",
                perturb_value=keep,
            )
            all_rows.extend(rows)

        # 2. Beam Dropout sweep
        for step, n_beams in beam_reductions:
            deg_pts = beam_dropout(raw_pts, keep_every=step, n_beams=64)
            rows = evaluate_frame_objects(
                frame_id, raw_pts, deg_pts, calib, labels,
                perturb_type="beam_dropout",
                perturb_param="beam_count",
                perturb_value=n_beams,
            )
            all_rows.extend(rows)

        # 3. Range Cutoff sweep
        for r_max in range_cutoffs:
            deg_pts = range_dropout(raw_pts, max_range_m=r_max)
            rows = evaluate_frame_objects(
                frame_id, raw_pts, deg_pts, calib, labels,
                perturb_type="range_cutoff",
                perturb_param="max_range_m",
                perturb_value=r_max,
            )
            all_rows.extend(rows)

    df_detail = pd.DataFrame(all_rows)

    # Tổng hợp bảng tóm tắt starvation rate và retention theo cấu hình
    summary_rows = []
    for (ptype, pparam, pval), group in df_detail.groupby(
        ["perturb_type", "perturb_param", "perturb_value"]
    ):
        total_objs = len(group)
        starved_objs = group["is_starved"].sum()
        starvation_rate = round(float(starved_objs / total_objs), 4)

        # Người đi bộ riêng
        ped_group = group[group["type"] == "Pedestrian"]
        ped_total = len(ped_group)
        ped_starved = ped_group["is_starved"].sum()
        ped_starvation_rate = (
            round(float(ped_starved / ped_total), 4) if ped_total > 0 else 0.0
        )
        ped_mean_pts = (
            round(float(ped_group["points_degraded"].mean()), 1) if ped_total > 0 else 0.0
        )

        # Xe con riêng
        car_group = group[group["type"] == "Car"]
        car_total = len(car_group)
        car_starved = car_group["is_starved"].sum()
        car_starvation_rate = (
            round(float(car_starved / car_total), 4) if car_total > 0 else 0.0
        )
        car_mean_pts = (
            round(float(car_group["points_degraded"].mean()), 1) if car_total > 0 else 0.0
        )

        summary_rows.append({
            "perturb_type": ptype,
            "perturb_param": pparam,
            "perturb_value": pval,
            "total_objects": total_objs,
            "starved_objects": int(starved_objs),
            "starvation_rate": starvation_rate,
            "pedestrian_count": ped_total,
            "ped_starvation_rate": ped_starvation_rate,
            "ped_mean_points": ped_mean_pts,
            "car_count": car_total,
            "car_starvation_rate": car_starvation_rate,
            "car_mean_points": car_mean_pts,
        })

    df_summary = pd.DataFrame(summary_rows)
    return df_detail, df_summary


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stress Test Suy Giảm Cảm Biến LiDAR & Đánh Giá Ngưỡng Suy Sụp Nhận Diện 3D (Topic C)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-root",
        default="data/kitti_mini",
        help="Đường dẫn thư mục dataset gốc (mặc định: data/kitti_mini)",
    )
    parser.add_argument(
        "--frames",
        nargs="+",
        default=["000001", "000010", "000011", "000021", "000049"],
        help="Danh sách frame ID cần chạy stress test",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed để đảm bảo 100% tái lập được số liệu thí nghiệm",
    )
    parser.add_argument(
        "--out",
        default="results/degradation_sweep.csv",
        help="Đường dẫn file CSV lưu chi tiết số điểm trên từng đối tượng",
    )
    parser.add_argument(
        "--summary-out",
        default="results/degradation_summary.csv",
        help="Đường dẫn file CSV lưu bảng tổng hợp starvation rate và mean points",
    )
    args = parser.parse_args()

    print(f"=== Chạy stress test trên {len(args.frames)} frames của {args.data_root} ===")
    df_detail, df_summary = run_experiment(args.data_root, args.frames, seed=args.seed)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df_detail.to_csv(out_path, index=False)
    print(f"-> Đã lưu dữ liệu chi tiết ({len(df_detail)} dòng) vào: {out_path}")

    summary_path = Path(args.summary_out)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    df_summary.to_csv(summary_path, index=False)
    print(f"-> Đã lưu bảng tổng hợp ({len(df_summary)} dòng) vào: {summary_path}")

    print("\n--- BẢNG TỔNG HỢP KẾT QUẢ STRESS TEST ---")
    print(df_summary.to_string(index=False))


if __name__ == "__main__":
    main()
