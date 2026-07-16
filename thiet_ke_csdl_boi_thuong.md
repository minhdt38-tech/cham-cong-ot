# Thiết kế CSDL — Module Bồi thường, Hỗ trợ

Tài liệu tổng hợp toàn bộ cấu trúc dữ liệu đã thống nhất, thay thế cho 4 bảng hiện tại (`bt_projects`, `bt_owners`, `bt_parcels`, `bt_records`, `bt_status_config`).

**Cơ sở tham chiếu:** ISO 19152 (LADM — mô hình Chủ thể/Quyền/Đơn vị không gian), Thông tư 09/2024/TT-BTNMT (cấu trúc CSDL đất đai quốc gia), Nghị định 88/2024/NĐ-CP (bồi thường, hỗ trợ, tái định cư).

---

## Tình trạng triển khai (cập nhật 2026-07-14)

**Đã xong — Lớp cơ sở dữ liệu (14 bảng bên dưới).** Đã thêm vào `server.py`, đã kiểm tra: tạo bảng sạch không lỗi, chạy lại nhiều lần (giả lập server khởi động lại) không lỗi, không đụng tới dữ liệu chấm công/tài liệu hiện có.

**Đã xong — Module 1: Chủ thể + Nhân khẩu (đầy đủ, dùng được).** API thêm/sửa/xoá cho cả 2 bảng (`/api/bt/parties`, `/api/bt/parties/:id/members`, `/api/bt/members/:id`), và giao diện quản lý mới trong `boi-thuong.html` (mục "👤 Chủ thể / Hộ dân" ở sidebar — độc lập với dự án, vì 1 người có thể liên quan nhiều dự án). Đã kiểm tra kỹ: toàn bộ câu lệnh SQL chạy đúng trên CSDL thật, toàn bộ hàm JS (thêm/sửa/xoá/tìm kiếm/mở form) chạy đúng qua bài test mô phỏng dữ liệu thật. Lưu ý: môi trường làm việc hiện tại gặp lỗi kỹ thuật khiến không tự bấm thử trực tiếp trên trình duyệt được (đã ghi chú kỹ thuật riêng) — khuyến nghị anh mở thử trang này 1 lần sau khi deploy để xác nhận trực quan trước khi dùng thật.

**Đã xong — Module 2a: Thửa đất (gốc + theo dự án + đồng sở hữu).** API cho `bt_parcel_master` (tìm trùng theo số tờ/số thửa), `bt_parcels` (thêm/sửa/xoá theo dự án, tự tạo/liên kết thửa gốc), `bt_parcel_owners` (đồng sở hữu nhiều chủ thể theo tỷ lệ). Giao diện: tab "🗺️ Thửa đất" mới trong từng dự án — form có gợi ý trùng thửa gốc (nếu số tờ/số thửa khớp thửa đã có ở dự án khác thì cảnh báo, cho chọn liên kết hoặc tạo mới), phần chọn nhiều chủ sở hữu kèm vai trò/tỷ lệ. Đã kiểm tra kỹ như Module 1 (SQL chạy đúng + JS chạy đúng qua bài test mô phỏng: tải danh sách, thêm mới, sửa có sẵn đồng sở hữu + liên kết thửa gốc, gỡ liên kết, thêm/xoá đồng sở hữu, lưu đúng dữ liệu). Xoá thửa sẽ tự dọn `bt_parcel_owners`/`bt_asset_parcels` liên quan (vì SQLite không tự cascade — xem ghi chú kỹ thuật).

**Đã xong — Module 2b: Bản đồ (`bt_maps` + `bt_map_parcels` + `bt_map_files`).** API tạo/sửa/xoá bản đồ theo dự án, gắn nhiều thửa đất (tự gợi ý liên kết với thửa gốc theo số tờ/số thửa, giống cơ chế cảnh báo trùng của module Thửa đất), và tải lên/tải xuống/xoá nhiều tệp đính kèm cho mỗi bản đồ (dùng chung cơ chế lưu trữ R2/local đã có sẵn cho module Tài liệu). Giao diện: tab "🗂️ Bản đồ" mới trong từng dự án. Vì bản đồ cần được lưu (có `id`) trước khi có thể gắn thửa/tệp, form chia 2 bước trong cùng 1 hộp thoại: nhập thông tin cơ bản → bấm "Lưu bản đồ" → phần "Thửa đất trên bản đồ" và "Tệp đính kèm" mới hiện ra để thao tác tiếp. Xoá bản đồ sẽ tự dọn `bt_map_parcels`, `bt_map_files`, và xoá luôn tệp vật lý (R2 hoặc local) — cùng nguyên tắc thủ công-cascade như các module trước. Đã kiểm tra kỹ như các module trước (SQL chạy đúng qua bài test mô phỏng đầy đủ các thao tác CRUD + JS chạy đúng qua bài test mô phỏng toàn bộ luồng: tạo mới, liên kết thửa gốc, gỡ liên kết, tải tệp, xoá tệp, xoá bản đồ).

**Đã xong — Module 3: Tài sản trên đất (`bt_assets` + `bt_asset_parcels`).** API tạo/sửa/xoá tài sản (chỉ dữ liệu kiểm đếm khách quan — nhóm tài sản, loại cụ thể, chủ tài sản, đơn vị tính, số lượng, thời điểm hình thành, tình trạng pháp lý, ngày/người kiểm đếm), gắn với nhiều thửa đất trong cùng dự án (danh sách tài sản của 1 dự án được xác định qua các thửa đất nó gắn vào, vì bản thân bảng tài sản không có project_id riêng). Giao diện: tab "🌳 Tài sản" mới trong từng dự án, form có chọn chủ tài sản (từ danh sách Chủ thể, có thể khác chủ đất hoặc để trống) và phần gắn nhiều thửa đất kiểu tương tự đồng sở hữu ở module Thửa đất. Xoá tài sản sẽ tự dọn `bt_asset_parcels` liên quan. Đã kiểm tra kỹ như các module trước (SQL chạy đúng qua bài test mô phỏng CRUD + gắn/gỡ nhiều thửa + JS chạy đúng qua bài test mô phỏng toàn bộ luồng thêm mới, sửa, xoá).

**Đã xong — Module 4: Dự án mở rộng.** Form dự án bổ sung: chủ đầu tư, diện tích dự án, ranh giới dự án (GeoJSON dạng text, kiểm tra hợp lệ trước khi lưu — chưa có công cụ vẽ bản đồ, để sau), ngày thông báo thu hồi đất, ngày bắt đầu/kết thúc dự kiến. Pháp lý dự án tận dụng module Tài liệu sẵn có: tab "Tổng quan" của mỗi dự án giờ có mục "📄 Tài liệu pháp lý dự án" tự động lấy các tài liệu được gắn thẻ (tag) trùng tên dự án — không tạo bảng/field pháp lý riêng, đúng nguyên tắc thiết kế đã thống nhất. Tiến độ dự án: giữ nguyên cách tính hiện tại (tổng hợp theo trạng thái `bt_records`, hiển thị ở tab Tổng quan) — sẽ chuyển sang tính từ Hồ sơ Hộ/Quyết định theo Thửa khi module đó được xây (module cuối cùng).

Nhân tiện sửa luôn một lỗi tồn tại từ trước: xoá dự án trước đây chỉ xoá bản ghi `bt_projects`, để sót lại toàn bộ thửa đất/hồ sơ/bản đồ/tệp/hồ sơ hộ liên quan (do cờ `foreign_keys` của SQLite đang tắt nên các khai báo CASCADE trong schema không có tác dụng thật). Đã bổ sung dọn dẹp thủ công đầy đủ khi xoá dự án: thửa đất + đồng sở hữu + hồ sơ cũ + quyết định theo thửa, bản đồ + tệp đính kèm (kể cả xoá file vật lý trên R2/local), hồ sơ hộ + người liên quan. Đã kiểm tra kỹ như các module trước (SQL chạy đúng qua bài test mô phỏng tạo/sửa/xoá đầy đủ cascade + JS chạy đúng qua bài test mô phỏng toàn bộ luồng form dự án). Trong lúc kiểm tra JS cũng phát hiện và sửa 1 lỗi nhỏ có từ trước (không phải do session này gây ra): thông báo "Đã cập nhật..." bị hiển thị nhầm thành "Đã thêm mới..." sau khi sửa thành công (do code đóng hộp thoại — reset biến theo dõi — trước khi kiểm tra biến đó để chọn thông báo); đã sửa cho 3 form chạm tới trong phiên này (Dự án, Thửa đất, Tài sản). Đây chỉ là lỗi hiển thị chữ, không ảnh hưởng dữ liệu đã lưu.

**Đã xong — Module 5: Hồ sơ Hộ + Quyết định theo Thửa (module cuối cùng).** API cho `bt_dossiers` (chính sách theo hộ: thưởng tiến độ, hỗ trợ ổn định đời sống/đào tạo chuyển đổi nghề/tái định cư/khác, tạm ứng, đã chi trả, ý kiến), `bt_parcel_decisions` (quyết định phê duyệt theo từng thửa, có thể lệch thời điểm trong cùng hộ), `bt_dossier_persons` (đánh dấu đối tượng trực tiếp sản xuất nông nghiệp theo Nghị định 88/2024/NĐ-CP, theo từng người/từng hồ sơ). Giao diện: tab "💰 Hồ sơ Hộ" mới trong từng dự án — chọn chủ hộ, nhập các khoản hỗ trợ theo hộ, thêm/xoá quyết định theo từng thửa (mỗi thửa chỉ 1 quyết định trong cùng hồ sơ), và danh sách checkbox đánh dấu chủ hộ/nhân khẩu nào là đối tượng SXNN trực tiếp (tự tải danh sách nhân khẩu khi đổi chủ hộ). Đây là tab **mới, bổ sung** — tab "📋 Hồ sơ" cũ (dùng `bt_records`) vẫn giữ nguyên, không xoá, đúng nguyên tắc "để yên dữ liệu cũ" đã thống nhất từ đầu.

Đã kiểm tra kỹ như các module trước (SQL chạy đúng qua bài test mô phỏng CRUD + đồng bộ lại toàn bộ quyết định/người mỗi lần lưu + JS chạy đúng qua bài test mô phỏng toàn bộ luồng). Trong lúc viết bài test JS, phát hiện và sửa ngay 1 lỗi thực sự trong code: phần "tick sẵn" đối tượng SXNN khi mở lại hồ sơ để sửa dùng khoá tắt (`chu:`/`nk:`) không khớp với khoá đầy đủ (`chu_the:`/`nhan_khau:`) mà phần tick/bỏ tick tay dùng — nếu không có bài test này, lỗi sẽ khiến khi sửa hồ sơ đã lưu, các ô tick SXNN trước đó sẽ hiện sai (luôn hiện chưa tick) dù dữ liệu trong CSDL vẫn đúng. Đã sửa cho khớp trước khi báo hoàn thành.

Cũng đã bổ sung: xoá 1 thửa đất riêng lẻ (không phải xoá cả dự án) giờ sẽ tự dọn cả `bt_parcel_decisions` liên quan (trước đó bị bỏ sót khi module Thửa đất được xây, vì lúc đó bảng Hồ sơ Hộ chưa tồn tại).

**Tổng kết: cả 5 module trong kế hoạch redesign CSDL Bồi thường đã hoàn thành** (Chủ thể/Nhân khẩu, Thửa đất+Bản đồ, Tài sản trên đất, Dự án mở rộng, Hồ sơ Hộ+Quyết định theo Thửa). Các việc còn lại nằm ngoài phạm vi thiết kế CSDL này (xem mục Backlog bên dưới): công cụ vẽ ranh giới bản đồ, engine tính đơn giá/thành tiền tài sản, logic áp dụng chính sách hỗ trợ tự động, và cân nhắc chuyển tab "Tổng quan" sang tính tiến độ dự án từ `bt_parcel_decisions` thay vì `bt_records` cũ khi phù hợp.

## Cập nhật 2026-07-14 (sau khi Minh báo lỗi): sửa nút xóa không hoạt động + thêm xác nhận mật khẩu

**Nguyên nhân nút xóa không hoạt động:** lỗi có từ trước (không phải do các module mới gây ra) trong hàm dùng chung cho toàn bộ hộp thoại "Xác nhận xóa" của cả module Bồi thường:

```js
function closeConfirm() { ...; confirmCb = null; }
function confirmAction() { closeConfirm(); if (confirmCb) confirmCb(); }
```

`confirmAction()` gọi `closeConfirm()` trước — hàm này xóa `confirmCb` về `null` — rồi mới kiểm tra `if (confirmCb)`, lúc này luôn là `null` nên hành động xóa thật sự **không bao giờ được gọi**. Hộp thoại đóng lại như bình thường nên trông có vẻ "đã xóa", nhưng dữ liệu vẫn còn nguyên. Lỗi này ảnh hưởng **toàn bộ nút xóa trong module Bồi thường** (dự án, hồ sơ cũ, chủ thể, nhân khẩu, thửa đất, bản đồ, tệp bản đồ, tài sản, hồ sơ hộ) vì tất cả đều dùng chung 1 hộp thoại này. Không ảnh hưởng các trang khác của app (chấm công, tài liệu...) vì các trang đó không dùng chung cơ chế này.

**Đã sửa:** `confirmAction()` giờ lưu `confirmCb` vào 1 biến tạm trước khi đóng hộp thoại, đảm bảo hành động xóa luôn được gọi đúng.

**Đã thêm theo yêu cầu của Minh — xác nhận mật khẩu trước khi xóa:** hộp thoại xác nhận xóa giờ có thêm ô nhập mật khẩu. Trước khi thực sự xóa, hệ thống gọi API mới `/api/verify-password` để kiểm tra mật khẩu đúng với tài khoản đang đăng nhập; sai mật khẩu hoặc để trống sẽ báo lỗi ngay tại chỗ và không cho xóa. Vì toàn bộ nút xóa trong module dùng chung 1 hộp thoại, sửa 1 chỗ này áp dụng cho tất cả — không cần sửa từng nút riêng lẻ.

**Tiện thể sửa luôn:** xóa 1 "hồ sơ" ở tab Hồ sơ cũ (`bt_records`) trước đây chỉ xóa thửa đất liên quan mà không dọn `bt_parcel_owners`/`bt_asset_parcels`/`bt_parcel_decisions` — vì bảng thửa đất (`bt_parcels`) giờ được dùng chung giữa tab Hồ sơ cũ và các module mới (Thửa đất, Tài sản, Hồ sơ Hộ), nên đã bổ sung dọn dẹp đầy đủ để tránh dữ liệu mồ côi.

**2 điểm khác biệt nhỏ so với bản thiết kế gốc, làm vậy vì lý do an toàn:**

- Bảng `bt_parcels` vẫn còn giữ 2 cột cũ không dùng nữa: `owner_id`, `dia_diem_thu_hoi` (thay vì xoá hẳn). Lý do: SQLite không hỗ trợ xoá cột an toàn dễ dàng, và xoá cột có rủi ro nếu môi trường Railway đã có dữ liệu khác với bản test cục bộ. 2 cột này không gây hại gì, chỉ là "thừa", có thể dọn sau khi mọi thứ chạy ổn định.
- Bảng `bt_owners` (Chủ sử dụng đất kiểu cũ) và `bt_records` (Hồ sơ bồi thường kiểu cũ) vẫn còn tồn tại trong CSDL nhưng **không còn được dùng nữa** — toàn bộ chức năng mới sẽ dùng `bt_parties`, `bt_dossiers`, `bt_parcel_decisions` thay thế. 2 bảng cũ này để yên, không xoá, phòng trường hợp cần đối chiếu lại.

## Cập nhật 2026-07-14 (thay đổi kiến trúc lớn): Bản đồ GPMB là nguồn gốc sinh Thửa đất

Theo yêu cầu của Minh, quan hệ giữa Bản đồ và Thửa đất được thiết kế lại để đúng với quy trình GPMB thật: **Bản đồ GPMB là bước đầu tiên** (phải lập được bản đồ GPMB trước), số tờ/số thửa/hình thể trên Bản đồ GPMB **sinh ra** bản ghi Thửa đất — không phải 2 luồng nhập liệu độc lập như trước. Các loại bản đồ khác (trích lục, giao ruộng thời kỳ trước, địa chính...) chỉ dùng để tham khảo/đối chiếu (chồng ghép xác định quá trình sử dụng đất), không sinh Thửa đất.

**Thay đổi schema:** bảng `bt_map_parcels` (đã có từ Module 2b) được bổ sung 3 cột: `parcel_id` (liên kết tới bản ghi `bt_parcels` do thửa này sinh ra), `dien_tich_thu_hoi_tren_ban_do`, `toa_do` (GeoJSON tuỳ chọn cho từng thửa, dùng để xem trước hình dạng).

