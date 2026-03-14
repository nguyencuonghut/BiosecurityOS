# Đặc tả API mức ứng dụng
## BIOSECURITY OS 2026

**Phiên bản:** 1.1  
**Ghi chú cập nhật:** Bổ sung chú giải tiếng Việt cho field, viết tắt và cách đọc permission matrix.  
**Ngày:** 2026-03-14  
**Kiểu tài liệu:** API contract draft cho backend FastAPI  
**Phạm vi:** MVP + hướng mở rộng Phase 2

---

## 1. Mục tiêu tài liệu

Tài liệu này mô tả bộ API lõi để đội backend và frontend có thể bắt đầu thiết kế chi tiết, chia sprint và thống nhất contract dữ liệu.

Thiết kế bám theo nguyên tắc:
- RESTful, JSON-first
- Expert-in-the-loop
- Tách rõ module nghiệp vụ
- Không có auto-task và không có AI decision trong giai đoạn 1
- Upload evidence thông qua object storage với cơ chế an toàn và truy vết

---

## 2. Quy ước chung

### 2.1 Base path

```text
/api/v1
```

### 2.2 Authentication

- JWT access token
- Refresh token
- RBAC ở tầng application
- Mọi endpoint nghiệp vụ đều cần token, trừ login/refresh/health

### 2.3 Chuẩn response thành công

```json
{
  "data": {},
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-03-14T10:30:00Z"
  }
}
```

### 2.4 Chuẩn response lỗi

```json
{
  "error": {
    "code": "TASK_REVIEW_REQUIRED",
    "message": "Task chưa thể đóng vì chưa có review phê duyệt.",
    "details": {
      "task_id": "8f0..."
    }
  },
  "meta": {
    "request_id": "req_123",
    "timestamp": "2026-03-14T10:30:00Z"
  }
}
```

### 2.5 Phân trang

```http
GET /resource?page=1&page_size=20&sort=-created_at
```

Response:

```json
{
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 135,
    "request_id": "req_123"
  }
}
```

### 2.6 Chuẩn trường thời gian
- Dùng ISO-8601 UTC ở API
- UI tự render theo timezone người dùng

### 2.7 Idempotency
- Với các thao tác tạo case/task từ UI hoặc tích hợp ngoài, nên hỗ trợ `Idempotency-Key` header ở một số endpoint POST trọng yếu.

### 2.8 Trạng thái chuẩn
- `assessment.status`: draft, submitted, reviewed, locked
- `case.current_status`: new, in_review, prescribed, monitoring, closed
- `task.status`: new, assigned, in_progress, pending_evidence, pending_review, rejected, completed, closed

---


### 2.9 Chú giải field và viết tắt dùng nhiều trong API

| Thuật ngữ / field | Diễn giải tiếng Việt |
|---|---|
| `*_id` | ID tham chiếu tới bản ghi khác. |
| `*_at` | Mốc thời gian phát sinh hoặc hoàn tất một hành động. |
| `status` | Trạng thái nghiệp vụ hiện tại của đối tượng. |
| `priority` | Mức ưu tiên xử lý, thường dùng P0 đến P3. |
| `scope` | Phạm vi dữ liệu mà người dùng được quyền xem hoặc thao tác. |
| `snapshot` | Giá trị chụp lại tại một thời điểm để làm bằng chứng/truy vết lịch sử. |
| `evidence` | Bằng chứng số như ảnh/video/file đính kèm. |
| `review` | Bước chuyên gia/QA kiểm tra và kết luận. |
| `assignee` | Người được giao xử lý công việc. |
| `R / C / U / D / A` | Read / Create / Update / Delete / Approve. Trong tài liệu nội bộ có thể đọc là Xem / Tạo / Sửa / Xóa / Phê duyệt. |

### 2.10 Cách hiểu payload ví dụ trong tài liệu

- Các JSON mẫu trong tài liệu là **contract minh họa**, chưa phải OpenAPI cuối cùng.
- Tên field trong JSON nên giữ nguyên tiếng Anh để đội kỹ thuật triển khai thống nhất.
- Mọi enum như `draft`, `reviewed`, `closed`, `approved` nên được chốt lại thành **lookup code** hoặc enum dùng chung trước khi code chính thức.


## 3. Danh mục endpoint theo module

## 3.1 Auth & Session

### POST `/auth/login`
Đăng nhập.

Request:
```json
{
  "username": "expert01",
  "password": "***"
}
```

