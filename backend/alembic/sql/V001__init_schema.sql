-- BIOSECURITY OS 2026
-- PostgreSQL schema draft (Vietnamese annotations)
-- Phiên bản: 1.1
-- Ghi chú: schema này bám sát ERD v2 tiếng Việt, có một số tinh chỉnh thực thi:
--   1) `user` -> `app_user`
--   2) `role` -> `app_role`
--   3) `permission` -> `app_permission`
--   4) Bổ sung `role_permission` để mô hình role-permission ở dạng nhiều-nhiều
--   5) Bổ sung `lookup_code` với cấu trúc đầy đủ để quản lý danh mục dùng chung
--   6) Bổ sung `app_user_credential` và `app_refresh_token` cho xác thực
--   7) Bổ sung cột `version` cho các bảng có state machine (optimistic locking)
--   8) Bổ sung cột `archived_at` cho các bảng dữ liệu điều tra (soft delete)
--   9) Bổ sung `created_at`/`updated_at` cho các bảng còn thiếu

CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE SCHEMA IF NOT EXISTS biosec;
COMMENT ON SCHEMA biosec IS 'Schema nghiệp vụ chính cho BIOSECURITY OS 2026';

-- region
CREATE TABLE biosec.region (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    code varchar(50) NOT NULL,
    name varchar(255) NOT NULL,
    manager_user_id uuid,
    status varchar(30) DEFAULT 'active' NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_region_1 CHECK (status IN ('active','inactive'))
);

-- farm
CREATE TABLE biosec.farm (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    code varchar(50) NOT NULL,
    name varchar(255) NOT NULL,
    farm_type varchar(30) NOT NULL,
    ownership_type varchar(30) NOT NULL,
    region_id uuid NOT NULL,
    address text,
    latitude numeric(10,7),
    longitude numeric(10,7),
    capacity_headcount integer,
    operational_status varchar(30) DEFAULT 'active' NOT NULL,
    baseline_risk_level varchar(30) DEFAULT 'medium' NOT NULL,
    structural_risk_note text,
    opened_at date DEFAULT now(),
    closed_at date,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_farm_1 CHECK (farm_type IN ('sow','finisher','mixed','other')),
    CONSTRAINT ck_farm_2 CHECK (ownership_type IN ('company','lease','contract','other')),
    CONSTRAINT ck_farm_3 CHECK (operational_status IN ('active','paused','closed','archived')),
    CONSTRAINT ck_farm_4 CHECK (baseline_risk_level IN ('low','medium','high','critical')),
    CONSTRAINT ck_farm_5 CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90)),
    CONSTRAINT ck_farm_6 CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180)),
    CONSTRAINT ck_farm_7 CHECK (capacity_headcount IS NULL OR capacity_headcount >= 0),
    CONSTRAINT ck_farm_8 CHECK (closed_at IS NULL OR opened_at IS NULL OR closed_at >= opened_at)
);

-- app_user
CREATE TABLE biosec.app_user (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    username varchar(100) NOT NULL,
    full_name varchar(255) NOT NULL,
    email varchar(255),
    phone varchar(30),
    region_id uuid,
    farm_id uuid,
    title varchar(150),
    status varchar(30) DEFAULT 'active' NOT NULL,
    last_login_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_app_user_1 CHECK (status IN ('active','locked','archived'))
);

-- app_user_credential
CREATE TABLE biosec.app_user_credential (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL,
    password_hash varchar(255) NOT NULL,
    failed_attempts integer DEFAULT 0 NOT NULL,
    locked_until timestamptz,
    password_changed_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_app_user_credential_1 CHECK (failed_attempts >= 0)
);

-- app_refresh_token
CREATE TABLE biosec.app_refresh_token (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL,
    token_hash varchar(255) NOT NULL,
    expires_at timestamptz NOT NULL,
    revoked_at timestamptz,
    ip_address inet,
    user_agent text,
    created_at timestamptz DEFAULT now() NOT NULL
);

-- app_role
CREATE TABLE biosec.app_role (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    code varchar(50) NOT NULL,
    name varchar(255) NOT NULL,
    scope_type varchar(30) NOT NULL,
    description text,
    CONSTRAINT ck_app_role_1 CHECK (scope_type IN ('global','region','farm'))
);

-- app_permission
CREATE TABLE biosec.app_permission (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    code varchar(100) NOT NULL,
    name varchar(255) NOT NULL,
    module varchar(100) NOT NULL,
    action varchar(50) NOT NULL
);

-- role_permission
CREATE TABLE biosec.role_permission (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    role_id uuid NOT NULL,
    permission_id uuid NOT NULL,
    granted_at timestamptz DEFAULT now() NOT NULL
);

-- user_role
CREATE TABLE biosec.user_role (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    user_id uuid NOT NULL,
    role_id uuid NOT NULL,
    scope_region_id uuid,
    scope_farm_id uuid,
    effective_from date,
    effective_to date,
    CONSTRAINT ck_user_role_1 CHECK (effective_to IS NULL OR effective_from IS NULL OR effective_to >= effective_from)
);

-- lookup_code
CREATE TABLE biosec.lookup_code (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    group_code varchar(100) NOT NULL,
    code varchar(100) NOT NULL,
    name varchar(255) NOT NULL,
    display_order integer DEFAULT 1 NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    note text,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_lookup_code_1 CHECK (display_order > 0)
);

-- attachment
CREATE TABLE biosec.attachment (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    storage_bucket varchar(100) NOT NULL,
    object_key varchar(500) NOT NULL,
    file_name_original varchar(255) NOT NULL,
    mime_type varchar(100) NOT NULL,
    file_size_bytes bigint NOT NULL,
    sha256_hash varchar(64),
    captured_at timestamptz,
    latitude numeric(10,7),
    longitude numeric(10,7),
    watermark_text text,
    uploaded_by_user_id uuid NOT NULL,
    uploaded_at timestamptz DEFAULT now() NOT NULL,
    is_original_file boolean DEFAULT true NOT NULL,
    parent_attachment_id uuid,
    archived_at timestamptz,
    CONSTRAINT ck_attachment_1 CHECK (file_size_bytes >= 0),
    CONSTRAINT ck_attachment_2 CHECK (latitude IS NULL OR (latitude >= -90 AND latitude <= 90)),
    CONSTRAINT ck_attachment_3 CHECK (longitude IS NULL OR (longitude >= -180 AND longitude <= 180))
);

-- farm_area
CREATE TABLE biosec.farm_area (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    parent_area_id uuid,
    code varchar(50) NOT NULL,
    name varchar(255) NOT NULL,
    area_type varchar(50) NOT NULL,
    clean_dirty_class varchar(30),
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_farm_area_1 CHECK (clean_dirty_class IS NULL OR clean_dirty_class IN ('clean','buffer','dirty')),
    CONSTRAINT ck_farm_area_2 CHECK (parent_area_id IS NULL OR parent_area_id <> id)
);

-- farm_route
CREATE TABLE biosec.farm_route (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    route_type varchar(30) NOT NULL,
    from_area_id uuid NOT NULL,
    to_area_id uuid NOT NULL,
    direction_rule varchar(30) NOT NULL,
    note text,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_farm_route_1 CHECK (direction_rule IN ('one_way','restricted','conditional','bidirectional')),
    CONSTRAINT ck_farm_route_2 CHECK (from_area_id <> to_area_id)
);

