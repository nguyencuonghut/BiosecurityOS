# HƯỚNG DẪN SỬ DỤNG PHẦN MỀM BIOSECURITY OS 2026

**Phiên bản:** 1.0  
**Ngày:** 2026-03-20  
**Đối tượng:** Tất cả người dùng hệ thống — từ ban điều hành, chuyên gia ATSH, quản lý trại đến nhân viên thực địa.

---

## Mục lục

1. [Giới thiệu tổng quan](#1-giới-thiệu-tổng-quan)
2. [Mô hình vận hành và chu trình nghiệp vụ](#2-mô-hình-vận-hành-và-chu-trình-nghiệp-vụ)
3. [Đăng nhập và phân quyền](#3-đăng-nhập-và-phân-quyền)
4. [Dashboard điều hành](#4-dashboard-điều-hành)
5. [Quản lý trại (Farms)](#5-quản-lý-trại-farms)
6. [Scorecard & Đánh giá (Assessment)](#6-scorecard--đánh-giá-assessment)
7. [Killer Metrics](#7-killer-metrics)
8. [Trust Score — Độ tin cậy khai báo](#8-trust-score--độ-tin-cậy-khai-báo)
9. [Case rủi ro & Phân tích nguyên nhân gốc (RCA)](#9-case-rủi-ro--phân-tích-nguyên-nhân-gốc-rca)
10. [Task khắc phục (Corrective Tasks)](#10-task-khắc-phục-corrective-tasks)
11. [Scar Map — Bản đồ vết sẹo](#11-scar-map--bản-đồ-vết-sẹo)
12. [Bài học kinh nghiệm (Lesson Learned)](#12-bài-học-kinh-nghiệm-lesson-learned)
13. [Thông báo](#13-thông-báo)
14. [Báo cáo](#14-báo-cáo)
15. [Quản trị hệ thống (Admin)](#15-quản-trị-hệ-thống-admin)
16. [Logic vận hành liên module — Bản đồ tổng thể](#16-logic-vận-hành-liên-module--bản-đồ-tổng-thể)

---

## 1. Giới thiệu tổng quan

### 1.1. BIOSECURITY OS là gì?

BIOSECURITY OS 2026 là **hệ điều hành quản trị An toàn sinh học (ATSH)** cho doanh nghiệp chăn nuôi heo. Hệ thống không chỉ là phần mềm báo cáo checklist mà là một nền tảng vận hành sống, giúp doanh nghiệp:

- **Chuẩn hóa** đánh giá ATSH trên toàn bộ hệ thống trại.
- **Phát hiện** lỗ hổng trọng yếu nhanh chóng.
- **Xử lý** bằng quy trình giao việc, theo dõi, xác minh bằng chứng.
- **Ghi nhớ** tri thức dịch tễ nội bộ để không phụ thuộc vào cá nhân.
- **Truy vết** toàn bộ lịch sử rủi ro, sự cố và biện pháp đã áp dụng.

### 1.2. Nguyên tắc vận hành

| Nguyên tắc | Ý nghĩa |
|-------------|----------|
| **Expert-in-the-loop** | Chuyên gia dịch tễ/ATSH là người ra quyết định — hệ thống hỗ trợ chứ không thay thế. |
| **Evidence-first** | Không đóng task chỉ bằng khai báo. Phải có bằng chứng số xác minh được. |
| **Memory-first** | Mọi sự cố, near-miss, lỗ hổng đều được lưu trữ có cấu trúc thành tri thức di sản. |

### 1.3. Chu trình vận hành cốt lõi

```
Scan ──▶ Analyze ──▶ Prescribe ──▶ Execute ──▶ Verify ──▶ Learn
  │          │           │            │           │          │
  │          │           │            │           │          │
Thu thập   Chuyên gia  Chuyên gia   Trại thực   Chuyên    Lưu vết sẹo
điểm số,   phân tích   đề xuất     hiện theo    gia xác   + bài học
audit,     nguyên      hành động    task được    minh kết  thành tri
bằng       nhân gốc    khắc phục    giao         quả       thức di sản
chứng
```

Mỗi module trong hệ thống đảm nhận một hoặc nhiều giai đoạn trong chu trình này. Các module không hoạt động độc lập mà **liên kết chặt chẽ với nhau** theo dòng chảy nghiệp vụ.

---

## 2. Mô hình vận hành và chu trình nghiệp vụ

### 2.1. Sơ đồ luồng vận hành tổng thể

```
┌─────────────────────────────────────────────────────────────────────┐
│                         BIOSECURITY OS                              │
│                                                                     │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐      │
│  │ SCORECARD│───▶│ASSESSMENT│───▶│  TRUST   │    │ KILLER   │      │
│  │ TEMPLATE │    │ (Đánh giá)│   │  SCORE   │    │ METRICS  │      │
│  └──────────┘    └────┬─────┘    └──────────┘    └────┬─────┘      │
│                       │                                │            │
│                       │  điểm thấp / bất thường        │ vi phạm    │
│                       ▼                                ▼            │
│                  ┌─────────────────────────────────────────┐        │
│                  │           RISK CASE                      │        │
│                  │   (Hồ sơ rủi ro / sự cố)                │        │
│                  └────────────────┬────────────────────────┘        │
│                                  │                                  │
│                                  ▼                                  │
│                          ┌──────────────┐                           │
│                          │     RCA      │                           │
│                          │ Phân tích    │                           │
│                          │ nguyên nhân  │                           │
│                          └──────┬───────┘                           │
│                                 │                                   │
│                                 ▼                                   │
│                       ┌──────────────────┐                          │
│                       │ CORRECTIVE TASK  │                          │
│                       │ (Task khắc phục) │                          │
│                       └────────┬─────────┘                          │
│                                │                                    │
│                     ┌──────────┼──────────┐                         │
│                     ▼          ▼          ▼                         │
│               ┌──────────┐ ┌────────┐ ┌──────────┐                 │
│               │ EVIDENCE │ │ REVIEW │ │  CLOSE   │                 │
│               │ (Upload  │ │ (Xác   │ │  TASK    │                 │
│               │ bằng     │ │ minh)  │ │          │                 │
│               │ chứng)   │ │        │ │          │                 │
│               └──────────┘ └────────┘ └──────────┘                 │
│                                │                                    │
│                                ▼                                    │
│                  ┌──────────────────────────────┐                   │
│                  │     SCAR MAP + LESSON        │                   │
│                  │  (Vết sẹo + Bài học di sản)  │                   │
│                  └──────────────────────────────┘                   │
│                                                                     │
│                       ┌──────────────┐                              │
│                       │  DASHBOARD   │  ◀── Tổng hợp mọi dữ liệu  │
│                       └──────────────┘                              │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2. Giải thích luồng chính

**Luồng 1 — Đánh giá phát hiện rủi ro:**
1. Chuyên gia cấu hình **Scorecard template** (các tiêu chí đánh giá ATSH).
2. Trại thực hiện **tự đánh giá** hoặc thanh tra thực hiện **audit**.
3. Hệ thống tính điểm tự động, hiển thị **Spider Chart** và so sánh.
4. Nếu có cặp tự đánh giá + audit, hệ thống tính **Trust Score** (độ tin cậy khai báo).
5. Nếu phát hiện điểm thấp hoặc bất thường → chuyên gia tạo **Risk Case**.

**Luồng 2 — Killer Metric kích hoạt xử lý khẩn cấp:**
1. Khi phát hiện vi phạm nghiêm trọng (vd: đưa thực phẩm lạ vào trại), ghi nhận **Killer Metric Event**.
2. Hệ thống tự động **gửi cảnh báo** cho toàn bộ chuyên gia và quản lý.
3. Killer event **bắt buộc** phải có Risk Case mới được đóng.
4. Khi tạo case từ killer event, event tự chuyển sang trạng thái "đang xử lý".

**Luồng 3 — Xử lý case đến đóng:**
1. Chuyên gia nhận case trong **Case Queue**, phân loại và bắt đầu phân tích.
2. Chuyên gia lập **RCA** (phân tích nguyên nhân gốc) với các yếu tố nguyên nhân.
3. Từ kết quả RCA, chuyên gia tạo **Task khắc phục** cụ thể.
4. Trại thực hiện task, upload **bằng chứng** (ảnh/video/tài liệu).
5. Chuyên gia **review** bằng chứng: duyệt hoặc yêu cầu làm lại.
6. Task đóng khi có ít nhất 1 review duyệt thành công.
7. Case chuyển sang theo dõi (monitoring) rồi đóng.

**Luồng 4 — Ghi nhớ tri thức:**
1. Khi case có giá trị tri thức, chuyên gia tạo **Scar** (vết sẹo) trên bản đồ mặt bằng trại.
2. Scar ghi lại vị trí, mô tả, nguồn lây nghi ngờ, bằng chứng, mức độ tin cậy.
3. Chuyên gia chắt lọc thành **Lesson Learned** (bài học di sản) — có thể áp dụng cho các trại tương tự.
4. Khi gặp vấn đề mới, chuyên gia tra cứu scar và lesson tương tự đã xảy ra.

---

## 3. Đăng nhập và phân quyền

### 3.1. Đăng nhập

Truy cập hệ thống qua trình duyệt web. Nhập **tên đăng nhập** (username) và **mật khẩu**, nhấn **Đăng nhập**.

Hệ thống sử dụng JWT token — sau khi đăng nhập thành công, phiên làm việc được duy trì tự động. Khi hết phiên, hệ thống yêu cầu đăng nhập lại.

### 3.2. Các vai trò trong hệ thống

| Vai trò | Phạm vi | Mô tả |
|---------|---------|-------|
| **Quản trị hệ thống** (System Admin) | Toàn hệ thống | Quản lý người dùng, phân quyền, cấu hình hệ thống. |
| **Chuyên gia ATSH** (Biosec Expert) | Toàn hệ thống | Phân tích RCA, tạo task, review bằng chứng, xác nhận scar/lesson. Vai trò trung tâm. |
| **Quản lý vùng** (Region Manager) | Theo vùng | Theo dõi các trại trong phạm vi vùng phụ trách, điều phối xử lý. |
| **Quản lý trại** (Farm Manager) | Theo trại | Tự đánh giá, nhận task, upload bằng chứng, phân công nội bộ. |
| **Thanh tra** (Auditor) | Toàn hệ thống | Thực hiện audit độc lập, ghi nhận chấm điểm và bằng chứng. |
| **Người xem** (Viewer) | Theo trại | Chỉ xem dữ liệu được phân quyền, không thao tác. |

### 3.3. Phân quyền theo chức năng

Hệ thống kiểm soát quyền truy cập theo từng chức năng cụ thể. Các mục trên sidebar chỉ hiển thị khi người dùng có quyền tương ứng. Ví dụ:
- Chỉ người có quyền `CASE_CREATE` mới thấy menu **Cases**.
- Chỉ người có quyền `TASK_REVIEW` mới thấy nút **Duyệt/Từ chối** trong task.
- Chỉ người có quyền `USER_ADMIN` mới truy cập được **Admin**.

---

## 4. Dashboard điều hành

### 4.1. Mục đích

Dashboard là màn hình tổng quan toàn hệ thống, giúp ban điều hành và chuyên gia **quan sát trước, hành động sau**. Mọi dữ liệu từ các module khác được tổng hợp tại đây.

### 4.2. Các thành phần chính

| Vùng | Nội dung | Dữ liệu đến từ |
|------|----------|-----------------|
| **KPI Cards** (7 thẻ) | Tổng số trại, Điểm trung bình, Trại rủi ro cao, Case mở, Task quá hạn, Killer Metrics, Trại tin cậy thấp | Tổng hợp từ Farms, Assessments, Cases, Tasks, Killer Metrics, Trust Scores |
| **Bảng Trust Gap** | Xếp hạng các trại có độ lệch khai báo cao nhất | Trust Score module |
| **Biểu đồ Benchmark** | So sánh điểm ATSH giữa các trại | Assessments |
| **Biểu đồ xu hướng Killer** | Trend số lượng killer event theo thời gian | Killer Metrics |
| **Bảng Scar Hotspot** | Các trại/khu vực có nhiều vết sẹo nhất | Scar Map |

### 4.3. Hành động nhanh

Dashboard cung cấp 4 nút truy cập nhanh:
- **Quản lý Case** → mở Case Queue
- **Xem Scorecard** → mở danh sách Scorecard
- **Xem Bài học** → mở Lesson Library
- **Scar Map** → mở bản đồ vết sẹo

### 4.4. Click vào KPI card

Mỗi thẻ KPI đều có thể click để đi thẳng tới module liên quan:
- "Trại rủi ro cao" → danh sách trại
- "Case mở" → Case Queue
- "Task quá hạn" → danh sách task

---

## 5. Quản lý trại (Farms)

### 5.1. Danh sách trại

Màn hình hiển thị tất cả các trại với khả năng tìm kiếm và lọc theo:
- **Vùng** (region)
- **Loại trại** (nái, thịt, hỗn hợp)
- **Hình thức sở hữu** (công ty, thuê)

Các cột hiển thị: Mã trại, Tên trại, Loại, Sở hữu, Vùng, Rủi ro nền, Điểm gần nhất.

### 5.2. Hồ sơ chi tiết trại

Khi click vào trại, hiển thị trang chi tiết gồm:

**Phần header:** Tên trại, mã trại, vùng, loại trại, sở hữu, mức rủi ro nền, trạng thái hoạt động.

**5 thẻ thông tin:** Công suất, Địa chỉ, Tọa độ, Ngày mở, Trust Score (có mũi tên xu hướng ↑↓ và mức thay đổi).

**6 tab quản lý:**

| Tab | Nội dung | Liên kết logic |
|-----|----------|----------------|
| **Tổng quan** | Dashboard cấp trại: biểu đồ điểm ATSH theo thời gian, Trust Score trend | Tổng hợp từ Assessment + Trust Score |
| **Khu vực** | Danh sách các khu vực trong trại (cổng, chuồng, khu cách ly...), hỗ trợ cấu trúc phân cấp | Dùng làm vị trí cho Scar, Task |
| **Lộ trình** | Các tuyến di chuyển (luồng sạch/bẩn, luồng xe cám, luồng heo...) | Liên quan Assessment (chấm luồng) |
| **Điểm rủi ro** | Các điểm rủi ro ngoại sinh (nhà dân, chợ, lò mổ, bãi rác...) | Dùng cho RCA khi tìm nguồn lây |
| **Floorplan** | Sơ đồ mặt bằng trại (hỗ trợ nhiều phiên bản theo thời gian) | Nền cho Scar Map — gắn vết sẹo lên mặt bằng |
| **Bài học** | Các lesson learned liên quan đến trại này | Lọc từ Lesson Library |

### 5.3. Floorplan và mối liên hệ với Scar Map

Mỗi trại có thể lưu **nhiều phiên bản sơ đồ mặt bằng** (floorplan) theo thời gian. Phiên bản đang "active" là bản hiện tại được sử dụng. Khi trại thay đổi cấu trúc (xây thêm chuồng, thay đổi luồng), tạo phiên bản mới — các scar cũ vẫn gắn với phiên bản cũ, đảm bảo bối cảnh lịch sử chính xác.

Floorplan là **nền** để vẽ các marker trên Scar Map: điểm nổ dịch, điểm vi phạm, nguồn lây nghi ngờ, v.v.

---

## 6. Scorecard & Đánh giá (Assessment)

### 6.1. Scorecard Template — Bộ tiêu chí đánh giá

Chuyên gia ATSH cấu hình bộ scorecard bao gồm:

- **Các nhóm tiêu chí (Sections):**
  - Hạ tầng (Hardware)
  - Quy trình (Process)
  - Hành vi (Behavior)
  - Giám sát (Monitoring)
- Mỗi nhóm chứa các **tiêu chí cụ thể (Items)** — mỗi item có điểm tối đa, ngưỡng đạt, và cờ "killer" nếu là vi phạm nghiêm trọng.
- Scorecard có **trọng số** cho từng nhóm để tính điểm tổng.
- Hỗ trợ **nhiều mẫu** khác nhau cho từng loại trại (nái, thịt, công ty, thuê...).

**Liên kết:** Khi tạo assessment, hệ thống snapshot phiên bản scorecard template hiện tại. Nếu template được cập nhật sau đó, các assessment cũ không bị ảnh hưởng (BR-07).

### 6.2. Tạo đánh giá (Assessment)

**Ai tạo:**
- **Quản lý trại** tạo phiếu tự đánh giá (self-assessment).
- **Thanh tra/Chuyên gia** tạo phiếu audit (audit, spot audit, blind audit, re-audit).

**Quy trình:**

```
 ┌─────────┐     ┌───────────┐     ┌──────────┐     ┌────────┐
 │  DRAFT  │────▶│ SUBMITTED │────▶│ REVIEWED │────▶│ LOCKED │
 │ (Nháp)  │     │ (Đã nộp)  │     │ (Đã xét) │     │(Lưu kho)│
 └─────────┘     └───────────┘     └──────────┘     └────────┘
```

1. **Bước 1 — Tạo mới & chấm điểm:**
   - Chọn trại, loại đánh giá, mẫu scorecard.
   - Chấm từng tiêu chí: nhập điểm (0 đến max), ghi chú, đính kèm ảnh/video.
   - Thanh bên trái hiển thị danh sách các nhóm tiêu chí để di chuyển nhanh.
   - Thanh tiến trình ở header cho biết đã chấm bao nhiêu items.

2. **Bước 2 — Lưu nháp (Draft):**
   - Nhấn "Lưu nháp" để lưu tạm, có thể quay lại chỉnh sửa.

3. **Bước 3 — Nộp đánh giá (Submit):**
   - Nhấn "Nộp đánh giá" để hoàn tất.
   - Hệ thống **tự động tính** điểm tổng và điểm theo 4 trục (Hardware, Process, Behavior, Monitoring).
   - Hiển thị **Spider Chart** với kết quả.
   - Hiển thị bảng **các tiêu chí điểm thấp** (top 10 items cần cải thiện).

### 6.3. Spider Chart & Dashboard điểm số

Sau khi nộp đánh giá, hệ thống hiển thị:
- **Spider Chart** (biểu đồ radar) theo 4 trục — nhìn trực quan trại mạnh/yếu ở đâu.
- Nếu có nhiều đánh giá trước đó, có thể **so sánh overlay** để thấy xu hướng.
- **Trust Score bar** hiển thị nếu có cặp tự đánh giá + audit.

### 6.4. Mối liên hệ với các module khác

| Sự kiện sau Assessment | Hành động liên kết |
|------------------------|---------------------|
| Điểm thấp được phát hiện | Chuyên gia có thể tạo **Risk Case** (loại: `low_score`) gắn với assessment |
| Có tiêu chí killer bị vi phạm | Kết hợp với module **Killer Metrics** |
| Có cặp self + audit | Hệ thống tính **Trust Score** |
| Spider Chart cho thấy xu hướng xấu | Dữ liệu chảy về **Dashboard** để cảnh báo |

---

## 7. Killer Metrics

### 7.1. Killer Metric là gì?

Killer Metrics là các vi phạm đặc biệt nghiêm trọng mà doanh nghiệp xác định là **không thể chấp nhận** — dù chỉ xảy ra một lần cũng cần hành động ngay. Ví dụ:
- Vi phạm vạch đỏ phân luồng.
- Đưa thực phẩm lạ vào trại.
- Xử lý heo chết sai quy trình.
- Người lạ vào khu nuôi không qua sát trùng.

### 7.2. Quản lý định nghĩa Killer Metric

Chuyên gia ATSH định nghĩa các loại killer metric qua màn hình **Killer Metric Definitions** (`/killer-metrics/definitions`):
- Mã, tên, mô tả.
- Mức độ nghiêm trọng mặc định.
- Hướng dẫn xử lý.

### 7.3. Ghi nhận sự kiện Killer

Khi phát hiện vi phạm killer, người dùng ghi nhận **Killer Metric Event** qua màn hình `/killer-metrics/events`:
- Chọn loại killer metric đã định nghĩa.
- Chọn trại, mô tả chi tiết, đính kèm bằng chứng.

### 7.4. Hành vi tự động khi xảy ra Killer Event

Đây là điểm liên kết quan trọng nhất của module này:

```
                    Killer Event
                        │
                        ▼
        ┌───────────────────────────────────┐
        │ TỰ ĐỘNG: Gửi cảnh báo           │
        │ → Tất cả người dùng có quyền     │
        │   KILLER_EVENT_READ nhận thông    │
        │   báo trong hệ thống             │
        └───────────────┬───────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │ BẮT BUỘC: Phải tạo Risk Case    │
        │ → Killer event KHÔNG THỂ đóng    │
        │   nếu chưa có case liên kết      │
        └───────────────┬───────────────────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │ TỰ ĐỘNG: Khi case được tạo từ    │
        │ killer event → event tự chuyển   │
        │ trạng thái: open → under_review  │
        └───────────────────────────────────┘
```

### 7.5. Trạng thái Killer Event

```
open ──▶ under_review ──▶ contained ──▶ closed
                                          ▲
                              Chỉ đóng khi đã có
                              Risk Case liên kết
```

- **open:** Vừa ghi nhận.
- **under_review:** Chuyên gia đang xem xét (tự chuyển khi có case).
- **contained:** Đã kiểm soát tình huống.
- **closed:** Đã xử lý xong (bắt buộc có case).

---

## 8. Trust Score — Độ tin cậy khai báo

### 8.1. Mục đích

Trust Score đo **mức độ trung thực** giữa điểm trại tự khai và điểm audit độc lập. Nếu trại khai điểm cao hơn thực tế (khai khống), Trust Score sẽ thấp → cần kiểm tra kỹ hơn.

### 8.2. Cách tính

Trust Score được tính tự động khi hệ thống có **cặp đánh giá**: 1 phiếu tự đánh giá + 1 phiếu audit của cùng một trại.

```
Gap        = Điểm tự đánh giá − Điểm audit
Hệ số phạt = 1.5 nếu Gap > 0 (khai khống)
             1.0 nếu Gap ≤ 0 (khai thấp hơn → không phạt nặng)

Trust Score = max(0, 100 − |Gap| × Hệ số phạt × Severity Factor)
```

| Ví dụ | Tự đánh giá | Audit | Gap | Trust Score |
|-------|-------------|-------|-----|-------------|
| Khai chính xác | 80 | 80 | 0 | **100** |
| Khai thấp hơn | 60 | 95 | −35 | **65** |
| Khai khống ít | 92 | 90 | +2 | **97** |
| Khai khống nhiều | 95 | 60 | +35 | **47.5** |

### 8.3. Ý nghĩa vận hành

- Trust Score hiển thị trong **hồ sơ trại** (thẻ Trust Score ở header).
- Xu hướng Trust Score hiển thị trong **dashboard cấp trại** (biểu đồ trend).
- Bảng **Trust Gap** trên Dashboard điều hành xếp hạng các trại lệch nhiều nhất.
- **Trại có Trust Score thấp** sẽ được ưu tiên kiểm tra độc lập (BR-06).

### 8.4. Liên kết với Assessment

Trust Score chỉ được tính khi có đủ 2 phiếu (self + audit). Hệ thống tự động:
1. Xác định cặp assessment phù hợp.
2. Tính gap theo công thức.
3. Tạo/cập nhật bản ghi Trust Score Snapshot.
4. Hiển thị kết quả tại dashboard và hồ sơ trại.

---

## 9. Case rủi ro & Phân tích nguyên nhân gốc (RCA)

### 9.1. Risk Case là gì?

Risk Case là **hồ sơ quản lý rủi ro/sự cố** — một "case" để chuyên gia theo dõi, phân tích và xử lý từ đầu đến cuối. Một case có thể được tạo từ nhiều nguồn:

| Nguồn | Loại case | Hành vi liên kết |
|-------|-----------|-------------------|
| Assessment có điểm thấp | `low_score` | Gắn `source_assessment_id` |
| Vi phạm killer metric | `killer_event` | Gắn `source_killer_event_id`, killer event tự chuyển sang `under_review` |
| Scar/sự kiện hiện trường | `scar` | Gắn `source_scar_id` |
| Chuyên gia tự mở | `manual` | Không gắn nguồn cụ thể |

### 9.2. Case Queue — Hàng đợi xử lý

Chuyên gia ATSH làm việc chính trên màn hình **Case Queue**:

- **2 chế độ xem:**
  - **Queue** (hàng đợi): Chỉ hiển thị case chờ xử lý, sắp xếp theo ưu tiên và SLA.
  - **Tất cả**: Hiển thị toàn bộ case, có bộ lọc đầy đủ.

- **Bộ lọc:** Trại, Mức ưu tiên (P0–P3), Trạng thái, Loại case.

- **Quick Preview:** Click vào hàng → hiển thị preview bên phải gồm tiêu đề, mô tả, ưu tiên, hạn SLA. Nhấn "Mở chi tiết" để vào case.

### 9.3. Chi tiết Case

Trang chi tiết case gồm:

**Thanh trạng thái (Status Pipeline):**
```
open ──▶ triage ──▶ in_analysis ──▶ actioning ──▶ monitoring ──▶ closed
                                                                   │
                                          Có thể cancel từ hầu hết ──▶ cancelled
```

Mỗi trạng thái có nút chuyển tiếp tương ứng (chỉ hiển thị khi có quyền).

**3 Tab:**

| Tab | Nội dung | Liên kết |
|-----|----------|----------|
| **Tổng quan** | Thông tin case (trại, loại, ưu tiên, nghiêm trọng, SLA), mô tả, chuyên gia phụ trách, nguồn case (link đến assessment/killer event), tóm tắt RCA | Nguồn case → Assessment hoặc Killer Event |
| **RCA Workspace** | Danh sách phân tích nguyên nhân gốc, mỗi RCA gồm: phương pháp, 6 nhóm nguyên nhân, các yếu tố chi tiết, trạng thái phê duyệt | Kết quả RCA → cơ sở tạo Task |
| **Timeline** | Dòng thời gian tất cả sự kiện liên quan: mở case, phân công, tạo RCA, duyệt RCA, liên kết killer event | Tổng hợp audit log |

### 9.4. RCA — Phân tích nguyên nhân gốc

RCA là bước **phân tích** đặc biệt quan trọng — đây là nơi chuyên gia xác định **tại sao** sự cố xảy ra, không chỉ **điều gì** xảy ra.

**Cấu trúc 1 bản ghi RCA:**
- **Phương pháp:** 5 Why, Fishbone/Ishikawa, CAPA, hoặc checklist.
- **Mô tả vấn đề** (problem statement).
- **6 nhóm nguyên nhân:**
  - Nguyên nhân trực tiếp
  - Nguyên nhân hệ thống
  - Nguyên nhân hành vi
  - Nguyên nhân hạ tầng
  - Nguyên nhân giám sát
  - Yếu tố ngoại sinh
- **Phạm vi ảnh hưởng** (impact scope).
- **Độ tin cậy** kết luận.

**Các yếu tố (Factors):**
Mỗi RCA có thể có nhiều yếu tố chi tiết, phân theo nhóm: Con người (People), Quy trình (Process), Địa điểm (Place), Thiết bị (Equipment), Môi trường (Environment), Giám sát (Monitoring), Ngoại sinh (External). Mỗi yếu tố có thể đánh dấu **là nguyên nhân chính** (primary) bằng biểu tượng sao.

**Phê duyệt RCA:** Sau khi lập xong, RCA cần được phê duyệt. RCA đã duyệt **không thể sửa đổi** nữa — đảm bảo tính toàn vẹn kết luận.

### 9.5. Từ RCA đến Task

Đây là điểm nối quan trọng nhất trong luồng vận hành:

```
    RCA (kết luận nguyên nhân)
         │
         ▼
    Chuyên gia quyết định hành động khắc phục
         │
         ▼
    Tạo CORRECTIVE TASK
    ├── Gắn case_id (bắt buộc)
    ├── Gắn source_rca_id (tham chiếu nguyên nhân)
    ├── Mô tả chi tiết
    ├── Tiêu chí hoàn thành
    ├── Yêu cầu bằng chứng
    └── Hạn hoàn thành + ưu tiên
```

Một case có thể sinh ra **nhiều task** khắc phục. Ví dụ: 1 case về vi phạm luồng di chuyển có thể tạo:
- Task 1: Sửa lại biển chỉ dẫn (capex)
- Task 2: Đào tạo nhân viên về luồng mới (training)
- Task 3: Lắp camera giám sát (corrective)

---

## 10. Task khắc phục (Corrective Tasks)

### 10.1. Danh sách Task

Màn hình `/tasks` hiển thị tất cả task khắc phục với:
- **Bộ lọc:** Trại, Mức ưu tiên (P0–P3), Trạng thái, Loại task.
- **Loại task:** corrective (sửa lỗi), preventive (phòng ngừa), inspection (kiểm tra), training (đào tạo), capex (đầu tư hạ tầng).
- **Quick Preview:** Click hàng để xem tóm tắt bên phải, nhấn "Mở chi tiết" để vào.

### 10.2. Vòng đời của Task

```
  ┌──────┐    ┌──────────┐    ┌─────────────┐    ┌────────────────┐    ┌────────┐
  │ OPEN │───▶│ ACCEPTED │───▶│ IN_PROGRESS │───▶│ PENDING_REVIEW │───▶│ CLOSED │
  └──────┘    └──────────┘    └──────┬──────┘    └───────┬────────┘    └────────┘
                                     ▲                   │
                                     │            ┌──────▼───────┐
                                     └────────────│ NEEDS_REWORK │
                                                  └──────────────┘
                              (Có thể cancel từ hầu hết trạng thái)
```

### 10.3. Quy trình xử lý chi tiết

**Bước 1 — Mở task (Open):**
- Chuyên gia tạo task từ case, gắn thông tin: tiêu đề, mô tả, loại, ưu tiên, hạn, tiêu chí hoàn thành, yêu cầu bằng chứng.

**Bước 2 — Nhận việc (Accepted):**
- Người được giao nhấn chấp nhận task.

**Bước 3 — Thực hiện (In Progress):**
- Người thực hiện làm việc và upload **bằng chứng**: ảnh, video, tài liệu, biểu mẫu.
- Bằng chứng hiển thị trong tab "Bằng chứng" của task.
- **Bắt buộc** phải có ít nhất 1 file bằng chứng trước khi nộp review.

**Bước 4 — Nộp review (Pending Review):**
- Nhấn "Submit for Review" để chuyển task cho chuyên gia xem xét.

**Bước 5 — Review:**
Chuyên gia xem bằng chứng và quyết định:

| Kết quả | Hành vi |
|---------|---------|
| **Duyệt (Approve)** | Task sẵn sàng đóng |
| **Từ chối / Cần rework** | Task chuyển về `needs_rework`, chuyên gia ghi lý do + hạn nộp lại. Người thực hiện sửa và nộp lại. |

> **Quy tắc quan trọng (BR-04):** Task chỉ được đóng khi có **ít nhất 1 review duyệt thành công**. Không thể đóng task thiếu bằng chứng hoặc thiếu review.

**Bước 6 — Đóng task (Closed):**
- Sau khi có review duyệt, task được đóng.

### 10.4. Tab trong trang chi tiết Task

| Tab | Nội dung |
|-----|----------|
| **Tổng quan** | Mô tả, tiêu chí hoàn thành, yêu cầu bằng chứng, danh sách người được giao (owner/support), tóm tắt review gần nhất |
| **Bằng chứng** | Upload file + gallery hiển thị các file đã upload. Có thể xóa trước khi task đóng |
| **Reviews** | Lịch sử tất cả các lần review: kết quả, người review, ngày, ghi chú, hạn rework |
| **Bình luận** | Trao đổi giữa người thực hiện và reviewer về task |

### 10.5. Mối liên hệ với Case

- Mỗi task **bắt buộc** gắn với 1 Risk Case (`case_id`).
- Khi **tất cả task** của case đều đóng → case có thể chuyển sang `monitoring` rồi `closed`.
- Case ở trạng thái `actioning` nghĩa là đang có task đang thực hiện.

---

## 11. Scar Map — Bản đồ vết sẹo

### 11.1. Scar là gì?

"Scar" (vết sẹo) là **điểm tri thức dịch tễ** được gắn vào vị trí cụ thể trên sơ đồ mặt bằng trại. Mỗi scar ghi lại:
- **Vị trí:** Tọa độ % trên floorplan.
- **Loại sự kiện:** Outbreak (ổ dịch), Hotspot (điểm nóng), Repeated breach (vi phạm lặp lại), Near miss (suýt xảy ra), Structural flaw (lỗi cấu trúc).
- **Mô tả**, nguồn lây nghi ngờ.
- **Độ tin cậy:** suspected → probable → confirmed.
- **Bằng chứng** và case/task liên quan.
- **Số lần tái diễn** (recurrence count).

### 11.2. Giao diện Scar Map

Màn hình Scar Map gồm:

**Phần trên — Floorplan Canvas:**
- Hiển thị sơ đồ mặt bằng trại (phiên bản active).
- Các marker khu vực (cổng, chuồng, kho...) được đánh dấu bằng icon trên bản đồ.
- Các **scar dot** (chấm tròn màu) hiển thị tại vị trí xảy ra sự kiện. Màu biểu thị loại scar.
- Hover lên scar → hiển thị tooltip (tiêu đề, loại, độ tin cậy).
- Click scar → mở Scar Detail Drawer bên phải.

**Phần dưới — Bảng danh sách scar:**
- Các cột: Loại, Tiêu đề, Độ tin cậy, Ngày, Số lần lặp.
- Click hàng → mở drawer chi tiết.

**Bộ lọc:**
- Trại (bắt buộc chọn).
- Loại scar.
- Độ tin cậy.
- Khoảng ngày.

### 11.3. Tạo Scar mới

Có 2 cách tạo scar:
1. **Nhấn "Tạo Scar"** → mở ScarFormDialog → chọn vị trí trên minimap bằng cách click.
2. **Click trực tiếp lên floorplan** → mở dialog đã điền sẵn tọa độ.

### 11.4. Phát hiện lặp lại tự động

Khi tạo scar mới ở cùng **khu vực + cùng loại** với scar đã tồn tại, hệ thống tự động:
- Đánh dấu `recurrence_flag = true`.
- Tăng `recurrence_count` (số lần tái diễn).

Điều này giúp chuyên gia nhận biết **điểm nóng tái diễn** — vấn đề cần hành động mạnh hơn.

### 11.5. Liên kết Scar với các module khác (ScarLink)

Scar có thể được **liên kết** với nhiều thực thể khác qua cơ chế polymorphic:
- Gắn với **Risk Case** → biết case nào đã xử lý vấn đề tại vị trí này.
- Gắn với **Assessment** → biết đánh giá nào phát hiện vấn đề.
- Gắn với **Killer Event** → biết killer nào xảy ra tại đây.
- Gắn với **Lesson Learned** → bài học nào được rút ra.

Nhờ liên kết này, khi chuyên gia nhìn vào 1 scar trên bản đồ, họ có thể **truy vết toàn bộ** lịch sử: phát hiện khi nào, xử lý qua case nào, task nào, bài học gì.

---

## 12. Bài học kinh nghiệm (Lesson Learned)

### 12.1. Mục đích

Lesson Learned là **tri thức di sản** được chắt lọc từ thực tế vận hành. Không phải mọi ghi chú hiện trường đều trở thành lesson — chỉ những bài học **đã được chuyên gia xác nhận** mới có giá trị (BR-05).

### 12.2. Cấu trúc 1 Lesson

- **Mã lesson** (tự sinh).
- **Tiêu đề** và mô tả vấn đề.
- **Bối cảnh:** Loại trại, mùa vụ, hình thức sở hữu.
- **Nguyên nhân gốc.**
- **Biện pháp đã áp dụng** và kết quả.
- **Bài học khuyến nghị** cho các trại tương tự.
- **Độ tin cậy** và **trạng thái**.

### 12.3. Trạng thái Lesson

```
draft ──▶ confirmed (validated) ──▶ archived / obsolete
```

- **draft:** Bản nháp, chưa được xác nhận.
- **confirmed (validated):** Đã được chuyên gia xác nhận — đây mới là tri thức chính thức.
- **archived/obsolete:** Hết giá trị hoặc đã lỗi thời.

### 12.4. Thư viện Bài học (Lesson Library)

Màn hình `/lessons` cung cấp 2 chế độ:

**Tab 1 — Thư viện:**
- Duyệt toàn bộ lessons theo bộ lọc: Loại trại, Loại vấn đề, Độ tin cậy, Trạng thái, Tag.
- Click hàng → mở Lesson Detail Drawer.

**Tab 2 — Tìm kiếm tương tự:**
- Nhập tiêu chí: Loại trại, Hình thức sở hữu, Loại vấn đề, Mùa vụ.
- Nhấn "Tìm kiếm" → hệ thống trả về các lessons phù hợp.
- Đây là **tra cứu có cấu trúc**, không phải AI — giúp chuyên gia tìm bài học từ các trại tương tự.

### 12.5. Liên kết Lesson với các module khác (LessonReference)

Tương tự ScarLink, Lesson có thể tham chiếu đến:
- **Risk Case** lý do tạo ra lesson.
- **Task khắc phục** đã áp dụng.
- **Scar** liên quan.
- **Assessment** liên quan.

Nhờ đó, khi đọc 1 lesson, người dùng có thể **truy vết ngược** đến toàn bộ bối cảnh: case nào, scar ở đâu, task gì đã làm, kết quả ra sao.

---

## 13. Thông báo

### 13.1. Cách hoạt động

Hệ thống gửi thông báo in-app cho người dùng liên quan khi có sự kiện quan trọng:
- Killer metric event mới.
- Task được giao.
- Task quá hạn.
- Review hoàn tất.
- Case cần xử lý.

### 13.2. Giao diện

- **Chuông thông báo** ở góc phải topbar — hiển thị badge đếm số thông báo chưa đọc, tự cập nhật.
- Click chuông → popover hiển thị danh sách thông báo gần nhất.
- Màn hình `/notifications` hiển thị toàn bộ lịch sử thông báo.

---

## 14. Báo cáo

Màn hình `/reports` cho phép xuất các báo cáo vận hành:
- Báo cáo điểm ATSH theo tháng.
- Báo cáo case phát sinh.
- Báo cáo task quá hạn.
- Báo cáo killer metrics.
- Báo cáo trust gap.
- Báo cáo lesson learned.

Hỗ trợ xuất dạng PDF, Excel/CSV.

---

## 15. Quản trị hệ thống (Admin)

### 15.1. Quản lý người dùng

Màn hình `/admin/users` cho phép:
- Tạo tài khoản mới.
- Gán vai trò (role) cho từng người dùng.
- Quản lý trạng thái tài khoản (kích hoạt/vô hiệu hóa).

### 15.2. Nhật ký kiểm toán (Audit Log)

Màn hình `/admin/audit-logs` ghi nhận toàn bộ hành động trong hệ thống:
- Ai đã tạo/sửa/xóa dữ liệu gì, lúc nào.
- Lịch sử chuyển trạng thái case, task.
- Upload/xóa bằng chứng.
- Thay đổi phân quyền.

Audit log giúp **truy vết** khi cần kiểm tra lịch sử thao tác.

---

## 16. Logic vận hành liên module — Bản đồ tổng thể

### 16.1. Bảng tổng hợp luồng dữ liệu giữa các module

| Từ module | → Đến module | Kiểu liên kết | Mô tả |
|-----------|--------------|----------------|--------|
| **Scorecard Template** | → Assessment | Snapshot tại thời điểm tạo | Assessment sử dụng bản scorecard cố định, không bị ảnh hưởng khi template thay đổi sau |
| **Assessment** (điểm thấp) | → Risk Case | `source_assessment_id` | Chuyên gia tạo case loại `low_score` gắn với phiếu đánh giá |
| **Assessment** (self + audit) | → Trust Score | Tự động tính | Hệ thống tự tính Trust Score khi có cặp self + audit |
| **Assessment** | → Dashboard | Tổng hợp | Spider Chart, biểu đồ benchmark, KPI điểm trung bình |
| **Killer Event** | → Thông báo | Tự động | Tạo cảnh báo cho toàn bộ người có quyền |
| **Killer Event** | → Risk Case | `source_killer_event_id` | Bắt buộc phải tạo case; event tự chuyển `under_review` |
| **Scar** | → Risk Case | `source_scar_id` | Có thể tạo case từ scar |
| **Risk Case** | → RCA | 1:N | Mỗi case có thể có nhiều bản phân tích RCA |
| **RCA** | → Task | `source_rca_id` | Task khắc phục gắn với kết luận RCA cụ thể |
| **Risk Case** | → Task | `case_id` (bắt buộc) | Mọi task đều thuộc về 1 case |
| **Task** | → Evidence | Upload file | Nhân viên upload bằng chứng khi thực hiện task |
| **Task** | → Review | 1:N | Nhiều lần review; duyệt/rework/từ chối |
| **Scar** | → ScarLink | Polymorphic | Liên kết sang Case, Assessment, Killer Event, Lesson |
| **Lesson** | → LessonReference | Polymorphic | Tham chiếu sang Case, Task, Scar, Assessment |
| **Trust Score** | → Dashboard | Tổng hợp | Bảng Trust Gap, KPI trại tin cậy thấp |
| **Killer Event** | → Dashboard | Tổng hợp | Biểu đồ trend Killer, KPI Killer Metrics |
| **Scar** | → Dashboard | Tổng hợp | Bảng Scar Hotspot |
| **Farm** | → Floorplan | 1:N (versioned) | Nhiều phiên bản sơ đồ mặt bằng theo thời gian |
| **Floorplan** | → Scar Map | Nền hiển thị | Scar dot được vẽ lên floorplan image |

### 16.2. Chuỗi vận hành điển hình — Ví dụ thực tế

#### Kịch bản: Phát hiện heo chết xử lý sai quy trình

```
Bước 1: Thanh tra phát hiện → Ghi nhận Killer Metric Event
         (loại: "Xử lý heo chết sai quy trình")
              │
              ▼
Bước 2: Hệ thống TỰ ĐỘNG gửi thông báo cho chuyên gia ATSH
              │
              ▼
Bước 3: Chuyên gia mở Case Queue → thấy cảnh báo killer
         → Tạo Risk Case (loại: killer_event, ưu tiên: P0)
              │
              ▼
         Killer event TỰ ĐỘNG chuyển: open → under_review
              │
              ▼
Bước 4: Chuyên gia vào Case Detail → tab RCA Workspace
         → Lập RCA (phương pháp: 5 Why)
         → Kết luận: nhân viên chưa được đào tạo quy trình xử lý
                      + thiếu dụng cụ di chuyển xác tại khu nuôi
              │
              ▼
Bước 5: Từ kết quả RCA → Tạo 2 Task:
         Task 1: Đào tạo nhân viên quy trình xử lý xác (training, P0, hạn 3 ngày)
         Task 2: Mua dụng cụ di chuyển xác chuyên dụng (capex, P1, hạn 2 tuần)
              │
              ▼
Bước 6: Quản lý trại nhận task → phân công nhân viên
         → Nhân viên thực hiện → Chụp ảnh buổi đào tạo (Task 1)
         → Upload ảnh hóa đơn + ảnh dụng cụ (Task 2)
              │
              ▼
Bước 7: Chuyên gia review bằng chứng:
         ✅ Task 1: Duyệt (ảnh buổi đào tạo đầy đủ)
         ❌ Task 2: Cần rework (ảnh không rõ, yêu cầu chụp lại)
              │
              ▼
Bước 8: Nhân viên chụp lại ảnh → nộp lại
         → Chuyên gia duyệt
         → Cả 2 task CLOSED
              │
              ▼
Bước 9: Case chuyển: actioning → monitoring → closed
         Killer event: contained → closed
              │
              ▼
Bước 10: Chuyên gia tạo SCAR tại vị trí khu chứa xác trên floorplan:
          - Loại: repeated_breach
          - Mô tả: "Xử lý heo chết sai quy trình, nguyên nhân: chưa đào tạo"
          - Liên kết: Case + Killer Event
              │
              ▼
Bước 11: Chuyên gia chắt lọc LESSON LEARNED:
          - "Cần đào tạo lại quy trình xử lý heo chết mỗi 3 tháng
             cho trại thịt có nhân viên mới"
          - Tham chiếu: Case + Task + Scar
          - Trạng thái: confirmed
              │
              ▼
Bước 12: Lần sau gặp case tương tự ở trại khác
          → Chuyên gia vào Lesson Library → tab "Tìm kiếm tương tự"
          → Tìm thấy lesson → áp dụng ngay
```

### 16.3. Ba nguồn kích hoạt Case

```
      Assessment                Killer Event               Scar / Manual
     (điểm thấp)              (vi phạm nghiêm             (phát hiện
                                trọng)                     tại hiện trường)
          │                        │                           │
          │                        │ + auto notify             │
          │                        │ + auto status change      │
          ▼                        ▼                           ▼
      ┌──────────────────────────────────────────────────────────┐
      │                        RISK CASE                         │
      │              (Quy trình xử lý thống nhất)                │
      │                                                          │
      │  open → triage → in_analysis → actioning → monitoring    │
      │                                                → closed  │
      └──────────────────────────────────────────────────────────┘
```

### 16.4. Vòng lặp review — Cơ chế đảm bảo chất lượng

```
                    ┌──────────────────────────┐
                    │      IN_PROGRESS         │
                    │ (Thực hiện + upload      │
                    │  bằng chứng)             │
                    └────────────┬─────────────┘
                                 │ Submit for Review
                                 ▼
                    ┌──────────────────────────┐
                    │     PENDING_REVIEW       │
                    │ (Chuyên gia xem xét)     │
                    └─────┬──────────┬─────────┘
                          │          │
                  Approve │          │ Reject
                          │          │
                          ▼          ▼
               ┌──────────┐  ┌──────────────┐
               │  CLOSED  │  │ NEEDS_REWORK │
               │  (Xong)  │  │ (Sửa lại)   │
               └──────────┘  └──────┬───────┘
                                    │
                                    │ Làm lại + nộp lại
                                    │
                                    ▼
                         Quay về IN_PROGRESS
                         (lặp cho đến khi đạt)
```

Vòng lặp này có thể diễn ra nhiều lần — đảm bảo **bằng chứng phải đạt chuẩn** mới được đóng task.

### 16.5. Tri thức tích lũy theo thời gian

```
   Thời gian ──────────────────────────────────────────────▶

   Case 1 ──▶ Scar A ──▶ Lesson X
                 │
   Case 2 ──▶ Scar B ──▶ Lesson X (bổ sung)
                 │
   Case 3 ──▶ Scar C ──┐
                        │
                        ▼
              Scar A.recurrence_count = 3
              → Hệ thống tự động phát hiện lặp lại
              → Chuyên gia biết cần hành động mạnh hơn
              → Tra cứu Lesson X để áp dụng + mở rộng
```

Hệ thống tích lũy tri thức **có cấu trúc** theo thời gian:
- Scar ghi nhận **ở đâu** vấn đề xảy ra và **bao nhiêu lần**.
- Lesson ghi nhận **tại sao** và **cách xử lý hiệu quả**.
- Liên kết 2 chiều giúp tra cứu ngược/xuôi.

---

## Phụ lục: Thuật ngữ

| Thuật ngữ | Tiếng Việt | Giải thích |
|-----------|------------|------------|
| Assessment | Phiếu đánh giá | Bản ghi kết quả chấm điểm ATSH |
| Case | Hồ sơ rủi ro | Hồ sơ theo dõi và xử lý một sự cố/rủi ro |
| Task | Công việc khắc phục | Hành động cụ thể cần thực hiện để sửa lỗi |
| Evidence | Bằng chứng | Ảnh/video/tài liệu chứng minh |
| Scar | Vết sẹo | Điểm tri thức trên bản đồ trại, dấu tích rủi ro |
| Lesson Learned | Bài học di sản | Tri thức được chắt lọc và xác nhận |
| RCA | Phân tích nguyên nhân gốc | Tìm hiểu tại sao sự cố xảy ra |
| Killer Metric | Chỉ số vi phạm nghiêm trọng | Vi phạm "không thể chấp nhận" |
| Trust Score | Điểm tin cậy | Đo độ lệch giữa tự khai và audit |
| Spider Chart | Biểu đồ radar | Hiển thị điểm theo 4 trục |
| Floorplan | Sơ đồ mặt bằng | Bản vẽ bố trí trại |
| SLA | Thời hạn cam kết | Thời gian tối đa để hoàn thành |
| Scorecard | Bộ tiêu chí | Template chấm điểm ATSH |