**Thay đổi luồng nghiệp vụ:**
- Tab mới **"📐 Bản đồ GPMB"** (tách riêng khỏi tab "🗂️ Bản đồ" cũ — tab cũ giữ nguyên, chỉ còn dùng cho bản đồ tham khảo). Một dự án có thể có **nhiều đợt** Bản đồ GPMB (đợt 1, đợt 2...); Thửa đất được gộp từ tất cả các đợt.
- Thêm 1 thửa trên Bản đồ GPMB → backend tự tạo 1 bản ghi `bt_parcels` (số tờ, số thửa, tổng diện tích, diện tích thu hồi, diện tích còn lại = tổng − thu hồi). Sửa thửa trên Bản đồ GPMB → đồng bộ lại các trường không gian đó vào `bt_parcels`, **giữ nguyên** các trường người dùng nhập ở tab Thửa đất (loại đất, nguồn gốc sử dụng, GCN, ghi chú, chủ sở hữu). Xóa thửa khỏi Bản đồ GPMB → xóa luôn `bt_parcels` tương ứng và cascade dọn `bt_parcel_owners`/`bt_asset_parcels`/`bt_parcel_decisions` (thủ công, vì `foreign_keys` pragma vẫn tắt như toàn bộ hệ thống).
- Tab "🗺️ Thửa đất" giờ chỉ còn dùng để **sửa các trường phi không gian**: loại đất, nguồn gốc sử dụng, GCN, ghi chú, chủ sở hữu. Số tờ/số thửa/diện tích hiển thị dạng chỉ đọc kèm ghi chú "sửa tại Bản đồ GPMB". Đã bỏ nút "Thêm thửa đất" và toàn bộ cơ chế cảnh báo trùng thửa ở tab này (chuyển hẳn sang tab Bản đồ GPMB, nơi thửa thật sự được tạo).
- **Khóa tab** cho đến khi đủ điều kiện: Thửa đất, Bản đồ (tham khảo), Tài sản, Hồ sơ Hộ chỉ mở khi dự án đã có Bản đồ GPMB với **ít nhất 1 thửa**; nếu chưa, hiển thị màn hình khóa hướng dẫn quay lại tạo Bản đồ GPMB. Tab Tổng quan và tab Hồ sơ cũ (`bt_records`, ngoài phạm vi redesign) không bị khóa. Khi chọn 1 dự án chưa đủ điều kiện, hệ thống tự chuyển vào tab Bản đồ GPMB — đúng tinh thần "việc đầu tiên phải làm là lập Bản đồ GPMB".
- Có thể dán tọa độ (GeoJSON Polygon/MultiPolygon) cho từng thửa trên Bản đồ GPMB để xem trước hình dạng đơn giản (vẽ bằng SVG dựng từ bounding box, không theo tỉ lệ bản đồ thực). **Chưa làm công cụ vẽ bằng chuột** (Leaflet) — nằm trong Backlog.
- Endpoint mới `GET /api/bt/projects/:id/gpmb-status` trả về `{has_gpmb, parcel_count}` để giao diện quyết định khóa/mở tab.
- Trường hợp thửa cũ/mồ côi (được tạo trực tiếp ở tab Thửa đất từ trước khi có thay đổi này, hoặc từ Import Excel) không có `bt_map_parcels.parcel_id` liên kết: xóa trực tiếp ở tab Thửa đất vẫn hoạt động bình thường (đã bổ sung: tự gỡ liên kết `parcel_id` phía `bt_map_parcels` nếu có, tránh tham chiếu treo).

Đã kiểm tra kỹ theo đúng phương pháp các module trước (SQL mô phỏng đầy đủ luồng tạo/sửa/xóa thửa trên Bản đồ GPMB + đồng bộ + cascade xóa + gpmb-status khóa/mở khóa; JS mô phỏng logic gating của `switchTab`/`selectProject` và logic phân tích GeoJSON của phần xem trước hình dạng).

## Cập nhật 2026-07-14 (bổ sung): Import Excel hàng loạt thửa vào Bản đồ GPMB

Sau khi thấy Minh gặp khó với việc tự tay điền GeoJSON, bổ sung tính năng import Excel cho tab Bản đồ GPMB (ưu tiên trước — đây là màn hình đang chặn Minh; các tab khác vẫn còn nút thêm tay bình thường nên chưa cần import ngay, có thể làm thêm sau nếu Minh thấy cần):

- Nút **"📥 Import Excel nhiều thửa"** và **"📄 Tải file mẫu"** trong phần "Thửa đất trên Bản đồ GPMB" của modal đợt Bản đồ GPMB.
- File mẫu (`GET /api/bt/gpmb-template`) gồm 2 sheet: "Dữ liệu" (5 cột: Số tờ, Số thửa, Diện tích thửa, Diện tích thu hồi, Tọa độ các đỉnh — tùy chọn) và "Hướng dẫn" (giải thích từng cột bằng lời).
- **Định dạng tọa độ đơn giản hóa** thay vì bắt Minh gõ GeoJSON: chỉ cần liệt kê các đỉnh theo thứ tự dạng `X1,Y1; X2,Y2; X3,Y3; ...` — hệ thống tự chuyển sang GeoJSON Polygon và tự khép kín vòng (không cần lặp lại đỉnh đầu ở cuối).
- `POST /api/bt/maps/:id/parcels/import`: đọc file, dò cột theo tên (không phụ thuộc thứ tự cột), đối chiếu trùng theo Số tờ + Số thửa **trong cùng đợt Bản đồ GPMB**. Nếu có trùng, trả về danh sách trùng và **không áp dụng gì cả** cho tới khi client xác nhận ghi đè (field `confirm_overwrite=1`) — đúng yêu cầu "phải xác nhận lại 1 lần nữa trước khi ghi đè", và cố ý tách khỏi cơ chế xác nhận mật khẩu của hành động xóa (mục "Delete requires password" trong bộ nhớ dự án) vì import/ghi đè không phải hành động xóa. Thửa mới (không trùng) luôn được thêm ngay cả khi có thửa khác bị trùng.
- Mỗi dòng import tái sử dụng đúng logic `_create_parcel_from_map_entry`/`_sync_parcel_from_map_entry` đã có — nghĩa là import cũng tự sinh/đồng bộ `bt_parcels` giống hệt như thêm/sửa tay từng thửa một, không có đường tắt riêng dễ lệch dữ liệu.
- Đã tạo sẵn 1 file Excel mẫu có dữ liệu thật (`demo-4-thua-lien-nhau-GPMB.xlsx`, gửi trực tiếp cho Minh) mô phỏng 4 thửa (tờ 15, thửa 101–104) ghép thành lưới 2×2 liền kề nhau (mỗi thửa 20m×15m=300m², tọa độ giả định gốc 0,0) — dùng để Minh thử luồng import + xem trước hình dạng ngay mà không cần có dữ liệu thật trong tay trước.

Đã kiểm tra kỹ bằng test mô phỏng đầy đủ (`/tmp/sql_verify_import/test_import.py`): import lần đầu tạo đúng 4 thửa + đúng dữ liệu Thửa đất sinh ra + tọa độ đơn giản chuyển đúng sang GeoJSON; import lại cùng file bị chặn và báo đúng danh sách trùng, không âm thầm tạo trùng; sau khi xác nhận ghi đè thì cập nhật đúng dữ liệu mà không tạo thêm bản ghi thừa. File Excel mẫu thực tế đã tạo cũng được đọc lại và xác nhận đúng cấu trúc mong đợi trước khi gửi cho Minh.

## Cập nhật 2026-07-14 (bổ sung): xem trước tổng thể nhiều thửa + chuẩn hóa tọa độ ở mọi nơi

Minh thử import xong nhưng không thấy hình dạng thửa ở đâu — hóa ra thiết kế ban đầu chỉ hiện hình khi sửa **từng thửa một** (bấm ✏️), chưa có chỗ xem tất cả thửa ghép lại. Đã bổ sung:

- Khung **"🗺️ Xem trước tổng thể"** trong hộp thoại mảnh trích đo (`renderGpmbCombinedPreview()`): tự động gộp tất cả thửa đã có tọa độ trên mảnh đang sửa thành 1 hình duy nhất, mỗi thửa 1 màu + nhãn tờ-thửa, để thấy các thửa liền nhau ghép ra sao — không cần bấm sửa từng thửa nữa.
- **Chuẩn hóa 1 hàm dùng chung** (`_normalize_toa_do` phía backend, `parseToaDoToRings` phía frontend) cho cả 3 chỗ nhập tọa độ: thêm/sửa 1 thửa bằng tay, xem trước khi gõ, và import Excel — tất cả đều chấp nhận định dạng đơn giản `X,Y; X,Y; ...` (không bắt biết GeoJSON), đồng thời vẫn nhận GeoJSON đầy đủ nếu ai đó đã có sẵn. Trước đó ô nhập tay cho 1 thửa vẫn bắt gõ GeoJSON thô — đây có thể là một phần lý do Minh thấy khó hiểu.

## Cập nhật 2026-07-14 (bổ sung, theo phác thảo tay của Minh): giao diện 2 nửa + đổi thuật ngữ "đợt" → "mảnh trích đo"

Minh vẽ tay lên ảnh chụp màn hình, yêu cầu chia tab Bản đồ GPMB thành 2 nửa có thanh kéo chỉnh tỉ lệ, và giải thích rõ thuật ngữ đúng theo thông tư đo đạc: 1 dự án thường trải nhiều xã → mỗi xã lập 1 **mảnh trích đo** riêng → 1 mảnh có nhiều tờ → 1 tờ có nhiều thửa. Trước đó hệ thống gọi sai là "đợt Bản đồ GPMB", đã đổi toàn bộ giao diện (nút, tiêu đề, thông báo, toast) sang "mảnh trích đo Bản đồ GPMB". **Không** đổi số tờ (`so_to`) thành 1 bảng/thực thể riêng — vẫn là 1 trường trên mỗi thửa như cũ, vì mục tiêu của Minh là sửa thuật ngữ hiển thị chứ không yêu cầu thêm tầng phân cấp mới trong CSDL.

Giao diện tab Bản đồ GPMB giờ có 2 nửa (`.gpmb-split`), chỉnh được tỉ lệ bằng cách kéo thanh chia (`#gpmb-split-resizer`, giới hạn 20%-75%):
- **Nửa trái** (`#gpmb-split-left`): danh sách các mảnh trích đo (bảng như cũ, đổi tên cột). Bấm vào 1 dòng (ngoài nút ✏️/🗑️) sẽ chọn mảnh đó (`selectGpmbMap()`).
- **Nửa phải** (`#gpmb-split-right`): bản đồ của mảnh đang chọn (`renderGpmbMapCanvas()`) — vẽ tất cả thửa có tọa độ dạng **polyline kín, không tô màu, cùng 1 màu viền** (`stroke="#5dade2"`, `fill="none"`) đúng yêu cầu — cố ý chưa tô màu vì màu tô sẽ dành để thể hiện tiến độ GPMB từng thửa (tính năng sau này, chưa làm ở bước này).

Khi mở lại tab, tự động chọn mảnh đầu tiên trong danh sách nếu chưa chọn gì (tránh nửa phải trống trơn ngay từ đầu). Lưu/sửa 1 mảnh xong sẽ tự chọn lại đúng mảnh đó để thấy ngay bản đồ cập nhật.

Đã kiểm tra bằng test mô phỏng thuần logic (`/tmp/js_verify_gpmb/split_ui.mjs`): tính đúng bounding box gộp cho 4 thửa demo (0-40 x 0-30), bỏ qua an toàn thửa chưa có tọa độ mà không crash, báo đúng trạng thái rỗng khi mảnh chưa có thửa nào có tọa độ, và giới hạn % thanh kéo hoạt động đúng (20%-75%).

## Cập nhật 2026-07-14 (bổ sung): bản đồ thực (Leaflet + OpenStreetMap) ở nửa phải, quy đổi tọa độ VN-2000

Minh yêu cầu bản đồ ở nửa phải phải là bản đồ thực (kiểu Google Maps) thay vì sơ đồ minh họa. Minh xác nhận dữ liệu tọa độ thực tế của dự án ở dạng **VN-2000** (hệ tọa độ hồ sơ địa chính chuẩn của Việt Nam), không phải GPS trực tiếp.

**Thay đổi schema:** `bt_projects` thêm cột `kinh_tuyen_truc` (REAL, độ) — mỗi dự án cần khai 1 lần, tra theo tỉnh nơi dự án tọa lạc (Phụ lục 2, Thông tư 25/2014/TT-BTNMT, hoặc hỏi đơn vị đo đạc). Có ô nhập trong form Sửa dự án.

**Cơ chế quy đổi:** dùng thư viện `proj4js` (CDN) ở phía trình duyệt, KHÔNG chuyển đổi và lưu lại tọa độ — dữ liệu `toa_do` trong CSDL vẫn giữ nguyên là VN-2000 gốc (đúng với hồ sơ pháp lý), việc quy đổi sang kinh độ/vĩ độ WGS84 chỉ diễn ra tạm thời lúc hiển thị. Định nghĩa phép chiếu: `+proj=tmerc +lat_0=0 +lon_0=<kinh_tuyen_truc> +k=0.9999 +x_0=500000 +y_0=0 +ellps=WGS84 +towgs84=...` — đây là cách quy đổi phổ biến trong các phần mềm GIS Việt Nam, độ chính xác ở mức mét (đủ cho mục đích xem trên bản đồ, **không dùng để chứng thực ranh giới pháp lý chính xác tuyệt đối**).

**Quy ước nhập liệu quan trọng (đã sửa lại 2026-07-15, xem mục cập nhật bên dưới):** tọa độ mỗi đỉnh thửa nhập theo đúng định dạng `X,Y; X,Y; ...`, X/Y được hiểu là **X (Đông/Easting), Y (Bắc/Northing)** — đúng theo thứ tự cột trong hồ sơ đo đạc/CAD thực tế của Minh (đã xác nhận qua dữ liệu thật, xem cập nhật 2026-07-15). Hàm quy đổi gọi thẳng proj4 theo thứ tự [X, Y] = [Đông, Bắc], không hoán vị.

**Logic hiển thị nửa phải (`renderGpmbMapCanvas`):**
- Nếu dự án **đã có** Kinh tuyến trục hợp lệ và thư viện Leaflet/proj4 đã tải: dựng bản đồ Leaflet thật với nền OpenStreetMap (`renderGpmbLeafletMap`), vẽ từng thửa dạng polygon viền (không tô, cùng màu, đúng yêu cầu trước đó), tự động zoom/pan vừa khung để thấy hết các thửa, hover vào thửa hiện tooltip tờ-thửa.
- Nếu **chưa có** Kinh tuyến trục: giữ nguyên sơ đồ SVG minh họa trừu tượng như trước (`renderGpmbSvgCanvas`), không gây lỗi, chỉ là chưa lên được bản đồ thật.
- Bản đồ Leaflet chỉ khởi tạo 1 lần (giữ lại instance), các lần chọn mảnh khác chỉ vẽ lại layer — tránh rò rỉ bộ nhớ/nhấp nháy. Gọi `invalidateSize()` sau khi kéo thanh chia đôi màn hình hoặc chuyển tab, vì Leaflet cần biết lại kích thước khung chứa mỗi khi nó thay đổi.

**Vì sao không dùng Google Maps thật:** Google Maps Platform cần API key trả phí, ứng dụng chưa có tích hợp/khoá API nào cho việc này. Dùng OpenStreetMap (miễn phí, không cần khoá, nhìn tương tự bản đồ đường phố Google Maps) để đạt đúng mục tiêu "giống Google Maps" mà không phát sinh chi phí/cấu hình mới.

Đã kiểm tra kỹ phần toán học quy đổi tọa độ bằng cách viết lại độc lập công thức nghịch đảo Transverse Mercator chuẩn (Snyder) bằng Python (`/tmp/vn2000test/inverse_tm.py`, không phụ thuộc proj4 vì sandbox không có mạng để cài npm package) — xác nhận: tọa độ VN-2000 giả định gần Hà Nội quy đổi ra đúng khu vực miền Bắc (~21°N, ~106.5°E), tọa độ giả định gần TP.HCM quy đổi ra đúng khu vực miền Nam (vĩ độ thấp hơn hẳn), đảo ngược thứ tự X/Y cho kết quả lệch vị trí rất lớn (xác nhận thứ tự nhập liệu thực sự quan trọng), và tỉ lệ khoảng cách trên thực địa đúng (lệch 100m trên VN-2000 tương ứng ~100m thực tế, không bị lệch tỷ lệ bất thường).

---

## Cập nhật 2026-07-15: import Excel theo dạng "mỗi dòng 1 đỉnh thửa" + tự tính diện tích + sửa quy ước X/Y

Minh gửi file dữ liệu đo đạc thật (`Copy of DanhSachToaDo.xls`, cột STT/Tờ/Thửa/X/Y, mỗi dòng là 1 đỉnh — không phải 1 thửa) và đề xuất định dạng import mới: các dòng liên tiếp cùng Tờ+Thửa là các đỉnh nối nhau tạo thành 1 thửa, đỉnh cuối tự nối lại đỉnh đầu để khép kín; diện tích tự tính từ tọa độ; nhãn thửa dạng `Thửa.Tờ.Diện tíchm2` đặt ở tâm hình học của thửa.

**Phát hiện quan trọng — sửa lại quy ước X/Y:** khi thử quy đổi tọa độ thật của Minh (VD đỉnh đầu tiên X=590943.981, Y=2313150.975) qua công thức nghịch đảo Transverse Mercator, giả thiết "X=Bắc, Y=Đông" (quy ước đã ghi ở mục cập nhật 2026-07-14 phía trên) cho ra kinh độ/vĩ độ **sai** (~121.9°E, 5.1°N — ngoài lãnh thổ Việt Nam, khu vực Philippines). Giả thiết ngược lại "X=Đông, Y=Bắc" (đúng quy ước Cartesian/CAD phổ thông) cho ra kết quả **đúng** (~106.6°E, 20.9°N — khu vực miền Bắc Việt Nam, hợp lý với độ lớn Y~2.3 triệu mét ứng với vĩ độ ~21°). Kết luận: dữ liệu xuất ra từ phần mềm đo đạc/CAD thực tế của Minh dùng quy ước X=Đông(Easting), Y=Bắc(Northing) — ngược với quy ước văn bản hồ sơ tôi tra cứu trước đó. Đã sửa lại toàn bộ: `vn2000ToLonLat(xDong, yBac, kinhTuyenTruc)` gọi proj4 trực tiếp `[xDong, yBac]` không hoán vị, cùng các dòng chú thích/hướng dẫn trong giao diện (tab Bản đồ GPMB, thông báo lỗi bản đồ).

