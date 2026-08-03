---
source_path: AnalysisGuide/topics/json-lines-format-description.rst
title: ## JSON Lines
---
## JSON Lines

In the JSON Lines export format (JSON Lines Documentation ),
events and other report data (such as strings and processes) are serialized into JSON
objects, with each object written to a new line.

Output layout:


   {"id":0,"table":"StringIds","value":"[Unknown]"}
   {"globalPid":284057963331584,"name":"chrome","pid":153958,"table":"PROCESSES"}
   {"globalTid":281523009882942,"nameId":442,"priority":20,"table":"ThreadNames"}
   {"name":"COLLECT_GPU_CTX_SW_TRACE","table":"META_DATA_CAPTURE","value":"false"}
   ...

Note the presence of the "table" field in each JSON object. This field allows readers to identify
the type of the event and corresponds to the table name in the ``sqlite`` export.
