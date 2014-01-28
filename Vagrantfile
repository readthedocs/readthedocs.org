Vagrant.configure(2) do |config|
  config.vm.box = "raring64"
  config.vm.box_url = "http://cloud-images.ubuntu.com/vagrant/raring/current/raring-server-cloudimg-amd64-vagrant-disk1.box"

  config.vm.provider "virtualbox" do |vm|
    vm.memory = 1024
    vm.customize ["modifyvm", :id, "--natdnshostresolver1", "on"]
  end
  config.vm.network "forwarded_port", guest: 8000, host: 8000
  config.vm.network "forwarded_port", guest: 9999, host: 9999

  config.vm.synced_folder "deploy/salt/", "/srv/salt/"

  config.vm.provision :salt do |salt|
    salt.minion_config = "deploy/salt/minion"
    salt.run_highstate = true
    salt.verbose = true
    salt.install_type = "git"
    salt.install_args = "develop"
  end
end