-- floorplan_version
CREATE TABLE biosec.floorplan_version (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    version_no integer NOT NULL,
    title varchar(255) NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    plan_file_attachment_id uuid,
    status varchar(30) DEFAULT 'draft' NOT NULL,
    approved_by uuid,
    approved_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_floorplan_version_1 CHECK (version_no > 0),
    CONSTRAINT ck_floorplan_version_2 CHECK (status IN ('draft','active','archived')),
    CONSTRAINT ck_floorplan_version_3 CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- floorplan_marker
CREATE TABLE biosec.floorplan_marker (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    floorplan_version_id uuid NOT NULL,
    area_id uuid,
    marker_type varchar(50) NOT NULL,
    label varchar(255) NOT NULL,
    x_percent numeric(5,2) NOT NULL,
    y_percent numeric(5,2) NOT NULL,
    metadata_json jsonb,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_floorplan_marker_1 CHECK (x_percent >= 0 AND x_percent <= 100),
    CONSTRAINT ck_floorplan_marker_2 CHECK (y_percent >= 0 AND y_percent <= 100)
);

-- external_risk_point
CREATE TABLE biosec.external_risk_point (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    risk_type varchar(50) NOT NULL,
    name varchar(255),
    latitude numeric(10,7) NOT NULL,
    longitude numeric(10,7) NOT NULL,
    distance_m integer,
    note text,
    confidence_level varchar(20) NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_external_risk_point_1 CHECK (latitude >= -90 AND latitude <= 90),
    CONSTRAINT ck_external_risk_point_2 CHECK (longitude >= -180 AND longitude <= 180),
    CONSTRAINT ck_external_risk_point_3 CHECK (distance_m IS NULL OR distance_m >= 0),
    CONSTRAINT ck_external_risk_point_4 CHECK (confidence_level IN ('suspected','probable','confirmed'))
);

-- scorecard_template
CREATE TABLE biosec.scorecard_template (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    code varchar(50) NOT NULL,
    name varchar(255) NOT NULL,
    farm_type varchar(30),
    ownership_type varchar(30),
    risk_profile varchar(30),
    version_no integer NOT NULL,
    status varchar(30) DEFAULT 'draft' NOT NULL,
    effective_from date NOT NULL,
    effective_to date,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_scorecard_template_1 CHECK (version_no > 0),
    CONSTRAINT ck_scorecard_template_2 CHECK (status IN ('draft','active','archived')),
    CONSTRAINT ck_scorecard_template_3 CHECK (effective_to IS NULL OR effective_to >= effective_from)
);

-- scorecard_section
CREATE TABLE biosec.scorecard_section (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    template_id uuid NOT NULL,
    code varchar(50) NOT NULL,
    name varchar(255) NOT NULL,
    section_type varchar(30) NOT NULL,
    weight numeric(8,2) NOT NULL,
    display_order integer DEFAULT 1 NOT NULL,
    CONSTRAINT ck_scorecard_section_1 CHECK (section_type IN ('hardware','software','behavior','monitoring','other')),
    CONSTRAINT ck_scorecard_section_2 CHECK (weight >= 0),
    CONSTRAINT ck_scorecard_section_3 CHECK (display_order > 0)
);

-- scorecard_item
CREATE TABLE biosec.scorecard_item (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    section_id uuid NOT NULL,
    code varchar(50) NOT NULL,
    question_text text NOT NULL,
    response_type varchar(30) NOT NULL,
    max_score numeric(8,2) NOT NULL,
    weight numeric(8,2) NOT NULL,
    killer_metric_definition_id uuid,  -- FK nullable → killer_metric_definition
    is_killer_related boolean GENERATED ALWAYS AS (killer_metric_definition_id IS NOT NULL) STORED,
    threshold_warning numeric(8,2),
    threshold_fail numeric(8,2),
    guidance_text text,
    display_order integer DEFAULT 1 NOT NULL,
    CONSTRAINT ck_scorecard_item_1 CHECK (response_type IN ('yes_no','score_0_5','option','numeric','text')),
    CONSTRAINT ck_scorecard_item_2 CHECK (max_score >= 0),
    CONSTRAINT ck_scorecard_item_3 CHECK (weight >= 0),
    CONSTRAINT ck_scorecard_item_4 CHECK (threshold_warning IS NULL OR threshold_warning >= 0),
    CONSTRAINT ck_scorecard_item_5 CHECK (threshold_fail IS NULL OR threshold_fail >= 0),
    CONSTRAINT ck_scorecard_item_6 CHECK (threshold_fail IS NULL OR threshold_warning IS NULL OR threshold_fail >= threshold_warning),
    CONSTRAINT ck_scorecard_item_7 CHECK (display_order > 0)
);

-- assessment
CREATE TABLE biosec.assessment (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    template_id uuid NOT NULL,
    assessment_type varchar(30) NOT NULL,
    assessment_date timestamptz DEFAULT now() NOT NULL,
    performed_by_user_id uuid NOT NULL,
    performed_by_name_snapshot varchar(255) NOT NULL,
    overall_score numeric(8,2),
    hardware_score numeric(8,2),
    process_score numeric(8,2),
    behavior_score numeric(8,2),
    monitoring_score numeric(8,2),
    status varchar(30) DEFAULT 'draft' NOT NULL,
    summary_note text,
    trust_gap_basis_id uuid,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_assessment_1 CHECK (assessment_type IN ('self','scheduled_audit','spot','blind','incident_review')),
    CONSTRAINT ck_assessment_2 CHECK (overall_score IS NULL OR (overall_score >= 0 AND overall_score <= 100)),
    CONSTRAINT ck_assessment_3 CHECK (hardware_score IS NULL OR (hardware_score >= 0 AND hardware_score <= 100)),
    CONSTRAINT ck_assessment_4 CHECK (process_score IS NULL OR (process_score >= 0 AND process_score <= 100)),
    CONSTRAINT ck_assessment_5 CHECK (behavior_score IS NULL OR (behavior_score >= 0 AND behavior_score <= 100)),
    CONSTRAINT ck_assessment_6 CHECK (monitoring_score IS NULL OR (monitoring_score >= 0 AND monitoring_score <= 100)),
    CONSTRAINT ck_assessment_7 CHECK (status IN ('draft','submitted','reviewed','locked')),
    CONSTRAINT ck_assessment_8 CHECK (trust_gap_basis_id IS NULL OR trust_gap_basis_id <> id)
);

-- assessment_item_result
CREATE TABLE biosec.assessment_item_result (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    assessment_id uuid NOT NULL,
    scorecard_item_id uuid NOT NULL,
    response_value_text text,
    response_value_numeric numeric(8,2),
    awarded_score numeric(8,2) NOT NULL,
    is_non_compliant boolean DEFAULT false NOT NULL,
    note text,
    area_id uuid,
    evidence_required boolean DEFAULT false NOT NULL,
    CONSTRAINT ck_assessment_item_result_1 CHECK (response_value_numeric IS NULL OR response_value_numeric >= 0),
    CONSTRAINT ck_assessment_item_result_2 CHECK (awarded_score >= 0)
);

-- assessment_attachment
CREATE TABLE biosec.assessment_attachment (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    assessment_id uuid NOT NULL,
    attachment_id uuid NOT NULL,
    area_id uuid,
    caption text
);

-- killer_metric_definition
CREATE TABLE biosec.killer_metric_definition (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    code varchar(50) NOT NULL,
    name varchar(255) NOT NULL,
    description text NOT NULL,
    source_type varchar(30) NOT NULL DEFAULT 'both',  -- 'scorecard_item' | 'field_report' | 'both'
    severity_level varchar(20) NOT NULL,
    default_case_priority varchar(20) NOT NULL,
    active_flag boolean DEFAULT true NOT NULL,
    CONSTRAINT ck_killer_metric_definition_1 CHECK (severity_level IN ('low','medium','high','critical')),
    CONSTRAINT ck_killer_metric_definition_2 CHECK (default_case_priority IN ('P0','P1','P2','P3')),
    CONSTRAINT ck_killer_metric_definition_3 CHECK (source_type IN ('scorecard_item','field_report','both'))
);

-- killer_metric_event
CREATE TABLE biosec.killer_metric_event (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    area_id uuid,
    definition_id uuid NOT NULL,
    event_at timestamptz DEFAULT now() NOT NULL,
    detected_by_user_id uuid NOT NULL,
    source_type varchar(30) NOT NULL,  -- 'assessment' | 'field_report'
    source_assessment_item_result_id uuid,  -- nullable FK → assessment_item_result; bắt buộc khi source_type='assessment'
    summary text NOT NULL,
    status varchar(30) DEFAULT 'open' NOT NULL,
    required_case_flag boolean DEFAULT true NOT NULL,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_killer_metric_event_1 CHECK (status IN ('open','under_review','controlled','closed','rejected')),
    CONSTRAINT ck_killer_metric_event_2 CHECK (source_type IN ('assessment','field_report')),
    CONSTRAINT ck_killer_metric_event_3 CHECK (
        (source_type = 'assessment' AND source_assessment_item_result_id IS NOT NULL)
        OR
        (source_type = 'field_report' AND source_assessment_item_result_id IS NULL)
    )
);

-- trust_score_snapshot
CREATE TABLE biosec.trust_score_snapshot (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    source_self_assessment_id uuid NOT NULL,
    source_audit_assessment_id uuid NOT NULL,
    trust_score numeric(8,2) NOT NULL,
    absolute_gap_score numeric(8,2) NOT NULL,
    severity_factor numeric(8,2),
    snapshot_date date DEFAULT CURRENT_DATE NOT NULL,
    note text,
    CONSTRAINT ck_trust_score_snapshot_1 CHECK (trust_score >= 0 AND trust_score <= 100),
    CONSTRAINT ck_trust_score_snapshot_2 CHECK (absolute_gap_score >= 0),
    CONSTRAINT ck_trust_score_snapshot_3 CHECK (severity_factor IS NULL OR severity_factor >= 0),
    CONSTRAINT ck_trust_score_snapshot_4 CHECK (source_self_assessment_id <> source_audit_assessment_id)
);

-- risk_case
CREATE TABLE biosec.risk_case (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    area_id uuid,
    case_no varchar(50) NOT NULL,
    case_type varchar(30) NOT NULL,
    title varchar(255) NOT NULL,
    summary text NOT NULL,
    source_assessment_id uuid,
    source_killer_event_id uuid,
    source_scar_id uuid,
    priority varchar(20) NOT NULL,
    severity varchar(20) NOT NULL,
    current_status varchar(30) DEFAULT 'open' NOT NULL,
    assigned_expert_user_id uuid,
    first_response_due_at timestamptz,
    closure_due_at timestamptz,
    opened_at timestamptz DEFAULT now() NOT NULL,
    closed_at timestamptz,
    version integer DEFAULT 1 NOT NULL,
    archived_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_risk_case_1 CHECK (priority IN ('P0','P1','P2','P3')),
    CONSTRAINT ck_risk_case_2 CHECK (severity IN ('low','medium','high','critical')),
    CONSTRAINT ck_risk_case_3 CHECK (current_status IN ('open','triage','in_analysis','actioning','monitoring','closed','cancelled')),
    CONSTRAINT ck_risk_case_4 CHECK (closed_at IS NULL OR closed_at >= opened_at)
);

-- case_participant
CREATE TABLE biosec.case_participant (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    case_id uuid NOT NULL,
    user_id uuid NOT NULL,
    role_in_case varchar(30) NOT NULL,
    CONSTRAINT ck_case_participant_1 CHECK (role_in_case IN ('owner','reviewer','observer','farm_contact'))
);

-- rca_record
CREATE TABLE biosec.rca_record (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    case_id uuid NOT NULL,
    method varchar(30) NOT NULL,
    problem_statement text NOT NULL,
    impact_scope text,
    direct_cause text,
    system_cause text,
    behavioral_cause text,
    structural_cause text,
    monitoring_cause text,
    external_factor text,
    conclusion_confidence varchar(20) NOT NULL,
    analyzed_by_user_id uuid NOT NULL,
    analyzed_at timestamptz DEFAULT now() NOT NULL,
    approved_by_user_id uuid,
    approved_at timestamptz,
    CONSTRAINT ck_rca_record_1 CHECK (method IN ('5_why','fishbone','capa','other')),
    CONSTRAINT ck_rca_record_2 CHECK (conclusion_confidence IN ('low','medium','high','confirmed'))
);

-- rca_factor
CREATE TABLE biosec.rca_factor (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    rca_record_id uuid NOT NULL,
    factor_group varchar(30) NOT NULL,
    factor_text text NOT NULL,
    confidence_level varchar(20) NOT NULL,
    is_primary boolean NOT NULL,
    CONSTRAINT ck_rca_factor_1 CHECK (factor_group IN ('people','process','place','equipment','environment','monitoring','external')),
    CONSTRAINT ck_rca_factor_2 CHECK (confidence_level IN ('low','medium','high','confirmed'))
);

-- corrective_task
CREATE TABLE biosec.corrective_task (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    case_id uuid NOT NULL,
    task_no varchar(50) NOT NULL,
    title varchar(255) NOT NULL,
    description text NOT NULL,
    task_type varchar(30) NOT NULL,
    source_rca_id uuid,
    area_id uuid,
    priority varchar(20) NOT NULL,
    status varchar(30) DEFAULT 'open' NOT NULL,
    sla_due_at timestamptz,
    completion_due_at timestamptz,
    completion_criteria text,
    evidence_requirement text,
    created_by_user_id uuid NOT NULL,
    closed_by_user_id uuid,
    closed_at timestamptz,
    version integer DEFAULT 1 NOT NULL,
    archived_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_corrective_task_1 CHECK (task_type IN ('corrective','preventive','inspection','training','capex')),
    CONSTRAINT ck_corrective_task_2 CHECK (priority IN ('P0','P1','P2','P3')),
    CONSTRAINT ck_corrective_task_3 CHECK (status IN ('open','accepted','in_progress','pending_review','needs_rework','closed','cancelled')),
    CONSTRAINT ck_corrective_task_4 CHECK (completion_due_at IS NULL OR sla_due_at IS NULL OR completion_due_at >= sla_due_at)
);

-- task_assignee
CREATE TABLE biosec.task_assignee (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    task_id uuid NOT NULL,
    user_id uuid NOT NULL,
    responsibility_type varchar(30) NOT NULL,
    accepted_at timestamptz,
    CONSTRAINT ck_task_assignee_1 CHECK (responsibility_type IN ('owner','support','approver'))
);

-- task_attachment
CREATE TABLE biosec.task_attachment (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    task_id uuid NOT NULL,
    attachment_id uuid NOT NULL,
    upload_stage varchar(30) NOT NULL,
    is_primary_evidence boolean DEFAULT false NOT NULL,
    caption text,
    CONSTRAINT ck_task_attachment_1 CHECK (upload_stage IN ('before','during','after','review'))
);

-- task_review
CREATE TABLE biosec.task_review (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    task_id uuid NOT NULL,
    reviewer_user_id uuid NOT NULL,
    review_result varchar(30) NOT NULL,
    review_note text,
    reviewed_at timestamptz DEFAULT now() NOT NULL,
    next_action_due_at timestamptz,
    CONSTRAINT ck_task_review_1 CHECK (review_result IN ('approved','rejected','needs_rework'))
);

-- task_comment
CREATE TABLE biosec.task_comment (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    task_id uuid NOT NULL,
    author_user_id uuid NOT NULL,
    comment_text text NOT NULL,
    comment_type varchar(30) NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL
);

-- scar_record
CREATE TABLE biosec.scar_record (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    farm_id uuid NOT NULL,
    floorplan_version_id uuid,
    area_id uuid,
    scar_type varchar(30) NOT NULL,
    title varchar(255) NOT NULL,
    description text NOT NULL,
    source_of_risk text,
    confidence_level varchar(20) NOT NULL,
    event_date date,
    x_percent numeric(5,2),
    y_percent numeric(5,2),
    status varchar(30) DEFAULT 'active' NOT NULL,
    recurrence_flag boolean DEFAULT false NOT NULL,
    recurrence_count integer DEFAULT 0 NOT NULL,
    created_by_user_id uuid NOT NULL,
    validated_by_user_id uuid,
    validated_at timestamptz,
    archived_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_scar_record_1 CHECK (scar_type IN ('outbreak','hotspot','repeated_breach','near_miss','structural_flaw')),
    CONSTRAINT ck_scar_record_2 CHECK (confidence_level IN ('suspected','probable','confirmed')),
    CONSTRAINT ck_scar_record_3 CHECK (x_percent IS NULL OR (x_percent >= 0 AND x_percent <= 100)),
    CONSTRAINT ck_scar_record_4 CHECK (y_percent IS NULL OR (y_percent >= 0 AND y_percent <= 100)),
    CONSTRAINT ck_scar_record_5 CHECK (status IN ('active','archived','obsolete')),
    CONSTRAINT ck_scar_record_6 CHECK (recurrence_count >= 0)
);

-- scar_link
CREATE TABLE biosec.scar_link (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    scar_id uuid NOT NULL,
    linked_object_type varchar(30) NOT NULL,
    linked_object_id uuid NOT NULL,
    link_reason varchar(100),
    CONSTRAINT ck_scar_link_1 CHECK (linked_object_type IN ('case','task','assessment','attachment'))
);

-- lesson_learned
CREATE TABLE biosec.lesson_learned (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    lesson_no varchar(50) NOT NULL,
    title varchar(255) NOT NULL,
    problem_context text NOT NULL,
    root_cause_summary text,
    action_summary text,
    outcome_summary text,
    recurrence_observed boolean NOT NULL,
    applicability_scope text,
    confidence_level varchar(20) NOT NULL,
    status varchar(30) DEFAULT 'draft' NOT NULL,
    confirmed_by_user_id uuid,
    confirmed_at timestamptz,
    archived_at timestamptz,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    CONSTRAINT ck_lesson_learned_1 CHECK (confidence_level IN ('suspected','probable','confirmed')),
    CONSTRAINT ck_lesson_learned_2 CHECK (status IN ('draft','validated','archived','obsolete'))
);

-- lesson_reference
CREATE TABLE biosec.lesson_reference (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    lesson_id uuid NOT NULL,
    reference_type varchar(30) NOT NULL,
    reference_id uuid NOT NULL,
    contribution_note text,
    CONSTRAINT ck_lesson_reference_1 CHECK (reference_type IN ('scar','case','task','assessment'))
);

-- similarity_tag
CREATE TABLE biosec.similarity_tag (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    lesson_id uuid NOT NULL,
    tag_type varchar(30) NOT NULL,
    tag_value varchar(100) NOT NULL,
    CONSTRAINT ck_similarity_tag_1 CHECK (tag_type IN ('farm_type','issue_type','route_type','season','ownership_type','risk_profile','other'))
);

-- notification
CREATE TABLE biosec.notification (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    recipient_user_id uuid NOT NULL,
    channel varchar(30) NOT NULL,
    title varchar(255) NOT NULL,
    body text NOT NULL,
    entity_type varchar(30),
    entity_id uuid,
    status varchar(30) DEFAULT 'queued' NOT NULL,
    sent_at timestamptz,
    read_at timestamptz,
    CONSTRAINT ck_notification_1 CHECK (channel IN ('in_app','email','webhook','sms')),
    CONSTRAINT ck_notification_2 CHECK (status IN ('queued','sent','read','failed'))
);

-- audit_log
CREATE TABLE biosec.audit_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL PRIMARY KEY,
    actor_user_id uuid NOT NULL,
    action varchar(100) NOT NULL,
    entity_type varchar(50) NOT NULL,
    entity_id uuid NOT NULL,
    before_json jsonb,
    after_json jsonb,
    ip_address inet,
    user_agent text,
    occurred_at timestamptz DEFAULT now() NOT NULL
);

COMMENT ON TABLE biosec.region IS $$ Bảng danh mục vùng/cụm để gom trại theo địa bàn và phục vụ phân quyền. $$;
COMMENT ON COLUMN biosec.region.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.region.code IS $$ Mã vùng/cụm trại để chuẩn hóa báo cáo và phân quyền. $$;
COMMENT ON COLUMN biosec.region.name IS $$ Tên vùng hoặc cụm trại, ví dụ Miền Tây 1. $$;
COMMENT ON COLUMN biosec.region.manager_user_id IS $$ Người quản lý phụ trách vùng/cụm này. $$;
COMMENT ON COLUMN biosec.region.status IS $$ Trạng thái sử dụng của vùng: active/inactive. $$;
COMMENT ON COLUMN biosec.region.created_at IS $$ Thời điểm hệ thống tạo bản ghi. $$;
COMMENT ON COLUMN biosec.region.updated_at IS $$ Thời điểm cập nhật gần nhất. $$;

COMMENT ON TABLE biosec.farm IS $$ Bảng hồ sơ gốc của từng trại. $$;
COMMENT ON COLUMN biosec.farm.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.farm.code IS $$ Mã trại duy nhất, dùng xuyên suốt báo cáo, API và tích hợp. $$;
COMMENT ON COLUMN biosec.farm.name IS $$ Tên trại hiển thị cho người dùng. $$;
COMMENT ON COLUMN biosec.farm.farm_type IS $$ Loại trại, ví dụ nái (sow), thịt/finisher hoặc hỗn hợp. $$;
COMMENT ON COLUMN biosec.farm.ownership_type IS $$ Hình thức sở hữu/vận hành: trại công ty hay trại thuê. $$;
COMMENT ON COLUMN biosec.farm.region_id IS $$ Vùng/cụm mà trại đang thuộc về. $$;
COMMENT ON COLUMN biosec.farm.address IS $$ Địa chỉ mô tả của trại. $$;
COMMENT ON COLUMN biosec.farm.latitude IS $$ Vĩ độ vị trí trung tâm trại hoặc cổng chính. $$;
COMMENT ON COLUMN biosec.farm.longitude IS $$ Kinh độ vị trí trung tâm trại hoặc cổng chính. $$;
COMMENT ON COLUMN biosec.farm.capacity_headcount IS $$ Quy mô sức chứa tham chiếu của trại (đầu heo). $$;
COMMENT ON COLUMN biosec.farm.operational_status IS $$ Trạng thái vận hành của trại: active/paused/closed. $$;
COMMENT ON COLUMN biosec.farm.baseline_risk_level IS $$ Mức rủi ro nền mang tính cấu trúc của trại. $$;
COMMENT ON COLUMN biosec.farm.structural_risk_note IS $$ Mô tả các điểm yếu nền như sai luồng, gần bãi rác, gần khu hủy heo. $$;
COMMENT ON COLUMN biosec.farm.opened_at IS $$ Ngày trại bắt đầu vận hành. $$;
COMMENT ON COLUMN biosec.farm.closed_at IS $$ Ngày trại ngừng vận hành nếu có. $$;
COMMENT ON COLUMN biosec.farm.created_at IS $$ Thời điểm hệ thống tạo bản ghi. $$;
COMMENT ON COLUMN biosec.farm.updated_at IS $$ Thời điểm cập nhật gần nhất. $$;

