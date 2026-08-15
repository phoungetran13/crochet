---
title: Crochet Chart Studio
emoji: 🧶
colorFrom: pink
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# Crochet Chart Generator

Web app nhận ảnh (chụp phác thảo hoặc ảnh sản phẩm) để sinh ra **chart móc len** (dạng ký hiệu mũi đan hoặc dạng pixel màu) kèm **công thức chữ** (written pattern), giới hạn trong 4 nhóm sản phẩm: **mũ, áo, váy, khăn**.

## Ý tưởng & giới hạn kỹ thuật

- Không có model AI nào "sinh chart móc len" trực tiếp từ ảnh. Pipeline thực tế:
  1. AI (CLIP) nhận diện **loại sản phẩm** từ ảnh.
  2. Người dùng tự chọn **kiểu con** (subtype) — vì đây là lựa chọn thiết kế, không phải thứ AI đoán được từ ảnh (vd: beanie vs bucket hat).
  3. Người dùng nhập **số đo cơ thể + gauge** (mật độ đan riêng của mình).
  4. Hệ thống dùng **công thức crochet toán học chuẩn** (không phải AI đoán) để tính số mũi/hàng và sinh chart + công thức.
- Sản phẩm nhiều mảnh (áo, váy bèo) được tách thành từng "piece" riêng kèm hướng dẫn ghép nối cuối cùng — giống cách pattern crochet thật được trình bày.

## Cấu trúc dự án

```
phungkhanhlinh/
├── README.md
├── Dockerfile                     # build image chung backend+frontend de deploy
├── .dockerignore
├── render.yaml                    # blueprint deploy 1-click len Render.com
├── backend/                       # FastAPI (Python)
│   ├── requirements.txt
│   ├── venv/                      # virtualenv (không commit)
│   └── app/
│       ├── main.py                # khởi tạo FastAPI app, CORS, include router
│       ├── routers/
│       │   └── pattern.py         # API endpoints: /api/classify, /api/generate
│       ├── schemas/
│       │   └── pattern.py         # Pydantic models (request/response)
│       └── services/
│           ├── ai_classifier.py   # Nhận diện loại sản phẩm bằng CLIP (model AI pretrain)
│           ├── shape_detector.py  # (dự phòng) nhận diện bằng xử lý hình học/contour
│           ├── formulas.py        # Công thức crochet chuẩn theo từng loại + subtype
│           └── color_chart.py     # Sinh pixel/color chart (k-means) từ ảnh
└── frontend/
    └── index.html                 # UI thuần HTML/CSS/JS (không cần Node/build)
```

## Các loại sản phẩm & subtype

| garment_type | subtype       | Mô tả                                              | Số mảnh (pieces) |
|--------------|---------------|-----------------------------------------------------|-------------------|
| `khan`       | —             | Khăn hình chữ nhật                                  | 1                 |
| `mu`         | `beanie`      | Mũ ôm đầu (crown tăng mũi tròn + thân thẳng)        | 1                 |
| `mu`         | `bucket`      | Mũ vành loe (crown + thân + vành loe ra)            | 1                 |
| `ao`         | `sweater`     | Áo chui đầu, may ghép mảnh                          | 4 (thân trước, thân sau, 2 tay) |
| `ao`         | `cardigan`    | Áo khoác cài nút, may ghép mảnh                     | 5 (thân trước trái/phải, thân sau, 2 tay) |
| `vay`        | `don`         | Váy đơn, móc vòng tròn từ eo xuống                  | 1                 |
| `vay`        | `beo`         | Váy nhiều tầng bèo, ghép chồng                      | N tầng (mặc định 3) |

## Yêu cầu hệ thống

- Python 3.9+
- ~1GB dung lượng trống (model CLIP ViT-B-32 ~350MB, cache tại `~/.cache/huggingface`)
- Trình duyệt bất kỳ (frontend không cần Node.js/npm — mở trực tiếp file HTML)

## Cài đặt & chạy backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Lần chạy đầu tiên sẽ tự tải model CLIP (~350MB, mất 1-2 phút tùy mạng). Các lần sau dùng cache nên nhanh hơn.

