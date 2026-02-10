# UVT Scholarly

This library (and command-line utility) is meant to help with generating various
accreditation / hiring documents for the West University of Timișoara (UVT).

These documents generally require a complete list of publications, all citing
articles and various scores from the
[UEFISCDI](https://uefiscdi.gov.ro/scientometrie-baze-de-date) (Romanian agency
for research funding). The Romanian government mainly works with data from [Web of
Science](https://www.webofscience.com/), but this data is not easily obtained or
exported in a helpful format.

That is where this library comes into play! You can download the required metadata
from WoS, in whatever format they offer more readily, and we can then take it
and produce some nice documents with all the required information and in the
required format.

Since we do not have API access to the WoS database, there's still a bit of manual
work required, but we hope to keep it to a minimum.

To see the supported formats and types of documents we can generate, see the
[Documentation](docs).

# License

This library is MIT licensed (see the `LICENSES` folder).
