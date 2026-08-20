# NHẬT KÝ THEO DÕI VÀ XỬ LÝ LỖI (CAPCAP ERROR & DEBUG LOG)

Tài liệu này lưu trữ toàn bộ các lỗi kỹ thuật phát sinh trong suốt vòng đời phát triển của dự án **CapCap**, kèm phân tích nguyên nhân gốc rễ và giải pháp kỹ thuật đã áp dụng để xử lý triệt để.

---

## BẢNG TỔNG HỢP NHANH CÁC LỖI (ERROR SUMMARY TABLE)

| STT | Tên lỗi | Giai đoạn | Mức độ | Trạng thái |
| :---: | :--- | :---: | :---: | :---: |
| **01** | Bấm nút New Project không phản hồi | Khởi tạo giao diện | Nghiêm trọng | Đã fix triệt để |
| **02** | Nút Preview Voice không phát âm thanh | Tính năng Lồng tiếng | Trung bình | Đã fix triệt để |
| **03** | Bấm Generate chạy thẳng không kiểm tra Colab | Luồng Pipeline | Nghiêm trọng | Đã fix triệt để |
| **04** | Hiện popup báo lỗi đỏ thay vì mở Cài đặt Colab | Trải nghiệm UI/UX | Nhẹ | Đã fix triệt để |
| **05** | Ký tự BOM UTF-8 gây lỗi Syntax khi build | Đóng gói hệ thống | Nghiêm trọng | Đã fix triệt để |
| **06** | Trùng lặp dự án & đè trạng thái cũ | Quản lý dự án | Nghiêm trọng | Đã fix triệt để |
| **07** | PyInstaller thiếu DLLs & Hidden Imports | Đóng gói hệ thống | Nghiêm trọng | Đã fix triệt để |
| **08** | Cảnh báo Qt Signal Disconnect khi tắt app | Tối ưu hóa UI | Nhẹ | Đã fix triệt để |
| **09** | Treo 8–10 phút do Fallback ngầm về CPU | Động cơ ASR | Rất nghiêm trọng | Đã fix triệt để |
| **10** | URL & Token Colab bị lưu đè / không tự xóa | Phiên làm việc | Trung bình | Đã fix triệt để |
| **11** | Khung cảnh báo đỏ trong hộp thoại Colab | Trải nghiệm UI/UX | Nhẹ | Đã fix triệt để |
| **12** | Treo 20 phút do gọi nhầm server `127.0.0.1` | Luồng Pipeline | Rất nghiêm trọng | Đã fix triệt để |
| **13** | Lỗi 404 Not Found khi gọi `/v1/prepare` | Tích hợp Colab | Nghiêm trọng | Đã fix triệt để |
| **14** | Lỗi 500 Internal Server Error khi gọi `/v1/transcribe` | Tích hợp Colab | Nghiêm trọng | Đã fix triệt để |
| **15** | Server Colab tự gọi lại API remote và tách giọng chạy CPU local | Định tuyến AI/Colab | Rất nghiêm trọng | Đã fix triệt để |
| **20** | Ứng dụng văng Qt6Core sau khi hoàn tất pipeline hoặc tạo waveform | Vòng đời QThread/đóng gói | Rất nghiêm trọng | Đã fix triệt để |
| **21** | Yêu cầu Colab All-in-One chỉ được báo sau khi đã hoàn tất phụ đề | Kiểm tra capability | Nghiêm trọng | Đã fix triệt để |
| **22** | Setup Colab vẫn mở notebook Whisper-only | Cấu hình notebook | Nghiêm trọng | Đã fix triệt để |
| **23** | SRT gốc từ nút Transcription chỉ nằm trong thư mục tạm | Lưu trữ dự án | Trung bình | Đã fix triệt để |
| **24** | Không thể lấy đồng thời nguồn STT và OCR độc lập | Luồng tạo phụ đề | Trung bình | Đã fix triệt để |
| **25** | Processed Files có thể lỗi khi kiểm tra đường dẫn artifact | Hiển thị artifact | Nhẹ | Đã fix triệt để |

---