Kiểm tra server: mở `http://127.0.0.1:8000/api/health` → phải trả về `{"status":"ok"}`.

## Chạy frontend

Không cần build. Chỉ cần mở trực tiếp file bằng trình duyệt:

```bash
open frontend/index.html        # macOS
# hoặc double-click file trong Finder/Explorer
```

Trong giao diện, ô **API backend URL** mặc định là `http://127.0.0.1:8000` — đổi nếu backend chạy ở địa chỉ khác.

## API

### `POST /api/classify`
Nhận diện loại sản phẩm từ ảnh bằng CLIP zero-shot classification.

- Input: `multipart/form-data`, field `image` (file ảnh).
- Output:
```json
{
  "garment_type": "mu",
  "confidence": 0.53,
  "diagnostics": {
    "scores": {"mu": 0.53, "ao": 0.35, "vay": 0.04, "khan": 0.09},
    "model": "ViT-B-32 (openai, CLIP zero-shot)"
  }
}
```

### `POST /api/generate`
Sinh chart + công thức móc len.

- Input: `multipart/form-data`:
  - `garment_type`: `khan` | `mu` | `ao` | `vay`
  - `subtype`: tùy loại (xem bảng trên), optional cho `khan`
  - `chart_type`: `symbol` | `pixel`
  - `measurements`: chuỗi JSON (xem `Measurements` trong `backend/app/schemas/pattern.py`), bắt buộc có `gauge_stitches_per_10cm` và `gauge_rows_per_10cm`
  - `image`: file ảnh, **bắt buộc nếu `chart_type=pixel`** (dùng để lấy màu)
- Output: danh sách `pieces` (mỗi piece có `written_pattern`, `symbol_chart` hoặc `pixel_chart` riêng), `assembly_instructions` (nếu nhiều mảnh), `notes`.

## Deploy lên public URL

App gồm 1 Docker image duy nhất (backend FastAPI phục vụ luôn cả frontend tĩnh ở route `/`), nên chỉ cần **1 service** khi deploy — không cần tách frontend/backend ra 2 domain.

### Cách miễn phí: Hugging Face Spaces (khuyên dùng nếu không muốn tốn phí)

