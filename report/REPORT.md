# Báo cáo Day 6: Stress Test Suy Giảm Cảm Biến LiDAR và Đánh Giá Ngưỡng Suy Sụp Nhận Diện 3D

> Thay **mọi** ô có chữ ĐIỀN nằm trong ngoặc vuông bằng nội dung của bạn, xoá luôn cả dấu ngoặc vuông. Lệnh `python tools/check_submission.py` sẽ báo FAIL nếu còn sót bất kỳ chỗ nào.

- **Họ tên:** Dương Văn Thành
- **MSSV:** 2A202602368
- **Lớp:** K4 Track 4
- **Link repo:** https://github.com/JJayzdev/DuongVanThanh-2A202602368-Track4-Day06
- **Topic:** C — Sensor degradation stress test
- **Dataset:** data/kitti_mini, data/synthetic
- **Các frame đã dùng:** 000001, 000010, 000011, 000021, 000049

> Hãy viết ngắn: mỗi mục từ 3 đến 8 dòng, ưu tiên số liệu và hình ảnh.

## 1. Claim

Khi LiDAR bị suy giảm do hạ độ phân giải chùm tia (beam dropout từ 64 xuống 16–8 tia) hoặc thời tiết bất lợi (random dropout giữ lại <= 30%, range cutoff <= 30 m), số điểm phản xạ trên người đi bộ ở khoảng cách > 14 m giảm hơn 70% (xuống dưới ngưỡng tối thiểu 10 điểm để model 3D nhận diện tin cậy), làm tỷ lệ người đi bộ bị đói điểm (pedestrian starvation rate) tăng vọt từ 0.0% lên 57.1% - 71.4%, và tỷ lệ đói điểm toàn bộ vật thể tăng từ 6.8% lên 31.8% - 47.7%.

## 2. Evidence

Dữ liệu chi tiết lưu tại `results/degradation_sweep.csv` và bảng tổng hợp tại `results/degradation_summary.csv`.

| Cấu hình / Mức suy giảm | Starvation Rate (%) | Điểm TB Người đi bộ | Điểm TB Xe con | Ghi chú |
|---|---|---|---|---|
| **Baseline (64 beams / 100% pts)** | **6.82%** (Ped: 0.0%) | 171.7 pts | 380.3 pts | Mốc chuẩn, 100% người đi bộ đủ điểm nhận diện |
| Beam Dropout: 32 beams | 11.36% (Ped: 0.0%) | 90.7 pts | 184.8 pts | Người đi bộ giảm ~47% điểm nhưng vẫn >10 pts |
| Beam Dropout: 16 beams | 31.82% (Ped: **57.14%**) | 53.4 pts | 93.4 pts | 4/7 người đi bộ bị đói điểm (<10 điểm) |
| Beam Dropout: 8 beams | 47.73% (Ped: **71.43%**) | 26.4 pts | 49.5 pts | Hơn 71% người đi bộ mất dấu hình học |
| Random Dropout: keep 70% | 6.82% (Ped: 0.0%) | 120.4 pts | 265.7 pts | Tương đương mưa nhỏ, chưa gây sụp đổ |
| Random Dropout: keep 50% | 13.64% (Ped: 0.0%) | 86.3 pts | 188.6 pts | Điểm trên vật thể giảm một nửa |
| Random Dropout: keep 30% | 20.45% (Ped: **28.57%**) | 53.3 pts | 113.7 pts | Mưa lớn / sương mù, 28.6% người đi bộ bị đói điểm |
| Range Cutoff: <= 30 m | 31.82% (Ped: 28.57%) | 160.0 pts | 373.1 pts | Mất trắng toàn bộ vật thể ngoài 30m |
| Range Cutoff: <= 20 m | 61.36% (Ped: 42.86%) | 156.7 pts | 326.8 pts | 27/44 vật thể bị loại bỏ hoàn toàn |

![degradation_sweep](../results/figures/degradation_sweep.png)
![points_vs_distance](../results/figures/points_vs_distance.png)

