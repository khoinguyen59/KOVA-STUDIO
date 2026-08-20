# MỤC TIÊU VÀ YÊU CẦU DỰ ÁN CAPCAP (PROJECT GOALS & REQUIREMENTS)

---

## 1. MỤC TIÊU CỐT LÕI (CORE OBJECTIVE)

**CapCap** là ứng dụng chuyên dụng cho việc **Dịch thuật phụ đề** và **Lồng tiếng video (Video Translation & Dubbing)** tự động bằng AI.

---

## 2. NGUYÊN TẮC PHÂN CHIA TÁC VỤ (TASK ALLOCATION RULE)

> **QUY TẮC BẮT BUỘC:**
> **Tất cả các chức năng cần sử dụng GPU đều bắt buộc phải chạy trên Google Colab GPU.**
> Máy tính người dùng (Local Client) chỉ đảm nhiệm các tác vụ nhẹ về giao diện và xử lý media cơ bản.

### Bảng phân định chức năng:

| Thành phần | Nơi thực thi | Mô tả chi tiết |
| :--- | :--- | :--- |
| **Nhận diện giọng nói (ASR)** | **Google Colab (GPU)** | Sử dụng **Faster-Whisper** trên GPU Nvidia T4 để bóc băng âm thanh thành văn bản và mốc thời gian chính xác từng từ (Word-level timestamps). |
| **Tách nhạc nền & giọng nói** | **Google Colab (GPU)** | Sử dụng **Demucs** trên GPU Colab để tách giọng nói gốc và giữ lại rãnh nhạc nền cho video lồng tiếng. |
| **Tạo giọng đọc AI (TTS)** | **Google Colab (GPU)** | Sử dụng mô hình tổng hợp giọng nói trên GPU Colab để tạo giọng lồng tiếng mượt mà, tự nhiên và đúng nhịp điệu câu thoại. |
| **Dịch thuật phụ đề** | **AI Cloud / Local API** | Dịch thuật và chuốt câu (AI Polish) bằng Gemini / Google Web Translate theo phong cách tự nhiên. |
| **Giao diện & Timeline** | **Máy tính (Local)** | Hiển thị Timeline đa rãnh, cho phép chỉnh sửa văn bản, kéo mốc thời gian, nghe thử và xem trước video thời gian thực. |
| **Render & Xuất video** | **Máy tính (Local)** | Ghép rãnh giọng lồng tiếng, nhạc nền, gắn phụ đề (Hardsub/Softsub) và render video đầu ra bằng FFmpeg. |

---

## 3. CÁC TÍNH NĂNG CHÍNH CỦA DỰ ÁN (KEY FEATURES)

### 3.1. Dịch thuật video (Video Translation)
* Tự động nhận diện ngôn ngữ nguồn (Tiếng Trung, Tiếng Anh, Tiếng Nhật, Tiếng Hàn...).
* Trích xuất phụ đề gốc với mốc thời gian chuẩn xác.
* Dịch sang ngôn ngữ đích (Tiếng Việt, Tiếng Anh...) với bản dịch thoát nghĩa, tự nhiên.

### 3.2. Lồng tiếng video (Video Dubbing)
* Tách và giữ nguyên rãnh nhạc nền/âm thanh môi trường gốc của video.
* Tạo giọng đọc lồng tiếng AI mới khớp với từng câu phụ đề đã dịch.
* Tự động đồng bộ tốc độ đọc (Auto Speed Sync) để giọng đọc khớp chuẩn với độ dài câu thoại gốc của diễn viên.
* Tự động giảm âm lượng nhạc nền khi có giọng đọc lồng tiếng (Audio Ducking).

### 3.3. Trình chỉnh sửa Timeline trực quan (Timeline Editor)
* Quản lý đa rãnh: Rãnh Video, Rãnh Phụ đề, Rãnh Giọng lồng tiếng, Rãnh Nhạc nền.
* Cho phép người dùng trực tiếp sửa chữ, tách/gộp câu, kéo chỉnh mốc thời gian và nghe thử từng câu trước khi xuất bản.

### 3.4. Xuất bản Video (Export)
* Xuất video hoàn chỉnh có lồng tiếng và phụ đề gắn cứng (Hardsub).
* Xuất file phụ đề rời (`.srt`, `.ass`).
* Xuất file âm thanh lồng tiếng riêng lẻ.

---

## 4. TIÊU CHUẨN HOẠT ĐỘNG (OPERATIONAL CONSTRAINTS)

1. **Chặn 100% việc chạy AI nặng trên CPU máy tính:**
   * Không bao giờ để máy tính tự ý chạy Whisper hay Demucs trên CPU cục bộ gây đơ/treo máy.
   * Nếu chưa kết nối Colab hoặc mất kết nối, hệ thống lập tức dừng lại và yêu cầu người dùng nhập link Colab.
2. **Không lưu vết link Colab cũ:**
   * Mỗi lần mở ứng dụng, các ô nhập URL và Token của Colab luôn tự động để trống để sẵn sàng dán link mới của phiên chạy đó.
