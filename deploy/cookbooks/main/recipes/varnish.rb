package "varnish" do
    :upgrade
end

cookbook_file "/etc/init/varnishlog.conf" do
    source "varnishlog.conf"
    owner "root"
    group "root"
    mode 0644
end

cookbook_file "/etc/init/readthedocs-varnish.conf" do
    source "varnish.conf"
    owner "root"
    group "root"
    mode 0644
end

cookbook_file "/etc/varnish/readthedocs.vcl" do
  source "readthedocs.vcl"
  mode 0640
  owner "root"
  group "root"
end

service "readthedocs-varnish" do
  provider Chef::Provider::Service::Upstart
  enabled true
  running true
  supports :status => true, :restart => true, :reload => true
  action [:start, :enable]
end

service "varnishlog" do
  provider Chef::Provider::Service::Upstart
  enabled true
  running true
  supports :status => true, :restart => true, :reload => true
  action [:start, :enable]
end
