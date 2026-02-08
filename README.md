# uvt-scholarly

This library (and command-line utility) is meant to help with generating various
accreditation / hiring documents for the West University of Timișoara (UVT).

These documents generally require a complete list of publications, all citing
articles and various scores from the
[UEFISCDI](https://uefiscdi.gov.ro/scientometrie-baze-de-date) (Romanian agency
for research funding). The information is usually available on [Web of
Science](https://www.webofscience.com/), but is not easily obtained or exported
in a helpful format.

That is where this library comes into play! You can download the required metadata
from WoS, in whatever format they offer more readily, and we can then take it
and produce some nice documents with all the required information and in the
required format.

Since we do not have API access to the WoS database, there's still a bit of manual
work required, but we hope to keep it to a minimum.

# Usage

First, you should download all publicly available information that is used by the
library. This can be done using
```bash
uvtscholarly download
```

This may take a while, since it downloads a bunch of files from UEFISCDI and
other sources that provide all the scores, quartiles, and impact factors used
by the Romanian government (and UVT). These are generally downloaded once and
cached on your system.

Then, we can go on to generate the needed documents. These all have some additional
requirements that will be detailed below.

## Preprocessing

In most cases, the data downloaded from Web of Science will not be perfect. We
can perform some simple preprocessing on it to bring it more in line with the
following workflows.

First, WoS allows downloading at most 500 entries per export. If you are particularly
successful, this will not be sufficient, so you will have to download multiple
files. They can be merged together using
```
uvtscholarly wos merge --outfile savedrecs.merged.txt savedrecs1.txt savedrecs2.txt
```

Second, most documents require some form of score or influence factor distributed
by UEFISCDI. The journals in those lists all have a valid ISSN (or eISSN) and
other metadata. To filter out entries from WoS that cannot be found in the
UEFISCDI database, run
```
uvtscholarly wos filter --outfile savedrecs.filtered.txt savedrecs.txt
```

Applying these pre-processing steps is generally recommended, as it will reduce
the number of entries in the files and allow for quicker document generation.
Note that these documents will be filtered out anyway, if they still appear.

## UVT: Math Department

The (minimal) requirements for a new position in the West University of Timișoara
can be found [here](https://cariere.uvt.ro/standarde-minimale-si-obligatorii/).
To generate a file with your information, you can follow these steps.

1. Go to Web of Science and sign in with your institutional login.

2. Go to **Advanced Search**, select **Author**, and enter your name.

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

You should now have two files with all your publications and all the citing
articles. We can take over from there! To generate the verification sheet for the
Mathematics department, just run
```bash
uvtscholarly math generate \
    --candidate "prof. dr. John Smith" \
    --position cs1 \
    --source wos \
    --pub-file path/to/your/publications.txt \
    --cite-file path/to/citing/citations.txt
    --outfile john-smith-math.tex
```

## UVT: Computer Science Department

TODO

# License

This library is MIT licensed (see the `LICENSES` folder).
