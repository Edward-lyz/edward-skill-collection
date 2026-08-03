# OpenGL

**Short:** Khronos's long-running cross-platform graphics API; a state-machine model where the application binds objects and calls draw functions on a single current context per thread, with the driver hiding command-buffer construction and submission.

**Details:**

- A context (``HGLRC`` on Windows via WGL, ``GLXContext`` on X11, ``EGLContext`` on Android / Wayland / embedded) is current on one thread at a time; all GL calls go through that current context.
- The API is a global state machine: ``glBindBuffer``, ``glBindTexture``, ``glUseProgram``, ``glBindFramebuffer``. Modern OpenGL 4.x adds Vertex Array Objects (VAOs), Uniform Buffer Objects (UBOs), and Shader Storage Buffer Objects (SSBOs) to reduce binding chatter.
- Compute shaders, indirect draws (``glDrawArraysIndirect``), tessellation, transform feedback, and bindless textures are all available on 4.x-class drivers.
- Presentation is platform-specific: ``SwapBuffers`` on Windows, ``glXSwapBuffers`` on X11, ``eglSwapBuffers`` elsewhere; profilers treat that call as the frame boundary.
- Debug groups (``glPushDebugGroup`` / ``glPopDebugGroup``) and object labels (``glObjectLabel``) give human-readable annotations that show up in tools.

**See also:**

- [Swap chain](swap-chain.md)
- [Graphics pipeline](graphics-pipeline.md)
- [Frame boundary / Present](frame-boundary-present.md)
- [Debug marker](debug-marker.md)
