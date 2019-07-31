---
layout: default
menu: docs
---

<div markdown="1" class="w3-container">
<div markdown="1" class="w3-col l2 m2 s12">
# FAQ
</div>
<div markdown="1" class="w3-col l6 m6 s12">
## What kind of expressions can a cell contain?
A cell can contain any normal Python expression such as a list
comprehension or a generator expression. However, it cannot
contain statements such as
```Python 
for i in xrange(10): pass
```
If you want to program more complex algorithms then use the macro editor.
There, you can define functions that use arbitrary Python code and is callable
from any cell.

(Note: This is going to change in pyspread 2.0+)

**Example**

Type in the macro editor:

```Python
def factorize(number): 
    """Silly factorizing algorithm for demonstration purposes only"""
    counter = 1
    result = []
    while counter &lt;= number:
        if number % counter == 0:
            result.append(counter)
        counter += 1
    return result
```
And in the cell:
```Python
factorize(25)
```

The result is:
```Python
[1 5 25]
```

## What are the boundaries for the number of rows, columns and tables?

These are limited by your memory (and maybe your stack restriction if any).
However, the grid is restricted to a number that changes with row size.
For standard size on GTK platforms, 80 000 000 rows can be displayed.

*Last changed: 29. July 2019*
</div>
</div>
