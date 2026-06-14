--[[
  device/main.lua — Synesthetic Familiar on-device render loop.

  ARD §5.1 (on-device spec), §5.2 (wire format), §5.5 (render spec).
  Sprite position and animation spec from Da5id — sprites/README.md.

  Week 1 scope: FAMILIAR_UPDATE decode → sprite bob with full mood rendering
  (all four mood enums: neutral/calm/stressed/attention — palette + per-mood
  bob frequency).  Host harness mock-cycles NEUTRAL→CALM→STRESSED to drive
  this.  Genuinely deferred: halo glow (Week 2 calm), edge fraying (Week 2
  stress), attention jump (Week 2-3), double-tap FAMILIAR_RESET (Week 3).
  Week 3 adds: double-tap FAMILIAR_RESET, IMU-peak callback.

  Da5id sprite swap-in: set SPRITE_BITMAP_READY = true and populate
  SPRITE_BITMAP (packed bytes) once frame.display.bitmap() format is
  confirmed (ARD §10 open question #2 — see SDK gap comment below).

  Owner: Ng
--]]

-- ─── SDK gap flags (ARD §10) ──────────────────────────────────────────────────
--
--  GAP-1  RESOLVED (2026-06-12, Ng): frame.imu.tap_callback(func) confirmed in
--         Halo Lua stdlib (halo_emulator/stubs/imu.py, brilliant_sdk main).
--         Fires once per hardware tap — no built-in N-count param.
--         Double-tap FAMILIAR_RESET wired at startup via 350ms window accumulator.
--         ATTENTION-on-IMU-peak: render-loop poll of frame.imu.raw() at 20fps
--         (≤50ms latency, meets ARD §10 Q1 target).
--
--  GAP-2  frame.display.bitmap() pixel-buffer format: nibble-packed 4-bit
--         indexed (Da5id's proposed format) NOT yet confirmed against Halo
--         firmware.  Week 1 renders with set_pixel() loop — always correct.
--         Swap in bitmap() when format is confirmed; no other code changes.
--
--  GAP-3  RESOLVED-FALLBACK (2026-06-12, Ng): frame.system.get_heap_usage()
--         absent; frame.system namespace does not exist in current Halo stdlib.
--         Using manual proxy: sprite rows + BLE MTU bytes vs 40KB budget.
--         See heap_fraction() below.
--         TODO(firmware-swap): replace heap_fraction() body with:
--           local u, t = frame.system.get_heap_usage(); return u / t
--
--  GAP-4  frame.sleep() vs frame.time.sleep(): ARD references frame.time.sleep;
--         Frame SDK examples use frame.sleep().  Both forms tried at startup;
--         the working one is stored in _sleep().

-- Runtime requirement: Lua 5.3+ (uses native bitwise operators for BLE seq
-- decode and visual color math).  Confirm against live Halo firmware during
-- hardware validation (ARD §10).

-- ─── Sleep compatibility shim (GAP-4) ────────────────────────────────────────
local _sleep
if frame and frame.sleep then
  _sleep = frame.sleep
elseif frame and frame.time and frame.time.sleep then
  _sleep = frame.time.sleep
else
  -- Last-resort: busy-wait (should not happen on real device)
  _sleep = function(s)
    local t0 = os.clock()
    while (os.clock() - t0) < s do end
  end
end

-- ─── Configuration ────────────────────────────────────────────────────────────
local RENDER_HZ    = 20         -- target render rate (ARD §5.5: 15–30fps)
local RENDER_DT    = 1.0 / RENDER_HZ
local TIMEOUT_S    = 10.0       -- no update for 10s → neutral (ARD §5.1)
local ACK_INTERVAL = 10         -- send FAMILIAR_ACK every N accepted packets

-- ─── Week 3: IMU-peak ATTENTION trigger ──────────────────────────────────────
-- Da5id / hardware-validation tunables — adjust once visual spec and real-device
-- calibration are complete.
local IMU_PEAK_THRESH_G    = 1.8   -- acceleration magnitude (g) that fires ATTENTION
local ATTENTION_DURATION_S = 0.5   -- overlay duration in seconds (ARD §5.1: 500ms)
local IMU_SCALE            = 1000  -- Halo raw-unit → g divisor (matches imu.lua relay)

-- ─── Week 3: ATTENTION jump animation (Da5id spec, decisions.md §3) ──────────
-- Total jump window: LAUNCH_MS + SETTLE_MS = 180ms.  Overlay holds until 500ms.
-- Timer source of truth: state.attn_timer (countdown from ATTENTION_DURATION_S).
-- Elapsed derived as (ATTENTION_DURATION_S - attn_timer) — no separate start_t needed.
local ATTENTION_JUMP_AMP_PX  = 4    -- upward burst amplitude (pixels)
local ATTENTION_LAUNCH_MS    = 60   -- launch phase: 0 → peak (ms)
local ATTENTION_SETTLE_MS    = 120  -- settle phase: peak → 0 (ms)
local ATTENTION_DURATION_MS  = 180  -- total jump window (launch + settle)

-- ─── Week 3: ATTENTION eye dilation (Da5id addendum 2026-06-13) ───────────────
-- Morphological dilation: pixels adjacent to eye pixels render as eye color.
-- Dilated eye: 11 → 19 pixels (rows 7–10, cols 12–18, within 24×24 sprite). ✓
local ATTENTION_EYE_DILATE_PX = 1   -- neighbor radius for dilation

-- ─── Week 2 Visual Enhancements (ARD §5.5) ────────────────────────────────────
-- CALM halo glow: 3 concentric rings (radii in pixels from sprite center)
local HALO_RADII = { 14, 17, 20 }       -- inner → outer
local HALO_BRIGHTNESS = { 0.6, 0.35, 0.15 }  -- decreasing brightness

-- STRESSED edge fraying: noise amplitude and sampling rate
local FRAY_AMP_PX = 2                   -- max displacement from edge
local FRAY_SEGMENTS = 16                -- sample points around perimeter

-- ─── Sprite position (Da5id spec, sprites/README.md) ─────────────────────────
-- 7 o'clock on rim, 80% radius.  Sprite center = (40, 179); 24×24 top-left = (28, 167).
local SPRITE_CX = 40
local SPRITE_CY = 179
local SPRITE_W  = 24
local SPRITE_H  = 24

-- ─── Da5id sprite data (sprites/familiar_neutral.txt, index grid) ─────────────
-- Each string is one row of 24 palette-index characters.
-- Index 0 = transparent (black, OLED off)
-- Index 1 = body dark  (0x1A2D3D)
-- Index 2 = body mid   (0x2E4756)
-- Index 3 = eye white  (0xE0F4FF)
-- Index 4 = shadow     (0x0D1820)
local SPRITE_ROWS = {
  "000000000000000000000000",
  "000000000000000000000000",
  "000000000000000000000000",
  "000000000111100000000000",
  "000000011111111000000000",
  "000000112222221100000000",
  "000001222222222210000000",
  "000012222222333221000000",
  "000122222233333221000000",
  "000122222223332221000000",
  "001222222222222221000000",
  "001222222222222222100000",
  "012222222222222222100000",
  "012222222222222222100000",
  "012222222222222221000000",
  "012222222222222210000000",
  "001222222222221100000000",
  "001222222222210000000000",
  "000112222221100000000000",
  "000001111110000000000000",
  "000000000000000000000000",
  "000000000000000000000000",
  "000000000000000000000000",
  "000000000000000000000000",
}

-- SDK gap #2: When frame.display.bitmap() format is confirmed, set this to
-- true and provide SPRITE_BITMAP as a nibble-packed byte string (288 bytes).
-- Rendering will automatically switch to the faster bitmap() path.
local SPRITE_BITMAP_READY = false
local SPRITE_BITMAP = nil   -- Da5id: populate once format confirmed

-- ─── Colour palettes (ARD §5.5) ───────────────────────────────────────────────
-- SDK gap: colour integer format not confirmed — assuming 0xRRGGBB 24-bit.
-- If frame.display uses palette indices, replace integer values with index refs.
local PALETTE = {
  [0] = { -- NEUTRAL: cool blue-gray (Week 1 active palette)
    [1] = 0x1A2D3D,   -- body dark
    [2] = 0x2E4756,   -- body mid
    [3] = 0xE0F4FF,   -- eye white (cyan-white, 12:1 contrast vs body)
    [4] = 0x0D1820,   -- shadow
  },
  [1] = { -- CALM: cool teal (Week 2)
    [1] = 0x0D3333,
    [2] = 0x1A4F4F,
    [3] = 0x00FFCC,
    [4] = 0x061A1A,
  },
  [2] = { -- STRESSED: warm amber/orange (Week 2)
    [1] = 0x3D1A0D,
    [2] = 0x563020,
    [3] = 0xFF8800,
    [4] = 0x1A0A05,
  },
  [3] = { -- ATTENTION: body desaturated to neutral gray (distinguishes from STRESSED amber);
          --           eye bright white (Da5id spec, decisions.md §3+§5)
    [1] = 0x1A1A1A,   -- body dark  — gray (desaturated)
    [2] = 0x2E2E2E,   -- body mid   — gray (desaturated)
    [3] = 0xFFFFFF,   -- eye        — white
    [4] = 0x0D0D0D,   -- shadow     — near-black
  },
}

-- ─── Bob animation parameters per mood (ARD §5.5) ─────────────────────────────
local BOB_HZ = {
  [0] = 0.25,   -- neutral:   4s cycle
  [1] = 0.15,   -- calm:      6.7s cycle (Week 2)
  [2] = 0.75,   -- stressed:  1.3s cycle (Week 2)
  [3] = 1.0,    -- attention: fast (Week 3)
}
local BOB_AMP_PX = 2   -- ±2px vertical (Da5id spec)

-- ─── State ────────────────────────────────────────────────────────────────────
local state = {
  mood          = 0,        -- active mood enum (0=neutral)
  intensity     = 50,       -- 0–100
  confidence    = 0,
  last_seq      = 0xFFFF,   -- reconnect rule: first seq=0 → delta=1 → accept
  accepted      = 0,        -- total accepted FAMILIAR_UPDATE count
  last_rx_t     = 0,        -- time of last accepted packet (for timeout)
  bob_phase     = 0.0,      -- radians; advances each frame
  render_int    = 50.0,     -- smoothed intensity for rendering (lerp target)
  fray_seed     = 0,        -- Week 2: pseudo-random seed for stressed edge fraying
  attn_timer    = 0.0,      -- >0 while ATTENTION overlay is active (seconds remaining)
  pre_attn_mood = 0,        -- mood to restore after ATTENTION overlay expires
}

-- ─── Heap proxy (GAP-3 fallback, ARD §5.1: 80% reduce, 95% halt) ─────────────
-- frame.system.get_heap_usage() is absent from current Halo stdlib.
-- TODO(firmware-swap): when frame.system.get_heap_usage() is available, replace
-- the body of heap_fraction() with:
--   local u, t = frame.system.get_heap_usage(); return u / t
local _HEAP_BUDGET = 40 * 1024   -- conservative per-app budget (bytes)
local _BLE_MTU_MAX = 244         -- worst-case BLE receive buffer (bytes)

local function heap_fraction()
  -- WARNING: This proxy is STRUCTURALLY STATIC (~2% of budget) because
  -- sprite_bytes and _BLE_MTU_MAX are compile-time constants.
  -- The 80% (reduce) and 95% (halt) guards in the render loop can NEVER fire
  -- with this implementation.  These thresholds are INACTIVE until GAP-3 is
  -- resolved (frame.system.get_heap_usage() confirmed in firmware).
  -- TODO(firmware-swap): replace this body with:
  --   local u, t = frame.system.get_heap_usage(); return u / t
  -- (cross-references: GAP-3 note in SDK gap block above, TODO(firmware-swap))
  local sprite_bytes = #SPRITE_ROWS * 25
  return (sprite_bytes + _BLE_MTU_MAX) / _HEAP_BUDGET
end

-- Flag set by the 95% heap guard inside the render loop.
-- Checked at the top of the loop to break cleanly after pcall exits.
local _halt = false

-- ─── BLE wire-format decode (ARD §5.2) ────────────────────────────────────────
local function decode_update(data)
  if #data ~= 6 then return nil end
  local op = data:byte(1)
  if op ~= 0x80 then return nil end
  local mood       = data:byte(2)
  local intensity  = data:byte(3)
  local confidence = data:byte(4)
  -- uint16 little-endian: byte 5 = low, byte 6 = high
  local seq = data:byte(5) | (data:byte(6) << 8)
  return { mood = mood, intensity = intensity, confidence = confidence, seq = seq }
end

-- Wraparound-aware dedup per ARD §5.2.
-- Returns true if received_seq is strictly newer than last_accepted_seq.
local function is_newer_seq(received, last)
  local delta = (received - last) & 0xFFFF
  if delta == 0 then return false end        -- duplicate
  if delta <= 32767 then return true end     -- newer (includes wraparound)
  return false                               -- stale / out-of-order
end

-- ─── BLE receive callback ─────────────────────────────────────────────────────
local function on_ble_data(data)
  -- pcall guard: a transient decode/send error must not freeze the callback.
  local ok, err = pcall(function()
    if not data or #data == 0 then return end
    local op = data:byte(1)
    if op ~= 0x80 then return end   -- only FAMILIAR_UPDATE handled device-side

    local msg = decode_update(data)
    if not msg then return end
    if not is_newer_seq(msg.seq, state.last_seq) then return end

    -- Accept the packet
    state.last_seq   = msg.seq
    state.last_rx_t  = frame.time.utc()
    state.accepted   = state.accepted + 1
    -- Trust boundary (M1): clamp all host-supplied fields at the acceptance point.
    -- Zero behavior change for in-range inputs; explicit guard against malformed host data.
    local mood_in       = clamp(msg.mood,       0,   3)
    local intensity_in  = clamp(msg.intensity,  0, 100)
    local confidence_in = clamp(msg.confidence, 0, 100)
    -- ATTENTION is an overlay (ARD §5.1 state machine): incoming mood updates
    -- go to pre_attn_mood while the overlay is active so the revert after
    -- ATTENTION_DURATION_S restores the correct underlying state.
    if state.attn_timer > 0 then
      -- ATTENTION domain invariant (I3): underlying mood must be in {0,1,2}.
      -- Treat mood==3 as trigger-only; never stash 3 as pre_attn_mood so
      -- restore-on-expiry always lands on a real underlying mood, never ATTENTION.
      state.pre_attn_mood = clamp(mood_in, 0, 2)
    else
      state.mood = mood_in
    end
    state.intensity  = intensity_in
    state.confidence = confidence_in

    -- ACK every 10 accepted packets (ARD §5.2)
    if state.accepted % ACK_INTERVAL == 0 then
      -- FAMILIAR_ACK: opcode 0x02 + last_received_seq (uint16 LE)
      local ack = string.char(0x02) .. string.pack("<I2", state.last_seq)
      frame.bluetooth.send(ack)
    end
  end)
  if not ok then
    -- Minimal visibility: print keeps the error surfaced without crashing.
    print("on_ble_data error: " .. tostring(err))
  end
end

-- ─── Render ───────────────────────────────────────────────────────────────────

-- Clamp a value to [lo, hi].
local function clamp(v, lo, hi)
  if v < lo then return lo end
  if v > hi then return hi end
  return v
end

-- ─── Easing helpers (Da5id spec, decisions.md §3) ────────────────────────────
-- ease_out_quad: fast start, decelerating.  t ∈ [0,1] → [0,1].
local function ease_out_quad(t)
  return 1 - (1 - t) * (1 - t)
end

-- ease_in_out_quad: smooth acceleration then deceleration.  t ∈ [0,1] → [0,1].
local function ease_in_out_quad(t)
  if t < 0.5 then
    return 2 * t * t
  else
    return 1 - ((-2 * t + 2) ^ 2) / 2
  end
end

-- Compute ATTENTION jump offset (pixels upward, 0–ATTENTION_JUMP_AMP_PX).
-- Uses state.attn_timer countdown as the single timer source of truth;
-- elapsed_ms derived as (ATTENTION_DURATION_S - attn_timer) * 1000 —
-- no separate attention_start_t needed (reconciles Da5id checklist, decisions.md §3).
local function compute_attention_jump(attn_timer)
  if attn_timer <= 0 then return 0 end
  local elapsed_ms = (ATTENTION_DURATION_S - attn_timer) * 1000
  if elapsed_ms >= ATTENTION_DURATION_MS then return 0 end  -- animation done; overlay holds
  if elapsed_ms < ATTENTION_LAUNCH_MS then
    -- Launch: ease-out-quad up to peak
    local t = elapsed_ms / ATTENTION_LAUNCH_MS
    return math.floor(ATTENTION_JUMP_AMP_PX * ease_out_quad(t) + 0.5)
  else
    -- Settle: ease-in-out-quad back to baseline
    local t = (elapsed_ms - ATTENTION_LAUNCH_MS) / ATTENTION_SETTLE_MS
    return math.floor(ATTENTION_JUMP_AMP_PX * (1 - ease_in_out_quad(t)) + 0.5)
  end
end

-- ─── Week 2: CALM Halo Glow (ARD §5.5) ────────────────────────────────────────
-- Draws 3 concentric rings around the sprite with decreasing brightness.
-- frame.display.circle() confirmed available (halo_emulator display API, 2026-06-12).
-- Each ring: ~2πr pixels; 3 rings totaling ~230 lit pixels at r=14,17,20.
-- Lit-pixel budget impact: ~3.8% canvas (230 / 6144) — well under 30% cap.
local function draw_halo_glow(cx, cy, mood_idx, intensity_norm)
  if mood_idx ~= 1 then return end  -- only for CALM state
  
  local pal = PALETTE[1]
  local base_color = pal[2]  -- body mid teal as halo base
  
  -- Intensity modulates halo opacity (0.0–1.0 → 0%–100% of brightness)
  local int_scale = clamp(intensity_norm, 0.0, 1.0)
  
  for ring = 1, #HALO_RADII do
    local r = HALO_RADII[ring]
    local brightness = HALO_BRIGHTNESS[ring] * int_scale
    if brightness >= 0.05 then  -- skip invisible rings
      -- Dim the base color by brightness factor (0xRRGGBB decomposition)
      local rr = math.floor(((base_color >> 16) & 0xFF) * brightness)
      local gg = math.floor(((base_color >> 8) & 0xFF) * brightness)
      local bb = math.floor((base_color & 0xFF) * brightness)
      local ring_color = (rr << 16) | (gg << 8) | bb
      frame.display.circle(cx, cy, r, ring_color, false)
    end
  end
end

-- ─── Week 2: STRESSED Edge Fraying (ARD §5.5) ─────────────────────────────────
-- Adds border noise via scattered pixels around sprite perimeter.
-- Anti-robotic jitter: uses frame-varying seed (5–10% visual variance).
-- Lit-pixel budget impact: ~16 pixels max (FRAY_SEGMENTS) = 0.3% canvas.
local function draw_edge_fraying(cx, cy, mood_idx, intensity_norm, fray_seed)
  if mood_idx ~= 2 then return end  -- only for STRESSED state
  
  local pal = PALETTE[2]
  local fray_color = pal[3]  -- bright amber for frayed edges
  
  -- Intensity modulates fray amplitude (more stress = more fraying)
  local int_scale = clamp(intensity_norm, 0.0, 1.0)
  local amp = math.floor(FRAY_AMP_PX * int_scale + 0.5)
  if amp < 1 then return end  -- no visible fraying at low intensity
  
  -- Sprite approximate radius (from center to edge of 24×24)
  local sprite_r = 11
  
  -- Scatter pixels around the perimeter with pseudo-random displacement
  local seed = fray_seed
  for i = 0, FRAY_SEGMENTS - 1 do
    local angle = (i / FRAY_SEGMENTS) * 2 * math.pi
    
    -- Simple LCG for deterministic per-frame jitter (period = 2^16)
    seed = (seed * 1103515245 + 12345) & 0xFFFF
    local noise = ((seed % (2 * amp + 1)) - amp)  -- range: [-amp, +amp]
    
    local r_disp = sprite_r + noise
    local px = cx + math.floor(r_disp * math.cos(angle) + 0.5)
    local py = cy + math.floor(r_disp * math.sin(angle) + 0.5)
    
    frame.display.set_pixel(px, py, fray_color)
  end
  
  return seed  -- return updated seed for next frame continuity
end

-- Draw the 24×24 creature sprite centered at (cx, cy + bob_y).
-- Uses set_pixel() per non-transparent pixel (correct for any firmware).
-- SDK gap #2: replace the inner loop with frame.display.bitmap() once
-- the nibble-packed format is confirmed — no other changes needed.
local function draw_creature(cx, cy, mood_idx)
  local pal = PALETTE[mood_idx] or PALETTE[0]
  local ox  = cx - 12   -- top-left x of 24×24 sprite
  local oy  = cy - 12   -- top-left y

  if SPRITE_BITMAP_READY and SPRITE_BITMAP then
    -- Fast path: single bitmap() call (SDK gap #2 — confirm format first).
    -- `drawn` gates the early return: the bitmap() call must have actually
    -- executed (not just the pcall succeeded) before we skip the pixel loop.
    local drawn = false
    local ok = pcall(function()
      -- frame.display.bitmap(ox, oy, SPRITE_W, SPRITE_BITMAP)
      -- drawn = true   -- uncomment together with the line above (Week 2)
    end)
    if ok and drawn then return end
    -- Until both lines above are uncommented, drawn stays false → always
    -- falls through to the pixel loop.  On a future failed bitmap() call,
    -- ok=false → also falls through.  Never blanks.
  end

  -- Pixel loop (always correct; slower than bitmap()).
  for row = 1, SPRITE_H do
    local row_str = SPRITE_ROWS[row]
    for col = 1, SPRITE_W do
      local idx = row_str:byte(col) - 48  -- byte() avoids sub() alloc; 48 = ASCII '0'
      if idx > 0 then
        local color = pal[idx]
        if color then
          frame.display.set_pixel(ox + col - 1, oy + row - 1, color)
        end
      end
    end
  end

  -- Eye dilation pass (ATTENTION only, Da5id addendum 2026-06-13).
  -- During mood=3, any pixel orthogonally or diagonally adjacent to an eye pixel
  -- (sprite index 3) also renders as eye color (morphological dilation).
  -- Dilated eye: rows 7–11, cols 12–18 — stays within sprite bounds (rows 4–20, cols 6–21). ✓
  if mood_idx == 3 and ATTENTION_EYE_DILATE_PX > 0 then
    local eye_color = pal[3]  -- 0xFFFFFF for ATTENTION
    local r = ATTENTION_EYE_DILATE_PX
    for row = 1, SPRITE_H do
      local row_str = SPRITE_ROWS[row]
      for col = 1, SPRITE_W do
        if (row_str:byte(col) - 48) == 3 then
          -- Paint all neighbors (radius r) as eye color if not already eye pixels
          for dr = -r, r do
            for dc = -r, r do
              if (dr ~= 0 or dc ~= 0) then
                local nr = row + dr
                local nc = col + dc
                if nr >= 1 and nr <= SPRITE_H and nc >= 1 and nc <= SPRITE_W then
                  if (SPRITE_ROWS[nr]:byte(nc) - 48) ~= 3 then
                    frame.display.set_pixel(ox + nc - 1, oy + nr - 1, eye_color)
                  end
                end
              end
            end
          end
        end
      end
    end
  end
end

-- ─── Startup ──────────────────────────────────────────────────────────────────
frame.display.power_save(false)   -- required on Halo (Frame→Halo gotcha, decisions.md)
frame.bluetooth.receive_callback(on_ble_data)

-- Send an unsolicited FAMILIAR_ACK on startup / reconnect (ARD §5.2).
-- Signals to the host that the device is alive and reports last_seq = 0xFFFF
-- (device reset state), prompting the host to re-send from seq 0x0000.
do
  local reconnect_ack = string.char(0x02) .. string.pack("<I2", state.last_seq)
  frame.bluetooth.send(reconnect_ack)
end

-- ─── Double-tap FAMILIAR_RESET (Week 3, Gate 1 resolved 2026-06-12) ──────────
-- API confirmed: frame.imu.tap_callback(func) fires once per hardware tap.
-- Double-tap discrimination: accumulate taps within TAP_WINDOW_S (350ms).
-- Debounce: ignore taps < TAP_DEBOUNCE_S apart — suppresses hardware bounce,
-- mirrors the 40ms debounce in RxTap (host-side brilliant_msg).
-- On double-tap: snap to NEUTRAL locally (no host round-trip — ARD §5.2,
-- decision 2026-06-08) and send FAMILIAR_RESET opcode 0x01 to host
-- (familiar_protocol.py OPCODE_FAMILIAR_RESET = 0x01).
local _tap_count    = 0
local _tap_last_t   = 0.0
local _tap_window_t = 0.0
local TAP_WINDOW_S   = 0.35   -- seconds to aggregate taps into a gesture
local TAP_DEBOUNCE_S = 0.04   -- minimum interval between counted taps (40ms)

frame.imu.tap_callback(function()
  local now = frame.time.utc()
  -- Debounce: drop taps too close together (hardware bounce)
  if (now - _tap_last_t) < TAP_DEBOUNCE_S then
    _tap_last_t = now
    return
  end
  -- Outside accumulation window: start a fresh sequence
  if (now - _tap_window_t) > TAP_WINDOW_S then
    _tap_count   = 0
    _tap_window_t = now
  end
  _tap_count  = _tap_count + 1
  _tap_last_t = now
  if _tap_count >= 2 then
    _tap_count = 0
    -- Snap to NEUTRAL immediately on-device (ARD §5.2)
    state.mood        = 0
    state.intensity   = 50
    state.bob_phase   = 0.0
    state.render_int  = 50.0
    state.attn_timer  = 0.0    -- cancel any in-flight ATTENTION overlay
    -- Reset dedup sentinel (B2): host calls seq.reset() which restarts at 0x0000.
    -- Sentinel 0xFFFF → delta=(0x0000-0xFFFF)&0xFFFF=1 → first post-reset packet
    -- accepted.  Without this reset, stale last_seq silently rejects seq=0.
    state.last_seq    = 0xFFFF
    -- Notify host (Device→Host, 1 byte, ARD §5.2)
    pcall(frame.bluetooth.send, string.char(0x01))
  end
end)

-- ─── Main render loop ─────────────────────────────────────────────────────────
local t_prev = frame.time.utc()

while true do
  local ok, err = pcall(function()
    local t_now = frame.time.utc()
    local dt     = t_now - t_prev
    t_prev       = t_now

    -- Clamp dt: prevents bob_phase teleport on wall-clock jumps (e.g. NTP).
    -- Lower bound 0 prevents a backward clock step from running bob_phase in reverse.
    dt = math.max(0, math.min(dt, 2 * RENDER_DT))

    -- Timeout: no BLE update for 10s → snap to neutral (ARD §5.1).
    -- Also reset last_seq so a restarted host (seq 0x0000) is accepted
    -- (reconnect rule: delta = 0x0000 - 0xFFFF = 1 → accept).
    if state.last_rx_t > 0 and (t_now - state.last_rx_t) > TIMEOUT_S then
      state.mood      = 0
      state.intensity = 50
      state.last_seq  = 0xFFFF   -- reconnect rule: next host seq=0 → delta=1 → accept
      state.last_rx_t = 0        -- re-arm: don't fire again until next real packet
      state.attn_timer = 0       -- cancel any in-flight ATTENTION overlay on timeout
    end

    -- ── Heap guard (GAP-3 fallback, ARD §5.1) ───────────────────────────────
    -- WARNING: heap_fraction() is STRUCTURALLY STATIC (~2%); the 0.95 and 0.80
    -- thresholds below are INACTIVE until GAP-3 is resolved.  Structure is kept
    -- intact so the firmware-swap is a one-line body change to heap_fraction().
    -- See heap_fraction() definition and TODO(firmware-swap) in the GAP-3 note.
    local hf = heap_fraction()
    if hf >= 0.95 then
      -- 95%: graceful halt — blank screen and exit render loop.
      frame.display.clear()
      frame.display.show()
      _halt = true
      return
    end
    local skip_glow = (hf >= 0.80)   -- 80%: drop halo glow to shed ~230 API calls/frame

    -- ── IMU-peak ATTENTION trigger (Week 3, ARD §5.1 state machine) ─────────
    -- Polls frame.imu.raw() each frame (20fps = 50ms max latency).
    -- Only fires when not already in ATTENTION (no re-entrancy).
    if state.attn_timer <= 0 then
      local ok_imu, imu_raw = pcall(frame.imu.raw)
      if ok_imu and imu_raw and imu_raw.accelerometer then
        local ax = imu_raw.accelerometer.x / IMU_SCALE
        local ay = imu_raw.accelerometer.y / IMU_SCALE
        local az = imu_raw.accelerometer.z / IMU_SCALE
        local mag = math.sqrt(ax * ax + ay * ay + az * az)
        if mag > IMU_PEAK_THRESH_G then
          -- ATTENTION domain invariant (I3): clamp to {0,1,2} so restore-on-expiry
          -- never lands on mood=3, even if host previously set state.mood=3 directly.
          state.pre_attn_mood = clamp(state.mood, 0, 2)
          state.mood          = 3          -- ATTENTION (ARD §5.1, mood enum [3])
          state.attn_timer    = ATTENTION_DURATION_S
        end
      end
    end

    -- ── Attention timer countdown ─────────────────────────────────────────────
    -- ATTENTION is a transient overlay — reverts to pre_attn_mood on expiry.
    -- Team decision (2026-06-13): restore-to-previous-mood (not neutral).
    -- Aaron deferred to team; team converged; no behavior change needed.
    if state.attn_timer > 0 then
      state.attn_timer = state.attn_timer - dt
      if state.attn_timer <= 0 then
        state.attn_timer = 0
        state.mood = state.pre_attn_mood
      end
    end

    -- Advance bob phase; clamp to [0, 2π) to prevent float growth.
    local hz = BOB_HZ[state.mood] or 0.25
    state.bob_phase = (state.bob_phase + 2 * math.pi * hz * dt) % (2 * math.pi)
    local bob_y = math.floor(BOB_AMP_PX * math.sin(state.bob_phase) + 0.5)

    -- Smooth intensity toward target (200ms lerp, ARD §5.1)
    local lerp_t = clamp(dt / 0.2, 0.0, 1.0)
    state.render_int = state.render_int + (state.intensity - state.render_int) * lerp_t
    
    -- Normalized intensity for visual effects (0.0–1.0)
    local intensity_norm = state.render_int / 100.0

    -- Clear frame (OLED: fill with black = zero power)
    frame.display.clear()
    
    -- Attention jump: additive upward offset (0px outside ATTENTION, 0–4px during).
    -- ADDITIVE on top of bob; only non-zero during mood=3 (ATTENTION overlay).
    local attn_jump_px = compute_attention_jump(state.attn_timer)
    local render_y = SPRITE_CY + bob_y - attn_jump_px

    -- Week 2: Draw halo glow BEHIND creature (CALM state only; skip when heap >= 80%)
    if not skip_glow then
      draw_halo_glow(SPRITE_CX, render_y, state.mood, intensity_norm)
    end

    -- Draw creature at bobbed + jumped position
    draw_creature(SPRITE_CX, render_y, state.mood)
    
    -- Week 2: Draw edge fraying ON TOP of creature (STRESSED state only)
    -- Advance fray_seed each frame for temporal jitter (5-10% anti-robotic variance)
    state.fray_seed = draw_edge_fraying(SPRITE_CX, render_y, state.mood, intensity_norm, state.fray_seed) or state.fray_seed

    -- Flush display buffer to screen
    frame.display.show()

    -- Sleep for remainder of frame budget
    local elapsed = frame.time.utc() - t_now
    local sleep_t = RENDER_DT - elapsed
    if sleep_t > 0 then
      _sleep(sleep_t)
    end
  end)
  if not ok then
    -- Brief backoff before retrying; keeps the creature alive after transient errors.
    -- Both print() and _sleep() are guarded so a failure in the handler itself
    -- cannot escape the loop.  (Dev fail-fast: replace pcall(print,...) with
    -- error(err) here if you want hard crashes during firmware development.)
    pcall(print, "render loop error: " .. tostring(err))
    if type(_sleep) == "function" then
      pcall(_sleep, RENDER_DT)
    end
  end
  if _halt then break end
end