## CHI TIẾT CÁC LỖI VÀ GIẢI PHÁP XỬ LÝ (DETAILED ERROR REPORTS)

### 1. Lỗi nút New Project không phản hồi khi bấm từ Start Panel
* **Mô tả hiện tượng:** Khi người dùng vừa mở app lên, bấm nút "New Project" trên màn hình Start Panel thì ứng dụng bị đơ, không có phản hồi và không mở hộp thoại chọn file video.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Tín hiệu `clicked` của `new_project_btn` trong `ui/views/start_panel.py` chưa được nối đúng với hàm điều phối `open_video_file()` trong `ui/main_window.py`.
  * Khởi tạo `workspace_root` và `ProjectService` bị trễ so với chu kỳ render giao diện của Qt.
* **Cách xử lý (Fix Details):**
  * Nối trực tiếp Signal `new_project_btn.clicked` tới hàm mở hộp thoại `QFileDialog.getOpenFileName`.
  * Khởi tạo sẵn sàng `workspace_root` và nạp dự án mượt mà ngay khi chọn xong file video.
* **File liên quan:** [`ui/views/start_panel.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/views/start_panel.py), [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py).

---

### 2. Lỗi Preview Voice không phát âm thanh
* **Mô tả hiện tượng:** Bấm nút "Nghe thử" (Preview Voice) trong danh sách giọng đọc tiếng Việt thì không nghe thấy âm thanh hoặc giao diện bị đơ tạm thời.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Chưa tích hợp worker chạy ngầm cho tính năng preview giọng nhanh; gọi tổng hợp âm thanh đồng bộ trên luồng chính làm nghẽn UI.
* **Cách xử lý (Fix Details):**
  * Tạo luồng nền xử lý preview nhanh một câu mẫu ngắn 2–3 từ, sử dụng `QMediaPlayer` phát audio ngay lập tức mà không ảnh hưởng luồng giao diện.
* **File liên quan:** [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py), [`app/tts_processor.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/tts_processor.py).

---

### 3. Lỗi Bấm Generate chạy thẳng không kiểm tra kết nối Colab
* **Mô tả hiện tượng:** Khi chưa cài Colab hoặc Colab đang offline, người dùng bấm nút Generate thì app vẫn tiến hành chạy, sau đó mới văng lỗi hoặc treo tiến trình.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Nút `run_all_btn` trong `pipeline_controller.py` thiếu bước kiểm tra tiền khả thi (Pre-flight Gate) đối với biến môi trường `CAPCAP_REMOTE_API_URL`.
* **Cách xử lý (Fix Details):**
  * Bổ sung hàm kiểm tra kết nối Colab trước khi chạy bất kỳ bước nào trong pipeline. Nếu URL trống hoặc offline, lập tức dừng pipeline và mở màn hình Cài đặt Colab.
* **File liên quan:** [`ui/controllers/pipeline_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/pipeline_controller.py).

---

### 4. Lỗi Hiện popup báo lỗi đỏ thay vì mở thẳng màn hình Cài đặt Colab
* **Mô tả hiện tượng:** Khi phát hiện chưa có Colab, ứng dụng hiện một bảng thông báo lỗi màu đỏ bắt người dùng phải bấm OK rồi tự đi tìm chỗ mở cài đặt.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Sử dụng `QMessageBox.warning` để chặn luồng thay vì điều hướng giao diện trực quan.
* **Cách xử lý (Fix Details):**
  * Loại bỏ hoàn toàn popup cảnh báo, tự động mở thẳng hộp thoại Cài đặt Colab (`open_model_settings_dialog(focus_colab=True)`) và focus sẵn con trỏ chuột vào ô nhập URL.
* **File liên quan:** [`ui/controllers/pipeline_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/pipeline_controller.py), [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py).

---

