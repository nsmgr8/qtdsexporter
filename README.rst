QtDSExporter
============

This is a desktop DSE data exporter software. It collects current share prices
from the `Dhaka Stock Exchange`_ website.

.. _Dhaka Stock Exchange: http://www.dsebd.org/latest_share_price_all.php

Disclaimer
----------

The software totally depends on the data availability of the above mentioned
website. The author has no affiliation with DSE. He has no access to the actual
database. This is just a scrapper of the DSE website. Therefore author does not
guarantee the data accuracy or hold any responsibility for damages that may
occur using this data.

Installation
============

The software requires `PyQt`_, `SQLAlchemy`_, `Elixir`_, `SQLite`_,
`Matplotlib`_ to be installed. Following is a quick installation for
Ubuntu/Debian Linux:

Requirements::

    sudo apt-get install python-qt4 python-elixir python-matplotlib

Now, download the `source code`_, unzip it in a folder and run.

Install::

    wget http://github.com/nsmgr8/qtdsexporter/zipball/master
    unzip nsmgr8-qtdsexporter-*.zip
    cd nsmgr8-qtdsexporter-*
    ./main.py


* Note that, * should be replaced by some random characters that you get from
  github.

Enjoy the software. Feel free to contact the developer about bug report and
feature request. Please use the `Issues`_ page in the `github`_ site.

Thanks!

.. _PyQt: http://www.riverbankcomputing.co.uk/software/pyqt/intro
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _Elixir: http://elixir.ematia.de/trac/wiki
.. _SQLite: http://www.sqlite.org/
.. _Matplotlib: http://matplotlib.sourceforge.net/
.. _source code: http://github.com/nsmgr8/qtdsexporter/zipball/master
.. _Issues: http://github.com/nsmgr8/qtdsexporter/issues
.. _github: http://github.com

