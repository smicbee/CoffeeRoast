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
- 🔄 [BUG/high] Fix control loop timer interval scaling (in_progress)
- 🔍 [BUG/high] Make firmware failsafe fan behavior match the documented safety behavior (proposed)
- 🔍 [BUG/high] Add bounds checks before writing PID history arrays (proposed)
- 🔍 [BUG/medium] Clamp fan speed command output to firmware PWM range (proposed)
- 📋 [IMPROVEMENT/medium] Document how to build and run the Windows control application (open)
- 🔍 [TASK/medium] Add first-run serial calibration and safety checklist to setup docs (proposed)
- 🔍 [TASK/low] No actionable suggestion found (proposed)

## Active Task
**Fix control loop timer interval scaling** [bug/high]

`iRoastControl Software/ControlClass.cs` defines `deltaTime` as seconds (`0.5`) but `initialize()` assigns `t.Interval = deltaTime/1000`. `System.Timers.Timer.Interval` is milliseconds, so the loop is configured around `0.0005 ms` instead of the intended `500 ms`. Change the conversion to milliseconds, then verify the roast control loop updates at the intended cadence.

When finished, write your summary to `tickets/0b21f860-7d57-475a-a2b9-e5dd7d25c521/result.md`
