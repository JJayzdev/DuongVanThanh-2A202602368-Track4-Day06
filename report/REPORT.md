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

Khi LiDAR bị suy giảm do giảm độ phân giải chùm tia (beam dropout xuống 16–8 tia tương đương) hoặc thời tiết bất lợi (random dropout giữ lại <= 30%, range cutoff < 25 m), số điểm phản xạ trên người đi bộ ở khoảng cách > 14 m giảm hơn 70% (xuống dưới ngưỡng tối thiểu 10 điểm để model phát hiện tin cậy), làm tỷ lệ vật thể bị đói điểm (starvation rate) tăng vọt từ 12.5% lên 44.0% - 73.6%.

## 2. Evidence

Bảng hoặc plot số liệu, kèm ảnh/video demo. Ghi rõ đường dẫn file trong `results/`.

| Cấu hình / mức perturb | Metric 1 | Metric 2 | Ghi chú |
|---|---|---|---|
| [ĐIỀN] | | | |

![demo](../results/figures/[ĐIỀN].png)

## 3. Failure case

Nêu khi nào hệ thống hoặc phương pháp fail, vì sao fail, và liên hệ tới lớp nào trong 6 lớp debug: I/O, Geometry, Time, Preprocess, Model, Metric.

![failure](../results/figures/fail_[ĐIỀN].png)

[ĐIỀN]

## 4. Khuyến nghị nếu triển khai thật

Use-case cụ thể (ADAS / robot / drone), trade-off và bước tiếp theo.

[ĐIỀN]

## 5. Cách chạy lại

Các lệnh tái tạo lại toàn bộ kết quả từ repo sạch.

```bash
[ĐIỀN]
```

## 6. Khai báo sử dụng AI

Ghi rõ đã dùng công cụ AI nào, dùng vào việc gì, và bạn đã tự kiểm chứng kết quả đó bằng cách nào. Nếu không dùng AI, ghi "Không sử dụng". Xem quy định ở `RULES.md` mục 2.

| Công cụ | Dùng cho việc gì | Bạn đã kiểm chứng thế nào |
|---|---|---|
| [ĐIỀN] | | |
