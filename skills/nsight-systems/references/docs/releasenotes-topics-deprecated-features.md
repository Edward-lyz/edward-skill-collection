---
source_path: ReleaseNotes/topics/deprecated-features.rst
title: Deprecated Features
---
# Deprecated Features

-  Nsight Systems versions, starting with 2026.4 do not provide support for the
   legacy ``json`` and ``text`` export options. Use ``jsonlines`` instead. If you need to
   use the old exports, we recommend you use an older version, downloadable from
   `<https://developer.nvidia.com/gameworksdownload>`__.

-  Nsight Systems versions, starting with 2026.2 have changed the available
   options for ``nic-metrics`` on the command line from ``true`` and ``false``
   to ``lf``, ``hf`` and ``none``. Currently the old options continue to work
   with the old behavior, but they will be removed in a future version of the
   product.

-  Nsight Systems versions, starting with 2026.1 do not provide support for the
   legacy ``--nvprof`` CLI option. If you need to convert a script that uses this
   option, see an archived version of the documentation for the Nsight Systems CLI
   equivalent options.

-  Nsight Systems versions, starting with 2025.4 do not provide support for Pascal
   or Volta architectures, we recommend you use an older version, downloadable from
   `<https://developer.nvidia.com/gameworksdownload>`__.

-  Nsight Systems versions, starting with 2024.2 do not provide support for Power
   PC, we recommend you use an older version, downloadable from
   `<https://developer.nvidia.com/gameworksdownload>`__.

-  Nsight Systems versions, starting with 2024.4 do not provide support for
   cuBLAS versions prior to 11.4. If you cannot update your cuBLAS, we recommend
   you use an older version, downloadable from
   `<https://developer.nvidia.com/gameworksdownload>`__.