[Hugging Face Spaces](https://huggingface.co/spaces) có gói **CPU Basic hoàn toàn miễn phí, không cần thẻ thanh toán**, cấp sẵn 16GB RAM — dư sức chạy CLIP + PyTorch (nhu cầu thực tế chỉ ~2GB). Nhược điểm: Space có thể "ngủ" sau một thời gian không ai truy cập và cần khoảng 10-30s để khởi động lại ở lượt truy cập tiếp theo (bình thường với dịch vụ free).

Các bước:
1. Tạo tài khoản miễn phí tại [huggingface.co/join](https://huggingface.co/join) (chỉ cần email, không cần thẻ).
2. Vào [huggingface.co/new-space](https://huggingface.co/new-space) → đặt tên Space → chọn **SDK = Docker** → **Space hardware = CPU basic (free)** → Create Space.
3. HF cấp cho bạn 1 git remote riêng (dạng `https://huggingface.co/spaces/<username>/<space-name>`). Trong thư mục project, chạy:
   ```bash
   git init                     # neu chua init git
   git add .
   git commit -m "Deploy crochet chart studio"
   git remote add space https://huggingface.co/spaces/<username>/<space-name>
   git push space main
   ```
   (Lần đầu push sẽ được yêu cầu đăng nhập — dùng username HF + [access token](https://huggingface.co/settings/tokens) thay cho mật khẩu.)
4. HF tự động build theo `Dockerfile` ở gốc repo (đã cấu hình sẵn port 7860 đúng chuẩn HF Spaces) và đọc `sdk: docker` từ frontmatter trong `README.md`.
5. Chờ build xong (5-10 phút do tải PyTorch + model CLIP ~350MB lần đầu) — theo dõi tiến trình ngay trên trang Space.
6. Xong, bạn có link public dạng `https://huggingface.co/spaces/<username>/<space-name>` (hoặc link "app" riêng hiển thị ngay trên trang Space) để chia sẻ.

### Cách trả phí: Render.com (nếu sau này muốn uptime ổn định hơn, không bị "ngủ")

**Lưu ý về tài nguyên:** model CLIP + PyTorch cần tối thiểu **~2GB RAM**. Gói free của Render (512MB) **sẽ không đủ**, có thể bị crash/OOM — `render.yaml` đã đặt sẵn `plan: standard` (gói trả phí, đủ RAM).

1. Đẩy code repo này lên GitHub (`git init && git add . && git commit -m "init" && git push` lên 1 repo GitHub bạn tạo).
2. Vào [render.com](https://render.com) → tạo tài khoản (cần thẻ thanh toán vì dùng gói trả phí).
3. Chọn **New → Blueprint**, trỏ vào repo GitHub vừa đẩy lên. Render sẽ tự đọc `render.yaml` ở gốc repo và tạo service.
4. Chờ build xong rồi lấy URL dạng `https://crochet-chart-studio.onrender.com`.

### Cách deploy thủ công khác (không dùng Blueprint)

1. Trên Render: **New → Web Service** → chọn **Docker** làm environment, trỏ tới repo GitHub.
2. Đặt **Health Check Path** = `/api/health`.
3. Chọn plan có tối thiểu 2GB RAM (Standard trở lên).
4. Deploy — Render tự build theo `Dockerfile` ở gốc repo.

### Build & chạy thử bằng Docker ở máy khác (nếu máy đó có Docker)

```bash
docker build -t crochet-chart-studio .
docker run -p 8000:8000 crochet-chart-studio
# mở http://localhost:8000
```

*(Máy hiện tại chưa cài Docker nên chưa build thử image trực tiếp được — đã kiểm tra logic phục vụ frontend tĩnh + API cùng lúc bằng cách chạy uvicorn thường, hoạt động đúng. Nên build thử bằng lệnh trên trước khi deploy thật để chắc chắn.)*

## Gauge là gì?

Gauge (mật độ đan) là số mũi và số hàng bạn đan được trong 10x10cm với sợi và kim của riêng bạn. Mỗi người đan chặt/lỏng khác nhau nên trước khi đan sản phẩm thật, cần đan thử một miếng vuông ~12x12cm, đếm số mũi và số hàng trong 10cm — đó là 2 giá trị `gauge_stitches_per_10cm` và `gauge_rows_per_10cm`. Hệ thống dùng 2 số này để tính chính xác cần bao nhiêu mũi/hàng để ra đúng kích thước thật (cm), không chỉ đúng theo "số mũi" trừu tượng.

## Giới hạn hiện tại (MVP)

- Nhận diện subtype (beanie/bucket, sweater/cardigan, váy đơn/bèo) **do người dùng tự chọn**, AI chỉ nhận diện nhóm lớn (mũ/áo/váy/khăn) — vì đây là lựa chọn thiết kế không suy ra được từ ảnh.
- Công thức áo/váy là **bản đơn giản hóa (beta)**: chưa tính vòng nách cong chi tiết, độ co giãn theo từng loại sợi cụ thể — nên đan thử mẫu nhỏ trước khi đan sản phẩm thật.
- `shape_detector.py` (nhận diện bằng contour hình học) được giữ lại trong code nhưng **không còn được gọi** từ API — đã thay bằng `ai_classifier.py` (CLIP) vì xử lý tốt hơn với ảnh chụp thật, không chỉ ảnh nét vẽ tay.
- Pixel chart lấy màu từ chính ảnh gốc, không phân biệt màu theo từng mảnh khác nhau (vì ảnh input là 1 ảnh chung).

## Roadmap gợi ý

- Thêm prompt/label tiếng Việt hoặc fine-tune nhẹ CLIP nếu độ chính xác nhận diện chưa đạt yêu cầu thực tế.
- Tính công thức áo/váy chi tiết hơn (vòng nách cong, độ giãn theo sợi).
- Xuất chart ra PDF/PNG để in.
- Chuyển frontend sang React nếu cần giao diện phức tạp hơn (hiện tại dùng HTML thuần vì máy chưa cài Node.js).
