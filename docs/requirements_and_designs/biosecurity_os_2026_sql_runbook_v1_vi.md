# Gói SQL PostgreSQL / Migration draft
## BIOSECURITY OS 2026

**Ngày:** 2026-03-14  
**Ngôn ngữ:** Tiếng Việt  
**Phạm vi:** Schema nghiệp vụ giai đoạn MVP–Phase 1, bám theo ERD tiếng Việt đã chốt.

---

## 1. Bộ file trong gói này

### 1.1 `biosecurity_os_2026_postgres_schema_v1_vi.sql`
Schema PostgreSQL đầy đủ, gồm:
- tạo schema `biosec`
- tạo toàn bộ bảng
- comment tiếng Việt cho bảng và cột
- ràng buộc PK/FK/UNIQUE/CHECK
- index cơ bản + full-text/JSON GIN index
- trigger cập nhật `updated_at`
- trigger guard cho một số business rule quan trọng

### 1.2 `V001__biosecurity_os_2026_init_schema.sql`
Bản migration khởi tạo tương đương với schema file ở trên, đặt tên theo kiểu Flyway.

### 1.3 `V002__biosecurity_os_2026_seed_reference_data.sql`
Seed dữ liệu tham chiếu mẫu:
- role
- permission
- role_permission
- lookup_code
- killer_metric_definition

---

## 2. Tinh chỉnh tên bảng so với ERD

Để tránh va chạm với từ khóa SQL/ORM và để triển khai rõ ràng hơn, migration dùng các tên sau:

| Trong ERD | Trong SQL | Lý do |
|---|---|---|
| `user` | `app_user` | Tránh xung đột với từ khóa/hàm hệ thống và giúp ORM ổn định hơn |
| `role` | `app_role` | Đồng bộ với `app_user`, dễ đọc khi join |
| `permission` | `app_permission` | Đồng bộ với `app_role` |
| *(không có riêng trong ERD)* | `role_permission` | Bảng nối nhiều-nhiều để một role có nhiều permission |

Ngoài các đổi tên trên, phần lớn bảng và cột còn lại bám sát ERD.

---

## 3. Cách chạy

### 3.1 Dùng `psql`
```bash
psql "$DATABASE_URL" -f V001__biosecurity_os_2026_init_schema.sql
psql "$DATABASE_URL" -f V002__biosecurity_os_2026_seed_reference_data.sql
```

### 3.2 Dùng Flyway
- đặt `V001__biosecurity_os_2026_init_schema.sql` vào thư mục migration
- đặt `V002__biosecurity_os_2026_seed_reference_data.sql` vào thư mục migration tiếp theo

### 3.3 Extension bắt buộc
Migration hiện dùng:
- `pgcrypto` để sinh `gen_random_uuid()`

---

## 4. Những business rule đã được đẩy xuống DB

### 4.1 Không cho đóng task khi chưa có review approved
Bảng: `corrective_task`, `task_review`

Ý nghĩa:
- nếu `corrective_task.status = 'closed'`
- nhưng chưa có ít nhất 1 `task_review.review_result = 'approved'`
- database sẽ từ chối cập nhật

### 4.2 Không cho đóng killer event nếu chưa có case
Bảng: `killer_metric_event`, `risk_case`

Ý nghĩa:
- nếu `killer_metric_event.status = 'closed'`
- nhưng chưa có `risk_case.source_killer_event_id` trỏ tới sự kiện đó
- database sẽ từ chối cập nhật

### 4.3 Không cho validate lesson learned khi thiếu căn cứ
Bảng: `lesson_learned`, `lesson_reference`

Ý nghĩa:
- nếu `lesson_learned.status = 'validated'`
- phải có `confirmed_by_user_id`, `confirmed_at`
- và phải có ít nhất 1 `lesson_reference`

### 4.4 Tự cập nhật `updated_at`
Các bảng đã có `updated_at` sẽ tự cập nhật mốc thời gian khi thay đổi dữ liệu.

---

## 5. Những phần vẫn nên để application/service layer xử lý

Database draft này **chưa** ép ở tầng DB cho các phần dưới đây; nên làm ở backend service:

1. Sinh mã số theo quy ước doanh nghiệp:
   - `risk_case.case_no`
   - `corrective_task.task_no`
   - `lesson_learned.lesson_no`

2. Logic nghiệp vụ sâu hơn:
   - SLA động theo loại task/case
   - xác định độ lệch trust score theo cửa sổ thời gian
   - cross-check watermark/GPS/time của file evidence
   - quy tắc chọn `floorplan_version` đúng theo thời điểm sự kiện

3. Soft delete / archive strategy:
   - migration này chưa thêm `archived_at` cho mọi bảng

4. PostGIS / TimescaleDB:
   - chưa bật trong migration init để giữ MVP dễ chạy
   - nên tách thành migration riêng khi hạ tầng production sẵn sàng

---

## 6. Cách đọc comment tiếng Việt của từng cột ngay trong PostgreSQL

Sau khi migrate xong, có thể chạy query này để xem mô tả bảng/cột:

```sql
SELECT
    cols.table_schema,
    cols.table_name,
    cols.column_name,
    pgd.description AS column_comment
FROM pg_catalog.pg_statio_all_tables st
JOIN information_schema.columns cols
  ON cols.table_schema = st.schemaname
 AND cols.table_name = st.relname
LEFT JOIN pg_catalog.pg_description pgd
  ON pgd.objoid = st.relid
 AND pgd.objsubid = cols.ordinal_position
WHERE cols.table_schema = 'biosec'
ORDER BY cols.table_name, cols.ordinal_position;
```

Xem comment cấp bảng:

```sql
SELECT
    n.nspname AS schema_name,
    c.relname AS table_name,
    d.description AS table_comment
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = 0
WHERE n.nspname = 'biosec'
  AND c.relkind = 'r'
ORDER BY c.relname;
```

---

## 7. Gợi ý migration tiếp theo

### V003 – số hóa phát sinh mã chứng từ
Nên thêm:
- bảng sequence theo prefix/năm/tháng
- function sinh `case_no`, `task_no`, `lesson_no`

### V004 – spatial
Nên thêm khi cần:
- PostGIS
- cột `geom` cho `farm`, `external_risk_point`
- spatial index

### V005 – analytics/time-series
Nên thêm khi cần:
- TimescaleDB
- hypertable cho `assessment`, `trust_score_snapshot`, `audit_log`

---

## 8. Ghi chú cuối

Bản migration này bám theo định hướng bạn đã chốt:
- **không có auto-task từ Spider Chart**
- **không có AI learning**
- **không có AI review ảnh**
- chuyên gia ATSH/dịch tễ vẫn là người RCA, tạo task và review evidence
- scar memory / lesson learned vẫn là lõi tri thức di sản của hệ thống
