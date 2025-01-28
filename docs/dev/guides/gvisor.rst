gVisor installation
===================

You can mostly get by just following installation instructions in the `gVisor
Docker Quick Start`_ guide.

There are a few caveats to installation, which likely depend on your local
environment. For ``systemd`` based OS, you do need to configure the Docker
daemon to avoid systemd cgroups.

.. tabs::

    .. tab:: Arch

        Follow the installation and quick start directions like normal:

        .. code:: console

            % yay -S gvisor-bin
            ...
            % sudo runsc install

        You do need to instruct Docker to avoid systemd cgroups. You will need
        to make further changes to ``/etc/docker/daemon.json`` and restart the
        Docker service:

        .. code:: json

            {
                "runtimes": {
                    "runsc": {
                        "path": "/usr/bin/runsc"
                    }
                },
                "exec-opts": ["native.cgroupdriver=cgroupfs"]
            }

    .. tab:: Fedora

       - Install docker from their repositories,
         the one included in Fedora doesn't work,
         using their `convenience script`_ is an easy way to do it.
       - `Install gvisor manually`_, the one included in Fedora doesn't work.
       - Enable cgroups v1:

         .. code:: console

            % sudo grubby --update-kernel=ALL --args="systemd.unified_cgroup_hierarchy=0"

       .. _convenience script: https://docs.docker.com/engine/install/fedora/#install-using-the-convenience-script
       .. _Install gvisor manually: https://gvisor.dev/docs/user_guide/install/#install-latest

Docker is correctly configured when you can run this command from the quick
start guide:

.. code:: console

    % docker run --rm -ti --runtime=runsc readthedocs/build dmesg
    [    0.000000] Starting gVisor...
    ...

.. _gVisor Docker Quick Start: https://gvisor.dev/docs/user_guide/quick_start/docker/

Testing gVisor
--------------

You can enable the gVisor feature flag on a project and you should see the
container created with ``runtime=runsc`` now.
