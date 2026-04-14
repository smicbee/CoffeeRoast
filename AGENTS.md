# Project: CoffeeRoast

## Description
CoffeeRoast is a DIY coffee roaster project that converts a popcorn machine into a temperature-controlled roaster using an ESP32, thermocouple, solid-state relay, fan control, and a Windows iRoastControl application. It includes firmware, hardware documentation, KiCAD resources, and roast recipe/profile files for reproducible roasting curves.

## Current Idea
CoffeeRoast helps home roasters and hardware tinkerers turn an inexpensive popcorn machine into a controllable coffee roaster with repeatable roast curves. The project combines ESP32 firmware for temperature, relay, fan, and failsafe control with a Windows control app and shared roast profiles. The next meaningful direction is to tighten the end-to-end roasting workflow by improving setup documentation, validating safety behavior, and making the control software easier to run and calibrate for new builds.

## Guidelines
- Commit all changes with descriptive messages
- Do not modify files outside this directory
- When completing a ticket, create `tickets/<ticket-id>/result.md` with a summary
- Follow existing code patterns in the repository
- Run tests if a test suite exists before submitting
- Keep changes focused on the assigned ticket