Response:
```json
{
  "data": {
    "access_token": "jwt_access",
    "refresh_token": "jwt_refresh",
    "expires_in": 3600,
    "user": {
      "id": "u_001",
      "full_name": "Nguyen Van A",
      "roles": ["EXPERT"]
    }
  }
}
```

### POST `/auth/refresh`
Lấy access token mới.

### POST `/auth/logout`
Thu hồi phiên.

### GET `/auth/me`
Lấy hồ sơ người dùng hiện tại, role, scope truy cập, farm/region được phép xem.

---

## 3.2 Users, Roles, Regions

### GET `/regions`
### POST `/regions`
### GET `/regions/{region_id}`
### PATCH `/regions/{region_id}`

### GET `/users`
Hỗ trợ filter theo `role`, `region_id`, `farm_id`, `status`.

### POST `/users`
### GET `/users/{user_id}`
### PATCH `/users/{user_id}`
### POST `/users/{user_id}/roles`
Gán role cho user.

Request:
```json
{
  "role_id": "role_expert",
  "scope_region_id": null,
  "scope_farm_id": null,
  "effective_from": "2026-03-14"
}
```

### DELETE `/users/{user_id}/roles/{user_role_id}`

### GET `/roles`
### GET `/permissions`

---

## 3.3 Farm Master Data

### GET `/farms`
Filter theo `region_id`, `farm_type`, `ownership_type`, `baseline_risk_level`, `operational_status`.

### POST `/farms`
Request:
```json
{
  "code": "FARM-001",
  "name": "Trại A",
  "farm_type": "sow",
  "ownership_type": "company",
  "region_id": "reg_001",
  "address": "...",
  "latitude": 10.123456,
  "longitude": 106.123456,
  "capacity_headcount": 2500,
  "baseline_risk_level": "medium",
  "structural_risk_note": "Luồng xe cám và xe bắt heo còn giao cắt"
}
```

### GET `/farms/{farm_id}`
### PATCH `/farms/{farm_id}`

### GET `/farms/{farm_id}/areas`
### POST `/farms/{farm_id}/areas`
### PATCH `/farms/{farm_id}/areas/{area_id}`

### GET `/farms/{farm_id}/routes`
### POST `/farms/{farm_id}/routes`

### GET `/farms/{farm_id}/external-risk-points`
### POST `/farms/{farm_id}/external-risk-points`

---

## 3.4 Floorplan / Digital Twin

### GET `/farms/{farm_id}/floorplans`
Lấy danh sách phiên bản sơ đồ trại.

### POST `/farms/{farm_id}/floorplans`
Tạo version mới.

Request:
```json
{
  "title": "Mặt bằng cập nhật sau cải tạo Q2/2026",
  "effective_from": "2026-04-01",
  "plan_file_attachment_id": "att_001"
}
```

### GET `/floorplans/{floorplan_id}`
### PATCH `/floorplans/{floorplan_id}`
### POST `/floorplans/{floorplan_id}/approve`

### GET `/floorplans/{floorplan_id}/markers`
### POST `/floorplans/{floorplan_id}/markers`
### PATCH `/floorplans/{floorplan_id}/markers/{marker_id}`
### DELETE `/floorplans/{floorplan_id}/markers/{marker_id}`

---

## 3.5 Scorecard Template

### GET `/scorecard-templates`
Filter theo `farm_type`, `ownership_type`, `status`.

### POST `/scorecard-templates`
### GET `/scorecard-templates/{template_id}`
### PATCH `/scorecard-templates/{template_id}`
### POST `/scorecard-templates/{template_id}/activate`
### POST `/scorecard-templates/{template_id}/archive`

### GET `/scorecard-templates/{template_id}/sections`
### POST `/scorecard-templates/{template_id}/sections`
### PATCH `/scorecard-sections/{section_id}`

### GET `/scorecard-sections/{section_id}/items`
### POST `/scorecard-sections/{section_id}/items`
### PATCH `/scorecard-items/{item_id}`
### DELETE `/scorecard-items/{item_id}`

---

## 3.6 Assessments & Audits

### GET `/assessments`
Filter theo `farm_id`, `assessment_type`, `status`, `date_from`, `date_to`.

### POST `/assessments`
Tạo assessment mới.

Request:
```json
{
  "farm_id": "farm_001",
  "template_id": "tmpl_001",
  "assessment_type": "self",
  "assessment_date": "2026-03-14T08:00:00Z"
}
```

### GET `/assessments/{assessment_id}`
Lấy header + item results + evidence summary.

