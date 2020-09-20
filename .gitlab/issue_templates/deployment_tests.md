Pyspread deployment test
========================

<date>
<version>

The tests are conducted with commit
<hash>

Test system:
 + Manjaro
 + Python <version>
 + PyQt5 <version>
 + numpy <version>
 + matplotlib <version>
 + pyenchant <version>

1. Startup
----------

```
$ cd <pyspread main directory>
$ ./bin/pyspread
```
Expected result: Pyspread main window is shown.

- [ ] Test conducted and ok

Repetition after deleting config file
```
$ rm ~/.config/pyspread/pyspread.conf
$ ./pyspread.sh
```
Expected result: Pyspread main window is shown.
- [ ] Test conducted and ok

2. File -> New
--------------
Select File -> New via menubar
Enter 1,1,1 in dialog
Expected result: Grid with 1 cell shown
- [ ] Test conducted and ok

Select File -> New via toolbar
Enter 1,1,1 in dialog
Expected result: Grid with 1 cell shown
- [ ] Test conducted and ok

Select File -> New via toolbar
Enter 0,0,0 in dialog
Expected result: No change in grid, error message
- [ ] Test conducted and ok

Select File -> New via toolbar
Enter 9999999999,0,0 in dialog
Expected result: No change in grid, error message
- [ ] Test conducted and ok

Select File -> New via toolbar
Enter 1000000,10000,10 in dialog
Expected result: Grid with correct shape shown
Rating: OK (unit test)

Select cell 999999, 9999, 9
Select File -> New via toolbar
Enter 2,2,2 in dialog
Expected result: Grid with correct shape shown
- [ ] Test conducted and ok

Select File -> New via toolbar
Enter 1000,100,3 in dialog
Expected result: Grid with correct shape shown
- [ ] Test conducted and ok

Select File -> New via toolbar
Cancel dialog
Expected result: No changes
- [ ] Test conducted and ok


2. File -> Open
---------------

Select File -> Open via menubar
Choose valid and signed file test.pysu
Expected result: File loaded and displayed correctly
- [ ] Test conducted and ok

Select File -> Open via toolbar
Choose valid and unsigned file test.pysu
Expected result: File loaded and put into safe mode
- [ ] Test conducted and ok

Select File -> Open via toolbar
Cancel dialog
Expected result: No changes
- [ ] Test conducted and ok

Select File -> Open via toolbar
Enter invalid filename
Expected result: Button is disabled
- [ ] Test conducted and ok

Select File -> Open via toolbar
Choose valid and unsigned file test.pys
Expected result: File loaded and put into safe mode
- [ ] Test conducted and ok

Select File -> Open via toolbar
Choose valid and signed file test.pys
Expected result: File loaded and displayed correctly
- [ ] Test conducted and ok

Select File -> Open via toolbar
Choose invalid and unsigned file test_invalid.pysu with shape 0,100,3
Expected result: Invalid grid is displayed in safe mode
- [ ] Test conducted and ok

Select File -> Open via toolbar
Choose invalid and unsigned file test_invalid.pysu with version 12.0 and shape 0,100,3
Expected result: Crash with ValueError indicating invalid version
- [ ] Test conducted and ok

Select File -> Open via toolbar
Choose invalid and unsigned file test_invalid.pysu with cell out of shape
Expected result: Grid is displayed in safe mode, crash on approve
- [ ] Test conducted and ok

Select File -> Open via toolbar
Choose valid and unsigned file without read permissions test_inaccessible.pysu
Expected result: Crash with PermissionError [Errno 13] Permission denied
- [ ] Test conducted and ok


3. File -> Open recent
----------------------

Select recent file test.pysu from menubar
Expected result: File is loaded correctly
- [ ] Test conducted and ok

Select recent file test.pys from menubar
Expected result: File is loaded correctly
- [ ] Test conducted and ok


4. File -> Save
---------------

Select recent file test.pys from menubar
Enter 'Test' in cell 0,0,0
Select File -> Save from menubar
Select recent file test.pys from menubar
Expected result: Change is still present, file is signed correctly and save moe is disabled
- [ ] Test conducted and ok


