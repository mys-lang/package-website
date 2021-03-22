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
