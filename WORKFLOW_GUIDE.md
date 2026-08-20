# CapCap — Hướng dẫn workflow và các lựa chọn chạy

Tài liệu này mô tả cách CapCap vận hành ở trạng thái hiện tại, bao gồm các lựa chọn tạo phụ đề, dịch, lồng tiếng và vị trí file đầu ra.

## 1. Nguyên tắc vận hành

- Chỉ dùng một notebook: `colab/CapCap_All_in_One_Colab.ipynb`.
- Whisper (STT), Demucs (tách giọng/nhạc nền) và TTS chạy qua Google Colab GPU. Desktop không được fallback các tác vụ này sang CPU.
- Máy Windows xử lý giao diện, Timeline, FFmpeg, preview/export và OCR quét chữ trực tiếp trên video.
- Mỗi phiên Colab có URL/token riêng. Mở notebook All-in-One, chạy toàn bộ cell, copy URL/token mới vào **Settings**, rồi bấm **Test Connection**.
- Với dự án output **Voice** hoặc **Both**, kết nối phải có các capability phù hợp: `transcribe`, `tts`; thêm `separate_vocals` nếu dùng Clean Voice. Nếu thiếu, app dừng trước khi chạy để tránh tình trạng đã làm phụ đề rồi lại phải đổi notebook.

## 2. Luồng chuẩn

```text
Chọn video
  -> Kết nối All-in-One Colab
  -> Extract audio bằng FFmpeg
  -> [tuỳ chọn] Demucs GPU tách vocals/background
  -> STT GPU hoặc OCR video
  -> Dịch/nhập SRT đã dịch
  -> TTS GPU
  -> Ghép giọng lồng tiếng + background
  -> Preview / Export
```

### Audio Fast và Clean Voice

| Option | Dùng cho STT | Background khi lồng tiếng | Nơi chạy phần nặng |
|---|---|---|---|
| `Fast` | Audio gốc đã extract | Audio gốc | Whisper/TTS: Colab |
| `Clean Voice` | Stem `vocals` từ Demucs | Stem `music`/`no_vocals` | Demucs, Whisper, TTS: Colab |

Ở Clean Voice, CapCap gửi audio đã extract tới Colab để Demucs tách hai stem. STT dùng giọng đã tách; khi preview/export, background được ghép lại với track TTS theo volume A1/A2. Vì vậy background không bị mất khỏi thành phẩm.

## 3. Chọn nguồn phụ đề

Mở **Settings → Subtitle source** để chọn một trong các mode sau.

| Option | Kết quả | Khi nên dùng |
|---|---|---|
| `Audio (Whisper) - Quality` | STT từ lời nói kèm timestamp | Video có hội thoại/giọng nói rõ; đây là lựa chọn ổn định cho Colab GPU. |
| `Audio (SenseVoice) - Speed` | STT audio nhanh | Tuỳ chọn tương thích; bản desktop bàn giao được khóa chạy AI qua Colab nên khi lưu kèm phiên Colab, app dùng remote Whisper. |
| `Video (OCR)` | SRT từ chữ nhìn thấy trong khung hình | Video đã có subtitle/text hardcoded. Chỉnh vùng Bottom/Top/Full frame và sampling rate nếu cần. |
| `Audio STT + Video OCR (two separate SRT files)` | Hai SRT nguồn độc lập | Khi cần tự đối chiếu, ghép hoặc dịch bằng Antigravity IDE trước TTS. |

### Mode STT + OCR độc lập

Đây là mode dành cho workflow ngoài app:

1. STT audio chạy qua All-in-One Colab và được lưu trước.
2. OCR quét chữ trên các frame video độc lập với STT.
3. CapCap **không tự ghép**, **không tự dịch**, **không gọi TTS** trong lượt chạy này.
4. Pipeline dừng và báo hai đường dẫn nguồn.

Hai file được lưu bền vững trong project:

```text
projects/<project-id>/subtitle/original_stt.srt
projects/<project-id>/subtitle/original_ocr.srt
```

Nếu OCR không nhận diện được chữ trong vùng đã chọn, `original_stt.srt` vẫn được lưu. Hãy đổi vùng OCR hoặc sampling rồi chạy lại để tạo file OCR.

## 4. Workflow dùng Antigravity IDE

