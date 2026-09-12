# 4Power for Home Assistant

Control your 4Power spa from Home Assistant — temperature, jets, light, rest
mode — and see its water temperature, water quality and safety sensors.

## Install

**HACS** → ⋮ → Custom repositories → `https://github.com/4power-dk/homeassistant-4power`,
type *Integration* → install → restart Home Assistant.

Then **Settings → Devices & Services → Add integration → 4Power**, and sign in
with your normal 4Power account. There is nothing to copy and paste: no client
ID, no secret, no API key.

## What you get, per spa

| Entity | |
|---|---|
| Climate | current and target temperature, heating status, **Ready / Rest** preset |
| Light | on/off |
| Switches | Jet 1, Jet 2, auto fill — whichever your spa has |
| Sensors | water temperature, pH, sanitizer level (ORP), Wi-Fi signal |
| Binary sensors | heating, circulation, water flow, water level, thermal switch, shutdowns |

Entities are created from what your spa actually reports, so you will not get a
Jet 2 switch on a spa with one jet, or a pH sensor on a spa with no analyzer.

## A subscription is required

Home Assistant control is a paid 4Power feature. A spa without an active
subscription **will not appear** — the integration logs how many spas are
visible without one. If you set it up and get no devices, that is the most
likely reason; check your subscription or contact 4Power.

## Notes

- **Polling.** State is fetched every 60 seconds for your whole account in one
  request, and the integration honours whatever minimum the cloud publishes.
  After you change something it re-checks within a few seconds, so the UI
  settles without waiting for the next poll.
- **An offline spa** shows its controls as unavailable rather than accepting a
  command that would never reach it. Temperature and water quality stay
  visible, since the last reading is still the last known truth.
- **Rest mode** is the spa's own energy-saving state, exposed as the climate
  preset. `Ready` is normal operation.

## Troubleshooting

No devices at all — almost always the subscription. Check the Home Assistant
log for a line from `fourpower` saying how many spas were seen without one.

Asked to sign in again — the integration refreshes its own token, so being
asked again means the account's access was revoked or changed. Signing in
resolves it.

Controls greyed out — the spa is offline. Sensors keep their last values.

## Licence

MIT. Not affiliated with the Home Assistant project.
