---
source_path: AnalysisGuide/topics/tutorial-create-a-user-defined-recipe.rst
title: ## Tutorial: Create a User-Defined Recipe
---
## Tutorial: Create a User-Defined Recipe

The Nsight Systems recipe system is designed to be extensible and we hope that
many users will use it to create their own recipes. This short tutorial will
highlight the steps needed to create a recipe that is a customized version of
one of the recipes that is included in the Nsight Systems recipe package.

Before starting, you may want to review recipe composite tables for an
overview of the pre-processed data tables available to recipes.

**Step 1: Create the recipe directory and script**

Make a new directory in the
``<install-dir>/target-linux-x64/python/packages/nsys_recipe/recipes`` folder based on
the name of your new recipe. For this example, we will call our new recipe
new_metric_util_map. We will copy the existing gpu_metric_util_map.py script
and create a new script called
new_metric_util_map.py in the new_metric_util_map directory. We will also
copy the heatmap.ipynb and metadata json files into the new_metric_util_map
directory. Type these steps in a Linux terminal window:


   > cd <install-dir>/target-linux-x64/python/packages/nsys_recipe
   > mkdir new_metric_util_map
   > cp gpu_metric_util_map/metadata.json new_metric_util_map/metadata.json
   > cp gpu_metric_util_map/heatmap.ipynb new_metric_util_map/heatmap.ipynb
   > cp gpu_metric_util_map/gpu_metric_util_map.py new_metric_util_map/new_metric_util_map.py

Replace the module name in ``metadata.json`` with new_metric_util_map
and update the display name and description to your preference. Also, rename
the class name ``GpuMetricUtilMap`` in ``new_metric_util_map.py`` to
``NewMetricUtilMap``. We will discuss the detailed functionality of the new
recipe code in the subsequent steps.

**Step 2: Modify the mapper function**

Many recipes are structured as a map-reduce algorithm. The mapper function is
called for every .nsys-rep file in the report directory. The mapper function
performs a series of calculations on the events in each Nsight Systems report
and produces an intermediate data set. The intermediate results are then
combined by the reduce function to produce the final results. The mapper
function can be called in parallel, either on multiple cores of a single node
(using the concurrent python module), or multiple ranks of a multi-node recipe
analysis (using the Dask distributed module).

When we create a new recipe, we need to create a class that derives from the
Recipe base class. For our example, that class will be called NewMetricUtilMap
(which we had renamed in step 1).

The mapper function is called mapper_func(). It will first convert the .nsys-rep
file into a data storage file (SQLite/Parquet/Arrow), if the file does
not already exist. It then reads all the necessary tables from the exported file
into Pandas Dataframes needed by the recipe. GPU Metric data is stored using a
database schema table called ``GENERIC_EVENTS``. For extra flexibility,
``GENERIC_EVENTS`` represents the data as a JSON object, which is stored as a string.
The ``NewMetricUtilMap`` class extracts fields from the JSON object and accumulates
them over the histogram bins of the heat map.

The original script retrieved three GPU metrics: SM Active, SM Issue, and Tensor
Active. In our new version of the script, we will extract a fourth metric,
Unallocated Warps in Active SMs.

#. Find this line (approximately line 44):


        metric_cols = ["SMs Active", "SM Issue", "Tensor Active"]
        
#. Add the Unallocated Warps in Active SMs metric:

   
        metric_cols = [
            "SMs Active",
            "SM Issue",
            "Tensor Active",
            "Unallocated Warps in Active SMs",
        ]

**Step 3: Modify the reduce function**

Our new mapper function will extract four GPU metrics and return them as a
Pandas DataFrame. The reduce function receives a list of DataFrames, one for
each .nsys-rep file in the analysis, and combines them into a single DataFrame
using the Pandas concat function. Since the reducer function is generic in our
case, no modifications are needed. However, if you would like to add any
additional post-processing, you can do so in this function.

**Step 4: Add a plot to the Jupyter notebook**

Our new recipe class will create a Parquet output file with all the data
produced by the reducer function, using the ``to_parquet()`` function. It will also
create a Jupyter notebook file using the ``create_notebook()`` function.

In this step, we will change the ``create_notebook()`` function to produce a plot
for our fourth metric. To do this, we need to change these two lines (located
in the second cell of ``new_metric_util_map/heatmap.ipynb``):


        metrics = [
           "SMs Active",
           "SM Issue",
           "Tensor Active",
        ]

To this:


        metrics = [
            "SMs Active",
            "SM Issue",
            "Tensor Active",
            "Unallocated Warps in Active SMs",
        ]

That completes all the modifications for our NewMetricUtilMap class.

**Step 5: Run the new recipe**

If the new recipe is located in the default recipe directory nsys_recipe/recipes,
we can directly run it using the ``nsys recipe`` command like this:


   > nsys recipe new_metric_util_map --input <directory of reports>
   
   
It is also possible to have a recipe located outside of this directory. In this
case, you need to set the environment variable ``NSYS_RECIPE_PATH`` to the directory
containing the recipe when running the ``nsys recipe`` command.

When successful, the recipe should produce a new recipe result directory called
``new_metric_util_map-1``.

If we open the Jupyter notebook in that recipe and execute the code, we should
see our new heatmap along with the three plots produced by the original version
of the recipe. Here is an example:

   :alt: Output from tutorial recipe
   :class: image
