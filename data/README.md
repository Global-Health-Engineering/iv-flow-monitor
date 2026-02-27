---
title: "README for `./data`"
output: pdf_document
---

The data directory contains three sub-directories: `raw_data`, `metadata`, and `derived_data`.

# `data/raw_data`

This directory contains unedited raw data. Files are stored in comma-separated values (CSV) files.

# `data/derived_data`

This directory contains data that has been cleaned. It can also contains data that is underlying tables and figures in the published report. Files are stored in CSV file format.

## `data/metadata/README.md`

General metadata is stored in a `README.pdf` file that is contained in the `/metadata` folder. It is a template adapted from a [guide shared by Cornell University](https://data.research.cornell.edu/content/readme) and recommended for use by ETH Library under [Guidance and instructions for the ETH Zurich DMP template - Section 1: Data collection and documentation - 1.3 What documentation and metadata will you provide with the data? - Supporting resources](https://documentation.library.ethz.ch/display/DD/Data+Management+Plan+Instructions+for+ETH+Zurich+Researchers).

## `data/metadata/codebook.csv`

In addition to the human readable README with a description of the data, a codebook describes the variables and values, following general metadata standards (e.g. schema.org metadata standards): 

| variable name     | description                                                       |
| ----------------- | ----------------------------------------------------------------- |
| `directory`       | the directory name the file is stored in (raw_data, derived_data) |
| `file_name`       | the name of the input data file                                   |
| `variable_name`   | the name of measured variable                                     |
| `variable_type`   | the type of measured variable (categorical, numeric)              |
| `variable_values` | if categorical, all levels. if numeric, the range                 |
| `description`     | a written description of what that measured variable is           |
| `unit`            | the units the variable was measured in                            |
