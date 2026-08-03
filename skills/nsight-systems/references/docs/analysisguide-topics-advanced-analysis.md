---
source_path: AnalysisGuide/topics/advanced-analysis.rst
title: Advanced Report Analysis
---
# Advanced Report Analysis

Nsight Systems Advanced Report Analysis is functionality to better support complex
statistical analysis across multiple result files. Possible use cases for this
functionality include:

-  Multi-Node Analysis - When you run Nsight Systems across a cluster, it
   typically generates one result file per rank on the cluster. While you can
   load multiple result files into the GUI for visualization, this analysis
   system allows you to run statistical analysis across all of the result files.
-  Multi-Pass Analysis - Some features in Nsight Systems cannot be run together
   due to overhead or hardware considerations. For example, there are frequently
   more CPU performance counters available than your CPU has registers. Using
   this analysis, you could run multiple runs with different sets of counters
   and then analyze the results together.
-  Multi-Run Analysis - Sometimes you want to compare two runs that were not
   taken at the same time together. Perhaps you ran the tool on two different
   hardware configurations and want to see what changed. Perhaps you are doing
   regression testing or performance improvement analysis and want to check your
   status. Comparing those result files statistically can show patterns.
-  Complex/multi-phase analysis - Sometimes you may want to perform a
   complicated, or multi-phase analysis on one or more results files. The 
   helper functionality available in the Advanced Analysis system can simplify
   common steps.
-  Complex data output - Sometimes you want to be able to build complex
   visualizations from your analysis, rather than just tabular data from bare
   statistics.
   

**Analysis Steps**

Note:
    
    Prior to using advanced analysis, please make sure that you have
    installed all required dependencies. See **Installing Advanced Analysis
    System** in the **Installation Guide** for more information.

#. Generate the reports - Generate the reports as you always have, in fact, you
   can use reports that you have generated previously.
#. Set up - Choose the recipe (See Available Recipes, below), give it any
   required parameters, and run.
#. Launch Analysis - Nsight Systems will run the analysis, using your local
   system or Dask, as you have selected.
#. Output - the output is a directory containing an .nsys-analysis file, which
   can then be opened within the Nsight Systems GUI.
#. View the data - depending on your recipe, you can have any number of
   visualizations, from simple tabular information to Jupyter notebooks which
   can be opened inside the GUI.
