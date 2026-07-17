/*
 * Hiệu ứng "đang xử lý" (pending overlay) dùng chung cho TOÀN BỘ ứng dụng Web_cham_cong.
 * Theo yêu cầu của Minh (2026-07-17): mọi thao tác gọi lên server mà mất >2 giây mới xong sẽ tự động
 * hiện 1 overlay toàn màn hình với biểu tượng "PTDA" (animation loading) — không cần mỗi trang/mỗi nút
 * tự cài đặt riêng.
 *
 * Cách hoạt động: file này chỉ cần include 1 lần bằng <script src="/pending-loader.js"></script> ở đầu
 * <head> của mỗi trang (index.html, boi-thuong.html, cay.html, docs.html). Nó tự:
 *   1) Chèn CSS + overlay HTML vào trang (không cần sửa gì thêm ở HTML/CSS của từng trang).
 *   2) "Đánh chặn" (monkey-patch) window.fetch — TOÀN BỘ code hiện tại của app gọi API đều qua fetch
 *      (đã rà soát, không nơi nào dùng XMLHttpRequest), nên chặn ở đây là đủ, không cần sửa từng lời gọi.
 *   3) Với mỗi lời gọi fetch: đặt hẹn giờ 2000ms — nếu request CHƯA xong khi hẹn giờ bắn, mới hiện
 *      overlay (request nhanh hơn 2s sẽ không thấy overlay, giữ nguyên trải nghiệm mượt như cũ). Đếm số
 *      request đang "chạy quá 2s" cùng lúc — chỉ ẩn overlay khi KHÔNG còn request nào như vậy (tránh 1
 *      request nhanh ẩn mất overlay trong khi request khác vẫn đang chạy lâu).
 *
 * Không đụng tới các overlay "bận" riêng đã có sẵn của từng trang (VD #bt-busy-overlay ở tab Bồi thường,
 * hiện NGAY khi bắt đầu import thay vì đợi 2s, vì import vốn biết trước là sẽ lâu) — xem isSuppressed().
 */
(function () {
  if (window.__ptdaPendingLoaderInstalled) return;
  window.__ptdaPendingLoaderInstalled = true;

  const PENDING_DELAY_MS = 2000;
  const OVERLAY_ID = 'ptda-pending-overlay';

  const STYLE = `
#${OVERLAY_ID}{position:fixed;inset:0;z-index:999999;display:flex;align-items:center;justify-content:center;
  background:rgba(10,16,28,.55);backdrop-filter:blur(2px);-webkit-backdrop-filter:blur(2px);
  opacity:0;pointer-events:none;transition:opacity .18s ease;font-family:'Be Vietnam Pro',system-ui,-apple-system,Segoe UI,Roboto,Arial,sans-serif}
#${OVERLAY_ID}.ptda-show{opacity:1;pointer-events:all}
#${OVERLAY_ID} .ptda-pending-box{display:flex;flex-direction:column;align-items:center;gap:14px}
#${OVERLAY_ID} .ptda-pending-badge{position:relative;width:76px;height:76px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  background:radial-gradient(circle at 32% 28%,#22355c,#0f1e36 72%);
  box-shadow:0 8px 28px rgba(0,0,0,.45),inset 0 0 0 1px rgba(196,136,58,.35);
  animation:ptda-pulse 1.6s ease-in-out infinite}
#${OVERLAY_ID} .ptda-pending-badge::before{content:'';position:absolute;inset:-6px;border-radius:50%;
  border:3px solid transparent;border-top-color:#C4883A;border-right-color:rgba(196,136,58,.35);
  animation:ptda-spin .9s linear infinite}
#${OVERLAY_ID} .ptda-pending-badge span{position:relative;font-weight:800;font-size:15px;letter-spacing:.5px;
  color:#F8EFE2;text-shadow:0 1px 2px rgba(0,0,0,.4)}
#${OVERLAY_ID} .ptda-pending-text{color:#F8EFE2;font-size:14px;font-weight:500;letter-spacing:.2px;
  display:flex;align-items:baseline;gap:2px;text-shadow:0 1px 3px rgba(0,0,0,.5)}
#${OVERLAY_ID} .ptda-dots span{animation:ptda-dot 1.4s infinite;opacity:0}
#${OVERLAY_ID} .ptda-dots span:nth-child(2){animation-delay:.2s}
#${OVERLAY_ID} .ptda-dots span:nth-child(3){animation-delay:.4s}
@keyframes ptda-spin{to{transform:rotate(360deg)}}
@keyframes ptda-pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.06)}}
@keyframes ptda-dot{0%,80%,100%{opacity:0}40%{opacity:1}}
`;

  function injectStyle() {
    if (document.getElementById('ptda-pending-style')) return;
    const styleEl = document.createElement('style');
    styleEl.id = 'ptda-pending-style';
    styleEl.textContent = STYLE;
    document.head.appendChild(styleEl);
  }

  function buildOverlay() {
    let el = document.getElementById(OVERLAY_ID);
    if (el) return el;
    el = document.createElement('div');
    el.id = OVERLAY_ID;
    el.innerHTML =
      '<div class="ptda-pending-box">' +
        '<div class="ptda-pending-badge"><span>PTDA</span></div>' +
        '<div class="ptda-pending-text">Đang xử lý<span class="ptda-dots"><span>.</span><span>.</span><span>.</span></span></div>' +
      '</div>';
    document.body.appendChild(el);
    return el;
  }

  function mount() {
    injectStyle();
    return buildOverlay();
  }

  let overlayEl = null;
  function ensureOverlay() {
    if (!overlayEl) overlayEl = mount();
    return overlayEl;
  }
  if (document.body) {
    ensureOverlay();
  } else {
    document.addEventListener('DOMContentLoaded', ensureOverlay);
  }

  // Không hiện overlay chung nếu trang đang tự hiện 1 overlay "bận" riêng của nó (đã hiện SẴN trước khi
  // request bắt đầu, VD import Excel/bản đồ ở tab Bồi thường) — tránh 2 lớp nền tối chồng lên nhau.
  function isSuppressed() {
    const known = document.getElementById('bt-busy-overlay');
    if (known && getComputedStyle(known).display !== 'none') return true;
    return false;
  }

  let pendingCount = 0; // số request ĐANG chạy quá PENDING_DELAY_MS mà chưa xong

  function showOverlay() {
    const el = ensureOverlay();
    if (isSuppressed()) return;
    el.classList.add('ptda-show');
  }
  function maybeHideOverlay() {
    if (pendingCount <= 0 && overlayEl) overlayEl.classList.remove('ptda-show');
  }

  function trackPromise(promise) {
    let settled = false;
    let crossedThreshold = false;
    const timer = setTimeout(function () {
      if (settled) return;
      crossedThreshold = true;
      pendingCount++;
      showOverlay();
    }, PENDING_DELAY_MS);
    const finish = function () {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      if (crossedThreshold) {
        pendingCount = Math.max(0, pendingCount - 1);
        maybeHideOverlay();
      }
    };
    promise.then(finish, finish);
  }

  if (typeof window.fetch === 'function') {
    const origFetch = window.fetch.bind(window);
    window.fetch = function () {
      const p = origFetch.apply(window, arguments);
      trackPromise(p);
      return p;
    };
  }
})();
