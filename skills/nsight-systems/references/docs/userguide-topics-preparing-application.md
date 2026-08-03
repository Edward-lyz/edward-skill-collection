---
source_path: UserGuide/topics/preparing-application.rst
title: Preparing Your Application for Profiling
---
# Preparing Your Application for Profiling

Nsight Systems does not require any application changes to enable profiling;
however, by making some simple modifications and additions, you can greatly
increase the effectiveness of your profiling and the usability of the resulting
data. 

## Focused Profiling

By default, Nsight Systems collects a profile over the entire run of your
application. But, as explained below, you typically only want to profile the
region(s) of your application containing some or all of the performance-critical
code. Limiting profiling to performance-critical regions reduces the amount
of data that both you and the tools must process, and focuses attention on the
code where optimization will result in the greatest performance gains.

There are several common situations where limiting profiling to a region of the
application is helpful.

*  The application is a test harness wrapping all or part of your algorithm. The
   test harness may initial the data, run the algorithm cold, and then check
   the results for correctness. Using a test harness is a common and productive
   way to quickly iterate and test algorithm changes. When profiling, you will
   want to collect profile data for the functionality, but not for the test
   harness initialization and validation.
*  The application operates in phases, where a different set of algorithms is
   active in each phase. When the performance of each phase of the application
   can be optimized independently of the others, you want to profile each phase
   separately to focus your optimization efforts.
*  The application contains algorithms that operate over a large number of
   iterations, but the performance of the algorithm does not vary significantly
   across those iterations. In this case you can collect profile data from a
   subset of the iterations.


Nsight Systems supports two methods of code annotations to limit profile duration.

*  To limit profiling to a region of your CUDA application, CUDA provides functions
   to start and stop data collection. cudaProfilerStart() is used to start
   profiling and cudaProfilerStop() is used to stop profiling. To use these
   functions you must include cuda_profiler_api.h.
*  To limit profiling to a region of CPU activity, you can use the NVIDIA Tools
   Extension API (NVTX) to set range(s) for profiling. 
   

   


## Marking and Labeling Regions

To understand what the application’s CPU threads are doing beyond CUDA function
calls, you can use the NVIDIA Tools Extension API (NVTX) . When you add NVTX
markers and ranges to your application, the Timeline View shows when your CPU
threads are executing within those regions. The Timeline View also projects these
ranges onto the GPU timeline, allowing you to see what GPU activity was launched
within each CPU range.


Using custom names for CPU and CUDA resources can also improve understanding of
application behavior, especially for applications that have many host threads,
devices, contexts, or streams. You can use the NVIDIA Tools Extension API to
assign custom names for your CPU and GPU resources. Your custom names will then
be displayed in the Timeline View.