5. File -> Save as
------------------

Select recent file test.pysu from menubar
Select File -> Save as from menubar
Enter file test_empty.pysu and press OK
Expected result: File is created
- [ ] Test conducted and ok

Delete content and remove merges
Select File -> Save as from menubar
Enter file test_empty.pysu and press OK
Expected result: File overwriting is protected by dialog
- [ ] Test conducted and ok

Select recent file test.pysu from menubar
Select File -> Save as from menubar
Enter file test_empty.pysu in folder '/' without write permissions and press OK
Expected result: Crash with PermissionError
- [ ] Test conducted and ok


6. File -> Approve
------------------
Select File -> Open via toolbar
Choose valid and unsigned file test.pysu
Select File -> Approve via menubar
Expected result: File loaded correctly but safe mode message is still shown in macro panel.
- [ ] Test conducted and ok


7. File -> Clear globals
------------------------
Select File -> Clear globals from menubar
Expected result: Message on_nothing >  &Clear globals <src.actions.Action object at 0x7f25a1614a50>
- [ ] Test conducted and ok


8. File -> Print preview
------------------------
Select File -> Print preview from menubar
Cancel dialog
Expected result: Nothing
- [ ] Test conducted and ok

Select File -> Print preview from menubar
Press OK
Expected result: Print Preview dialog
- [ ] Test conducted and ok

Select File -> Print preview from menubar
Enter 1111, 0, 1199, 5 (outside shape 1000, 100, 3)
Press OK
Expected result: Crash, ZeroDivisionError
- [ ] Test conducted and ok

Select File -> Print preview from menubar
Enter 1, 1, 12, 5
Press OK
Expected result: Print preview dialog shows non-centered grid
- [ ] Test conducted and ok

Select File -> Print preview from menubar
Enter 3, 3, 33, 33
Press OK
Expected result: Print preview dialog shows non-centered grid
- [ ] Test conducted and ok

Select File -> Print preview from menubar
Insert png image into cell 0,0,0
Enter 0, 0, 1, 1
Press OK
Expected result: Print preview dialog shows grid
- [ ] Test conducted and ok

Select File -> Print preview from menubar
Insert png image into cell 0,0,0
Enter 0, 0, 0, 0
Press OK
Expected result: Print preview dialog shows grid cell that is larger than the page
- [ ] Test conducted and ok

Select File -> Print preview from menubar
Insert png image into cell 0,0,0
Enter 0, 0, 9999, 999
Press OK
Expected result: Long wait, Memory consumption > 3GB, test aborted by tester
- [ ] Test conducted and ok


9. File -> Print
----------------

Select File -> Print from menubar
Press OK
Expected result: Printer dialog
- [ ] Test conducted and ok


10. File -> Preferences
-----------------------

Select File -> Preferences from menubar
Press Cancel
Expected result: Nothing
- [ ] Test conducted and ok

Select File -> Preferences from menubar
Change Signature key to "" and press OK
Select File -> Preferences from menubar
Expected result: Signature key is ""
- [ ] Test conducted and ok

Select File -> Preferences from menubar
Change Signature key to empty string and press OK
Select File -> Preferences from menubar
Expected result: New signature key is visible
- [ ] Test conducted and ok

Select File -> Preferences from menubar
Change Cell calculation timeout to 10000 and press OK
Select File -> Preferences from menubar
Expected result: New Cell calculation timeout is visible
- [ ] Test conducted and ok

Select File -> Preferences from menubar
Change Frozen cell refresh period to 10000 and press OK
Select File -> Preferences from menubar
Expected result: New Frozen cell refresh period is visible
- [ ] Test conducted and ok


Select File -> Preferences from menubar
Change number of recent files to 2 and press OK
Select File -> Preferences from menubar
Expected result: Value has not changed and is still 5
- [ ] Test conducted and ok


11. File -> Quit
----------------

Open Pyspread
Select File -> Quit from menubar
Expected result: Application has closed
- [ ] Test conducted and ok

Open Pyspread
Enter 1 in cell 0,0,0
Select File -> Quit from menubar
Expected result: Dialog unsaved changes is visible
- [ ] Test conducted and ok

