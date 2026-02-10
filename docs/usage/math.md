# Mathematics Department

The (minimal) requirements for a new position in the West University of Timișoara
can be found [here](https://cariere.uvt.ro/standarde-minimale-si-obligatorii/).
To generate a file with your information, you can follow steps described in
the [Web of Science](wos.md) section.

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

## Supported Formats

We can export to the following formats:

1. **CSV**: Generates a comma separated file that can be loaded into Excel or
   your favourite spreadsheet application. This is selected if the *outfile*
   has a `.csv` or `.txt` extension.
2. **LaTeX**: Generates a LaTeX file that you can then compile and modify to
   generate a pretty looking document. This is selected if the *outfile* has a
   `.tex` extension.

