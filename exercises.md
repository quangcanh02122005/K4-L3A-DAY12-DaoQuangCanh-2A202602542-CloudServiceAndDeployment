# Phiếu Phản Ánh — K4 Level 3A, Ngày 12

> **Bài làm cá nhân.** Trả lời bằng lời của chính bạn, dựa trên những gì bạn
> quan sát được khi chạy code — không sao chép đáp án của người khác.
>
> Cách trả lời: thay dòng `> *Câu trả lời của bạn*` bằng câu trả lời.
> `grade.py` đếm số câu đã trả lời (15 điểm cho 10 câu).
>
> Họ và tên: Đào Quang Cảnh  Mã học viên: 2A202602542

---

### Câu 1 — Fail fast (CP1)

Trong `Settings`, `agent_api_key` không có giá trị mặc định nên app chết ngay
khi khởi động nếu thiếu biến môi trường. Hãy mô tả một tình huống cụ thể mà
việc "chết sớm" này cứu bạn, so với việc để mặc định `"changeme"`.

> Khi deploy lên Railway, nếu quên set biến `AGENT_API_KEY` trên dashboard, app sẽ crash ngay lập tức khi khởi động và Railway báo deployment failed. Tôi phát hiện ra ngay và sửa được. Nếu để mặc định `"changeme"`, app vẫn start thành công, health check pass, nhưng endpoint `/ask` sẽ chấp nhận bất kỳ ai dùng key `"changeme"` — người dùng bên ngoài có thể gọi API tốn tiền OpenRouter của mình mà mình không hay biết cho đến khi thấy hóa đơn cuối tháng.

---

### Câu 2 — Log cho máy đọc (CP1)

Chạy service và gọi `/ask` vài lần. Dán một dòng log JSON bạn thu được, rồi
nêu **hai** việc bạn làm được với dòng log đó mà `print("đã trả lời xong")`
không làm được.

> Dòng log thu được: `{"event": "ask_completed", "timestamp": "2026-09-29T03:48:27+00:00", "user_id": "sv-test", "tokens_in": 3, "tokens_out": 35, "cost_usd": 2.145e-05}`
>
> Hai việc làm được với log JSON mà `print` không làm được:
> 1. **Lọc và aggregate tự động**: dùng `jq` hoặc công cụ như Datadog/Grafana để tính tổng `cost_usd` theo `user_id` trong ngày, phát hiện user nào đang tốn tiền nhiều nhất — `print` chỉ là chuỗi thuần, không thể parse field.
> 2. **Cảnh báo có điều kiện**: hệ thống giám sát có thể đọc field `cost_usd`, nếu vượt ngưỡng thì tự động gửi alert Slack/email — `print` không có cấu trúc để trigger rule này.

---

### Câu 3 — Kích thước image (CP2)

Build cả hai phiên bản và ghi lại số đo thật:

```bash
docker build -f <Dockerfile-1-stage> -t agent:single .
docker build -t agent:multi .
docker images | grep agent
```

| Bản | Dung lượng |
|-----|-----------|
| 1 stage (bản đầu) | ~980 MB |
| Multi-stage | ~210 MB |

Giải thích: phần dung lượng chênh lệch đó là những gì?

> Phần chênh lệch ~770 MB là toàn bộ toolchain build không cần thiết khi chạy: compiler C/C++ (gcc, g++), header files của Python, các package build tools (`pip` wheel cache, setuptools nguồn), và image gốc `python:3.12` đầy đủ. Multi-stage build dùng `python:3.12-slim` làm runtime image và chỉ copy thư mục `.venv` đã được cài xong từ build stage sang — kết quả image chỉ chứa Python runtime + dependencies đã compile, không có gì thừa.

---

### Câu 4 — Thứ tự lệnh trong Dockerfile (CP2)

Sửa một ký tự trong `app/main.py` rồi build lại. Với Dockerfile của bạn, những
layer nào được dùng lại từ cache, layer nào phải chạy lại? Nếu bạn đặt
`COPY . .` lên trước `RUN pip install` thì kết quả khác thế nào?

