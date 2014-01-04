package "munin-node" do
    :upgrade
end

service "munin-node" do
  enabled true
  running true
  supports :status => true, :restart => true, :reload => true
  action [:enable, :start]
end

if node.attribute?("munin_servers")
  template "/etc/munin/munin-node.conf" do
    source "munin-node.conf"
    mode 0640
    owner "root"
    group "root"
    variables :munin_servers => node[:munin_servers] || []
    notifies :restart, resources(:service => "munin-node")
  end
end
