# Web of Science

## Exporting WoS Data

If you have access to Web of Science, you will be able to download all the
required files to generate the documents with this library. We will need two
datasets for each researcher / candidate

1. A list of all their publications.
2. A list of all the articles citing the publications.

You can download these by following these steps:

1. Go to Web of Science and sign in with your institutional login.

2. Go to **Advanced Search**, select **Author**, and enter your name. Preferably
   enter something like `LastName I*` with your initial and a little asterisk at
   the end so that it catches various forms of your first name.

3. On top of the search results, there should be an *Export* button. Click it
   and select *Tab delimited file* (or some other supported format).

4. Select all the records you want to export (maximum 500). For the **Record Content**,
   select **Full Record and Cited References**. Click export and save the file
   somewhere convenient.

5. Click on the **Citation Report** button at the top. On the new page, find the
   **Citing Articles** section rectangle at the top and click the **Total** number
   there (not the **Analyze** text next to it!).

6. On the new search results page, perform steps 3+4 again to download all the
   citations.

## Preprocessing

In most cases, the data downloaded from Web of Science will not be perfect. We
can perform some simple preprocessing on it to bring it more in line with the
following workflows.

First, WoS allows downloading at most 500 entries per export. If you are particularly
successful, this will not be sufficient, so you will have to download multiple
files. They can be merged together using
```bash
uvtscholarly wos merge \
    --outfile savedrecs.merged.txt \
    savedrecs1.txt savedrecs2.txt
```

Second, most documents require some form of score or influence factor distributed
by UEFISCDI. The journals in those lists all have a valid ISSN (or eISSN) and
other metadata. To filter out entries from WoS that cannot be found in the
UEFISCDI database, run
```bash
uvtscholarly wos filter \
    --outfile savedrecs.filtered.txt \
    savedrecs.txt
```

Applying these pre-processing steps is generally recommended, as it will reduce
the number of entries in the files and allow for quicker document generation.
Note that these documents will be filtered out anyway, if they still appear.

## Supported Formats

If you followed the steps from the previous section, you might have noticed that
Web of Science supports many different formats. This is intended to be a growing
list, but current the following formats are actually supported by the library:

1. **Tab delimited file**: this is a standard CSV file that you can open in Excel.
2. **BibTeX**: this is a non-standard BibTeX file with many WoS-specific fields.
