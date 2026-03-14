-- BIOSECURITY OS 2026
-- Seed dữ liệu tham chiếu mẫu cho PostgreSQL schema draft
BEGIN;
SET search_path TO biosec, public;

-- 1) Vai trò hệ thống
INSERT INTO biosec.app_role (code, name, scope_type, description)
VALUES
    ('SYSTEM_ADMIN', 'Quản trị hệ thống', 'global', 'Toàn quyền cấu hình, dữ liệu và phân quyền.'),
    ('REGION_MANAGER', 'Quản lý vùng', 'region', 'Quản lý trại trong phạm vi vùng/cụm.'),
    ('FARM_MANAGER', 'Quản lý trại', 'farm', 'Điều hành dữ liệu và thực thi tại một trại cụ thể.'),
    ('BIOSEC_EXPERT', 'Chuyên gia ATSH', 'global', 'Phân tích RCA, tạo task, review bằng chứng, xác nhận scar/lesson.'),
    ('AUDITOR', 'Thanh tra/Audit', 'global', 'Thực hiện audit độc lập, blind audit và spot audit.'),
    ('VIEWER', 'Người xem', 'farm', 'Chỉ xem dữ liệu được phân quyền.')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    scope_type = EXCLUDED.scope_type,
    description = EXCLUDED.description;

-- 2) Quyền hệ thống
INSERT INTO biosec.app_permission (code, name, module, action)
VALUES
    ('FARM_READ', 'Xem hồ sơ trại', 'farm', 'read'),
    ('FARM_WRITE', 'Cập nhật hồ sơ trại', 'farm', 'update'),
    ('ASSESSMENT_CREATE', 'Tạo phiếu đánh giá', 'assessment', 'create'),
    ('ASSESSMENT_REVIEW', 'Review phiếu đánh giá', 'assessment', 'review'),
    ('CASE_CREATE', 'Mở case rủi ro', 'case', 'create'),
    ('CASE_ASSIGN', 'Phân công chuyên gia cho case', 'case', 'assign'),
    ('RCA_WRITE', 'Lập RCA', 'rca', 'create'),
    ('TASK_CREATE', 'Tạo task khắc phục', 'task', 'create'),
    ('TASK_REVIEW', 'Review kết quả task', 'task', 'review'),
    ('TASK_CLOSE', 'Đóng task', 'task', 'close'),
    ('SCAR_READ', 'Xem scar memory', 'scar', 'read'),
    ('SCAR_WRITE', 'Tạo/cập nhật scar memory', 'scar', 'update'),
    ('LESSON_VALIDATE', 'Xác nhận lesson learned', 'lesson', 'validate'),
    ('USER_ADMIN', 'Quản trị tài khoản và phân quyền', 'iam', 'admin')
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    module = EXCLUDED.module,
    action = EXCLUDED.action;

