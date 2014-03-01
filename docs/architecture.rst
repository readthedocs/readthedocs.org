Architecture
============

Read the Docs is architected to be highly available. A lot of projects host their documentation with us, so we have built the site so that it shouldn't go down. Varnish is the only real single point of failure currently, but we have plans to eliminate that as well.

Diagram
-------
::

                                      +-----------+
                                      |           |
                                +-----|  Nginx    |------+
                                |     +-----------+      |
                                |                        |
                           +---------+              +---------+                                  
       +-------------+     |         |              |         |    +--------------+              
       |             |-----| Nginx   |              | Nginx   |----|              |              
       |  File       |     +---------+              +---------+    |  File        |              
       |  System     |          |                        |         |  System      |              
       +-------------+     +---------+  +--------+  +---------+    +--------------+              
              |  |         |         |  |        |  |         |        |   |                     
              |  +---------|Gunicorn |--|Postgres|--|Gunicorn |--------+   |                     
              |            +---------+  +--------+  +---------+            |                     
              |                             |                              |
              |                             |                              |
              |                     +------------------+                   |
              |                     |                  |                   |
              +---------------------|  Build Server    |-------------------+
                                    |                  |              
                                    +------------------+       
                                                               
                                                               
                                                               
                                                               