**Backend (`server.py`):**
- Thêm `_ring_from_toa_do()`, `_polygon_area()` (công thức Shoelace/Gauss), `_polygon_centroid()` — dùng chung cho thêm/sửa 1 thửa thủ công VÀ import Excel, đảm bảo diện tích luôn nhất quán = tính từ hình học khi có tọa độ (ghi đè số nhập tay), giữ nguyên nếu chưa có tọa độ.
- Viết lại hoàn toàn `api_bt_map_parcels_import`: đọc cột STT (chỉ tham khảo, không dùng để sắp thứ tự — tin theo thứ tự dòng thực trong file), Tờ, Thửa, X, Y bắt buộc. Gom các dòng liên tiếp cùng (Tờ,Thửa) thành 1 nhóm đỉnh, tự khép vòng nếu đỉnh cuối chưa trùng đỉnh đầu (dữ liệu thật của Minh vốn đã tự lặp đỉnh đầu ở cuối mỗi nhóm — code xử lý đúng cả 2 trường hợp). Diện tích thu hồi mặc định 0 (không có trong định dạng mới, sửa riêng sau bằng nút ✏️). Giữ nguyên cơ chế phát hiện trùng Tờ+Thửa → hỏi xác nhận ghi đè.
- Viết lại `api_bt_gpmb_template`: cột mới STT/Tờ/Thửa/X/Y, dữ liệu mẫu là 2 thửa liền kề lấy từ chính dữ liệu thật của Minh (Tờ 1, Thửa 4 và 5), sheet Hướng dẫn giải thích rõ "mỗi dòng 1 đỉnh, không phải 1 thửa".
- Chặn sớm file `.xls` cũ (nhận diện qua magic bytes OLE2 `D0 CF 11 E0...`) với thông báo rõ ràng — `openpyxl` chỉ đọc được `.xlsx`, không đọc được định dạng nhị phân Excel cũ (chính file thật của Minh là `.xls` cũ, tạo từ 2008). Hướng dẫn Minh "Save As" sang `.xlsx` trước khi import. Input file trên UI cũng giới hạn lại `accept=".xlsx"`.

**Frontend (`boi-thuong.html`):**
- Thêm `polygonCentroid()` (JS, cùng công thức với Python) và `gpmbParcelLabel()` — dùng chung cho cả 3 nơi vẽ nhãn thửa: `renderGpmbSvgCanvas` (sơ đồ minh họa), `renderGpmbLeafletMap` (bản đồ thực — nhãn hiện dưới dạng `L.divIcon`, class CSS `.gpmb-parcel-label`), `renderGpmbCombinedPreview` (xem trước tổng thể trong modal). Cả 3 đều đổi từ tâm hình chữ nhật bao quanh (bbox center) sang tâm hình học thật (centroid) — quan trọng vì thửa 6 trong dữ liệu thật của Minh có 39 đỉnh, hình dạng phức tạp/có thể lõm, tâm bbox có thể rơi ra ngoài ranh giới thửa.

**Xác minh:** viết lại logic gom nhóm + Shoelace + centroid thành script Python độc lập (`/tmp/verify_import/test_import.py`, do bash bị đông cứng view file `server.py`/`boi-thuong.html` sau khi Edit tool ghi đè — xem ghi chú gotcha), chạy qua 3 bài test: (1) dữ liệu mẫu trong template mới, (2) toàn bộ file thật `Copy of DanhSachToaDo.xls` của Minh (chuyển đổi sang `.xlsx` bằng LibreOffice headless vì sandbox không cài được `xlrd` — không có mạng), (3) phát hiện trùng lặp theo nhóm. Kết quả: 4 thửa (Tờ 1 - Thửa 4/5/6/7), diện tích 1470.03 / 1563.01 / 34644.95 / 1323.02 m², khớp tay tính trước. Xác minh chéo hàm centroid JS cho kết quả giống hệt Python (chạy qua Node). File `.xlsx` đã chuyển đổi từ dữ liệu thật của Minh được gửi lại kèm response để anh import thử trực tiếp (không cần tự "Save As").

---

## Cập nhật 2026-07-15 (sau khi thử import thật): hợp nhất tab "Bản đồ GPMB" thành tab "Bản đồ" chung — quản lý nhiều loại bản đồ, nhóm theo đầu mục, chồng nhiều lớp

Sau khi Minh import thành công dữ liệu thật và xem bản đồ, anh yêu cầu mở rộng tab Bản đồ GPMB thành nơi quản lý **mọi loại bản đồ** của dự án, không chỉ GPMB, theo đúng giao diện split-pane + Leaflet đã có.

**Phát hiện quan trọng trước khi sửa:** codebase đã có sẵn HAI khái niệm "Bản đồ" riêng biệt — tab "📐 Bản đồ GPMB" (`tab-gpmb`, xây dựng xuyên suốt phiên này, có polygon/tọa độ/import Excel/Leaflet) và một tab "🗂️ Bản đồ" cũ hơn (`tab-maps`, xây từ đầu dự án — chỉ lưu metadata + file đính kèm, KHÔNG có bản đồ không gian, đã có sẵn dropdown Loại bản đồ với 4 giá trị gần giống yêu cầu mới của Minh: Bản đồ trích lục/Bản đồ giao ruộng thời kỳ trước/Bản đồ địa chính/Khác). Cả hai cùng dùng chung bảng `bt_maps`/API `/api/bt/maps` — `tab-maps` không lọc `loai_ban_do` (hiển thị lẫn cả bản đồ GPMB), còn `tab-gpmb` lọc cứng `loai_ban_do === 'Bản đồ GPMB'`. Quyết định: biến `tab-gpmb` (giao diện mạnh hơn) thành tab Bản đồ duy nhất, **gỡ bỏ nút điều hướng của `tab-maps` cũ** (còn lại code/modal cũ nằm im, không xóa hẳn để giảm rủi ro — cờ dọn dẹp sau nếu Minh muốn). Đã báo quyết định này thay vì hỏi, vì cách đọc yêu cầu của Minh ("biến tab Bản đồ GPMB này thành tab Bản đồ") khá rõ ràng.

**Schema:** thêm cột `bt_maps.nhom_ban_do` (TEXT, tự do) — nhãn đầu mục để nhóm các mảnh lại (VD "Xã Chương Dương"), không phải bảng riêng — nhóm được suy ra ở phía UI theo giá trị trùng nhau, giống cách module Tài liệu đã dùng tag tự do khớp theo tên dự án. `loai_ban_do` vẫn là TEXT tự do như cũ (không đổi thành enum cứng DB-side), chỉ ràng buộc ở UI qua dropdown 4 giá trị: Bản đồ GPMB / Bản đồ mốc giới GPMB / Bản đồ địa chính / Bản đồ khác.

**Quy tắc quan trọng — chỉ loại "Bản đồ GPMB" mới tự sinh Thửa đất:** logic `_create_parcel_from_map_entry`/`_sync_parcel_from_map_entry` vốn đã kiểm tra chính xác `loai_ban_do == 'Bản đồ GPMB'` trước khi đồng bộ — không cần sửa gì thêm, chỉ cần đảm bảo giá trị mới không phá vỡ điều kiện này. 3 loại còn lại (mốc giới/địa chính/khác) dùng CHUNG cơ chế nhập liệu (form thủ công + import Excel theo dạng đỉnh) nhưng dữ liệu thửa/tờ của chúng độc lập, không tạo Thửa đất — đúng như Minh mô tả.

