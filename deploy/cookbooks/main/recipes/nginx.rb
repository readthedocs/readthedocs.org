script "Install Nginx" do
  interpreter "bash"
  code <<-EOH
    nginx=stable # use nginx=development for latest development version
    echo "deb http://ppa.launchpad.net/nginx/$nginx/ubuntu $(lsb_release -cs) main" > /etc/apt/sources.list.d/nginx-$nginx-$(lsb_release -cs).list
    apt-key adv --keyserver keyserver.ubuntu.com --recv-keys C300EE8C
    apt-get update
    apt-get install nginx
  EOH
  not_if "nginx -V |grep 0.8"
end

service "nginx" do
  enabled true
  running true
  supports :status => true, :restart => true, :reload => true
  action [:start, :enable]
end

file "/etc/nginx/sites-enabled/default" do
    action :delete
end

template "/etc/nginx/sites-enabled/readthedocs" do
  source "readthedocs"
  mode 0640
  owner "root"
  group "root"
  notifies :restart, resources(:service => "nginx")
end

cookbook_file "/etc/nginx/nginx.conf" do
  source "nginx.conf"
  mode 0640
  owner "root"
  group "root"
  notifies :restart, resources(:service => "nginx")

end
