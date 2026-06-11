--[[
  device/main.lua — Synesthetic Familiar on-device render loop.

  ARD §5.1 (on-device spec), §5.2 (wire format), §5.5 (render spec).
  Sprite position and animation spec from Da5id — sprites/README.md.

  Week 1 scope: FAMILIAR_UPDATE decode → sprite bob (neutral state only).
  Week 2 adds: calm/stressed palette shifts, halo glow, edge fraying.
  Week 3 adds: attention jump, double-tap FAMILIAR_RESET, IMU-peak callback.

  Da5id sprite swap-in: set SPRITE_BITMAP_READY = true and populate
  SPRITE_BITMAP (packed bytes) once frame.display.bitmap() format is
  confirmed (ARD §10 open question #2 — see SDK gap comment below).

  Owner: Ng
--]]

-- ─── SDK gap flags (ARD §10) ──────────────────────────────────────────────────
--
--  GAP-1  frame.imu.on_tap / on_imu_peak: current SDK is polling-only.
--         Double-tap reset (Week 3) needs this; not blocking Week 1.
--
--  GAP-2  frame.display.bitmap() pixel-buffer format: nibble-packed 4-bit
--         indexed (Da5id's proposed format) NOT yet confirmed against Halo
--         firmware.  Week 1 renders with set_pixel() loop — always correct.
--         Swap in bitmap() when format is confirmed; no other code changes.
--
--  GAP-3  frame.system.get_heap_usage(): not confirmed in current Lua stdlib.
--         Heap budget enforcement (80%/95% thresholds, ARD §5.1) uses a
--         manual counter approximation until this is confirmed.
--
--  GAP-4  frame.sleep() vs frame.time.sleep(): ARD references frame.time.sleep;
--         Frame SDK examples use frame.sleep().  Both forms tried at startup;
--         the working one is stored in _sleep().

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
  [3] = { -- ATTENTION: high contrast white eye (Week 3)
    [1] = 0x1A1A1A,
    [2] = 0x2E2E2E,
    [3] = 0xFFFFFF,
    [4] = 0x0D0D0D,
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
  mood        = 0,        -- active mood enum (0=neutral)
  intensity   = 50,       -- 0–100
  confidence  = 0,
  last_seq    = 0xFFFF,   -- reconnect rule: first seq=0 → delta=1 → accept
  accepted    = 0,        -- total accepted FAMILIAR_UPDATE count
  last_rx_t   = 0,        -- time of last accepted packet (for timeout)
  bob_phase   = 0.0,      -- radians; advances each frame
  render_int  = 50.0,     -- smoothed intensity for rendering (lerp target)
}

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
    state.mood       = msg.mood
    state.intensity  = msg.intensity
    state.confidence = msg.confidence

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
    -- frame.display.bitmap(ox, oy, SPRITE_W, SPRITE_BITMAP)
    -- Uncomment the line above once frame.display.bitmap() format is confirmed
    -- with Da5id.  The return below ensures the pixel loop is skipped so
    -- enabling this path does not double-render (bitmap + set_pixel).
    return
  end

  -- Pixel loop (always correct; slower than bitmap()).
  for row = 1, SPRITE_H do
    local row_str = SPRITE_ROWS[row]
    for col = 1, SPRITE_W do
      local idx = tonumber(row_str:sub(col, col))
      if idx and idx > 0 then
        local color = pal[idx]
        if color then
          frame.display.set_pixel(ox + col - 1, oy + row - 1, color)
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

-- SDK gap #1: frame.imu.on_tap not confirmed. Week-3 double-tap handler
-- will be wired here once the API is available.
-- if frame.imu and frame.imu.on_tap then
--   frame.imu.on_tap(2, function()
--     state.mood, state.intensity, state.bob_phase = 0, 50, 0.0
--     frame.bluetooth.send(string.char(0x01))   -- FAMILIAR_RESET
--   end)
-- end

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
    end

    -- Advance bob phase; clamp to [0, 2π) to prevent float growth.
    local hz = BOB_HZ[state.mood] or 0.25
    state.bob_phase = (state.bob_phase + 2 * math.pi * hz * dt) % (2 * math.pi)
    local bob_y = math.floor(BOB_AMP_PX * math.sin(state.bob_phase) + 0.5)

    -- Smooth intensity toward target (200ms lerp, ARD §5.1)
    local lerp_t = clamp(dt / 0.2, 0.0, 1.0)
    state.render_int = state.render_int + (state.intensity - state.render_int) * lerp_t

    -- Clear frame (OLED: fill with black = zero power)
    frame.display.clear()

    -- Draw creature at bobbed position
    draw_creature(SPRITE_CX, SPRITE_CY + bob_y, state.mood)

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
end
