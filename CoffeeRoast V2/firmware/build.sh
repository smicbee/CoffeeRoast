#!/usr/bin/env bash
set -euo pipefail

ARDUINO_CLI="${ARDUINO_CLI:-arduino-cli}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CURRENT_SKETCH="$ROOT/ESP32S3 Zero/RoastingControl"
OUTPUT="${OUTPUT:-/tmp/coffeeroast-firmware-build}"
LEGACY_ROOT="${LEGACY_ROOT:-/tmp/coffeeroast-firmware-legacy}"
WEB_FIRMWARE="$ROOT/CoffeeRoast V2/firmware"
FQBN='esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,FlashMode=dio,FlashSize=8M,PartitionScheme=default_8MB,PSRAM=opi'

"$ARDUINO_CLI" core update-index
"$ARDUINO_CLI" core install esp32:esp32@3.3.10
"$ARDUINO_CLI" lib install 'MAX6675 library@1.1.2'
rm -rf "$OUTPUT" "$LEGACY_ROOT"
mkdir -p "$OUTPUT/current" "$OUTPUT/legacy" "$LEGACY_ROOT/RoastingControl" "$WEB_FIRMWARE"
git -C "$ROOT" show '2a05fb0:ESP32S3 Zero/RoastingControl/RoastingControl.ino' > "$LEGACY_ROOT/RoastingControl/RoastingControl.ino"
"$ARDUINO_CLI" compile --fqbn "$FQBN" --output-dir "$OUTPUT/current" "$CURRENT_SKETCH"
"$ARDUINO_CLI" compile --fqbn "$FQBN" --output-dir "$OUTPUT/legacy" "$LEGACY_ROOT/RoastingControl"
cp "$OUTPUT/current/RoastingControl.ino.merged.bin" "$WEB_FIRMWARE/coffeeroast-n8r8-v1.2.0.bin"
cp "$OUTPUT/legacy/RoastingControl.ino.merged.bin" "$WEB_FIRMWARE/coffeeroast-n8r8-legacy-2a05fb0.bin"
(cd "$WEB_FIRMWARE" && sha256sum -c SHA256SUMS)