> Với Dockerfile hiện tại (copy `requirements.txt` trước, `pip install`, rồi mới `COPY . .`): khi sửa `app/main.py`, các layer `FROM`, `RUN apt-get`, `COPY requirements.txt`, `RUN pip install` đều được dùng lại từ cache vì chúng không thay đổi. Chỉ layer `COPY . .` và các bước sau phải chạy lại — rất nhanh.
>
> Nếu đặt `COPY . .` lên trước `RUN pip install`: mỗi lần sửa bất kỳ file code nào (kể cả sửa 1 comment), Docker sẽ thấy context thay đổi, invalidate cache từ đó trở đi, và phải chạy lại toàn bộ `pip install` — mất 2–5 phút thay vì vài giây.

---

### Câu 5 — Vì sao không chạy bằng root (CP2)

Container mặc định chạy bằng root. Mô tả chuỗi sự kiện dẫn từ "một lỗ hổng
trong code Python của bạn" tới "kẻ tấn công có quyền cao trên máy host", và
lệnh `USER` cắt đứt chuỗi đó ở chỗ nào.

> Chuỗi sự kiện: (1) Kẻ tấn công gửi payload khai thác lỗ hổng trong code xử lý file upload của app → (2) Chạy được code tùy ý bên trong container với quyền root → (3) Vì container chạy root và có `--privileged` hoặc mount `/var/run/docker.sock`, kẻ tấn công escape ra ngoài container → (4) Có quyền root trên máy host, toàn quyền kiểm soát server.
>
> Lệnh `USER appuser` cắt đứt ở bước (2)→(3): kể cả khi kẻ tấn công chạy được code bên trong container, họ chỉ là user thường (`uid=1000`), không có quyền mount, không đọc được `/etc/shadow`, không thể ghi vào socket của Docker daemon — container escape bị chặn lại.

---

### Câu 6 — Cửa sổ trượt (CP3)

Rate limit của bạn dùng sliding window 60 giây. Nếu thay bằng cách đếm theo
phút đồng hồ (reset lúc giây 00), một người dùng có thể gửi tối đa bao nhiêu
request trong 2 giây liên tiếp khi hạn mức là 10/phút? Giải thích cách đạt được
con số đó.

> Tối đa **20 request** trong 2 giây. Cách đạt được: gửi 10 request lúc giây thứ 59 của phút N (ví dụ 10:00:59) — đây là phút N, counter đang ở 10, đạt giới hạn. Sang giây 10:01:00, đồng hồ reset, counter về 0, gửi thêm 10 request nữa trong vòng 1 giây — tổng 20 request trong khoảng 2 giây nhưng không vi phạm rule "10/phút" vì mỗi phút chỉ có đúng 10. Sliding window loại bỏ lỗ hổng này vì nó luôn nhìn vào 60 giây gần nhất, không có khái niệm "reset".

---

### Câu 7 — Rate limit và cost guard (CP3)

Hai cơ chế này khác nhau ở điểm nào? Cho một tình huống mà rate limit cho qua
nhưng cost guard phải chặn, và một tình huống ngược lại.

> **Khác nhau**: Rate limit kiểm soát **tần suất** (số request/thời gian), cost guard kiểm soát **ngân sách** (tổng tiền đã tiêu/tháng). Rate limit reset theo cửa sổ thời gian, cost guard tích lũy cộng dồn.
>
> - **Rate limit cho qua, cost guard chặn**: User gửi 1 request/giờ suốt cả tháng — tần suất rất thấp, không bao giờ chạm rate limit. Nhưng mỗi request hỏi một câu cực dài khiến LLM trả về 4000 token, sau 30 ngày tổng chi phí vượt $10 ngân sách → cost guard chặn.
> - **Cost guard cho qua, rate limit chặn**: Ngày đầu tháng, user mới chưa tiêu xu nào. Họ spam 50 request trong 1 phút → rate limit chặn ngay ở request thứ 11. Cost guard không chặn vì budget vẫn còn nhiều.

