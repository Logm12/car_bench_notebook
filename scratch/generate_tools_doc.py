import sys
import os
import json
from pathlib import Path

# Add paths to sys.path
workspace_dir = Path("e:/VinAI/VSG/car-bench-ijcai-vsf")
third_party_car_bench = workspace_dir / "third_party" / "car-bench"
sys.path.insert(0, str(third_party_car_bench))
sys.path.insert(0, str(workspace_dir / "src"))

from car_bench.envs.car_voice_assistant.tools import ALL_TOOLS

# Create the output markdown content
md_lines = []
md_lines.append("# CAR-bench Agent Tool Documentation\n")
md_lines.append("This document provides a detailed description of each tool available to the CAR-bench voice assistant agent, including name, description, and parameter specifications.\n")

# Define importance groups
CRITICAL_TOOLS = {
    # Yêu cầu xác nhận từ người dùng
    "open_close_trunk_door",
    "send_email",
    "set_head_lights_high_beams",
    # Khử mơ hồ & Cấu hình cá nhân
    "get_user_preferences",
    # Kiểm tra an toàn trước khi hành động
    "get_weather",
    # Quản lý kế hoạch phức tạp
    "planning_tool"
}

HIGH_PRIORITY_TOOLS = {
    # Thay đổi trạng thái dẫn đường
    "set_new_navigation",
    "navigation_add_one_waypoint",
    "navigation_replace_one_waypoint",
    "navigation_replace_final_destination",
    "navigation_delete_one_waypoint",
    "navigation_delete_final_destination",
    "delete_current_navigation",
    "get_current_navigation_state",
    "get_routes_from_start_to_destination",
    # Ràng buộc điều khiển tương hỗ (Interdependencies)
    "open_close_sunroof",
    "open_close_sunshade",
    "open_close_window",
    "set_air_conditioning",
    "set_window_defrost",
    "set_fog_lights",
    "set_head_lights_low_beams",
    # Hành động kết thúc hội thoại
    "call_phone_by_number"
}

# Group tools by importance
importance_groups = {
    "1. Quan trọng nhất (Bắt buộc tuân thủ, Xác nhận & An toàn)": [],
    "2. Quan trọng hơn (Quy định tương hỗ xe & Dẫn đường nâng cao)": [],
    "3. Quan trọng (Truy vấn thông tin xe/môi trường & Tiện ích hỗ trợ)": []
}

for t in ALL_TOOLS:
    info = t.get_info()
    func = info.get("function", {})
    name = func.get("name", "Unknown")
    description = func.get("description", "No description provided.")
    parameters = func.get("parameters", {})
    
    if name in CRITICAL_TOOLS:
        group_key = "1. Quan trọng nhất (Bắt buộc tuân thủ, Xác nhận & An toàn)"
    elif name in HIGH_PRIORITY_TOOLS:
        group_key = "2. Quan trọng hơn (Quy định tương hỗ xe & Dẫn đường nâng cao)"
    else:
        group_key = "3. Quan trọng (Truy vấn thông tin xe/môi trường & Tiện ích hỗ trợ)"
        
    importance_groups[group_key].append((name, description, parameters))

# Write grouped tools
for category in sorted(importance_groups.keys()):
    md_lines.append(f"## {category}\n")
    # Explain the group importance rationale
    if "Quan trọng nhất" in category:
        md_lines.append("> [!IMPORTANT]\n> **LÝ DO:** Các tool này bắt buộc phải đi kèm với xác nhận người dùng (`REQUIRES_CONFIRMATION`), thực hiện khử mơ hồ mức độ ưu tiên cao (`get_user_preferences`), kiểm tra an toàn thời tiết bắt buộc (`get_weather`) hoặc quản lý kế hoạch. Vi phạm quy trình của nhóm này sẽ bị trừ toàn bộ điểm (Reward = 0.0) ngay lập tức.\n")
    elif "Quan trọng hơn" in category:
        md_lines.append("> [!TIP]\n> **LÝ DO:** Các tool điều khiển có độ phức tạp cao, đòi hỏi phải gọi tuần tự (như mở sunshade trước khi mở sunroof) hoặc tự động thay đổi các trạng thái liên đới (defrost/AC chỉnh fan speed/airflow direction). Nhóm này cũng gồm các điều khiển navigation động.\n")
    else:
        md_lines.append("> [!NOTE]\n> **LÝ DO:** Các tool truy vấn thông tin cơ bản, tính toán số học, hoặc thay đổi các thông số thoải mái (ambient lights, seat heating level) ít bị ràng buộc bởi các điều kiện chính sách khắt khe của hệ thống.\n")

    for name, desc, params in sorted(importance_groups[category], key=lambda x: x[0]):
        md_lines.append(f"### `{name}`\n")
        md_lines.append(f"**Description:** {desc}\n")
        
        properties = params.get("properties", {})
        required = params.get("required", [])
        
        if properties:
            md_lines.append("**Parameters:**\n")
            md_lines.append("| Name | Type | Required | Description | Details |")
            md_lines.append("| --- | --- | --- | --- | --- |")
            for prop_name, prop_info in properties.items():
                if not isinstance(prop_info, dict):
                    continue
                p_type = prop_info.get("type", "unknown")
                p_required = "Yes" if prop_name in required else "No"
                p_desc = prop_info.get("description", "").replace("\n", " ")
                
                # Check for enum or other details
                details = []
                if "enum" in prop_info:
                    details.append(f"Enum: {', '.join([repr(x) for x in prop_info['enum']])}")
                if "minimum" in prop_info:
                    details.append(f"Min: {prop_info['minimum']}")
                if "maximum" in prop_info:
                    details.append(f"Max: {prop_info['maximum']}")
                
                details_str = "; ".join(details) if details else "-"
                md_lines.append(f"| `{prop_name}` | `{p_type}` | {p_required} | {p_desc} | {details_str} |")
            md_lines.append("")
        else:
            md_lines.append("**Parameters:** None\n")
        md_lines.append("---\n")

reports_dir = workspace_dir / "reports"
reports_dir.mkdir(parents=True, exist_ok=True)
output_file = reports_dir / "tool_documentation.md"

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))

print(f"Documentation generated successfully at {output_file}")

