---
source_path: UserGuide/topics/hotkey-trace-startstop-1.rst
title: #### Hotkey Trace Start/Stop
---
#### Hotkey Trace Start/Stop

Nsight Systems Workstation Edition can use hotkeys to control profiling. Press the hotkey to start and/or stop a trace session from within the target application’s graphic window. This is useful when tracing games and graphic applications that use fullscreen display. In these scenarios, switching to Nsight Systems' UI would unnecessarily introduce the window manager's footprint into the trace. To enable the use of Hotkey, check the Hotkey checkbox in the project settings page:

      :alt: Hotkey checkbox
      :class: image

The default hotkey is F12.

**Changing the Default Hotkey Binding** - A different hotkey binding can be configured by setting the ``HotKeyIntValue`` configuration field in the ``config.ini`` file.

Set the decimal numeric identifier of the hotkey you would like to use for triggering start/stop from the target app graphics window. The default value is 123 which corresponds to 0x7B, or the F12 key.

Virtual key identifiers are detailed in MSDN's Virtual-Key Codes .

Note that you must convert the hexadecimal values detailed in this page to their decimal counterpart before using them in the file. For example, to use the F1 key as a start/stop trace hotkey, use the following settings in the ``config.ini`` file:

::

   HotKeyIntValue=112
