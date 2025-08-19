---
title: "README for `root`"
output: pdf_document
---

# Overview

This is a template directory for projects at the Global Health Engineering research group at ETH Zurich. It is designed to be used for BSc and MSc projects. The folder contains a structure for generated data with guidance on how to store raw and derived data. Templates are provided for metadata and documentation.

# Computational Competencies

Within the GHE group, we have competent practitioners in using Python, STATA, and R.
Students are free to use any other programming language for data analysis (SQL, Julia, C++, etc.), but limited or no support can be provided for code review.

# Directories & Files

The repository has the following directory tree:

    .
    ├── README.md
    ├── analysis
    │   └── README.md
    ├── data
    │   ├── README.md
    │   ├── derived_data
    │   │   └── README.md
    │   ├── dictionary_template.csv
    │   ├── metadata
    │   │   ├── README.md
    │   │   └── codebook.csv
    │   └── raw_data
    │       └── README.md
    ├── docs
    │   ├── README.md
    │   ├── reports
    │   │   ├── GHE_style_guide_LaTeX.pdf
    │   │   ├── GHE_style_guide_LaTeX.zip
    │   │   ├── GHE_style_guide_Word.docx
    │   │   ├── Proposal_template.docx
    │   │   └── README.md
    │   └── slides
    │       ├── GHE_presentation_template.pptx
    │       └── README.md
    ├── grading
    │   └── README.md
    ├── hardware
    │   ├── README.md
    │   ├── design
    │   │   └── README.md
    │   └── testing
    │       └── README.md
    ├── media
    │   ├── README.md
    │   ├── photo
    │   │   └── README.md
    │   └── video
    │       └── README.md
    ├── src
    │   └── README.md
    └── tree.txt

| name         | description                                                                                                                                                                                                                        |
| ------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| README.pdf   | File to write up general information about this project.                                                                                                                                                                           |
| analysis     | Directory containing code or Excel spreadsheets for data analysis.                                                                                                                                                                 |
| data         | Data directory with sub-directories (raw_data, derived_data, metadata). This directory and its all sub-directories contain README.md files with instructions and information about their content.                                  |
| docs         | Directory for documents that are generated as part of the project. Two sub-folders (report and slides) provide templates and structure for including the manuscript and the presentations prepared over the course of the project. |
| grading      | Directory containing template for grading the project and the student. Supervisors need to ensure that students are aware of this grading rubric prior to starting their work with the GHE group.                                  |
| hardware     | Directory containing hardware design, calculations and documentation as well as testing documentation as a product of the project.                                                                                                 |
| media        | Directory for storing media related to the project (divided into photo and video sub-directories).                                                                                                                                 |
| src          | Directory for software development (not analysis files)                                                                                                                                                                     |