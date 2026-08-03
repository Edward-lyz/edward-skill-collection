---
source_path: AnalysisGuide/topics/arrow-format-description.rst
title: ## Arrow
---
## Arrow

The Arrow type exported file, ``.arrows``, uses the IPC stream format to store all tables in a
file. The tables can be read by opening the file as an arrow stream. For example one can use the
``open_stream`` function from the arrow python package. For more information on the interfaces that
can be used to read an IPC stream file, please refer to the Apache Arrow documentation
[1 , 2 ].

The name of each table is included in the schema metadata. Thus, while reading each table, the user
can extract the table title from the metadata. The table name metadata field has the key
``table_name``. The titles of all the available tables can be found in section
SQLite Schema Reference .

A sample function that reads all Arrow tables in a ``.arrows`` file is provided below in Python:


    import pyarrow as pa

    def read_tables(arrow_file):
        with pa.input_stream(arrow_file) as source:
            while source.tell() < source.size():
                try:
                    yield pa.ipc.open_stream(arrow_file).read_all()
                except:
                    continue

The Arrow directory exporter type, ``_arwdir``, will create a directory with one arrow file per
table/dataset.