### 5. Lỗi Ký tự BOM UTF-8 gây lỗi Syntax khi build đóng gói
* **Mô tả hiện tượng:** Quá trình đóng gói PyInstaller bị lỗi biên dịch cú pháp trên một số file mã nguồn Python.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Một số trình soạn thảo trên Windows tự động chèn ký tự Byte Order Mark (`\xef\xbb\xbf`) vào đầu file khi lưu file UTF-8.
* **Cách xử lý (Fix Details):**
  * Tạo script `clean_bom.py` tự động quét toàn bộ 140 file Python trong dự án và loại bỏ hoàn toàn ký tự BOM trước khi chạy audit và build.
* **File liên quan:** [`clean_bom.py`](file:///C:/NTKhoi/Downloads/CAPCAP/clean_bom.py), [`build_final_clean.bat`](file:///C:/NTKhoi/Downloads/CAPCAP/build_final_clean.bat).

---

### 6. Lỗi Trùng lặp dự án & Đè trạng thái cũ (Project State Cache Desync)
* **Mô tả hiện tượng:** Khi người dùng mở một video mới, phần phụ đề và audio đôi khi vẫn giữ lại dữ liệu của video trước đó.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Thư mục cache và ID dự án sử dụng đường dẫn cố định, không phân biệt theo mã băm nội dung của file video.
* **Cách xử lý (Fix Details):**
  * Xây dựng cơ chế sinh fingerprint duy nhất (SHA256 kết hợp đường dẫn, dung lượng và mtime của video), đảm bảo mỗi video có một thư mục dự án độc lập hoàn toàn.
* **File liên quan:** [`app/services/project_service.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/services/project_service.py).

---

### 7. Lỗi PyInstaller thiếu DLLs & Hidden Imports khi đóng gói EXE
* **Mô tả hiện tượng:** File `CapCap.exe` build ra mở lên ở máy khác bị crash do thiếu các thư viện (Shapely, OmegaConf, PyClipper, FFmpeg).
* **Nguyên nhân gốc rễ (Root Cause):**
  * PyInstaller không tự động truy vết được các thư viện C++ động và module import gián tiếp.
* **Cách xử lý (Fix Details):**
  * Cấu hình đầy đủ danh sách `hiddenimports` và `binaries` trong file `CapCap.spec`, đóng gói kèm binary `ffmpeg.exe` và `ffprobe.exe` trong thư mục `bin/`.
* **File liên quan:** [`CapCap.spec`](file:///C:/NTKhoi/Downloads/CAPCAP/CapCap.spec), [`build_final_clean.bat`](file:///C:/NTKhoi/Downloads/CAPCAP/build_final_clean.bat).

---

### 8. Lỗi Cảnh báo Runtime Qt Signal Disconnect khi đóng app
* **Mô tả hiện tượng:** Khi tắt ứng dụng, terminal xuất hiện cảnh báo `RuntimeWarning: libpyside: Failed to disconnect...`.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Hàm cleanup cố gắng disconnect một Signal từ widget đã bị hủy trước đó trong cây bộ nhớ Qt.
* **Cách xử lý (Fix Details):**
  * Không gọi `disconnect` trong lúc shutdown. Thay vào đó, chặn signal tạm thời bằng `blockSignals(True)` khi xóa blur overlay, rồi khôi phục trạng thái signal.
* **File liên quan:** [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py).

---

### 9. Lỗi Treo 8–10 phút do Fallback ngầm về CPU máy tính
* **Mô tả hiện tượng:** Khi mất kết nối Colab hoặc Colab chưa sẵn sàng, ứng dụng tự động chạy ngầm trên CPU máy tính mất 8–10 phút làm quạt máy quay tối đa và nghẽn CPU.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Các adapter `RemoteWhisperAdapter`, `RemoteTTSAdapter`, `RemoteTranslatorAdapter` có nhánh code `except: fallback to local WhisperAdapter()`.
* **Cách xử lý (Fix Details):**
  * Gỡ bỏ 100% các nhánh code fallback về CPU.
  * Khóa profile hệ thống mặc định là `remote` (Colab GPU). Nếu mất kết nối, hệ thống ngắt ngay lập tức và báo lỗi thay vì chạy CPU.
* **File liên quan:** [`app/engines/remote_whisper_adapter.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/engines/remote_whisper_adapter.py), [`app/runtime_profile.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/runtime_profile.py).

---

### 10. Lỗi URL & Token Colab bị lưu đè / không tự động làm trống
* **Mô tả hiện tượng:** Mỗi lần mở lại app, link Colab cũ của phiên trước vẫn còn hiển thị, gây nhầm lẫn vì mỗi phiên Colab đều sinh ra một link mới.
* **Nguyên nhân gốc rễ (Root Cause):**
  * File `.env` cũ được sao lưu và nạp đè vào `os.environ` khi khởi động.
* **Cách xử lý (Fix Details):**
  * Thêm hook dọn dẹp biến môi trường lúc khởi động (`os.environ.pop("CAPCAP_REMOTE_API_URL")`).
  * Luôn gán ô nhập liệu `remote_url_edit.setText("")` và `remote_token_edit.setText("")` mỗi khi mở hộp thoại Colab.
* **File liên quan:** [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py), [`ui/gui.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/gui.py).

---

### 11. Lỗi Khung cảnh báo đỏ trong hộp thoại Colab
* **Mô tả hiện tượng:** Khi mở bảng Cài đặt Colab, xuất hiện một khung viền màu đỏ báo lỗi gây mất thẩm mỹ.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Tồn tại widget `warning_label` được tạo sẵn trong phương thức `open_model_settings_dialog`.
* **Cách xử lý (Fix Details):**
  * Xóa bỏ hoàn toàn widget `warning_label`, giao diện cài đặt mở ra sạch sẽ và trỏ chuột thẳng vào ô nhập link.
* **File liên quan:** [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py).

---

### 12. Lỗi Treo 20 phút do code gọi nhầm server nội bộ `127.0.0.1` (Local Worker Bypass)
* **Mô tả hiện tượng:** Người dùng đã nhập link Colab nhưng khi bấm Generate, tiến trình vẫn bị dừng ở bước `Transcribing audio` và chạy hơn 20 phút.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Trong `pipeline_controller.py`, hàm `run_all_pipeline` khởi chạy `self._start_local_worker_server()` và gán địa chỉ `self.local_worker_api_url` (`127.0.0.1`) vào worker thay vì lấy link Colab URL.
* **Cách xử lý (Fix Details):**
  * Kiểm tra nếu có link Colab thì truyền trực tiếp URL Colab đó vào worker và bỏ qua hoàn toàn việc khởi chạy server Python cục bộ.
* **File liên quan:** [`ui/controllers/pipeline_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/pipeline_controller.py).

---

### 13. Lỗi 404 Not Found do gửi nhầm request `/v1/prepare` lên Colab
* **Mô tả hiện tượng:** Ứng dụng báo lỗi màu đỏ: `Prepare workflow failed: Local worker /v1/prepare failed (404): {"detail":"Not Found"}` ngay sau 2 giây.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Máy chủ Google Colab (`CapCap_Whisper_Colab.ipynb`) là server chuyên dụng cho Whisper GPU, chỉ cung cấp 2 endpoint: `GET /health` và `POST /v1/transcribe`.
  * `PrepareWorkflowWorker.run()` lại cố gửi toàn bộ payload dự án vào endpoint `/v1/prepare` (đường dẫn không tồn tại trên Colab).
* **Cách xử lý (Fix Details):**
  * Chạy `PrepareWorkflow` trực tiếp trên client thread (trích xuất audio siêu nhanh < 1s), và chỉ gửi request **`POST /v1/transcribe`** lên Colab GPU khi đến bước bóc băng Whisper.
* **File liên quan:** [`ui/worker_adapters/processing_workers.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/worker_adapters/processing_workers.py), [`colab/CapCap_Whisper_Colab.ipynb`](file:///C:/NTKhoi/Downloads/CAPCAP/colab/CapCap_Whisper_Colab.ipynb).

---

### 14. Lỗi 500 Internal Server Error khi gọi `/v1/transcribe` lên Colab
* **Mô tả hiện tượng:** Khi gọi bóc băng lên Colab, sau khoảng 35s ứng dụng báo lỗi: `Local worker /v1/transcribe failed (500): Internal Server Error`.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Trong sổ tay Colab, việc load mô hình Whisper và khởi tạo bộ nhớ GPU nằm ngoài `try...except`, đồng thời chưa tự động phát hiện thiết bị GPU/CPU.
  * Client `remote_api.py` chỉ bóc tách `error_payload.get("error")` mà bỏ qua trường chuẩn `error_payload.get("detail")` của FastAPI, khiến chi tiết lỗi bị ẩn.
  * Thiếu hàm chuẩn hóa mã ngôn ngữ (ví dụ `zh-CN` gửi lên thay vì `zh`).
* **Cách xử lý (Fix Details):**
  * Cập nhật `app/remote_api.py` để trích xuất cả `detail` và `error` từ phản hồi JSON của FastAPI.
  * Thêm hàm `_normalize_language` trong `app/engines/remote_whisper_adapter.py` để làm sạch mã ngôn ngữ.
  * Cập nhật sổ tay Colab tự động nhận diện GPU (`torch.cuda.is_available()`), bọc toàn bộ hàm `transcribe` trong `try...except` và in traceback chi tiết.
* **File liên quan:** [`app/remote_api.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/remote_api.py), [`app/engines/remote_whisper_adapter.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/engines/remote_whisper_adapter.py), [`colab/CapCap_Whisper_Colab.ipynb`](file:///C:/NTKhoi/Downloads/CAPCAP/colab/CapCap_Whisper_Colab.ipynb).

---

### 15. Lỗi All-in-One Colab tự gọi ngược API remote và tách giọng chạy CPU local
* **Thời gian:** 20/08/2026
* **Mô tả hiện tượng:** Chạy notebook All-in-One có thể treo ở TTS/dịch hoặc tách giọng khiến máy Windows chạy ONNX trên CPU.
* **Nguyên nhân gốc rễ (Root Cause):**
  * Notebook khởi động `remote_api_server.py` với `CAPCAP_RUNTIME_PROFILE=remote`. Khi server xử lý một request, `EngineRuntime` lại chọn remote adapter và gọi chính server đó trong khi GPU lock đang giữ.
  * `EngineRuntime.demucs` không có adapter remote; `vocal_processor.py` lại ép `CPUExecutionProvider`, nên thao tác tách giọng từ client chạy cục bộ.
  * Client chỉ kiểm tra URL/health, không xác nhận server có các capability cần cho Whisper, TTS và tách giọng.
* **Cách xử lý (Fix Details):**
  * Server ép profile nội bộ `local`, xóa URL remote kế thừa và notebook All-in-One đặt thiết bị `cuda`.
  * Thêm endpoint `/v1/separate-vocals`, `RemoteVocalAdapter` và bắt buộc `CUDAExecutionProvider` cho tách giọng.
  * Thêm capability vào `/health`; client mở Settings ngay khi server không có capability cần thiết. URL/token chỉ tồn tại trong phiên, không được ghi vào `.env`.
  * Thêm `test_release_contract.py` để kiểm tra syntax, notebook, định tuyến API và cô lập profile server.
* **File liên quan:** [`app/remote_api_server.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/remote_api_server.py), [`app/engines/remote_vocal_adapter.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/engines/remote_vocal_adapter.py), [`app/vocal_processor.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/vocal_processor.py), [`colab/CapCap_All_in_One_Colab.ipynb`](file:///C:/NTKhoi/Downloads/CAPCAP/colab/CapCap_All_in_One_Colab.ipynb), [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py).

---

### 16. Nhánh pipeline/Whisper còn có thể chạy CPU khi cấu hình Colab lỗi
* **Thời gian:** 20/08/2026
* **Mô tả hiện tượng:** Dù giao diện mặc định remote, việc tắt URL trong Settings hoặc lỗi tải CUDA của Whisper vẫn có thể đưa một số nhánh sang local worker/CPU.
* **Nguyên nhân gốc rễ (Root Cause):** `run_all_pipeline` còn giữ local-worker fallback; Settings có thể đổi runtime profile thành `local`; Whisper không import trực tiếp `os` và có cơ chế CPU fallback không bị khóa khi chạy All-in-One.
* **Cách xử lý (Fix Details):** Khóa desktop ở runtime profile `remote`, yêu cầu Colab có capability trước khi transcribe vùng chọn/pipeline, bỏ fallback local trong pipeline, thêm `CAPCAP_REQUIRE_GPU=1` cho All-in-One và chặn mọi CPU fallback của Whisper khi cờ này bật.
* **File liên quan:** [`ui/controllers/pipeline_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/pipeline_controller.py), [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py), [`app/whisper_processor.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/whisper_processor.py), [`colab/CapCap_All_in_One_Colab.ipynb`](file:///C:/NTKhoi/Downloads/CAPCAP/colab/CapCap_All_in_One_Colab.ipynb).

---

### 17. Build one-file dừng trước khi tạo EXE trong thư mục release
* **Thời gian:** 20/08/2026
* **Mô tả hiện tượng:** PyInstaller phân tích và tạo `build/onefile/CapCap/CapCap.exe` trung gian nhưng `release/CapCap.exe` không xuất hiện, khiến batch build thất bại ở bước kiểm tra đầu ra.
* **Nguyên nhân gốc rễ (Root Cause):** `CapCap.spec` đã bỏ `COLLECT` để chuyển sang one-file nhưng vẫn giữ `exclude_binaries=True`. Cờ này chỉ phù hợp với mô hình one-folder (binaries sẽ do `COLLECT` đóng gói), nên EXE one-file không thể hoàn tất assembly.
* **Cách xử lý (Fix Details):** Bỏ `exclude_binaries=True` để `EXE` nhúng `a.binaries`, `a.zipfiles` và `a.datas` thành một executable duy nhất.
* **File liên quan:** [`CapCap.spec`](file:///C:/NTKhoi/Downloads/CAPCAP/CapCap.spec), [`build_final_clean.bat`](file:///C:/NTKhoi/Downloads/CAPCAP/build_final_clean.bat).

---

### 18. EXE chạy nhưng không hiển thị cửa sổ
* **Thời gian:** 20/08/2026
* **Mô tả hiện tượng:** Mở `CapCap.exe` tạo tiến trình nhưng không thấy launcher hoặc cửa sổ giao diện.
* **Nguyên nhân gốc rễ (Root Cause):** Qt có thể kế thừa `QT_QPA_PLATFORM=offscreen` từ luồng test/export trước khi `QApplication` khởi tạo. Khi đó ứng dụng vẫn chạy nhưng không tạo cửa sổ Windows hiển thị.
* **Cách xử lý (Fix Details):** Entry point của EXE ép Qt dùng platform `windows`; chỉ cho phép `offscreen` khi cờ rõ ràng `CAPCAP_HEADLESS=1` được đặt bởi smoke test.
* **File liên quan:** [`ui/gui.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/gui.py), [`test_release_contract.py`](file:///C:/NTKhoi/Downloads/CAPCAP/test_release_contract.py).

---

### 19. Smoke test one-file để lại child process và khóa single-instance
* **Thời gian:** 20/08/2026
* **Mô tả hiện tượng:** Sau smoke test headless, mở EXE desktop lần tiếp theo không tạo cửa sổ vì còn một tiến trình CapCap ẩn.
* **Nguyên nhân gốc rễ (Root Cause):** EXE one-file của PyInstaller chạy theo parent bootloader và child GUI. `process.terminate()` chỉ đóng parent, để child giữ mutex `CapCap.SingleInstance`.
* **Cách xử lý (Fix Details):** Smoke test trên Windows dùng `taskkill /T /F` trên parent PID để kết thúc trọn cây tiến trình trước khi trả về.
* **File liên quan:** [`test_release_contract.py`](file:///C:/NTKhoi/Downloads/CAPCAP/test_release_contract.py).

---

### 20. Ứng dụng văng Qt6Core sau khi hoàn tất pipeline hoặc tạo waveform
* **Thời gian:** 20/08/2026
* **Mô tả hiện tượng:** Sau khi Colab đã bóc băng thành công, ứng dụng có thể đóng đột ngột. Windows Event Viewer ghi lỗi `Qt6Core.dll`, mã `0xc0000409` (BEX64). Đồng thời log runtime báo `numpy._core._multiarray_umath` không tải được DLL khi tạo waveform trên Timeline.
* **Nguyên nhân gốc rễ (Root Cause):** Nhiều lớp `QThread` khai báo Signal kết quả tên `finished`, che khuất Signal vòng đời gốc `QThread.finished`. Callback kết quả sau đó giải phóng tham chiếu worker trước khi native thread thực sự kết thúc, dẫn tới lỗi bộ nhớ trong Qt. Môi trường build cũng có NumPy hỏng/thiếu DLL OpenBLAS, nên EXE không thể nạp NumPy cho waveform.
* **Cách xử lý (Fix Details):** Đổi toàn bộ Signal kết quả của worker sang `result_ready`; chỉ dùng `QThread.finished` gốc để giữ tham chiếu và hủy worker sau khi thread dừng. Bổ sung đóng gói bắt buộc các DLL NumPy/`numpy.libs` và kiểm tra import NumPy ngay khi build. Thêm test tự động kiểm tra không được che khuất `QThread.finished` và chạy worker waveform tối giản đến khi native thread kết thúc.
* **File liên quan:** [`ui/worker_adapters/processing_workers.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/worker_adapters/processing_workers.py), [`ui/worker_adapters/preview_workers.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/worker_adapters/preview_workers.py), [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py), [`ui/controllers/pipeline_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/pipeline_controller.py), [`ui/controllers/preview_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/preview_controller.py), [`ui/controllers/subtitle_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/subtitle_controller.py), [`CapCap.spec`](file:///C:/NTKhoi/Downloads/CAPCAP/CapCap.spec), [`test_release_contract.py`](file:///C:/NTKhoi/Downloads/CAPCAP/test_release_contract.py).

---

### 21. Yêu cầu Colab All-in-One chỉ được báo sau khi đã hoàn tất phụ đề
* **Thời gian:** 21/08/2026
* **Mô tả hiện tượng:** Người dùng có thể chạy bước Transcript bằng notebook Whisper-only, sau đó khi chuyển sang tạo voice mới nhận thông báo thiếu capability `tts`. Hộp thoại xuất hiện khi Progress Dialog đã sang Stage 2/3, tạo cảm giác phải chạy hai notebook.
* **Nguyên nhân gốc rễ (Root Cause):** `PipelineController` chỉ thêm capability `tts` khi `target_stage` là `full`; các luồng chạy theo bước và luồng tiếp tục Voice kiểm tra TTS quá muộn.
* **Cách xử lý (Fix Details):** Tập trung xác định capability vào `required_colab_capabilities`. Với mode Voice/Both, `tts` luôn là yêu cầu ngay cả khi bắt đầu từ Transcript hoặc Translate; mode Clean kiểm tra thêm `separate_vocals`. Trước khi mở Progress Dialog TTS, ứng dụng kiểm tra `tts` ngay lập tức.
* **File liên quan:** [`ui/controllers/pipeline_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/pipeline_controller.py), [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py), [`test_release_contract.py`](file:///C:/NTKhoi/Downloads/CAPCAP/test_release_contract.py).

---

### 22. Setup Colab vẫn mở notebook Whisper-only
* **Thời gian:** 21/08/2026
* **Mô tả hiện tượng:** Hai nút trong Settings có thể dẫn người dùng tới notebook Whisper-only, nên server chỉ có `transcribe` và thất bại ở TTS.
* **Nguyên nhân gốc rễ (Root Cause):** URL hard-code trỏ tới `CapCap_Whisper_Colab.ipynb`; nút mở file lại mở toàn bộ thư mục Colab.
* **Cách xử lý (Fix Details):** Cả hai nút nay chỉ mở `CapCap_All_in_One_Colab.ipynb`: một nút mở Colab trên GitHub, một nút mở trực tiếp đúng file cục bộ. Test contract chặn mọi tham chiếu UI về notebook Whisper-only.
* **File liên quan:** [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py), [`test_release_contract.py`](file:///C:/NTKhoi/Downloads/CAPCAP/test_release_contract.py).

---

### 23. SRT gốc từ nút Transcription chỉ nằm trong thư mục tạm
* **Thời gian:** 21/08/2026
* **Mô tả hiện tượng:** SRT gốc tạo bằng pipeline đã có vị trí cố định, nhưng SRT từ nút Transcription thủ công lại được lưu trong thư mục tạm theo tên video, khó tìm để dịch bằng IDE ngoài.
* **Nguyên nhân gốc rễ (Root Cause):** `SubtitleController` dùng `get_project_temp_dir("subtitle")` thay vì thư mục subtitle chính thức của ProjectService.
* **Cách xử lý (Fix Details):** Cả pipeline và nút Transcription giờ dùng một đường dẫn chuẩn: `projects/<project-id>/subtitle/original.srt`. File được ghi trong artifact của project, hiển thị trong Processed Files và có thể mở trực tiếp bằng Antigravity IDE.
* **File liên quan:** [`app/workflows/prepare_workflow.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/workflows/prepare_workflow.py), [`ui/controllers/subtitle_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/subtitle_controller.py), [`test_release_contract.py`](file:///C:/NTKhoi/Downloads/CAPCAP/test_release_contract.py).

---

### 24. Không thể lấy đồng thời nguồn STT và OCR độc lập
* **Thời gian:** 21/08/2026
* **Mô tả hiện tượng:** Người dùng phải chọn hoặc Audio STT hoặc Video OCR. Không có cách xuất riêng hai file nguồn để chỉnh sửa/dịch bằng Antigravity IDE trước bước TTS.
* **Nguyên nhân gốc rễ (Root Cause):** `PrepareWorkflow` coi `ocr` là một nhánh thay thế hoàn toàn cho ASR, chỉ duy trì một artifact SRT gốc và pipeline tiếp tục dịch/TTS theo output mode hiện tại.
* **Cách xử lý (Fix Details):** Thêm source mode `stt_ocr`. Luồng này gọi STT audio qua Colab, lưu `projects/<project-id>/subtitle/original_stt.srt`, sau đó chạy OCR video và lưu `projects/<project-id>/subtitle/original_ocr.srt`. Hai file không tự ghép hoặc tự dịch; pipeline bắt buộc dừng sau bước nguồn. Người dùng nhập SRT hoàn chỉnh qua **Import Translated SRT** trước khi chạy TTS. Nếu OCR không nhận được chữ, SRT STT đã tạo vẫn được giữ lại và đường dẫn được báo trong lỗi.
* **File liên quan:** [`app/workflows/prepare_workflow.py`](file:///C:/NTKhoi/Downloads/CAPCAP/app/workflows/prepare_workflow.py), [`ui/controllers/pipeline_controller.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/controllers/pipeline_controller.py), [`ui/main_window.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/main_window.py), [`ui/utils/display_utils.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/utils/display_utils.py), [`test_release_contract.py`](file:///C:/NTKhoi/Downloads/CAPCAP/test_release_contract.py).

---

### 25. Processed Files có thể lỗi khi kiểm tra đường dẫn artifact
* **Thời gian:** 21/08/2026
* **Mô tả hiện tượng:** Khi mở **Processed Files**, giao diện có thể lỗi tại bước xác nhận file tồn tại, khiến các đường dẫn SRT mới không được hiển thị.
* **Nguyên nhân gốc rễ (Root Cause):** `ui/utils/display_utils.py` gọi `os.path.exists()` nhưng không import module `os` rõ ràng.
* **Cách xử lý (Fix Details):** Import `os` tường minh và hiển thị thêm hai artifact `Independent STT SRT` và `Independent OCR SRT` trong hộp thoại Processed Files.
* **File liên quan:** [`ui/utils/display_utils.py`](file:///C:/NTKhoi/Downloads/CAPCAP/ui/utils/display_utils.py), [`test_release_contract.py`](file:///C:/NTKhoi/Downloads/CAPCAP/test_release_contract.py).
