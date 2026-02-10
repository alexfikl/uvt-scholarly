# Usage

This library has a bunch of functionality that helps build up metadata for generating
the required documents. These are briefly described below, but you should see their
main pages for additional details.

## UEFISCDI

The [UEFISCDI](https://uefiscdi.gov.ro/scientometrie-baze-de-date) uses their own
personal lists and databases of scores and accepted journals. Therefore, to generate
the required documents, we will need to get these in a format that works better
than a opaque PDF file.

To download all publicly available information that is used by the library use
```bash
uvtscholarly download
```

This may take a while, since it downloads a bunch of files from UEFISCDI and
other sources that provide all the scores, quartiles, and impact factors used
by the Romanian government (and UVT). These are generally downloaded once and
cached on your system.

## Web of Science

For each researcher and/or candidate, we also need a bunch of information from
Web of Science. In general, we need

1. All the published articles, but only the ones that are supported by UEFISCDI
   will eventually be counted.
2. All the citations for the published articles, where again only ones mentioned
   in the UEFISCDI lists are counted.

The simple steps to obtain these files in multiple formats are detailed in the
[Web of Science](usage/wos.md) section. However, once these are obtained, you
may want to further filter any invalid (e.g. invalid ISSN) or unneeded (not in
UEFISCDI lists) entries. We have some simple commands to help you!

First, Web of Science has a limit of 500 entries per export. If you are one of
the lucky ones, you'll exceed this number and need to download multiple big files.
We can merge these back together using
```bash
uvtscholarly wos merge FILE1 FILE2 FILE3 ...
```

Even so, these files may have a bunch of ill-formatted entries. We can further
filter them using
```
uvtscholarly wos filter FILE
```

## Scopus

TODO

## Documents

We can generate different type of documents based on the Web of Science /
Scopus / other data. Currently supported are:

1. Documents for the [Mathematics Department](usage/math.md).
2. Documents for the [Computer Science Department](usage/cs.md).

As you might have guessed, these are the ones I needed, but we can always add more
if willing contributors show up!