COMMENT ON TABLE biosec.app_user IS $$ Bảng tài khoản người dùng sử dụng hệ thống. Bảng này tương ứng với bảng `user` trong ERD; tên được đổi thành `app_user` để tránh xung đột tên từ khóa và ORM. $$;
COMMENT ON COLUMN biosec.app_user.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.app_user.username IS $$ Tên đăng nhập duy nhất vào hệ thống. $$;
COMMENT ON COLUMN biosec.app_user.full_name IS $$ Họ tên đầy đủ của người dùng. $$;
COMMENT ON COLUMN biosec.app_user.email IS $$ Email công việc; có thể để trống với lao động hiện trường không dùng email. $$;
COMMENT ON COLUMN biosec.app_user.phone IS $$ Số điện thoại liên hệ. $$;
COMMENT ON COLUMN biosec.app_user.region_id IS $$ Vùng phụ trách chính nếu người dùng làm ở cấp vùng. $$;
COMMENT ON COLUMN biosec.app_user.farm_id IS $$ Trại gắn trực tiếp với người dùng nếu là nhân sự trại. $$;
COMMENT ON COLUMN biosec.app_user.title IS $$ Chức danh hiển thị, ví dụ Quản lý trại hoặc Chuyên gia ATSH. $$;
COMMENT ON COLUMN biosec.app_user.status IS $$ Trạng thái tài khoản: đang hoạt động, tạm khóa hoặc lưu trữ. $$;
COMMENT ON COLUMN biosec.app_user.last_login_at IS $$ Lần đăng nhập gần nhất, phục vụ kiểm soát sử dụng tài khoản. $$;
COMMENT ON COLUMN biosec.app_user.created_at IS $$ Thời điểm hệ thống tạo bản ghi. $$;
COMMENT ON COLUMN biosec.app_user.updated_at IS $$ Thời điểm cập nhật gần nhất. $$;

COMMENT ON TABLE biosec.app_user_credential IS $$ Bảng lưu trữ thông tin xác thực của người dùng. Tách riêng khỏi app_user để tăng bảo mật. $$;
COMMENT ON COLUMN biosec.app_user_credential.user_id IS $$ Người dùng sở hữu credential này. $$;
COMMENT ON COLUMN biosec.app_user_credential.password_hash IS $$ Mật khẩu đã hash (bcrypt/argon2). Không bao giờ lưu plaintext. $$;
COMMENT ON COLUMN biosec.app_user_credential.failed_attempts IS $$ Số lần đăng nhập sai liên tiếp, reset về 0 khi thành công. $$;
COMMENT ON COLUMN biosec.app_user_credential.locked_until IS $$ Thời điểm hết khóa tạm nếu tài khoản bị lock do sai password. $$;
COMMENT ON COLUMN biosec.app_user_credential.password_changed_at IS $$ Lần đổi mật khẩu gần nhất. $$;

COMMENT ON TABLE biosec.app_refresh_token IS $$ Bảng lưu trữ refresh token cho JWT session management. $$;
COMMENT ON COLUMN biosec.app_refresh_token.user_id IS $$ Người dùng sở hữu token. $$;
COMMENT ON COLUMN biosec.app_refresh_token.token_hash IS $$ Hash của refresh token, không lưu token gốc. $$;
COMMENT ON COLUMN biosec.app_refresh_token.expires_at IS $$ Thời điểm token hết hạn. $$;
COMMENT ON COLUMN biosec.app_refresh_token.revoked_at IS $$ Thời điểm token bị thu hồi (logout hoặc kick). $$;

COMMENT ON TABLE biosec.app_role IS $$ Bảng vai trò nghiệp vụ/ứng dụng. Bảng này tương ứng với bảng `role` trong ERD. $$;
COMMENT ON COLUMN biosec.app_role.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.app_role.code IS $$ Mã role kỹ thuật/nghiệp vụ, ví dụ EXEC, EXPERT, QA. $$;
COMMENT ON COLUMN biosec.app_role.name IS $$ Tên role hiển thị bằng ngôn ngữ người dùng. $$;
COMMENT ON COLUMN biosec.app_role.scope_type IS $$ Phạm vi role được áp dụng: toàn hệ thống, theo vùng hoặc theo trại. $$;
COMMENT ON COLUMN biosec.app_role.description IS $$ Giải thích vai trò này dùng cho nhóm người dùng nào. $$;

COMMENT ON TABLE biosec.app_permission IS $$ Bảng quyền thao tác chi tiết theo module. Bảng này tương ứng với bảng `permission` trong ERD. $$;
COMMENT ON COLUMN biosec.app_permission.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.app_permission.code IS $$ Mã quyền duy nhất để backend kiểm soát truy cập. $$;
COMMENT ON COLUMN biosec.app_permission.name IS $$ Tên quyền hiển thị cho admin hoặc tài liệu phân quyền. $$;
COMMENT ON COLUMN biosec.app_permission.module IS $$ Module mà quyền này áp dụng, ví dụ cases, tasks, scorecards. $$;
COMMENT ON COLUMN biosec.app_permission.action IS $$ Hành động được phép thực hiện, ví dụ read/create/update/review/approve. $$;

COMMENT ON TABLE biosec.role_permission IS $$ Bảng nối nhiều-nhiều giữa vai trò và quyền. Bảng này được bổ sung ở mức triển khai để role có thể gom nhiều permission và một permission có thể dùng cho nhiều role. $$;
COMMENT ON COLUMN biosec.role_permission.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.role_permission.role_id IS $$ Vai trò được cấp quyền. $$;
COMMENT ON COLUMN biosec.role_permission.permission_id IS $$ Quyền chi tiết được gán cho vai trò. $$;
COMMENT ON COLUMN biosec.role_permission.granted_at IS $$ Thời điểm quyền được gán cho vai trò. $$;

COMMENT ON TABLE biosec.user_role IS $$ Bảng nối user với role và phạm vi hiệu lực. $$;
COMMENT ON COLUMN biosec.user_role.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.user_role.user_id IS $$ Người dùng được gán role. $$;
COMMENT ON COLUMN biosec.user_role.role_id IS $$ Role được gán cho người dùng. $$;
COMMENT ON COLUMN biosec.user_role.scope_region_id IS $$ Nếu role chỉ hiệu lực trong một vùng thì lưu vùng tại đây. $$;
COMMENT ON COLUMN biosec.user_role.scope_farm_id IS $$ Nếu role chỉ hiệu lực trong một trại thì lưu trại tại đây. $$;
COMMENT ON COLUMN biosec.user_role.effective_from IS $$ Ngày role bắt đầu có hiệu lực. $$;
COMMENT ON COLUMN biosec.user_role.effective_to IS $$ Ngày role hết hiệu lực; để trống nếu còn hiệu lực. $$;

COMMENT ON TABLE biosec.lookup_code IS $$ Bảng tùy chọn để chuẩn hóa code set như status, priority, confidence_level, farm_type, task_type. $$;
COMMENT ON COLUMN biosec.lookup_code.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.lookup_code.group_code IS $$ Nhóm mã danh mục, ví dụ task_status, case_priority, farm_type. $$;
COMMENT ON COLUMN biosec.lookup_code.code IS $$ Mã kỹ thuật duy nhất trong phạm vi một group_code. $$;
COMMENT ON COLUMN biosec.lookup_code.name IS $$ Tên hiển thị tiếng Việt hoặc tên nghiệp vụ. $$;
COMMENT ON COLUMN biosec.lookup_code.display_order IS $$ Thứ tự hiển thị trong combobox, bộ lọc hoặc bảng quản trị. $$;
COMMENT ON COLUMN biosec.lookup_code.is_active IS $$ Đánh dấu mã này còn được phép sử dụng hay đã ngưng. $$;
COMMENT ON COLUMN biosec.lookup_code.note IS $$ Ghi chú nghiệp vụ hoặc quy tắc sử dụng mã. $$;
COMMENT ON COLUMN biosec.lookup_code.created_at IS $$ Thời điểm tạo mã danh mục trong hệ thống. $$;
COMMENT ON COLUMN biosec.lookup_code.updated_at IS $$ Thời điểm cập nhật gần nhất của mã danh mục. $$;

COMMENT ON TABLE biosec.attachment IS $$ Bảng metadata file bằng chứng hoặc file nghiệp vụ. $$;
COMMENT ON COLUMN biosec.attachment.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.attachment.storage_bucket IS $$ Bucket lưu file trong MinIO hoặc object storage. $$;
COMMENT ON COLUMN biosec.attachment.object_key IS $$ Đường dẫn logic/khóa object duy nhất trong bucket. $$;
COMMENT ON COLUMN biosec.attachment.file_name_original IS $$ Tên file gốc do người dùng tải lên hoặc thiết bị tạo ra. $$;
COMMENT ON COLUMN biosec.attachment.mime_type IS $$ Kiểu nội dung file, ví dụ image/jpeg, video/mp4. $$;
COMMENT ON COLUMN biosec.attachment.file_size_bytes IS $$ Kích thước file tính theo byte. $$;
COMMENT ON COLUMN biosec.attachment.sha256_hash IS $$ Mã băm phục vụ kiểm tra tính toàn vẹn và chain-of-custody. $$;
COMMENT ON COLUMN biosec.attachment.captured_at IS $$ Thời điểm chụp/ghi từ metadata file nếu đọc được. $$;
COMMENT ON COLUMN biosec.attachment.latitude IS $$ Vĩ độ từ metadata hoặc watermark nếu có. $$;
COMMENT ON COLUMN biosec.attachment.longitude IS $$ Kinh độ từ metadata hoặc watermark nếu có. $$;
COMMENT ON COLUMN biosec.attachment.watermark_text IS $$ Chuỗi watermark hiển thị trên ảnh/video sau khi đóng dấu. $$;
COMMENT ON COLUMN biosec.attachment.uploaded_by_user_id IS $$ Người tải file lên hệ thống. $$;
COMMENT ON COLUMN biosec.attachment.uploaded_at IS $$ Thời điểm upload thành công. $$;
COMMENT ON COLUMN biosec.attachment.is_original_file IS $$ Phân biệt file gốc và file bản trình bày/annotate/chuyển đổi. $$;
COMMENT ON COLUMN biosec.attachment.parent_attachment_id IS $$ Nếu file này sinh ra từ file gốc khác thì tham chiếu về file cha. $$;
COMMENT ON COLUMN biosec.attachment.archived_at IS $$ Thời điểm soft delete; NULL nghĩa là chưa xóa. $$;

COMMENT ON TABLE biosec.farm_area IS $$ Bảng cấu trúc khu vực bên trong trại. $$;
COMMENT ON COLUMN biosec.farm_area.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.farm_area.farm_id IS $$ Trại mà khu vực này thuộc về. $$;
COMMENT ON COLUMN biosec.farm_area.parent_area_id IS $$ Khu cha để tạo cấu trúc phân cấp, ví dụ Barn 1 thuộc Khu chăn nuôi. $$;
COMMENT ON COLUMN biosec.farm_area.code IS $$ Mã khu vực duy nhất trong phạm vi một trại. $$;
COMMENT ON COLUMN biosec.farm_area.name IS $$ Tên khu vực hiển thị, ví dụ Cổng, Nhà tắm, Khu nái đẻ. $$;
COMMENT ON COLUMN biosec.farm_area.area_type IS $$ Loại khu vực để chuẩn hóa logic, ví dụ gate, shower, office, barn, quarantine. $$;
COMMENT ON COLUMN biosec.farm_area.clean_dirty_class IS $$ Phân loại sạch/buffer/bẩn phục vụ kiểm soát luồng ATSH. $$;
COMMENT ON COLUMN biosec.farm_area.is_active IS $$ Đánh dấu khu này còn được sử dụng hay đã ngưng. $$;
COMMENT ON COLUMN biosec.farm_area.created_at IS $$ Thời điểm hệ thống tạo bản ghi. $$;
COMMENT ON COLUMN biosec.farm_area.updated_at IS $$ Thời điểm cập nhật gần nhất. $$;

COMMENT ON TABLE biosec.farm_route IS $$ Bảng mô tả các luồng di chuyển cần kiểm soát ATSH. $$;
COMMENT ON COLUMN biosec.farm_route.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.farm_route.farm_id IS $$ Trại sở hữu tuyến/luồng này. $$;
COMMENT ON COLUMN biosec.farm_route.route_type IS $$ Loại luồng cần quản lý: người, xe, xác chết, cám... $$;
COMMENT ON COLUMN biosec.farm_route.from_area_id IS $$ Điểm bắt đầu của luồng di chuyển. $$;
COMMENT ON COLUMN biosec.farm_route.to_area_id IS $$ Điểm kết thúc của luồng di chuyển. $$;
COMMENT ON COLUMN biosec.farm_route.direction_rule IS $$ Quy tắc đi một chiều, hạn chế hoặc có điều kiện. $$;
COMMENT ON COLUMN biosec.farm_route.note IS $$ Ghi chú nghiệp vụ về cách vận hành luồng. $$;

COMMENT ON TABLE biosec.floorplan_version IS $$ Bảng quản lý phiên bản sơ đồ mặt bằng trại. $$;
COMMENT ON COLUMN biosec.floorplan_version.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.floorplan_version.farm_id IS $$ Trại áp dụng phiên bản sơ đồ này. $$;
COMMENT ON COLUMN biosec.floorplan_version.version_no IS $$ Số phiên bản tăng dần để lưu lịch sử thay đổi mặt bằng. $$;
COMMENT ON COLUMN biosec.floorplan_version.title IS $$ Tên phiên bản sơ đồ, thường gắn với đợt cải tạo hoặc giai đoạn vận hành. $$;
COMMENT ON COLUMN biosec.floorplan_version.effective_from IS $$ Ngày sơ đồ bắt đầu được xem là bản vận hành chính thức. $$;
COMMENT ON COLUMN biosec.floorplan_version.effective_to IS $$ Ngày sơ đồ hết hiệu lực nếu đã thay bằng bản mới. $$;
COMMENT ON COLUMN biosec.floorplan_version.plan_file_attachment_id IS $$ File sơ đồ gốc đính kèm trong kho file. $$;
COMMENT ON COLUMN biosec.floorplan_version.status IS $$ Trạng thái phiên bản sơ đồ: draft/active/archived. $$;
COMMENT ON COLUMN biosec.floorplan_version.approved_by IS $$ Người phê duyệt cho phép dùng phiên bản sơ đồ này. $$;
COMMENT ON COLUMN biosec.floorplan_version.approved_at IS $$ Thời điểm phê duyệt phiên bản sơ đồ. $$;