**Frontend — mô hình hiển thị nhiều lớp:** thay hẳn khái niệm "chọn 1 mảnh để xem" (`selectedGpmbMapId`) bằng tập hợp `visibleMapIds` (Set các id đang bật 👁) + `mapDetailCache` (cache chi tiết từng bản đồ, tải theo yêu cầu qua `ensureMapDetail()`, xóa cache khi có sửa đổi). Panel trái nhóm các bản đồ theo `nhom_ban_do` (`renderGpmbMapsPanel`, nhóm không tên → "(Chưa phân nhóm)"), mỗi nhóm có header thu gọn/mở rộng (▼/▶) + 1 nút mắt cấp nhóm (bật/tắt cả nhóm cùng lúc — nếu có ít nhất 1 mảnh trong nhóm đang tắt thì bấm sẽ bật tất cả, ngược lại tắt tất cả). Mỗi bản đồ có nút mắt riêng + 1 chấm màu theo loại (`gpmbTypeStyle`: GPMB=xanh dương, mốc giới=cam, địa chính=xanh lá, khác=xám) để phân biệt khi chồng nhiều lớp. Mặc định khi tải trang: chỉ các bản đồ loại "Bản đồ GPMB" được bật sẵn (đúng yêu cầu #2 của Minh — "bản đồ bên phải hiển thị hết các mảnh bản đồ GPMB"), các loại khác mặc định tắt để không gây rối; nhưng chỉ áp dụng mặc định 1 lần cho mỗi id mới thấy (`seenMapIds`) — không ghi đè lựa chọn người dùng đã tự bật/tắt ở lần tải sau. `renderGpmbMapCanvas()` giờ không nhận tham số, tự gom parcels từ tất cả bản đồ đang bật trong cache, vẽ chồng cả SVG minh họa lẫn Leaflet thật theo đúng màu loại bản đồ.

**Việc mô tả mục đích ở đây đã được triển khai thật sau đó cùng ngày** — xem mục "Cập nhật 2026-07-15 (follow-up): tự động tính diện tích thu hồi..." bên dưới (tính giao hình học bằng shapely, khai báo liên kết + hướng tính, popup xác nhận rà soát).

**Xác minh:** logic nhóm + toggle hiển thị (mặc định theo loại, toggle từng mảnh, toggle cả nhóm, dọn id đã xóa) viết lại thành script Node độc lập (`/tmp/verify_import/gpmb_grouping.mjs`) do bash tiếp tục đông cứng view `boi-thuong.html`/`server.py` phiên này (xác nhận qua `wc -l` lệch xa so với số dòng thực đọc bằng Read tool) — mọi assertion pass. Chưa xác minh trực quan qua browser thật (không có quyền truy cập) — Minh nên thử bấm 👁 từng mảnh và cả nhóm sau khi pull code mới.

---

## Cập nhật 2026-07-15 (follow-up ngay sau): popup hướng dẫn thay banner cố định + bản đồ nền thật (basemap switcher)

Minh phản hồi 2 việc sau khi thấy giao diện tab Bản đồ mới: (1) banner ghi chú dài (giải thích 4 loại bản đồ + kinh tuyến trục) chiếm quá nhiều diện tích màn hình, muốn gom vào popup mở khi bấm 1 nút ❗ cạnh nút "Thêm bản đồ"; (2) muốn biến OpenStreetMap hiện tại thành 1 "bản đồ nền" có thể đổi, và tìm thêm các nguồn bản đồ nền miễn phí khác nếu có.

**Popup hướng dẫn:** thêm nút `❗` (`.gpmb-info-btn`) cạnh nút Thêm bản đồ, mở modal mới `#modal-gpmb-info` (`openGpmbInfoModal`/`closeGpmbInfoModal`) chứa đúng nội dung banner cũ, trình bày lại rõ ràng hơn theo từng đoạn. Banner cố định trong `#tab-gpmb` đã được xoá hẳn khỏi layout.

**Bản đồ nền thật (basemap switcher):** trước đây `renderGpmbLeafletMap` chỉ gắn cứng 1 lớp tile OpenStreetMap. Đã thêm `buildGpmbBasemaps()` trả về nhiều lớp tile lựa chọn được qua `L.control.layers()` (control có sẵn của Leaflet, góc trên-phải bản đồ, không cần thư viện thêm) — đã web-search xác nhận các nguồn này miễn phí, không cần API key, tính đến 2026:
- **OpenStreetMap** (mặc định, giữ nguyên) — `tile.openstreetmap.org`.
- **Vệ tinh (Esri World Imagery)** — `server.arcgisonline.com/.../World_Imagery` — Esri công khai cho phép dùng miễn phí trong các dự án dạng OSM-style mapping, không yêu cầu key hay attribution bắt buộc theo pháp lý (dù vẫn ghi "Tiles © Esri" cho lịch sự).
- **Địa hình (OpenTopoMap)** — `tile.opentopomap.org` — miễn phí cho khối lượng thấp (dưới ~400.000 tile/tháng là "chấp nhận được" theo chính họ công bố) — phù hợp quy mô 1 ứng dụng nội bộ dùng cho vài dự án.
- **Nền tối (CartoDB dark_all)** — `basemaps.cartocdn.com/dark_all` — dịch vụ tile nền miễn phí lâu năm của CARTO, tách biệt với sản phẩm phân tích không gian trả phí của họ (Builder/Enable) — chọn thêm vì hợp với theme tối sẵn có của app.

Đổi bản đồ nền chỉ đổi hình ảnh hiển thị, KHÔNG đụng tới dữ liệu `toa_do` đã lưu (vẫn nguyên VN-2000, không convert lại). Có thêm CSS override để hộp chọn layer của Leaflet (mặc định nền trắng) hoà với theme tối của app.

**Lưu ý cho Minh:** trong lúc chờ tính năng này, Minh đã tự tạo 2 bản ghi bản đồ giả ("OpenStreetMap Hình ảnh", "OpenStreetMap Vệ tinh", nhóm "NỀN BẢN ĐỒ", 0 thửa) trong danh sách bên trái như một cách thử nghiệm/đề xuất trực quan. Các bản ghi này KHÔNG phải là bản đồ nền thật — chúng chỉ là các dòng metadata trống trong `bt_maps`, không có tile ảnh nào cả. Bản đồ nền thật giờ nằm ở nút điều khiển góc trên-phải của chính khung bản đồ Leaflet (không phải là 1 mục trong danh sách bên trái). Đã gợi ý Minh xoá 2 bản ghi thử nghiệm đó vì không còn cần thiết.

---

## Cập nhật 2026-07-15 (follow-up ngay sau): bản đồ nền không được tắt theo mảnh — sửa để nền luôn hiển thị độc lập

Minh test và báo: khi tắt hết 👁 các mảnh (VD nhóm "Xã Hồng Vân" cả 2 mảnh đều tắt), toàn bộ khung bản đồ bên phải biến mất luôn (chỉ còn chữ "Bấm 👁 bên trái để bật hiển thị bản đồ"), thay vì giữ lại bản đồ nền (OpenStreetMap/vệ tinh...) để vẫn có ngữ cảnh địa lý, chỉ ẩn phần ranh giới thửa thôi.

**Nguyên nhân:** `renderGpmbMapCanvas()` bản cũ kiểm tra `withGeo.length` (có mảnh nào đang bật VÀ có tọa độ hay không) TRƯỚC khi quyết định có khởi tạo/hiển thị bản đồ Leaflet hay không — nên hễ không có thửa nào đang bật, cả khung Leaflet (gồm cả bản đồ nền) bị ẩn theo, đúng như Minh mô tả ("lớp nền không tuân theo lệnh bật/tắt các mảnh" — thực ra là bị ẩn CHUNG với các mảnh, ngược với ý Minh muốn).

**Cách sửa — tách rời 2 khái niệm:** bản đồ nền (basemap, hình ảnh street/vệ tinh) là ngữ cảnh địa lý cố định, phải luôn hiển thị nếu dự án đã có Kinh tuyến trục hợp lệ — không phụ thuộc có thửa nào đang bật hay không, giống mọi phần mềm GIS chuẩn (Google Maps, QGIS...). Chỉ RIÊNG lớp ranh giới thửa (`gpmbLeafletLayer`, các polygon + nhãn) mới bật/tắt/vẽ lại theo mảnh đang chọn.

Cụ thể: đảo thứ tự kiểm tra trong `renderGpmbMapCanvas()` — hễ dự án có Kinh tuyến trục hợp lệ (`canUseLeaflet`), LUÔN gọi `renderGpmbLeafletMap()` (bản đồ nền + control chọn nền luôn dựng lên), bất kể `withGeo` rỗng hay không; chỉ khi KHÔNG dùng được Leaflet (chưa khai kinh tuyến trục) mới rơi về nhánh kiểm tra "có thửa nào để vẽ sơ đồ minh hoạ không". Trong `renderGpmbLeafletMap()`: nếu `withGeo` rỗng thì dừng sớm ngay sau khi đảm bảo bản đồ nền đã dựng (không đụng, không xoá gì), giữ nguyên khung nhìn hiện tại. Thêm khung nhìn mặc định `setView([16.0, 106.0], 6)` (trung tâm Việt Nam) cho lần khởi tạo đầu tiên, để có gì đó để nhìn/điều hướng ngay cả khi chưa có mảnh nào bật (trước đây bản đồ chỉ `fitBounds` khi có dữ liệu, nên nếu không có dữ liệu thì chưa từng có khung nhìn nào được set).

Cũng đổi luôn: trường hợp có dữ liệu nhưng quy đổi tọa độ thất bại hoàn toàn (VD sai Kinh tuyến trục) — trước đây ẩn cả bản đồ để hiện dòng cảnh báo, giờ đổi sang cảnh báo bằng `toast()` (không chặn/ẩn bản đồ nền), nhất quán với nguyên tắc "bản đồ nền luôn hiển thị, không bị ẩn vì lý do dữ liệu".

---

## Cập nhật 2026-07-15 (follow-up ngay sau): hiển thị % thu phóng, nhập tay để nhảy zoom

Minh muốn thấy % thu phóng hiện tại của bản đồ Leaflet, nhập tay được, và tự cập nhật khi cuộn/bấm +/-.

**Quy đổi zoom → %:** Leaflet dùng "zoom level" (mỗi mức tăng = độ phân giải nhân đôi), không có khái niệm % sẵn có. Chọn quy đổi tuyến tính đơn giản, dễ giải thích: `% = (zoom - ZOOM_MIN) / (ZOOM_MAX - ZOOM_MIN) * 100`, với `ZOOM_MIN=3` (0% — thu nhỏ hết cỡ) và `ZOOM_MAX=19` (100% — phóng to hết cỡ, khớp mức zoom tối đa phổ biến của các bản đồ nền OSM/CartoDB đã thêm; riêng Esri/OpenTopoMap có maxZoom thấp hơn (19/17) nhưng Leaflet tự upscale ảnh khi vượt `maxNativeZoom` của layer, không lỗi). Chọn map tuyến tính theo min/max thay vì mốc "100% = tỉ lệ thực" kiểu AutoCAD vì không có mốc "tỉ lệ thực" nào tự nhiên áp dụng được cho bản đồ web slippy-tile — cách này đơn giản, không cần chọn mốc tham chiếu tuỳ ý, và nhập/xuất % luôn khớp round-trip.

**Triển khai:** custom Leaflet control (`GpmbZoomPercentControl`, góc trên-trái, xếp ngay dưới nút +/- có sẵn) chứa 1 ô nhập số — gõ số rồi Enter/rời focus sẽ gọi `map.setZoom()` tới mức zoom tương ứng (đã kẹp 0-100). Lắng nghe sự kiện `zoomend` của bản đồ (bắn ra từ MỌI nguồn: cuộn chuột, bấm +/-, `fitBounds` khi bật mảnh, hay chính việc nhập tay) để đồng bộ lại số hiển thị trong ô — đảm bảo % luôn khớp trạng thái zoom thực tế bất kể đến từ đâu, đúng yêu cầu "tự động thay đổi theo".

---

## Cập nhật 2026-07-15 (follow-up ngay sau): nâng trần zoom lên 200% + thêm thanh trượt

Minh muốn tăng khả năng zoom tối đa lên 200% (từ 100% cũ) và có thêm thanh kéo (slider) để thu phóng, không chỉ ô nhập số.

**Nâng trần %:** đổi `GPMB_ZOOM_MAX` từ 19 lên 21 (thêm dư một chút so với mức zoom gốc cao nhất mà các nguồn nền hỗ trợ, để có chỗ "phóng sâu hơn"), thêm hằng `GPMB_PCT_MAX=200`, công thức quy đổi zoom↔% đổi từ nhân 100 sang nhân `GPMB_PCT_MAX`. Vẫn giữ 0% = zoom 3 (thu nhỏ nhất) làm mốc gốc, chỉ nới trần %.

**Vấn đề kỹ thuật phát sinh khi nâng trần:** các nguồn bản đồ nền khác nhau có mức zoom "nét" (native) khác nhau — Esri World Imagery/OSM tối đa ảnh nét ở zoom 19, OpenTopoMap ở 17, CartoDB ở 20 — thấp hơn `GPMB_ZOOM_MAX=21` mới. Nếu chỉ set `maxZoom` trên tile layer bằng mức native, Leaflet sẽ để trống (không hiện gì) khi zoom vượt quá mức đó thay vì phóng to ảnh có sẵn. Đã sửa: mỗi tile layer trong `buildGpmbBasemaps()` giờ có `maxNativeZoom` (mức ảnh nét thật của từng nguồn) tách riêng khỏi `maxZoom` (luôn bằng `GPMB_ZOOM_MAX` chung cho mọi nguồn) — nhờ vậy vượt quá mức nét, Leaflet tự phóng to (upscale, có thể hơi mờ) ảnh sâu nhất đã tải thay vì bỏ trống, đảm bảo zoom tới 200% luôn nhìn thấy gì đó bất kể đang chọn nền nào.

**Thanh trượt:** thêm `<input type="range">` trong cùng control với ô nhập số, kéo tới đâu gọi `map.setZoom()` ngay tới đó (sự kiện `input`, phản hồi tức thời khi đang kéo, không cần thả chuột mới cập nhật). Cả thanh trượt và ô số dùng chung hàm `updateGpmbZoomPercentDisplay()` để đồng bộ 2 chiều — kéo thanh trượt thì ô số cập nhật theo và ngược lại, cùng nghe theo sự kiện `zoomend` như cũ.

---

## Cập nhật 2026-07-15 (follow-up nhỏ): tỉ lệ mặc định cột trái/bản đồ

Minh muốn tỉ lệ mặc định khi tải trang giống lúc đã kéo thanh chia sang trái (ưu tiên khung bản đồ lớn hơn), thay vì mặc định 40% cho cột danh sách mảnh. Đổi width mặc định của `#gpmb-split-left` từ 40% xuống 18%, hạ luôn giới hạn kéo tối thiểu của thanh resizer từ 20% xuống 12% (và `min-width` CSS từ 220px xuống 160px) để Minh có thể kéo hẹp hơn nữa nếu muốn, đúng ý "có thể co nhỏ hơn nữa".

---

## Cập nhật 2026-07-15 (follow-up): import Bản đồ ranh giới GPMB bị rối hình — thêm tùy chọn tự sắp xếp lại đỉnh theo khoảng cách gần nhất

Minh import file tọa độ ranh giới thật (`Copy of DanhSachToaDo Ranh HV.xlsx`, 546 đỉnh) vào loại "Bản đồ mốc giới GPMB" và thấy hình vẽ ra bị rối — các đường nối cắt chéo lung tung thay vì 1 đường viền khép kín rõ ràng. Minh hỏi liệu đổi sang định dạng JSON có sửa được không.

**Nguyên nhân:** toàn bộ 546 dòng trong file của Minh đều có Tờ=999, Thửa=999 (giá trị giữ chỗ cố định, không phải số tờ/thửa thật — hợp lý vì đây là ranh giới thu hồi theo địa giới hành chính, không theo từng thửa). Logic import hiện tại gom các dòng liên tiếp cùng (Tờ,Thửa) thành 1 nhóm đỉnh nối theo đúng thứ tự dòng trong file — vì tất cả 546 dòng cùng 1 giá trị (999,999), cả file bị gom thành 1 đa giác duy nhất, nối theo đúng thứ tự dòng gốc. Nhưng thứ tự dòng trong file không theo đúng thứ tự đường biên thực địa (có thể do ghép từ nhiều đợt đo, xuất từ phần mềm không giữ thứ tự) → các đỉnh xa nhau về vị trí thực nhưng gần nhau về số dòng bị nối thẳng vào nhau, tạo hình răng cưa/tự cắt chéo. Đã hỏi Minh xác nhận: ranh giới là **1 đường khép kín duy nhất** (không phải nhiều đoạn rời nhau) — nghĩa là vấn đề thuần túy nằm ở **thứ tự** đỉnh, không phải ở cách gom nhóm.

**Vì sao đổi sang JSON không tự sửa được:** JSON so với Excel chỉ là khác định dạng lưu trữ (cách gõ dữ liệu), không tự thêm thông tin về thứ tự đúng của đường biên — nếu Minh gõ JSON theo đúng thứ tự dòng file gốc (vốn đã sai) thì kết quả vẫn rối y hệt. Đã giải thích rõ với Minh trước khi chọn hướng sửa.

**Giải pháp đã làm — tùy chọn "tự động sắp xếp lại thứ tự đỉnh" khi import Excel:** thêm hàm `_nearest_neighbor_reorder()` (heuristic "láng giềng gần nhất" — bắt đầu từ đỉnh đầu tiên trong file, mỗi bước nối tới đỉnh CHƯA dùng gần nhất về khoảng cách hình học), áp dụng cho từng nhóm (Tờ,Thửa) khi người dùng tick checkbox mới "Tự động sắp xếp lại thứ tự đỉnh theo khoảng cách gần nhất" trong bước Import Excel. **Mặc định TẮT** (không đụng vào dữ liệu đã đúng thứ tự — trường hợp thông thường của các mảnh Bản đồ GPMB bình thường), Minh cần chủ động bật khi thấy hình vẽ ra bị rối. Đây là **heuristic suy đoán hợp lý, không đảm bảo đúng tuyệt đối** — hoạt động tốt với ranh giới lồi/tương đối đơn giản (dựa trên giả định các mốc liền kề trên thực địa thường ở gần nhau), có thể sai ở các đoạn ranh giới lõm sâu hoặc hình dạng phức tạp bất thường; Minh nên xem trực quan sau khi import để xác nhận hình hợp lý, không dùng mù quáng cho mọi trường hợp.

**Xác minh bằng script độc lập** (`/sessions/trusting-vibrant-turing/mnt/outputs/test_reorder_v2.py`, mô phỏng đúng logic gom nhóm + `auto_reorder` mới trong `api_bt_map_parcels_import`) chạy trên chính file thật của Minh: chu vi đa giác theo thứ tự file gốc = 98.085 m (rối, gấp khúc dài bất thường); chu vi sau khi bật tự sắp xếp lại = 37.626 m (giảm ~62%, hợp lý hơn nhiều cho 1 đường biên khép kín bao quanh vùng ~507ha — khớp quy mô 1 khu vực GPMB cấp xã). Diện tích tính ra ~506,6ha nằm trong khoảng hợp lý (50–2.000ha) đã kiểm tra.

**Việc dự tính nhưng chưa làm (Minh xác nhận muốn "cả hai" — Excel và JSON):** phần nhập tay 1 thửa/mảnh (ô "Tọa độ các đỉnh") đã sẵn hỗ trợ dán trực tiếp GeoJSON đầy đủ từ trước (qua `_normalize_toa_do`/`parseToaDoToRings` dùng chung, xem cập nhật 2026-07-14 phần "chuẩn hóa tọa độ") — đây là cách Minh có thể dùng ngay nếu muốn dán 1 vòng ranh giới đã tự sắp xếp đúng thứ tự từ nguồn khác. Một tính năng **upload file JSON hàng loạt riêng cho bước Import** (thay thế/song song với Excel) **chưa được xây** — cần bàn kỹ hơn về cấu trúc JSON mong muốn (mảng điểm đơn giản? nhiều ranh giới cùng lúc?) trước khi làm, vì hướng auto-reorder ở trên đã giải quyết được vấn đề trước mắt.

---

## Cập nhật 2026-07-15 (follow-up): thêm import KML/KMZ cho mảnh trích đo Bản đồ

Sau khi sửa xong lỗi hình rối bằng tùy chọn tự sắp xếp lại đỉnh, Minh yêu cầu thêm hẳn khả năng import trực tiếp từ file KML/KMZ (định dạng chuẩn của Google Earth/Google My Maps/QGIS) — đây cũng là hướng đã thống nhất trước đó khi Minh trả lời muốn "cả hai" cách import (Excel và một định dạng khác ngoài Excel).

**Vì sao KML/KMZ giải quyết tận gốc vấn đề thứ tự đỉnh:** khác với file Excel (nơi người dùng gõ tay từng dòng, dễ bị xáo trộn thứ tự khi ghép dữ liệu từ nhiều đợt đo), file KML luôn do phần mềm vẽ bản đồ xuất ra theo **đúng thứ tự đường vẽ trên thực địa/màn hình** — mỗi Placemark (hình vẽ) đã tự nhiên là 1 đường khép kín đúng thứ tự, không cần đến tùy chọn "tự động sắp xếp lại đỉnh" (`auto_reorder`) như luồng Excel.

**Định dạng nhận diện:** endpoint import hiện có (`POST /api/bt/maps/:id/parcels/import`) được mở rộng để tự nhận diện đuôi file (`.xlsx` / `.kml` / `.kmz`) và định tuyến sang parser tương ứng — Minh không cần chọn loại file riêng, chỉ việc chọn đúng file, hệ thống tự xử lý.
- `.kml`: XML thuần, đọc bằng `xml.etree.ElementTree` (thư viện chuẩn Python, không cần cài thêm).
- `.kmz`: file nén zip chứa 1 file `.kml` bên trong (thường tên `doc.kml`) — đọc bằng `zipfile` (thư viện chuẩn), tự tìm file `.kml` đầu tiên trong gói.
- Mỗi Placemark trong file → 1 nhóm đỉnh (1 "thửa"/hình). Ưu tiên đọc từ `<Polygon>` (vành ngoài `outerBoundaryIs`, bỏ qua lỗ hổng bên trong nếu có); nếu Placemark không có Polygon (nhiều người vẽ ranh giới bằng công cụ "Đường" — Path/LineString — trong Google Earth thay vì "Đa giác") thì tự động thử đọc `<LineString>` thay thế.
- Tên Placemark (`<name>`) được dò để đoán Tờ/Thửa theo vài mẫu thường gặp ("Tờ 3 Thửa 45", "Tờ: 3, Thửa: 45", hoặc nhãn dạng "45.3" giống định dạng nhãn thửa app đang dùng) — không phân biệt dấu tiếng Việt (so khớp sau khi bỏ dấu). Không đoán được thì lấy nguyên tên Placemark làm "số thửa" tạm, số tờ để trống — mỗi hình như vậy vẫn được lưu riêng biệt (không bị gộp nhầm với hình khác cũng không đoán được tên) để xem/đối chiếu trên bản đồ, nhưng **không tự sinh Thửa đất** ngay cả khi mảnh đang import là loại "Bản đồ GPMB" (vì không có số tờ thật — đúng tinh thần chỉ Bản đồ GPMB có Tờ+Thửa hợp lệ mới sinh `bt_parcels`, giữ nguyên bất biến đã có từ trước).

**Bắt buộc phải khai Kinh tuyến trục trước khi import KML/KMZ:** tọa độ trong file KML luôn ở hệ WGS84 (kinh độ, vĩ độ — chuẩn toàn cầu của Google Earth), trong khi CSDL của app lưu tọa độ VN-2000 (khớp hồ sơ đo đạc gốc, xem cập nhật 2026-07-14 "bản đồ nền thực"). Nếu dự án chưa khai Kinh tuyến trục, endpoint trả lỗi rõ ràng yêu cầu vào "Sửa dự án" khai trước, không âm thầm dùng giá trị mặc định sai.

**Toán học quy đổi WGS84 → VN-2000 (ngược lại của phép quy đổi hiển thị bản đồ đang chạy phía trình duyệt):** viết thủ công bằng Python thuần (`_geodetic_to_geocentric`, `_geocentric_to_geodetic`, `_helmert_wgs84_to_vn2000_src`, `_forward_tmerc` trong `server.py`), KHÔNG dùng thư viện `pyproj` — môi trường phát triển hiện tại không có mạng để cài, và `pyproj` cần biên dịch C-extension nên có rủi ro không chắc Railway có sẵn wheel phù hợp lúc deploy; viết tay bằng công thức Snyder chuẩn (cùng gốc công thức TM đang dùng, chỉ đảo chiều) tránh được rủi ro phụ thuộc mới. Quan trọng: bước đầu có thử bỏ qua thành phần xoay/tỷ lệ nhỏ (~1e-8 radian) của phép dịch chuyển gốc tọa độ Helmert 7-tham số (`+towgs84=...`) vì tưởng là không đáng kể — kiểm tra bằng test round-trip mới phát hiện sai số thực tế lên tới ~0.3-0.4m (do bán kính Trái Đất rất lớn, góc xoay dù nhỏ vẫn nhân ra khoảng cách đáng kể ở bề mặt) — đã sửa dùng đúng ma trận nghịch đảo (chuyển vị của ma trận xoay góc nhỏ) thay vì bỏ qua, đưa sai số round-trip xuống dưới 1mm. Đây là ví dụ cụ thể cho nguyên tắc "không được coi nhẹ sai số tưởng chừng nhỏ khi làm việc với tọa độ địa lý" — chỉ phát hiện được nhờ có viết test round-trip định lượng, không thể nhìn code mà đoán ra.

**Xác minh:** viết lại chính xác toàn bộ logic (parser KML/KMZ + phép quy đổi tọa độ) thành script độc lập (`/sessions/trusting-vibrant-turing/mnt/outputs/kml_import_e2e_test.py`), chạy 4 kịch bản: (1) lấy đúng 4 đỉnh thật của Thửa 4 (Tờ 1) đã dùng xuyên suốt phiên này, quy đổi ngược sang WGS84, đóng gói thành KML giả lập rồi import lại — sai số khôi phục tọa độ dưới 1mm, diện tích tính ra đúng khớp 1470.03m² (con số đã tính độc lập qua đường Excel trước đó trong cùng phiên — một phép đối chiếu chéo tốt xác nhận cả 2 đường import cho cùng kết quả); (2) cùng nội dung đóng gói dưới dạng `.kmz` (zip) cho kết quả giống hệt `.kml`; (3) một ranh giới lớn dạng hình chữ nhật ~2879ha (mô phỏng quy mô ranh giới GPMB cấp xã) giữ đúng hình khép kín, chu vi/diện tích hợp lý, không tự cắt chéo; (4) 2 Placemark có tên khác nhau không đoán được mẫu Tờ/Thửa vẫn được giữ thành 2 nhóm riêng biệt, không bị gộp nhầm thành trùng lặp.

**Frontend:** ô chọn file trong bước Import của modal Bản đồ (`#gpmb-import-file-input`) mở rộng `accept` sang `.xlsx,.kml,.kmz`; nút đổi tên thành "📥 Import Excel / KML / KMZ"; phần hướng dẫn mô tả rõ cả 2 luồng; ghi chú thêm vào checkbox "tự động sắp xếp lại đỉnh" rằng nó chỉ áp dụng cho Excel, không cần thiết cho KML/KMZ. Không cần thêm nút/luồng riêng — cùng 1 nút, backend tự nhận diện định dạng qua đuôi file.

---

## Cập nhật 2026-07-15 (follow-up): tự động tính diện tích thu hồi bằng cách chồng Bản đồ Mốc giới GPMB lên Mảnh trích đo GPMB

Đây là tính năng đã được flag từ đầu quá trình redesign là "chưa làm — cần thư viện hình học nếu triển khai" (xem mục "Tình trạng triển khai" và các cập nhật trước về Bản đồ đa lớp). Minh giờ yêu cầu triển khai thật, kèm 2 yêu cầu khai báo cụ thể (qua ảnh chụp màn hình popup Thêm/Sửa bản đồ) và 1 yêu cầu về luồng xác nhận.

**Yêu cầu gốc của Minh (tóm tắt):**
1. Khai báo Bản đồ Mốc giới GPMB liên quan đến (những) Mảnh trích đo GPMB nào.
2. Khai báo phần nằm TRONG polygon của Mốc giới GPMB là diện tích thu hồi (trong dự án) hay diện tích còn lại (ngoài dự án) — khai tại popup Thêm/Sửa bản đồ khi chọn loại "Bản đồ mốc giới GPMB".
3. Mỗi khi vừa cập nhật xong dữ liệu 1 Bản đồ Mốc giới GPMB, tự rà soát và hỏi xác nhận trước khi cập nhật diện tích thu hồi của các thửa bị ảnh hưởng (nếu phát hiện chênh lệch) — không tự động ghi đè âm thầm.

**Quyết định kiến trúc quan trọng — chính thức thêm thư viện `shapely`:** đây là lựa chọn đã được thống nhất từ chính bản thiết kế CSDL gốc ("Nguyên tắc thiết kế chung" #2 bên dưới: "tính toán không gian dùng thư viện Python Shapely, không dùng PostGIS/SpatiaLite"), nay mới thực sự cần dùng lần đầu (tính giao 2 đa giác là bài toán hình học tính toán khó, không nên tự viết tay — rủi ro sai số ảnh hưởng trực tiếp đến số tiền bồi thường thực tế). Đã thêm `shapely>=2.0.0` vào `requirements.txt`.

**QUAN TRỌNG — giới hạn xác minh:** môi trường phát triển hiện tại (sandbox) không có kết nối mạng để cài `shapely` (đã thử `pip install`, bị chặn bởi proxy), nên **phần tính giao đa giác hình học thật SỰ CHƯA CHẠY THỬ ĐƯỢC** trong phiên làm việc này. `shapely` là thư viện rất phổ biến, ổn định, có sẵn bản build (wheel) cho hầu hết môi trường Linux nên khả năng cài thành công trên Railway (nơi có mạng thật lúc build) là cao, nhưng đây là một giả định chưa được xác nhận trực tiếp. **Minh nên tự kiểm tra bằng 1 case đơn giản** (VD 2 hình chữ nhật chồng lên nhau một phần, diện tích giao có thể tính tay) ngay sau khi deploy, trước khi tin tưởng dùng số liệu này cho hồ sơ bồi thường thật.

**Schema:** `bt_maps` thêm 2 cột (chỉ có ý nghĩa khi `loai_ban_do == 'Bản đồ mốc giới GPMB'`):
- `mocgioi_manh_ids` (TEXT, JSON mảng id các Mảnh trích đo GPMB liên quan — VD `"[12, 15]"`).
- `mocgioi_trong_la` (TEXT, `'thu_hoi'` hoặc `'con_lai'`).

**Công thức:** với mỗi thửa trên các Mảnh trích đo GPMB đã liên kết, tính diện tích giao (`intersection`) giữa polygon thửa và polygon (hợp nhất, `unary_union`) của Bản đồ Mốc giới GPMB:
- Nếu khai "trong polygon = thu hồi": diện tích thu hồi mới = diện tích giao.
- Nếu khai "trong polygon = còn lại": diện tích thu hồi mới = tổng diện tích thửa − diện tích giao.

**Backend (`server.py`):**
- `_compute_mocgioi_overlap(db, mocgioi_map_id)` — hàm dùng chung cho cả 2 endpoint bên dưới, KHÔNG tự ghi CSDL, chỉ trả về danh sách thửa có chênh lệch > 1m² (ngưỡng bỏ qua sai số làm tròn/số học vặt) so với giá trị `dien_tich_thu_hoi_tren_ban_do` đang lưu.
- `GET /api/bt/maps/:id/mocgioi/recompute-check` — tính thử, trả về danh sách chênh lệch để hiển thị cho người dùng xác nhận.
- `POST /api/bt/maps/:id/mocgioi/apply-recompute` — **tự tính lại từ đầu** (không tin số phía client gửi lên — vì đây là số liệu ảnh hưởng tiền bồi thường, ưu tiên an toàn tránh dữ liệu cũ/đua lệnh hơn là tiện lợi truyền lại số đã tính), áp dụng toàn bộ chênh lệch: cập nhật `bt_map_parcels.dien_tich_thu_hoi_tren_ban_do` rồi gọi `_sync_parcel_from_map_entry` có sẵn để đồng bộ tiếp sang `bt_parcels.dien_tich_thu_hoi`/`dien_tich_con_lai` — tái sử dụng đúng cơ chế đồng bộ đã có, không tạo đường ghi dữ liệu riêng dễ lệch.
- Nếu import `shapely` thất bại (chưa cài) → trả lỗi rõ ràng thay vì crash, theo đúng pattern phòng thủ đã dùng cho các thư viện tùy chọn khác (`openpyxl`) trong codebase.

**Frontend (`boi-thuong.html`):**
- Popup Thêm/Sửa bản đồ: khi chọn Loại bản đồ = "Bản đồ mốc giới GPMB", hiện thêm khối khai báo — danh sách checkbox chọn 1/nhiều Mảnh trích đo GPMB trong dự án (`renderMocgioiManhChecklist`, lấy từ `gpmbMapsList` đã tải sẵn cho panel trái, lọc `loai_ban_do === 'Bản đồ GPMB'`) và select "Phần nằm bên trong ranh giới là: Diện tích thu hồi / Diện tích còn lại".
- Luồng rà soát tự động: móc vào đúng 1 điểm chung `reloadGpmbDetail()` (hàm đã được gọi sau MỌI thao tác thay đổi polygon trên 1 mảnh — thêm/sửa/xóa thửa thủ công, import Excel, import KML/KMZ) — nếu bản đồ đang sửa là loại Mốc giới GPMB, tự gọi `checkMocgioiRecompute()`. Ngoài ra `saveGpmbMap()` cũng gọi lại rà soát riêng khi vừa lưu thay đổi liên kết/hướng tính trên 1 bản đồ Mốc giới GPMB đã có sẵn polygon (trường hợp Minh đổi liên kết mà không đụng gì đến polygon).
- Nếu phát hiện chênh lệch, hiện popup mới `#modal-mocgioi-confirm` — bảng liệt kê Mảnh / Tờ-Thửa / diện tích thu hồi cũ / mới, 2 nút "Cập nhật diện tích thu hồi" (gọi apply-recompute) hoặc "Bỏ qua" (đóng popup, giữ nguyên, có thể rà soát lại sau lần sửa tiếp theo).

**Xác minh:** vì không chạy được `shapely` thật, đã viết script độc lập (`/sessions/trusting-vibrant-turing/mnt/outputs/mocgioi_overlap_test.py`) copy nguyên logic điều phối của `_compute_mocgioi_overlap` nhưng thay phần "tính giao 2 đa giác" (`Polygon(...).intersection(...).area`) bằng 1 hàm tính giao HÌNH CHỮ NHẬT trục-song-song đơn giản (kiểm tra được bằng tay, không cần thư viện) — chỉ để xác nhận phần LOGIC ĐIỀU PHỐI xung quanh nó đúng: đọc đúng danh sách liên kết JSON, áp dụng đúng công thức theo hướng thu_hoi/còn_lại (2 hướng cho 2 kết quả khác nhau rõ ràng khi hình giao lệch, đã kiểm chứng cả 2), ngưỡng 1m² lọc đúng sai số vặt, gom đúng nhiều Mảnh trích đo GPMB cùng lúc, và không lỗi khi chưa khai đủ liên kết/hướng tính. Cả 6 kịch bản đều pass. **Việc bản thân `shapely` tính đúng giao 2 đa giác tổng quát (có thể lõm, phức tạp) là trách nhiệm của thư viện (rất phổ biến/ổn định) chứ không phải logic tự viết — nhưng chưa được xác nhận chạy thật trong dự án này**, xem lưu ý ở trên.

---

## Cập nhật 2026-07-15 (follow-up nhỏ): rà soát diện tích thu hồi khi xóa Bản đồ Mốc giới GPMB + ẩn nhãn thửa khi zoom nhỏ

**1. Xóa Bản đồ Mốc giới GPMB phải rà soát lại diện tích thu hồi bị ảnh hưởng.** Trước đó tính năng rà soát (mục cập nhật ngay phía trên) chỉ trigger khi SỬA 1 Bản đồ mốc giới GPMB đang tồn tại — chưa xử lý trường hợp XÓA hẳn nó đi, khi đó các thửa từng được tính thu hồi từ ranh giới đó sẽ mất căn cứ hình học.

- `api_bt_maps_delete`: trước khi xóa, nếu bản đồ là loại "Bản đồ mốc giới GPMB", ghi lại `mocgioi_manh_ids` của nó. Sau khi xóa xong (transaction đã commit), gọi `_compute_mocgioi_recompute_for_manh_ids(db, manh_ids)` (hàm mới) và trả kèm trong response xóa (`mocgioi_diffs`, `mocgioi_manh_ids`).
- `_compute_mocgioi_recompute_for_manh_ids`: với mỗi mảnh từng bị ảnh hưởng, kiểm tra còn Bản đồ mốc giới GPMB nào KHÁC vẫn liên kết tới nó không — nếu còn, tính lại theo (các) bản đồ còn lại đó (tái dùng `_compute_mocgioi_overlap`, không viết công thức riêng). Nếu KHÔNG còn cái nào bao phủ nữa, đề xuất đưa diện tích thu hồi về 0 (không còn căn cứ hình học để giữ số cũ) — nhưng vẫn chỉ là ĐỀ XUẤT, không tự ghi, cùng nguyên tắc "luôn hỏi trước khi ghi đè" đã thống nhất.
- Endpoint mới `POST /api/bt/mocgioi/apply-recompute-for-manh` (nhận `{manh_ids}` — không có map_id vì bản đồ đã bị xóa, không còn để tra cứu) — tự tính lại từ đầu (không tin số client gửi) trước khi áp dụng, giống nguyên tắc an toàn của `apply-recompute` theo map_id.
- Frontend: `askDeleteGpmbMap` đọc `mocgioi_diffs` trong response xóa, nếu có thì gọi `showMocgioiDiffsAfterDelete()` mở lại đúng popup `#modal-mocgioi-confirm` đã có sẵn (tái sử dụng UI, chỉ thêm biến `pendingMocgioiMode` để phân biệt 2 nguồn rà soát — 'map' khi đang sửa 1 bản đồ còn sống, 'delete' khi vừa xóa xong — `applyMocgioiRecompute()` gọi đúng endpoint tương ứng theo mode).

Xác minh bằng test độc lập tương tự (`/sessions/trusting-vibrant-turing/mnt/outputs/mocgioi_delete_recompute_test.py`, dùng hình chữ nhật trục-song-song thay shapely như các test trước): xóa mốc giới mà mảnh không còn ai bao phủ → đề xuất về 0; xóa mốc giới nhưng mảnh vẫn còn 1 mốc giới khác bao phủ → tính lại theo cái còn lại (không về 0); xóa mốc giới bao phủ 2 mảnh với 2 tình huống khác nhau cùng lúc → mỗi mảnh xử lý đúng riêng; danh sách mảnh rỗng hoặc thửa vốn đã 0 → không có gì để rà soát, không lỗi. Cùng giới hạn xác minh như tính năng gốc: bản thân `shapely` chưa chạy thử được trong sandbox.

**2. Ẩn nhãn thửa khi zoom bản đồ ≤178%.** Ở mức thu nhỏ, nhãn "{Thửa}.{Tờ}.{Diện tích}m2" của nhiều thửa chồng lấn lên nhau che khuất bản đồ. Thêm hằng `GPMB_LABEL_MIN_PCT = 178`; `updateGpmbZoomPercentDisplay()` (đã là hàm chạy mỗi khi zoom đổi — kéo chuột, bấm +/-, kéo thanh trượt, nhập số, hay `fitBounds` khi bật/tắt mảnh) giờ toggle thêm class CSS `hide-parcel-labels` trên khung bản đồ (`#gpmb-map-leaflet`) dựa theo `pct <= 178`; CSS `#gpmb-map-leaflet.hide-parcel-labels .gpmb-parcel-label{display:none}` ẩn toàn bộ nhãn (marker `L.divIcon`) mà không đụng tới các đường viền polygon thửa (chỉ ẩn nhãn, không ẩn hình). Chọn cách toggle bằng 1 class CSS ở khung chứa thay vì gỡ từng marker khỏi layer, vì polygon và nhãn đang gộp chung 1 mảng `layers`/`gpmbLeafletLayer` — tách riêng sẽ phức tạp hơn không cần thiết cho mục tiêu "chỉ ẩn nhãn". Gọi thêm `updateGpmbZoomPercentDisplay()` ngay sau `fitBounds()` trong `renderGpmbLeafletMap` (không chỉ dựa vào sự kiện `zoomend`), vì `fitBounds` không phải lúc nào cũng bắn `zoomend` (khi mức zoom mới trùng mức hiện tại) — đảm bảo trạng thái ẩn/hiện nhãn luôn đúng ngay sau khi vẽ lại dữ liệu, không cần đợi người dùng tự zoom thêm 1 lần.

---

## Cập nhật 2026-07-15 (follow-up): Minh báo diện tích thu hồi tính ra lệch với phần mềm khác — sửa xử lý hình không hợp lệ

Minh kiểm tra chéo bằng phần mềm GIS khác: Thửa 6 (Tờ 1, tổng diện tích 34.644,95 m²) hệ thống tính ra diện tích thu hồi 29.766,67 m², nhưng phần mềm kia cho 29.729,56 m² — lệch 37,11 m² (~0,1%). Minh xác nhận ranh giới bản đồ (hình vẽ) đã đúng, nghi vấn nằm ở cách tính.

**Nguyên nhân nghi ngờ nhiều nhất:** Thửa 6 là hình phức tạp 39 đỉnh (đã ghi chú từ trước, xem cập nhật 2026-07-15 sớm hơn: "có thể lõm"), và ranh giới Mốc giới GPMB liên quan từng phải sửa qua tính năng "tự động sắp xếp lại đỉnh" (do dữ liệu gốc bị xáo trộn thứ tự — xem mục "import Bản đồ ranh giới GPMB bị rối hình"). Cả 2 loại hình này đều có nguy cơ hình học không hoàn toàn "hợp lệ" theo chuẩn GIS (tự cắt chéo nhẹ ở 1-2 đỉnh, dù nhìn bằng mắt vẫn có vẻ đúng) — code cũ khi gặp polygon không hợp lệ (`is_valid == False`) sẽ **bỏ qua hẳn** thay vì cố gắng sửa, có thể khiến phép tính giao dùng thiếu 1 phần hình hoặc GEOS xử lý hình không hợp lệ theo cách không như mong đợi.

**Đã sửa:** thêm `_shapely_repair(geom)` — dùng kỹ thuật `buffer(0)` chuẩn của shapely để tự sửa các lỗi hình học nhẹ (tự cắt chéo, đỉnh trùng/gần trùng) thay vì loại bỏ toàn bộ hình. Áp dụng cho cả polygon Mốc giới GPMB (từng đoạn, và cả sau khi hợp nhất `unary_union`) lẫn polygon từng thửa trước khi tính giao. Đồng thời đổi cách lấy "tổng diện tích thửa" dùng trong công thức: trước đây ưu tiên số `dien_tich_tren_ban_do` lưu sẵn (tính bằng Shoelace ở Python lúc import), giờ LUÔN lấy từ `thua_poly.area` (shapely, trên chính hình đã dùng để tính giao, sau khi sửa nếu cần) — để phép trừ "tổng − giao" luôn nhất quán trong cùng 1 bộ máy tính toán hình học, tránh 2 công thức khác nhau (Python shoelace thuần vs GEOS) xử lý hình không hoàn toàn hợp lệ theo 2 cách khác nhau, vốn có thể là nguồn gây lệch số như Minh gặp phải.

**QUAN TRỌNG — vẫn chưa xác minh được bằng số thật:** như đã báo trước, sandbox này không cài được `shapely` (không có mạng) nên **không thể chạy lại đúng dữ liệu Thửa 6 để xác nhận sau khi sửa có ra đúng 29.729,56 m² hay không**. Đây là 1 sửa lỗi có cơ sở kỹ thuật vững (buffer(0) là kỹ thuật tiêu chuẩn, rất phổ biến để xử lý đúng tình huống "hình gần hợp lệ" như nghi ngờ ở đây), nhưng không đảm bảo chắc chắn khớp chính xác con số Minh đưa ra. **Đề nghị Minh sau khi deploy: mở lại Bản đồ Mốc giới GPMB liên quan, bấm rà soát lại (sửa/lưu lại 1 lần để trigger tính năng rà soát), xem số mới ra bao nhiêu, rồi báo lại** — nếu vẫn lệch, cần thêm bước chẩn đoán sâu hơn (có thể cần tôi xem trực tiếp tọa độ thô của Thửa 6 và ranh giới Mốc giới GPMB tương ứng để so khớp từng đỉnh).

---

## Nguyên tắc thiết kế chung

1. **Mở rộng linh hoạt:** mọi bảng nghiệp vụ đều có cột `custom_fields` (JSON) để thêm thuộc tính phát sinh mà không cần sửa code ngay; trường dùng thường xuyên sẽ được nâng thành cột chính thức sau.
2. **GIS:** ranh giới không gian (thửa đất, dự án) lưu dạng text GeoJSON trong SQLite; tính toán không gian (diện tích, chồng lấn, thửa nằm trong dự án nào) dùng thư viện Python **Shapely**, không dùng PostGIS/SpatiaLite — giữ nguyên hạ tầng Railway + SQLite hiện tại để tránh rủi ro.
3. **Pháp lý dự án:** tận dụng module Tài liệu (`documents`, `doc_types`) đã có sẵn trong hệ thống, không tạo field text riêng cho văn bản pháp lý.
4. **Tiến độ dự án:** tính động (aggregate) từ trạng thái các Hồ sơ Hộ/Quyết định theo Thửa, không lưu thành cột cố định.
5. **Tính đơn giá/thành tiền tài sản:** là tính năng riêng, làm ở giai đoạn sau (chưa nằm trong phạm vi thiết kế này). Bảng Tài sản hiện tại chỉ lưu dữ liệu kiểm đếm khách quan.
6. **Nhận diện thửa trùng khi nhập liệu:** khi tạo thửa mới trong 1 dự án, hệ thống đối chiếu số tờ/số thửa với Thửa đất gốc đã có, cảnh báo và cho chọn liên kết hoặc tạo mới — đây là hành vi màn hình nhập liệu, không phải cấu trúc bảng.

---

## Nhóm 1 — Chủ thể & Nhân khẩu

### Bảng `bt_parties` — Chủ thể
Dùng chung cho chủ sử dụng đất và chủ tài sản (một người có thể vừa là chủ đất vừa là chủ tài sản, hoặc khác nhau).

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| loai_chu_the | string | cá nhân / hộ gia đình / tổ chức |
| ho_ten | string | tên cá nhân hoặc người đại diện hộ/tổ chức |
| gioi_tinh | string | |
| ngay_sinh | date | |
| so_cccd | string | |
| ngay_cap_cccd | date | |
| noi_cap_cccd | string | |
| dia_chi_thuong_tru | string | |
| so_dien_thoai | string | |
| ghi_chu | text | |
| custom_fields | JSON | |

### Bảng `bt_household_members` — Nhân khẩu
Thành viên trong hộ, gắn với 1 Chủ thể loại "hộ gia đình".

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| chu_the_id | int (FK → bt_parties) | hộ đại diện |
| ho_ten | string | |
| quan_he_voi_chu_ho | string | vợ/chồng, con, cha mẹ... |
| ngay_sinh | date | |
| so_cccd | string, nullable | có thể trống nếu trẻ em |
| ghi_chu | text | |
| custom_fields | JSON | |

---

## Nhóm 2 — Thửa đất & Bản đồ

### Bảng `bt_parcel_master` — Thửa đất gốc
Thực thể vật lý, độc lập với dự án — vì 1 thửa có thể bị thu hồi ở nhiều dự án khác nhau qua các năm.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | dùng làm "mã thửa gốc" xuyên dự án |
| so_to_hien_hanh | string | |
| so_thua_hien_hanh | string | |
| dia_chi_vi_tri | string | |
| toa_do_ranh_gioi | text (GeoJSON) | điểm hoặc đa giác ranh giới |
| ghi_chu | text | |
| custom_fields | JSON | |

### Bảng `bt_parcels` — Thửa đất theo dự án
Mỗi lần thửa gốc xuất hiện trong 1 đợt thu hồi là 1 dòng riêng (snapshot số liệu tại thời điểm đó).

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| parcel_master_id | int (FK → bt_parcel_master) | |
| project_id | int (FK → bt_projects) | |
| so_to / so_thua | string | tại thời điểm dự án này |
| loai_dat | string | đất ở, nông nghiệp, đất trồng cây lâu năm... |
| tong_dien_tich | real | m² |
| dien_tich_thu_hoi | real | |
| dien_tich_con_lai | real | |
| nguon_goc_su_dung | string | được giao / nhận chuyển nhượng / khai hoang... |
| so_gcn | string | |
| ngay_cap_gcn | date | |
| ghi_chu | text | |
| custom_fields | JSON | |

### Bảng `bt_parcel_owners` — nối Chủ thể ↔ Thửa đất (đồng sở hữu)
Gắn ở tầng "theo dự án" vì người đứng tên có thể thay đổi giữa các dự án.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| parcel_id | int (FK → bt_parcels) | |
| chu_the_id | int (FK → bt_parties) | |
| vai_tro | string | đại diện đứng tên / đồng sở hữu |
| ty_le_so_huu | real, nullable | %, để trống nếu không chia rõ |

### Bảng `bt_maps` — Bản đồ
Phiên bản dữ liệu về 1 thửa gốc theo từng loại/thời kỳ; nối vào thửa **gốc**, không phải thửa theo dự án.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| project_id | int (FK, nullable) | có thể không thuộc dự án nào (vd bản đồ giao ruộng thời kỳ trước) |
| loai_ban_do | string | GPMB / Trích lục / Giao ruộng thời kỳ trước / Khác |
| ten_ban_do | string | |
| ngay_lap | date | |
| don_vi_lap | string | đơn vị đo vẽ |
| ghi_chu | text | |
| custom_fields | JSON | |

### Bảng `bt_map_parcels` — nối Bản đồ ↔ Thửa đất gốc
1 bản đồ có thể phủ nhiều thửa; số liệu ghi tại thời điểm bản đồ đó (có thể khác bảng Thửa đất gốc hiện hành).

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| map_id | int (FK → bt_maps) | |
| parcel_master_id | int (FK, nullable) | trống = bản đồ chưa gắn thửa cụ thể |
| so_to_tren_ban_do | string | |
| so_thua_tren_ban_do | string | |
| dien_tich_tren_ban_do | real | |

### Bảng `bt_map_files` — file đính kèm của Bản đồ
1 bản đồ có thể có nhiều file (nhiều trang scan).

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| map_id | int (FK → bt_maps) | |
| file_path | string | |
| file_name | string | |
| uploaded_at | datetime | |

---

## Nhóm 3 — Tài sản trên đất

### Bảng `bt_assets` — Tài sản
Chỉ lưu dữ liệu kiểm đếm khách quan; không có đơn giá/thành tiền (việc tính toán bồi thường là tính năng riêng ở bước sau).

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| loai_tai_san_nhom | string | Nhà ở / Công trình xây dựng khác / Vật kiến trúc / Cây cối / Hoa màu |
| loai_tai_san_cu_the | string | vd "Nhà cấp 4 mái tôn", "Giếng khoan", "Xoài trên 5 năm tuổi" |
| chu_tai_san_id | int (FK → bt_parties) | có thể khác chủ sử dụng đất |
| don_vi_tinh | string | m², m³, m, cái, cây... |
| so_luong_khoi_luong | real | |
| thoi_diem_hinh_thanh | date | để đối chiếu với ngày thông báo thu hồi đất của dự án |
| tinh_trang_phap_ly | string | Đúng quy định / Sai mục đích SDD / Xây dựng-trồng trái phép / Khác |
| ngay_kiem_dem | date | |
| nguoi_kiem_dem | string | cán bộ đi kiểm đếm |
| ghi_chu | text | |
| custom_fields | JSON | |

### Bảng `bt_asset_parcels` — nối Tài sản ↔ Thửa đất theo dự án
1 tài sản có thể nằm trên nhiều thửa.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| asset_id | int (FK → bt_assets) | |
| parcel_id | int (FK → bt_parcels) | |

---

## Nhóm 4 — Dự án

### Bảng `bt_projects` — Dự án (mở rộng)
Bản thân là 1 thực thể không gian, không chỉ là nhãn nhóm.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| ten_du_an | string | |
| chu_dau_tu | string | |
| dia_diem | string | (đã có) |
| mo_ta | text | (đã có) |
| dien_tich_du_an | real | tổng diện tích theo pháp lý phê duyệt |
| ranh_gioi_du_an | text (GeoJSON) | ranh giới dự án |
| ngay_thong_bao_thu_hoi | date | mốc pháp lý — đối chiếu thời điểm hình thành tài sản |
| ngay_bat_dau | date | |
| ngay_ket_thuc_du_kien | date | |
| ghi_chu | text | |
| custom_fields | JSON | |
| created_at | datetime | (đã có) |

---

## Nhóm 5 — Quyền & Bồi thường/Hỗ trợ

Cấu trúc 2 tầng: **Hồ sơ Hộ** (đa số chính sách bồi thường/hỗ trợ tính theo hộ) chứa nhiều **Quyết định theo Thửa** (vì cơ quan có thẩm quyền có thể phê duyệt lệch thời điểm giữa các thửa trong cùng 1 hộ).

### Bảng `bt_dossiers` — Hồ sơ Hộ

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| project_id | int (FK → bt_projects) | |
| chu_the_id | int (FK → bt_parties) | hộ/chủ đại diện |
| tien_thuong_tien_do | real | theo hộ, có mức trần |
| tien_ho_tro_on_dinh_doi_song | real | tính theo tổng nhân khẩu hộ |
| tien_ho_tro_dao_tao_chuyen_doi_nghe | real | |
| tien_ho_tro_tai_dinh_cu | real | nếu phải di dời chỗ ở |
| tien_ho_tro_khac | real | |
| so_tien_tam_ung | real | |
| so_tien_da_chi_tra | real | |
| ngay_chi_tra | date | |
| co_don_y_kien | int (0/1) | (đã có) |
| noi_dung_y_kien | text | (đã có) |
| ghi_chu | text | |
| custom_fields | JSON | |
| created_at / updated_at | datetime | |

### Bảng `bt_parcel_decisions` — Quyết định theo Thửa
Con của Hồ sơ Hộ, gắn với 1 thửa cụ thể.

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| ho_so_ho_id | int (FK → bt_dossiers) | |
| parcel_id | int (FK → bt_parcels) | |
| so_quyet_dinh_pd | string | |
| ngay_quyet_dinh_pd | date | |
| tien_bt_dat | real | |
| tien_bt_tai_san | real | tổng hợp từ Tài sản gắn thửa này (bước tính toán sau) |
| trang_thai | string | tham chiếu `bt_status_config` (giữ nguyên) |
| ghi_chu | text | |

### Bảng `bt_dossier_persons` — nối Hồ sơ Hộ ↔ Người
Lưu điều kiện "đối tượng trực tiếp sản xuất nông nghiệp" (Nghị định 88/2024/NĐ-CP) — theo từng người, theo từng hồ sơ/dự án, vì luật xét điều kiện này "tại thời điểm phê duyệt phương án".

| Trường | Kiểu | Ghi chú |
|---|---|---|
| id | int (PK) | |
| ho_so_ho_id | int (FK → bt_dossiers) | |
| chu_the_id | int (FK, nullable) | |
| nhan_khau_id | int (FK, nullable) | đúng 1 trong 2 cột chu_the_id/nhan_khau_id có giá trị |
| la_doi_tuong_sxnn_truc_tiep | boolean | |
| ghi_chu | text | |

### Bảng `bt_status_config` — giữ nguyên
Không đổi so với hiện tại (danh mục trạng thái + màu sắc).

---

## Sơ đồ quan hệ tổng quát

```
bt_projects (Dự án, có ranh_gioi_du_an)
 ├─ bt_parcels (Thửa theo dự án) ── parcel_master_id ──▶ bt_parcel_master (Thửa gốc, có toa_do_ranh_gioi)
 │    ├─ bt_parcel_owners ──▶ bt_parties (Chủ thể)
 │    └─ bt_asset_parcels ──▶ bt_assets (Tài sản) ──▶ chu_tai_san_id ──▶ bt_parties
 │
 ├─ bt_maps (Bản đồ) ── bt_map_parcels ──▶ bt_parcel_master
 │    └─ bt_map_files
 │
 └─ bt_dossiers (Hồ sơ Hộ) ──▶ chu_the_id ──▶ bt_parties
      ├─ bt_parcel_decisions ──▶ bt_parcels
      └─ bt_dossier_persons ──▶ bt_parties / bt_household_members

bt_parties (Chủ thể) ──▶ bt_household_members (Nhân khẩu)
```

---

## Cập nhật 2026-07-15 (kết luận điều tra): lệch 37m² Thửa 6 — app tính đúng, chênh là do nguồn ranh giới khác nhau

Minh gửi trực tiếp file `21_05 RGQH New.kmz` (ranh giới mốc giới GPMB anh dùng để đối chiếu bằng phần mềm khác) và file Excel tọa độ thật của Thửa 6/Tờ 1 (39 đỉnh, VN-2000). Vì không cài được shapely trong sandbox này (không có mạng), đã tự viết một phép kiểm chứng **hoàn toàn độc lập, không dùng shapely**: quét lưới điểm mịn (point-in-polygon bằng ray-casting tự viết bằng numpy) trên toàn bộ Thửa 6, tính diện tích phần nằm trong ranh giới mốc giới lấy thẳng từ file KMZ gốc của Minh.

Các bước đã làm:
1. Giải nén KMZ, phát hiện ranh giới lưu dưới dạng `<LineString>` (không phải `<Polygon>`) — vòng khép kín 3933 đỉnh, tọa độ WGS84.
2. Quy đổi WGS84 → VN-2000 dùng đúng công thức đang chạy trong `server.py`. Kinh tuyến trục 105.75° (giả định trước đó cho khu vực Hà Nội) cho ra tọa độ lệch tới ~79km so với Thửa 6 — sai. Dò lại bằng cách so khớp không gian với tọa độ Excel thật thì **kinh tuyến trục đúng phải là 105.0°** (khớp chính xác vị trí, có thể do khu vực này thuộc địa giới Hà Tây cũ, dùng kinh tuyến trục 105° thay vì 105°45' của Hà Nội gốc).
3. Với ranh giới quy đổi đúng, quét lưới điểm ở nhiều độ phân giải khác nhau (0.033m đến 0.2m) để kiểm tra kết quả có ổn định không — đều cho ra **~29.766,6 m²**, khớp gần như tuyệt đối với số app tính ra ban đầu (29.766,67 m²), **không khớp với số 29.729,56 m² Minh đối chiếu từ phần mềm khác**.

**Kết luận:** với đúng ranh giới trong file KMZ Minh gửi, app tính đúng. Số liệu app ra khớp cả 2 cách tính độc lập (shapely trong app + lưới điểm tự viết ở đây). Fix `buffer(0)` sửa hình không hợp lệ thêm tuần trước không phải nguyên nhân thật (hình vốn đã hợp lệ, không có gì để sửa) — không gây hại nhưng không phải fix đúng chỗ.

Chênh lệch 37m² nhiều khả năng đến từ **phần mềm khác dùng một phiên bản ranh giới khác** với file KMZ này (số hóa lại, làm mượt đường biên, hoặc file cập nhật sau) — không phải lỗi tính toán trong app.

**Cần Minh xác nhận 2 việc:**
- Ranh giới anh dùng để đối chiếu trong phần mềm khác có đúng là file `21_05 RGQH New.kmz` này, cùng ngày/phiên bản không? Nếu khác file, đó là nguồn gây lệch.
- Kinh tuyến trục đang cấu hình cho dự án trong app hiện là bao nhiêu? Nếu đang để 105.75° thay vì 105.0°, cần sửa lại field dự án — dù bản đồ mốc giới đã import trước đó vẫn hiển thị đúng vị trí trên nền OSM (do lúc import dùng giá trị nào đó cho ra đúng), nhưng nếu field dự án đang lưu sai giá trị thì các lần import KML/KMZ sau này có nguy cơ bị lệch ~79km.

## Cập nhật 2026-07-15 (tính năng mới): import Bản đồ GPMB bằng GeoJSON — lấy Tờ/Thửa trực tiếp từ thuộc tính, không đoán từ tên

Minh xuất thử 1 thửa ra KMZ từ phần mềm CAD, phát hiện file gồm nhiều đoạn đường rời rạc (không phải 1 đa giác khép kín), khiến ranh giới import vào bị sai lệch so với bản Excel gốc. Xác nhận phần mềm CAD/đo đạc của Minh (AutoCAD, MicroStation, và phần mềm bản đồ khác) đều xuất được **1 đa giác khép kín riêng cho từng thửa**, nhưng Minh vẫn muốn Excel làm nguồn dữ liệu chính vì gán được Tờ/Thửa trực tiếp theo từng thửa. Yêu cầu: tìm 1 định dạng bản đồ vừa mang hình vừa mang chính xác 100% thuộc tính Tờ/Thửa.

Đã tra cứu Thông tư 09/2024/TT-BTNMT (chuẩn CSDL đất đai quốc gia) — quy định dùng GML hoặc GeoJSON cho dữ liệu không gian, XML/JSON mở rộng cho dữ liệu thuộc tính khi trao đổi dữ liệu đất đai. Chọn **GeoJSON** làm định dạng import mới (đơn giản hơn GML, không cần thư viện ngoài — chỉ dùng `json` chuẩn, đúng khuyến nghị của Bộ TN&MT) thay vì Shapefile (phức tạp hơn: nhiều file, tên trường DBF giới hạn 10 ký tự, cần thư viện ngoài `pyshp`).

**Cơ chế:** mỗi Feature trong file GeoJSON (FeatureCollection) có sẵn `geometry` (Polygon/MultiPolygon) VÀ `properties` (thuộc tính Tờ/Thửa gán sẵn bởi phần mềm CAD/đo đạc) — đọc thẳng từ `properties`, không đoán từ tên như KML. Tên thuộc tính khuyến nghị: `so_to`/`so_thua`; chấp nhận thêm vài tên đồng nghĩa (`to`/`thua`, `sheet`/`parcel`...) nhưng **khớp CHÍNH XÁC theo khoá đã chuẩn hoá** (bỏ dấu, chữ thường, bỏ ký tự đặc biệt), không phải "chứa chuỗi con" như cột Excel — để tránh khớp nhầm 1 thuộc tính không liên quan chỉ vì tên có chứa "to" (VD "toa_do", "tong_dt") — đã viết test riêng xác nhận việc này (`_GEOJSON_SO_TO_KEYS`/`_GEOJSON_SO_THUA_KEYS` trong `server.py`).

Tự nhận diện tọa độ trong file đang ở hệ WGS84 (kinh độ/vĩ độ, trị tuyệt đối ≤180/≤90) hay đã là VN-2000 (trị lớn) để quyết định có quy đổi theo Kinh tuyến trục của dự án hay dùng thẳng — vì tùy phần mềm mà GeoJSON xuất ra có thể ở 1 trong 2 hệ.

**Tích hợp:** `api_bt_map_parcels_import` giờ nhận 4 định dạng (.xlsx, .kml/.kmz, .geojson/.json) qua cùng 1 endpoint, cùng 1 luồng đối chiếu trùng/xác nhận ghi đè như trước. Thêm endpoint `GET /api/bt/gpmb-geojson-template` trả về file mẫu minh họa đúng cấu trúc + tên thuộc tính. Frontend: input file trong tab Bản đồ GPMB nhận thêm `.geojson,.json`, thêm nút tải file mẫu GeoJSON, cập nhật hướng dẫn trong modal.

Verify bằng test độc lập với dữ liệu thật (Thửa 6 Tờ 1, tọa độ Excel 39 đỉnh): dựng GeoJSON có `properties: {so_to:'1', so_thua:'6'}` + toạ độ VN-2000 gốc, chạy qua bản mirror của `_extract_geojson_groups` — ra đúng so_to/so_thua và diện tích khớp chính xác 34.644,95 m² (bằng Shoelace, không lệch). Cũng test: tự nhận WGS84 khi tọa độ là kinh/vĩ độ, tên thuộc tính có dấu ("Tờ"/"Thửa") vẫn khớp đúng, thuộc tính giả/không liên quan ("toa_do", "tong_dt") KHÔNG bị khớp nhầm thành so_to, và 2 Feature trùng Tờ/Thửa trong cùng file được tự đánh số phân biệt.

## Cập nhật 2026-07-16: Xã/Phường trở thành trường thật — sửa lỗi có thể gợi ý nhầm 2 thửa khác xã là 1 thửa

Minh đặt câu hỏi đúng trọng tâm: dự án khai báo nằm trên các xã nào, mỗi xã có 1 tập hợp mảnh Bản đồ GPMB riêng — vậy CSDL Bản đồ/Thửa đất/Tài sản/Bồi thường có cần phân chia theo xã không, vì Số tờ/Số thửa của Xã A và Xã B hoàn toàn có thể trùng nhau (cùng "Tờ 1 - Thửa 1") mà là 2 thửa khác nhau.

**Kiểm tra lại code thực tế trước khi trả lời (không đoán):** hệ thống trước đây CHƯA bắt buộc khai xã khi tạo dự án — "Xã" chỉ tồn tại dưới 2 dạng chữ tự do, không ràng buộc gì: ô "Địa điểm" của dự án (1 chuỗi duy nhất, không có cấu trúc) và ô "Nhóm bản đồ" của từng mảnh (free text, có gợi ý nhưng không bắt buộc). Quan trọng hơn: tính năng "gợi ý trùng thửa gốc" (`api_bt_parcel_master_search`, dùng khi thêm thửa trên Bản đồ GPMB để liên kết với `bt_parcel_master` — thửa gốc theo dõi xuyên suốt nhiều dự án/năm) tìm theo Tờ+Thửa TRÊN TOÀN BỘ CSDL, không lọc theo xã — xác nhận đúng rủi ro Minh nêu: Xã A Thửa 1 Tờ 1 và Xã B Thửa 1 Tờ 1 có thể bị gợi ý nhầm là cùng 1 thửa, nếu người dùng bấm liên kết nhầm sẽ làm hỏng dữ liệu 2 xã (gộp lịch sử 2 thửa hoàn toàn khác nhau làm 1).

Minh xác nhận muốn xây đầy đủ như mô tả (không chỉ vá lỗi gợi ý trùng).

**Thiết kế:**
- `bt_projects.danh_sach_xa` (JSON mảng tên xã) — khai 1 lần khi tạo/sửa dự án, mục "📍 Địa bàn hành chính" (ô nhập mỗi dòng 1 xã).
- `bt_maps.xa` — trường THẬT (không phải chữ tự do), bắt buộc với loại "Bản đồ GPMB" và "Bản đồ mốc giới GPMB" (2 loại có Tờ/Thửa thật sự tham gia sinh/đồng bộ Thửa đất — nơi xảy ra rủi ro), chọn từ dropdown lấy đúng theo `danh_sach_xa` của dự án đang mở (không tự gõ tay để tránh lỗi chính tả làm 2 tên khác nhau bị coi là 2 xã khác nhau, VD "Xã Chương Dương" vs "xã chương dương"). Khi lưu, nếu "Nhóm bản đồ" (nhãn hiển thị ở panel trái, giữ nguyên cơ chế cũ) để trống thì tự lấy theo Xã đã chọn — không phải sửa lại toàn bộ code nhóm hiển thị đang chạy tốt.
- `bt_parcels.xa` và `bt_parcel_master.xa` — được điền tự động theo `bt_maps.xa` của mảnh đã sinh/đồng bộ ra thửa đó (qua `_create_parcel_from_map_entry`/`_sync_parcel_from_map_entry`), không cần người dùng nhập tay.
- `api_bt_parcel_master_search` nhận thêm tham số `xa` — khi có, chỉ trả về thửa gốc CÙNG xã (hoặc thửa gốc cũ chưa xác định được xã, hiển thị kèm cảnh báo "⚠️ chưa rõ xã" ở frontend để người dùng tự xác nhận thay vì hệ thống tự động ẩn mất dữ liệu cũ). Luồng thêm thửa trên Bản đồ GPMB luôn truyền đúng xã của mảnh đang thao tác.
- Panel trái tab Bản đồ giờ hiện đủ "thư mục" cho MỌI xã đã khai trong dự án, kể cả xã chưa có mảnh bản đồ nào (đúng yêu cầu "tạo thư mục Bản đồ GPMB tương ứng") — không tạo bản ghi `bt_maps` rỗng giả, chỉ hiển thị nhóm rỗng ở UI dựa trên `danh_sach_xa`, tránh phải dọn dữ liệu rác nếu xã đó cuối cùng không dùng tới.

**Di trú dữ liệu cũ (backfill, chạy tự động 1 lần khi server khởi động, an toàn chạy lại nhiều lần):** các mảnh Bản đồ GPMB cũ đã dùng "Nhóm bản đồ" đúng như tên xã (Minh đã tự quy ước từ trước, VD "Xã Chương Dương") được copy thẳng sang cột `xa` mới; danh sách xã của mỗi dự án được suy ra từ các `xa` đã dùng trong các mảnh của dự án đó nếu dự án chưa tự khai; `bt_parcels.xa`/`bt_parcel_master.xa` được điền lại qua liên kết `bt_map_parcels`→`bt_maps.xa` đã có sẵn. Thửa đất cũ nhập tay ở tab Thửa đất (không qua Bản đồ GPMB) sẽ không suy luận được xã, để trống — không thể tự bịa dữ liệu.

Verify bằng SQLite in-memory thật (không chỉ mirror tay) cho 2 phần rủi ro nhất: (1) đúng kịch bản Minh nêu — Xã A và Xã B cùng có Tờ 1/Thửa 1, tìm theo xa=Xã A chỉ ra đúng 1 kết quả của Xã A, không lẫn Xã B; thửa gốc cũ chưa rõ xã vẫn hiện lên (không bị ẩn mất) khi tìm có xa; (2) toàn bộ script backfill chạy đúng trên schema mô phỏng thật — 2 mảnh nhóm theo 2 xã cũ được backfill đúng cột `xa`, danh sách xã dự án được suy ra đúng thứ tự, thửa đất/thửa gốc liên kết qua mảnh cũng nhận đúng xã. Cũng chạy `py_compile` xác nhận `server.py` không lỗi cú pháp sau các sửa đổi.

## Việc chưa nằm trong phạm vi thiết kế này (backlog)

- Tính năng tính đơn giá/thành tiền cho Tài sản (theo bảng giá tỉnh, hệ số bồi thường/hỗ trợ) → ghi vào `bt_parcel_decisions.tien_bt_tai_san`.
- Logic áp dụng chính sách hỗ trợ theo `tinh_trang_phap_ly` của tài sản (đúng quy định / sai mục đích / trái phép).
- Tính năng hiển thị bản đồ số từ dữ liệu GeoJSON (`toa_do_ranh_gioi`, `ranh_gioi_du_an`).
- Tính tiến độ dự án tự động từ trạng thái `bt_dossiers`/`bt_parcel_decisions`.

## Cập nhật 2026-07-16: Hiển thị Xã tại tab Thửa đất + bộ lọc kiểu Excel cho bảng Thửa đất

**Yêu cầu:** (1) Thêm trường Xã vào CSDL/hiển thị tại tab Thửa đất. (2) Xác nhận việc khai báo Xã khi import Bản đồ GPMB tự động điền Xã cho toàn bộ thửa sinh ra từ mảnh đó. (3) Thêm bộ lọc từng cột kiểu Microsoft Excel cho bảng Thửa đất.

**(1) + (2) — Hiển thị Xã:**
Backend đã có sẵn cột `xa` trên `bt_parcels` (thêm ở đợt schema Xã/Phường 2026-07-16 trước đó — xem phần "Xã/Phường trở thành trường thật" phía trên) và cả `api_bt_parcels_list` (`SELECT pl.*, ...`) lẫn `api_bt_parcel_detail` (`SELECT * FROM bt_parcels`) đã trả về cột này — không cần sửa backend. Toàn bộ luồng tự động điền Xã (khai báo Xã khi tạo/sửa Bản đồ GPMB → truyền qua `_create_parcel_from_map_entry`/`_sync_parcel_from_map_entry` → ghi vào `bt_parcels.xa` + backfill `bt_parcel_master.xa`) đã được xây và verify ở đợt trước; đợt này chỉ re-xác nhận bằng cách đọc lại toàn bộ call site (`api_bt_map_parcels_add`, `api_bt_map_parcels_update`, nhánh import Excel/KML/GeoJSON) — xác nhận cả 2 câu SELECT lấy `m['xa']`/`map_xa` từ `bt_maps` đều đã đúng.

Việc còn lại chỉ là frontend: thêm cột "Xã" vào bảng danh sách Thửa đất (`public/boi-thuong.html`, giữa Số thửa và Loại đất) và field "Xã" **chỉ đọc** vào modal Sửa/Thêm thửa đất, cùng nhóm với Số tờ/Số thửa/diện tích (sửa tại tab Bản đồ, không sửa trực tiếp ở đây) — đúng theo nguyên tắc "Bản đồ GPMB là nguồn duy nhất sinh Thửa đất" đã thống nhất trước đó.

**(3) — Bộ lọc kiểu Excel cho bảng Thửa đất:**
Thiết kế: mỗi cột dữ liệu (Số tờ, Số thửa, Xã, Loại đất, Tổng DT, DT thu hồi, Chủ sở hữu) có nút lọc (▾) ở tiêu đề cột, bấm vào mở popup gồm: ô tìm kiếm giá trị, "Chọn tất cả"/"Bỏ chọn", danh sách checkbox các giá trị riêng biệt trong cột, nút Áp dụng/Hủy. Lọc chạy hoàn toàn phía client trên mảng `parcelsList` đã tải từ server — không gọi lại API mỗi lần đổi bộ lọc.

Logic: AND giữa các cột đang lọc, OR giữa các giá trị được chọn trong cùng 1 cột (đúng ngữ nghĩa AutoFilter của Excel). Danh sách giá trị hiển thị trong dropdown của 1 cột được tính "cascade" — tức là chỉ tính trên các dòng đã thỏa mãn bộ lọc của *các cột khác* (không tính bộ lọc của chính cột đó), giống hành vi thực tế của Excel khi mở lại dropdown một cột đã lọc trước đó. Giá trị rỗng gom vào nhóm hiển thị `(Trống)` thay vì bị ẩn khỏi danh sách lọc. Cột số (Tổng DT, DT thu hồi) lọc theo giá trị đã làm tròn 1 chữ số thập phân — đúng với giá trị người dùng nhìn thấy trên bảng.

Có thanh trạng thái phía trên bảng hiện "Đang lọc theo N cột — hiển thị X/Y thửa" kèm link "Xóa tất cả bộ lọc" khi có ít nhất 1 cột đang lọc; nút lọc của cột đang có bộ lọc active được tô màu accent để dễ nhận biết. Bộ lọc được reset về rỗng mỗi khi chuyển sang dự án khác (tránh bộ lọc "dính" từ dự án cũ khiến bảng trông như trống dữ liệu).

**Verify:** viết bộ test độc lập bằng Node (trích xuất nguyên hàm lọc ra file test, không chỉnh sửa gì) — 12 assertion bao gồm: không lọc trả về đủ dòng, lọc 1 cột, AND nhiều cột, OR trong 1 cột, tính cascade đúng cho dropdown, gom giá trị rỗng vào `(Trống)`, lọc đúng theo giá trị số đã format, và trường hợp bỏ chọn hết 1 cột (dùng giá trị sentinel `__NONE_SELECTED__` để ẩn toàn bộ dòng mà không lỗi) — toàn bộ pass. Đã kiểm tra cú pháp JS toàn file bằng `node --check` sau khi trích xuất các thẻ `<script>` — không lỗi.

**Sự cố phát sinh khi sửa (đã khắc phục):** lần đầu ghi sentinel `' __none__'` (dấu cách + chuỗi) qua công cụ Edit, ký tự dấu cách bị mã hoá sai thành byte NUL (`\x00`) trong file HTML — phát hiện nhờ `Grep` báo "binary file matches". Khắc phục bằng cách đọc/ghi trực tiếp byte của file (Python) để thay thế đúng đoạn bị lỗi bằng sentinel không có ký tự đặc biệt (`__NONE_SELECTED__`), sau đó đọc lại để đồng bộ view, rồi kiểm tra lại không còn byte NUL nào trong file và cú pháp JS hợp lệ.

## Cập nhật 2026-07-16: Khôi phục + nâng cấp Bản đồ nền (tab riêng, đa nguồn, định vị người dùng)

**Vấn đề Minh báo:** sau khi xóa và tạo lại dự án, bản đồ nền (OpenStreetMap) không còn hiển thị ở tab 🗂️ Bản đồ — chỉ còn sơ đồ minh hoạ (SVG) với các đường viền cam và nhãn chữ chồng lên nhau trên nền tối, không có nền bản đồ thực nào.

**Nguyên nhân gốc:** `renderGpmbMapCanvas` trước đây chỉ chuyển sang chế độ Leaflet (bản đồ nền thực) khi dự án ĐÃ khai `kinh_tuyen_truc` (Kinh tuyến trục VN-2000) — nếu chưa khai (như một dự án vừa tạo lại), toàn bộ bản đồ nền bị ẩn hoàn toàn và rơi về chế độ SVG chỉ-vẽ-đường-viền. Đây không phải lỗi mất dữ liệu, mà là 1 điều kiện gate sai: bản đồ nền (tile ảnh) không cần biết Kinh tuyến trục — chỉ có việc CHUYỂN ĐỔI toạ độ VN-2000 của các thửa sang kinh/vĩ độ để VẼ ranh giới thửa đè lên mới cần.

**Sửa gốc:** tách điều kiện — `renderGpmbMapCanvas` giờ chuyển sang Leaflet ngay khi thư viện đã tải (`typeof L === 'object'`), không quan tâm đến Kinh tuyến trục. `renderGpmbLeafletMap(withGeo, ktt)` nhận `ktt=null` khi chưa khai, và trong trường hợp đó chỉ bỏ qua bước vẽ ranh giới thửa (giữ nguyên bản đồ nền), kèm dòng cảnh báo nhỏ ở tiêu đề bản đồ nhắc khai Kinh tuyến trục. SVG giờ chỉ còn là phương án dự phòng cuối cùng khi chính thư viện Leaflet không tải được (mất mạng).

**Yêu cầu 1 — bản đồ nền tự động có sẵn khi tạo dự án:** đạt được nhờ 2 cột mới `bt_projects.basemap_provider` (mặc định `'osm'`) và `basemap_visible` (mặc định `1`) — dự án mới tạo ra đã có giá trị mặc định ngay từ SQL `DEFAULT`, không cần người dùng thao tác gì.

**Yêu cầu 2 — tab "🛰️ Bản đồ nền" mới:** thêm ngay sau tab 🗂️ Bản đồ, KHÔNG bị khóa như Thửa đất/Tài sản/Hồ sơ Hộ (không phụ thuộc đã có Bản đồ GPMB hay chưa, vì đây là cấu hình cấp dự án). Gồm: checkbox bật/tắt bản đồ nền, danh sách radio chọn nguồn, và 1 bản đồ Leaflet xem trước riêng (`basemapPreviewMap`) để thấy ngay kết quả. Lựa chọn lưu ngay lập tức (không có nút Lưu riêng) qua endpoint mới `PUT /api/bt/projects/:id/basemap` — tách khỏi endpoint sửa dự án đầy đủ để phản hồi tức thời khi đổi lựa chọn.

**Yêu cầu 3 — mở rộng nguồn bản đồ nền:** giữ nguyên OpenStreetMap/Esri vệ tinh/OpenTopoMap/CartoDB tối đã có, thêm 2 nguồn mới: CartoDB Voyager và Esri World Street Map (giao diện nhiều màu, gần giống Google Maps). KHÔNG nhúng trực tiếp Google Maps chính thức vì yêu cầu API key trả phí theo Điều khoản dịch vụ của Google — đã ghi rõ trong UI tab Bản đồ nền, sẵn sàng tích hợp nếu Minh cung cấp API key sau này. Toàn bộ 6 nguồn khai báo tập trung tại `GPMB_BASEMAP_PROVIDERS` (dùng chung cho cả map chính và map xem trước, tránh lặp code — thay cho hàm `buildGpmbBasemaps` cũ chỉ phục vụ 1 map).

**Yêu cầu zoom (kiểm tra lại, không viết lại):** rà lại code cũ theo đúng yêu cầu của Minh — phát hiện tính năng zoom % (thanh trượt + nhập số thủ công + nút +/- gốc của Leaflet) đã được xây dựng đầy đủ và đúng từ trước (`GpmbZoomPercentControl`, việc "biến mất" trên màn hình chỉ là hệ quả của lỗi gốc ở trên — vì cả bản đồ Leaflet lẫn control zoom đều không được khởi tạo khi rơi vào chế độ SVG). Quyết định GIỮ NGUYÊN code này (không xóa viết lại) vì đã đúng, chỉ bổ sung cùng control cho map xem trước ở tab mới, và thêm CSS tối màu cho nút +/- gốc của Leaflet (`.leaflet-bar a`) — trước đó khi nút này hiển thị sẽ bị sáng trắng lạc tông với theme tối của app.

**Yêu cầu 4 — định vị vị trí người dùng:** thêm `GpmbLocateControl` (nút 📍 tự viết, dùng thẳng `navigator.geolocation` — không cần thư viện ngoài): bấm 1 lần lấy vị trí + theo dõi liên tục (chấm xanh + vòng tròn bán kính sai số cập nhật theo GPS di chuyển), bấm lại lần 2 dừng theo dõi. Gắn vào cả map chính lẫn map xem trước. **Lưu ý đã ghi trong code:** Geolocation API của trình duyệt chỉ hoạt động trên kết nối HTTPS hoặc localhost — nếu server chạy HTTP thường trên mạng LAN nội bộ, tính năng này có thể bị trình duyệt chặn hoặc báo lỗi.

**Verify:** `py_compile server.py` sạch; test SQLite in-memory riêng cho migration + endpoint `basemap` (default đúng, update toàn phần đúng, update từng phần không đụng field còn lại — đều pass). Với `boi-thuong.html`, bash-mounted view của file bị đơ giữa chừng phiên (xem [[sandbox_file_sync_gotcha]], lần 4) nên việc kiểm tra cú pháp JS/HTML được làm thủ công bằng Grep (xác nhận đúng 1 cặp thẻ `<script>...</script>`, không còn code cũ `buildGpmbBasemaps`/`L.control.layers(basemaps`, mọi biến/hàm mới chỉ khai báo đúng 1 lần) + đọc lại toàn bộ vùng code đã sửa bằng Read tool để soát ngoặc/logic thủ công.

## Cập nhật 2026-07-16 (tiếp): Bản đồ nền → panel trong tab Bản đồ, nhãn thửa 5 trường tự co giãn, 2 loại warning liên kết thửa↔bản đồ, quét lại toàn xã khi sửa/xóa bản đồ

Minh gửi 4 yêu cầu sửa/mở rộng dựa trên bản dựng "Bản đồ nền" nói trên (kèm ảnh chụp màn hình khoanh đỏ):

**1. Sửa lại vị trí Bản đồ nền:** Minh phản hồi tab "🛰️ Bản đồ nền" riêng (mục Yêu cầu 2 ở trên) không đúng ý — chỉ muốn gộp vào tab 🗂️ Bản đồ hiện có, không tách tab mới. Đã gỡ bỏ hoàn toàn tab riêng (`tab-basemap`, `basemapPreviewMap`, `loadBasemapTab`, `initBasemapPreviewMap`) và chuyển thành 1 panel thu gọn được (▸/▾) ở cuối cột trái của tab Bản đồ (`gpmb-basemap-panel`, `toggleGpmbBasemapPanel()`), thao tác trực tiếp trên `gpmbLeafletMap` — chỉ còn 1 bản đồ Leaflet duy nhất trong toàn tab thay vì 2.

**2. Nhãn thửa 5 trường, tự co giãn vừa trong thửa (không còn ẩn/hiện theo % zoom):** thay cơ chế cũ (`GPMB_LABEL_MIN_PCT`, ẩn nhãn khi zoom ≤178%) bằng nhãn LUÔN hiển thị, tự tính lại `scale()` mỗi khi zoom map thay đổi (`updateGpmbLabelScaling()`, lắng nghe sự kiện `zoomend`) sao cho khung nhãn vừa khít bên trong đường bao ngoài (outer ring) của thửa, tâm nhãn trùng tâm hình học (centroid) của thửa — dùng `L.divIcon` neo tại centroid + `transform: translate(-50%,-50%) scale(s)` trên 1 `<div>` con TÁCH RIÊNG khỏi phần tử Leaflet tự quản lý vị trí (tránh xung đột 2 transform). `s` tính bằng cách đo kích thước tự nhiên (`offsetWidth/offsetHeight` ở scale 1) so với bounding-box hiện tại của polygon trên màn hình (`latLngToContainerPoint`), giới hạn trong khoảng [0.3, 1.5] để không quá nhỏ đọc không được hay quá to tràn ra ngoài thửa nhỏ. Nội dung nhãn gồm đúng 5 trường theo yêu cầu: Tờ/Thửa, DT thu hồi, Loại đất, Chủ sử dụng — chủ sử dụng dùng `text-overflow:ellipsis` + `title` (tooltip hiện đầy đủ khi hover) để xử lý tên dài nhiều ký tự mà không phá vỡ bố cục nhãn.

**3. Cảnh báo liên kết Thửa đất ↔ Bản đồ GPMB (2 chiều, tự động, không cần thao tác thủ công gỡ):** tận dụng cột có sẵn `bt_map_parcels.parcel_id` (nullable) làm "nguồn sự thật" sống — không thêm cờ lưu trữ mới, nhờ vậy trạng thái cảnh báo LUÔN khớp dữ liệu hiện tại, tự biến mất khi dữ liệu được khôi phục đúng mà không cần nút "dismiss" nào:
- **Case A — thửa mất bản đồ:** Bản đồ GPMB bị xóa (hoặc thửa chưa từng được vẽ trên bản đồ nào) → `bt_parcels` không còn `bt_map_parcels` nào trỏ tới qua 1 bản đồ loại 'Bản đồ GPMB'. Cờ `has_gpmb_map` (EXISTS-subquery, tính ngay trong `api_bt_parcels_list`/`api_bt_parcel_detail`, không cache) = false → tab Thửa đất hiện badge ⚠️ đỏ cạnh Số tờ trong bảng (`row-gpmb-warn`, `gpmb-warn-badge`) và banner cảnh báo đỏ đầu modal sửa thửa (`parcel-warn-banner`) với nội dung đúng câu Minh yêu cầu.
- **Case B — bản đồ mất thửa:** hồ sơ Thửa đất (`bt_parcels`) bị xóa thủ công ở tab Thửa đất trong khi ô thửa vẫn còn trên Bản đồ GPMB → `bt_map_parcels.parcel_id` thành NULL (đã có sẵn từ `api_bt_parcels_delete`, xem code cũ). Trên bản đồ Leaflet, thửa loại này được tô đen (`fillColor:'#000'`, viền đỏ đứt nét) và nhãn đổi màu đỏ (`gpl-warn`) với dòng "Chưa có hồ sơ thửa đất" thay cho DT/loại đất/chủ SD.

Cả 2 cảnh báo tính lại mỗi lần tải dữ liệu (không lưu trạng thái) — tự "dỡ bỏ" đúng như yêu cầu khi Bản đồ GPMB được vẽ/tải lại (Case A) hoặc thửa đất được thêm/liên kết lại (Case B), không cần cơ chế dismiss riêng.

**4. Quét lại diện tích thu hồi TOÀN XÃ khi sửa/xóa Bản đồ GPMB hoặc Bản đồ mốc giới GPMB:** trước đây việc rà soát diện tích thu hồi (cơ chế giao đa giác Shapely, xem mục Mốc giới GPMB phía trên) chỉ chạy trong 2 tình huống hẹp — (a) người dùng tự sửa liên kết/hướng tính của 1 Bản đồ mốc giới GPMB cụ thể (chỉ tính lại đúng các mảnh bản đồ đó khai `mocgioi_manh_ids`), (b) xóa 1 Bản đồ mốc giới GPMB (chỉ tính lại đúng các mảnh nó từng khai liên kết) — và hoàn toàn KHÔNG kích hoạt khi sửa/xóa 1 Bản đồ GPMB (mảnh trích đo). Thêm hàm `_compute_xa_recompute(db, project_id, xa)`: gom TOÀN BỘ Bản đồ GPMB (mảnh) đang có trong đúng 1 xã của 1 dự án, rồi tái dùng nguyên `_compute_mocgioi_recompute_for_manh_ids` (không viết lại công thức giao đa giác) — hàm này tự tính theo (các) Bản đồ mốc giới GPMB còn phủ mỗi mảnh, và đề xuất về 0 với mảnh không còn bản đồ mốc giới nào phủ. `api_bt_maps_update`/`api_bt_maps_delete` giờ tự gọi hàm này (ghi lại xã CŨ trước khi ghi đè để quét cả xã cũ lẫn xã mới nếu bản đồ đổi xã) và trả `xa_diffs`/`xa_targets` kèm response — KHÔNG tự ghi CSDL, chỉ để frontend hỏi xác nhận qua popup có sẵn (`modal-mocgioi-confirm`, tái dùng nguyên UI, thêm mode `'xa'`) rồi áp dụng qua endpoint mới `POST /api/bt/xa/apply-recompute` (tự tính lại từ đầu tại thời điểm áp dụng, không tin số diffs cũ phía client, đúng nguyên tắc an toàn nhất quán với các endpoint rà soát khác trong hệ thống).

**Verify:** với `server.py`, bash-mounted view bị đơ giữa phiên KHÔNG do bash-write (xem [[sandbox_file_sync_gotcha]], lần 5) — dùng Grep xác nhận mọi định danh mới (`_compute_xa_recompute`, `api_bt_xa_apply_recompute`, route `/api/bt/xa/apply-recompute`) chỉ khai báo đúng 1 lần và đã nối dây đủ; đọc lại thủ công bằng Read tool toàn bộ vùng `api_bt_maps_update`/`api_bt_maps_delete`/2 hàm mới để soát thụt lề/ngoặc; viết script SQLite in-memory độc lập ở `/tmp` xác nhận: (a) câu SQL lấy đúng danh sách mảnh theo `project_id+xa`, không lẫn xã khác hay lẫn bản đồ mốc giới, (b) logic chọn `xa_targets` khi cập nhật xử lý đúng cả trường hợp đổi xã (quét cả xã cũ lẫn xã mới), (c) việc gộp diffs từ nhiều xã dedupe đúng theo `link_id`. Với `boi-thuong.html`, dùng Grep xác nhận không còn tham chiếu cơ chế cũ (`GPMB_LABEL_MIN_PCT`, `hide-parcel-labels`, `mocgioi_diffs`/`mocgioi_manh_ids` trong luồng xóa bản đồ) và mọi định danh mới (`gpmbParcelLabelHtml`, `gpmbLabelEntries`, `updateGpmbLabelScaling`, `has_gpmb_map`, `showXaDiffsConfirm`, `pendingXaTargets`) chỉ khai báo/nối dây đúng chỗ.

## Cập nhật 2026-07-16 (tiếp): Chỉ Bản đồ GPMB mới trích xuất Tờ/Thửa; xóa mục khai báo Nhóm bản đồ

Minh gửi thêm 2 yêu cầu, kèm 3 ảnh chụp minh hoạ (form khai Nhóm bản đồ, danh sách đối tượng bản đồ mốc giới GPMB hiện đang bị hiện nhãn "Tờ - Thửa GEO-N" kỳ lạ):

**1. Chỉ Bản đồ GPMB mới có khái niệm Tờ/Thửa thật; 3 loại bản đồ còn lại chỉ đánh số thứ tự + diện tích.** Trước đây mọi loại bản đồ (kể cả Bản đồ mốc giới GPMB, Bản đồ địa chính, Bản đồ khác) đều bị bắt trích xuất/đoán Tờ/Thửa như Bản đồ GPMB — riêng nhánh import GeoJSON, khi properties của Feature không có gì đoán được (trường hợp bình thường với 1 bản đồ mốc giới không có khái niệm thửa), sẽ rơi vào nhãn tạm xấu kiểu `GEO-1`, `GEO-2`... rồi UI hiển thị thành "Tờ - Thửa GEO-1" (so_to rỗng) — đúng như ảnh Minh chụp gửi kèm.

Sửa gốc theo hướng: chỉ `loai_ban_do == 'Bản đồ GPMB'` mới đoán/đọc Tờ/Thửa, 3 loại còn lại luôn đánh số thứ tự đơn giản (1, 2, 3... theo đúng thứ tự đọc được trong file), không đụng đến tên Placemark KML hay properties GeoJSON dù chúng có sẵn giá trị hợp lệ hay không.

Backend (`server.py`): `_extract_kml_groups`/`_extract_geojson_groups` nhận thêm tham số `is_gpmb` (mặc định `True` để tương thích ngược) — khi `False`: KML bỏ qua `_kml_guess_so_to_so_thua` hoàn toàn, đánh số theo bộ đếm toàn cục `idx` (tăng dần qua mọi ring hợp lệ trong file); GeoJSON bỏ qua đọc `properties` hoàn toàn (kể cả khi Feature CÓ properties hợp lệ), đánh số theo bộ đếm `obj_idx` tương tự. `api_bt_map_parcels_import` tính `is_gpmb = m['loai_ban_do'] == 'Bản đồ GPMB'` ngay sau khi tra map, truyền vào cả 2 hàm trên, và sửa mọi chỗ dựng nhãn hiển thị lỗi/trùng (`skipped_short`, `conflicts`) để không còn ghép chữ "Tờ/Thửa" khi `is_gpmb=False` — thay bằng "Đối tượng {số}".

Nhánh Excel (mỗi dòng 1 đỉnh, gom theo cột Tờ/Thửa liên tiếp) CỐ Ý giữ nguyên cơ chế cột Tờ/Thửa làm khoá gom nhóm nội bộ cho cả 4 loại bản đồ — đây là quyết định phạm vi có chủ đích (không được hỏi trước, nêu rõ ở đây): định dạng "mỗi dòng 1 đỉnh" cần MỘT khoá nào đó để biết ranh giới giữa 2 polygon liên tiếp, và cột Tờ/Thửa của file mẫu hiện có là khoá duy nhất khả dụng — không viết lại toàn bộ cơ chế gom nhóm Excel trong lượt này. Chỉ nhãn HIỂN THỊ cho các giá trị này (ở UI, và ở thông báo lỗi/trùng phía backend) không còn ghi "Tờ/Thửa" nữa với bản đồ không phải GPMB — dữ liệu Tờ/Thửa trong file Excel với các bản đồ này chỉ còn ý nghĩa là khoá gom nhóm nội bộ, không hiển thị nguyên văn.

Frontend (`boi-thuong.html`): `gpmbParcelLabel(p, isGpmb=true, idx)` và `gpmbParcelLabelHtml(p, isGpmb=true, idx)` (nhãn rút gọn cho SVG/preview và nhãn đầy đủ cho Leaflet) đều nhận thêm 2 tham số — khi `isGpmb=false` chỉ hiện "Đối tượng {idx}" + diện tích, bỏ hẳn Tờ/Thửa/DT thu hồi/loại đất/chủ SD (những trường này không tồn tại có ý nghĩa với bản đồ không phải GPMB). `renderGpmbMapCanvas` tính `isGpmb`/`idx` (vị trí trong danh sách của từng bản đồ) ngay khi dựng mảng `withGeo`, truyền xuống cả `renderGpmbSvgCanvas` và `renderGpmbLeafletMap`. Modal sửa bản đồ: ẩn hẳn 2 ô nhập Số tờ/Số thửa và ô Diện tích thu hồi khi loại bản đồ không phải GPMB (`onGpmbLoaiChange()` toggle 3 wrapper mới `gpf-so-to-wrap`/`gpf-so-thua-wrap`/`gpf-dt-thu-hoi-wrap`), đổi nhãn ô Diện tích còn lại từ "Diện tích thửa" sang "Diện tích polygon"; `submitGpmbParcelRow()` với bản đồ không phải GPMB tự đánh số thứ tự (giữ số cũ khi sửa, số tiếp theo khi thêm) thay vì đọc từ 2 ô đã ẩn, bỏ điều kiện bắt buộc nhập Tờ/Thửa. `renderGpmbParcelsList()`/`renderGpmbCombinedPreview()` cùng đổi nhãn danh sách/chú thích xem trước theo `isGpmb`.

**Bug thật phát hiện và sửa nhân tiện lúc này (không phải yêu cầu ban đầu của Minh, nhưng là hệ quả trực tiếp của thiết kế cũ):** `renderGpmbLeafletMap`'s cờ cảnh báo Case B (`isWarn = !p.parcel_id`, xem mục "2 loại warning" ở trên) trước đây KHÔNG kiểm tra loại bản đồ — vì `p.parcel_id` LUÔN rỗng với 3 loại bản đồ không phải GPMB (chúng không bao giờ sinh Thửa đất, theo đúng thiết kế), mọi polygon trên các bản đồ này sẽ bị tô đen/viền đỏ đứt nét + nhãn "Chưa có hồ sơ thửa đất" một cách SAI — dù đó là hành vi hoàn toàn bình thường, không phải lỗi dữ liệu. Sửa: `isWarn = isGpmb && !p.parcel_id`.

**2. Xóa mục khai báo "Nhóm bản đồ (đầu mục, tùy chọn)" khỏi UI — nhóm bản đồ giờ theo Xã trực tiếp.** Xoá hẳn ô nhập `gf-nhom-ban-do` + `<datalist>` gợi ý khỏi form Sửa bản đồ, hàm `populateGpmbNhomOptions()` (dựng datalist, nay chết hoàn toàn), và mọi điểm đọc/ghi giá trị này ở frontend (`openGpmbModal` không còn set giá trị field khi sửa, `saveGpmbMap` không còn gửi `nhom_ban_do` trong payload). `groupKeyOf(m)` (hàm quyết định nhóm hiển thị ở panel trái) đổi từ đọc `m.nhom_ban_do` sang đọc thẳng `m.xa` — vừa khớp đúng ý "nhóm theo xã" của Minh, vừa tránh trường hợp dữ liệu cũ (bản đồ có `nhom_ban_do` tự gõ tay khác `xa` từ trước khi tính năng Xã ra đời) còn hiển thị nhầm nhóm cũ cho đến lần lưu lại tiếp theo.

Backend KHÔNG bị đụng đến — `api_bt_maps_create`/`api_bt_maps_update` từ trước đã có sẵn `nhom_ban_do = body.get('nhom_ban_do', '') or xa`, nên khi frontend đơn giản là không còn gửi field này, backend tự động dùng `xa` làm `nhom_ban_do`, đúng ý "nhóm theo xã" mà không cần sửa gì thêm. Cột `bt_maps.nhom_ban_do` vẫn giữ nguyên trong schema (không xoá) — vẫn được backend tự đồng bộ = `xa` ở mọi lần lưu, chỉ không còn là 1 mục khai báo độc lập ở UI nữa.

**Verify:** viết script Python độc lập ở `/tmp/verify_nogpmb/test.py` mô phỏng đúng logic nhánh `is_gpmb` mới trong `_extract_geojson_groups` — xác nhận: `is_gpmb=True` đọc/đoán `so_thua` như cũ (kể cả fallback `GEO-N` khi thiếu property); `is_gpmb=False` bỏ qua HOÀN TOÀN properties (dù Feature có sẵn `so_thua` hợp lệ), chỉ đánh số 1,2,3... — cả 2 test pass. Với `boi-thuong.html`, bash-mounted view lại bị đơ giữa phiên (claim 3930 dòng trong khi Grep tìm thấy `</html>` thật ở dòng 4384 — đúng mẫu hình đã ghi trong [[sandbox_file_sync_gotcha]]), nên dùng Grep xác nhận: (a) toàn bộ 10 điểm dùng `isGpmb` trong `renderGpmbMapCanvas`/`renderGpmbSvgCanvas`/`renderGpmbLeafletMap`/`onGpmbLoaiChange`/`submitGpmbParcelRow`/`renderGpmbParcelsList`/`renderGpmbCombinedPreview`/`askDeleteGpmbMap` (chỗ có sẵn từ trước) nối dây nhất quán; (b) không còn tham chiếu nào tới `nhom_ban_do`/`nhom-ban-do`/`gpmb-nhom-options`/`populateGpmbNhomOptions` ngoài các dòng comment giải thích quyết định bỏ field; đọc lại thủ công bằng Read tool toàn bộ các hàm đã sửa để soát ngoặc/thụt lề.
