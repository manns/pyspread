---
layout: default
section: manual
parent: ../
title: Overview
---

## What is pyspread ?

*pyspread* is a spreadsheet application that computes Python expressions in its cells. It is written in the [Python](https://www.python.org/) programming language.

At least basic knowledge of Python is required to use *pyspread* effectively. The core mission of *pyspread* is to be the most pythonic spreadsheet.

*pyspread* does not follow the traditional spreadsheet approach. Its approach is comparable to the spreadsheet [Siag](http://siag.nu/). However, Siag uses the Scheme programming language.

*pyspread* provides a three dimensional grid. Rows, columns and tables are treated similar, so that each row, column and table is identified by a number. Therefore, *pyspread* allows editing three dimensional arrays. These arrays can later addressed as [numpy](https://numpy.org/) arrays for further computation.

Cell functions in *pyspread* that are known from conventional spreadsheets such as Excel, [gnumeric](http://gnumeric.org/) or [LibreOffice.org Calc](https://www.libreoffice.org/) are not supported. Instead, Python expressions are entered into the spreadsheet cells. Each cell returns a Python object. These objects can represent anything including lists or matrices.