### Nhận xét xu hướng định lượng:
1. **Beam Dropout gây suy thoái nghiêm trọng hơn nhiều so với Random Point Loss:** Cùng giảm ~75% số điểm, nhưng hạ xuống 16 beams làm 57.14% người đi bộ bị đói điểm (so với 28.57% của random dropout keep 30%). Nguyên nhân do độ phân giải góc bị thưa, các tia laser bắn xuyên qua khoảng trống giữa thân người thay vì trúng bề mặt.
2. **Khoảng cách khuếch đại mức độ tổn thương:** Người đi bộ ở cự ly > 14m (ví dụ frame `000011` ở 14.5m và 34.2m) chỉ có từ 35–40 điểm ở baseline; khi giảm xuống 16 beams hoặc 8 beams, số điểm rơi thẳng xuống còn 4–7 điểm (dưới ngưỡng 10 điểm), gây hiện tượng "suy sụp nhận diện" (structural collapse).
3. **Xe con có khả năng kháng suy giảm tốt hơn:** Nhờ diện tích phản xạ lớn, ngay cả ở mức 8 beams hoặc random keep 30%, xe con vẫn giữ trung bình 49.5–113.7 điểm, ít bị ảnh hưởng nguy kịch như người đi bộ.

### Mở rộng Bonus (Bằng chứng và phân tích định lượng):

#### [B1] So sánh 2 cơ chế suy giảm: Beam Dropout (hạ số tia) vs Random Dropout (mất điểm ngẫu nhiên) (+4 điểm)

| Tiêu chí so sánh | Beam Dropout (64 -> 16 tia, giữ 25%) | Random Dropout (keep 30% điểm) | Nhận xét phân tích |
|---|---|---|---|
| **Starvation Rate Người đi bộ** | **57.14%** (4/7 người bị đói điểm) | **28.57%** (2/7 người bị đói điểm) | Beam Dropout gây đói điểm gấp 2.0 lần Random Dropout |
| **Starvation Rate Toàn bộ vật thể**| **31.82%** (14/44 vật thể) | **20.45%** (9/44 vật thể) | Mất tia làm sụp đổ hình học trên diện rộng |
| **Cơ chế tác động** | Mất toàn bộ các lát cắt ngang (angular gap giãn rộng 4 lần) | Điểm bị mất phân tán đều khắp không gian | Random loss vẫn giữ được viền contour bao quanh thân |
| **Failure mode riêng biệt** | Điểm bắn xuyên qua người (false negative hoàn toàn) | Mật độ thưa nhưng vẫn còn điểm định vị tâm vật thể | Beam dropout là dạng suy thoái nguy hiểm nhất cho ADAS |

#### [B3] Đo Latency pipeline chuẩn xác (+2 điểm)
- Dữ liệu lưu tại `results/latency_benchmark.csv` (21 vòng lặp liên tiếp trên frame `000011`, loại bỏ vòng 0 warmup).
- **Phần cứng thử nghiệm:** AMD Ryzen 7 6800H with Radeon Graphics (8 cores / 16 threads), 32 GB RAM, Windows 11.
- **Kết quả đo:**
  - Vòng 0 (Warmup): **31.08 ms** (được loại bỏ để tránh méo mó số liệu).
  - Độ trễ trung vị **p50: 30.24 ms** (~33.1 FPS, đáp ứng thời gian thực cho cảm biến LiDAR 10–20 Hz).
  - Phân vị **p95: 31.24 ms**; Mean ± Std: 30.17 ± 0.98 ms (độ biến thiên cực thấp, tính ổn định cao).

#### [B5] So sánh trên cả 2 dataset thật: KITTI vs nuScenes (+2 điểm)

