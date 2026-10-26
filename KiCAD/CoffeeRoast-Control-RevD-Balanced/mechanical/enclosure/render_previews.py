#!/usr/bin/env python3
"""Render verified PNG previews from the generated enclosure STLs using VTK."""

from pathlib import Path

import vtk


ROOT = Path(__file__).resolve().parent
GEN = ROOT / "generated"


def actor_from_stl(path: Path, color: tuple[float, float, float], opacity=1.0):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(str(path))
    reader.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(*color)
    actor.GetProperty().SetOpacity(opacity)
    actor.GetProperty().SetInterpolationToPhong()
    actor.GetProperty().SetSpecular(0.25)
    actor.GetProperty().SetSpecularPower(25)
    return actor


def render(name: str, mode: str) -> Path:
    exploded = mode == "exploded"
    usb_side = mode == "usb_side"
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.055, 0.065, 0.085)
    renderer.SetBackground2(0.17, 0.19, 0.23)
    renderer.GradientBackgroundOn()
    tray = actor_from_stl(GEN / "tray.stl", (0.54, 0.60, 0.69), 1.0)
    board = actor_from_stl(GEN / "board_proxy.stl", (0.03, 0.57, 0.20), 1.0)
    lid = actor_from_stl(GEN / "lid.stl", (0.18, 0.42, 0.78), 1.0)
    # Put the lid beside the open tray in the exploded review; transparency made
    # the enclosure surfaces ambiguous on headless OpenGL implementations.
    lid.SetPosition(125.0 if exploded else 0.0, 0.0, 25.0 if exploded else 30.0)
    if usb_side:
        lid.VisibilityOff()

    renderer.AddActor(tray)
    renderer.AddActor(board)
    renderer.AddActor(lid)

    # Ground plane provides scale/depth without changing the geometry.
    plane = vtk.vtkPlaneSource()
    plane.SetOrigin(-15, -15, -0.5)
    plane.SetPoint1(125, -15, -0.5)
    plane.SetPoint2(-15, 90, -0.5)
    plane.SetResolution(1, 1)
    plane_mapper = vtk.vtkPolyDataMapper()
    plane_mapper.SetInputConnection(plane.GetOutputPort())
    plane_actor = vtk.vtkActor()
    plane_actor.SetMapper(plane_mapper)
    plane_actor.GetProperty().SetColor(0.10, 0.11, 0.14)
    plane_actor.GetProperty().SetOpacity(0.8)
    renderer.AddActor(plane_actor)

    title = vtk.vtkTextActor()
    titles = {
        "exploded": "CoffeeRoast RevD enclosure — exploded prototype",
        "closed": "CoffeeRoast RevD enclosure — closed prototype",
        "usb_side": "CoffeeRoast RevD enclosure — USB/RF wall review",
    }
    title.SetInput(titles[mode])
    title.GetTextProperty().SetFontSize(24)
    title.GetTextProperty().SetColor(0.92, 0.94, 0.98)
    title.SetPosition(28, 1140)
    renderer.AddActor2D(title)

    note = vtk.vtkTextActor()
    note.SetInput("PROTOTYPE: USB/cable/Q1/C4 dimensions require physical fit coupons")
    note.GetTextProperty().SetFontSize(17)
    note.GetTextProperty().SetColor(1.0, 0.68, 0.25)
    note.SetPosition(28, 28)
    renderer.AddActor2D(note)

    window = vtk.vtkRenderWindow()
    window.SetOffScreenRendering(True)
    window.SetSize(1800, 1200)
    window.SetMultiSamples(8)
    window.AddRenderer(renderer)

    camera = renderer.GetActiveCamera()
    if usb_side:
        camera.SetFocalPoint(50.0, 50.0, 12.0)
        camera.SetPosition(35.0, 185.0, 75.0)
    elif exploded:
        camera.SetFocalPoint(112.0, 32.0, 15.0)
        camera.SetPosition(245.0, -175.0, 155.0)
    else:
        camera.SetFocalPoint(50.0, 32.0, 15.0)
        camera.SetPosition(155.0, -145.0, 120.0)
    camera.SetViewUp(0.0, 0.0, 1.0)
    renderer.ResetCameraClippingRange()

    window.Render()
    capture = vtk.vtkWindowToImageFilter()
    capture.SetInput(window)
    capture.SetScale(1)
    capture.SetInputBufferTypeToRGBA()
    capture.ReadFrontBufferOff()
    capture.Update()

    out = GENERATED = GEN / name
    writer = vtk.vtkPNGWriter()
    writer.SetFileName(str(out))
    writer.SetInputConnection(capture.GetOutputPort())
    writer.Write()
    return out


if __name__ == "__main__":
    for filename, mode in [
        ("preview_exploded.png", "exploded"),
        ("preview_closed.png", "closed"),
        ("preview_usb_side.png", "usb_side"),
    ]:
        path = render(filename, mode)
        print(f"wrote {path} ({path.stat().st_size} bytes)")
