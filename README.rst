****************************************
taileff: tail -f for humans
****************************************

.. image:: taileff_showcase.gif

taileff makes it easier to read the output of tail -f, using features such as:

* syntax highlighting
* line numbering
* separating lines
* grouping separators
* indentation (only for SQL atm)


Installation
------------

.. code-block:: bash

    $ pip install taileff

Usage
-----

.. code-block:: bash

    $ tailf <file> [-s -i -n -l <language> -g <seconds>]
    $ tailf --help


Licence
-------

BSD
