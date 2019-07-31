---
layout: default
title: First steps into pyspread
menu: docs
---

<div markdown="1" class="w3-container w3-margin-left w3-margin-right">

# About this document

This document provides a quick overview over pyspread.
Readers should have at least some experience with Python.

# What is pyspread?

Pyspread is a spreadsheet application that computes Python
expressions in its cells.
It is written in the programming language Python.

The core mission of pyspread is to be the most pythonic spreadsheet.

Pyspread does not follow the traditional spreadsheet approach.
Cell functions that are known from conventional spreadsheets
such as Excel, gnumeric or OpenOffice.org Calc are not supported.
Instead, Python expressions are entered into the spreadsheet
cells. Each cell returns a Python object. These objects can
represent anything including lists or matrices.


Pyspread's approach is comparable to the spreadsheet Siag.
However, Siag uses the programming language Scheme.

At least basic knowledge of Python is required to
effectively use pyspread.
Pyspread provides a three dimensional grid that can comprise
millions of rows, columns and tables. This is possible because
a dictionary is used for storing all grid data. Note that
tables with many filled cells may require considerable
amounts of RAM.

# Basic concepts

## Python code as cell language

Pyspread uses Python expressions in each cell.
This is similar to typing expressions into the Python shell.
The main difference is that cells are only executed
when required e.g. for displaying results. There is no
guaranteed execution order.

