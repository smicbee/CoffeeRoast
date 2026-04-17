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

## Existing Tickets (do not duplicate)
- 📋 [IMPROVEMENT/high] Rework UI (open)
- 🔄 [BUG/high] Add bounds checks before writing PID history arrays (in_progress)
- 📋 [BUG/medium] Clamp fan speed command output to firmware PWM range (open)

## Active Task
**Add bounds checks before writing PID history arrays** [bug/high]

`iRoastControl Software/PIDController.cs` writes `pidvalues[Convert.ToInt32(currentTime)]` in `Set()` and `Update()` without checking whether `currentTime` is within the 1200-sample array. Long roasts or unexpected timestamps can throw `IndexOutOfRangeException` and stop control updates mid-roast. Clamp or guard the index and define what should happen after the recorded profile length is exceeded.

When finished, write your summary to `tickets/36701760-8fb3-49de-bbbe-963350389d5f/result.md`
