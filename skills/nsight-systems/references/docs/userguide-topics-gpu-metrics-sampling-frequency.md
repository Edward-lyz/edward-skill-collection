---
source_path: UserGuide/topics/gpu-metrics-sampling-frequency.rst
title: #### Sampling frequency
---
#### Sampling frequency

Sampling frequency can be selected from the range of 10 Hz - 200 kHz. The
default value is 10 kHz.

The maximum sampling frequency without buffer overflow events depends on GPU
(SM count), GPU load intensity, and overall system load. The bigger the chip and
the higher the load, the lower the maximum frequency. If you need higher
frequency, you can increase it until you get "Buffer overflow" message in the
Diagnostics Summary report page.

Each metric set has a recommended sampling frequency range in its description.
These ranges are approximate. If you observe ``Inconsistent Data`` or
``Missing Data`` ranges on timeline, please try closer to the recommended
frequency.
