# The Synesthetic Familiar

> A tiny reactive creature living in the wearer's peripheral vision on Halo's
> 256×256 round monocular display. Its form and motion mirror the wearer's
> internal state — stress, calm, attention — inferred from mic + IMU.
> No numbers, no metrics, no literal UI.

**Project codename:** PULSE  
**ARD:** `docs/projects/synesthetic-familiar/ARD.md`  
**Status:** Week 1 scaffold — "It moves"

---

## Week 1 Goal

Aaron sees the creature bobbing on Halo, driven by a mock `FAMILIAR_UPDATE`
from the Python host harness. BLE wire format works end-to-end.

Success bar: creature bobs on device, no jitter, no freeze.

---

## File Map

```
projects/synesthetic-familiar/
├── host/
│   ├── main.py              # Entry point + BLE connection harness  [Ng]
│   ├── sensors.py           # Mic capture (sounddevice) + IMU relay
│   ├── inference.py         # Local mood heuristic (no cloud)
│   ├── familiar_protocol.py # FAMILIAR_UPDATE/ACK/RESET wire encoding  [Ng]
│   └── requirements.txt     # Python deps
├── device/
│   ├── main.lua             # On-device render loop  [Ng]
│   └── sprites/             # 24×24 sprite assets (abstract-with-eyes)  [Da5id]
└── tests/
    ├── test_inference.py    # Unit tests for mood heuristic
    └── test_protocol.py     # BLE message tests  [Juanita]
```

---

## Ownership

| File | Owner | Notes |
|------|-------|-------|
| `host/main.py` | Ng | Mock-send harness + BLE loop |
| `host/sensors.py` | — | Stub ready; fill in Week 2 |
| `host/inference.py` | — | Stub ready; fill in Week 2 |
| `host/familiar_protocol.py` | Ng | Full encode/decode implementation |
| `device/main.lua` | Ng | Full render loop |
| `device/sprites/` | Da5id | 24×24 abstract-with-eyes sprite assets |
| `tests/test_inference.py` | — | Stub ready; fill in as inference lands |
| `tests/test_protocol.py` | Juanita | Full BLE message test suite |

---

## Running (Week 1)

```bash
cd projects/synesthetic-familiar/host
pip install -r requirements.txt
python main.py --device <HALO_BLE_ADDRESS>
```

---

## Architecture Summary

- **Host (Python):** captures mic + IMU → computes mood heuristic → sends
  `FAMILIAR_UPDATE` at 10Hz via BLE.
- **Device (Lua):** receives updates → interpolates state (200–500ms) →
  renders 24×24 abstract-with-eyes sprite at 15–30fps.
- **Confidence gating:** host is the single authority. If confidence < 0.7,
  no update sent (silence > hallucination).
- **Privacy:** raw audio/IMU never leave host. Wire format carries only
  `mood_enum + intensity + confidence` — no PII.  The confidence byte
  is transmitted as a 0–100 integer so the device can surface signal
  quality (e.g. dim the creature when confidence is low).  No raw
  biometric values are included.

See ARD §4–§5.5 for full architecture, wire format, and render spec.

---

## Credits

Built on [Brilliant Labs Halo SDK](https://brilliant.xyz).  
Dependencies: `brilliant-ble`, `brilliant-msg` (BSD-3-Clause), `numpy` (BSD),
`sounddevice` (MIT).
