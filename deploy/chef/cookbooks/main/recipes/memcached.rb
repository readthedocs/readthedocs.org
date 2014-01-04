package "memcached" do
    :upgrade
end

service "memcached" do
  enabled true
  running true
  supports :status => true, :restart => true
  action [:enable, :start]
end

cookbook_file "/etc/memcached.conf" do
  source "memcached.conf"
  mode 0640
  owner "root"
  group "root"
  notifies :restart, resources(:service => "memcached")
end
