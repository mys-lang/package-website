About
=====

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
        }
    }

Install certbot.

https://www.nginx.com/blog/using-free-ssltls-certificates-from-lets-encrypt-with-nginx/

sudo certbot --nginx -d mys-lang.org

Redirect http to https.

sudo certbot renew

Disk quota
----------

https://www.digitalocean.com/community/tutorials/how-to-set-filesystem-quotas-on-ubuntu-18-04

sudo apt update
sudo apt install quota

Add usrquota to /etc/fstab.

sudo nano /etc/fstab

sudo mount -o remount /

cat /proc/mounts | grep ' / '

sudo quotacheck -ugm /

Set soft and hard limits:

sudo edquota -u sammy

Report quotas:

sudo repquota -s /
