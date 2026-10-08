"""Vẽ biểu đồ phân tích thí nghiệm suy giảm cảm biến LiDAR (Topic C).

Tạo ra 2 biểu đồ:
1. results/figures/degradation_sweep.png: Tỉ lệ đói điểm (Starvation Rate) và suy giảm điểm trung bình
2. results/figures/points_vs_distance.png: Phân bố số điểm trên Người đi bộ theo khoảng cách và mức suy giảm

Chạy từ gốc repo:
    python -m src.plot_degradation
"""
from __future__ import annotations

from pathlib import Path
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def plot_summary_trends(summary_csv: Path, out_path: Path) -> None:
    df = pd.read_csv(summary_csv)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    # Subplot 1: Beam Dropout (64 -> 32 -> 16 -> 8 beams)
    df_beam = df[df["perturb_type"] == "beam_dropout"].sort_values("perturb_value", ascending=False)
    ax1.plot(
        df_beam["perturb_value"],
        df_beam["starvation_rate"] * 100,
        marker="o",
        linewidth=2.2,
        color="#d9534f",
        label="Tất cả vật thể (All objects)",
    )
    ax1.plot(
        df_beam["perturb_value"],
        df_beam["ped_starvation_rate"] * 100,
        marker="s",
        linewidth=2.2,
        linestyle="--",
        color="#f0ad4e",
        label="Người đi bộ (Pedestrian)",
    )
    ax1.plot(
        df_beam["perturb_value"],
        df_beam["car_starvation_rate"] * 100,
        marker="^",
        linewidth=2.2,
        linestyle=":",
        color="#0275d8",
        label="Xe con (Car)",
    )
    ax1.set_title("Beam Dropout: Starvation Rate (< 10 điểm)", fontsize=12, fontweight="bold")
    ax1.set_xlabel("Số chùm tia tương đương (Beams)", fontsize=11)
    ax1.set_ylabel("Tỉ lệ vật thể bị đói điểm (%)", fontsize=11)
    ax1.set_ylim(0, 100)
    ax1.invert_xaxis()  # 64 -> 8 beams (mức suy giảm tăng dần từ trái sang phải)
    ax1.grid(True, linestyle="--", alpha=0.5)
    ax1.legend(fontsize=10)

    # Subplot 2: Random Dropout (keep_ratio 1.0 -> 0.3)
    df_rand = df[df["perturb_type"] == "random_dropout"].sort_values("perturb_value", ascending=False)
    ax2.plot(
        df_rand["perturb_value"] * 100,
        df_rand["starvation_rate"] * 100,
        marker="o",
        linewidth=2.2,
        color="#d9534f",
        label="Tất cả vật thể (All objects)",
    )
    ax2.plot(
        df_rand["perturb_value"] * 100,
        df_rand["ped_starvation_rate"] * 100,
        marker="s",
        linewidth=2.2,
        linestyle="--",
        color="#f0ad4e",
        label="Người đi bộ (Pedestrian)",
    )
    ax2.plot(
        df_rand["perturb_value"] * 100,
        df_rand["car_starvation_rate"] * 100,
        marker="^",
        linewidth=2.2,
        linestyle=":",
        color="#0275d8",
        label="Xe con (Car)",
    )
    ax2.set_title("Random Dropout: Starvation Rate (< 10 điểm)", fontsize=12, fontweight="bold")
    ax2.set_xlabel("Tỉ lệ điểm giữ lại - Keep ratio (%)", fontsize=11)
    ax2.set_ylabel("Tỉ lệ vật thể bị đói điểm (%)", fontsize=11)
    ax2.set_ylim(0, 100)
    ax2.invert_xaxis()  # 100% -> 30% (suy giảm tăng dần từ trái sang phải)
    ax2.grid(True, linestyle="--", alpha=0.5)
    ax2.legend(fontsize=10)

    fig.suptitle(
        "Đánh giá ngưỡng suy sụp nhận diện 3D theo các mức suy giảm cảm biến (Topic C)",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )
    fig.tight_layout()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"-> Đã lưu biểu đồ tổng hợp xu hướng: {out_path}")


def plot_distance_breakdown(detail_csv: Path, out_path: Path) -> None:
    df = pd.read_csv(detail_csv)

    # Lọc các mức beam dropout trên Người đi bộ
    ped_df = df[(df["type"] == "Pedestrian") & (df["perturb_type"] == "beam_dropout")]

    fig, ax = plt.subplots(figsize=(8, 5))

    beams = [64, 32, 16, 8]
    colors = ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728"]
    markers = ["o", "s", "^", "v"]

    for b, col, m in zip(beams, colors, markers):
        sub = ped_df[ped_df["perturb_value"] == b].sort_values("distance_m")
        ax.plot(
            sub["distance_m"],
            sub["points_degraded"],
            marker=m,
            linewidth=1.8,
            color=col,
            label=f"{b} Beams",
        )

    # Đường ngưỡng đói điểm (Starvation threshold)
    ax.axhline(
        y=10,
        color="red",
        linestyle="--",
        linewidth=1.5,
        label="Ngưỡng đói điểm (10 điểm)",
    )
    ax.set_title(
        "Số điểm phản xạ trên Người đi bộ theo khoảng cách dưới các mức Beam Dropout",
        fontsize=12,
        fontweight="bold",
    )
    ax.set_xlabel("Khoảng cách tới LiDAR (mét)", fontsize=11)
    ax.set_ylabel("Số điểm phản xạ trên người đi bộ", fontsize=11)
    ax.set_ylim(0, max(ped_df["points_degraded"].max() * 1.1, 100))
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(fontsize=10)

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    print(f"-> Đã lưu biểu đồ phân bố theo khoảng cách: {out_path}")


def main() -> None:
    summary_csv = Path("results/degradation_summary.csv")
    detail_csv = Path("results/degradation_sweep.csv")

    if not summary_csv.exists() or not detail_csv.exists():
        print("Lỗi: Chưa tìm thấy kết quả CSV. Vui lòng chạy python -m src.exp_degradation_sweep trước.")
        sys.exit(1)

    fig_dir = Path("results/figures")
    plot_summary_trends(summary_csv, fig_dir / "degradation_sweep.png")
    plot_distance_breakdown(detail_csv, fig_dir / "points_vs_distance.png")


if __name__ == "__main__":
    main()
