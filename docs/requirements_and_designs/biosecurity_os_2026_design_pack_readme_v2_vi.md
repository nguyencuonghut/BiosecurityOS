# BIOSECURITY OS 2026 - Design Pack (bản chú thích tiếng Việt)

Bộ tài liệu này là phiên bản đã được bổ sung **ghi chú tiếng Việt rõ nghĩa**, đặc biệt cho:
- các **cột trong bảng ERD**,
- các **field/viết tắt trong API**,
- các **nhãn cột trong wireframe**.

## 1. Requirements đã hiệu chỉnh
- `biosecurity_os_2026_requirements_v3_vi.md`
- Vai trò: tài liệu nghiệp vụ, mục tiêu, business rule, phạm vi MVP

## 2. ERD mức logic có chú thích cột
- `biosecurity_os_2026_erd_v2_vi_chu_thich.md`
- Vai trò: mô hình dữ liệu, giải thích bằng tiếng Việt cho từng bảng và từng cột quan trọng
- Đây là file nên ưu tiên review với BA, backend và QA

## 3. API contracts có chú giải field
- `biosecurity_os_2026_api_contracts_v2_vi.md`
- Vai trò: khung endpoint, payload, workflow và permission matrix
- Đã bổ sung phần giải thích `*_id`, `status`, `scope`, `R/C/U/D/A`...

## 4. Module map và wireframes có chú giải nhãn
- `biosecurity_os_2026_wireframes_modules_v2_vi.md`
- Vai trò: information architecture, module boundaries, cấu trúc màn hình web/mobile
- Đã bổ sung gợi ý Việt hóa tên cột/nhãn khi đưa sang Figma

## Trình tự sử dụng đề xuất
1. Chốt requirements.
2. Review ERD đã chú thích với backend + BA.
3. Chốt enum, status code, priority code và lookup code.
4. Review API contract.
5. Chuyển wireframe sang Figma và Việt hóa label cuối cùng.
6. Tách backlog MVP theo module.

## Gợi ý khi review
- Nếu đội backend cần thống nhất tên field, hãy lấy **ERD annotated** làm chuẩn.
- Nếu đội frontend cần tên cột tiếng Việt, hãy lấy phần gợi ý trong **wireframes annotated** làm đầu vào.
- Nếu đội BA cần diễn giải nghiệp vụ cho dev mới, hãy dùng **requirements + ERD annotated** song song.

