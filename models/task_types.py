from tasks import AbstractTask


class AbstractTaskType(object):
    def __init__(self, redundancy):
        self.redundancy = redundancy

        assert issubclass(self.task_model, AbstractTask), \
            "You should define task_model property"

        assert self.type_name, "You should define type_name (underscore)"
        assert self.template, "You should define template"

    def import_tasks(self, tasks):
        """Imports tasks from an iterable over dicts
        io is left out of scope here.

        Args:
            tasks: An iterable over dicts
        Returns:
            None

        Raises:
            TaskImportError
        """
        raise NotImplementedError()

    def export_reports(self, qs=None):
        """Exports results
        io is left out of scope here as well

        Args:
            qs: Queryset, an optional argument. Default value is QS that
            exports all tasks with amount of answers > redundancy
        Returns:
            Generator of dicts with results
        """

        if qs is None:
            raise NotImplementedError
            qs = self.task_model.objects.filter()

        for task in qs:
            yield task.get_results()

    def get_next(self, user):
        """Finds given user a new task
        Assumes that user is eligible for this kind of tasks

        Args:
            user: an instance of User model
        Returns:
            rendered self.template with task or None
        """

        raise NotImplementedError

    def _render_task(self, task):
        """Returns rendered self.template with values from task inserted
        Takes burden to prepare task data for Jinja template if this cannot
        be covered by jinja itself

        Args:
            task: an instance of self.task_model model
        Returns:
            rendered self.template with task
        """

        raise NotImplementedError

    def skip_task(self, user, task):
        """Marks given task as a skipped by a given user
        Assumes that user is eligible for this kind of tasks

        Args:
            user: an instance of User model
            task: an instance of self.task_model model
        Returns:
            None

        Raises:
            TaskSkipError
        """

        raise NotImplementedError

    def save_task_result(self, user, task, answer):
        """Saves user's answers for a given task
        Assumes that user is eligible for this kind of tasks
        Covers both, add and update (when user is editing his results) cases

        Args:
            user: an instance of User model who provided an answer
            task: an instance of self.task_model model
            answer: QueryDict with answers
        Returns:
            None

        Raises:
            TaskSaveError - in case of general problems
            TaskValidationError - in case of validation problems
        """

        raise NotImplementedError

    # Still in doubts about these methods:
    # get_media that returns js/css specific for a task. Might as well go
    # to a TaskType property or be mentioned right in template
    #
    # get_help that returns help text or template with help. Might be a
    # property too
    #
    # edit, that will return qs or a paginated list of tasks that was already
    # complete by a given user or None if editing is prohibited for this task
    # type
