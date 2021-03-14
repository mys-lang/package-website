Website
=======

The Mys programming language website and package registry.

.. code-block:: text

   $ mys run
   Listening for clients on port 8000.

Brainstorming
-------------

HTTP GET and POST to download and upload package archives.

.. code-block:: text

   -- {root}
      +-- website.sqlite
      +-- package/
          +-- os-0.3.0.tar.gz
          +-- os-0.4.0.tar.gz
          +-- random-1.4.0.tar.gz
          +-- sqlite-0.10.0.tar.gz

Various pages
-------------

GET /
GET /package/{name}

Upload and download
-------------------

GET /package/{name}-{version}.tar.gz
POST /package/{name}-{version}.tar.gz

mys run