Open Pyspread
Enter 1 in cell 0,0,0
Select File -> Quit from menubar
Press Save in Dialog unsaved changes
Expected result: Save as dialog is shown
- [ ] Test conducted and ok

Open Pyspread
Enter 1 in cell 0,0,0
Select File -> Quit from menubar
Press Cancel in Dialog unsaved changes
Expected result: Nothing
- [ ] Test conducted and ok

Open Pyspread
Enter 1 in cell 0,0,0
Select File -> Quit from menubar
Press Save in Dialog unsaved changes
Cancel Save dialog
Expected result: Application has closed
- [ ] Test conducted and ok


12. Edit -> Undo
----------------

Enter 1 in cell 0,0,0
Enter 2 in cell 0,1,0
Format cell 0,1,0 bold
Enter 3 in cell 0,2,0
Format cell 0,2,0 bold, italics, underlined and strikethrough
Enter 'Test' in cell 0,3,0
Align and justify cell 0,3,0 centered
Select cells 0,1,0 to 2,2,0
Change line color to blue and background color to yellow
Undo all steps
Expected result: Steps undone, border line coloring is undone in 2 steps
- [ ] Test conducted and ok


13. Edit -> Redo
----------------

Enter 1 in cell 0,0,0
Enter 2 in cell 0,1,0
Format cell 0,1,0 bold
Enter 3 in cell 0,2,0
Format cell 0,2,0 bold, italics, underlined and strikethrough
Enter 'Test' in cell 0,3,0
Align and justify cell 0,3,0 centered
Select cells 0,1,0 to 2,2,0
Change line color to blue and background color to yellow
Undo all steps
Redo all steps
Expected result: Cells look like before the undo operation
- [ ] Test conducted and ok


14. Edit -> Cut
---------------

Enter 1 in cell 0,0,0
Select cell 0,0,0
Select Edit -> Cut from menubar
Select cell 1,0,0
Select Edit -> Paste from menubar
Expected result: Cell 0,0,0 is empty, cell 1,0,0 shows 1
- [ ] Test conducted and ok

Enter 1 in cell 0,0,0
Select cell 0,0,0
Press Ctrl+x
Select cell 1,0,0
Press Ctrl+v
Expected result: Cell 0,0,0 is empty, cell 1,0,0 shows 1
- [ ] Test conducted and ok

Enter 1 in cell 0,0,0
Select cell 0,0,0
Select Cut from toolbar
Select cell 1,0,0
Select Paste from toolbar
Expected result: Cell 0,0,0 is empty, cell 1,0,0 shows 1
- [ ] Test conducted and ok

Enter 1 in all cells between 0,0,0 and 3,2,0
Select cells 0,0,0 to 3,2,0
Select Edit -> Cut from menubar
Select Cell 6,0,0
Select Edit -> Paste from menubar
Expected result: Cell 0,0,0 to 3,2,0 are empty, cells in the area at 6,0,0 show 1
- [ ] Test conducted and ok


15. Edit -> Copy
----------------

Enter 1 in cell 0,0,0
Select cell 0,0,0
Select Edit -> Copy from menubar
Select cell 1,0,0
Select Edit -> Paste from menubar
Expected result: Cell 0,0,0 and cell 1,0,0 show 1
- [ ] Test conducted and ok

Enter 1 in cell 0,0,0
Select cell 0,0,0
Select Copy from toolbar
Select cell 1,0,0
Select Paste from toolbar
Expected result: Cell 0,0,0 and cell 1,0,0 show 1
- [ ] Test conducted and ok

Enter 1+1 in cell 0,0,0
Select cell 0,0,0
Select Edit -> Copy from menubar
Select cell 1,0,0
Select Edit -> Paste from menubar
Expected result: Cell 1,0,0 has the code 1+1 and shows 2
- [ ] Test conducted and ok

Enter 1+1 in cell 0,0,0
Select cell 0,0,0
Press Ctrl+c
Select cell 1,0,0
Press Ctrl+v
Expected result: Cell 1,0,0 has the code 1+1 and shows 2
- [ ] Test conducted and ok