1. Chọn mode **STT + OCR** và bấm **Generate** hoặc **Transcription**.
2. Mở **Processed Files** để copy đường dẫn hai file nguồn.
3. Mở hai SRT trong Antigravity IDE, đối chiếu/gộp/chỉnh timestamp và dịch theo yêu cầu.
4. Lưu bản hoàn chỉnh, ví dụ `translated_final.srt`.
5. Trong CapCap, bấm **Import Translated SRT** và chọn `translated_final.srt`.
6. Kiểm tra nội dung trên Timeline, chọn voice và bấm **Generate Voice / TTS**.
7. Preview, chỉnh volume A1 (background) và A2 (dub), sau đó **Export Video**.

CapCap giữ metadata speaker/timestamp khi có thể khớp các cue nhập vào. File SRT đã nhập trở thành `Translated SRT` đang hoạt động cho TTS và export.

## 5. Các cách chạy

### Generate (full pipeline)

- **Subtitle**: tạo transcript, dịch và tạo subtitle. Không chạy TTS.
- **Voice**: chuẩn bị transcript/dịch, tạo TTS; dùng audio lồng tiếng cho output.
- **Both**: chuẩn bị transcript/dịch, tạo TTS, giữ subtitle và audio lồng tiếng để export.
- Nếu source là **STT + OCR**, Generate luôn kết thúc ở hai SRT nguồn, kể cả khi output đang chọn Voice/Both. Đây là hành vi có chủ đích để chờ SRT hoàn chỉnh từ Antigravity.

### Chạy từng bước

| Bước | Điều kiện đầu vào | Đầu ra |
|---|---|---|
| `Transcription` | Video + Colab cho STT | Transcript/SRT nguồn. Với STT+OCR: hai SRT độc lập. |
| `Translate` | Transcript đã có | Translated SRT. Có thể thay bằng Import Translated SRT. |
| `Generate Voice / TTS` | Translated SRT hợp lệ + capability `tts` | `voice_vi` và audio mix khi có background. |
| `Export Video` | Subtitle/audio theo output mode | Video thành phẩm. |

## 6. Cấu trúc file của một project

```text
projects/<project-id>/
├── project.json                         # settings, step state, artifact paths
├── source/
│   └── extracted_audio.wav
├── audio/
│   └── separated/                       # chỉ có ở Clean Voice
│       ├── vocals.wav
│       └── no_vocals.wav / music.wav
├── subtitle/
│   ├── original.srt                     # nguồn thông thường
│   ├── original_stt.srt                 # chỉ ở mode STT + OCR
│   ├── original_ocr.srt                 # chỉ ở mode STT + OCR
│   └── subtitle.srt                     # phụ đề dịch do workflow nội bộ tạo
└── analysis/                            # cache segment/metadata của project
```

SRT được import từ Antigravity được ghi nhận như artifact `subtitle_translated_srt` và là file được dùng để tạo voice/export.

## 7. Kiểm tra và xử lý lỗi

- **Colab capability unavailable**: đang dùng sai notebook hoặc server chưa chạy đủ. Mở All-in-One, chạy lại toàn bộ cell, copy URL/token mới rồi Test Connection.
- **OCR không có kết quả**: thử `Bottom`, `Top` hoặc `Full frame`; tăng OCR sampling cho subtitle hiện rất ngắn.
- **Không tạo được voice**: cần import/dịch SRT hoàn chỉnh trước, đồng thời Colab phải có `tts`.
- **Clean Voice không có background**: kiểm tra bước Demucs hoàn tất và artifact `music`/`no_vocals` xuất hiện trong Processed Files.
- **App không dùng Colab cũ**: đây là đúng thiết kế; URL/token không được lưu lâu dài vì tunnel Colab hết hạn theo phiên.

## 8. Phạm vi đã được kiểm tra tự động

- Parse toàn bộ Python source và JSON/code của hai notebook Colab.
- Kiểm tra one-file packaging contract, QThread lifecycle và GUI startup.
- Kiểm tra route remote cho Whisper, TTS và tách vocals.
- Chạy nhánh STT+OCR bằng engine test: xác nhận tạo riêng hai SRT, không tự gọi dịch hay TTS.

Kiểm tra tự động không thay thế việc chạy một video thật với URL Colab của phiên người dùng; đó là bước xác nhận cuối cho model/voice và chất lượng dữ liệu đầu vào cụ thể.
