---
source_path: UserGuide/topics/report-formatters-shipped-with-nsight-systems.rst
title: #### Report Formatters Shipped With |product-name|
---
#### Report Formatters Shipped With |product-name|

The following formats are available in Nsight Systems


### Column

Usage:


      column[:nohdr][:nolimit][:nofmt][:<width>[:<width>]...]

Arguments

-  ``nohdr`` : Do not display the header.
-  ``nolimit`` : Remove 100 character limit from auto-width columns Note: This can
   result in extremely wide columns.
-  ``nofmt`` : Do not reformat numbers.
-  ``<width>...`` : Define the explicit width of one or more columns. If the value
   ``.`` is given, the column will auto-adjust. If a width of 0 is given, the
   column will not be displayed.

The column formatter presents data in vertical text columns. It is primarily
designed to be a human-readable format for displaying data on a console display.

Text data will be left-justified, while numeric data will be right-justified.
If the data overflows the available column width, it will be marked with a "…"
character, to indicate the data values were clipped. Clipping always occurs on
the right-hand side, even for numeric data.

Numbers will be reformatted to make easier to visually scan and understand. This
includes adding thousands-separators. This process requires that the string
representation of the number is converted into its native representation
(integer or floating point) and then converted back into a string representation
to print. This conversion process attempts to preserve elements of number
presentation, such as the number of decimal places, or the use of scientific
notation, but the conversion is not always perfect (the number should always be
the same, but the presentation may not be). To disable the reformatting process,
use the argument ``nofmt``.

If no explicit width is given, the columns auto-adjust their width based off the
header size and the first 100 lines of data. This auto-adjustment is limited to
a maximum width of 100 characters. To allow larger auto-width columns, pass the
initial argument nolimit. If the first 100 lines do not calculate the correct
column width, it is suggested that explicit column widths be provided.

### Table
Usage:


      table[:nohdr][:nolimit][:nofmt][:<width>[:<width>]...]

Arguments

-  ``nohdr`` : Do not display the header.
-  ``nolimit`` : Remove 100 character limit from auto-width columns Note: This can
   result in extremely wide columns.
-  ``nofmt`` : Do not reformat numbers.
-  ``<width>...`` : Define the explicit width of one or more columns. If the value
   ``.`` is given, the column will auto-adjust. If a width of 0 is given, the
   column will not be displayed.


The table formatter presents data in vertical text columns inside text boxes.
Other than the lines between columns, it is identical to the column formatter.

### CSV
Usage:


      csv[:nohdr]

Arguments

-  ``nohdr`` : Do not display the header.

The csv formatter outputs data as comma-separated values. This format is commonly
used for import into other data applications, such as spread-sheets and databases.

There are many different standards for CSV files. Most differences are in how
escapes are handled, meaning data values that contain a comma or space.

This CSV formatter will escape commas by surrounding the whole value in
double-quotes.

### TSV
Usage:


      tsv[:nohdr][:esc]

Arguments

-  ``nohdr`` : Do not display the header.
-  ``esc`` : escape tab characters, rather than removing them.

The TSV formatter outputs data as tab-separated values. This format is sometimes
used for import into other data applications, such as spreadsheets and databases.

Most TSV import/export systems disallow the tab character in data values. The
formatter will normally replace any tab characters with a single space. If the
esc argument has been provided, any tab characters will be replaced with the
literal characters "\t".

### JSON
Usage:


      json

Arguments: no arguments

The JSON formatter outputs data as an array of JSON objects. Each object
represents one line of data, and uses the column names as field labels. All
objects have the same fields. The formatter attempts to recognize numeric values,
as well as JSON keywords, and converts them. Empty values are passed as an empty
string (and not nil, or as a missing field).

At this time the formatter does not escape quotes, so if a data value includes
double-quotation marks, it will corrupt the JSON file.

### HDoc


      hdoc[:title=<title>][:css=<URL>]

Arguments:

-  ``title`` : string for HTML document title.
-  ``css`` : URL of CSS document to include.

The HDoc formatter generates a complete, verifiable (mostly), standalone HTML
document. It is designed to be opened in a web browser, or included in a larger
document via an ``<iframe>``.

### HTable
Usage:


      htable

Arguments: no arguments

The HTable formatter outputs a raw HTML ``<table>`` without any of the surrounding
HTML document. It is designed to be included into a larger HTML document.
Although most web browsers will open and display the document, it is better to
use the HDoc format for this type of use.