-- 3) Gán quyền vào vai trò
WITH role_perm(role_code, perm_code) AS (
    VALUES
        ('SYSTEM_ADMIN', 'FARM_READ'),
        ('SYSTEM_ADMIN', 'FARM_WRITE'),
        ('SYSTEM_ADMIN', 'ASSESSMENT_CREATE'),
        ('SYSTEM_ADMIN', 'ASSESSMENT_REVIEW'),
        ('SYSTEM_ADMIN', 'CASE_CREATE'),
        ('SYSTEM_ADMIN', 'CASE_ASSIGN'),
        ('SYSTEM_ADMIN', 'RCA_WRITE'),
        ('SYSTEM_ADMIN', 'TASK_CREATE'),
        ('SYSTEM_ADMIN', 'TASK_REVIEW'),
        ('SYSTEM_ADMIN', 'TASK_CLOSE'),
        ('SYSTEM_ADMIN', 'SCAR_READ'),
        ('SYSTEM_ADMIN', 'SCAR_WRITE'),
        ('SYSTEM_ADMIN', 'LESSON_VALIDATE'),
        ('SYSTEM_ADMIN', 'USER_ADMIN'),

        ('REGION_MANAGER', 'FARM_READ'),
        ('REGION_MANAGER', 'ASSESSMENT_REVIEW'),
        ('REGION_MANAGER', 'CASE_ASSIGN'),
        ('REGION_MANAGER', 'TASK_REVIEW'),
        ('REGION_MANAGER', 'SCAR_READ'),

        ('FARM_MANAGER', 'FARM_READ'),
        ('FARM_MANAGER', 'FARM_WRITE'),
        ('FARM_MANAGER', 'ASSESSMENT_CREATE'),
        ('FARM_MANAGER', 'CASE_CREATE'),
        ('FARM_MANAGER', 'SCAR_READ'),

        ('BIOSEC_EXPERT', 'FARM_READ'),
        ('BIOSEC_EXPERT', 'ASSESSMENT_REVIEW'),
        ('BIOSEC_EXPERT', 'CASE_CREATE'),
        ('BIOSEC_EXPERT', 'CASE_ASSIGN'),
        ('BIOSEC_EXPERT', 'RCA_WRITE'),
        ('BIOSEC_EXPERT', 'TASK_CREATE'),
        ('BIOSEC_EXPERT', 'TASK_REVIEW'),
        ('BIOSEC_EXPERT', 'TASK_CLOSE'),
        ('BIOSEC_EXPERT', 'SCAR_READ'),
        ('BIOSEC_EXPERT', 'SCAR_WRITE'),
        ('BIOSEC_EXPERT', 'LESSON_VALIDATE'),

        ('AUDITOR', 'FARM_READ'),
        ('AUDITOR', 'ASSESSMENT_CREATE'),
        ('AUDITOR', 'ASSESSMENT_REVIEW'),
        ('AUDITOR', 'SCAR_READ'),

        ('VIEWER', 'FARM_READ'),
        ('VIEWER', 'SCAR_READ')
)
INSERT INTO biosec.role_permission (role_id, permission_id)
SELECT r.id, p.id
FROM role_perm rp
JOIN biosec.app_role r ON r.code = rp.role_code
JOIN biosec.app_permission p ON p.code = rp.perm_code
ON CONFLICT DO NOTHING;

