import re
from pathlib import Path

# Paths
workspace_dir = Path("e:/VinAI/VSG/car-bench-ijcai-vsf")
eng_file = workspace_dir / "reports" / "vehicle_tools_and_rules.md"
output_file = workspace_dir / "reports" / "vehicle_tools_and_rules_vi.md"

# Priority groups
priority_1 = ["get_user_preferences", "get_weather", "planning_tool", "open_close_trunk_door", "send_email", "set_head_lights_high_beams"]
priority_2 = [
    "set_new_navigation", "navigation_add_one_waypoint", "navigation_replace_one_waypoint", 
    "navigation_replace_final_destination", "navigation_delete_one_waypoint", "navigation_delete_final_destination", 
    "delete_current_navigation", "get_current_navigation_state", "get_routes_from_start_to_destination", 
    "open_close_sunroof", "open_close_sunshade", "open_close_window", "set_air_conditioning", 
    "set_window_defrost", "set_fog_lights", "set_head_lights_low_beams", "call_phone_by_number"
]

# Read English file
with open(eng_file, "r", encoding="utf-8") as f:
    content = f.read()

# Extract tools: Name and Description
tool_pattern = re.compile(r"\| \d+ \| `([^`]+)` \| ([^\n|]+) \|")
tools = tool_pattern.findall(content)

