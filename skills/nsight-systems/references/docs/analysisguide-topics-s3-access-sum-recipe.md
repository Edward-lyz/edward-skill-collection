---
source_path: AnalysisGuide/topics/s3_access_sum-recipe.rst
title: ## s3_access_sum Recipe
---
## s3_access_sum Recipe

This recipe analyzes S3 access patterns and I/O statistics from one or more Nsight Systems' reports,
aggregating data across processes and hosts.

**Overview**

The s3_access_sum recipe generates an interactive Jupyter notebook that analyzes S3 operations
captured during profiling sessions. It provides a statistical overview of which buckets and objects
were accessed and of access patterns.

**Key Capabilities**

The recipe provides insights into:

- **Bucket-Level Summary**: Aggregated access statistics per S3 bucket, including object counts, download/upload bytes, and operation counts.
- **Object Access Patterns**: Breakdown of download-only, upload-only, and mixed-access objects.
- **Hotspot Identification**: Top objects by download/upload volume and operation frequency.
- **Cross-Process Analysis**: S3 access patterns across multiple hosts, processes, and threads.
- **NVTX Range Correlation**: S3 activity correlated with user-defined NVTX ranges, such as access-time statistics and I/O volume.

**Use Cases**

The recipe is particularly valuable for identifying and addressing the following scenarios (but not limited to these):

1. **Hot Buckets and Objects**: Identifying which S3 buckets and objects carry the most traffic to focus optimization efforts.
2. **Small or Frequent Operations**: Detecting frequent small S3 transfers that could benefit from batching or prefetching.
3. **Application Phase Correlation**: Using NVTX ranges to understand which application phases drive the most S3 I/O.
4. **Multi-Rank Comparison**: Comparing S3 usage across MPI ranks or hosts to identify load imbalances.

**Supported S3 Client Libraries**

The recipe counts the following operations from traced S3 client libraries:

- **AWS CRT** (aws-c-s3): ``GetObject``, ``PutObject``, ``CopyObject``
- **AWS C++ SDK** (aws-cpp-sdk-s3): ``GetObject``, ``PutObject``, ``CopyObject``, ``DeleteObject``, ``HeadObject``, ``CreateMultipartUpload``, ``UploadPart``, ``CompleteMultipartUpload``, ``AbortMultipartUpload``, ``ListObjects``, ``ListObjectsV2``, ``CreateBucket``
- **Boto3**: ``get_object``, ``put_object``, ``head_object``, ``upload_part``, ``create_multipart_upload``, ``abort_multipart_upload``, ``generate_presigned_url``, ``generate_presigned_post``
- **S3TorchConnector**: ``SequentialS3Reader.read``, ``S3Writer.write``
- **Tensorflow-io**: ``read``, ``readline``, ``readlines``, ``write``, ``copy``, ``copy_v2`` via ``tf.io.gfile`` with ``s3://`` paths

For more information about S3 tracing capabilities and setup, refer to S3 Trace  in the User Guide.

**Prerequisites**

This recipe requires that Nsight Systems reports be collected with specific tracing parameters:

- ``--trace=s3`` - Enables S3 operation tracing.
    - This recipe will also work with ``--trace=s3-verbose``, but does not use any additional data from it.
- **Optional:** To enable tracing of MPI rank information, use ``--trace=mpi`` along with either ``--mpi-impl=openmpi`` or ``--mpi-impl=mpich``.
- **Optional:** To enable the NVTX range correlation table, instrument your application code with NVTX ranges. See Marking and Labeling Regions  in the User Guide.

**Usage**


   [1] Create a reports folder.
   [2] Collect nsys-rep reports, using '--trace=s3' parameter, and save them to the reports folder.
   [3] Run the recipe, using 'nsys recipe s3_access_sum --input [reports folder path]'.

**Output**

As the main output, the recipe generates an interactive Jupyter notebook
``s3_access_stats.ipynb`` with the following sections:

-   Bucket Access Summary:
           :alt: S3 Access Recipe: Bucket Access Summary. Provides a high-level overview of S3 access patterns aggregated by bucket.
           :class: image

-   Objects Access Summary:
           :alt: S3 Access Recipe: Objects Access Summary. Shows aggregated statistics broken down by access type (download-only, upload-only, both, access-only).
           :class: image

-   Hottest Downloaded Objects:
           :alt: S3 Access Recipe: Hottest Downloaded Objects. Lists the top objects by total downloaded bytes.
           :class: image

-   All Objects Table:
           :alt: S3 Access Recipe: All Objects Table. Provides a detailed breakdown of S3 access patterns for each individual object.
           :class: image

-   S3 Access Statistics for NVTX Ranges:
           :alt: S3 Access Recipe: NVTX Ranges Analysis. Shows aggregate S3 access statistics for each NVTX range across all its instances.
           :class: image
