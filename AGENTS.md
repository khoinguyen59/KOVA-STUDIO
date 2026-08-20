# QUY TẮC BẮT BUỘC KHI LÀM VIỆC VỚI DỰ ÁN CAPCAP (MANDATORY RULES)

## 1. QUY TẮC XÁC NHẬN TRƯỚC KHI SỬA CODE (STRICT APPROVAL BEFORE CODING)
- **Tuyệt đối KHÔNG ĐƯỢC tự ý cắm đầu sửa code hoặc chạy lệnh sửa đổi hệ thống ngay lập tức.**
- **Bắt buộc phải tuân thủ quy trình 3 bước sau trong MỌI lượt trả lời:**
  1. **Giải thích thông tin cặn kẽ**: Nêu rõ hiện tượng gì đang xảy ra, lỗi ở đâu, file nào, nguyên nhân gốc rễ là gì.
  2. **Đề xuất hướng giải quyết**: Trình bày rõ phương án xử lý, các file dự kiến sẽ sửa và lý do chọn cách đó.
  3. **CHỜ XÁC NHẬN**: Dừng lại và yêu cầu người dùng xác nhận / đồng ý. Chỉ khi người dùng đồng ý mới được tiến hành viết code, sửa file hoặc build.

---

## 2. QUY TẮC GHI CHÉP LỊCH SỬ LỖI (ERROR & FIX LOGGING)
- Sau mỗi lần sửa lỗi hoặc khi phát hiện lỗi mới, **BẮT BUỘC** phải cập nhật thông tin vào file [`ERROR_LOG.md`](file:///c:/Users/Nguyen%20Trong%20Khoi/Downloads/CAPCAP/ERROR_LOG.md).
- Cấu trúc mỗi mục trong log:
  - Thời gian & Tên lỗi
  - Mô tả hiện tượng
  - Nguyên nhân gốc rễ (Root Cause)
  - Cách thức đã xử lý (Fix Details)
  - Các file liên quan

---

## 3. QUY TẮC DUY TRÌ TÀI LIỆU KIẾN TRÚC DỰ ÁN (PROJECT STRUCTURE INTEGRITY)
- File [`PROJECT_STRUCTURE.md`](file:///c:/Users/Nguyen%20Trong%20Khoi/Downloads/CAPCAP/PROJECT_STRUCTURE.md) là tài liệu chuẩn mô tả toàn bộ kiến trúc, thư mục, chức năng từng module và luồng hoạt động của CapCap.
- Khi có bất kỳ thay đổi lớn nào về luồng xử lý hoặc cấu trúc module, phải cập nhật file này ngay lập tức.

---

## 4. QUY TẮC MÔI TRƯỜNG THỰC THI (ENVIRONMENT & SHELL)
- Môi trường: Windows.
- Luôn sử dụng cú pháp `cmd /c <lệnh>` khi chạy terminal và thêm dấu Enter (`\n`) ở cuối lệnh.
- Không sử dụng shell tương tác.
- Tất cả các tác vụ AI nặng (Whisper, Demucs, TTS) bắt buộc phải tuân thủ định tuyến qua Colab GPU, cấm chạy ngầm CPU cục bộ.
