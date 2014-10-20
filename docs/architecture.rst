Architecture
============

Read the Docs is architected to be highly available. A lot of projects host their documentation with us, so we have built the site so that it shouldn't go down. The load balancer is the only real single point of failure currently. This means mainly that if the network to the load balancer goes down, we have issues.

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
              |                                                            |
              |                                                            |
              |                     +------------------+                   |
              |                     |                  |                   |
              +---------------------|  Build Server    |-------------------+
                                    |                  |              
                                    +------------------+       
                                                               
                                                               
                                                               
                                                               