COMMENT ON TABLE biosec.floorplan_marker IS $$ Bảng marker hiển thị trên sơ đồ/digital twin. $$;
COMMENT ON COLUMN biosec.floorplan_marker.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.floorplan_marker.floorplan_version_id IS $$ Phiên bản sơ đồ mà marker này nằm trên đó. $$;
COMMENT ON COLUMN biosec.floorplan_marker.area_id IS $$ Khu vực nội bộ liên quan nếu marker trỏ tới một area chuẩn hóa. $$;
COMMENT ON COLUMN biosec.floorplan_marker.marker_type IS $$ Loại marker: cổng, điểm rủi ro, điểm scar, checkpoint... $$;
COMMENT ON COLUMN biosec.floorplan_marker.label IS $$ Nhãn hiển thị ngay trên sơ đồ. $$;
COMMENT ON COLUMN biosec.floorplan_marker.x_percent IS $$ Tọa độ X theo phần trăm chiều ngang sơ đồ để hiển thị ổn định theo kích thước màn hình. $$;
COMMENT ON COLUMN biosec.floorplan_marker.y_percent IS $$ Tọa độ Y theo phần trăm chiều dọc sơ đồ. $$;
COMMENT ON COLUMN biosec.floorplan_marker.metadata_json IS $$ Thông tin mở rộng cho marker, ví dụ màu, icon, loại liên kết. $$;

COMMENT ON TABLE biosec.external_risk_point IS $$ Bảng điểm nguy cơ bên ngoài ảnh hưởng tới trại. $$;
COMMENT ON COLUMN biosec.external_risk_point.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.external_risk_point.farm_id IS $$ Trại bị ảnh hưởng bởi điểm rủi ro bên ngoài này. $$;
COMMENT ON COLUMN biosec.external_risk_point.risk_type IS $$ Loại rủi ro bên ngoài, ví dụ bãi rác, lò mổ, khu tiêu hủy, ao nước thải. $$;
COMMENT ON COLUMN biosec.external_risk_point.name IS $$ Tên hoặc mô tả ngắn của điểm rủi ro. $$;
COMMENT ON COLUMN biosec.external_risk_point.latitude IS $$ Vĩ độ của điểm rủi ro bên ngoài. $$;
COMMENT ON COLUMN biosec.external_risk_point.longitude IS $$ Kinh độ của điểm rủi ro bên ngoài. $$;
COMMENT ON COLUMN biosec.external_risk_point.distance_m IS $$ Khoảng cách ước tính từ trại tới điểm rủi ro, tính bằng mét. $$;
COMMENT ON COLUMN biosec.external_risk_point.note IS $$ Ghi chú thêm về bối cảnh hoặc mức độ ảnh hưởng. $$;
COMMENT ON COLUMN biosec.external_risk_point.confidence_level IS $$ Độ tin cậy của thông tin điểm rủi ro: suspected/probable/confirmed. $$;

COMMENT ON TABLE biosec.scorecard_template IS $$ Bảng mẫu scorecard theo loại trại/rủi ro. $$;
COMMENT ON COLUMN biosec.scorecard_template.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.scorecard_template.code IS $$ Mã bộ scorecard để version hóa và tích hợp. $$;
COMMENT ON COLUMN biosec.scorecard_template.name IS $$ Tên bộ scorecard hiển thị, ví dụ Trại nái thuê rủi ro cao. $$;
COMMENT ON COLUMN biosec.scorecard_template.farm_type IS $$ Loại trại mà mẫu scorecard này áp dụng. $$;
COMMENT ON COLUMN biosec.scorecard_template.ownership_type IS $$ Áp dụng cho trại công ty hay trại thuê. $$;
COMMENT ON COLUMN biosec.scorecard_template.risk_profile IS $$ Hồ sơ rủi ro mục tiêu của mẫu, ví dụ high-risk lease. $$;
COMMENT ON COLUMN biosec.scorecard_template.version_no IS $$ Phiên bản của bộ scorecard. $$;
COMMENT ON COLUMN biosec.scorecard_template.status IS $$ Trạng thái mẫu: draft/active/archived. $$;
COMMENT ON COLUMN biosec.scorecard_template.effective_from IS $$ Ngày mẫu bắt đầu được dùng. $$;
COMMENT ON COLUMN biosec.scorecard_template.effective_to IS $$ Ngày mẫu ngưng hiệu lực nếu có mẫu mới thay thế. $$;

COMMENT ON TABLE biosec.scorecard_section IS $$ Bảng nhóm tiêu chí trong một scorecard. $$;
COMMENT ON COLUMN biosec.scorecard_section.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.scorecard_section.template_id IS $$ Mẫu scorecard mà nhóm tiêu chí này thuộc về. $$;
COMMENT ON COLUMN biosec.scorecard_section.code IS $$ Mã nhóm tiêu chí duy nhất trong một mẫu. $$;
COMMENT ON COLUMN biosec.scorecard_section.name IS $$ Tên nhóm tiêu chí, ví dụ Hạ tầng hoặc Quy trình. $$;
COMMENT ON COLUMN biosec.scorecard_section.section_type IS $$ Loại nhóm để gom logic tính điểm, ví dụ hardware/software/behavior/monitoring. $$;
COMMENT ON COLUMN biosec.scorecard_section.weight IS $$ Trọng số của nhóm tiêu chí trong tổng điểm. $$;
COMMENT ON COLUMN biosec.scorecard_section.display_order IS $$ Thứ tự hiển thị trên UI và biểu đồ. $$;

COMMENT ON TABLE biosec.scorecard_item IS $$ Bảng tiêu chí/câu hỏi chi tiết dùng để chấm điểm. $$;
COMMENT ON COLUMN biosec.scorecard_item.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.scorecard_item.section_id IS $$ Nhóm tiêu chí mà câu hỏi này thuộc về. $$;
COMMENT ON COLUMN biosec.scorecard_item.code IS $$ Mã câu hỏi/tiêu chí duy nhất trong nhóm. $$;
COMMENT ON COLUMN biosec.scorecard_item.question_text IS $$ Nội dung tiêu chí hoặc câu hỏi đánh giá. $$;
COMMENT ON COLUMN biosec.scorecard_item.response_type IS $$ Kiểu câu trả lời đầu vào, ví dụ yes_no, score_0_5, option, numeric. $$;
COMMENT ON COLUMN biosec.scorecard_item.max_score IS $$ Điểm tối đa của tiêu chí. $$;
COMMENT ON COLUMN biosec.scorecard_item.weight IS $$ Trọng số của tiêu chí trong nhóm. $$;
COMMENT ON COLUMN biosec.scorecard_item.is_killer_related IS $$ Cột tính toán tự động (GENERATED): true khi killer_metric_definition_id IS NOT NULL. Dùng để UI highlight, không cho phép nhập tay. $$;
COMMENT ON COLUMN biosec.scorecard_item.threshold_warning IS $$ Ngưỡng cảnh báo để UI tô màu hoặc kích hoạt theo dõi. $$;
COMMENT ON COLUMN biosec.scorecard_item.threshold_fail IS $$ Ngưỡng xem là không đạt nghiêm trọng. $$;
COMMENT ON COLUMN biosec.scorecard_item.guidance_text IS $$ Hướng dẫn chấm điểm hoặc giải thích tiêu chí cho người đánh giá. $$;
COMMENT ON COLUMN biosec.scorecard_item.display_order IS $$ Thứ tự hiển thị trong form đánh giá. $$;

COMMENT ON TABLE biosec.assessment IS $$ Bảng phiếu đánh giá hoặc audit. $$;
COMMENT ON COLUMN biosec.assessment.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.assessment.farm_id IS $$ Trại được đánh giá. $$;
COMMENT ON COLUMN biosec.assessment.template_id IS $$ Mẫu scorecard được sử dụng cho phiếu đánh giá này. $$;
COMMENT ON COLUMN biosec.assessment.assessment_type IS $$ Loại đánh giá: tự đánh giá, audit định kỳ, spot, blind... $$;
COMMENT ON COLUMN biosec.assessment.assessment_date IS $$ Thời điểm thực hiện đánh giá. $$;
COMMENT ON COLUMN biosec.assessment.performed_by_user_id IS $$ Người trực tiếp thực hiện đánh giá. $$;
COMMENT ON COLUMN biosec.assessment.performed_by_name_snapshot IS $$ Tên người đánh giá được chụp lại tại thời điểm đó để tránh thay đổi lịch sử khi user đổi tên. $$;
COMMENT ON COLUMN biosec.assessment.overall_score IS $$ Tổng điểm của phiếu sau khi tính toán. $$;
COMMENT ON COLUMN biosec.assessment.hardware_score IS $$ Điểm nhóm hạ tầng/phần cứng. $$;
COMMENT ON COLUMN biosec.assessment.process_score IS $$ Điểm nhóm quy trình. $$;
COMMENT ON COLUMN biosec.assessment.behavior_score IS $$ Điểm nhóm hành vi/kỷ luật. $$;
COMMENT ON COLUMN biosec.assessment.monitoring_score IS $$ Điểm nhóm giám sát/phát hiện. $$;
COMMENT ON COLUMN biosec.assessment.status IS $$ Trạng thái phiếu đánh giá: nháp, đã gửi, đã review, đã khóa. $$;
COMMENT ON COLUMN biosec.assessment.summary_note IS $$ Nhận xét tổng hợp của người đánh giá hoặc reviewer. $$;
COMMENT ON COLUMN biosec.assessment.trust_gap_basis_id IS $$ Tham chiếu tới phiếu audit đối chiếu để tính trust gap nếu có. $$;
COMMENT ON COLUMN biosec.assessment.created_at IS $$ Thời điểm hệ thống tạo bản ghi. $$;
COMMENT ON COLUMN biosec.assessment.updated_at IS $$ Thời điểm cập nhật gần nhất. $$;

COMMENT ON TABLE biosec.assessment_item_result IS $$ Bảng kết quả từng tiêu chí trong một phiếu đánh giá. $$;
COMMENT ON COLUMN biosec.assessment_item_result.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.assessment_item_result.assessment_id IS $$ Phiếu đánh giá chứa kết quả dòng này. $$;
COMMENT ON COLUMN biosec.assessment_item_result.scorecard_item_id IS $$ Tiêu chí scorecard được chấm. $$;
COMMENT ON COLUMN biosec.assessment_item_result.response_value_text IS $$ Giá trị trả lời dạng chữ hoặc lựa chọn. $$;
COMMENT ON COLUMN biosec.assessment_item_result.response_value_numeric IS $$ Giá trị trả lời dạng số nếu tiêu chí hỗ trợ. $$;
COMMENT ON COLUMN biosec.assessment_item_result.awarded_score IS $$ Điểm thực nhận của tiêu chí. $$;
COMMENT ON COLUMN biosec.assessment_item_result.is_non_compliant IS $$ Đánh dấu tiêu chí không đạt tuân thủ. $$;
COMMENT ON COLUMN biosec.assessment_item_result.note IS $$ Ghi chú hiện trường cho riêng tiêu chí này. $$;
COMMENT ON COLUMN biosec.assessment_item_result.area_id IS $$ Khu vực trong trại mà kết quả này gắn với. $$;
COMMENT ON COLUMN biosec.assessment_item_result.evidence_required IS $$ Tiêu chí này có bắt buộc đính kèm bằng chứng hay không. $$;

COMMENT ON TABLE biosec.assessment_attachment IS $$ Bảng liên kết file bằng chứng cho assessment. $$;
COMMENT ON COLUMN biosec.assessment_attachment.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.assessment_attachment.assessment_id IS $$ Phiếu đánh giá mà file này đính kèm. $$;
COMMENT ON COLUMN biosec.assessment_attachment.attachment_id IS $$ File bằng chứng cụ thể trong kho file. $$;
COMMENT ON COLUMN biosec.assessment_attachment.area_id IS $$ Khu vực liên quan tới file nếu có. $$;
COMMENT ON COLUMN biosec.assessment_attachment.caption IS $$ Chú thích giúp hiểu nhanh nội dung file. $$;

COMMENT ON TABLE biosec.killer_metric_definition IS $$ Bảng định nghĩa các killer metric của doanh nghiệp. $$;
COMMENT ON COLUMN biosec.killer_metric_definition.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.killer_metric_definition.code IS $$ Mã killer metric, ví dụ SWILL_FEED hoặc RED_LINE_BREACH. $$;
COMMENT ON COLUMN biosec.killer_metric_definition.name IS $$ Tên ngắn của killer metric. $$;
COMMENT ON COLUMN biosec.killer_metric_definition.description IS $$ Giải thích điều kiện nào được xem là vi phạm killer metric. $$;
COMMENT ON COLUMN biosec.killer_metric_definition.source_type IS $$ Nguồn có thể kích hoạt metric này: scorecard_item (chỉ từ đánh giá), field_report (chỉ từ hiện trường), both (cả hai). $$;
COMMENT ON COLUMN biosec.killer_metric_definition.severity_level IS $$ Mức độ nghiêm trọng chuẩn của killer metric. $$;
COMMENT ON COLUMN biosec.killer_metric_definition.default_case_priority IS $$ Mức ưu tiên case mặc định khi metric này xảy ra. $$;
COMMENT ON COLUMN biosec.killer_metric_definition.active_flag IS $$ Có còn dùng metric này trong vận hành hiện tại hay không. $$;

COMMENT ON TABLE biosec.killer_metric_event IS $$ Bảng sự kiện killer metric thực tế phát sinh. $$;
COMMENT ON COLUMN biosec.killer_metric_event.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.killer_metric_event.farm_id IS $$ Trại xảy ra sự kiện killer metric. $$;
COMMENT ON COLUMN biosec.killer_metric_event.area_id IS $$ Khu vực cụ thể nơi phát hiện sự kiện nếu xác định được. $$;
COMMENT ON COLUMN biosec.killer_metric_event.definition_id IS $$ Loại killer metric đã bị kích hoạt. $$;
COMMENT ON COLUMN biosec.killer_metric_event.event_at IS $$ Thời điểm phát hiện hoặc ghi nhận sự kiện. $$;
COMMENT ON COLUMN biosec.killer_metric_event.detected_by_user_id IS $$ Người phát hiện hoặc người ghi nhận sự kiện. $$;
COMMENT ON COLUMN biosec.killer_metric_event.source_type IS $$ Nguồn kích hoạt event: assessment (phát hiện qua chấm điểm) hoặc field_report (báo cáo hiện trường). $$;
COMMENT ON COLUMN biosec.killer_metric_event.source_assessment_item_result_id IS $$ FK tới assessment_item_result; bắt buộc khi source_type='assessment', NULL khi source_type='field_report'. $$;
COMMENT ON COLUMN biosec.killer_metric_event.summary IS $$ Mô tả ngắn nội dung vi phạm hoặc sự kiện. $$;
COMMENT ON COLUMN biosec.killer_metric_event.status IS $$ Trạng thái xử lý: open (mới phát hiện), under_review (đang xem xét), controlled (đã kiểm soát), closed (đã đóng), rejected (bác bỏ). $$;
COMMENT ON COLUMN biosec.killer_metric_event.required_case_flag IS $$ Đánh dấu bắt buộc phải mở case review cho sự kiện này. $$;