# Translation dictionary for tools
translations = {
    "calculate_charging_soc_by_time": "Thông tin sạc: Tính toán mức sạc (SoC) đạt được khi sạc xe trong khoảng thời gian nhất định.",
    "calculate_charging_time_by_soc": "Thông tin sạc: Tính toán thời gian sạc cần thiết để sạc từ mức pin hiện tại đến mức pin mục tiêu.",
    "calculate_datetime": "Tiện ích thời gian: Cộng thêm khoảng thời gian chỉ định vào mốc thời gian gốc và trả về thời gian mới.",
    "calculate_math": "Tiện ích toán học: Tính toán kết quả của một biểu thức toán học dạng chuỗi.",
    "call_phone_by_number": "Công cụ điện thoại: Thực hiện cuộc gọi tới số điện thoại được chỉ định (Hội thoại kết thúc ngay sau đó).",
    "convert_route_distance_and_time": "Công cụ hỗ trợ: Quy đổi khoảng cách (km) thành thời gian di chuyển (phút) tương ứng trên tuyến đường và ngược lại.",
    "delete_current_navigation": "Điều khiển dẫn đường: Xóa tuyến dẫn đường hiện tại, chuyển trạng thái hệ thống dẫn đường thành không hoạt động.",
    "get_ambient_light_status_and_color": "Thông tin xe: Lấy trạng thái hoạt động và màu sắc hiện tại của đèn nội thất (ambient light).",
    "get_car_color": "Thông tin xe: Lấy màu sơn ngoại thất của xe.",
    "get_charging_specs_and_status": "Thông tin sạc: Lấy thông số sạc và trạng thái sạc hiện tại của xe (dung lượng pin, công suất sạc AC/DC tối đa, mức pin, phạm vi di chuyển còn lại).",
    "get_climate_settings": "Thông tin xe: Lấy cài đặt hệ thống điều hòa (tốc độ quạt, hướng gió, trạng thái AC, chế độ tuần hoàn, sấy kính).",
    "get_contact_id_by_contact_name": "Thông tin danh bạ: Tra cứu ID liên hệ dựa theo họ và/hoặc tên được chỉ định.",
    "get_contact_information": "Thông tin danh bạ: Lấy chi tiết thông tin liên hệ (tên, số điện thoại, email) dựa theo danh sách ID.",
    "get_current_navigation_state": "Thông tin dẫn đường: Lấy trạng thái hệ thống dẫn đường hiện tại (tuyến đường đã chọn, các điểm trung gian waypoint).",
    "get_distance_by_soc": "Thông tin sạc: Lấy phạm vi khoảng cách có thể lái được tương ứng từ mức pin ban đầu đến mức pin đích.",
    "get_entries_from_calendar": "Thông tin lịch trình: Lấy danh sách các cuộc hẹn, sự kiện trong lịch trình cá nhân của ngày hiện tại.",
    "get_exterior_lights_status": "Thông tin xe: Lấy trạng thái hệ thống chiếu sáng ngoài xe (đèn chiếu gần low-beam, chiếu xa high-beam, đèn sương mù).",
    "get_fuel_information": "Thông tin xe: Lấy thông tin về loại nhiên liệu, mức tiêu thụ nhiên liệu và lượng nhiên liệu còn lại.",
    "get_location_id_by_location_name": "Thông tin địa điểm: Lấy ID địa điểm tương ứng với tên thành phố/địa danh được chỉ định.",
    "get_reading_lights_status": "Thông tin xe: Lấy trạng thái hoạt động của các đèn đọc sách trong cabin xe.",
    "get_routes_from_start_to_destination": "Thông tin tuyến đường: Tìm kiếm tuyến đường nhanh nhất (và các tuyến thay thế) giữa điểm xuất phát và điểm đích.",
    "get_seat_heating_level": "Thông tin xe: Lấy mức độ sưởi ghế hiện tại ở các khu vực ghế ngồi trong xe.",
    "get_seats_occupancy": "Thông tin xe: Lấy trạng thái có người ngồi của các ghế trong cabin.",
    "get_steering_wheel_heating_level": "Thông tin xe: Lấy mức sưởi hiện tại của vô lăng.",
    "get_sunroof_and_sunshade_position": "Thông tin xe: Lấy vị trí phần trăm đóng/mở hiện tại của cửa sổ trời (sunroof) và tấm che nắng (sunshade).",
    "get_temperature_inside_car": "Thông tin xe: Lấy nhiệt độ hiện tại ở các phân vùng ghế ngồi trong xe.",
    "get_trunk_door_position": "Thông tin xe: Lấy trạng thái vị trí đóng/mở của cửa cốp xe.",
    "get_user_preferences": "Cấu hình cá nhân: Truy vấn sở thích đã thiết lập của người dùng theo từng danh mục chức năng.",
    "get_vehicle_window_positions": "Thông tin xe: Lấy vị trí phần trăm mở hiện tại của toàn bộ các cửa sổ xe.",
    "get_weather": "Thông tin thời tiết: Lấy thông tin dự báo thời tiết tại địa điểm và mốc giờ chỉ định.",
    "navigation_add_one_waypoint": "Điều khiển dẫn đường: Thêm một điểm trung gian (waypoint) vào tuyến đường hiện tại.",
    "navigation_delete_destination": "Điều khiển dẫn đường: Xóa điểm đến cuối cùng của tuyến dẫn đường hiện tại (điểm dừng kế cuối sẽ trở thành đích mới).",
    "navigation_delete_waypoint": "Điều khiển dẫn đường: Xóa một điểm trung gian được chỉ định ra khỏi lộ trình.",
    "navigation_replace_final_destination": "Điều khiển dẫn đường: Thay thế điểm đến cuối cùng bằng điểm đến mới.",
    "navigation_replace_one_waypoint": "Điều khiển dẫn đường: Thay thế một điểm trung gian trong lộ trình bằng một điểm mới.",
    "open_close_sunroof": "Điều khiển xe: Mở hoặc đóng cửa sổ trời (sunroof) theo tỷ lệ phần trăm (0 - 100%).",
    "open_close_sunshade": "Điều khiển xe: Mở hoặc đóng tấm che nắng (sunshade) theo tỷ lệ phần trăm (0 - 100%).",
    "open_close_trunk_door": "YÊU CẦU XÁC NHẬN, Điều khiển xe: Mở hoặc đóng cửa cốp xe.",
    "open_close_window": "Điều khiển xe: Nâng hoặc hạ cửa sổ được chỉ định (hoặc tất cả các cửa) theo phần trăm.",
    "planning_tool": "Công cụ lập kế hoạch: Tạo lập, cập nhật và quản lý kế hoạch thực thi đa bước cho các yêu cầu phức tạp.",
    "search_poi_along_the_route": "Tìm kiếm POI: Tìm kiếm điểm ưa thích (POI) theo phân loại dọc theo tuyến lộ trình di chuyển.",
    "search_poi_at_location": "Tìm kiếm POI: Tìm kiếm điểm ưa thích (POI) theo phân loại xung quanh một địa điểm cụ thể.",
    "send_email": "YÊU CẦU XÁC NHẬN, Công cụ email: Soạn và gửi email tới các địa chỉ người nhận chỉ định.",
    "set_air_circulation": "Điều khiển điều hòa: Thiết lập chế độ lấy gió của điều hòa (gió ngoài, gió trong cabin, hoặc tự động).",
    "set_air_conditioning": "Điều khiển điều hòa: Bật hoặc tắt hệ thống làm mát AC của xe.",
    "set_ambient_lights": "Điều khiển xe: Bật (kèm màu sắc lựa chọn) hoặc tắt hệ thống đèn viền trang trí nội thất xe.",
    "set_climate_temperature": "Điều khiển điều hòa: Thiết lập mức nhiệt độ điều hòa (độ C) cho vùng ghế được chỉ định.",
    "set_fan_airflow_direction": "Điều khiển điều hòa: Thiết lập hướng luồng gió của quạt gió điều hòa cabin.",
    "set_fan_speed": "Điều khiển điều hòa: Thiết lập mức tốc độ quạt gió điều hòa cabin (từ 0 đến 5).",
    "set_fog_lights": "Điều khiển xe: Bật hoặc tắt đèn sương mù ngoại thất.",
    "set_head_lights_high_beams": "YÊU CẦU XÁC NHẬN, Điều khiển xe: Bật hoặc tắt đèn pha chiếu xa (pha cao) ngoại thất.",
    "set_head_lights_low_beams": "Điều khiển xe: Bật hoặc tắt đèn chiếu gần (cốt) ngoại thất.",
    "set_new_navigation": "Điều khiển dẫn đường: Thiết lập và bắt đầu một tuyến lộ trình dẫn đường hoàn toàn mới.",
    "set_reading_light": "Điều khiển xe: Bật hoặc tắt đèn đọc sách tại vị trí ghế chỉ định.",
    "set_seat_heating": "Điều khiển điều hòa: Thiết lập mức độ sưởi ghế cho khu vực ghế chỉ chỉ định.",
    "set_steering_wheel_heating": "Điều khiển điều hòa: Thiết lập mức độ sưởi cho vô lăng xe.",
    "set_window_defrost": "Điều khiển điều hòa: Kích hoạt sấy kính trước/sau hoặc toàn bộ các kính để khử sương mù.",
    "think": "Hỗ trợ suy nghĩ: Ghi chú lại luồng lập luận nội bộ của Agent để giải quyết bài toán phức tạp.",
}

