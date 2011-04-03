# Gunicorn setup

cookbook_file "/etc/init/readthedocs-gunicorn.conf" do
    source "gunicorn.conf"
    owner "root"
    group "root"
    mode 0644
    notifies :restart, "service[readthedocs-gunicorn]"
end

service "readthedocs-gunicorn" do
    provider Chef::Provider::Service::Upstart
    enabled true
    running true
    supports :restart => true, :reload => true, :status => true
    action [:enable, :start]
end
