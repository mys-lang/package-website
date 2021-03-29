About
=====

The Mys programming language website and package registry.

.. code-block:: text

   $ mys run
   Listening for clients on port 8000.

Run the test suite.

.. code-block:: text

   $ make test

Installation
------------

Install nginx.

/etc/nginx/conf.d/mys-lang.org.conf:

.. code-block:: text

    server {
        listen 80;
        server_name mys-lang.org;

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

Create a certificate and update nginx configuration. Redirect http to
https.

.. code-block:: text

   sudo certbot --nginx -d mys-lang.org

Run once in a while to renew the certificate.

.. code-block:: text

   sudo certbot renew

Disk quota
----------

https://www.digitalocean.com/community/tutorials/how-to-set-filesystem-quotas-on-ubuntu-18-04

.. code-block:: text

   sudo apt install quota

Add usrquota to /etc/fstab.

.. code-block:: text

   sudo nano /etc/fstab

Remount the filesystem and check that usrquota is present.

.. code-block:: text

   sudo mount -o remount /
   cat /proc/mounts | grep ' / '

Set soft and hard limits on the mys user:

.. code-block:: text

   $ sudo edquota -u mys

Report quotas:

.. code-block:: text

   $ sudo repquota -u -s -t /

Systemd service
---------------

/etc/systemd/system/mys-lang.org.service

.. code-block::

   [Unit]
   Description=Mys website
   After=network.target
   StartLimitIntervalSec=0

   [Service]
   Type=simple
   Restart=always
   RestartSec=1
   User=mys
   ExecStart=/home/mys/package-website/build/speed/app -d /home/mys/database
   WorkingDirectory=/home/mys

   [Install]
   WantedBy=multi-user.target

Enable is for start at boot.

.. code-block::

   $ sudo systemctl start mys-lang.org
   $ sudo systemctl enable mys-lang.org