16. Edit -> Copy results
------------------------

Enter 1+1 in cell 0,0,0
Select cell 0,0,0
Select Edit -> Copy results from menubar
Select cell 1,0,0
Press Ctrl-v
Expected result: Cell 1,0,0 has the code 2 and shows 2
- [ ] Test conducted and ok


17. Edit -> Paste
-----------------

Enter 1 in cells 0,0,0 and 1,0,0
Select cells 0,0,0 and 1,0,0
Select Edit -> Copy from menubar
Select cell 999,0,0 (grid shape is 1000,100,3)
Select Edit -> Paste from menubar
Expected result: Cell 999,0,0 shows 1
- [ ] Test conducted and ok

Enter 1 in cells 0,0,0 and 1,0,0
Select cells 0,0,0 and 1,0,0
Select Edit -> Copy from menubar
Select Table 1
Select cell 0,0,1
Select Edit -> Paste from menubar
Expected result: Cells 0,0,1 and 1,0,1 show 1
- [ ] Test conducted and ok


18. Edit -> Paste as
--------------------

Enter 1+1 in cell 0,0,0
Select cell 0,0,0
Press Ctrl-c
Select cell 1,0,0
Select Edit -> Paste as from menubar
Expected result: Cell 1,0,0 has the code 1+1 and shows 2
- [ ] Test conducted and ok

Enter 1+1 in cells 0,0,0 and 1,0,0
Select cells 0,0,0 and 1,0,0
Press Ctrl-c
Select cell 3,0,0
Select Edit -> Paste as from menubar
Expected result: Cell 3,0,0 has the code 1+1\n1+1
- [ ] Test conducted and ok

Load png image in cell 1,2,0
Select cell 1,2,0
Select Copy results from menubar
Select cell 4,2,0
Select Edit -> Paste as from menubar
Expected result: Image appears in cell 4,2,0
- [ ] Test conducted and ok

Load svg image in cell 7,1,0
Select cell 7,1,0
Select Copy results from menubar
Select cell 7,2,0
Select Edit -> Paste as from menubar
Expected result: Image appears in cell 7,2,0
- [ ] Test conducted and ok

Creat pie chart in cell 9,1,0
Select cell 9,1,0
Select Copy results from menubar
Select cell 9,2,0
Select Edit -> Paste as from menubar
Expected result: Dialog appears with choices image svg+xml and x-qt-image
- [ ] Test conducted and ok

Creat pie chart in cell 9,1,0
Select cell 9,1,0
Select Copy results from menubar
Select cell 9,2,0
Select Edit -> Paste as from menubar
Choose image svg+xml from dialog
Expected result: Crash IndexError: list index out of range (cannot reproduce)
- [ ] Test conducted and ok

Creat pie chart in cell 9,1,0
Select cell 9,1,0
Select Copy results from menubar
Select cell 9,2,0
Select Edit -> Paste as from menubar
Choose image x-qt-image from dialog
Expected result: Chart appears in cell 9,2,0
- [ ] Test conducted and ok


19. Edit -> Find
----------------
Enter 1 in cell 0,0,0
Enter 2 in cell 1,0,0
Enter 3 in cell 2,0,0
Enter 4 in cell 3,0,0
Enter 'a' in cell 0,1,0
Enter 'b' in cell 1,1,0
Enter 'c' in cell 2,1,0
Enter 'Test' in cell 3,1,0
Enter 2000+1 in cell 0,2,0

Enter 1 in Search box and press <Enter>
Expected result: Cell 0,0,0 is selected
- [ ] Test conducted and ok

Press <Enter> again
Expected result: Nothing
- [ ] Test conducted and ok

Enter 1 in Search box and press <Enter>
Expected result: Cell 1,0,0 is selected
- [ ] Test conducted and ok

Enter Te in Search box and press <Enter>
Expected result: Cell 3,1,0 is selected
- [ ] Test conducted and ok

Enter test in Search box and press <Enter>
Expected result: Cell 3,1,0 is selected
- [ ] Test conducted and ok

