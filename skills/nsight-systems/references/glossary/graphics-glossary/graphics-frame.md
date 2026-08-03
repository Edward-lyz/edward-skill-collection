# Graphics frame

**Short:** One iteration of an application's render loop, delimited on the CPU by a Present (or SwapBuffers) call to the graphics API.

**Details:**

- A frame is the unit of work that produces one image for the display.
- Each iteration typically runs input sampling, simulation, render-command recording, submission to a GPU queue, and a final present.
- The present call hands the just-rendered image to the display system and conceptually closes the frame.
- A frame has both a CPU side (the work the application thread did) and a GPU side (the work the device actually executed), and the two are usually offset in time because the GPU runs behind the CPU.
- Frames are usually numbered with a monotonic frame index so that later analysis can line up CPU work, GPU work, and display events that belong together.
- A consistent frame cadence matters more for perceived smoothness than a high average frame rate.

**See also:**

- [Frame boundary / Present](frame-boundary-present.md)
- [FPS and frame time](fps-frame-time.md)
- [Reflex render latency](reflex-render-latency.md)
- [VSync](vsync.md)
