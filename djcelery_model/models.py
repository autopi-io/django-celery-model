# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from celery.result import BaseAsyncResult
from celery.utils import uuid
from celery import signals

class ModelTaskMetaState(object):
    PENDING = 0
    STARTED = 1
    RETRY   = 2
    FAILURE = 3
    SUCCESS = 4

    @classmethod
    def lookup(cls, state):
        return getattr(cls, state)

class ModelTaskMetaManager(models.Manager):
    use_for_related_fields = True

    def pending(self):
        return self.filter(state__exact=ModelTaskMetaState.PENDING)

    def started(self):
        return self.filter(state__exact=ModelTaskMetaState.STARTED)

    def retrying(self):
        return self.filter(state__exact=ModelTaskMetaState.RETRY)

    def failed(self):
        return self.filter(state__exact=ModelTaskMetaState.FAILURE)

    def successful(self):
        return self.filter(state__exact=ModelTaskMetaState.SUCCESS)

    def ready(self):
        return self.filter(state__gte=ModelTaskMetaState.FAILURE)

class ModelTaskMeta(models.Model):
    STATES = (
        (ModelTaskMetaState.PENDING, 'PENDING'),
        (ModelTaskMetaState.STARTED, 'STARTED'),
        (ModelTaskMetaState.RETRY,   'RETRY'),
        (ModelTaskMetaState.FAILURE, 'FAILURE'),
        (ModelTaskMetaState.SUCCESS, 'SUCCESS'),
    )

    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey()
    task_id = models.CharField(max_length=255, unique=True)
    state = models.PositiveIntegerField(choices=STATES,
                                        default=ModelTaskMetaState.PENDING)

    objects = ModelTaskMetaManager()

    def __unicode__(self):
        return u'%s: %s' % (self.task_id, dict(self.STATES)[self.state])

class ModelAsyncResult(BaseAsyncResult):
    def forget(self):
        ModelTaskMeta.objects.filter(task_id=self.id).delete()
        return super(ModelAsyncResult, self).forget()

class TaskMixin(object):
    class Meta:
        abstract = True

    @property
    def tasks(self):
        content_type = ContentType.objects.get_for_model(self)
        queryset = ModelTaskMeta.objects.filter(content_type=content_type)
        return queryset.filter(object_id=self.pk)

    def apply_async(self, task, *args, **kwargs):
        if 'task_id' in kwargs:
            task_id = kwargs['task_id']
        else:
            task_id = kwargs['task_id'] = uuid()
        try:
            taskmeta = ModelTaskMeta.objects.get(task_id=task_id)
            taskmeta.content_object = self
            forget_if_ready(BaseAsyncResult(task_id))
        except ModelTaskMeta.DoesNotExist:
            taskmeta = ModelTaskMeta(task_id=task_id, content_object=self)
        taskmeta.save()
        return task.apply_async(*args, **kwargs)

    def get_task_results(self):
        return map(lambda task_id: ModelAsyncResult(task_id),
                   self.tasks.values_list('task_id', flat=True))

    def get_task_result(self, task_id):
        if self.tasks.filter(task_id=task_id).exists():
            return ModelAsyncResult(task_id)
        return BaseAsyncResult(task_id)

    def clear_task_results(self):
        map(forget_if_ready, self.get_task_results())

    def clear_task_result(self, task_id):
        forget_if_ready(self.get_task_result(task_id))

    @property
    def has_running_task(self):
        return len(filter(lambda x: not x.ready(), self.get_task_results())) > 0

def forget_if_ready(async_result):
    if async_result and async_result.ready():
        async_result.forget()

@signals.after_task_publish.connect
def handle_after_task_publish(sender=None, body=None, **kwargs):
    if body and 'id' in body:
        queryset = ModelTaskMeta.objects.filter(task_id=body['id'])
        queryset.update(state=ModelTaskMetaState.PENDING)

@signals.task_prerun.connect
def handle_task_prerun(sender=None, task_id=None, **kwargs):
    if task_id:
        queryset = ModelTaskMeta.objects.filter(task_id=task_id)
        queryset.update(state=ModelTaskMetaState.STARTED)

@signals.task_postrun.connect
def handle_task_postrun(sender=None, task_id=None, state=None, **kwargs):
    if task_id and state:
        queryset = ModelTaskMeta.objects.filter(task_id=task_id)
        queryset.update(state=ModelTaskMetaState.lookup(state))

@signals.task_revoked.connect
def handle_task_revoked(sender=None, request=None, **kwargs):
    if request and request.id:
        queryset = ModelTaskMeta.objects.filter(task_id=request.id)
        queryset.delete()