### PATCH `/assessments/{assessment_id}`
Cho phép sửa metadata khi status còn `draft`.

### POST `/assessments/{assessment_id}/items/bulk-upsert`
Ghi kết quả chấm từng item.

Request:
```json
{
  "items": [
    {
      "scorecard_item_id": "item_001",
      "response_value_text": "Đạt",
      "response_value_numeric": 5,
      "awarded_score": 5,
      "is_non_compliant": false,
      "note": "",
      "area_id": "area_gate"
    },
    {
      "scorecard_item_id": "item_002",
      "response_value_text": "Không đạt",
      "response_value_numeric": 0,
      "awarded_score": 0,
      "is_non_compliant": true,
      "note": "Bồn sát trùng không có hóa chất",
      "area_id": "area_gate"
    }
  ]
}
```

### POST `/assessments/{assessment_id}/submit`
Khóa biểu mẫu và tính điểm tổng.

### POST `/assessments/{assessment_id}/attachments`
Liên kết attachment vào assessment.

### GET `/assessments/{assessment_id}/spider-chart`
Trả dữ liệu để frontend vẽ Spider Chart.

Response:
```json
{
  "data": {
    "farm_id": "farm_001",
    "assessment_id": "ass_001",
    "axes": [
      {"code": "HARDWARE", "label": "Hạ tầng", "score": 62},
      {"code": "PROCESS", "label": "Quy trình", "score": 85},
      {"code": "BEHAVIOR", "label": "Hành vi", "score": 71},
      {"code": "MONITORING", "label": "Giám sát", "score": 76}
    ]
  }
}
```

---

## 3.7 Killer Metrics

### GET `/killer-metric-definitions`
### POST `/killer-metric-definitions`
### PATCH `/killer-metric-definitions/{definition_id}`

### GET `/killer-metric-events`
Filter theo `farm_id`, `status`, `date_from`, `date_to`, `definition_id`.

### POST `/killer-metric-events`
Request:
```json
{
  "farm_id": "farm_001",
  "area_id": "area_dead_zone",
  "definition_id": "km_dead_pig_wrong_process",
  "event_at": "2026-03-14T02:00:00Z",
  "summary": "Heo chết được kéo qua luồng sạch",
  "source_type": "field_report"
}
```

### GET `/killer-metric-events/{event_id}`
### PATCH `/killer-metric-events/{event_id}`
### POST `/killer-metric-events/{event_id}/attachments`

---

## 3.8 Trust Score

### GET `/trust-scores`
Filter theo `farm_id`, `date_from`, `date_to`.

### POST `/trust-scores/calculate`
Tính snapshot từ cặp assessment tự đánh giá và audit.

Request:
```json
{
  "farm_id": "farm_001",
  "self_assessment_id": "ass_self_001",
  "audit_assessment_id": "ass_audit_001"
}
```

### GET `/farms/{farm_id}/trust-score/latest`

---

## 3.9 Risk Case

### GET `/cases`
Filter theo `farm_id`, `priority`, `current_status`, `case_type`, `assigned_expert_user_id`, `queue=my`.

### POST `/cases`
Tạo case thủ công hoặc từ assessment/killer metric.

Request:
```json
{
  "farm_id": "farm_001",
  "area_id": "area_gate",
  "case_type": "low_score",
  "title": "Điểm khu sát trùng cổng xuống thấp liên tục",
  "summary": "3 kỳ đánh giá liên tiếp không đạt tại khu cổng chính",
  "source_assessment_id": "ass_001",
  "priority": "P1",
  "severity": "high"
}
```

### GET `/cases/{case_id}`
### PATCH `/cases/{case_id}`
### POST `/cases/{case_id}/assign-expert`
### POST `/cases/{case_id}/change-status`

### GET `/cases/queue/review`
Danh sách case chờ chuyên gia xử lý, hỗ trợ sort theo SLA, killer metric, trust gap.

### GET `/cases/{case_id}/timeline`
Trả về chuỗi sự kiện: assessment -> event -> RCA -> task -> review -> scar/lesson.

---

## 3.10 RCA

### GET `/cases/{case_id}/rca-records`
### POST `/cases/{case_id}/rca-records`