# Group tools by priority
grouped_tools = {
    "1": [], # Quan trọng nhất
    "2": [], # Quan trọng hơn
    "3": []  # Quan trọng
}

for name, raw_desc in tools:
    desc = translations.get(name, raw_desc)
    if name in priority_1:
        grouped_tools["1"].append((name, desc))
    elif name in priority_2:
        grouped_tools["2"].append((name, desc))
    else:
        grouped_tools["3"].append((name, desc))

md_vi = []
md_vi.append("# Tài Liệu Tra Cứu Công Cụ và Quy Tắc Ràng Buộc Xe CAR-bench\n")
md_vi.append("Tài liệu này chứa danh sách đầy đủ 58 công cụ được sắp xếp theo mức độ quan trọng quyết định điểm số Pass^3, đi kèm các quy tắc ràng buộc cứng (operational interdependencies) của hệ thống xe.\n")

md_vi.append("## 1. Danh Sách 58 Công Cụ (Sắp xếp theo thứ tự ưu tiên giảm dần)\n")

# Writing priority table
md_vi.append("### Nhóm 1: Quan trọng nhất (Quyết định an toàn, Khử mơ hồ & Xác nhận người dùng)")
md_vi.append("> [!IMPORTANT]\n> Nhóm này chứa các công cụ bắt buộc phải tuân thủ quy trình xác nhận (`REQUIRES_CONFIRMATION`), các công cụ kiểm tra thời tiết an toàn bắt buộc trước khi thực thi hoặc công cụ truy xuất cấu hình cá nhân để giải quyết mơ hồ ở mức ưu tiên cao nhất. Vi phạm quy trình của nhóm này sẽ trực tiếp bị phạt điểm về 0.0.\n")
md_vi.append("| # | Tên Công Cụ | Chức Năng Chi Tiết | Mức Độ |")
md_vi.append("|---|---|---|---|")
idx = 1
for name, desc in sorted(grouped_tools["1"], key=lambda x: x[0]):
    md_vi.append(f"| {idx} | `{name}` | {desc} | **Quan trọng nhất** |")
    idx += 1

md_vi.append("\n### Nhóm 2: Quan trọng hơn (Ràng buộc tương hỗ của xe & Dẫn đường nâng cao)")
md_vi.append("> [!TIP]\n> Nhóm này chứa các công cụ điều khiển chịu ảnh hưởng trực tiếp bởi các ràng buộc tương hỗ giữa các hệ thống (ví dụ: liên kết sunroof/sunshade, AC/window, defrost cabin). Đồng thời chứa các công cụ cập nhật lộ trình dẫn đường động.\n")
md_vi.append("| # | Tên Công Cụ | Chức Năng Chi Tiết | Mức Độ |")
md_vi.append("|---|---|---|---|")
for name, desc in sorted(grouped_tools["2"], key=lambda x: x[0]):
    md_vi.append(f"| {idx} | `{name}` | {desc} | **Quan trọng hơn** |")
    idx += 1

