from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify

from projects.constants import DEFAULT_THEME_CHOICES, THEME_DEFAULT

from taggit.managers import TaggableManager


class Project(models.Model):
    user = models.ForeignKey(User, related_name='projects')
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    github_repo = models.CharField(max_length=100, blank=True)
    github_login = models.CharField(max_length=100, blank=True)
    docs_directory = models.CharField(max_length=255, blank=True)
    pub_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    tags = TaggableManager()

    class Meta:
        ordering = ('-modified_date', 'name')

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('project_detail', args=[self.user.username, self.slug])

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super(Project, self).save(*args, **kwargs)
        if not self.confs:
            conf = Conf.objects.create(project=self)

    @property
    def primary_conf(self):
        return self.confs.get(primary_conf=True)


class Conf(models.Model):
    project = models.ForeignKey(Project, related_name='confs')
    copyright = models.CharField(max_length=255, blank=True)
    version = models.CharField(max_length=20, blank=True)
    theme = models.CharField(max_length=20, choices=DEFAULT_THEME_CHOICES,
                             default=THEME_DEFAULT)
    primary_conf = models.BooleanField(default=True)

    def __unicode__(self):
        return '%s config, v. %s' % (self.project.name, self.version)
    
    def save(self, *args, **kwargs):
        if self.primary_conf:
            self.project.confs.update(primary_conf=False)
        super(Conf, self).save(*args, **kwargs)


class File(models.Model):
    project = models.ForeignKey(Project, related_name='files')
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children')
    heading = models.CharField(max_length=255)
    slug = models.SlugField()
    content = models.TextField()
    denormalized_path = models.CharField(max_length=255, editable=False)
    ordering = models.PositiveSmallIntegerField(default=1)

    class Meta:
        ordering = ('ordering', 'denormalized_path',)

    def __unicode__(self):
        return '%s: %s' % (self.project.name, self.heading) 
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.heading)

        if self.parent:
            path = '%s%s/' % (self.parent.denormalized_path, self.slug)
        else:
            path = '%s/' % (self.slug)

        self.denormalized_path = path

        super(File, self).save(*args, **kwargs)

        if self.children:
            def update_children(children):
                for child in children:
                    child.save()
                    update_children(child.children.all())
            update_children(self.children.all())
