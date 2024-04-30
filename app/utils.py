from celery import Celery

def make_celery(app):
    celery = Celery(app.import_name)
    celery.conf.update(app.config)  # Update Celery config using entire app config

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery