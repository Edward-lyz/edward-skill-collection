---
source_path: UserGuide/topics/python-profiling.rst
title: Python Profiling
---
# Python Profiling


Nsight Systems has several features that have been added in the last few years
to enhance users optimizing their python code.


Note:
   You may find that all of your python application output comes at the end of
   the run instead of as events happen.
   
   Python will change the buffering of stdout depending on whether it points to
   a tty or something else. Nsight Systems redirects the application stdout to
   a pipe to demultiplex stdout to both a file and the terminal. As a side
   effect, it makes Python change stdout buffering from line-buffered to
   page-buffered. You can use ``python -u`` option or the ``PYTHONUNBUFFERED
   environment`` variable to override this behavior.