md_vi.append("\n### Nhóm 3: Quan trọng (Truy vấn thông tin thông thường & Hỗ trợ tiện ích)")
md_vi.append("> [!NOTE]\n> Nhóm này chứa các công cụ hỗ trợ truy vấn trạng thái cơ bản hoặc điều khiển các tính năng thoải mái (sưởi vô lăng, đèn đọc sách, màu ambient) ít bị ràng buộc bởi các điều kiện chính sách khắt khe của BTC.\n")
md_vi.append("| # | Tên Công Cụ | Chức Năng Chi Tiết | Mức Độ |")
md_vi.append("|---|---|---|---|")
for name, desc in sorted(grouped_tools["3"], key=lambda x: x[0]):
    md_vi.append(f"| {idx} | `{name}` | {desc} | **Quan trọng** |")
    idx += 1

md_vi.append("\n## 2. Quy Tắc Ràng Buộc Cứng và Hệ Thống Tương Hỗ Trên Xe\n")

rules_vi = [
    "### Ràng Buộc Điều Khiển Cửa Sổ và Tấm Che Nắng",
    "- **Liên kết Sunroof và Sunshade**: Cửa sổ trời (`open_close_sunroof`) chỉ có thể mở được nếu tấm che nắng (`open_close_sunshade`) đã được mở hoàn toàn (100%) hoặc đang được mở song song. Nếu không, hoạt động mở cửa sổ trời sẽ bị hệ thống chặn lại.",
    "- **Mâu thuẫn trạng thái điều hòa AC và Cửa sổ**: Nếu người dùng yêu cầu mở bất kỳ cửa sổ nào lớn hơn 25% (vị trí tuyệt đối) trong khi hệ thống điều hòa AC đang BẬT, Agent bắt buộc phải cảnh báo người dùng về việc tiêu tốn năng lượng không hiệu quả và yêu cầu người dùng xác nhận trước khi gọi tool.",
    "",
    "### Ràng Buộc Điều Kiện Thời Tiết An Toàn",
    "- **Kiểm tra thời tiết cho Sunroof**: Trước khi mở cửa sổ trời, Agent bắt buộc phải gọi tool `get_weather` để kiểm tra thời tiết tại vị trí hiện tại. Nếu thời tiết không phải là một trong các trạng thái ['sunny' (nắng), 'cloudy' (nhiều mây), 'partly_cloudy' (nắng nhẹ/mây bán phần)], Agent bắt buộc phải hỏi xin ý kiến xác nhận của người dùng trước khi thực thi.",
    "- **Kiểm tra thời tiết cho Đèn Sương Mù**: Trước khi bật đèn sương mù, Agent bắt buộc phải gọi tool `get_weather` kiểm tra thời tiết. Nếu thời tiết không phải là một trong các trạng thái ['cloudy_and_thunderstorm' (giông bão), 'cloudy_and_hail' (mưa đá)], Agent bắt buộc phải xin xác nhận từ người dùng.",
    "- **Yêu cầu bắt buộc**: Trong cả hai trường hợp trên, việc gọi tool `get_weather` và phân tích dữ liệu trả về phải được thực hiện trước khi bất kỳ lệnh điều khiển nào được phát đi.",
    "",
    "### Ràng Buộc Hệ Thống Điều Hòa Không Khí",
    "- **Tự động điều chỉnh khi sấy defrost kính**: Khi kích hoạt sấy kính trước hoặc tất cả các kính (`set_window_defrost`), Agent phải tự động thực hiện đồng thời các hành động sau trong cùng bước gọi tool:",
    "  - Đưa tốc độ quạt gió (`set_fan_speed`) lên mức tối thiểu là 2 nếu tốc độ hiện tại dưới mức này.",
    "  - Đặt hướng gió thổi (`set_fan_airflow_direction`) về phía kính trước (WINDSHIELD) nếu hướng gió hiện tại chưa bao gồm WINDSHIELD.",
    "  - Bật hệ thống điều hòa làm mát AC (`set_air_conditioning`) nếu AC đang tắt.",
    "- **Tự động điều chỉnh khi bật điều hòa AC**: Khi kích hoạt điều hòa AC sang chế độ ON, Agent phải tự động:",
    "  - Đóng tất cả các cửa sổ nếu chúng đang mở hơn 20% (vị trí tuyệt đối).",
    "  - Thiết lập tốc độ quạt gió về mức 1 nếu tốc độ hiện tại đang bằng 0.",
    "- **Cảnh báo chênh lệch nhiệt độ vùng ghế**: Nếu người dùng thiết lập nhiệt độ điều hòa cho một phân vùng ghế duy nhất, và mức chênh lệch nhiệt độ sau đó giữa vùng ghế này với các vùng ghế khác vượt quá 3 độ C, Agent phải thông báo rõ ràng cho người dùng biết về sự chênh lệch này.",
    "",
    "### Ràng Buộc Hệ Thống Chiếu Sáng",
    "- **Liên kết Đèn Sương Mù và Đèn Pha**: Khi kích hoạt bật đèn sương mù, Agent bắt buộc phải tự động:",
    "  - Kiểm tra xem đèn chiếu gần (low-beams) đã bật chưa, nếu chưa bật thì phải kích hoạt bật lên.",
    "  - Kiểm tra xem đèn chiếu xa (high-beams) đã tắt chưa, nếu chưa tắt thì phải tắt đi.",
    "- **Ràng buộc loại trừ lẫn nhau**: Đèn chiếu xa (high-beams) tuyệt đối không được phép kích hoạt nếu đèn sương mù đang bật, vì sự kết hợp này sẽ làm giảm nghiêm trọng tầm nhìn của lái xe trong điều kiện sương mù.",
    "",
    "### Quy Định Hệ Thống Dẫn Đường Lộ Trình",
    "- **Điểm xuất phát bắt buộc**: Điểm xuất phát của toàn bộ tuyến lộ trình dẫn đường luôn luôn phải khớp với vị trí hiện tại của chiếc xe.",
    "- **Chỉnh sửa dẫn đường động**: Các công cụ thêm, xóa hoặc thay thế một điểm waypoint/điểm đích chỉ được sử dụng khi hệ thống dẫn đường đã hoạt động và đang có sẵn một tuyến đường được thiết lập. Nếu dẫn đường chưa được kích hoạt, Agent phải gọi lệnh thiết lập dẫn đường mới.",
    "- **Chỉnh sửa tuần tự**: Khi cần chỉnh sửa nhiều điểm waypoint, Agent bắt buộc phải thực hiện các cuộc gọi tool thêm/xóa/thay thế một cách tuần tự (sequential), tuyệt đối không gọi song song (in parallel) để tránh xung đột chỉ mục thứ tự điểm dừng.",
    "- **Yêu cầu tuyến tối thiểu**: Một lộ trình dẫn đường hợp lệ phải có ít nhất điểm xuất phát và một điểm đích. Điểm đích cuối cùng không thể bị xóa nếu tuyến đường không có bất kỳ điểm dừng trung gian nào.",
    "- **Thông báo trạm thu phí**: Nếu tuyến đường được lựa chọn hoặc một phân đoạn của tuyến đường có chứa đường thu phí (toll road), Agent bắt buộc phải thông báo cho người dùng biết.",
    "- **Lựa chọn tuyến đường mặc định**: Khi người dùng yêu cầu lộ trình đi qua nhiều điểm dừng nhưng không nói rõ tiêu chí chọn đường, Agent phải tự động chọn tuyến đường nhanh nhất cho từng phân đoạn. Đồng thời phải thông báo cho lái xe biết lựa chọn này và hỏi xem họ có muốn biết thông tin về các tuyến đường thay thế khác hay không.",
    "",
    "### Quy Định Hệ Thống Lịch Trình & Giao Tiếp",
    "- **Giới hạn thời gian của lịch trình**: Các truy vấn liên quan đến lịch trình calendar chỉ được phép giới hạn trong ngày hiện tại. Agent không được truy vấn lịch trình của các ngày khác.",
    "- **Tìm kiếm ID danh bạ**: ID liên hệ của một người chỉ có thể được tìm kiếm bằng cách sử dụng chính xác họ và/hoặc tên của người đó.",
    "- **Ngắt hội thoại khi thực hiện cuộc gọi**: Khi Agent thực hiện lệnh gọi điện thoại (`call_phone_by_number`), phiên hội thoại giọng nói giữa Agent và người dùng sẽ tự động kết thúc ngay lập tức sau lệnh gọi đó."
]

md_vi.extend(rules_vi)

with open(output_file, "w", encoding="utf-8") as f:
    f.write("\n".join(md_vi))

print(f"File written successfully to {output_file} containing sorted and translated tools.")
