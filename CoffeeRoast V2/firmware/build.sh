#!/usr/bin/env bash
set -euo pipefail
ARDUINO_CLI="${ARDUINO_CLI:-arduino-cli}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CURRENT_SKETCH="$ROOT/ESP32S3 Zero/RoastingControl"
OUTPUT="${OUTPUT:-/tmp/coffeeroast-firmware-build}"
WEB_FIRMWARE="$ROOT/CoffeeRoast V2/firmware"
FQBN='esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,FlashMode=qio,FlashSize=8M,PartitionScheme=default_8MB,PSRAM=opi'
"$ARDUINO_CLI" core update-index
"$ARDUINO_CLI" core install esp32:esp32@3.3.10
"$ARDUINO_CLI" lib install 'MAX6675 library@1.1.2'
rm -rf "$OUTPUT"
mkdir -p "$OUTPUT/current" "$WEB_FIRMWARE"
"$ARDUINO_CLI" compile --fqbn "$FQBN" --output-dir "$OUTPUT/current" "$CURRENT_SKETCH"
cp "$OUTPUT/current/RoastingControl.ino.merged.bin" "$WEB_FIRMWARE/coffeeroast-reva2-n8r8-v1.3.2.bin"
(cd "$WEB_FIRMWARE" && sha256sum -c SHA256SUMS)
