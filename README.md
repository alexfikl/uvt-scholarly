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

## UVT: Math Department

TODO

## UVT: Computer Science Department

TODO

# License

This library is MIT licensed (see the `LICENSES` folder).