Select cell 1,0,0
Toggle Match case On
Enter test in Search box and press <Enter>
Expected result: Nothing
- [ ] Test conducted and ok

Toggle Match case Off
Enter 2001 in Search box and press <Enter>
Expected result: Nothing
- [ ] Test conducted and ok

Toggle Code and Results On
Enter 2001 in Search box and press <Enter>
Expected result: Cell 0,2,0 is selected
- [ ] Test conducted and ok

Toggle Code and Results Off
Select cell 5,2,0
Enter 1 in Search box and press <Enter>
Expected result: Cell 0,0,0 is selected
- [ ] Test conducted and ok

Select cell 5,2,0
Toggle Search Backwards On
Enter 1 in Search box and press <Enter>
Expected result: Cell 0,2,0 is selected
- [ ] Test conducted and ok

Toggle Search Backwards Off
Enter Te in Search box and press <Enter>
Expected result: Cell 3,1,0 is selected
- [ ] Test conducted and ok

Toggle Whole Words On
Select cell 0,0,0
Enter Te in Search box and press <Enter>
Expected result: Nothing
- [ ] Test conducted and ok

Toggle Whole Words On
Select cell 0,0,0
Enter Test in Search box and press <Enter>
Expected result: Cell 3,1,0 is selected
- [ ] Test conducted and ok

Toggle Whole Words Off
Toggle Regular expression On
Select cell 10,0,0
Enter .*[1-3] in Search box and press <Enter>
Expected result: Cell 2,1,0 is selected
- [ ] Test conducted and ok

Enter .*[1-3] in Search box and press <Enter>
Expected result: Cell 0,0,0 is selected
- [ ] Test conducted and ok

Enter .*[1-3] in Search box and press <Enter>
Expected result: Cell 1,0,0 is selected
- [ ] Test conducted and ok

Enter .*[1-3] in Search box and press <Enter>
Expected result: Cell 1,0,0 is selected
- [ ] Test conducted and ok


20. Edit -> Replace
-------------------

Enter 'Test' in cell 0,0,0
Enter 1 in cell 1,0,0
Enter 1 in cell 2,0,0
Open Replace Dialog
Search for Te and Replace with Tee
Expected result: 'Teest' in cell 0,0,0
- [ ] Test conducted and ok

Search for Tee and Replace with Te
Expected result: 'Test' in cell 0,0,0
- [ ] Test conducted and ok

Select cell 0,0,0
Search for 1 and Replace all with 222
Expected result: 222 in cell 1,0,0
- [ ] Test conducted and ok


21. Edit -> Quote
-----------------
Enter Test in cell 0,0,0
Select cell 0,0,0
Press <Ctrl>+<Enter>
Result 'Test' in cell 0,0,0
- [ ] Test conducted and ok

Type Test in 0,0,0 and press <Ctrl> + <Enter>
Expected result: Code in cell is deleted
Ratung: [ ]


22. Edit -> Insert rows
-----------------------

Enter 1 in cell 1,0,0
Enter 2 in cell 2,0,0
Select row 2
Select Insert rows
Expected result: 2 is in cell 3,0,0
- [ ] Test conducted and ok

Select rows 2 and 3
Select Insert rows
Expected result: 2 is in cell 5,0,0
- [ ] Test conducted and ok

23. Edit -> Insert columns
--------------------------

Enter 1 in cell 1,0,0
Enter 2 in cell 1,1,0
Select column 1
Select Insert columns
Expected result: 2 is in cell 1,2,0
- [ ] Test conducted and ok

Select columns 1 and 2
Select Insert columns
Expected result: 2 is in cell 1,4,0
- [ ] Test conducted and ok


24. Edit -> Insert table
------------------------

Enter 0 in cell 0,0,0
Enter 1 in cell 0,0,1
Select Table 1
Select Insert table
Expected result: 1 is in cell 0,0,2
- [ ] Test conducted and ok

25. Edit -> Delete rows
-----------------------

Enter 1 in cell 1,0,0
Enter 2 in cell 3,0,0
Select row 1
Select Delete rows
Expected result: Crash, IndexError: Grid index (1, 100, 0) outside grid shape (1000, 100, 3).
- [ ] Test conducted and ok


