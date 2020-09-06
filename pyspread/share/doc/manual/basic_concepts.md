---
layout: default
section: manual
parent: ../
title: Basic Concepts
---

# Basic concepts

## Python code as cell language

*pyspread* executes Python code in each cell. This is similar to typing into the Python shell. Normal cells are only executed when required e.g. for displaying results. **Execution order between cells is not guaranteed to be stable** and may differ for different versions of Python.

Normally, only one line of code that contains a [Python expression](https://docs.python.org/3.7/reference/expressions.html) is entered in each cell. However, a cell can contain additional lines of arbitrary Python code that preceed the final expression. The object that the cell returns when addressed is always the result of **the last line's expression**. Note that only the last line **must** be an expression. (The described behavior describes pyspread >v1.99. Previous versions supported only one expression per cell.)

In order to enter a new line in one cell, press `<Shift> + <Enter>`. Only pressing `<Enter>` accepts the entered code and switches to the next cell.

While editing cell code in the entry line (not in a cell editor), pressing `<Insert>` switches the grid to selection mode, which is indicated by an icon in the statusbar. In selection mode, you may select cells in the grid, for which a relative reference is generated in the entry line. Pressing `<Meta>` while clicking instead results in absolute reference. You can exit seelction mode by selecting the entry line, by focusing the entry line and pressing `<Insert>` again or by presing `<Escape>` while inside the grid. Note that you cannot edit cell code in cell editors while in selection mode.

### Example

Let us enter an expression into the top left cell in table 0:
```python
1 + 1
```
After pressing `<Enter>`, the cell displays
```python
2
```
as expected. List comprehensions are also valid expessions.
```python
[i ** 2 for i in xrange(100) if i % 3]
```
works.

However, statements such as
```python
import math
```
are not valid in the last line of a cell. In contrast,
```python
import math
math
```
is valid. Note that multi-line cells have been added to make some 3rd party modules such as `rpy2` accessible. Abusing the feature for module imports and complex control flows is discouraged.

## Module import

Modules should be imported via the macro editor. If the panel is hidden press `<F4>`. Enter the code in the editor and press the `Apply` button. If errors are raised, they are displayed in the message box below the editor.

While it is now possible to import modules from within a cell, there drawbacks:
 * The module is not imported until the cell is executed, which is not guaranteed in any way.
 * A spreadsheet may quickly become hard to understand when importing from cells.

## Variable assignment

Besides Python expressions, one variable assignment is accepted within the last line of a cell. The assignment consists of one variable name at the start followed by “=” and a Python expression. The variable is considered as global. Therefore, it is accessible from other cells.

For example `a = 5 + 3` assigns `8` to the global variable `a`.

`b = c = 4`, `+=`, `-=` etc. are not valid in the last line of a pyspread cell. In preceeding lines, such code is valid. However, variables assigned there stay in the local scope of the cell while the assigment in the last line gets into the global scope of pyspread.

Since evaluation order of cells is not guaranteed, assigning a variable twice may result in unpredictable behaviour of the spreadsheet.

## Displaying results in the grid

Result objects from the cells are interpreted by the cell renderer. Therefore two renderers may display the same object in different ways. Cell renderers may be changed in the `Format` menu's sub-menu  `Cell renderer`. At the moment, pyspread provides four different renderers:

1. The `Text renderer` is selected by default. It displays the string representation of the object as plain text. The exception is the object `None`, which is displayed as empty cell. This behavior allows empty cells returning `None` without the grid appearing cluttered.

2. The `Image renderer` renders a QImage object as an image. It renders a 2D array as a monochrome bitmap and a 3D array of shape `(m, n, 3)` as a color image. Furthermore, it renders a `str` object with valid svg content as an SVG image.

3. The `Markup renderer` renders the object string representation as markup text. It supports the [limited subset of static HTML 4 / CSS 2.1](https://doc.qt.io/qt-5/richtext-html-subset.html) that is provided by QT5's [QTextDocument](https://doc.qt.io/qt-5/qtextdocument.html) class.

4. The `Matplotlib chart renderer` renders a [matplotlib Figure object](https://matplotlib.org/api/_as_gen/matplotlib.figure.Figure.html#matplotlib.figure.Figure).

Note that the concept of different cell renderers has been introduced with pyspread v1.99.0.0.

## Absolute cell access

The result objects, for which string representations are displayed in the grid, can be accessed from other cells (and from macros as well) via the getitem method of the grid, where the grid object is globally accessible via the name `S`. For example
```python
S[3, 2, 1]
```
returns the result object from the cell in row 3, column 2, table 1. This type of access is
called **absolute** because the targeted cell does not change when the code is copied to another cell similar to a call "$A$1" in a common spreadsheet.

## Relative cell access

In order to access a cell relative to the current cell position, 3 variables X, Y and Z are provided that point to the row, the column and the table of the calling cell. The values stay the same for called cells. Therefore,
```python
S[X-1, Y+1, Z]
```
returns the result object of the cell that is in the same table two rows above and 1 column right of the current cell. This type of access is called relative because the targeted cell changes when the code is copied to another cell similar to a call "A1" in a common spreadsheet.

## Slicing the grid

Cell access can refer to multiple cells by slicing similar to slicing a matrix in numpy. Therefore, a slice object is used in the getitem call. For example
```python
S[:3, 0, 0]
```
returns the first three rows of column 0 in table 0 and
```python
S[1:4:2, :2, -1]
```
returns row 1 and 3 and column 0 and 1 of the last table of the grid.

The returned object is a numpy object array of the result objects. This object allows utilization of the numpy commands such as numpy.sum that address all array dimensions instead of only the outermost. For example
```python
numpy.sum(S[1:10, 2:4, 0])
```
sums up the results of all cells from 1, 2, 0 to 9, 3, 0 instead of summing each row, which Pythons sum function does.

One disadvantage of this approach is that slicing results are not sparse as the grid itself and therefore consume memory for each cell. Therefore,
```python
S[:, :, :]
```
may lock up or even crash with a memory error if the grid size is too large.

## Everything is accessible

All parts of *pyspread* are written in Python, therefore all objects can be accessed from within each cell. This is also the case for external modules.

There are five convenient “magical” objects, which are merely syntactic sugar: `S`, `X`, `Y`, `Z` and `nn`.

`S` is the grid data object. It is ultimately based on a `dict`. However, it consists of several layers on top. When indexing or slicing, it behaves similarly to a 3D numpy-array that returns result objects. When calling it (like a function) with a 3 tuple, it returns the cell code.

`X`, `Y` and `Z` represent the current cell coordinates. When copied to another cell, these coordinates change accordingly. This approach allows relative addressing by adding the relative coordinates to X, Y or Z. Therefore, no special relative addressing methods are needed.

`nn` is a function that flattens a numpy array and removes all objects that are None. This function makes special casing None for operations such as sum unnecessary. `nn` is provided in pyspread >v.0.3.0.

## Security

Since Python expressions are evaluated in *pyspread*, a *pyspread* spreadsheet is as powerful as any program. It could harm the system or even send confidential data to third persons over the Internet.

The risk is the the same that all office applications poese, which is why many provide precautions. The concept in *pyspread* is that you - the user - are trustworthy and no-one else. When starting *pyspread* the first time, a secret key is generated that is stored in the local configuration file (`~/.config/pyspread/pyspread.conf` on many Linux systems). You can manually edit the secret key in the Preferences Dialog (select `Preferences...` in the `File` menu).

If you save a file then a signature is saved with it (suffix .pys.sig). Only if the signature is valid for the stored secret key, you can re-open the file directly. Otherwise, e.g. if anyone else opens the file, it is displayed in `Safe mode`, i.e. each cell displays the cell code and no cell code is evaluated. The user can approve the file by selecting `Approve file` in the `File` menu. Afterwards, cell code is evaluated. When the user then saves the file, it is newly signed. Then it can be re-opened without safe mode.

Never approve foreign pys-files unless you have thoroughly checked each cell. Each cell may delete valuable files. Malicious cells are likely to be hidden in the middle of a million rows. If unsure, inspect the pysu / pys-file. pysu files are plain text files. pys files are bzip2-ed text files. Both are easy to read and understand. It may also be a good idea to run pyspread (and any other office application) with a special user or sandbox that has restricted privileges.

## Current Limitations

* Execution of certain operations cannot be interrupted or terminated if slow. An example is creating very large integers. A counter-example is a for loop. Such long running code may block *pyspread*. This may look like pyspread had crashed.
* Maximum recursion depth is limited. Its value is a trade off between handling complex cell dependencies and time until stopping when cyclic dependencies are present. The former may lead to Exceptions. The latter may slow down *pyspread*.
* Python2 code from pyspread <=1.1.3 is not automatically converted to Python3 code when opening the pys/pysu file.
