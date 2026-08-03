---
source_path: AnalysisGuide/topics/using-expert-system-from-the-gui.rst
title: ## Using Expert System from the GUI
---
## Using Expert System from the GUI

The Expert System View can be found in the same drop-down as the Events View. If there is no .sqlite file with the same name as the .nsys-rep file in the same directory, it will be generated.

The Expert System View has the following components:

#. Drop-down to select the rule to be run.
#. Rule description and advice summary.
#. CLI command that will give the same result.
#. Table containing results of running the rule.
#. Settings button that allows users to specify the rule’s arguments.

   :alt: Expert systems information as shown in the GUI
   :class: image

A context menu is available to correlate the table entry with the timeline. The options are the same as the Events View:

-  Zoom to Selected on Timeline (ctrl+double-click)

The highlighting is not supported for rules that do not return an event but rather an arbitrary time range (e.g., GPU utilization rules).

The CLI and GUI share the same rule scripts and messages. There might be some formatting differences between the output table in GUI and CLI.
