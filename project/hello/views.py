import socket

from django.conf import settings
from django.views.generic import TemplateView
from django.utils import timezone

from . import tasks


class HelloView(TemplateView):
    template_name = "hello_world.html"

    def get_context_data(self, **kwargs):
        now = timezone.now()
        container = socket.gethostname()
        remote_addr = self.request.META.get("REMOTE_ADDR", "no remote addr")
        # Invoke a task to record the details and provide a usage count
        task_watcher = tasks.write_usage_log.delay(now, container, remote_addr)
        counter = task_watcher.get()
        # Provide the context to the template
        return super().get_context_data(
            now=now,
            counter=counter,
            debug=settings.DEBUG,
            container=container,
            remote_addr=remote_addr,
            **kwargs,
        )