Request:
```json
{
  "method": "five_why",
  "problem_statement": "Khu sát trùng cổng tái diễn thiếu hóa chất",
  "impact_scope": "Nguy cơ xe vào không khử trùng đúng quy cách",
  "direct_cause": "Nhân viên bảo vệ không kiểm tra tồn kho hóa chất",
  "system_cause": "Không có checklist bàn giao ca trực",
  "behavioral_cause": "Thói quen bỏ qua bước kiểm tra cuối ca",
  "structural_cause": "Không có kho hóa chất dự phòng tại cổng",
  "monitoring_cause": "Audit định kỳ không diễn ra vào ca đêm",
  "external_factor": null,
  "conclusion_confidence": "probable"
}
```

### GET `/rca-records/{rca_id}`
### PATCH `/rca-records/{rca_id}`
### POST `/rca-records/{rca_id}/approve`

### POST `/rca-records/{rca_id}/factors`
### PATCH `/rca-factors/{factor_id}`
### DELETE `/rca-factors/{factor_id}`

---

## 3.11 Corrective Tasks

### GET `/tasks`
Filter theo `farm_id`, `case_id`, `priority`, `status`, `assignee_user_id`, `overdue=true`.

### POST `/tasks`
Tạo task thủ công bởi chuyên gia.

Request:
```json
{
  "case_id": "case_001",
  "title": "Thiết lập checklist tồn kho hóa chất khu cổng",
  "description": "Lập checklist đầu ca/cuối ca và quy định người ký nhận",
  "task_type": "corrective",
  "source_rca_id": "rca_001",
  "area_id": "area_gate",
  "priority": "P1",
  "sla_due_at": "2026-03-14T12:00:00Z",
  "completion_due_at": "2026-03-16T12:00:00Z",
  "completion_criteria": "Checklist được ban hành và sử dụng 2 ca liên tiếp",
  "evidence_requirement": "Ảnh bảng checklist tại cổng + ảnh tồn kho hóa chất + xác nhận quản lý trại",
  "assignees": [
    {"user_id": "u_farm_mgr", "responsibility_type": "owner"},
    {"user_id": "u_supervisor", "responsibility_type": "support"}
  ]
}
```

### GET `/tasks/{task_id}`
### PATCH `/tasks/{task_id}`
### POST `/tasks/{task_id}/change-status`
### POST `/tasks/{task_id}/assignees`
### DELETE `/tasks/{task_id}/assignees/{assignee_id}`
### POST `/tasks/{task_id}/comments`

### POST `/tasks/{task_id}/submit-for-review`
Chuyển task sang `pending_review`.

### POST `/tasks/{task_id}/close`
Chỉ thành công nếu đã có review approved.

---

## 3.12 Evidence / Attachments

### POST `/attachments/presign`
Sinh pre-signed upload URL để frontend/mobile upload trực tiếp lên MinIO.

Request:
```json
{
  "file_name": "gate_20260314_0800.jpg",
  "mime_type": "image/jpeg",
  "entity_type": "task",
  "entity_id": "task_001"
}
```

Response:
```json
{
  "data": {
    "attachment_id": "att_001",
    "upload_url": "https://minio...",
    "headers": {
      "x-amz-meta-origin": "mobile"
    }
  }
}
```

### POST `/attachments/{attachment_id}/finalize`
Xác nhận upload xong, lưu metadata file.

Request:
```json
{
  "file_size_bytes": 524288,
  "captured_at": "2026-03-14T08:10:00Z",
  "latitude": 10.1234,
  "longitude": 106.1234,
  "watermark_text": "2026-03-14 15:10 | Farm A | Gate | user_12"
}
```

### GET `/attachments/{attachment_id}`
### GET `/attachments/{attachment_id}/download`
### DELETE `/attachments/{attachment_id}`
Soft delete hoặc chặn xóa với attachment đã là bằng chứng đã review.

### POST `/tasks/{task_id}/attachments`
Gắn attachment vào task.

### POST `/assessments/{assessment_id}/attachments`
Gắn attachment vào assessment.

---

## 3.13 Task Review

### GET `/tasks/{task_id}/reviews`
### POST `/tasks/{task_id}/reviews`

Request:
```json
{
  "review_result": "needs_rework",
  "review_note": "Thiếu ảnh thể hiện checklist có chữ ký cuối ca",
  "next_action_due_at": "2026-03-15T12:00:00Z"
}
```

### POST `/tasks/{task_id}/approve`
Sugar endpoint, nội bộ vẫn tạo `task_review`.

### POST `/tasks/{task_id}/reject`
Sugar endpoint.

---

## 3.14 Scar Memory

### GET `/scars`
Filter theo `farm_id`, `scar_type`, `confidence_level`, `status`, `area_id`.

