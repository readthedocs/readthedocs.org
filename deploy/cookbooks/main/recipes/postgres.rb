package "postgresql" do
    :upgrade
end

service "postgresql-8.4" do
  enabled true
  running true
  supports :status => true, :restart => true
  action [:enable, :start]
end
