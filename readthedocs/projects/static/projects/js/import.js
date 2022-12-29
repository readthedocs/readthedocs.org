require=function n(a,o,s){function i(r,e){if(!o[r]){if(!a[r]){var t="function"==typeof require&&require;if(!e&&t)return t(r,!0);if(u)return u(r,!0);throw(e=new Error("Cannot find module '"+r+"'")).code="MODULE_NOT_FOUND",e}t=o[r]={exports:{}},a[r][0].call(t.exports,function(e){return i(a[r][1][e]||e)},t,t.exports,n,a,o,s)}return o[r].exports}for(var u="function"==typeof require&&require,e=0;e<s.length;e++)i(s[e]);return i}({1:[function(e,r,t){var a=e("jquery");function n(e){var t=a.Deferred(),n=5;return setTimeout(function r(){a.getJSON(e.url).done(function(e){e.finished?e.success?t.resolve():t.reject({message:e.error}):setTimeout(r,2e3)}).fail(function(e){console.error("Error polling task:",e),0<--n?setTimeout(r,2e3):(e=e.responseJSON.detail||e.statusText,t.reject({message:e}))})},2e3),t}r.exports={poll_task:n,trigger_task:function(e){var r=a.Deferred(),t=e.url,e=e.token;return $.ajax({method:"POST",url:t,data:{csrfmiddlewaretoken:e},success:function(e){n(e).then(function(){r.resolve()}).fail(function(e){r.reject(e)})},error:function(e){e=e.responseJSON.detail||e.statusText;r.reject({message:e})}}),r}}},{jquery:"jquery"}],"projects/import":[function(e,r,t){var o=e("knockout"),i=e("jquery"),n=e("readthedocs/core/static-src/core/js/tasks");function u(e,r){var t=i("<a>").attr("href",e).get(0);return Object.keys(r).map(function(e){t.search&&(t.search+="&"),t.search+=e+"="+r[e]}),t.href}function l(e,r){var t=this;t.id=o.observable(e.id),t.name=o.observable(e.name),t.slug=o.observable(e.slug),t.provider_name=o.observable(e.vcs_provider),t.active=o.observable(e.active),t.avatar_url=o.observable(u(e.avatar_url,{size:32})),t.display_name=o.computed(function(){return`${t.name()||t.slug()} (${t.provider_name()} Organization)`}),t.filter_id=o.computed(function(){return t.id()}),t.filter_type="org",t.filtered=o.computed(function(){var e=r.filter_by();return e.id&&e.id!==t.filter_id()||e.type&&e.type!==t.filter_type})}function c(e,r){var t=this;t.id=o.observable(e.id),t.username=o.observable(e.username),t.provider_name=o.observable(e.provider.name),t.active=o.observable(e.active),t.avatar_url=o.observable(u(e.avatar_url,{size:32})),t.provider=o.observable(e.provider),t.display_name=o.computed(function(){return`${t.username()} (${t.provider_name()})`}),t.filter_id=o.computed(function(){return t.provider().id}),t.filter_type="own",t.filtered=o.computed(function(){var e=r.filter_by();return e.id&&e.id!==t.filter_id()||e.type&&e.type!==t.filter_type})}function a(e,n){var a=this;a.id=o.observable(e.id),a.name=o.observable(e.name),a.full_name=o.observable(e.full_name),a.description=o.observable(e.description),a.vcs=o.observable(e.vcs),a.default_branch=o.observable(e.default_branch),a.organization=o.observable(e.organization),a.html_url=o.observable(e.html_url),a.clone_url=o.observable(e.clone_url),a.ssh_url=o.observable(e.ssh_url),a.matches=o.observable(e.matches),a.match=o.computed(function(){var e=a.matches();if(e&&0<e.length)return e[0]}),a.private=o.observable(e.private),a.admin=o.observable(e.admin),a.is_locked=o.computed(function(){return(n.has_sso_enabled||a.private())&&!a.admin()}),a.avatar_url=o.observable(u(e.avatar_url,{size:32})),a.import_repo=function(){var r={name:a.name(),repo:a.clone_url(),repo_type:a.vcs(),default_branch:a.default_branch(),description:a.description(),project_url:a.html_url(),remote_repository:a.id()},t=i("<form />"),e=(t.attr("action",n.urls.projects_import).attr("method","POST").hide(),Object.keys(r).map(function(e){e=i("<input>").attr("type","hidden").attr("name",e).attr("value",r[e]);t.append(e)}),i("<input>").attr("type","hidden").attr("name","csrfmiddlewaretoken").attr("value",n.csrf_token)),e=(t.append(e),i("<input>").attr("type","submit"));t.append(e),i("body").append(t),t.submit()}}function s(e,r){var s=this;s.config=r||{},s.urls=r.urls||{},s.csrf_token=r.csrf_token||"",s.has_sso_enabled=r.has_sso_enabled||!1,s.error=o.observable(null),s.is_syncing=o.observable(!1),s.is_ready=o.observable(!1),s.page_current=o.observable(null),s.page_next=o.observable(null),s.page_previous=o.observable(null),s.filter_by=o.observable({id:null,type:null}),s.accounts_raw=o.observableArray(),s.organizations_raw=o.observableArray(),s.filters=o.computed(function(){var e,r=[],t=s.accounts_raw(),n=s.organizations_raw();for(e in t){var a=new c(t[e],s);r.push(a)}for(e in n){var o=new l(n[e],s);r.push(o)}return r}),s.projects=o.observableArray(),o.computed(function(){var e=s.filter_by(),r=s.page_current()||s.urls["remoterepository-list"];s.page_current()||("org"===e.type&&(r=u(s.urls["remoterepository-list"],{org:e.id})),"own"===e.type&&(r=u(s.urls["remoterepository-list"],{own:e.id}))),s.error(null),i.getJSON(r).done(function(e){var r,t=[];for(r in s.page_next(e.next),s.page_previous(e.previous),e.results){var n=new a(e.results[r],s);t.push(n)}s.projects(t)}).fail(function(e){e=e.responseJSON.detail||e.statusText;s.error({message:e})}).always(function(){s.is_ready(!0)})}).extend({deferred:!0}),s.get_organizations=function(){i.getJSON(s.urls["remoteorganization-list"]).done(function(e){s.organizations_raw(e.results)}).fail(function(e){e=e.responseJSON.detail||e.statusText;s.error({message:e})})},s.get_accounts=function(){i.getJSON(s.urls["remoteaccount-list"]).done(function(e){s.accounts_raw(e.results)}).fail(function(e){e=e.responseJSON.detail||e.statusText;s.error({message:e})})},s.sync_projects=function(){var e=s.urls.api_sync_remote_repositories;s.error(null),s.is_syncing(!0),n.trigger_task({url:e,token:s.csrf_token}).then(function(e){s.get_organizations(),s.get_accounts(),s.filter_by.valueHasMutated()}).fail(function(e){s.error(e)}).always(function(){s.is_syncing(!1)})},s.has_projects=o.computed(function(){return 0<s.projects().length}),s.next_page=function(){s.page_current(s.page_next())},s.previous_page=function(){s.page_current(s.page_previous())},s.set_filter_by=function(e,r){var t=s.filter_by();t.id===e?(t.id=null,t.type=null):(t.id=e,t.type=r),s.filter_by(t),t.id&&s.page_current(null)}}i(function(){var t=i("#id_repo"),n=i("#id_repo_type");t.blur(function(){var e,r=t.val();switch(!0){case/^hg/.test(r):e="hg";break;case/^bzr/.test(r):case/launchpad/.test(r):e="bzr";break;case/trunk/.test(r):case/^svn/.test(r):e="svn";break;default:case/github/.test(r):case/(^git|\.git$)/.test(r):e="git"}n.val(e)})}),s.init=function(e,r,t){t=new s(0,t);return t.get_accounts(),t.get_organizations(),o.applyBindings(t,e),t},r.exports.ProjectImportView=s},{jquery:"jquery",knockout:"knockout","readthedocs/core/static-src/core/js/tasks":1}]},{},[]);