Python expressions are terms
that Python evaluates to a result object.
For an overview to the different types of Python expressions see
[here](http://docs.python.org/reference/expressions.html).

Pyspread expects such Python
expressions in its grid cells. Therefore
```Python
1 + 1
```
is valid as is
```Python
[i ** 2 for i in xrange(100) if i % 3]
```
.
However, statements such as
```Python
print 2
```
or
```Python
import math
```
are **not** valid in cells. However, in the macro editor,
these statements are possible. Module imports should take place there.

## Module import

Since the import statement for importing Python modules
is no expression, it cannot be used from within a cell.
Module import from within a cell can be realized by
calling the function __import__:
```Python
<code><module_name> = __import__("<module name>")
```
This cell makes the module
available from each other cell. Alternatively, a module
can be imported via the macro editor with the import statement.

There are modules, which
cannot be imported from within a cell. One example is rpy2
(rpy works well). The reason is that module initialization
is stateful, i. e. certain statements have to be called in
a specific order. Such modules can only be from the macro editor.

## Variable assignment

Besides Python expressions,
one variable assignment is accepted within a cell. The
assignment consists of one variable name at the start
followed by "=" and a Python expression. The variable is
considered as global. Therefore, it is accessible from
other cells.

For example
```Python
a = 5 + 3
```
assigns 8 to the global
variable a.

Since only one assignment is
possible,
```Python
b = c = 4
```
is **not** valid in a
pyspread cell. Note that pyspread does also not support +=, -= etc.

Evaluation order
of cells is not guaranteed. Therefore, assigning a
variable twice may result in unpredictable behavior of the
spreadsheet.

## Result strings in the grid

Cells that contain a Python
expression display the string representation of the result
object that is returned from this expression.

Exceptions to this rule are:
* The None object that displays an empty string i. e. an
  empty cell instead. All empty cells also return None so
  that an empty grid appears empty. 
* wx.Bitmap objects that are displayed as images
* matplotlib figure objects that are displayed as images
* Valid SVG figure strings are rendered in the cell (static bitmap).
* VLCPanel (Vlc video panel) objects (pyspread 1.1 or newer) launch a
* VLC video player instance inside the cell.

## Absolute cell access

The result objects, for
which string representations are displayed in the grid,
can be accessed from other cells (and from macros as well)
via the __getitem__ method of the grid, where the grid
object is globally accessible via the name S. For example
```Python
S[3, 2, 1]
```
returns the result object
from the cell in row 3, column 2, table 1. This type of
access is called absolute because the targeted cell does
not change when the code is copied to another cell similar
to a call $A$1 in a common spreadsheet.

In order to make referencing cells easier, a toggle button
can be pressed when editing a cell. When it is toggled on, a
selection is converted into its code representation at the
cursor. Note that selection a cell is not enough. It has to
be selected (blue background) so that you see the selection
representing code.

## Relative cell access

In order to access a cell
relative to the current cell position, 3 variables X, Y
and Z are provided that point to the row, the column and
the table of the calling cell. The values stay the same
for called cells. Therefore,
```Python
S[X-1, Y+1, Z]
```
returns the result object of
the cell that is in the same table two rows above and 1
column right of the current cell. This type of access is
called relative because the targeted cell changes when the
code is copied to another cell similar to a call A1 in a
common spreadsheet.

## Slicing the grid

Cell access can refer to
multiple cells by slicing similar to slicing a matrix in
numpy. Therefore, a slice object is used in the
__getitem__ call. For example
```Python
S[:3, 0, 0]
```
returns the first three rows
of column 0 in table 0 and
```Python
S[1:4:2, :2, -1]
```
returns row 1 and 3 and
column 0 and 1 of the last table of the grid.

The returned object is a
numpy object array of the result objects. This object
allows utilization of the numpy commands such as numpy.sum
that address all array dimensions instead of only the
outermost. For example
```Python
numpy.sum(S[1:10, 2:4, 0])
```
sums up the results of all
cells from 1, 2, 0 to 9, 3, 0 instead of summing each row,
which Pythons sum function does.

One disadvantage of this
approach is that slicing results are not sparse as the
grid itself and therefore consume memory for each cell.
Therefore,
```Python
S[:, :, :]
```
will lock up or even crash
pyspread with a memory error if the grid size is too
large.

## Everything is accessible

All parts of pyspread are written in Python. Therefore, all
objects can be accessed from within each cell. This is also the
case for external modules.

There are 5 convenient
"magical" objects, which are merely syntactic sugar: S, X,
Y and Z and nn.

S is the grid data object.
It is ultimately based on a dict. However, it consists of
several layers on top. When indexing or slicing, it
behaves similarly to a 3D numpy-array that returns result
objects. When calling it (like a function) with a 3 tuple,
it returns the cell code.

X, Y and Z represent the
current cell coordinates. When copied to another cell,
these coordinates change accordingly. This approach allows
relative addressing by adding the relative coordinates to
X, Y or Z. Therefore, no special relative addressing
methods are needed.

nn is a function that
flattens a numpy array and removes all objects that are
None. This function makes special casing None for
operations such as sum unnecessary. nn is provided in
pyspread &gt;v.0.3.0.

External modules are
accessible from each cell. Unfortunately, Python's
convenient import syntax
```Python
from xx import yy
```
is no expression. Therefore, the expression
```Python
xx = __import__("xx")
```
has to be used.
Alternatively, the import statement can be used from
within the macro editor. Note that this limitation does not
apply to the pyspread version 2.x+

## GPG based security

Since Python expressions are
evaluated in pyspread, a pyspread spreadsheet is as
powerful as any program. Therefore, it could harm the
system or even send confidential data to third persons
over the Internet.

Even though this is
basically the case for all office applications, the easy
access to such behavior makes precautions necessary. The
idea in pyspread is that you - the user - are trustworthy
and no-one else. If you save a file and if you have the
Python gnupg interface installed then a signature is saved
with it (suffix .pys.sig). Only you can re-open the file
directly. If anyone else opens the file, it is displayed
in safe mode, i.e. each cell displays the cell code and
no cell code is evaluated. The user can approve the file.
Afterwards, cell code is evaluated. When the user then
saves the file, it is newly signed. Then it can be
re-opened without safe mode.

Never approve foreign pys-files unless you have 
**thoroughly checked each cell**. One cell may delete you
hard drive. And it is likely to be found somewhere in the
middle of a million rows, a million tables and a million
tabs. If unsure, inspect the pys-file. It is a bzip2-ed
text file. You can read it. You can grep in it.

It may also be a good idea to run pyspread (and any other
office application) with a special user that has restricted
privileges. If you like it even safer then a sandbox may
be worth a thought.

Technically, signing is done
with GPG. When starting pyspread the first time, no GPG key
is present and saved files are not signed. In order to activate
signing, you can generate or choose an existing key via
File->Switch GPG key...

# Current limitations

*   External libraries that set states in several steps (e.g. rpy2)
    may be hard to use because in pyspread cell execution order is
    **not** guaranteed. Such libraries should be used from within
    a macro.

*   There is no selection rectangle for auto-filling cells. Some
    of this functionality is provided by repeating cell content
    when pasting into selections.

*   Execution of C code that is called from Python expressions
    cannot be interrupted or terminated if slow. C code means that
    creating very large integers cannot be interrupted while a for
    loop can. Since spreadsheet code is executed sequentially, such
    long running C code may block pyspread.

*   Cyclic dependencies of cells stop at maximum recursion depth.
    If there are many cyclic dependencies, this may slow down
    pyspread.

*   Loading and saving Excel and Open document format files is not feature
    complete. Data will be lost when saving a document
    as an xls or an ods file and loading it again.

# The pyspread workplace

## Starting and exiting pyspread

On Linux or *nix systems, type
```bash
$ pyspread
```
from the command prompt. If you want to run pyspread without
installation then cd into the pyspread directory and type
```bash
$ pyspread.sh
```

On Windows, type
```
&gt; pyspread.bat
```
in the command line or launch the file via the Windows Explorer
(click or double click)

You can exit pyspread by closing the main window or by selecting
File -&gt; Quit from the menu.

## Pyspread main window

The main window comprises the following components (see Figure):
* Title bar
* Menu
* Toolbars
* Entry line
* Insertion mode toggle button (enabled on *nix only)
* Table selector
* Table list
* Grid
* Status bar

[![Pyspread main window](images/screenshot_main_window.png){:width="600px"}](images/screenshot_main_window.png)

## Title bar

When pyspread is started or a new spreadsheet is created then the
title bar displays "pyspread". When a file is opened or saved
then the filename is presented in front of " - pyspread".


Whenever a spreadsheet is changed then  an askerisk "*" is
displayed in front of the title bar text.

## Main menu

### File menu

#### New

An empty spreadsheet can be created by File -&gt; New. 

A Dialog pops up, in which
the size of the new spreadsheet grid can be entered. Note
that even though sizes of several million rows or columns
are possible, there is a limit that is imposed by
wx.Python. Therefore, grids with more than 80 million rows
and 30 million columns may show problems and
instabilities.

[![Grid dimension dialog](images/screenshot_new_dialog.png){:width="200px"}](images/screenshot_new_dialog.png)

#### Open

Loading a spreadsheet from disk can be initiated with File
-&gt; Open. Opening a file expects a file with the
extension .pys. The file format is pyspread specific.

Starting from v0.3.0 there
is a second file format with the extension .pysu. It is
identical to pys but for the file being uncompressed. This
format can be beneficial when using pyspread in
combination with file version control systems such as git.

Excel xls and xlsx files can also be opened via File -&gt; Open if the
Python module xlrd is installed.
Cell content and cell attributes are retrieved.
However, functions and macros are neither loaded nor converted.


Starting with v1.1, Opendocument format ods files can be opened via File -&gt; Open if the
Python module odfpy is installed. In v1.1, only cell content is imported.
Neither cell formats nor functions nor macros are loaded nor converted.

Since pyspread files are
ultimately Python programs, a file is opened in
safe mode if

* it has not been previously signed by the
    current user on the current system or
* gnupg is not installed or not configured to use a key
    with an empty(!) password.

Safe mode means that
the cell content is loaded and displayed in the grid.
However, it is not executed, so that 2+2 remains 2+2 and
is not computed into 4. You can leave safe mode with File
-&gt; Approve.

#### Save

A spreadsheet can be stored to disk with File
-&gt; Save.
If a file is already opened, Save overwrites it directly.
Otherwise, Save prompts for a filename.


When a file is saved and the Python module gnupg is installed
(and configured with a key that has no password) then a
signature is created in an additional file with the suffix
.pys.sig. The signature is a PGP signature. When pyspread
is started the first time for a user, a pgp key pair is
crreated for the user pyspread_&lt;user-id&gt;. This key
pair is used for signing pyspread save files. A correct
signature file lets pyspread open a file without going
into safe mode. Note that the save file is <span
style="font-weight: bold;">not</span> encrypted in any
way.

The pys file format is a
bzip2-ed Text file with the following structure (since
version 0.2.0):

```
[Pyspread save file version]
0.1
[shape]
1000 100 3
[grid]
7 22 0 'Testcode1'
8 9 0 'Testcode2'
[attributes]
[] [] [] [] [(0, 0)]
0 'textfont' u'URW Chancery L'
[] [] [] [] [(0, 0)]
0 'pointsize' 20
[row_heights]
0 0 56.0
7 0 25.0
[col_widths]
0 0 80.0
[macros]
Macro text
```

If the Python module xlwt is installed then pyspread can save
the spreadsheet as Excel xls file.
Cell attributes such as fonts and colors are preserved.
Python expressions are exported as strings.
Macros are not saved into the xls file.

#### Save As

File -&gt; Save As saves the spreadsheet as does File -&gt; Save.
While Save overwrites files that are opened on pyspread directly,
Save As always always prompts for a file name.

#### Import

With File -&gt; Import, a
csv file can be imported. There are two import filters.

"Tab-delimited text file" is
fast but does not handle ill-formed data or special
formats well. As the name suggests, only Tab delimited
values are allowed.

The other filter "Csv file"
opens the CSV file import dialog. In this dialog, CSV
import options can be set. Furthermore, target Python
types can be specified, so that import of dates becomes
possible. The grid of the import dialog only shows the
first few rows of the csv files in order to give an
impression how import data will look like in pyspread.

Importing a file always
activates safe mode (when no signature file is created
manually) because code in the CSV file might prove
harmful.

[![CSV file import dialog](images/screenshot_csv_import.png){:width="300px"}](images/screenshot_csv_import.png)

#### Export

Pyspread can export spreadsheets to csv, pdf and svg files.
Furthermore, if a chart cell is selected then pyspread offers to
export this cell to svg, eps, ps, pdf or png files.

When exporting a csv file then a dialog is displayed,
in which the format of the csv file may be specified.
The start of the exported file is shown below the options.

[![CSV file export dialog](images/screenshot_csv_export.png){:width="500px"}](images/screenshot_csv_export.png)

When exporting a spreadsheet to a pdf or svg file then a
dailog opens, in which page orientation and size as well as
the grid section to be exported can be chosen.
If more than one table is chosen for a pdf file then a multiple
page file is exported. For svg files only the last table
will be visible.

[![PDF file export dialog](images/screenshot_pdf_export.png){:width="300px"}](images/screenshot_pdf_export.png)

#### Approve file

Pyspread cells contain
Python code. Instead of a special purpose language, you
enter code in a general purpose language. This code can do
everything that the operating system allows. Normally,
this is a lot.

Even though the situation
differs little to common spreadsheet applications, the
approach makes malicious attacks easy. Instead of knowing
how to circumvent blocks of the domain specific language
to make the computer do what you want, everything is
straight forward.

In order to make working
with pyspread as safe as possible, all save-files (pys
files and pysu files) are signed by the current user with
a gpg signature file. Only a user with a private key can
open the file without approving it. That should ensure
that when loading a pys file, only the code that a user
has written him- or herself is executed. Pys files without
a valid signatures are opened in safe mode, i. e. the code
is displayed and not executed. However, it can be approved
after inspection.

[![Approve dialog](images/screenshot_approve_dialog.png){:width="300px"}](images/screenshot_approve_dialog.png)

Please note that in version
0.2.3 or higher, keys with passwords are no longer
supported. Since gpg should only make sure that the file
that you are trying to open is your own file,
password-less key pairs should provide sufficient
security.

Therefore, never approve
foreign pys-files unless you have **checked thoroughly each cell**.
One cell may delete you
hard drive. And it is likely to be found somewhere in the
middle of a million rows, a million tables and a million
tabs. If unsure, inspect the pys-file. It is a bzip2-ed
text file. You can read it. You can grep in it.

It may also be a good idea
to run pyspread with a special user that has restricted
privileges.

If you like it even safer
then use a sandbox. Chroot may be a good idea. Qemu / kvm
are also worth a thought.

#### Clear globals

Pyspread lets you define globals from within cells via "=" as well as
via the macro editor. Clear globals deletes all globals but the initial
set. This option frees memory and also gets rid of any globals that are set
via macros. Afterwards, you have to re-apply the macros in order to have
them available from within the spreadsheet.

#### Page setup

Page setup provides a dialog for printer page setup. Dialog content depends
on the operating system. The settings are used for print preview and print.

#### Print preview

When selecting print preview, a dialog box is shown, in which the
spreadsheet extents (rows, columns and tables) that should be printed
can be selected.

[![Print dialog](images/screenshot_print_preview_1.png){:width="300px"}](images/screenshot_print_preview_1.png)

After pressing o.k., a second dialog window displays the print preview.

[![Print preview](images/screenshot_print_preview_2.png){:width="600px"}](images/screenshot_print_preview_2.png)

#### Print

Print prints the spreadsheet. First, a dialog similar to print preview
is opened, in which the spreadsheet extents (rows, columns and tables)
can be selected. After pressing o.k., a operation system specific
print dialog is opened. This dialog provied an option to start printing.

#### Preferences...

The preferences dialog allows changing:

* __Max. undo steps__:
    The maximum number of elementary steps
    that can be undone via Edit -&gt; Undo.
    Note that pressing one butoon may result in multiple
    elementary steps.

* __Grid rows__:
    Initial number of grid rows when pyspread is started
    without paramaters.

* __Grid columns__:
    Initial number of grid columns when pyspread is started
    without paramaters.

* __Grid tables__:
    Initial number of grid tables when pyspread is started
    without paramaters.

* __Max. result length__:
    If a results is displayed as a string (and not as e.g. a
    bitmap) then the string is truncated to the value given
    here. The string length consideerd is the number of
    Unicode characters.

* __Timeout__:
    If calculations for a cell exceed the time in
    seconds given here  then calculation is aborted.
    This does not work
    for Python functions that are C code, so e.g.
    2\*\*99999999999999999 is *not* aborted.

* __Timer interval__:
    If View -&gt; Toggle periodic updates is activated then
    all frozen cells are updated in an interval. This interval
    in milliseconds is set here.
    The change takes effect the next time that View -&gt;
    Toggle periodic updates is activated.
    Too small values may lock up pyspread.

* __GPG fingerprint__:
    If a GPG key has been selected then its id is displayed
    here. Entering a new, valid id of an existing key that
    is <i>not</i> password protected changes the GPG key
    similarly to File -&gt; Switch GPG key...

* __Open filetype__:
    The default filetype that shall be opened with File -&gt; Open.
    This should be adapted when using pyspread collaboratively via
    git, where pysu files are preferrable.

* __Save filetype__:
    The default filetype that shall be saved with File -&gt; Save or File -&gt; Save As.
    This should be adapted when using pyspread collaboratively via
    git, where pysu files are preferrable.

* __Spell checker language__:
    Available since v1.1 if pyenchant is installed.
    The spellchecking language may be chosen, here. All installed language options are presented
    in the choice box. If a language that you need is misssing, please install it globally for pyenchant
    (e.g. via your operating system repository).

[![Preferences dialog](images/screenshot_preferences_dialog.png){:width="300px"}](images/screenshot_preferences_dialog.png)

On *nix, Pyspread stores its configuration in a file
```
~/.pyspreadrc
```
This file is created when pyspread is started the first time.
Removing it resets configuration.

On Windows, them same information is stored in the registry.

Initial configuration can be found in 
```
pyspread/src/config.py
```

#### Switch GPG key...

Pyspread lets you sign your spreadsheets so that they do not have to be
approved each time that they are opened. For this functionality, gnupg
must be installed along with its Python bindings (python-gnupg).
Furthermore, a GPG keypair must be created or chosen that has
**no password**. Key choice and creation is dialog driven.
Creating a new GPG may take some time depending on the machine.

#### Quit

File -&gt; Quit exits pyspread.
If changes have been made to a new or loaded file then
a dialog pops up and asks if the changes shall be saved.

### Edit menu

#### Undo

Most user actions in pyspread can be undone by Edit -&gt; Undo
(Shortcut: &lt;Ctrl&gt; + Z). Exceptions are:

* Loading a file (empties undo list)
* Saving a file (ignored)
* Approving a file (ignored)
* Deleting global variables

The undo list is limited.
The limit can be set in the File -&gt; Preferences dialog.

#### Redo

Undone steps can be redone with Edit -&gt; Redo
(Shortcut: &lt;Shift&gt; + &lt;Ctrl&gt; + Z).

#### Cut

Edit -&gt; Cut behaves like Edit -&gt; Copy and pressing the
&lt;Del&gt; key afterwards, i.e. the current cell code is
copied and the cell is deleted.
If cells are selected then the operations are applied to all
cells in the bounding box of the marked cells.

#### Copy

Edit -&gt; Copy copies cell code of the current cell (the one
with the cursor) is copied.
If cells are selected then the
copied set consists of the bounding box of the marked
cells, i. e. the smallest box, in which all cells are
situated. Cells that are not selected in that box are
copied as if they were empty.
The format of cells that are
copied is tab separated Unicode.

#### Copy results

Edit -&gt; Copy Results copies a string representation of
the current cell's result object.
If e.g. the cell code of the current cell is 4*"a" then
aaaa is copied to the Clipboard.
As in Edit -&gt; Copy,  if cells are selected then the
copied set consists of the bounding box of the marked
cells.
Copy Results is useful, if for example results shall be copied
into an external application.

#### Paste

When pasting cells, these
empty cells are pasted as well as the filled cells. That
means that an unselected cell in a marked area will be
pasted as empty cell.

Images can be inserted via
copy and paste. This creates cell code, which contains a
serialized string that represents the bitmap. The code can
be of considerable size. Therefore, it is normally split
into multiple lines. Line breaks inside a cell are ignored
by pyspread. Therefore, each cell behaves like one line of
Python code even if multiple lines are displayed in the
cell editor.

#### Paste As

Data can also be pasted with
Paste As. The keyboard shortcut is &lt;Shift&gt; +
&lt;Ctrl&gt; + V. A dialog appears, in which the target
dimensionality can be specified. If the transpose box is checked
then the data is
transposed. With this feature, fine grained access to
which target data object dimensions are pasted into single
cells and which are distributed across cells.

[![Paste As dialog](images/screenshot_paste_as.png){:width="200px"}](images/screenshot_paste_as.png)

#### Select All

Select All selects all cells of the current table.
The keyboard shortcut is &lt;Crtl&gt; + A.

#### Find

Cell code and cell results
can be searched with &lt;Ctrl&gt; + F or using the menu
with Edit -&gt; Find. The focus changes to the search
toolbar, in which search queries can be entered. Pyspread
allows searching contained text, word-wise contained text
and regular expressions, which can be toggled in the
search toolbar. Similarly upper and lower case sensitivity
can be toggled via the search toolbar. More details are
giveen in the Find toolbar section.

#### Replace

Replacing is done via the
Find &amp; Replace dialog that is accessible via
&lt;Shift&gt; + &lt;Ctrl&gt; + F or via Edit -&gt;
Replace... Strings that are found are replaced with the
replace string. Note that replace only allows searching in
cell code and not in results.

[![Replace dialog](images/screenshot_replace.png){:width="200px"}](images/screenshot_replace.png)

#### Quote cell(s)

Quote cells puts Unicode quotations around the cell code of
each selected cell or the current cell if no selection is
present. Quotations mean that the cell content is interpreted
as a Python unicode object, i.e. u" is put before the start
and " at the end of the cell code.
The keyboard shortcut is &lt;Crtl&gt; + &lt;Enter&gt;.


Quotation is <i>not</i> done if
* there is no code in the cell or
* the character \" appears in the code or
* the first and last character combination is any of: \"\", \'\', u\', u\"
    
#### Sort ascending

Sorts all rows of the current table accendingly
according to the order of the
cell result objects from the column of the current cell.
Cells that return None are sorted last.

#### Sort descending

Sorts all rows of the current table decendingly
according to the order of the
cell result objects from the column of the current cell.
Cells that return None are sorted last.

#### Insert rows

Inserts one row directly above the cursor if no selections are
made.
If selections are present, then the bounding box that covers all
selected cells is calculated, and the number of rows of this
bounding box is inserted above the bounding box.

#### Insert columns

Inserts one column directly left of the cursor if no selections
are made.
If selections are present, then the bounding box that covers all
selected cells is calculated, and the number of columns of this
bounding box is inserted just left of the the bounding box.

#### Insert table

Inserts one table directly before the current table and switches
to this new table.

#### Delete rows

Deletes the cursor row if no selections are made.
If selections are present, then all rows in the bounding box
that covers all selected cells are deleted.

#### Delete columns

Deletes the cursor column if no selections are made.
If selections are present, then all columns in the
bounding box that covers all selected cells are deleted.

#### Delete table

Deletes the current table.

#### Resize grid

Changes the grid size. Similar to File -&gt; New, a dialog
is shown, in which the new number of rows, columns and tables
can be set. The grid size is changed accordingly. Cells that
stay remain identical. Cells that are added are empty. Cells
that are removed are deleted and cannot be accessed any more.

### View menu 

#### Fullscreen

Toggles fullscreen mode, in which only the grid is visible on the screen.
In fullscreen mode, the mouse wheel changes tables as if the mouse were
in the table selection widget right to the entry line.
&lt;F11&gt; acts as shortcut to the fullscreen mode toggle.

Fullscreen mode has been added so that interactive presentations can be
shown with pyspread.

#### Toolbars

Toolbars contains a sub menu, in which the different toolbars can
be switched on and off.

#### Entry line

Swiches the entry line on and off.

#### Table list

Swiches the table list on the left side of the grid on and off.
The table list was introduced in v1.1 in order to improve usability
when using mice with poor wheels that jump over tables.
Note that switching on the table list limits the maximum number of
tables that pyspread supports to a few million tables depending on
the platform.

#### Go to cell

Go to cell opens a dialog, in which a cell can be specified via
row, column and table. After pressing o.k., the specified cell
becomes the current cell, and it is put into view on the grid.
This involves switching to another grid table if necessary.

#### Check spelling

Activates the spell checker for pyspread >=1.1 if pyenchant is
installed. All cells with text results are checked in the currently
active language that may be altered in the File &gt; Preferences
dialog. Words that are unknown are marked with a red curly underline. 

#### Zoom in

Zooms the grid in by 5%.

#### Zoom out

Zooms the grid out by 5%.

#### Normal size

Reset the grid zoom level to 100%.

#### Zoom to fit

New in v1.1. Zooms the grid so that it fits into the screen.
This also works in fullscreen mode with the &lt;F6&gt; shortcut key.
Note that if the grid is too large, which is the case for standard
grids on normal screens, nothing happens. For screen presentations,
minimize the grid size.

#### Refresh selected cells

Executes code of cells that are selected and frozen and updates
their cell results in the grid. If no cell is selected then the
current cell is refreshed. The shortcut for Refresh selected cells
is &lt;F5&gt;.

This action has <i>only</i> effects on cells that are frozen.

#### Toggle periodic updates

Periodically executes code of cells that are frozen and updates
their cell results in the grid. The period can be adjusted in the
Preferences dialog: Set the desired period as "Timer interval"
in seconds.

#### Show frozen

Toggles display of a diagonal blue stripe pattern on the
background of each frozen cell.

### Format menu

#### Copy format

New in v1.1. Copies only the format of the selected cells.
Copying formats has been separated from copying content 
in order to prevent unwanted behavior.

#### Paste format

New in v1.1. Pastes copied cell formats.

#### Font...

Assigns a font including style and size to the current cell
if no selection is present. If a selection is present, the font
is assigned to each selected cell.

The fonts are **not**
stored within the pys file.
Therefore, fonts have to be available at the
target system when opening a pys file.
Otherwise, the font is replaced by the default font.

#### Bold

Bold toggles the current selection's cell font bold attribute.
If no cell is selected, then the attribute is toggled for the
current cell. The shortcut for Bold is &lt;Ctrl&gt; + B.

#### Italics

Italics toggles the current selection's cell font italics
attribute.
If no cell is selected, then the attribute is toggled for the
current cell. The shortcut for Italics is &lt;Ctrl&gt; + I.

#### Underline

Underline toggles the current selection's cell font underline
attribute.
If no cell is selected, then the attribute is toggled for the
current cell. The shortcut for Underline is &lt;Ctrl&gt; + U.

#### Strikethrough

Strikethrough toggles the current selection's cell font
strikethrough attribute.
If no cell is selected, then the attribute is toggled for the
current cell.

#### Text color...

Opens a dialog, in which a color can be chosen.
On o.k., the text color is set to the chosen color for
all cells in the current selection. If no cell is selected,
then the text color is set for the current cell.

#### Background color...

Opens a dialog, in which a color can be chosen.
On o.k., the background color is set to the chosen color for
all cells in the current selection. If no cell is selected,
then the background color is set for the current cell.

#### Markup

Markup allows using pango markup for cell output formatting.
This is useful for formatting only parts of a cell output.
Any cell output is parsed for valid pango markup. If found
then it is interpreted.


An overview of pango markup can be found 
[here](https://developer.gnome.org/pango/stable/PangoMarkupFormat.html).
Some convenience functions are:

| b    | Bold                          |
| big  | Makes font relatively larger  |
| i    | Italic                        |
| s    | Strikethrough                 |
| sub  | Subscript                     |
| sup  | Superscript                   |
| small| Makes font relatively smaller |
| tt   | Monospace font                |
| u    | Underline                     |

#### Justification

Opens a sub-menu, in which cell justifications can be chosen from
left, center and right. The chosen justification is applied
to all cells in the current selection. If no cell is selected,
then it is applied to the current cell.

Besides text output, justification also applied to bitmap and
vector graphics that are displayed in the cell. Matplotlib
charts are an exception: They are always stretched to cell
limits and therefore ignore justification.

#### Alignment

Opens a sub-menu, in which cell alignment can be chosen from
top, center and bottom. The chosen alignment is applied
to all cells in the current selection. If no cell is selected,
then it is applied to the current cell.

Besides text output, alignment also applied to bitmap and
vector graphics that are displayed in the cell. Matplotlib
charts are an exception: They are always stretched to cell
limits and therefore ignore alignment.

#### Rotation

Opens a sub-menu, in which cell rotatation can be chosen from
0, 90, 180 and 270 degree. The chosen rotatation is applied
to all cells in the current selection. If no cell is selected,
then it is applied to the current cell.

Besides text output, rotatation also applied to bitmap and
vector graphics that are displayed in the cell. Matplotlib
charts are an exception: They ignore cell rotation.

#### <a name="frozen">Frozen</a>

The frozen button (flurry button toggles the frozen attribute
for the current cell (*not* the
selection). Frozen cells are immediately executed once.
Cell results are stored in a cache.
Instead of re-evaluating the cell result each time that
another cell is updated, frozen cells always display the
old, stored result.

The flurry button can only
mark one cell at a time as frozen. The selection is
ignored for this purpose. Only the cell at the cursor is
frozen.

Frozen cells can be
refreshed using the menu with View -&gt; Refresh Selected
Cells or with &lt;F5&gt;. All selected cells are refreshed
by this command.

Frozen cells can speed up
spreadsheets with long running calculations. Furthermore,
the number of callings of stateful functions can be
controlled.

While the frozen
attribute is stored in the pys save-file, the frozen cell
result cache is **not** saved.

#### Lock

Lock toggles the current selection's cell lock attribute.
If no cell is selected, then the current cell is locked.
Locking means that the cell cannot be edited from within pyspread
until it is unlocked again.

#### Merge cells

Merge cells merge all cells that are in the bounding box of the
current selection. If there is no selection the the current
cell will be merged (with itself) or unmerged if already merged.
Merged cells act as one. Output is shown for the top left cell,
which stays intact upon a merge.

### Macro menu

#### Macro list

Macros can be edited from
within the macro editor via Macro -&gt; Macro list
(Figure). The editor allows editing a text file that is
executed when the spreadsheet is opened or when its
content is updated.

[![Macro panel](images/screenshot_macros.png){:width="300px"}](images/screenshot_macros.png)

The Apply button executes the macro code.
Output (including exceptions) are shown in the lower part of the
macro editor.

The scope of macro execution
is global. Therefore, all functions are directly
accessible from each cell. For example, the function f
that is displayed in the Figure can be called from a cell
via f(). The result is the returned string "Hello World".

Since cell evaluation order
is not guaranteed in pyspread, macros can be used for
operations that enforce state. One example for such
operations are some module imports such as rpy2.
Furthermore, algorithms that are too complex for a single
cell can be written as a macro.

#### Load macro list

Macros can be loaded from files. The file format is UTF-8.
Basically, any pure Python file is acceptable.
When loaded, the new file content is appended to existing
macros.

Since macros may be harmful, loading macros makes the pys
file unapproved, i.e. before any further calcluations are done,
the file has to be approved again via File -&gt; Approve file.

#### Save macro list

Saves the macros in the macro editor to a file.

#### Insert bitmap...

The "Insert bitmap" option
in the Macros menu is Identical to the copy and paste
functionality.

#### Link bitmap...

Since version 0.2.3, images can be displayed in cells.
Each cell, which yields a wx.Bitmap object, displays the bitmap.
For each cell that yields a valid SVG xml string, the SVG ist displayed.


Linking an image with the
"Link bitmap" option in the Macros menu generates code
that refers to an image on the file system. This method
allows displaying high resolution images in a pyspread
grid. Please not that the image path is currently
absolute. You can replace it manually with a relative
path.

#### Insert chart...

Since version 0.2.3, pyspread can generate 
[matplotlib](http://matplotlib.org") charts.
Each cell, which yields a matplotlib figure displays this
figure. The bitmap is stretched to the cell's extents.

The "Insert chart" option in
the Macros menu provides an easy way of generating
matplotlib figures. They generate code of a special class
charts.ChartFigure that is provided by pyspread. This
class subclasses the matplotlib Figure class. The subclass
takes matplotlib arguments and creates a figure in one
step. The dialog creates the code for doing that. It also
parses any code starting with charts.ChartFigure and
figures out, which choice had been made last time. This
may very well fail if you changed the cell code manually.
For further reference, the 
[matplotlib Web site](http://matplotlib.org/api/pyplot_api.html")
is recommended.

Note that pyspread cells display all types of matplotlib figures.
The chart dialog just provides a convenient user to create and 
edit common chart types.

Since version 0.4, six chart types are supported by the chart dialog:
Plots, i.e. line charts, bar charts,
histograms, box plots, pie charts and annotations. Note
that pie charts cannot be combined with other chart type
yet. Please suggest other chart types that you find usable
by posting at the 
[pyspread issue tracker](https://github.com/manns/pyspread/issues).

[![Chart dialog](images/screenshot_chartdialog.png){:width="800px"}](images/screenshot_chartdialog.png)

The chart dialog is designed as a fast to use graphical front-end for
common matplotlib properties. Attributes correspond to matplotlib function
properties. Each property is described in tooltips.
The chart dialog consists of three parts (from left to right):
The Axes panel, the Series panel and a Chart preview panel.

##### Axes panel

The Axes panel allows changing X and Y axes attributes. Other axes types
such as Z axis in 3D charts are not supported by the chart dialog.
The axes panel is structured into three sections: Axes, X-Axis and Y-Axis.

In the first box, overall figure attributes can be set, which is title
text, the title text font and color and id a legend is drawn. The text
entry field for the title text accepts Python expressions, i.e. if you want
a specific string to be displayed as the title, you have to quote the text.
However, if you want a certain global variable of cell content to be
displayed then you can enter the object name. Functions and operators are
also allowed as long as they return a string or unicode like object.
Note that this applies for all fields of the chart dialog unless otherwise
specified.

In the second box, X-axis attributes are specified. The X-axis label is
provided again as a Python expression. Font and color can be specified.
Next, X-axis scaling can be set to linear (no check) or logarithmic (check),
and the X-axis grid can be turned on and off. If the X-axis shall display a
date instead of values and if a datetime.date object is provided as input 
for the x-axis values then the date format field should be filled with
a strftime format string. Details about the format string are given in the
tooltip. The ticks field accepts a list or a tuple of numbers or floats.
At these locations, axis ticks are set when specified. If left empty, axis
ticks are set automatically. The label field lets the user specify
arbitrary text as label at a tick. Font and color of the labels can be
specified here. The secondary ticks option allows ticks to be displayed
on the opposide side of the chart, i.e. on the top as at the bottom.
The outside, inside, both choice specifies, where the ticks are situated at
the axis. Padding allows setting the distance between label text and axis.
Size lets the user specify text size if no explicit labels are given in the
labels field.

In the third box, Y-axis attributes are specified. Attributes match those
of the X-axis both in content and format with the exception of the date
format field, which is not available for the Y-axis.

##### Series panel

The Series panel allows adding one or more series to the axes. In order to
add a new series, click on the + tab at the bottom of the panel. A series
is deleted with the x right of the tabs. You can switch between series by
clicking on the respective tabs.

Each data series can be of a specific type that is chosen from the list
that is on the left side of the Series panel. In version 1.0.3 there are
eight series types: plot, bar, hist, boxplot, pie, annotate, contour and
Sankey. Note that the series type names correspond to the respective
matplotlib names. Other types of matplotlib series are not supported in
the chart dialog. If such a need arises please post an e-mail to the
[pyspread issue tracker](https://github.com/manns/pyspread/issues).

##### Plot chart

When the plot chart type is selected then on the right panel, Data, Line
and Marker boxes are displayed.

In the Data box, a data label can be
specified that appears in the legend if it is activated. The X field is
optional. It has to be an iterable of the same length of Y and allows
specifying the X values of each data point. In the Y field, Y values of
each point are specified in an iterable.

In the Line box, the line style chosen from solid, dashed, dash-dotted and
frozen. Its width can be specified in points (integer values only) as well
as its color. 

In the Marker box, the marker style for the actual data points may be 
chosen from a range of 22 styles. The maerker size can be specified (integer
values only) as well as its face and egde colors. The marker alpha value is
set with a floating point value, where 1.0 is solid and 0.0 is fully 
transparent.

[![Chart dialog with plot chart](images/screenshot-chartdialog-plot.png){:width="800px"}](images/screenshot-chartdialog-plot.png)

##### Bar chart

When the bar chart type is selected then on the right panel, Data and
Bar boxes are displayed.

In the Data box, a data label can be
specified that appears in the legend if it is activated. The left 
positions field is mandatory. It expects an iterable of left bar values
that is as long as the bar heights iterable that defines the upper limits
of the bars (not the bar lengths). The bar widths field expects either a 
number that applies to all bars or an iterable so that specific bars may 
have different widths.  The bar bottoms field is optional and defines the 
lower limit of the bars. Similarly to the widths field, it allows entering a
number or an iterable.

In the Bar box, the bar fill and edge color can be chosen. Furthermore, an
alpha value can be specified with a floating point value, where 1.0 is solid
and 0.0 is fully transparent.

Note that while bar charts may be morte difficult to use than plot charts,
they can be used in order to plot arbitrary rectangles, which makes them 
also applicable for example to plot simple top down views on room layouts.

[![Chart dialog with bar chart](images/screenshot-chartdialog-bar.png){:width="800px"}](images/screenshot-chartdialog-bar.png)

##### Histogram

When the histogram chart type is selected then on the right panel, Data and
Histogram boxes are displayed.

In the Data box, a data label can be
specified that appears in the legend if it is activated.
The data series that has to be provided is an iterable of numerical values.
Categorical values are **not** supported here because this is not 
supported by matplotlib. Value tuples are also not supported.

In the Histogram box, the number of bin can be specified as an integer
value. If Normed is checked then the integral of the histogram will sum to
1. If stacked is also True, the sum of the histograms is normalized to 1.
If culumative is checked then then a histogram is computed where each bin
gives the counts in that bin plus all bins for smaller values. The last bin
gives the total number of datapoints. Furthermore, the histogram bar color 
can be set. The alpha value can be specified with a floating point value, 
where 1.0 is solid and 0.0 is fully transparent.

[![Chart dialog with histogram](images/screenshot-chartdialog-hist.png){:width="800px"}](images/screenshot-chartdialog-hist.png)

##### Boxplot

When the boxplot chart type is selected then on the right panel, Data and
Box plot boxes are displayed.

In the Data box, a sequence of numerical values or a sequence of sequences
can be provided. In the latter case, multiple boxplots are combined in
one diagram. 

In the Box plot box, the box width can be specified as a floatig point
value. If vertical is checked then the boxplots are frawn vertical
else horizontal. Flier symbols may be chosen from 22 choices. If notch is
checked then the main box shows a notch at the median value.

[![Chart dialog with boxplot](images/screenshot-chartdialog-boxplot.png){:width="800px"}](images/screenshot-chartdialog-boxplot.png)

##### Pie chart

When the pie chart type is selected then on the right panel, Data and
Pie boxes are displayed.

In the Data box, a sequence of numerical values can be provided.

In the Pie box, labels for the wedges can be specified as a sequence of objects (e.g. strings). Wedge colors are provided in the Colors text box as sequence of strings, where colors can be the strings "b" (black) "g" (green) "r" (red) "c" (cyan) "m" (magenta) "y" (yellow) "k" (black) "w" (white), a floating point number between 0.0 and 1.0 for gray values or an htm hex string such as "#a36271". The pie chart can be rotated with the angle value, which may be a positive or negative integer. The checkbox shadow enables or disables a shadow behind the pie chart.

[![Chart dialog with pie chart](images/screenshot-chartdialog-piechart.png){:width="800px"}](images/screenshot-chartdialog-piechart.png)

##### Chart annotation

When the annotation chart type is selected then on the right panel, an Annotation box is displayed.
There, a text can be entered as a string along with a 2-tuple of coordinates. In a choice box, information, what these coordinates refer to, is given. Annotations mostly make sense as an additional figure layer.

[![Chart dialog with chart annotation](images/screenshot-chartdialog-annotation.png){:width="800px"}](images/screenshot-chartdialog-annotation.png)

##### Countour chart

When the contour chart type is selected then on the right panel, Data and
Lines, Areas and Labels boxes are displayed.

In the Data box, x and y values form a mesh for which z values are specified. Note that z must be a one-time nested list. For optimizing performance, the numpy helper functions meshgrid may be used as z may also be a 2D numpy array.

In the Lines box, the style, width, color and alpha value of the contour separating line may be specified. The line wdth must be an Integer value. The colors are provided in the Colors text box as sequence of strings, where colors can be the strings "b" (black) "g" (green) "r" (red) "c" (cyan) "m" (magenta) "y" (yellow) "k" (black) "w" (white), a floating point number between 0.0 and 1.0 for gray values or an htm hex string such as "#a36271".
Note that the colors are also used for the filling of the contour. Therefore, two overlaying contour plots may be combined in order to get e.g. black contour lines for a coloured contour.

In the Areas box, filling of the contour can be turned on and off and hatch types can be specified that is overlaid with the filling. The hatch types can be given in a sequence of hatch strings. A hatch string can be one of: <br>
/   - diagonal hatching<br>
\   - back diagonal<br>
|   - vertical<br>"
-   - horizontal<br>
+   - crossed<br>
x   - crossed diagonal<br>
o   - small circle<br>
O   - large circle<br>
.   - dots<br>
*   - stars<br>
Letters can be combined, in which case all the specified hatchings are done. If same letter repeats, 
it increases the density of hatching of that pattern. 
Note that when the color is white then the mesh type is displayed as black on white. 

In the Labels box, contour labels can be turned on and off, and the font size can be spezified as an Integer.

[![Chart dialog with contour chart](images/screenshot-chartdialog-contour.png){:width="800px"}](images/screenshot-chartdialog-contour.png)

##### Sankey diagram

When the Sankey chart type is selected then on the right panel, Data and
Diagram and Area boxes are displayed.

In the Data box, flows and orientations can be specified as sequences of numbers. Flows have positive numbers
for inputs and negative numbers for outputs. The absolute value of the number specifies the arrow width.
Orientations may have the values are 1 (from/to the top), 0 (from/to the left or right), or -1 (from/to the bottom). If orientations == 0, inputs will break in from the left and outputs will break away to the right.
Labels may be specified as a sequence of strings - either one string for all arrows or one per arrow. Each label is followed by the value and the unit. Values are formatted using a Python formatting string

In the Diagram box, rotatation, gap, radius, shoulder, offset and angle can be specified, which control the 
layout of the Sankey diagram.

In the Area box, the color of the diagram edge and the diagram filling can be set.

[![Chart dialog with Sankey diagram](images/screenshot-chartdialog-sankey.png){:width="800px"}](images/screenshot-chartdialog-sankey.png)

The figure panel is automatically updated whenever content of the chart
dialog is changed. Should it show no chart then something is wrong with
the input so that later in the grid, no chart is shown as well.

### Help menu

#### First steps

This document can be
displayed from within pyspread via the menu with Help
-&gt; First Steps.

#### Tutorial

Help -&gt; Python tutorial displays the official Python tutorial
from the Internet.
Note that a working Internet connection is required to
access the Python tutorial.

#### FAQ

Help -&gt; FAQ, shows a page with frequently asked questions.

#### About

Help -&gt; About informs about pyspread's current version, license
and contributors. The exact layout depends on the oprtation
system.

## Context menu

Besides the main menu, pyspread provides a context menu that
is accessible by right-clicking on the grid. It contains the
following items:

* Cut
* Copy
* Paste
* Insert rows
* Insert columns
* Delete rows
* Delete columns

All options in the context menu are identical to those in the
edit menu.


## Toolbars

### Main toolbar

#### New

    Shortcut to File -&gt; New.

#### Open

    Shortcut to File -&gt; Open.

#### Save

    Shortcut to File -&gt; Save.

#### Export PDF

    Exports a PDF file similar to choosing PDF file when in the
    file choice dialog of File -&gt; Export.

#### Undo

    Shortcut to Edit -&gt; Undo.

#### Redo

    Shortcut to Edit -&gt; Redo.

#### Find

    Shortcut to Edit -&gt; Find. Focuses the find textbox in the find toolbar.

#### Replace

    Shortcut to Edit -&gt; Replace...

#### Cut

    Shortcut to Edit -&gt; Cut.

#### Copy

    Shortcut to Edit -&gt; Copy.

#### Copy results

    Shortcut to Edit -&gt; Copy results.

#### Paste

    Shortcut to Edit -&gt; Paste.

#### Sort ascending

    Shortcut to Edit -&gt; Sort ascending.

#### Sort descending

    Shortcut to Edit -&gt; Sort descending.

#### Print

    Shortcut to File -&gt; Print.

### Find toolbar
#### Search textbox

In this text editor, a search string can be entered.
When the textbox is focused via menu, toolbar or
via &lt;Ctrl&gt; + F then the prior text is selected.
When entered via mouseclick, it is not selected.


Cells are searched when pressing the &lt;Enter&gt; key or by
clicking on the magnifying glass icon in the left corner of the
textbox. The search always starts at the current cell.
If the search direction is down (standard setting) then the search
advances down through the current column then through the next
column to the right and so on. When the search reaches the end
of the table, it continues with the first column of the
next table. When it reaches the last table then it continues
at the first column of the first table.


For each non-empty cell, the cell code is searched, i.e.
Python code of the cell is searched for occurrences of the search string.
If there is no match then the string output of the result object,
i.e. the result from the str method of the cell is searched.
If either the code or the string output contains the search string
then the cell is put into view and becomes the current cell.
Furthermore, the text in the find textbox is selected.


When clicking on the downfacing triangle next to the magnifying glass
icon in the textbox then a drop-down menu appears. The drop-down menu
contains up to 10 recent search strings. When one of these search
strings is selected, it replaces the current search string in the
textbox.

#### Search direction

Toggles the search direction between down and up.

If the search direction
is down, the search behaves as described in the section search textbox.

If the search direction is up then the search instead advances up through
the current column.
It continues in the next column to the left. When at the top left cell
of the table then it continues with the previous table. If it reaches
cell [0, 0, 0] then it continues with the bottom right cell of the last
table.

#### Case sensitive

Toggles the search between case insensitive (standard, button not activated)
and case sensitive (button activated).

If the search is case insensitive then both the search string and the searched
string are lowercased before looking if the search string is contained in the
searched string.

If the search is case sensitive then the original strings are used.

#### Regular expression

Toggles the search between standard search (button not activated)
and regular expression search (button activated).

If the search is standard then the searched string is queried via Python's
__contains__ method, i.e. as in "search_string in seaarched_string". This is
the standard behavior.

If the search is a regular expression search then Python's module "re"
is invoked. The search string is treated as search pattern. The 
[Python documentation on the re module](https://docs.python.org/2/library/re.html)
provides an overview of how to build regular expressions. 
There are various help pages and tutorials
on the Web that focus on use cases.


Note that regular expression searches can be significantly
slower than standard searches.

#### Surrounded by whitespace

Toggles the search between standard search (button not activated)
and surrounded by whitespace search (button activated).

If the search is standard then any substring match inside
the searched string counts as valid.

If the search is a surrounded by whitespace search then the substring
inside the searched string has to be preceeded and succeeded by a
whitespace character. Otherwise, the substring does not count as
occurrence.

### Format toolbar
#### Text font

Choice box that contains the fonts that are available on the system.
On GTK platforms, the font names are displayed in the respective font.

If a font is selected then it is assigned to the current cell
if no selection is present. If a selection is present then the font
is assigned to each selected cell.

#### Text size (points)

Choice box that contains a choice of font sizes.

If a font size is selected then it is assigned to the current cell
if no selection is present. If a selection is present then the font
is assigned to each selected cell.

#### Bold

Shortcut to Format -&gt; Bold.

#### Italics

Shortcut to Format -&gt; Italics.

#### Underline

Shortcut to Format -&gt; Underline.

#### Strikethrough

Shortcut to Format -&gt; Strikethrough.

#### Freeze

Shortcut to Format -&gt; Freeze.

#### Lock cell

Shortcut to Format -&gt; Lock.

#### Markup

Shortcut to Format -&gt; Markup.

#### Cell text rotation

Toggle button that switches between 0&deg;, 90&deg;, 180&deg; and 270&deg;
cell rotation. Pressing the text rotation button is
equivalent to selecting
an entry in the Format -&gt; Rotation sub-menu.

#### Justification

Toggle button that switches between left, centered and right
justification.
Pressing the justification button is equivalent to selecting
an entry in the Format -&gt; Justification sub-menu.

#### Alignment

Toggle button that switches between top, center and bottom
alignment.
Pressing the alignment button is equivalent to selecting
an entry in the Format -&gt; Alignment sub-menu.

####  <a name="border_choice_box">Border choice box</a>

When changing border color or width, the command affects the selection
or -if no selection is present- the current cell. Since a cell has four
borders, all borders are affected by default. The border choice box
allows changing this behaviour by providing the following options:

* All borders: All borders are affected
* Left border: Only the left border of the smallest containing
  bounding box is affected. 
* Right border: Only the right border of the smallest containing
  bounding box is affected.
* Top border: Only the top border of the smallest containing
  bounding box is affected.
* Bottom border: Only the bottom border of the smallest containing
  bounding box is affected.
* Outer borders: All outer borders of the smallest containing
  bounding box are affected.
* Top and bottom borders: Only the top and the bottom border of the
  smallest containing bounding box are affected.

Each selection other that All borders refers to the smallest bounding box
that includes the current selection. This bounding box may include cells
that are not selected. Therefore, cell borders of non-selected cells may be affected.

#### Border width

Choice box that changes cell border widthes. The section
<a href="#border_choice_box">Border choice box</a>
explains, which borders are affected.
There are 11 different border widths.
The first width is 0, which means that no border is drawn.

#### Border line color

Invokes a color choice dialog that changes cell border color. The section
<a href="#border_choice_box">Border choice box</a>
explains, which borders are affected.
The border color is chosen as an RGB value. The color choice dialog may
look different depending on the operating system.

#### Cell background

Invokes a color choice dialog that changes cell background color for
all selected cells or for the current cell if no cells are selected.
The background color is chosen as an RGB value. The color choice dialog may
look different depending on the operating system.

#### Text color

Invokes a color choice dialog that changes the text color for
all selected cells or for the current cell if no cells are selected.
The text color is chosen as an RGB value. The color choice dialog may
look different depending on the operating system.

#### Merge cells

Merges cells that are in the smallest bounding box of the current selection.
In a merge, all but the top left cells are emptied and the size of the top left
cell is extended so that it includes all merged cells.

If the top left cell of the bounding box is already merged then the merged
cells are unmerged and no merging takes place. This also takes place if there
is no selection and the current cell is a merged cell.

While it is posssible to create overöapping merged cells this is not recommended.
It may result in loosing content of cells and will result in drawing errors.

### Macro toolbar
#### Insert bitmap

Shortcut to Macro -&gt; Insert bitmap...

#### Link bitmap

Shortcut to Macro -&gt; Link bitmap...

#### Insert chart

Shortcut to Macro -&gt; Insert chart...

### Widget toolbar
#### Button like cell

When pressed, a text entry dialog is opened, in which the text for
a button label can be entered. If no text is entered then no button is
created. However, whitespace labels are possible to get "empty" buttons.


After pressing Ok, the current cell shows a button with the entered label.
The cell code of the cell now is executed only if the button cell is clicked.
This behavior allows manually starting functions without resorting to the
<a href="#frozen">frozen cell mechanism</a>.

A button can be removed by making the buttoon cell the current cell and
then pressing on the tool "Button like cell" again.

#### Video cell

New in v1.1. Requires vlc-dev.
Opens a dialog, in which a video file can be chosen.
This video file is then played back with a vlc instance in the
current cell. The video is always linked and not included in the
pys file upon save. Playback can be started and stopped with the
left mouse button. Sound volume can be adjusted with the mouse wheel.
Multiple videos can be played back in parallel. Note that video
playback is considered experimental.

## Entry line

Code is entered into the grid cells via the entry line.
Code can also be entered by selecting a cell and then typing
into the appearing cell editor. Code
is accepted and evaluated when &lt;Enter&gt; is
pressed or when a new cell is selected.

When data shall be displayed as text, it has to be quoted so
that the code represents a Python string. In order to make
such data entry easier, quotation is automatically added if
&lt;Ctrl&gt;+&lt;Enter&gt; is pressed after editing a cell.
If multiple cells are selected then
&lt;Ctrl&gt;+&lt;Enter&gt; quotes all selected cell.

When entering data in the entry line, pyspread &gt;=v0.3.0
offers code completion and context help if the jedi package
is installed. When &lt;Tab&gt; is pressed while typing, an
unambiguous suggestion for the next characters is made.
Furthermore, the entry line tooltip is changed so that it
contains information about all found completions. The
tooltip is truncated to 1000 characters.

## Insertion mode toggle button

On GTK platforms, the insertion mode toggle button provides a
convenient way of referencing cells with the mouse so that
typing S[X+a,Y+b,Z] in many cases becomes unnecessary.
Note that on Windows, this functionality is not available.
Therefore, the toggle button is permanently disabled on Windows.

When activating the insertion mode toggle button, make sure that
the cursor in the entry line is at a possition at which you want
to insert a cell reference. When the button is activated, the
entry line and the grid editors are disabled, so that no cell
code may be changed manually. Now, select all cells that you want
to reference. Selections may be chossen by dragging a selection
on the grid as well as with &lt;Ctrl&gt; + &lt;Left click&gt; on
cells. Each time that a selection is chosen, i.e. the left button
is clicked without pressing &lt;Ctrl&gt;, a string that references
to all selected cells is inserted into the text editor for the
cell that was current when activating insertion mode.

Note that inserting two selections will normally result in invalid
Python code. unless "+" is put between the expressions.

For example, if you want to sum over three cell areas, you may write
"sum()" into the entry line and place the cursor between the parentheses.
Next you click on the insertion toggle button. While you keep &lt;Ctrl&gt;
pressed all the time, you select one range and two cells individually.
Then you press the insertion toggle button again.
The resulting code may look like this:
```Python
sum([S[key] for key in 
    [(r, c, 0) for r in xrange(1, 5) 
        for c in xrange(5, 7)] + 
        [(9, 7, 0)] + 
        [(11, 7, 0)] if S[key] is not None])
```
## Table selector

Tables can be switched by
changing the number in the table selector that is
situated right of the entry line directly above the grid.

This can be achieved by
either typing in a table number or by moving the mouse
over the table switch textbox and then scrolling with the
mouse wheel.

## Grid

### Changing cell content

In order to change cell
content, double-click on the cell or select the cell and
edit the text in the entry line.

### Deleting cell content

A cell can be deleted by
selecting it and pressing &lt;Del&gt;. This also works for
selections.

### Selecting cells

Cells can be selected by the following actions:

* Keeping the left mouse button pressed while over cells selects a block

* Pressing &lt;Ctrl&gt;
  when left-clicking on cells selects these cells
  individually

* Clicking on row or
  column labels selects all cells of a row or column

* Clicking on the top-left
  label of the grid or pressing &lt;Ctrl&gt; + A selects
  all grid cells of the current table

Only cells of the current
table can be selected at any time. Switching tables
switches cell selections to the new table, i.e. the same
cells in the new table are selected and no cells of the
old table are selected.

## Status bar

The status bar at the bottom of pyspread's main window
displays feedback for many operations:

* If the mouse is positioned over a cell, the cell code
  is displayed.

* Long running activities such as open and save may show hints on
  how to abort them.

* Find actions show information about the cell, in which
  the last occurrence has been found.

# Advanced topics

## Cyclic references

Cyclic references are possible in pyspread. However,
recursion depth is limited. Pyspread shows an error when
the maximum recursion depth is exceeded.
It is strongly advisable to only use cyclic references
when either a frozen or a button cell interrupts the cycle.
Otherwise, cyclic calculations may lock up pyspread.

## Result stability
Result stability is not guaranteed when
redefining global variables because
execution order may be changed. This happens for when in
large spreadsheets the result cache is full and cell
results that are purged from the cache are re-evaluated.

## Error handling
Cells, which contain expressions that raise an exception 
return the error string.

## Security annoyance when approving files in read only folders
If a pys file is situated in
a folder without write and file creation access, the
signature file cannot be created. Therefore, the file has
to approved each time it is opened.

## Handling large amounts of data
While the pyspread main grid
may be large, filling many cells may consume considerable
amounts of memory. When handling large amounts of data,
data that is loaded within one cell saves memory,
Therefore, load all your data in a numpy array that is
situated within a cell and work from there.

## Substituting pivot tables
In the examples directory, a Pivot table replacement is
shown using list comprehensions.

## Memory consumption for sheets with many matplotlib charts
If there are hundreds of charts in a spreadsheet then
pyspread can consume considerable amountss of memory.
This is most obvious when printing or when creating PDF files.
Be warned that 100 line charts in one spreadsheet table may require
10 GB of RAM.

One solution to this issue is to generate an SVG image
from each chart and insert it into the spreadsheet. 

# Contact

|Issues:|[pyspread issue tracker](https://github.com/manns/pyspread/issues)|
|E-mail:|mmanns &lt; at &gt; gmx &lt; dot &gt; net|

*Last changed: 29. July 2019*

</div>
