---
source_path: UserGuide/topics/s3-trace.rst
title: ## S3 Trace
---
## S3 Trace

Nsight Systems can capture information about Amazon S3 storage operations performed by the profiled process. When S3 tracing is enabled, upload and download activity is recorded on the timeline, along with metadata such as bucket name, object key, bytes transferred, and operation result.

In addition, Nsight Systems aggregates S3 trace events to produce per-process statistics including upload and download throughput and average transfer sizes.

S3 trace is available on Linux targets only.

The following S3 client libraries are supported:

-  **AWS CRT** — Native C/C++ applications (or higher-level SDKs) that use the AWS Common Runtime S3 client (``aws-c-s3``).
   Nsight Systems traces S3 upload and download request operations, and the individual HTTP transactions within each request.

Note:
      Requires aws-c-s3 version 0.9.3 or newer for tracing S3 operations. HTTP transaction tracing requires aws-c-s3 version 0.10.0 or newer.
      The profiled process must also dynamically link with the CRT library.

-  **AWS CPP SDK** — C++ applications that use the AWS C++ SDK (``aws-cpp-sdk``) for S3 operations can be traced.
   Nsight Systems traces both the S3 Client and the S3Crt Client.

Note:
      Tracing S3Client requires aws-cpp-sdk version 1.11.0 or newer.
      Tracing S3CrtClient also requires aws-c-s3 version 0.9.3 or newer
      (bundled in aws-cpp-sdk version 1.11.715 or newer).

      The profiled process must dynamically link with the CPP SDK library.

-  **Boto3** — Python applications that use the ``boto3`` library for S3 operations can be traced. The following operations are traced across Client, Bucket, and Object S3 resource types:

   ::

      upload_file              download_file
      upload_fileobj           download_fileobj
      put_object               get_object
      head_object              upload_part
      create_multipart_upload  abort_multipart_upload
      generate_presigned_url   generate_presigned_post

-  **S3TorchConnector** — Python applications that use the ``s3torchconnector`` library for PyTorch dataset access over S3 (e.g., ``S3IterableDataset``, ``S3MapDataset``, Checkpoint and direct reader/writer operations).

-  **Tensorflow-io** — Python applications that use the ``tensorflow-io`` library to access S3 objects via ``tf.io.gfile.GFile`` with ``s3://`` paths.

#### Usage Example

Example trace with Boto3:

   :alt: S3 trace example timeline
   :class: image

To enable S3 tracing from Nsight Systems:

**CLI** — Use the ``-t``, ``--trace`` option with the ``s3`` or ``s3-verbose`` parameter. See Command Line Options  for more information.


   nsys profile --trace=s3 <application> [application-arguments]


Two levels of detail are available:

-  ``--trace=s3`` — Collects S3 operation ranges, with core attributes, including bytes transferred, bucket name, key name, file path, and result status.

-  ``--trace=s3-verbose`` — In addition to everything collected by ``s3``, Nsight Systems will collect additional per-request metadata and breakdown of individual HTTP transactions.
   This additional data is intended for in-depth low-level analysis of transfer behavior, but may increase trace volume and processing overhead.
   This mode only affects tracing of AWS CRT, AWS CPP SDK, and Boto3 applications.

   :alt: S3 trace verbose view example
   :class: image

#### Process Statistics

When S3 trace data is collected, Nsight Systems aggregates the events from the profiled process to display the following statistics in the timeline:

-  **Download Throughput** — Aggregate download throughput over time (bytes/s).

-  **Upload Throughput** — Aggregate upload throughput over time (bytes/s).

-  **Avg Download Size** — Average file/object size of currently active download operations (bytes).

-  **Avg Upload Size** — Average file/object size of currently active upload operations (bytes).

These statistics can help identify periods of high or low S3 activity and reveal bottlenecks in data transfer patterns.

   :alt: S3 throughput and size counters example
   :class: image