26. Edit -> Delete columns
--------------------------

Enter 1 in cell 0,0,0
Enter 2 in cell 0,2,0
Select column 1
Select Delete columns
Expected result: Crash, IndexError: Grid index (1000, 1, 0) outside grid shape (1000, 100, 3)
- [ ] Test conducted and ok


27. Edit -> Delete table
------------------------

Enter 0 in cell 0,0,0
Enter 1 in cell 0,0,2
Select Table 1
Select Delete table
Expected result: 1 is in cell 0,0,1
- [ ] Test conducted and ok


28. Edit -> Resize grid
-----------------------

Select Edit -> Resize grid
Enter shape 5,5,1 and press ok
Expected result: Grid with shape 5,5,1
- [ ] Test conducted and ok

Select Edit -> Resize grid
Enter shape 0,0,0 and press ok
Expected result: Nothing
- [ ] Test conducted and ok


29. View -> Fullscreen
----------------------

Select View -> Fullscreen
Expected result: Application is in fullscreen mode
- [ ] Test conducted and ok

Select View -> Fullscreen
Expected result: Application is in normal mode again
- [ ] Test conducted and ok


30. View -> Toolbars
--------------------

Toggle each toolbar on and off via the View -> Toolbars menu
Expected result: Each toolbar disappears and reappears as requested
- [ ] Test conducted and ok


31. View -> Entry line
----------------------

Toggle entry line on and off via View -> Entry line
Expected result: The entry line disappears and reappears as requested
- [ ] Test conducted and ok


32. View -> Macro panel
-----------------------

Toggle macro panel on and off via View -> Macro panel
Expected result: The macro panel disappears and reappears as requested
- [ ] Test conducted and ok


33. View -> Go to cell
----------------------

Select cell 0,0,0
Select View -> Go to cell
Enter 0,0,0 in dialog
Expected result: Nothing
- [ ] Test conducted and ok

Select View -> Go to cell
Enter nothing in dialog
Expected result: Nothing
- [ ] Test conducted and ok

Select View -> Go to cell
Enter 1,0,0 in dialog
Expected result: Cell 1,0,0 is selected
- [ ] Test conducted and ok

Select View -> Go to cell
Enter 999,99,9 in dialog
Expected result: Cell 999,99,0 is selected
- [ ] Test conducted and ok

Select View -> Go to cell
Enter 999,99,1 in dialog
Expected result: Cell 999,99,1 is selected
- [ ] Test conducted and ok


34. View -> Toggle spell checker
--------------------------------

Select cell 0,0,0
Enter Tes
Select View -> Toggle spell checker
Expected result: Nothing
Rating: Bug, minor inconvenience, immediate enabling of the spell checker would be better

Select cell 0,0,0
Enter Tes
Select cell 1,0,0
Select View -> Toggle spell checker
Select cell 0,0,0
Expected result: Tes is marked as unknown word
- [ ] Test conducted and ok


35. View -> Zoom in
-------------------

Select View -> Zoom in
Expected result: Grid is zoomed in
Rating: OK


36. View -> Zoom out
--------------------

Select View -> Zoom out
Expected result: Grid is zoomed out
- [ ] Test conducted and ok


37. View -> Original size
-------------------------

Select View -> Original size
Expected result: Grid is zoomed to original size
- [ ] Test conducted and ok


38. View -> Refresh selected cells
----------------------------------

Enter i=0 in Macro editor
Enter i=i+1 in cell 0,0,0
Freeze cell 0,0,0
Select View -> Refresh multiple times
Results: Before Freezing, cell result is 1 after refreshing, it counts up
- [ ] Test conducted and ok


39. View -> Toggle periodic updates
-----------------------------------

Enter i=0 in Macro editor
Enter i=i+1 in cell 0,0,0
Freeze cell 0,0,0
Select View -> Toggle periodic updates
Results: Cell result counts up once a second (dependent on preference setting)
- [ ] Test conducted and ok


40. View -> Show frozen
-----------------------

Freeze cell 0,0,0
Select View -> Show frozen
Select View -> Show frozen
Results: Cell 0,0,0 shows blue diagonal pattern between When show frozen in toggled on.
- [ ] Test conducted and ok