### POST `/scars`
Request:
```json
{
  "farm_id": "farm_001",
  "floorplan_version_id": "fp_003",
  "area_id": "area_gate",
  "scar_type": "repeated_breach",
  "title": "Hotspot tái diễn tại khu cổng chính",
  "description": "Khu này liên tục phát sinh vi phạm thiếu hóa chất và bypass quy trình xe vào",
  "source_of_risk": "Điểm giao cắt giữa xe cám và xe kỹ thuật viên",
  "confidence_level": "probable",
  "event_date": "2026-03-14",
  "x_percent": 13.5,
  "y_percent": 27.0,
  "recurrence_flag": true
}
```

### GET `/scars/{scar_id}`
### PATCH `/scars/{scar_id}`
### POST `/scars/{scar_id}/validate`
### POST `/scars/{scar_id}/links`
Gắn case/task/assessment/evidence vào scar.

### GET `/farms/{farm_id}/scar-map`
Trả dữ liệu phục vụ ECharts layer map.

---

## 3.15 Lesson Learned

### GET `/lessons`
Filter theo `farm_type`, `issue_type`, `confidence_level`, `status`, `tag`.

### POST `/lessons`
### GET `/lessons/{lesson_id}`
### PATCH `/lessons/{lesson_id}`
### POST `/lessons/{lesson_id}/validate`
### POST `/lessons/{lesson_id}/references`
### POST `/lessons/{lesson_id}/tags`

### GET `/lessons/search/similar`
Tra cứu case/scar/lesson tương tự bằng filter có cấu trúc.

Request query ví dụ:
```http
GET /lessons/search/similar?farm_type=sow&ownership_type=leased&issue_type=vehicle_hygiene&area_type=gate
```

---

## 3.16 Dashboard & Analytics

### GET `/dashboards/executive-summary`
Tổng quan toàn hệ thống.

Response gợi ý:
```json
{
  "data": {
    "farm_count": 20,
    "avg_score": 78.4,
    "high_risk_farms": 4,
    "open_cases": 23,
    "overdue_tasks": 11,
    "killer_metric_open": 2,
    "low_trust_sites": 3
  }
}
```

### GET `/dashboards/farm/{farm_id}`
### GET `/dashboards/benchmark`
### GET `/dashboards/trust-gaps`
### GET `/dashboards/killer-metrics-trend`
### GET `/dashboards/scar-hotspots`

---

## 3.17 Reports & Export

### POST `/reports`
Sinh báo cáo bất đồng bộ.

Request:
```json
{
  "report_type": "monthly_biosecurity_summary",
  "format": "pdf",
  "filters": {
    "month": "2026-03",
    "region_id": "reg_001"
  }
}
```

### GET `/reports/{report_id}`
### GET `/reports/{report_id}/download`

---

## 3.18 Notifications

### GET `/notifications`
### POST `/notifications/{notification_id}/read`
### POST `/notifications/bulk-read`

---

## 3.19 Audit Log

### GET `/audit-logs`
Filter theo `entity_type`, `entity_id`, `actor_user_id`, `date_from`, `date_to`.
Chỉ cho admin hoặc role chuyên biệt.

---

## 4. Workflow API theo nghiệp vụ chính

## 4.1 Luồng tự đánh giá -> case -> task -> review

1. `POST /assessments`
2. `POST /assessments/{id}/items/bulk-upsert`
3. `POST /assessments/{id}/submit`
4. Chuyên gia xem dashboard hoặc queue, sau đó `POST /cases`
5. `POST /cases/{case_id}/rca-records`
6. `POST /tasks`
7. Mobile/web upload:
   - `POST /attachments/presign`
   - upload file trực tiếp MinIO
   - `POST /attachments/{id}/finalize`
   - `POST /tasks/{task_id}/attachments`
8. `POST /tasks/{task_id}/submit-for-review`
9. `POST /tasks/{task_id}/reviews`
10. Nếu approved, `POST /tasks/{task_id}/close`
11. Nếu case có giá trị tri thức, `POST /scars` và/hoặc `POST /lessons`

## 4.2 Luồng killer metric

1. `POST /killer-metric-events`
2. Gắn evidence nếu có
3. `POST /cases`
4. `POST /cases/{id}/assign-expert`
5. RCA và task như luồng trên

## 4.3 Luồng scar memory

1. `POST /scars`
2. `POST /scars/{id}/links`
3. `POST /scars/{id}/validate`
4. Nếu đủ điều kiện thành tri thức chuẩn: `POST /lessons`, `POST /lessons/{id}/references`, `POST /lessons/{id}/validate`

