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

## Việc chưa nằm trong phạm vi thiết kế này (backlog)

- Tính năng tính đơn giá/thành tiền cho Tài sản (theo bảng giá tỉnh, hệ số bồi thường/hỗ trợ) → ghi vào `bt_parcel_decisions.tien_bt_tai_san`.
- Logic áp dụng chính sách hỗ trợ theo `tinh_trang_phap_ly` của tài sản (đúng quy định / sai mục đích / trái phép).
- Tính năng hiển thị bản đồ số từ dữ liệu GeoJSON (`toa_do_ranh_gioi`, `ranh_gioi_du_an`).
- Tính tiến độ dự án tự động từ trạng thái `bt_dossiers`/`bt_parcel_decisions`.
