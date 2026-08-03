---
source_path: UserGuide/topics/cli-export-command-switch-options.rst
title: #### CLI Export Command Switch Options
---
#### CLI Export Command Switch Options

After choosing the ``export`` command switch, the following options are available. Usage:

::

   nsys [global-options] export [options] [nsys-rep-file]

   :name: table_export_table
   :class: table-compact table-expandable


   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | Option                        | Available Parameters  | Switch Description                                                                                      |
   |                               | (default in bold)     |                                                                                                         |
   +===============================+=======================+=========================================================================================================+
   | ``--append``                  |                       | This option only applies to "directory of files" output formats with existing export files. If this     |
   |                               |                       | option is given, an error will not be reported and the existing output files will not be over-written.  |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--dynamic-tables``          | **none**, all,        | Controls export of dynamic NVTX binary payload tables (one relational table per NVTX payload schema).   |
   |                               | <regex>               | 'none' disables it; 'all' exports every schema; any other value is treated as a case-insensitive POSIX  |
   |                               |                       | basic regular expression matched against schema names to export a subset. This affects SQLite, Arrow,   |
   |                               |                       | and Arrow/Parquet directory exports only.                                                               |
   |                               |                       | This feature is experimental and may change in future releases.                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--force-overwrite``         | true, **false**       | If true, overwrite all existing result files with same output filename (nsys-rep, SQLITE, HDF,          |
   | or ``-f``                     |                       | JSONLINES, ARROW, ARROWDIR, PARQUETDIR).                                                                |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--help``                    | <tag>                 | Print the help message. The option can take one optional argument that will be used as a tag. If a tag  |
   |                               |                       | is provided, only options relevant to the tag will be printed.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--include-blobs``           | true, **false**       | Controls if NVTX extended payloads are exported as binary data. This  option affects SQLite, Arrow, and |
   |                               |                       | Arrow/Parquet directory exports only.                                                                   |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--include-json``            | true, **false**       | Controls if repetitive JSON blocks are included in an export or not. Some events contain dynamically    |
   |                               |                       | defined payloads. These payloads are often exported as JSON blocks to preserve their free-form          |
   |                               |                       | structure. Unfortunately, blocks of JSON text are not an efficient way to represent data, and can cause |
   |                               |                       | the export files to become quite large. To address this, some classes of events (such as GENERIC_EVENT  |
   |                               |                       | data) were extended to export payload data in the native export format. For those events that have an   |
   |                               |                       | export-native representation, this flag enables or disables the export of the equivalent JSON blocks.   |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |    This does not suppress all JSON output. Some tables, like``META_DATA_*`` tables and                  |
   |                               |                       |    ``TARGET_INFO_*`` tables may contain a smallnumber of JSON strings. This flag will not suppress      |
   |                               |                       |    those. Additionally, some classes of events (such as ETW events and NVTX events with user-defined    |
   |                               |                       |    payloads) do not have a native export representation. For events where the JSON block is the only    |
   |                               |                       |    export format,it will always be included.                                                            |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |     This flag has nothing to do with JSON Lines exports, (i.e., ``--type=jsonlines``), nor does it      |
   |                               |                       |     alter the JSON Lines export output.                                                                 |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--lazy`` or ``-l``          | **true**, false       | Controls if table creation is lazy or not. When true, a table will only be created when it contains     |
   |                               |                       | data. This option will be deprecated in the future, and all exports will be non-lazy. This affects      |
   |                               |                       | SQLite, HDF5, Arrow, and Arrow/Parquet directory exports only.                                          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--output`` or ``-o``        | <filename>            | Set the .output filename. The default is the input filename with the extension for the chosen format.   |
   |                               | **<inputfile.ext>**   |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--quiet`` or ``-q``         | true, **false**       | If true, do not display progress bar.                                                                   |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--type`` or ``-t``          | **sqlite**, hdf,      | Export format type. HDF format is supported only on x86_64 Linux and Windows.                           |
   |                               | info, arrow,          |                                                                                                         |
   |                               | jsonlines, arrowdir,  |                                                                                                         |
   |                               | parquetdir,           |                                                                                                         |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--tables``                  | <pattern>             | Value is a comma-separated list of search patterns (no spaces). This option can be given more than      |
   |                               | [,<pattern>...]       | once. If set, only tables that match one or more of the patterns will be exported. If not set, all      |
   |                               |                       | tables will be exported. This feature applies to SQLite, HDFS, Arrow, and Arrow/Parquet directory       |
   |                               |                       | exports only. The patterns are case-insensitive POSIX basic regular expressions.                        |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |     This is an advanced feature intended for expert users. This option does not enforce any type of     |
   |                               |                       |     dependency or relationship between tables and will truly export only the listed tables. If partial  |
   |                               |                       |     exports are used with analytics features such as ``nsys stats`` or ``nsys analyze``, it is the      |
   |                               |                       |     responsibility of the user to ensure all required tables are exported.                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--times``                   | <timerange>           | Value is a comma-separated list of time ranges (no spaces). This option can be given more than once. If |
   |                               | [,<timerange>...]     | set, only events that fall within at least one of the given ranges will be exported. If not set, all    |
   |                               |                       | events will be exported. This feature applies to SQLite, HDFS, Arrow, and Arrow/Parquet directory       |
   |                               |                       | exports only.                                                                                           |
   |                               |                       |                                                                                                         |
   |                               |                       | .. note::                                                                                               |
   |                               |                       |     This is an advanced feature intended for expert users. This option does not enforce any type of     |
   |                               |                       |     dependency or relationship between related events (such as CUDA launch APIs and CUDA kernel         |
   |                               |                       |     executions). If analysis scripts that rely on missing data are run over filtered exports unexpected |
   |                               |                       |     or misleading results may be generated. It is the responsibility of the user to ensure all relevant |
   |                               |                       |     and interrelated events are exported.                                                               |
   |                               |                       |                                                                                                         |
   |                               |                       | The format of a time-range is:   ``[:][<start-time>]/[<end-time>][:]``                                  |
   |                               |                       | A single time range is defined by a pair of time values, separated by a slash. At least one time value  |
   |                               |                       | is required. Any omitted time value will default to the minimum or maximum value  (approximately        |
   |                               |                       | +/- 290 years from the zero-point). The start time must be less than or equal to the end time.          |
   |                               |                       |                                                                                                         |
   |                               |                       | The time values are a series of integer or floating-point values followed by an optional unit. If no    |
   |                               |                       | unit is given, the number is assumed to be in nanoseconds. Positive and negative values are supported,  |
   |                               |                       | as well as scientific ``e`` notation. More than one value/unit can be given as long as there are no     |
   |                               |                       | spaces. The units do not need to be given in any order and can even repeat.                             |
   |                               |                       |                                                                                                         |
   |                               |                       | The following units are understood:                                                                     |
   |                               |                       |                                                                                                         |
   |                               |                       |   ``ns``, ``nsec`` : nanosecond                                                                         |
   |                               |                       |                                                                                                         |
   |                               |                       |   ``us``, ``usec`` : microsecond                                                                        |
   |                               |                       |                                                                                                         |
   |                               |                       |   ``ms``, ``msec`` : millisecond                                                                        |
   |                               |                       |                                                                                                         |
   |                               |                       |   ``s``, ``sec``   : second                                                                             |
   |                               |                       |                                                                                                         |
   |                               |                       |   ``m``, ``min``   : minute (60 seconds)                                                                |
   |                               |                       |                                                                                                         |
   |                               |                       |   ``h``, ``hour``  : hour (3600 seconds)                                                                |
   |                               |                       |                                                                                                         |
   |                               |                       | For example, the value ``1s2ms3us4ns`` would indicate 1,002,003,004 nanoseconds. ``2ns5us2`` would be   |
   |                               |                       | 5004 nanoseconds (2 nanoseconds plus 5 microseconds plus 2 nanoseconds). A floating-point value is      |
   |                               |                       | converted as a 64-bit ``double`` and is subject to the precision limitations of that format.            |
   |                               |                       |                                                                                                         |
   |                               |                       | By default, the time ranges have ``strict`` boundaries. The presence of a ``:`` character at the        |
   |                               |                       | beginning and/or end of a time range makes that  boundary ``non-strict``, meaning the filtered events   |
   |                               |                       | are allowed to cross the boundary. In essence, if both boundaries are strict, the event must fully      |
   |                               |                       | exist *within* the defined range, but if both boundaries are ``non-strict``, the event must exist       |
   |                               |                       | *during* the defined range. Given the following timeline, with a single filter range (marked START and  |
   |                               |                       | END), the given events (marked with ``=`` characters) would be considered a match (T) or not (F),       |
   |                               |                       | depending on the strictness of the filter's start/endboundaries.                                        |
   |                               |                       |                                                                                                         |
   |                               |                       | ::                                                                                                      |
   |                               |                       |                                                                                                         |
   |                               |                       |  START          END        S/E   :S/E    S/E:  :S/E:                                                    |
   |                               |                       |                                                                                                         |
   |                               |                       |  |  ===========  |          T      T      T      T                                                      |
   |                               |                       |                                                                                                         |
   |                               |                       |  ==============  |          F      T      F      T                                                      |
   |                               |                       |                                                                                                         |
   |                               |                       |  |  ==============          F      F      T      T                                                      |
   |                               |                       |                                                                                                         |
   |                               |                       |  =================          F      F      F      T                                                      |
   |                               |                       |                                                                                                         |
   |                               |                       |  ===== | or | ====          F      F      F      F                                                      |
   |                               |                       |                                                                                                         |
   |                               |                       | While many events have both a start and end time, some events only have a single timestamp. These types |
   |                               |                       | of events are treated as an event with a start time equal to the end time. If an event's end time is    |
   |                               |                       | before the start time, the end time is adjusted to the start time. If used in conjunction with the      |
   |                               |                       | ``--ts-normalize`` and/or ``--ts-shift`` options, the time filter is applied after the event's time     |
   |                               |                       | values have been adjusted.                                                                              |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ts-normalize``            | true, **false**       | If true, all timestamp values in the report will be shifted to UTC wall-clock time, as defined by the   |
   |                               |                       | UNIX epoch, using vClock correlation data <vClock plugin> when available or the system clock     |
   |                               |                       | otherwise. This option can be used in conjunction with the ``--ts-shift`` option, in which case both    |
   |                               |                       | adjustments will be applied. If this option is used to align reports from a cluster or                  |
   |                               |                       | distributed system and vClock correlation data is unavailable, alignment accuracy is limited by the     |
   |                               |                       | synchronization precision of the system clocks. For detailed analysis, the use of PTP or another        |
   |                               |                       | high-precision synchronization methodology is recommended. NTP is unlikely to produce desirable         |
   |                               |                       | results. This option only applies to SQLite, HDF5, Arrow, and Arrow/Parquet directory exports.          |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
   | ``--ts-shift``                | signed integer,       | If given, all timestamp values in the report will be shifted by the given amount. This option can be    |
   |                               | in nanoseconds        | used in conjunction with the ``--ts-normalize`` option, in which case both adjustments will be applied. |
   |                               | **0**                 | be applied. This option can be used to "hand-align" report files captured at different times, or        |
   |                               |                       | reports captured on distributed systems with poorly synchronized system clocks. This option only        |
   |                               |                       | applies to SQLite, HDF5, Arrow, and Arrow/Parquet directory exports.                                    |
   +-------------------------------+-----------------------+---------------------------------------------------------------------------------------------------------+