COMMENT ON TABLE biosec.trust_score_snapshot IS $$ Bảng snapshot điểm tin cậy giữa tự đánh giá và audit độc lập. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.farm_id IS $$ Trại được tính trust score. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.source_self_assessment_id IS $$ Phiếu tự đánh giá dùng làm vế tự khai. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.source_audit_assessment_id IS $$ Phiếu audit độc lập dùng để đối chiếu. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.trust_score IS $$ Điểm tin cậy 0-100; càng thấp càng chênh lệch lớn. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.absolute_gap_score IS $$ Độ lệch tuyệt đối giữa hai bộ điểm. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.severity_factor IS $$ Hệ số điều chỉnh nếu chênh lệch rơi vào tiêu chí nghiêm trọng. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.snapshot_date IS $$ Ngày chụp ảnh điểm tin cậy để làm báo cáo xu hướng. $$;
COMMENT ON COLUMN biosec.trust_score_snapshot.note IS $$ Ghi chú giải thích nguyên nhân chênh lệch nếu có. $$;

COMMENT ON TABLE biosec.risk_case IS $$ Bảng case rủi ro/sự cố cần chuyên gia xử lý. $$;
COMMENT ON COLUMN biosec.risk_case.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.risk_case.farm_id IS $$ Trại mà case này thuộc về. $$;
COMMENT ON COLUMN biosec.risk_case.area_id IS $$ Khu vực cụ thể liên quan tới case nếu xác định được. $$;
COMMENT ON COLUMN biosec.risk_case.case_no IS $$ Mã case duy nhất để truy vết xuyên suốt. $$;
COMMENT ON COLUMN biosec.risk_case.case_type IS $$ Loại case: điểm thấp, killer metric, near miss, incident... $$;
COMMENT ON COLUMN biosec.risk_case.title IS $$ Tiêu đề ngắn mô tả vấn đề. $$;
COMMENT ON COLUMN biosec.risk_case.summary IS $$ Tóm tắt bối cảnh và lý do mở case. $$;
COMMENT ON COLUMN biosec.risk_case.source_assessment_id IS $$ Phiếu đánh giá nguồn kích hoạt case nếu có. $$;
COMMENT ON COLUMN biosec.risk_case.source_killer_event_id IS $$ Sự kiện killer metric nguồn kích hoạt case nếu có. $$;
COMMENT ON COLUMN biosec.risk_case.source_scar_id IS $$ Scar lịch sử liên quan nếu case mở từ tri thức cũ. $$;
COMMENT ON COLUMN biosec.risk_case.priority IS $$ Mức ưu tiên xử lý P0-P3. $$;
COMMENT ON COLUMN biosec.risk_case.severity IS $$ Mức độ nghiêm trọng nghiệp vụ của case. $$;
COMMENT ON COLUMN biosec.risk_case.current_status IS $$ Trạng thái sống của case từ lúc mở tới lúc đóng. $$;
COMMENT ON COLUMN biosec.risk_case.assigned_expert_user_id IS $$ Chuyên gia chính chịu trách nhiệm xử lý case. $$;
COMMENT ON COLUMN biosec.risk_case.first_response_due_at IS $$ Hạn phản hồi đầu tiên theo SLA. $$;
COMMENT ON COLUMN biosec.risk_case.closure_due_at IS $$ Hạn kỳ vọng đóng case. $$;
COMMENT ON COLUMN biosec.risk_case.opened_at IS $$ Thời điểm mở case. $$;
COMMENT ON COLUMN biosec.risk_case.closed_at IS $$ Thời điểm đóng case. $$;

COMMENT ON TABLE biosec.case_participant IS $$ Bảng người tham gia hoặc theo dõi case. $$;
COMMENT ON COLUMN biosec.case_participant.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.case_participant.case_id IS $$ Case mà người này tham gia. $$;
COMMENT ON COLUMN biosec.case_participant.user_id IS $$ Người tham gia case. $$;
COMMENT ON COLUMN biosec.case_participant.role_in_case IS $$ Vai trò trong case: owner, reviewer, observer, farm_contact. $$;

COMMENT ON TABLE biosec.rca_record IS $$ Bảng bản phân tích nguyên nhân gốc (RCA). $$;
COMMENT ON COLUMN biosec.rca_record.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.rca_record.case_id IS $$ Case mà bản phân tích RCA này thuộc về. $$;
COMMENT ON COLUMN biosec.rca_record.method IS $$ Phương pháp RCA sử dụng, ví dụ 5 Why, Fishbone hoặc CAPA. $$;
COMMENT ON COLUMN biosec.rca_record.problem_statement IS $$ Phát biểu vấn đề cần giải quyết trong RCA. $$;
COMMENT ON COLUMN biosec.rca_record.impact_scope IS $$ Mô tả phạm vi ảnh hưởng: chuồng nào, đàn nào, quy mô nào. $$;
COMMENT ON COLUMN biosec.rca_record.direct_cause IS $$ Nguyên nhân trực tiếp nhìn thấy tại hiện trường. $$;
COMMENT ON COLUMN biosec.rca_record.system_cause IS $$ Nguyên nhân hệ thống/quản trị phía sau. $$;
COMMENT ON COLUMN biosec.rca_record.behavioral_cause IS $$ Nguyên nhân thuộc hành vi, kỷ luật, con người. $$;
COMMENT ON COLUMN biosec.rca_record.structural_cause IS $$ Nguyên nhân cấu trúc như layout, hạ tầng, tuyến luồng. $$;
COMMENT ON COLUMN biosec.rca_record.monitoring_cause IS $$ Nguyên nhân do phát hiện chậm hoặc giám sát yếu. $$;
COMMENT ON COLUMN biosec.rca_record.external_factor IS $$ Yếu tố ngoại sinh như điểm ô nhiễm xung quanh hoặc nhà thầu. $$;
COMMENT ON COLUMN biosec.rca_record.conclusion_confidence IS $$ Độ tin cậy của kết luận RCA. $$;
COMMENT ON COLUMN biosec.rca_record.analyzed_by_user_id IS $$ Chuyên gia thực hiện phân tích RCA. $$;
COMMENT ON COLUMN biosec.rca_record.analyzed_at IS $$ Thời điểm hoàn thành phân tích. $$;
COMMENT ON COLUMN biosec.rca_record.approved_by_user_id IS $$ Người duyệt RCA nếu có bước duyệt. $$;
COMMENT ON COLUMN biosec.rca_record.approved_at IS $$ Thời điểm RCA được duyệt. $$;

COMMENT ON TABLE biosec.rca_factor IS $$ Bảng các yếu tố nguyên nhân chi tiết thuộc một RCA. $$;
COMMENT ON COLUMN biosec.rca_factor.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.rca_factor.rca_record_id IS $$ Bản RCA mà yếu tố này thuộc về. $$;
COMMENT ON COLUMN biosec.rca_factor.factor_group IS $$ Nhóm nguyên nhân: people, process, place, equipment, environment. $$;
COMMENT ON COLUMN biosec.rca_factor.factor_text IS $$ Nội dung chi tiết của yếu tố nguyên nhân. $$;
COMMENT ON COLUMN biosec.rca_factor.confidence_level IS $$ Độ tin cậy của từng yếu tố nguyên nhân. $$;
COMMENT ON COLUMN biosec.rca_factor.is_primary IS $$ Đánh dấu đây có phải nguyên nhân chính hay không. $$;

COMMENT ON TABLE biosec.corrective_task IS $$ Bảng task khắc phục/phòng ngừa do chuyên gia tạo. $$;
COMMENT ON COLUMN biosec.corrective_task.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.corrective_task.case_id IS $$ Case nguồn sinh ra task này. $$;
COMMENT ON COLUMN biosec.corrective_task.task_no IS $$ Mã task duy nhất để quản trị và báo cáo. $$;
COMMENT ON COLUMN biosec.corrective_task.title IS $$ Tên công việc khắc phục/phòng ngừa. $$;
COMMENT ON COLUMN biosec.corrective_task.description IS $$ Mô tả chi tiết công việc cần làm. $$;
COMMENT ON COLUMN biosec.corrective_task.task_type IS $$ Loại task: corrective, preventive, inspection, training, capex. $$;
COMMENT ON COLUMN biosec.corrective_task.source_rca_id IS $$ Bản RCA làm căn cứ tạo task nếu có. $$;
COMMENT ON COLUMN biosec.corrective_task.area_id IS $$ Khu vực áp dụng công việc. $$;
COMMENT ON COLUMN biosec.corrective_task.priority IS $$ Mức ưu tiên xử lý P0-P3. $$;
COMMENT ON COLUMN biosec.corrective_task.status IS $$ Trạng thái task từ lúc tạo tới lúc đóng. $$;
COMMENT ON COLUMN biosec.corrective_task.sla_due_at IS $$ Hạn phải có phản hồi/tiếp nhận theo SLA. $$;
COMMENT ON COLUMN biosec.corrective_task.completion_due_at IS $$ Hạn hoàn thành thực tế của task. $$;
COMMENT ON COLUMN biosec.corrective_task.completion_criteria IS $$ Tiêu chí để xem task đạt yêu cầu. $$;
COMMENT ON COLUMN biosec.corrective_task.evidence_requirement IS $$ Yêu cầu loại bằng chứng phải nộp khi hoàn thành. $$;
COMMENT ON COLUMN biosec.corrective_task.created_by_user_id IS $$ Người tạo task. $$;
COMMENT ON COLUMN biosec.corrective_task.closed_by_user_id IS $$ Người đóng task sau khi hoàn tất review. $$;
COMMENT ON COLUMN biosec.corrective_task.closed_at IS $$ Thời điểm đóng task. $$;

COMMENT ON TABLE biosec.task_assignee IS $$ Bảng người được giao và vai trò trong task. $$;
COMMENT ON COLUMN biosec.task_assignee.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.task_assignee.task_id IS $$ Task được giao. $$;
COMMENT ON COLUMN biosec.task_assignee.user_id IS $$ Người được gán vào task. $$;
COMMENT ON COLUMN biosec.task_assignee.responsibility_type IS $$ Vai trò trong task: owner, support, approver. $$;
COMMENT ON COLUMN biosec.task_assignee.accepted_at IS $$ Thời điểm người được giao xác nhận nhận việc. $$;

COMMENT ON TABLE biosec.task_attachment IS $$ Bảng file bằng chứng gắn cho task. $$;
COMMENT ON COLUMN biosec.task_attachment.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.task_attachment.task_id IS $$ Task mà file này đính kèm. $$;
COMMENT ON COLUMN biosec.task_attachment.attachment_id IS $$ File bằng chứng thực tế. $$;
COMMENT ON COLUMN biosec.task_attachment.upload_stage IS $$ Giai đoạn chụp/nộp: trước, trong, sau hoặc lúc review. $$;
COMMENT ON COLUMN biosec.task_attachment.is_primary_evidence IS $$ Đánh dấu đây là bằng chứng chính để reviewer xem đầu tiên. $$;
COMMENT ON COLUMN biosec.task_attachment.caption IS $$ Chú thích ngắn cho file. $$;

COMMENT ON TABLE biosec.task_review IS $$ Bảng lịch sử review bằng chứng/kết quả task. $$;
COMMENT ON COLUMN biosec.task_review.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.task_review.task_id IS $$ Task được chuyên gia hoặc reviewer xem xét. $$;
COMMENT ON COLUMN biosec.task_review.reviewer_user_id IS $$ Người thực hiện review. $$;
COMMENT ON COLUMN biosec.task_review.review_result IS $$ Kết quả review: approved, rejected hoặc needs_rework. $$;
COMMENT ON COLUMN biosec.task_review.review_note IS $$ Nhận xét của reviewer, đặc biệt khi yêu cầu làm lại. $$;
COMMENT ON COLUMN biosec.task_review.reviewed_at IS $$ Thời điểm review được ghi nhận. $$;
COMMENT ON COLUMN biosec.task_review.next_action_due_at IS $$ Hạn hành động tiếp theo sau review nếu có. $$;

COMMENT ON TABLE biosec.task_comment IS $$ Bảng trao đổi/bình luận trong task. $$;
COMMENT ON COLUMN biosec.task_comment.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.task_comment.task_id IS $$ Task mà bình luận này thuộc về. $$;
COMMENT ON COLUMN biosec.task_comment.author_user_id IS $$ Người để lại bình luận. $$;
COMMENT ON COLUMN biosec.task_comment.comment_text IS $$ Nội dung trao đổi hoặc giải thích. $$;
COMMENT ON COLUMN biosec.task_comment.comment_type IS $$ Loại bình luận: ghi chú, lý do từ chối, escalation... $$;
COMMENT ON COLUMN biosec.task_comment.created_at IS $$ Thời điểm tạo bình luận. $$;