-- 4) Danh mục dùng chung
INSERT INTO biosec.lookup_code (group_code, code, name, display_order, is_active, note)
VALUES
    ('farm_type','sow','Trại nái',1,true,NULL),
    ('farm_type','finisher','Trại thịt',2,true,NULL),
    ('farm_type','mixed','Trại hỗn hợp',3,true,NULL),
    ('farm_type','other','Khác',99,true,NULL),
    ('ownership_type','company','Trại công ty',1,true,NULL),
    ('ownership_type','lease','Trại thuê',2,true,NULL),
    ('ownership_type','contract','Trại liên kết/hợp đồng',3,true,NULL),
    ('ownership_type','other','Khác',99,true,NULL),
    ('baseline_risk_level','low','Thấp',1,true,NULL),
    ('baseline_risk_level','medium','Trung bình',2,true,NULL),
    ('baseline_risk_level','high','Cao',3,true,NULL),
    ('baseline_risk_level','critical','Rất cao',4,true,NULL),
    ('case_priority','P0','P0 - khẩn cấp',1,true,'Ưu tiên cao nhất'),
    ('case_priority','P1','P1 - rất cao',2,true,NULL),
    ('case_priority','P2','P2 - trung bình',3,true,NULL),
    ('case_priority','P3','P3 - dài hạn',4,true,NULL),
    ('case_status','open','Mới mở',1,true,NULL),
    ('case_status','triage','Đang phân loại',2,true,NULL),
    ('case_status','in_analysis','Đang RCA',3,true,NULL),
    ('case_status','actioning','Đang thực thi',4,true,NULL),
    ('case_status','monitoring','Đang theo dõi',5,true,NULL),
    ('case_status','closed','Đã đóng',6,true,NULL),
    ('case_status','cancelled','Đã hủy',7,true,NULL),
    ('task_status','open','Mới tạo',1,true,NULL),
    ('task_status','accepted','Đã nhận',2,true,NULL),
    ('task_status','in_progress','Đang thực hiện',3,true,NULL),
    ('task_status','pending_review','Chờ review',4,true,NULL),
    ('task_status','needs_rework','Cần làm lại',5,true,NULL),
    ('task_status','closed','Đã đóng',6,true,NULL),
    ('task_status','cancelled','Đã hủy',7,true,NULL),
    ('assessment_type','self','Tự đánh giá',1,true,NULL),
    ('assessment_type','scheduled_audit','Audit định kỳ',2,true,NULL),
    ('assessment_type','spot','Spot audit',3,true,NULL),
    ('assessment_type','blind','Blind audit',4,true,NULL),
    ('assessment_type','incident_review','Đánh giá sau sự cố',5,true,NULL),
    ('assessment_status','draft','Nháp',1,true,NULL),
    ('assessment_status','submitted','Đã gửi',2,true,NULL),
    ('assessment_status','reviewed','Đã review',3,true,NULL),
    ('assessment_status','locked','Đã khóa',4,true,NULL),
    ('confidence_level','suspected','Nghi ngờ',1,true,NULL),
    ('confidence_level','probable','Khả năng cao',2,true,NULL),
    ('confidence_level','confirmed','Xác nhận',3,true,NULL),
    ('floorplan_status','draft','Nháp',1,true,NULL),
    ('floorplan_status','active','Đang hiệu lực',2,true,NULL),
    ('floorplan_status','archived','Lưu trữ',3,true,NULL),
    ('notification_channel','in_app','Trong ứng dụng',1,true,NULL),
    ('notification_channel','email','Email',2,true,NULL),
    ('notification_channel','webhook','Webhook',3,true,NULL),
    ('notification_channel','sms','SMS',4,true,NULL)
ON CONFLICT (group_code, code) DO UPDATE
SET name = EXCLUDED.name,
    display_order = EXCLUDED.display_order,
    is_active = EXCLUDED.is_active,
    note = EXCLUDED.note;

-- 5) Định nghĩa killer metric mẫu
INSERT INTO biosec.killer_metric_definition (code, name, description, severity_level, default_case_priority, active_flag)
VALUES
    (
        'SWILL_FEED',
        'Thức ăn thừa / thực phẩm lạ',
        'Phát hiện sử dụng thức ăn thừa, thực phẩm lạ hoặc nguồn thức ăn không kiểm soát cho đàn heo.',
        'critical',
        'P0',
        true
    ),
    (
        'RED_LINE_BREACH',
        'Vi phạm vạch đỏ / ranh giới sạch-bẩn',
        'Có người, vật tư hoặc thiết bị đi sai tuyến và vượt qua ranh giới sạch-bẩn không đúng quy trình.',
        'critical',
        'P0',
        true
    ),
    (
        'DEAD_PIG_PROTOCOL_BREACH',
        'Sai quy trình xử lý heo chết',
        'Việc gom, vận chuyển hoặc tiêu hủy heo chết không tuân thủ SOP và có nguy cơ phát tán mầm bệnh.',
        'critical',
        'P0',
        true
    ),
    (
        'UNKNOWN_VISITOR',
        'Người lạ / nhà thầu không kiểm soát',
        'Có khách, nhà thầu hoặc tài xế vào khu vực trại khi chưa được kiểm soát ATSH đầy đủ.',
        'high',
        'P1',
        true
    )
ON CONFLICT (code) DO UPDATE
SET name = EXCLUDED.name,
    description = EXCLUDED.description,
    severity_level = EXCLUDED.severity_level,
    default_case_priority = EXCLUDED.default_case_priority,
    active_flag = EXCLUDED.active_flag;

COMMIT;