| Đặc trưng | KITTI (`data/kitti_mini`) | nuScenes (`data/nuscenes_mini_subset`) | Tác động tới độ bền vững (Robustness) |
|---|---|---|---|
| **Số chùm tia LiDAR** | 64 beams (Velodyne HDL-64E) | 32 beams | KITTI có mật độ tia dày hơn gấp đôi theo phương đứng |
| **Số điểm trung bình / frame** | 119,318 điểm | 34,719 điểm | nuScenes thưa hơn 3.4 lần, ngưỡng suy sụp đến sớm hơn |
| **Độ phân giải & FOV Camera**| 1242 × 375 (FOV ngang ~81°) | 1600 × 900 (FOV ngang ~70°) | nuScenes ảnh rộng và nét hơn, bù trừ tốt hơn cho LiDAR thưa |
| **Điều kiện môi trường** | Ban ngày, trời quang | Ban ngày (scene-0103) & Ban đêm sau mưa (scene-1094) | nuScenes trong scene-1094 có intensity giảm, phản xạ mặt đường ẩm ướt |
| **Ngưỡng suy sụp nhận diện** | Chịu được suy giảm đến 32 beams | Vốn ở 32 beams, nếu suy giảm thêm sẽ sụp đổ ngay ở cự ly > 10m |

#### [B6] Tìm đủ các lỗi cài sẵn trong `data/synthetic` (+2 điểm)

| Lỗi cài sẵn | Frame bị lỗi | Bằng chứng & Cách phát hiện (Lệnh/Số liệu) |
|---|---|---|
| **1. Lỗi I/O (NaN points)** | Cả 5 frame (`000000` đến `000004`) | Mỗi frame chứa đúng 66–69 điểm `NaN` (tỉ lệ 0.096% - 0.099%). Phát hiện qua `np.isnan(points).sum()` trong `starter.data_health`. |
| **2. Lỗi Time (Timestamp gap)** | Chuyển tiếp giữa `000002` và `000003` | Trong `timestamps.txt`, timestamp nhảy từ 0.200000s lên 0.400000s ($\Delta t = 0.2\text{s}$, gấp đôi chu kỳ chuẩn 0.1s), bị mất 1 frame ở thời điểm 0.3s. |
| **3. Lỗi Cảm biến (Sector dropout)** | Frame `000003` | Số điểm tụt xuống 22,063 điểm (mất ~1,700 điểm so với mức ~23.8k). Phân tích histogram góc azimuth phát hiện vùng góc $[-40^\circ, 0^\circ]$ phía trước-phải bị cắt mất ~70% điểm phản xạ (giả lập vật che cảm biến). |

## 3. Failure case

![failure](../results/figures/fail_01_pedestrian_starvation.png)