41. Format -> Copy format
-------------------------

see (42)

42. Format -> Paste format
--------------------------

Enter 1 in cell 1,2,0
Enter 2 in cell 2,2,0
Enter 3 in cell 1,3,0
Enter 4 in cell 2,3,0
Select cells 1,2,0 and 2,2,0
Format Bold
Select cells 1,3,0 and 2,3,0
Format Italics
Copy cell code of the 4 cells
Select cell 5,2,0
Paste clipboard
Select cells 1,2,0, 2,2,0, 1,3,0 and 2,3,0
Copy format
Select cell 5,2,0
Paste format
Expected result: Bold format is shown for cells 5,2,0 6,2,0 italics for  5,3,0, 6,3,0
- [ ] Test conducted and ok


43. Format -> Font
------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Font
Select Arial font, bold, 22 in dialog and press ok
Expected result: The text in cell 0,0,0 is rendered accordingly.
- [ ] Test conducted and ok

44. Format -> Bold
------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Bold
Expected result: The text in cell 0,0,0 is rendered accordingly.
- [ ] Test conducted and ok


45. Format -> Italics
---------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Italics
Expected result: The text in cell 0,0,0 is rendered accordingly.
- [ ] Test conducted and ok


46. Format -> Underline
-----------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Underline
Expected result: The text in cell 0,0,0 is rendered accordingly.
- [ ] Test conducted and ok


47. Format -> Strikethrough
---------------------------

Enter 'Hello World' in cell 0,0,0
Select Format -> Strikethrough
Expected result: The text in cell 0,0,0 is rendered accordingly.
- [ ] Test conducted and ok


48. Format -> Cell renderer
---------------------------

Enter numpy.diag([255]*100) in cell 0,0,0
Select Format -> Cell renderer ->  Image cell renderer
Expected result: Black image with diagonal white line
- [ ] Test conducted and ok


Enter '<b>Test</b>' in cell 0,0,0
Select Format -> Cell renderer -> Markup cell renderer
Expected result: Test is printed bold
- [ ] Test conducted and ok

Select Format -> Cell renderer -> Chart cell renderer
Result nothing but message
- [ ] Test conducted and ok


49. Format -> Freeze cell
-------------------------

Select Cell 0,0,0
Select Format -> Freeze cell
Enter 1 in cell 0,0,0
Results: Nothing
- [ ] Test conducted and ok


50. Format -> Lock cell
-----------------------

Select Cell 0,0,0
Enter 1 in cell 0,0,0
Select Format -> Lock cell
Try editing cell 0,0,0
Expected result: Cell is not selected, editor does not appear.
- [ ] Test conducted and ok

Select Cell 0,0,0
Enter 1 in cell 0,0,0
Select Format -> Lock cell
Select Cell 0,0,0
press <Del>
Expected result: Cell content is Deleted
- [ ] Test conducted and ok


51. Format -> Merge cells
-------------------------

Select cells 0,0,0 to 4,1,0
Select Format -> Merge cells
Expected result: Cells are merged
- [ ] Test conducted and ok

Select cell 0,0,0
Select Format -> Merge cells
Expected result: Cells are unmerged
- [ ] Test conducted and ok


52. Format -> Rotation
----------------------

Enter 'Test' in cell 0,0,0
Select each of the 4 rotation types
Expected result: Cells are rotated as expected
- [ ] Test conducted and ok


53. Format -> Justification
---------------------------

Enter 'Test' in cell 0,0,0
Select each of the 4 justification types
Expected result: Cells are justified as expected
- [ ] Test conducted and ok


54. Format -> Alignment
-----------------------

Enter 'Test' in cell 0,0,0
Select each of the 4 alignment types
Expected result: Cells are aligned as expected
- [ ] Test conducted and ok


55. Format -> Formatted borders
-------------------------------

Select cell 1,1,0
Select Format -> Formatted borders -> Top border
Select Format -> Border width -> 8
Expected result: Top border is fat
- [ ] Test conducted and ok

