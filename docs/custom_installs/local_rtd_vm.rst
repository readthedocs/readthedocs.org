Local VM Install
================

Assumptions and Prerequisites
-----------------------------

* Debian VM provisioned with python 2.7.x
* All python dependencies and setup tools are installed ::

  $ sudo apt-get install python-setuptools
  $ sudo apt-get install build-essential
  $ sudo apt-get install python-dev
  $ sudo apt-get install libevent-dev
  $ sudo easy_install pip 

* Git ::

  $ sudo apt-get install git
  
* Git repo is ``git.corp.company.com:git/docs/documentation.git``
* Source documents are in ``../docs/source``
* Sphinx ::

  $ sudo pip install sphinx

.. note:: Not using sudo may prevent access. “error: could not create '/usr/local/lib/python2.7/dist-packages/markupsafe': Permission denied” 

Local RTD Setup
---------------

1. Install RTD.
~~~~~~~~~~~~~~~

To host your documentation on a local RTD installation, set it up in your VM. ::

    $ mkdir checkouts
    $ cd checkouts
    $ git clone https://github.com/rtfd/readthedocs.org.git
    $ cd readthedocs.org
    $ sudo pip install -r requirements.txt
    
Possible Error and Resolution
`````````````````````````````

**Error**: ``error: command 'gcc' failed with exit status 1``

**Resolution**: Run the following commands. ::

    $ sudo apt-get update
    $ sudo apt-get install python2.7-dev tk8.5 tcl8.5 tk8.5-dev tcl8.5-dev libxml2-devel libxslt-devel
    $ sudo apt-get build-dep python-imaging --fix-missing 

On Debian 8 (jessie) the command is slightly different ::

    $ sudo apt-get update
    $ sudo apt-get install python2.7-dev tk8.5 tcl8.5 tk8.5-dev tcl8.5-dev libxml2-dev libxslt-dev
    $ sudo apt-get build-dep python-imaging --fix-missing 

Also don't forget to re-run the dependency installation ::

    $ sudo pip install -r requirements.txt

2. Configure the RTD Server and Superuser.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Run the following commands. ::

    $ ./manage.py migrate
    $ ./manage.py createsuperuser

2. This will prompt you to create a superuser account for Django. Enter appropriate details. For example: ::

    Username: monami.b
    Email address: monami.b@email.com
    Password: pa$$word

3. RTD Server Administration.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Navigate to the ``../checkouts/readthedocs.org`` folder in your VM and run the following command. ::

    $ ./manage.py runserver [VM IP ADDRESS]:8000
    $ curl -i http://[VM IP ADDRESS]:8000

You should now be able to log into the admin interface from any PC in your LAN at ``http://[VM IP ADDRESS]:8000/admin`` using the superuser account created in django.

Go to the dashboard at  ``http://[VM IP ADDRESS]:8000/dashboard`` and follow these steps:

1. Point the repository to your corporate Git project where the documentation source is checked in. Example:
git.corp.company.com:/git/docs/documentation.git

2. Clone the documentation sources from Git in the VM.
3. Navigate to the root path for documentation.
4. Run the following Sphinx commands. ::

    $ make html

This generates the HTML documentation site using the default Sphinx theme. Verify the output in your local documentation folder under ``../build/html``

Possible Error and Resolution
`````````````````````````````

**Error**: Couldn't access Git Corp from VM.

**Resolution**: The primary access may be set from your base PC/laptop. You will need to configure your RSA keys in the VM.

**Workaround-1**

1. In your machine, navigate to the ``.ssh`` folder. ::

    $ cd .ssh/ 
    $ cat id_rsa 

2. Copy the entire Private Key.
3. Now, SSH to the VM.
4. Open the ``id_rsa`` file in the VM. ::

    $ vim /home/<username>/.ssh/id_rsa

5. Paste the RSA key copied from your machine and save file (``Esc``. ``:wq!``).

**Workaround 2** 

SSH to the VM using the ``-A`` directive. ::

    $ ssh document-vm -A 
    
This provides all permissions for that particular remote session, which are revoked when you logout.

4. Build Documentation on Local RTD Instance.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Log into ``http://[VM IP ADDRESS]:[PORT]`` using the django superuser creds and follow these steps.	

For a new project
`````````````````

1. Select **<username> > Add Project** from the user menu.
2. Click **Manually Import Project**.
3. Provide the following information in the **Project Details** page:

    * **Name**: Appropriate name for the documentation project. For example – API Docs Project
    * **Repository URL**: URL to the documentation project. For example - git.corp.company.com:/git/docs/documentation.git
    * **Repository Type**: Git

4. Select the **Edit advanced project options** checkbox.
5. Click **Next**.

For an existing project
```````````````````````

1. Select **<username> > Projects** from the user menu.
2. Select the relevant project from the **Projects** list.
3. Select latest from the **Build a version** dropdown.
4. Click **Build**. This will take you to the Builds tab where the progress status is displayed. This may take some time.

Tips
----

* If the installation doesn't work on VM using your login/LDAP credentials, try running the operations as root (su).
