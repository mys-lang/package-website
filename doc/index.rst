|discord|_
|test|_
|stars|_

About
=====

The Mys programming language website and package registry implemented
in the `Mys programming language`_.

Project: https://github.com/mys-lang/package-website

Testing
=======

Run the test suite.

.. code-block:: text

   make test

Run locally
===========

Start an webserver locally. Run ``mys run -- --help`` for options.

.. code-block:: myscon

   ❯ mys run
    ✔ Reading package configuration (0 seconds)
    ✔ Getting compiler flags openssl (0.01 seconds)
    ✔ Getting linker flags for openssl (0 seconds)
    ✔ Getting compiler flags sqlite3 (0 seconds)
    ✔ Getting linker flags for sqlite3 (0.01 seconds)
    ✔ Building (5.62 seconds)
   Number of packages: 0
   Listening for clients on port 8000.

Installation
============

Nginx terminates SSL/TLS.

/etc/nginx/conf.d/mys-lang.org.conf:

.. code-block:: nginx

    server {
        listen 80;
        server_name mys-lang.org;
        gzip on;
        gzip_types image/svg+xml application/javascript text/css text/html;

        location ^~ /.well-known/acme-challenge/ {
            root /var/www/mys-lang.org;
        }

        location / {
            proxy_pass          http://localhost:8000/;
            proxy_http_version  1.1;
            proxy_set_header    X-Forwarded-For  $proxy_add_x_forwarded_for;
        }
    }

Install certbot.

https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/

Create a certificate and automatically updates nginx
configuration. Enable redirect of http to https.

.. code-block:: text

   sudo certbot --nginx -d mys-lang.org

Run once in a while to renew the certificate.

.. code-block:: text

   sudo certbot renew

ZFS storage with compression and deduplication
----------------------------------------------

There are lots of identical files in releases. Dedup saves disk
space. So does compression with LZ4. Not sure about the combination of
the two.

.. code-block:: text

   $ sudo dd if=/dev/zero of=/home/mys/database.img bs=4096 count=262144
   $ sudo zpool create mys-website /home/mys/database.img
   $ sudo zpool set autoexpand=on mys-website
   $ sudo zfs create mys-website/database
   $ sudo zfs set compression=lz4 mys-website/database
   $ sudo zfs set dedup=on mys-website/database
   $ sudo zfs set mountpoint=/home/mys/database mys-website/database
   $ zpool list
   NAME          SIZE  ALLOC   FREE  CKPOINT  EXPANDSZ   FRAG    CAP  DEDUP    HEALTH  ALTROOT
   mys-website   960M  15.1M   945M        -         -     0%     1%  79.76x    ONLINE  -

Systemd service
---------------

/etc/systemd/system/mys-lang.org.service

.. code-block:: ini

   [Unit]
   Description=Mys website
   After=network.target
   StartLimitIntervalSec=0

   [Service]
   Type=simple
   Restart=always
   RestartSec=1
   User=mys
   ExecStart=/home/mys/package-website/build/speed/app -d /home/mys/database [-i <ipinfo-token>]
   WorkingDirectory=/home/mys

   [Install]
   WantedBy=multi-user.target

Enable it for automatic start at boot.

.. code-block:: text

   sudo systemctl enable mys-lang.org

Start it.

.. code-block:: text

   sudo systemctl start mys-lang.org

.. |discord| image:: https://img.shields.io/discord/777073391320170507?label=Discord&logo=discord&logoColor=white
.. _discord: https://discord.gg/GFDN7JvWKS

.. |test| image:: https://github.com/mys-lang/package-website/actions/workflows/pythonpackage.yml/badge.svg
.. _test: https://github.com/mys-lang/package-website/actions/workflows/pythonpackage.yml

.. |stars| image:: https://img.shields.io/github/stars/mys-lang/package-website?style=social
.. _stars: https://github.com/mys-lang/package-website

.. _Mys programming language: https://mys-lang.org