- **Trường hợp:** KITTI, frame `000011`, đối tượng người đi bộ (Pedestrian #1) ở khoảng cách 14.5 m khi độ phân giải LiDAR suy giảm do hạ số tia (Beam Dropout từ 64 tia xuống 16 và 8 tia).
- **Quan sát:** Ở mốc chuẩn 64 beams, người đi bộ nhận được 35 điểm phản xạ bao phủ đồng đều dọc theo cơ thể (đủ điều kiện nhận diện tin cậy). Khi bị suy giảm xuống 16 beams (tương đương giữ 1/4 số tia), số điểm giảm tới 82.9% xuống chỉ còn 6 điểm. Khi hạ xuống 8 beams, số điểm chỉ còn 4 điểm. Các điểm này nằm rời rạc trên ảnh và không còn cấu trúc hình học 3D của thân người.
- **Nguyên nhân:** Lỗi phân giải hình học (Geometry) và cảm biến (Sensor resolution). Do góc phân giải đứng (vertical angular resolution) giãn rộng gấp 4 lần (từ ~0.4° lên ~1.6°), khoảng cách giữa hai chùm tia kế tiếp tại khoảng cách 14.5 m là $\Delta z \approx 14.5 \times \tan(1.6^\circ) \approx 0.41\text{ m}$. Với một người đi bộ có bề ngang chỉ ~0.6 m và chiều cao ~1.7 m, chỉ có 1–2 tia laser chạm vào cơ thể, phần lớn xung laser đi xuyên qua khoảng trống, dẫn đến hiện tượng "đói điểm" (point starvation).
- **Lớp debug:** Geometry & Preprocess (Sụt giảm mật độ hình học khiến bước trích xuất đặc trưng điểm/voxel của mô hình 3D detector bị sụp đổ hoàn toàn).
- **Cách phát hiện khi chạy thật:** Giám sát liên tục chỉ số mật độ điểm theo góc quét (point density per solid angle) và theo dõi số điểm trên từng cụm phân cụm sơ bộ. Nếu cụm vật thể nghi vấn ở khoảng cách < 30 m có số điểm $< 10$, hệ thống tự động kích hoạt cờ cảnh báo suy thoái cảm biến (Sensor Degradation Alert).

## 4. Khuyến nghị nếu triển khai thật

- **Use-case cụ thể:** Hệ thống phanh khẩn cấp tự động đô thị (Urban AEB / ADAS Cấp độ 2+/3) và Robot giao hàng tự hành (Autonomous Last-mile Delivery Robot) hoạt động trong môi trường hỗn hợp có nhiều người đi bộ.
- **Đánh đổi khi triển khai (Trade-offs):**
  - *LiDAR rẻ tiền (16 beams) vs LiDAR cao cấp (64–128 beams):* Tiết kiệm 70% chi phí phần cứng nhưng đánh đổi bằng việc mất khả năng phát hiện người đi bộ ở khoảng cách trên 15 m bằng riêng LiDAR đơn lẻ.
  - *Độ an toàn vs Tài nguyên tính toán:* Không thể dựa vào một ngưỡng khoảng cách cố định; cần kết hợp mô hình Fusion đa phương thức (Camera-LiDAR Fusion như BEVFusion hoặc PointPainting) để bù đắp điểm bị thiếu từ kênh ảnh quang học 2D.
- **Chỉ số hệ thống cần ghi log khi chạy thật:**
  - `lidar_beam_health_ratio`: Tỷ lệ các kênh tia LiDAR có tín hiệu phản hồi hợp lệ trong 1 chu kỳ quay (phát hiện cảm biến bị che khuất một phần bởi bùn đất, tuyết).
  - `starved_cluster_ratio`: Tỷ lệ các cụm vật thể kích thước người đi bộ bị thiếu điểm (< 10 điểm) trong bán kính cảnh báo 20 m.
  - `cross_modal_discrepancy`: Độ chênh lệch giữa số lượng bounding box dự đoán từ 2D camera so với 3D LiDAR (phát hiện điểm mù cảm biến).

## 5. Cách chạy lại

Các lệnh tái tạo lại toàn bộ kết quả từ repo sạch.

```bash
# 1. Chạy test phép chiếu baseline
python -m src.test_projection

# 2. Chạy thí nghiệm stress test suy giảm cảm biến LiDAR (CP3)
python -m src.exp_degradation_sweep --data-root data/kitti_mini --frames 000001 000010 000011 000021 000049

# 3. Vẽ biểu đồ phân tích xu hướng và khoảng cách
python -m src.plot_degradation

# 4. Sinh ảnh minh hoạ Failure Case (CP4)
python -m src.visualize_failure_case

# 5. [B3] Đo latency chuẩn xác (21 lần lặp, bỏ warmup)
python -m src.measure_latency --iterations 21

# 6. [B4] Xem trợ giúp CLI tool tái sử dụng
python -m src.exp_degradation_sweep --help
```

## 6. Khai báo sử dụng AI

Ghi rõ đã dùng công cụ AI nào, dùng vào việc gì, và bạn đã tự kiểm chứng kết quả đó bằng cách nào. Nếu không dùng AI, ghi "Không sử dụng". Xem quy định ở `RULES.md` mục 2.

| Công cụ | Dùng cho việc gì | Bạn đã kiểm chứng thế nào |
|---|---|---|
| Claude / GitHub Copilot / Antigravity | Gợi ý cấu trúc tính toán `points_in_box`, tối ưu vòng lặp sweep đa cấu hình và template vẽ đồ thị Matplotlib | Chạy tự kiểm tra ma trận hình học (`test_projection.py`), đối chiếu số điểm thực tế với visual overlay, và so sánh hash file kết quả tái lập 2 lần (`filecmp` đạt IDENTICAL) |
