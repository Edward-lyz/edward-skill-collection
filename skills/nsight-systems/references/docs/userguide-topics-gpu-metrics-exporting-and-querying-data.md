---
source_path: UserGuide/topics/gpu-metrics-exporting-and-querying-data.rst
title: #### Exporting and Querying Data
---
#### Exporting and Querying Data

It is possible to access metric values for automated processing using the
Nsight Systems CLI export capabilities.

An example that extracts values of **SMs Active**:


         $ nsys export -t sqlite report.nsys-rep
         $ sqlite3 report.sqlite "SELECT timestamp, value FROM GPU_METRICS
            JOIN TARGET_INFO_GPU_METRICS USING (metricId) WHERE value != 0
            AND metricName LIKE \"SMs Active%\" LIMIT 10;"

         309277039|80
         309301295|99
         309325583|99
         309349776|99
         309373872|60
         309397872|19
         309421840|100
         309446000|100
         309470096|100
         309494161|99

Values are integer percentages (0..100).