COMMENT ON TABLE biosec.scar_record IS $$ Bảng “vết sẹo” lịch sử và điểm tri thức trên sơ đồ trại. $$;
COMMENT ON COLUMN biosec.scar_record.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.scar_record.farm_id IS $$ Trại có “vết sẹo”/điểm tri thức này. $$;
COMMENT ON COLUMN biosec.scar_record.floorplan_version_id IS $$ Phiên bản sơ đồ dùng để gắn tọa độ scar cho đúng bối cảnh lịch sử. $$;
COMMENT ON COLUMN biosec.scar_record.area_id IS $$ Khu vực liên quan nếu scar gắn với một area chuẩn hóa. $$;
COMMENT ON COLUMN biosec.scar_record.scar_type IS $$ Loại scar: outbreak, hotspot, repeated_breach, near_miss, structural_flaw. $$;
COMMENT ON COLUMN biosec.scar_record.title IS $$ Tên ngắn để nhận biết scar. $$;
COMMENT ON COLUMN biosec.scar_record.description IS $$ Mô tả đầy đủ sự kiện, điểm yếu hoặc dấu tích lịch sử. $$;
COMMENT ON COLUMN biosec.scar_record.source_of_risk IS $$ Nguồn lây/nguy cơ nghi ngờ hoặc đã xác nhận. $$;
COMMENT ON COLUMN biosec.scar_record.confidence_level IS $$ Độ tin cậy của thông tin scar. $$;
COMMENT ON COLUMN biosec.scar_record.event_date IS $$ Ngày xảy ra sự kiện gốc của scar nếu biết. $$;
COMMENT ON COLUMN biosec.scar_record.x_percent IS $$ Tọa độ X trên sơ đồ khi không gắn theo area logic. $$;
COMMENT ON COLUMN biosec.scar_record.y_percent IS $$ Tọa độ Y trên sơ đồ. $$;
COMMENT ON COLUMN biosec.scar_record.status IS $$ Trạng thái scar: đang theo dõi, lưu trữ, lỗi thời... $$;
COMMENT ON COLUMN biosec.scar_record.recurrence_flag IS $$ Đánh dấu scar này có tái diễn hay không. $$;
COMMENT ON COLUMN biosec.scar_record.recurrence_count IS $$ Số lần hiện tượng tương tự đã lặp lại. $$;
COMMENT ON COLUMN biosec.scar_record.created_by_user_id IS $$ Người tạo scar ban đầu. $$;
COMMENT ON COLUMN biosec.scar_record.validated_by_user_id IS $$ Người xác nhận scar đủ tin cậy để dùng như tri thức. $$;
COMMENT ON COLUMN biosec.scar_record.validated_at IS $$ Thời điểm xác nhận scar. $$;

COMMENT ON TABLE biosec.scar_link IS $$ Bảng liên kết scar với case/task/evidence liên quan. $$;
COMMENT ON COLUMN biosec.scar_link.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.scar_link.scar_id IS $$ Scar trung tâm của liên kết. $$;
COMMENT ON COLUMN biosec.scar_link.linked_object_type IS $$ Loại đối tượng được liên kết tới scar, ví dụ case, task, assessment, attachment. $$;
COMMENT ON COLUMN biosec.scar_link.linked_object_id IS $$ ID của đối tượng liên kết. $$;
COMMENT ON COLUMN biosec.scar_link.link_reason IS $$ Lý do liên kết: nguồn gốc, bằng chứng, hành động khắc phục, theo dõi tiếp. $$;

COMMENT ON TABLE biosec.lesson_learned IS $$ Bảng bài học di sản đã được chuẩn hóa. $$;
COMMENT ON COLUMN biosec.lesson_learned.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.lesson_learned.lesson_no IS $$ Mã bài học duy nhất. $$;
COMMENT ON COLUMN biosec.lesson_learned.title IS $$ Tiêu đề ngắn của bài học. $$;
COMMENT ON COLUMN biosec.lesson_learned.problem_context IS $$ Bối cảnh/vấn đề ban đầu mà bài học này rút ra từ đó. $$;
COMMENT ON COLUMN biosec.lesson_learned.root_cause_summary IS $$ Tóm tắt nguyên nhân gốc đã được xác định. $$;
COMMENT ON COLUMN biosec.lesson_learned.action_summary IS $$ Tóm tắt giải pháp đã áp dụng. $$;
COMMENT ON COLUMN biosec.lesson_learned.outcome_summary IS $$ Tóm tắt kết quả thực tế sau khi áp dụng. $$;
COMMENT ON COLUMN biosec.lesson_learned.recurrence_observed IS $$ Sau khi xử lý có còn quan sát tái diễn hay không. $$;
COMMENT ON COLUMN biosec.lesson_learned.applicability_scope IS $$ Phạm vi nên áp dụng bài học này, ví dụ trại thuê, mùa mưa, trại nái. $$;
COMMENT ON COLUMN biosec.lesson_learned.confidence_level IS $$ Độ tin cậy của bài học di sản. $$;
COMMENT ON COLUMN biosec.lesson_learned.status IS $$ Trạng thái bài học: draft, validated, archived, obsolete. $$;
COMMENT ON COLUMN biosec.lesson_learned.confirmed_by_user_id IS $$ Người xác nhận bài học đã đủ cơ sở để phổ biến nội bộ. $$;
COMMENT ON COLUMN biosec.lesson_learned.confirmed_at IS $$ Thời điểm xác nhận bài học. $$;

COMMENT ON TABLE biosec.lesson_reference IS $$ Bảng nguồn tham chiếu làm căn cứ cho một lesson. $$;
COMMENT ON COLUMN biosec.lesson_reference.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.lesson_reference.lesson_id IS $$ Bài học mà nguồn tham chiếu này đóng góp vào. $$;
COMMENT ON COLUMN biosec.lesson_reference.reference_type IS $$ Loại nguồn tham chiếu: scar, case, task hoặc assessment. $$;
COMMENT ON COLUMN biosec.lesson_reference.reference_id IS $$ ID của nguồn tham chiếu. $$;
COMMENT ON COLUMN biosec.lesson_reference.contribution_note IS $$ Ghi chú nguồn này đóng góp điều gì cho bài học. $$;

COMMENT ON TABLE biosec.similarity_tag IS $$ Bảng thẻ phân loại để tìm lesson tương tự. $$;
COMMENT ON COLUMN biosec.similarity_tag.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.similarity_tag.lesson_id IS $$ Bài học được gắn thẻ. $$;
COMMENT ON COLUMN biosec.similarity_tag.tag_type IS $$ Loại thẻ để truy vấn, ví dụ farm_type, issue_type, route_type, season. $$;
COMMENT ON COLUMN biosec.similarity_tag.tag_value IS $$ Giá trị cụ thể của thẻ. $$;

COMMENT ON TABLE biosec.notification IS $$ Bảng thông báo hệ thống. $$;
COMMENT ON COLUMN biosec.notification.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.notification.recipient_user_id IS $$ Người nhận thông báo. $$;
COMMENT ON COLUMN biosec.notification.channel IS $$ Kênh gửi: in-app, email, webhook... $$;
COMMENT ON COLUMN biosec.notification.title IS $$ Tiêu đề thông báo. $$;
COMMENT ON COLUMN biosec.notification.body IS $$ Nội dung thông báo hiển thị cho người dùng. $$;
COMMENT ON COLUMN biosec.notification.entity_type IS $$ Loại đối tượng liên quan, ví dụ task, case, assessment. $$;
COMMENT ON COLUMN biosec.notification.entity_id IS $$ ID đối tượng liên quan để bấm mở đúng màn hình. $$;
COMMENT ON COLUMN biosec.notification.status IS $$ Trạng thái thông báo: queued, sent, read, failed. $$;
COMMENT ON COLUMN biosec.notification.sent_at IS $$ Thời điểm gửi ra kênh đích. $$;
COMMENT ON COLUMN biosec.notification.read_at IS $$ Thời điểm người dùng đọc thông báo. $$;

COMMENT ON TABLE biosec.audit_log IS $$ Bảng nhật ký truy vết thao tác hệ thống. $$;
COMMENT ON COLUMN biosec.audit_log.id IS $$ Khóa chính (PK) của bảng. $$;
COMMENT ON COLUMN biosec.audit_log.actor_user_id IS $$ Người thực hiện hành động được ghi log. $$;
COMMENT ON COLUMN biosec.audit_log.action IS $$ Tên hành động nghiệp vụ hoặc kỹ thuật đã xảy ra. $$;
COMMENT ON COLUMN biosec.audit_log.entity_type IS $$ Loại đối tượng bị tác động. $$;
COMMENT ON COLUMN biosec.audit_log.entity_id IS $$ ID đối tượng bị tác động. $$;
COMMENT ON COLUMN biosec.audit_log.before_json IS $$ Snapshot dữ liệu trước thay đổi để truy vết. $$;
COMMENT ON COLUMN biosec.audit_log.after_json IS $$ Snapshot dữ liệu sau thay đổi. $$;
COMMENT ON COLUMN biosec.audit_log.ip_address IS $$ Địa chỉ IP tại thời điểm thao tác nếu thu thập được. $$;
COMMENT ON COLUMN biosec.audit_log.user_agent IS $$ Thông tin thiết bị/trình duyệt đã thao tác. $$;
COMMENT ON COLUMN biosec.audit_log.occurred_at IS $$ Thời điểm hành động diễn ra. $$;