Select cell 1,1,0
Select Format -> Formatted borders -> Bottom border
Select Format -> Border width -> 8
Expected result: Bottom border is fat
- [ ] Test conducted and ok

Select cell 1,1,0
Select Format -> Formatted borders -> Left border
Select Format -> Border width -> 8
Expected result: Left border is fat
- [ ] Test conducted and ok

Select cell 1,1,0
Select Format -> Formatted borders -> Right border
Select Format -> Border width -> 8
Expected result: Right border is fat
- [ ] Test conducted and ok

Select cells 3,1,0 to 5,2,0
Select Format -> Formatted borders -> Outer border
Select Format -> Border width -> 8
Expected result: Outer borders are fat
- [ ] Test conducted and ok

Select Format -> Border width -> 1
Select cells 3,1,0 to 5,2,0
Select Format -> Formatted borders -> Inner border
Select Format -> Border width -> 8
Expected result: Inner borders are fat
- [ ] Test conducted and ok

Select Format -> Border width -> 1
Select cells 3,1,0 to 5,2,0
Select Format -> Formatted borders -> Top and bottom borders
Select Format -> Border width -> 8
Expected result: Top and bottom borders are fat
- [ ] Test conducted and ok


56. Format -> Border width
--------------------------

Select cell 0,0,0
Select Format -> Border width 0
Expected result: Border width is a pixel line
- [ ] Test conducted and ok

Select cell 1,1,0
Select Format -> Border width 1
Expected result: Border width is light line
- [ ] Test conducted and ok

Select cell 1,1,0
Select Format -> Border width 64
Expected result: Border width is a huge line
- [ ] Test conducted and ok


57. Format -> Text color
------------------------

Enter 'Test' in cell 0,0,0
Select cell 0,0,0
Select Format -> Text color
Choose red color in dialog and press ok
Expected result: Text is red
- [ ] Test conducted and ok


58. Format -> Line color
------------------------

Select cell 0,0,0
Select Format -> Line color
Choose blue color in dialog and press ok
Expected result: Cell border line is blue
- [ ] Test conducted and ok


59. Format -> Background color
------------------------------

Select cell 0,0,0
Select Format -> Background color
Choose yellow color in dialog and press ok
Expected result: Cell background is yellow
- [ ] Test conducted and ok


60. Macro -> Insert image
-------------------------

Select cell 1,1,0
Select Macro -> Insert image
Choose png image and press OK
Expected result: Cell renderer is set to image and image appears
- [ ] Test conducted and ok

Select cell 1,1,0
Select Macro -> Insert image
Choose svg image and press OK
Expected result: Cell renderer is set to image and image appears
- [ ] Test conducted and ok


61. Macro -> Link image
-----------------------

Select cell 1,1,0
Select Macro -> Link image
Expected result: Error message on_nothing >  Link image... <src.actions.Action object at 0x7f76a0e8f690>
- [ ] Test conducted and ok


62. Macro -> Insert chart
-------------------------

Select cell 1,1,0
Select Macro -> Insert chart
Choose Pie chart in chart dialog and press ok
Expected result: Chart renderer is activated and pie chart is displayed.
- [ ] Test conducted and ok


63. Help -> First steps
-----------------------
Select Help -> First steps from menubar
Expected result: Message on_nothing >  First steps... <src.actions.Action object at 0x7f78e1644550>
- [ ] Test conducted and ok

64. Help -> Tutorial
--------------------
Select Help -> Tutorial from menubar
Expected result: Message on_nothing >  Tutorial... <src.actions.Action object at 0x7f78e16445f0>
- [ ] Test conducted and ok


65. Help -> FAQ
---------------
Select Help -> FAQ from menubar
Expected result: Message on_nothing >  FAQ... <src.actions.Action object at 0x7f78e1644730>
- [ ] Test conducted and ok

66. Help -> Dependencies
------------------------

Select Help -> Dependencies from menubar
Expected result: Dependencies is displayed correctly
- [ ] Test conducted and ok

67. Help -> About pyspread
--------------------------

Select Help -> About from menubar
Expected result: About dialog is displayed correctly
- [ ] Test conducted and ok