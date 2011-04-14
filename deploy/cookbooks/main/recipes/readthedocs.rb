cookbook_file "/home/docs/.bash_profile" do
    source "bash_profile"
    owner "docs"
    group "docs"
    mode 0755
end

directory "/home/docs/.ssh" do
    owner "docs"
    group "docs"
    mode 0700
end

#This is currently broken :(
if node.attribute?('private_key')
    file = File.open(node[:private_key], "rb")
    file_contents = file.read
    file "/home/docs/.ssh/id_rsa" do
        owner "docs"
        group "docs"
        mode 0600
        content file_contents
    end
end

directory "/home/docs/sites/" do
    owner "docs"
    group "docs"
    mode 0775
end

virtualenv "/home/docs/sites/readthedocs.org" do
    owner "docs"
    group "docs"
    mode 0775
end

directory "/home/docs/sites/readthedocs.org/run" do
    owner "docs"
    group "docs"
    mode 0775
end

directory "/home/docs/sites/readthedocs.org/checkouts" do
    owner "docs"
    group "docs"
    mode 0775
end

git "/home/docs/sites/readthedocs.org/checkouts/readthedocs.org" do
  repository "git://github.com/rtfd/readthedocs.org.git"
  reference "HEAD"
  user "docs"
  group "docs"
  action :sync
end

execute "This next part installs all the requirements. It will take a while." do
    command "echo 'wee'"
end

script "Install Requirements" do
  interpreter "bash"
  user "docs"
  group "docs"
  code <<-EOH
  /home/docs/sites/readthedocs.org/bin/pip install -r /home/docs/sites/readthedocs.org/checkouts/readthedocs.org/deploy_requirements.txt
  touch /tmp/pip_ran
  EOH
  creates "/tmp/pip_ran"
end