---

## 5. Permission matrix tối giản theo endpoint

**Ghi chú:** `R = Xem`, `C = Tạo`, `U = Cập nhật`, `D = Xóa`, `A = Phê duyệt`. `scope` nghĩa là chỉ trong phạm vi vùng/trại được phân quyền.


| Module | Exec | Expert | Regional Manager | Farm Manager | QA/Auditor | Field Staff | Admin |
|---|---|---|---|---|---|---|---|
| View dashboard system | R | R | R(scope) | R(own) | R(scope) | - | R |
| Manage farms/areas | - | C/U | U(scope) | U(own limited) | - | - | C/U/D |
| Manage scorecard template | - | C/U/A | - | - | R | - | C/U/D |
| Create assessment | - | C | C(scope) | C | C | - | C |
| Review assessment | - | R/U | R(scope) | R(own) | R/U | - | R/U |
| Create case | - | C | C(scope) | C(own) | C | - | C |
| RCA approve | - | C/U/A | - | - | - | - | R |
| Create task | - | C/U | C(scope) | - | - | - | C/U |
| Submit evidence | - | R | R(scope) | C/U | C/U | C/U | R |
| Review evidence/task | - | C/U/A | U(scope) | - | U | - | C/U/A |
| Manage scars/lessons | R | C/U/A | R(scope) | R(own) | C/U | - | C/U/A |
| View audit logs | - | limited | limited | limited own | limited | - | full |

---

## 6. Eventing / automation khuyến nghị

Không đặt nghiệp vụ cốt lõi vào n8n. Tuy nhiên có thể phát event nội bộ để automation xử lý:

- `assessment.submitted`
- `killer_metric_event.created`
- `case.created`
- `case.sla_breached`
- `task.assigned`
- `task.overdue`
- `task.review_requested`
- `task.reviewed`
- `scar.validated`
- `lesson.validated`

Các event này có thể được Redis stream / message queue / background worker tiêu thụ để gửi thông báo hoặc cập nhật dashboard cache.

---

## 7. Error code nên chuẩn hóa sớm

| Code | Ý nghĩa |
|---|---|
| AUTH_INVALID_CREDENTIALS | Sai tài khoản hoặc mật khẩu |
| AUTH_FORBIDDEN_SCOPE | Không có quyền trong phạm vi farm/region |
| ASSESSMENT_ALREADY_LOCKED | Phiếu đánh giá đã khóa |
| CASE_EXPERT_REQUIRED | Case cần chuyên gia được gán |
| RCA_APPROVAL_REQUIRED | Chưa có RCA được duyệt |
| TASK_EVIDENCE_REQUIRED | Task thiếu bằng chứng |
| TASK_REVIEW_REQUIRED | Task chưa được review |
| TASK_ALREADY_CLOSED | Task đã đóng |
| KILLER_CASE_REQUIRED | Killer metric phải có case review |
| LESSON_REFERENCE_REQUIRED | Lesson thiếu reference |
| FLOORPLAN_VERSION_REQUIRED | Scar phải gắn phiên bản sơ đồ |
| ATTACHMENT_IMMUTABLE | File bằng chứng đã khóa, không được xóa |

---

## 8. Endpoint ưu tiên cho MVP Sprint 1-3

### Sprint 1
- auth
- users/roles cơ bản
- farms/areas
- scorecard templates
- assessments create/view/submit

### Sprint 2
- killer metrics
- cases
- RCA
- tasks
- attachments presign/finalize/link
- task review

### Sprint 3
- floorplans/markers
- scars
- lessons
- executive dashboard
- audit logs
- reports cơ bản

---

## 9. Open API spec nên sinh sau tài liệu này

Sau khi chốt contract mức business, đội backend nên sinh thêm:

- OpenAPI YAML/JSON chuẩn FastAPI
- Postman collection
- Mock server hoặc example server
- Contract test cho các endpoint trọng yếu: assessments, cases, tasks, reviews, scars

---

## 10. Kết luận

Bộ API trên được thiết kế để phục vụ đúng mô hình **Spider Chart là công cụ quan sát**, **chuyên gia là người phân tích và ra task**, còn **scar/lesson là trí nhớ doanh nghiệp**. Điều đó giúp MVP đủ đơn giản để triển khai, nhưng vẫn giữ đường nâng cấp dài hạn khi doanh nghiệp muốn đi sâu hơn vào analytics hoặc rule-based recommendation.
