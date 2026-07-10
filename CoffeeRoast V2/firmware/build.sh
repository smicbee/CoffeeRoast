#!/usr/bin/env bash
set -euo pipefail

ARDUINO_CLI="${ARDUINO_CLI:-arduino-cli}"
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SKETCH="$ROOT/ESP32S3 Zero/RoastingControl"
OUTPUT="${OUTPUT:-/tmp/coffeeroast-firmware-build}"
WEB_FIRMWARE="$ROOT/CoffeeRoast V2/firmware"
FQBN='esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,FlashMode=qio,FlashSize=4M,PartitionScheme=default'

"$ARDUINO_CLI" core update-index
"$ARDUINO_CLI" core install esp32:esp32@3.3.10
"$ARDUINO_CLI" lib install 'MAX6675 library@1.1.2'
rm -rf "$OUTPUT"
mkdir -p "$OUTPUT" "$WEB_FIRMWARE"
"$ARDUINO_CLI" compile --fqbn "$FQBN" --output-dir "$OUTPUT" "$SKETCH"
cp "$OUTPUT/RoastingControl.ino.merged.bin" "$WEB_FIRMWARE/coffeeroast-esp32s3-v1.1.0.bin"
sha256sum "$WEB_FIRMWARE/coffeeroast-esp32s3-v1.1.0.bin"