ALTER TABLE biosec.farm ADD CONSTRAINT fk_farm_region_id FOREIGN KEY (region_id) REFERENCES biosec.region(id) ON DELETE RESTRICT;
ALTER TABLE biosec.app_user ADD CONSTRAINT fk_app_user_region_id FOREIGN KEY (region_id) REFERENCES biosec.region(id) ON DELETE SET NULL;
ALTER TABLE biosec.app_user ADD CONSTRAINT fk_app_user_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE SET NULL;
ALTER TABLE biosec.region ADD CONSTRAINT fk_region_manager_user_id FOREIGN KEY (manager_user_id) REFERENCES biosec.app_user(id) ON DELETE SET NULL;
ALTER TABLE biosec.app_user_credential ADD CONSTRAINT fk_app_user_credential_user_id FOREIGN KEY (user_id) REFERENCES biosec.app_user(id) ON DELETE CASCADE;
ALTER TABLE biosec.app_refresh_token ADD CONSTRAINT fk_app_refresh_token_user_id FOREIGN KEY (user_id) REFERENCES biosec.app_user(id) ON DELETE CASCADE;
ALTER TABLE biosec.role_permission ADD CONSTRAINT fk_role_permission_role_id FOREIGN KEY (role_id) REFERENCES biosec.app_role(id) ON DELETE CASCADE;
ALTER TABLE biosec.role_permission ADD CONSTRAINT fk_role_permission_permission_id FOREIGN KEY (permission_id) REFERENCES biosec.app_permission(id) ON DELETE CASCADE;
ALTER TABLE biosec.user_role ADD CONSTRAINT fk_user_role_user_id FOREIGN KEY (user_id) REFERENCES biosec.app_user(id) ON DELETE CASCADE;
ALTER TABLE biosec.user_role ADD CONSTRAINT fk_user_role_role_id FOREIGN KEY (role_id) REFERENCES biosec.app_role(id) ON DELETE CASCADE;
ALTER TABLE biosec.user_role ADD CONSTRAINT fk_user_role_scope_region_id FOREIGN KEY (scope_region_id) REFERENCES biosec.region(id) ON DELETE SET NULL;
ALTER TABLE biosec.user_role ADD CONSTRAINT fk_user_role_scope_farm_id FOREIGN KEY (scope_farm_id) REFERENCES biosec.farm(id) ON DELETE SET NULL;
ALTER TABLE biosec.attachment ADD CONSTRAINT fk_attachment_uploaded_by_user_id FOREIGN KEY (uploaded_by_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;
ALTER TABLE biosec.attachment ADD CONSTRAINT fk_attachment_parent_attachment_id FOREIGN KEY (parent_attachment_id) REFERENCES biosec.attachment(id) ON DELETE SET NULL;
ALTER TABLE biosec.farm_area ADD CONSTRAINT fk_farm_area_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE CASCADE;
ALTER TABLE biosec.farm_area ADD CONSTRAINT fk_farm_area_parent_area_id FOREIGN KEY (parent_area_id) REFERENCES biosec.farm_area(id) ON DELETE SET NULL;
ALTER TABLE biosec.farm_route ADD CONSTRAINT fk_farm_route_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE CASCADE;
ALTER TABLE biosec.farm_route ADD CONSTRAINT fk_farm_route_from_area_id FOREIGN KEY (from_area_id) REFERENCES biosec.farm_area(id) ON DELETE RESTRICT;
ALTER TABLE biosec.farm_route ADD CONSTRAINT fk_farm_route_to_area_id FOREIGN KEY (to_area_id) REFERENCES biosec.farm_area(id) ON DELETE RESTRICT;
ALTER TABLE biosec.floorplan_version ADD CONSTRAINT fk_floorplan_version_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE CASCADE;
ALTER TABLE biosec.floorplan_version ADD CONSTRAINT fk_floorplan_version_plan_file_attachment_id FOREIGN KEY (plan_file_attachment_id) REFERENCES biosec.attachment(id) ON DELETE SET NULL;
ALTER TABLE biosec.floorplan_version ADD CONSTRAINT fk_floorplan_version_approved_by FOREIGN KEY (approved_by) REFERENCES biosec.app_user(id) ON DELETE SET NULL;
ALTER TABLE biosec.floorplan_marker ADD CONSTRAINT fk_floorplan_marker_floorplan_version_id FOREIGN KEY (floorplan_version_id) REFERENCES biosec.floorplan_version(id) ON DELETE CASCADE;
ALTER TABLE biosec.floorplan_marker ADD CONSTRAINT fk_floorplan_marker_area_id FOREIGN KEY (area_id) REFERENCES biosec.farm_area(id) ON DELETE SET NULL;
ALTER TABLE biosec.external_risk_point ADD CONSTRAINT fk_external_risk_point_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE CASCADE;
ALTER TABLE biosec.scorecard_section ADD CONSTRAINT fk_scorecard_section_template_id FOREIGN KEY (template_id) REFERENCES biosec.scorecard_template(id) ON DELETE CASCADE;
ALTER TABLE biosec.scorecard_item ADD CONSTRAINT fk_scorecard_item_section_id FOREIGN KEY (section_id) REFERENCES biosec.scorecard_section(id) ON DELETE CASCADE;
ALTER TABLE biosec.scorecard_item ADD CONSTRAINT fk_scorecard_item_killer_metric_definition_id FOREIGN KEY (killer_metric_definition_id) REFERENCES biosec.killer_metric_definition(id) ON DELETE SET NULL;
ALTER TABLE biosec.assessment ADD CONSTRAINT fk_assessment_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE RESTRICT;
ALTER TABLE biosec.assessment ADD CONSTRAINT fk_assessment_template_id FOREIGN KEY (template_id) REFERENCES biosec.scorecard_template(id) ON DELETE RESTRICT;
ALTER TABLE biosec.assessment ADD CONSTRAINT fk_assessment_performed_by_user_id FOREIGN KEY (performed_by_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;
ALTER TABLE biosec.assessment ADD CONSTRAINT fk_assessment_trust_gap_basis_id FOREIGN KEY (trust_gap_basis_id) REFERENCES biosec.assessment(id) ON DELETE SET NULL;
ALTER TABLE biosec.assessment_item_result ADD CONSTRAINT fk_assessment_item_result_assessment_id FOREIGN KEY (assessment_id) REFERENCES biosec.assessment(id) ON DELETE CASCADE;
ALTER TABLE biosec.assessment_item_result ADD CONSTRAINT fk_assessment_item_result_scorecard_item_id FOREIGN KEY (scorecard_item_id) REFERENCES biosec.scorecard_item(id) ON DELETE RESTRICT;
ALTER TABLE biosec.assessment_item_result ADD CONSTRAINT fk_assessment_item_result_area_id FOREIGN KEY (area_id) REFERENCES biosec.farm_area(id) ON DELETE SET NULL;
ALTER TABLE biosec.assessment_attachment ADD CONSTRAINT fk_assessment_attachment_assessment_id FOREIGN KEY (assessment_id) REFERENCES biosec.assessment(id) ON DELETE CASCADE;
ALTER TABLE biosec.assessment_attachment ADD CONSTRAINT fk_assessment_attachment_attachment_id FOREIGN KEY (attachment_id) REFERENCES biosec.attachment(id) ON DELETE CASCADE;
ALTER TABLE biosec.assessment_attachment ADD CONSTRAINT fk_assessment_attachment_area_id FOREIGN KEY (area_id) REFERENCES biosec.farm_area(id) ON DELETE SET NULL;
ALTER TABLE biosec.killer_metric_event ADD CONSTRAINT fk_killer_metric_event_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE RESTRICT;
ALTER TABLE biosec.killer_metric_event ADD CONSTRAINT fk_killer_metric_event_area_id FOREIGN KEY (area_id) REFERENCES biosec.farm_area(id) ON DELETE SET NULL;
ALTER TABLE biosec.killer_metric_event ADD CONSTRAINT fk_killer_metric_event_definition_id FOREIGN KEY (definition_id) REFERENCES biosec.killer_metric_definition(id) ON DELETE RESTRICT;
ALTER TABLE biosec.killer_metric_event ADD CONSTRAINT fk_killer_metric_event_detected_by_user_id FOREIGN KEY (detected_by_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;
ALTER TABLE biosec.killer_metric_event ADD CONSTRAINT fk_killer_metric_event_source_assessment_item_result_id FOREIGN KEY (source_assessment_item_result_id) REFERENCES biosec.assessment_item_result(id) ON DELETE SET NULL;
ALTER TABLE biosec.trust_score_snapshot ADD CONSTRAINT fk_trust_score_snapshot_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE RESTRICT;
ALTER TABLE biosec.trust_score_snapshot ADD CONSTRAINT fk_trust_score_snapshot_source_self_assessment_id FOREIGN KEY (source_self_assessment_id) REFERENCES biosec.assessment(id) ON DELETE RESTRICT;
ALTER TABLE biosec.trust_score_snapshot ADD CONSTRAINT fk_trust_score_snapshot_source_audit_assessment_id FOREIGN KEY (source_audit_assessment_id) REFERENCES biosec.assessment(id) ON DELETE RESTRICT;
ALTER TABLE biosec.risk_case ADD CONSTRAINT fk_risk_case_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE RESTRICT;
ALTER TABLE biosec.risk_case ADD CONSTRAINT fk_risk_case_area_id FOREIGN KEY (area_id) REFERENCES biosec.farm_area(id) ON DELETE SET NULL;
ALTER TABLE biosec.risk_case ADD CONSTRAINT fk_risk_case_source_assessment_id FOREIGN KEY (source_assessment_id) REFERENCES biosec.assessment(id) ON DELETE SET NULL;
ALTER TABLE biosec.risk_case ADD CONSTRAINT fk_risk_case_source_killer_event_id FOREIGN KEY (source_killer_event_id) REFERENCES biosec.killer_metric_event(id) ON DELETE SET NULL;
ALTER TABLE biosec.risk_case ADD CONSTRAINT fk_risk_case_assigned_expert_user_id FOREIGN KEY (assigned_expert_user_id) REFERENCES biosec.app_user(id) ON DELETE SET NULL;
ALTER TABLE biosec.case_participant ADD CONSTRAINT fk_case_participant_case_id FOREIGN KEY (case_id) REFERENCES biosec.risk_case(id) ON DELETE CASCADE;
ALTER TABLE biosec.case_participant ADD CONSTRAINT fk_case_participant_user_id FOREIGN KEY (user_id) REFERENCES biosec.app_user(id) ON DELETE CASCADE;
ALTER TABLE biosec.rca_record ADD CONSTRAINT fk_rca_record_case_id FOREIGN KEY (case_id) REFERENCES biosec.risk_case(id) ON DELETE CASCADE;
ALTER TABLE biosec.rca_record ADD CONSTRAINT fk_rca_record_analyzed_by_user_id FOREIGN KEY (analyzed_by_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;
ALTER TABLE biosec.rca_record ADD CONSTRAINT fk_rca_record_approved_by_user_id FOREIGN KEY (approved_by_user_id) REFERENCES biosec.app_user(id) ON DELETE SET NULL;
ALTER TABLE biosec.rca_factor ADD CONSTRAINT fk_rca_factor_rca_record_id FOREIGN KEY (rca_record_id) REFERENCES biosec.rca_record(id) ON DELETE CASCADE;
ALTER TABLE biosec.corrective_task ADD CONSTRAINT fk_corrective_task_case_id FOREIGN KEY (case_id) REFERENCES biosec.risk_case(id) ON DELETE CASCADE;
ALTER TABLE biosec.corrective_task ADD CONSTRAINT fk_corrective_task_source_rca_id FOREIGN KEY (source_rca_id) REFERENCES biosec.rca_record(id) ON DELETE SET NULL;
ALTER TABLE biosec.corrective_task ADD CONSTRAINT fk_corrective_task_area_id FOREIGN KEY (area_id) REFERENCES biosec.farm_area(id) ON DELETE SET NULL;
ALTER TABLE biosec.corrective_task ADD CONSTRAINT fk_corrective_task_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;
ALTER TABLE biosec.corrective_task ADD CONSTRAINT fk_corrective_task_closed_by_user_id FOREIGN KEY (closed_by_user_id) REFERENCES biosec.app_user(id) ON DELETE SET NULL;
ALTER TABLE biosec.task_assignee ADD CONSTRAINT fk_task_assignee_task_id FOREIGN KEY (task_id) REFERENCES biosec.corrective_task(id) ON DELETE CASCADE;
ALTER TABLE biosec.task_assignee ADD CONSTRAINT fk_task_assignee_user_id FOREIGN KEY (user_id) REFERENCES biosec.app_user(id) ON DELETE CASCADE;
ALTER TABLE biosec.task_attachment ADD CONSTRAINT fk_task_attachment_task_id FOREIGN KEY (task_id) REFERENCES biosec.corrective_task(id) ON DELETE CASCADE;
ALTER TABLE biosec.task_attachment ADD CONSTRAINT fk_task_attachment_attachment_id FOREIGN KEY (attachment_id) REFERENCES biosec.attachment(id) ON DELETE CASCADE;
ALTER TABLE biosec.task_review ADD CONSTRAINT fk_task_review_task_id FOREIGN KEY (task_id) REFERENCES biosec.corrective_task(id) ON DELETE CASCADE;
ALTER TABLE biosec.task_review ADD CONSTRAINT fk_task_review_reviewer_user_id FOREIGN KEY (reviewer_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;
ALTER TABLE biosec.task_comment ADD CONSTRAINT fk_task_comment_task_id FOREIGN KEY (task_id) REFERENCES biosec.corrective_task(id) ON DELETE CASCADE;
ALTER TABLE biosec.task_comment ADD CONSTRAINT fk_task_comment_author_user_id FOREIGN KEY (author_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;
ALTER TABLE biosec.scar_record ADD CONSTRAINT fk_scar_record_farm_id FOREIGN KEY (farm_id) REFERENCES biosec.farm(id) ON DELETE RESTRICT;
ALTER TABLE biosec.scar_record ADD CONSTRAINT fk_scar_record_floorplan_version_id FOREIGN KEY (floorplan_version_id) REFERENCES biosec.floorplan_version(id) ON DELETE SET NULL;
ALTER TABLE biosec.scar_record ADD CONSTRAINT fk_scar_record_area_id FOREIGN KEY (area_id) REFERENCES biosec.farm_area(id) ON DELETE SET NULL;
ALTER TABLE biosec.scar_record ADD CONSTRAINT fk_scar_record_created_by_user_id FOREIGN KEY (created_by_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;
ALTER TABLE biosec.scar_record ADD CONSTRAINT fk_scar_record_validated_by_user_id FOREIGN KEY (validated_by_user_id) REFERENCES biosec.app_user(id) ON DELETE SET NULL;
ALTER TABLE biosec.risk_case ADD CONSTRAINT fk_risk_case_source_scar_id FOREIGN KEY (source_scar_id) REFERENCES biosec.scar_record(id) ON DELETE SET NULL;
ALTER TABLE biosec.scar_link ADD CONSTRAINT fk_scar_link_scar_id FOREIGN KEY (scar_id) REFERENCES biosec.scar_record(id) ON DELETE CASCADE;
ALTER TABLE biosec.lesson_learned ADD CONSTRAINT fk_lesson_learned_confirmed_by_user_id FOREIGN KEY (confirmed_by_user_id) REFERENCES biosec.app_user(id) ON DELETE SET NULL;
ALTER TABLE biosec.lesson_reference ADD CONSTRAINT fk_lesson_reference_lesson_id FOREIGN KEY (lesson_id) REFERENCES biosec.lesson_learned(id) ON DELETE CASCADE;
ALTER TABLE biosec.similarity_tag ADD CONSTRAINT fk_similarity_tag_lesson_id FOREIGN KEY (lesson_id) REFERENCES biosec.lesson_learned(id) ON DELETE CASCADE;
ALTER TABLE biosec.notification ADD CONSTRAINT fk_notification_recipient_user_id FOREIGN KEY (recipient_user_id) REFERENCES biosec.app_user(id) ON DELETE CASCADE;
ALTER TABLE biosec.audit_log ADD CONSTRAINT fk_audit_log_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES biosec.app_user(id) ON DELETE RESTRICT;

ALTER TABLE biosec.region ADD CONSTRAINT uq_region_code UNIQUE (code);
ALTER TABLE biosec.app_user ADD CONSTRAINT uq_app_user_username UNIQUE (username);
ALTER TABLE biosec.app_user_credential ADD CONSTRAINT uq_app_user_credential_user_id UNIQUE (user_id);
ALTER TABLE biosec.app_role ADD CONSTRAINT uq_app_role_code UNIQUE (code);
ALTER TABLE biosec.app_permission ADD CONSTRAINT uq_app_permission_code UNIQUE (code);
ALTER TABLE biosec.role_permission ADD CONSTRAINT uq_role_permission_role_id_permission_id UNIQUE (role_id, permission_id);
ALTER TABLE biosec.farm ADD CONSTRAINT uq_farm_code UNIQUE (code);
ALTER TABLE biosec.farm_area ADD CONSTRAINT uq_farm_area_farm_id_code UNIQUE (farm_id, code);
ALTER TABLE biosec.floorplan_version ADD CONSTRAINT uq_floorplan_version_farm_id_version_no UNIQUE (farm_id, version_no);
ALTER TABLE biosec.scorecard_template ADD CONSTRAINT uq_scorecard_template_code_version_no UNIQUE (code, version_no);
ALTER TABLE biosec.scorecard_section ADD CONSTRAINT uq_scorecard_section_template_id_code UNIQUE (template_id, code);
ALTER TABLE biosec.scorecard_item ADD CONSTRAINT uq_scorecard_item_section_id_code UNIQUE (section_id, code);
ALTER TABLE biosec.assessment_attachment ADD CONSTRAINT uq_assessment_attachment_assessment_id_attachment_id UNIQUE (assessment_id, attachment_id);
ALTER TABLE biosec.killer_metric_definition ADD CONSTRAINT uq_killer_metric_definition_code UNIQUE (code);
ALTER TABLE biosec.trust_score_snapshot ADD CONSTRAINT uq_trust_score_snapshot_farm_id_source_self_assessment_17388dd7 UNIQUE (farm_id, source_self_assessment_id, source_audit_assessment_id);
ALTER TABLE biosec.risk_case ADD CONSTRAINT uq_risk_case_case_no UNIQUE (case_no);
ALTER TABLE biosec.case_participant ADD CONSTRAINT uq_case_participant_case_id_user_id_role_in_case UNIQUE (case_id, user_id, role_in_case);
ALTER TABLE biosec.corrective_task ADD CONSTRAINT uq_corrective_task_task_no UNIQUE (task_no);
ALTER TABLE biosec.task_assignee ADD CONSTRAINT uq_task_assignee_task_id_user_id_responsibility_type UNIQUE (task_id, user_id, responsibility_type);
ALTER TABLE biosec.task_attachment ADD CONSTRAINT uq_task_attachment_task_id_attachment_id UNIQUE (task_id, attachment_id);
ALTER TABLE biosec.scar_link ADD CONSTRAINT uq_scar_link_scar_id_linked_object_type_linked_object_id UNIQUE (scar_id, linked_object_type, linked_object_id);
ALTER TABLE biosec.lesson_learned ADD CONSTRAINT uq_lesson_learned_lesson_no UNIQUE (lesson_no);
ALTER TABLE biosec.lesson_reference ADD CONSTRAINT uq_lesson_reference_lesson_id_reference_type_reference_id UNIQUE (lesson_id, reference_type, reference_id);
ALTER TABLE biosec.similarity_tag ADD CONSTRAINT uq_similarity_tag_lesson_id_tag_type_tag_value UNIQUE (lesson_id, tag_type, tag_value);
ALTER TABLE biosec.attachment ADD CONSTRAINT uq_attachment_storage_bucket_object_key UNIQUE (storage_bucket, object_key);
ALTER TABLE biosec.lookup_code ADD CONSTRAINT uq_lookup_code_group_code_code UNIQUE (group_code, code);

CREATE OR REPLACE FUNCTION biosec.set_updated_at()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := now();
    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION biosec.set_updated_at() IS 'Trigger chung để tự cập nhật updated_at khi bản ghi thay đổi.';

CREATE TRIGGER trg_region_set_updated_at BEFORE UPDATE ON biosec.region FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_farm_set_updated_at BEFORE UPDATE ON biosec.farm FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_app_user_set_updated_at BEFORE UPDATE ON biosec.app_user FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_lookup_code_set_updated_at BEFORE UPDATE ON biosec.lookup_code FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_farm_area_set_updated_at BEFORE UPDATE ON biosec.farm_area FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_assessment_set_updated_at BEFORE UPDATE ON biosec.assessment FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_app_user_credential_set_updated_at BEFORE UPDATE ON biosec.app_user_credential FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_farm_route_set_updated_at BEFORE UPDATE ON biosec.farm_route FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_floorplan_version_set_updated_at BEFORE UPDATE ON biosec.floorplan_version FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_floorplan_marker_set_updated_at BEFORE UPDATE ON biosec.floorplan_marker FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_external_risk_point_set_updated_at BEFORE UPDATE ON biosec.external_risk_point FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_scorecard_template_set_updated_at BEFORE UPDATE ON biosec.scorecard_template FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_killer_metric_event_set_updated_at BEFORE UPDATE ON biosec.killer_metric_event FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_risk_case_set_updated_at BEFORE UPDATE ON biosec.risk_case FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_corrective_task_set_updated_at BEFORE UPDATE ON biosec.corrective_task FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_scar_record_set_updated_at BEFORE UPDATE ON biosec.scar_record FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();
CREATE TRIGGER trg_lesson_learned_set_updated_at BEFORE UPDATE ON biosec.lesson_learned FOR EACH ROW EXECUTE FUNCTION biosec.set_updated_at();

CREATE OR REPLACE FUNCTION biosec.fn_enforce_task_close_requires_review()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'closed' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM biosec.task_review tr
            WHERE tr.task_id = NEW.id
              AND tr.review_result = 'approved'
        ) THEN
            RAISE EXCEPTION 'Không thể đóng task % vì chưa có review approved.', NEW.task_no;
        END IF;

        IF NEW.closed_at IS NULL THEN
            NEW.closed_at := now();
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION biosec.fn_enforce_task_close_requires_review() IS 'Ngăn đóng corrective_task khi chưa có ít nhất một task_review ở trạng thái approved.';

CREATE TRIGGER trg_corrective_task_close_guard BEFORE INSERT OR UPDATE OF status, closed_at ON biosec.corrective_task FOR EACH ROW EXECUTE FUNCTION biosec.fn_enforce_task_close_requires_review();

CREATE OR REPLACE FUNCTION biosec.fn_enforce_killer_event_close_requires_case()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'closed' THEN
        IF NOT EXISTS (
            SELECT 1
            FROM biosec.risk_case rc
            WHERE rc.source_killer_event_id = NEW.id
        ) THEN
            RAISE EXCEPTION 'Không thể đóng killer_metric_event % vì chưa có risk_case liên kết.', NEW.id;
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION biosec.fn_enforce_killer_event_close_requires_case() IS 'Ngăn đóng killer_metric_event khi chưa có ít nhất một risk_case được mở từ sự kiện này.';

CREATE TRIGGER trg_killer_metric_event_close_guard BEFORE INSERT OR UPDATE OF status ON biosec.killer_metric_event FOR EACH ROW EXECUTE FUNCTION biosec.fn_enforce_killer_event_close_requires_case();

CREATE OR REPLACE FUNCTION biosec.fn_enforce_validated_lesson_requires_support()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.status = 'validated' THEN
        IF NEW.confirmed_by_user_id IS NULL OR NEW.confirmed_at IS NULL THEN
            RAISE EXCEPTION 'lesson_learned ở trạng thái validated phải có confirmed_by_user_id và confirmed_at.';
        END IF;

        IF NOT EXISTS (
            SELECT 1
            FROM biosec.lesson_reference lr
            WHERE lr.lesson_id = NEW.id
        ) THEN
            RAISE EXCEPTION 'lesson_learned ở trạng thái validated phải có ít nhất một lesson_reference.';
        END IF;
    END IF;

    RETURN NEW;
END;
$$;

COMMENT ON FUNCTION biosec.fn_enforce_validated_lesson_requires_support() IS 'Ngăn validate bài học di sản khi chưa có người xác nhận và chưa có nguồn tham chiếu.';

CREATE TRIGGER trg_lesson_learned_validate_guard BEFORE INSERT OR UPDATE OF status, confirmed_by_user_id, confirmed_at ON biosec.lesson_learned FOR EACH ROW EXECUTE FUNCTION biosec.fn_enforce_validated_lesson_requires_support();

CREATE INDEX idx_assessment_farm_date ON biosec.assessment (farm_id, assessment_date DESC);
CREATE INDEX idx_risk_case_farm_status_priority ON biosec.risk_case (farm_id, current_status, priority);
CREATE INDEX idx_corrective_task_case_status_due ON biosec.corrective_task (case_id, status, completion_due_at);
CREATE INDEX idx_scar_record_farm_area_event_date ON biosec.scar_record (farm_id, area_id, event_date DESC);
CREATE INDEX idx_trust_score_snapshot_farm_date ON biosec.trust_score_snapshot (farm_id, snapshot_date DESC);
CREATE INDEX idx_audit_log_entity_date ON biosec.audit_log (entity_type, entity_id, occurred_at DESC);
CREATE INDEX idx_notification_recipient_status ON biosec.notification (recipient_user_id, status, sent_at DESC);
CREATE INDEX idx_farm_region_id ON biosec.farm (region_id);
CREATE INDEX idx_app_user_region_id ON biosec.app_user (region_id);
CREATE INDEX idx_app_user_farm_id ON biosec.app_user (farm_id);
CREATE INDEX idx_region_manager_user_id ON biosec.region (manager_user_id);
CREATE INDEX idx_role_permission_role_id ON biosec.role_permission (role_id);
CREATE INDEX idx_role_permission_permission_id ON biosec.role_permission (permission_id);
CREATE INDEX idx_user_role_user_id ON biosec.user_role (user_id);
CREATE INDEX idx_user_role_role_id ON biosec.user_role (role_id);
CREATE INDEX idx_user_role_scope_region_id ON biosec.user_role (scope_region_id);
CREATE INDEX idx_user_role_scope_farm_id ON biosec.user_role (scope_farm_id);
CREATE INDEX idx_attachment_uploaded_by_user_id ON biosec.attachment (uploaded_by_user_id);
CREATE INDEX idx_attachment_parent_attachment_id ON biosec.attachment (parent_attachment_id);
CREATE INDEX idx_farm_area_farm_id ON biosec.farm_area (farm_id);
CREATE INDEX idx_farm_area_parent_area_id ON biosec.farm_area (parent_area_id);
CREATE INDEX idx_farm_route_farm_id ON biosec.farm_route (farm_id);
CREATE INDEX idx_farm_route_from_area_id ON biosec.farm_route (from_area_id);
CREATE INDEX idx_farm_route_to_area_id ON biosec.farm_route (to_area_id);
CREATE INDEX idx_floorplan_version_farm_id ON biosec.floorplan_version (farm_id);
CREATE INDEX idx_floorplan_version_plan_file_attachment_id ON biosec.floorplan_version (plan_file_attachment_id);
CREATE INDEX idx_floorplan_version_approved_by ON biosec.floorplan_version (approved_by);
CREATE INDEX idx_floorplan_marker_floorplan_version_id ON biosec.floorplan_marker (floorplan_version_id);
CREATE INDEX idx_floorplan_marker_area_id ON biosec.floorplan_marker (area_id);
CREATE INDEX idx_external_risk_point_farm_id ON biosec.external_risk_point (farm_id);
CREATE INDEX idx_scorecard_section_template_id ON biosec.scorecard_section (template_id);
CREATE INDEX idx_scorecard_item_section_id ON biosec.scorecard_item (section_id);
CREATE INDEX idx_assessment_farm_id ON biosec.assessment (farm_id);
CREATE INDEX idx_assessment_template_id ON biosec.assessment (template_id);
CREATE INDEX idx_assessment_performed_by_user_id ON biosec.assessment (performed_by_user_id);
CREATE INDEX idx_assessment_trust_gap_basis_id ON biosec.assessment (trust_gap_basis_id);
CREATE INDEX idx_assessment_item_result_assessment_id ON biosec.assessment_item_result (assessment_id);
CREATE INDEX idx_assessment_item_result_scorecard_item_id ON biosec.assessment_item_result (scorecard_item_id);
CREATE INDEX idx_assessment_item_result_area_id ON biosec.assessment_item_result (area_id);
CREATE INDEX idx_assessment_attachment_assessment_id ON biosec.assessment_attachment (assessment_id);
CREATE INDEX idx_assessment_attachment_attachment_id ON biosec.assessment_attachment (attachment_id);
CREATE INDEX idx_assessment_attachment_area_id ON biosec.assessment_attachment (area_id);
CREATE INDEX idx_killer_metric_event_farm_id ON biosec.killer_metric_event (farm_id);
CREATE INDEX idx_killer_metric_event_area_id ON biosec.killer_metric_event (area_id);
CREATE INDEX idx_killer_metric_event_definition_id ON biosec.killer_metric_event (definition_id);
CREATE INDEX idx_killer_metric_event_detected_by_user_id ON biosec.killer_metric_event (detected_by_user_id);
CREATE INDEX idx_trust_score_snapshot_farm_id ON biosec.trust_score_snapshot (farm_id);
CREATE INDEX idx_trust_score_snapshot_source_self_assessment_id ON biosec.trust_score_snapshot (source_self_assessment_id);
CREATE INDEX idx_trust_score_snapshot_source_audit_assessment_id ON biosec.trust_score_snapshot (source_audit_assessment_id);
CREATE INDEX idx_risk_case_farm_id ON biosec.risk_case (farm_id);
CREATE INDEX idx_risk_case_area_id ON biosec.risk_case (area_id);
CREATE INDEX idx_risk_case_source_assessment_id ON biosec.risk_case (source_assessment_id);
CREATE INDEX idx_risk_case_source_killer_event_id ON biosec.risk_case (source_killer_event_id);
CREATE INDEX idx_risk_case_assigned_expert_user_id ON biosec.risk_case (assigned_expert_user_id);
CREATE INDEX idx_case_participant_case_id ON biosec.case_participant (case_id);
CREATE INDEX idx_case_participant_user_id ON biosec.case_participant (user_id);
CREATE INDEX idx_rca_record_case_id ON biosec.rca_record (case_id);
CREATE INDEX idx_rca_record_analyzed_by_user_id ON biosec.rca_record (analyzed_by_user_id);
CREATE INDEX idx_rca_record_approved_by_user_id ON biosec.rca_record (approved_by_user_id);
CREATE INDEX idx_rca_factor_rca_record_id ON biosec.rca_factor (rca_record_id);
CREATE INDEX idx_corrective_task_case_id ON biosec.corrective_task (case_id);
CREATE INDEX idx_corrective_task_source_rca_id ON biosec.corrective_task (source_rca_id);
CREATE INDEX idx_corrective_task_area_id ON biosec.corrective_task (area_id);
CREATE INDEX idx_corrective_task_created_by_user_id ON biosec.corrective_task (created_by_user_id);
CREATE INDEX idx_corrective_task_closed_by_user_id ON biosec.corrective_task (closed_by_user_id);
CREATE INDEX idx_task_assignee_task_id ON biosec.task_assignee (task_id);
CREATE INDEX idx_task_assignee_user_id ON biosec.task_assignee (user_id);
CREATE INDEX idx_task_attachment_task_id ON biosec.task_attachment (task_id);
CREATE INDEX idx_task_attachment_attachment_id ON biosec.task_attachment (attachment_id);
CREATE INDEX idx_task_review_task_id ON biosec.task_review (task_id);
CREATE INDEX idx_task_review_reviewer_user_id ON biosec.task_review (reviewer_user_id);
CREATE INDEX idx_task_comment_task_id ON biosec.task_comment (task_id);
CREATE INDEX idx_task_comment_author_user_id ON biosec.task_comment (author_user_id);
CREATE INDEX idx_scar_record_farm_id ON biosec.scar_record (farm_id);
CREATE INDEX idx_scar_record_floorplan_version_id ON biosec.scar_record (floorplan_version_id);
CREATE INDEX idx_scar_record_area_id ON biosec.scar_record (area_id);
CREATE INDEX idx_scar_record_created_by_user_id ON biosec.scar_record (created_by_user_id);
CREATE INDEX idx_scar_record_validated_by_user_id ON biosec.scar_record (validated_by_user_id);
CREATE INDEX idx_risk_case_source_scar_id ON biosec.risk_case (source_scar_id);
CREATE INDEX idx_scar_link_scar_id ON biosec.scar_link (scar_id);
CREATE INDEX idx_lesson_learned_confirmed_by_user_id ON biosec.lesson_learned (confirmed_by_user_id);
CREATE INDEX idx_lesson_reference_lesson_id ON biosec.lesson_reference (lesson_id);
CREATE INDEX idx_similarity_tag_lesson_id ON biosec.similarity_tag (lesson_id);
CREATE INDEX idx_notification_recipient_user_id ON biosec.notification (recipient_user_id);
CREATE INDEX idx_audit_log_actor_user_id ON biosec.audit_log (actor_user_id);
CREATE UNIQUE INDEX uq_app_user_email_ci ON biosec.app_user (lower(email)) WHERE email IS NOT NULL;
CREATE INDEX gin_risk_case_search ON biosec.risk_case USING GIN (to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(summary,'')));
CREATE INDEX gin_rca_record_search ON biosec.rca_record USING GIN (to_tsvector('simple', coalesce(problem_statement,'') || ' ' || coalesce(direct_cause,'') || ' ' || coalesce(system_cause,'')));
CREATE INDEX gin_lesson_learned_search ON biosec.lesson_learned USING GIN (to_tsvector('simple', coalesce(title,'') || ' ' || coalesce(problem_context,'') || ' ' || coalesce(root_cause_summary,'')));
CREATE INDEX gin_audit_log_after_json ON biosec.audit_log USING GIN (after_json);
CREATE INDEX gin_floorplan_marker_metadata ON biosec.floorplan_marker USING GIN (metadata_json);

-- Composite indexes cho các query phổ biến nhất
CREATE INDEX idx_risk_case_queue ON biosec.risk_case (farm_id, current_status, priority) WHERE archived_at IS NULL;
CREATE INDEX idx_corrective_task_listing ON biosec.corrective_task (case_id, status, priority) WHERE archived_at IS NULL;
CREATE INDEX idx_assessment_listing ON biosec.assessment (farm_id, assessment_type, status);
CREATE INDEX idx_scar_record_farm_event ON biosec.scar_record (farm_id, area_id, event_date DESC) WHERE archived_at IS NULL;
CREATE INDEX idx_trust_score_trend ON biosec.trust_score_snapshot (farm_id, snapshot_date DESC);
CREATE INDEX idx_attachment_not_archived ON biosec.attachment (uploaded_at DESC) WHERE archived_at IS NULL;
CREATE INDEX idx_app_refresh_token_user_id ON biosec.app_refresh_token (user_id);
CREATE INDEX idx_app_refresh_token_expires ON biosec.app_refresh_token (expires_at) WHERE revoked_at IS NULL;

-- Ghi chú triển khai:
-- 1) `case_no`, `task_no`, `lesson_no` đang để application/service layer sinh theo quy ước doanh nghiệp.
-- 2) Nếu sau này cần PostGIS hoặc TimescaleDB, nên thêm migration riêng để tránh khóa chặt môi trường MVP.
-- 3) Soft delete đã được triển khai bằng cột `archived_at` cho các bảng dữ liệu điều tra (risk_case, corrective_task, scar_record, lesson_learned, attachment).
-- 4) Optimistic locking đã được triển khai bằng cột `version` cho các bảng có state machine (assessment, risk_case, corrective_task, killer_metric_event).
-- 5) Xác thực được hỗ trợ qua bảng `app_user_credential` và `app_refresh_token`.
-- 6) Application layer phải validate referential integrity cho polymorphic FK trong `scar_link` và `lesson_reference`.

