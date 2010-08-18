Webhooks
========

Web hooks are pretty amazing, and help to turn the web into a push instead of pull platform. We have support for hitting a URL whenever you commit to your project and we will try and rebuild your docs. This only rebuilds them if something has changed, so it is cheap on the server side. 

As anyone who has worked with push knows, pushing a doc update to your repo and watching it get updated within seconds is an awesome feeling. If you're on github, simply put `http://readthedocs.org/github` as a post-commit hook on your project. Otherwise your project detail page has your post-commit hook on it. It will