---

### Câu 8 — /health khác /ready (CP4)

Nếu gộp hai endpoint làm một và cho nó kiểm tra Redis, chuyện gì xảy ra với cụm
3 container khi Redis mất kết nối 30 giây? Trả lời theo đúng thứ tự sự kiện.

> Thứ tự sự kiện: (1) Redis mất kết nối → (2) Load balancer gọi `/health` (giờ kiểm tra Redis) → timeout hoặc nhận 503 → (3) Load balancer đánh dấu cả 3 container là unhealthy → (4) Orchestrator (Docker/Railway) thấy health check fail → bắt đầu restart cả 3 container đồng loạt → (5) Trong 30–60 giây restart, **không có container nào phục vụ request** → toàn bộ service down hoàn toàn → (6) Redis phục hồi sau 30 giây nhưng lúc này container đang trong quá trình restart, cần thêm thời gian để boot lại.
>
> Tách `/health` (chỉ kiểm tra process sống) và `/ready` (kiểm tra Redis) giải quyết: liveness probe dùng `/health` → container không bị restart khi Redis chết. Readiness probe dùng `/ready` → load balancer ngừng đẩy traffic vào nhưng container vẫn sống, sẵn sàng phục vụ ngay khi Redis phục hồi.

---

### Câu 9 — Stateless (CP4)

Chạy `docker compose up --scale agent=3` rồi gọi `/ask` nhiều lần với cùng một
`X-User-Id`. Quan sát `history_length` trong response. Nếu lịch sử được lưu
trong một dict Python thay vì Redis, bạn sẽ thấy con số đó thay đổi thế nào?

> Với Redis: `history_length` tăng đều 0, 1, 2, 3... qua mỗi request bất kể request đó rơi vào instance nào — vì tất cả 3 instance đều đọc/ghi vào cùng một Redis.
>
> Nếu lưu trong dict Python: `history_length` sẽ nhảy loạn, ví dụ: 0, 1, 0, 2, 1, 0... vì mỗi instance có dict riêng trong RAM. Request vào instance A thấy history 2 câu, request tiếp vào instance B thấy 0 câu (dict của B trống), request tiếp vào C cũng 0. Agent trở nên "mất trí nhớ" một cách ngẫu nhiên, không thể duy trì hội thoại liên tục.

---

### Câu 10 — Deploy thật (CP5)

Ghi lại **một** lỗi bạn gặp khi deploy lên cloud (build fail, health check
timeout, sai REDIS_URL, app không đọc `$PORT`...): thông báo lỗi là gì, bạn
tìm ra nguyên nhân bằng cách nào, và sửa ra sao?

> **Lỗi gặp phải**: Sau khi deploy lên Railway, endpoint `/ready` trả về `{"status":"not ready","redis":false}` mặc dù Redis service đang Online.
>
> **Nguyên nhân**: Biến `REDIS_URL` trong App service được set là `redis://localhost:6379/0` — URL này trỏ vào chính container của app, không phải Redis service trên Railway. Ngoài ra khi thử dùng cú pháp `${{Redis.REDIS_URL}}` của Railway, URL được inject có password sai (`<02122005>` thay vì password thật).
>
> **Cách tìm ra**: Chạy `railway variables --service <tên-service>` qua Railway CLI để xem giá trị thực tế của `REDIS_URL` đang được inject, đồng thời kiểm tra biến của Redis service để lấy password thật.
>
> **Cách sửa**: Set trực tiếp `REDIS_URL=redis://default:JIltpQSJpvLqwOoPnqQwpVCJJcRibxDY@redis.railway.internal:6379` với password lấy từ `REDISPASSWORD` của Redis service, sau đó redeploy. Kết quả `/ready` trả về `{"status":"ready","redis":true}`.
