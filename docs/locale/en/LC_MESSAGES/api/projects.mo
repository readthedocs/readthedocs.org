��    G      T  a   �                '     A     W     n     �     �     �     �     �     
  3     u   N  .   �  ;   �  e   /  r   �  R   	  �   [	      �	  A   
  q   D
     �
  F   �
  %        C  &   _  8   �     �  ?   �  6     ;   O  9   �     �  [   �  8   A  2   z  0   �  4   �  +     0   ?  1   p  �  �  ,   }     �  $   �  N   �  �   <  U  �  ]     x   q  5   �  �      �   �  0   6  /   g  /   �  /   �  /   �  .   '  5   V  2   �  M   �  9     #   G     k  �   �  %   I  #   o  #   �  z  �     2     H     b     x     �     �     �     �     �          +  3   ;  u   o  .   �  ;     e   P  r   �  R   )  �   |        A   #  q   e     �  F   �  %   >     d  &   �  8   �     �  ?   �  6   9   ;   p   9   �      �   [   !  8   b!  2   �!  0   �!  4   �!  +   4"  0   `"  1   �"  �  �"  ,   �$     �$  $   �$  N   %  �   ]%  U  �%  ]   4'  x   �'  5   (  �   A(  �   �(  0   W)  /   �)  /   �)  /   �)  /   *  .   H*  5   w*  2   �*  M   �*  9   .+  #   h+     �+  �   �+  %   j,  #   �,  #   �,         =           E              	   G      .   "       #   1          3      )          >   !                          &   9       8      ;             +      A   %      F   <          '   
   2   4            5             ,      /   C              D               -       ?            6                (          B      7       $   0   *   @      :        :mod:`projects.admin` :mod:`projects.constants` :mod:`projects.forms` :mod:`projects.models` :mod:`projects.search_indexes` :mod:`projects.tasks` :mod:`projects.utils` :mod:`projects.views.private` :mod:`projects.views.public` :mod:`projects.views` :mod:`projects` A balla API to find files inside of a projects dir. A dashboard!  If you aint know what that means you aint need to. Essentially we show you an overview of your content. A detail view for a project with various dataz A periodic task used to update all projects that we mirror. A temporary workaround for active_versions filtering out things that were active, but failed to build Default values and other various configuration for projects, including available theme names and repository types. Django administration interface for `~projects.models.Project` and related models. Edit an existing project - depending on what type of project is being edited (created or imported) a different form will be displayed EmailHook(id, project_id, email) Export a projects' docs as a .zip file, including the .rst source Find matching filenames in the current directory and its subdirectories, and return a list of matching filenames. Get the default version (slug). Get the list of supported versions. Returns a list of version strings. Get the version representing "latest" HOME/user_builds/<project>/ HOME/user_builds/<project>/rtd-builds/ HOME/user_builds/<project>/rtd-builds/<default_version>/ Import docs from an repo ImportedFile(id, project_id, version_id, name, slug, path, md5) Link from HOME/user_builds/<project>/single_version -> Link from HOME/user_builds/project/subprojects/<project> -> Link from HOME/user_builds/project/translations/<lang> -> List of all tags by most common Make a project as deleted on POST, otherwise show a form asking for confirmation of delete. NEW Link from HOME/user_builds/cnametoproject/<cname> -> Now redirects to the normal /projects/<slug> view. OLD Link from HOME/user_builds/cnames/<cname> -> Path in the doc_path for the single_version symlink. Path in the doc_path that we symlink cnames Path in the doc_path that we symlink subprojects Path in the doc_path that we symlink translations Project(id, pub_date, modified_date, name, slug, description, repo, repo_type, project_url, canonical_url, version, copyright, theme, suffix, single_version, default_version, default_branch, requirements_file, documentation_type, analytics_code, path, conf_py_file, featured, skip, mirror, use_virtualenv, python_interpreter, use_system_packages, django_packages_url, privacy_level, version_privacy_level, language, main_language_project_id, num_major, num_minor, num_point) ProjectRelationship(id, parent_id, child_id) Remove single_version symlink Return a sweet badge for the project Return a url for the docs. Always use http for now, to avoid content warnings. Returns self.default_version if the version with that slug actually exists (is built and published). Otherwise returns 'latest'. Run one or more commands, and return ``(status, out, err)``. If more than one command is given, then this is equivalent to chaining them together with ``&&``; if all commands succeed, then ``(status, out, err)`` will represent the last successful command. If one command failed, then ``(status, out, err)`` will represent the failed command. Shows the available versions and lets the user choose which ones he would like to have built. Tasks related to projects, including fetching repository code, cleaning ``conf.py`` files, and rebuilding documentation. The destination path where the built docs are copied. The list of projects, which will optionally filter by user or tag, in which case a 'person' or 'tag' will be added to the context The management view for a project, where you will have links to edit the projects' configuration, edit the files associated with that project, etc. The path to the build LaTeX docs in the project. The path to the build dash docs in the project. The path to the build epub docs in the project. The path to the build html docs in the project. The path to the build json docs in the project. The path to the build man docs in the project. The path to the build singlehtml docs in the project. The path to the documentation root in the project. This has to be at the top-level because Nginx doesn't know the projects slug. Try importing a Project model from Open Comparison sites. Utility functions used by projects. WebHook(id, project_id, url) Write ``contents`` to the given ``filename``. If the filename's directory does not exist, it is created. Contents are written as UTF-8, ignoring any characters that cannot be encoded as UTF-8. our ghetto site search.  see roadmap. return a json list of project names return a json list of version names Project-Id-Version: readthedocs-docs
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2014-03-01 22:07+0800
PO-Revision-Date: 2014-03-01 13:43+0000
Last-Translator: Eric Holscher <eric@ericholscher.com>
Language-Team: LANGUAGE <LL@li.org>
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
Content-Transfer-Encoding: 8bit
Language: en
Plural-Forms: nplurals=2; plural=(n != 1);
 :mod:`projects.admin` :mod:`projects.constants` :mod:`projects.forms` :mod:`projects.models` :mod:`projects.search_indexes` :mod:`projects.tasks` :mod:`projects.utils` :mod:`projects.views.private` :mod:`projects.views.public` :mod:`projects.views` :mod:`projects` A balla API to find files inside of a projects dir. A dashboard!  If you aint know what that means you aint need to. Essentially we show you an overview of your content. A detail view for a project with various dataz A periodic task used to update all projects that we mirror. A temporary workaround for active_versions filtering out things that were active, but failed to build Default values and other various configuration for projects, including available theme names and repository types. Django administration interface for `~projects.models.Project` and related models. Edit an existing project - depending on what type of project is being edited (created or imported) a different form will be displayed EmailHook(id, project_id, email) Export a projects' docs as a .zip file, including the .rst source Find matching filenames in the current directory and its subdirectories, and return a list of matching filenames. Get the default version (slug). Get the list of supported versions. Returns a list of version strings. Get the version representing "latest" HOME/user_builds/<project>/ HOME/user_builds/<project>/rtd-builds/ HOME/user_builds/<project>/rtd-builds/<default_version>/ Import docs from an repo ImportedFile(id, project_id, version_id, name, slug, path, md5) Link from HOME/user_builds/<project>/single_version -> Link from HOME/user_builds/project/subprojects/<project> -> Link from HOME/user_builds/project/translations/<lang> -> List of all tags by most common Make a project as deleted on POST, otherwise show a form asking for confirmation of delete. NEW Link from HOME/user_builds/cnametoproject/<cname> -> Now redirects to the normal /projects/<slug> view. OLD Link from HOME/user_builds/cnames/<cname> -> Path in the doc_path for the single_version symlink. Path in the doc_path that we symlink cnames Path in the doc_path that we symlink subprojects Path in the doc_path that we symlink translations Project(id, pub_date, modified_date, name, slug, description, repo, repo_type, project_url, canonical_url, version, copyright, theme, suffix, single_version, default_version, default_branch, requirements_file, documentation_type, analytics_code, path, conf_py_file, featured, skip, mirror, use_virtualenv, python_interpreter, use_system_packages, django_packages_url, privacy_level, version_privacy_level, language, main_language_project_id, num_major, num_minor, num_point) ProjectRelationship(id, parent_id, child_id) Remove single_version symlink Return a sweet badge for the project Return a url for the docs. Always use http for now, to avoid content warnings. Returns self.default_version if the version with that slug actually exists (is built and published). Otherwise returns 'latest'. Run one or more commands, and return ``(status, out, err)``. If more than one command is given, then this is equivalent to chaining them together with ``&&``; if all commands succeed, then ``(status, out, err)`` will represent the last successful command. If one command failed, then ``(status, out, err)`` will represent the failed command. Shows the available versions and lets the user choose which ones he would like to have built. Tasks related to projects, including fetching repository code, cleaning ``conf.py`` files, and rebuilding documentation. The destination path where the built docs are copied. The list of projects, which will optionally filter by user or tag, in which case a 'person' or 'tag' will be added to the context The management view for a project, where you will have links to edit the projects' configuration, edit the files associated with that project, etc. The path to the build LaTeX docs in the project. The path to the build dash docs in the project. The path to the build epub docs in the project. The path to the build html docs in the project. The path to the build json docs in the project. The path to the build man docs in the project. The path to the build singlehtml docs in the project. The path to the documentation root in the project. This has to be at the top-level because Nginx doesn't know the projects slug. Try importing a Project model from Open Comparison sites. Utility functions used by projects. WebHook(id, project_id, url) Write ``contents`` to the given ``filename``. If the filename's directory does not exist, it is created. Contents are written as UTF-8, ignoring any characters that cannot be encoded as UTF-8. our ghetto site search.  see roadmap. return a json list of project names return a json list of version names 