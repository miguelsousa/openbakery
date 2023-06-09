import traceback


class OpenBakeryRunnerError(Exception):
    pass


class CircularDependencyError(OpenBakeryRunnerError):
    pass


class APIViolationError(OpenBakeryRunnerError):
    def __init__(self, message, result, *args):
        self.message = message
        self.result = result
        super().__init__(message, *args)


class ProtocolViolationError(OpenBakeryRunnerError):
    def __init__(self, message, *args):
        self.message = message
        super().__init__(message, *args)


class FailedCheckError(OpenBakeryRunnerError):
    def __init__(self, error, *args):
        message = f"Failed with {type(error).__name__}: {error}"
        self.error = error
        self.traceback = "".join(traceback.format_tb(error.__traceback__))
        super().__init__(message, *args)


class FailedConditionError(OpenBakeryRunnerError):
    """This is a serious problem with the check suite profile
    and it must be solved.
    """

    def __init__(self, condition, error, *args):
        message = (
            f"The condition {condition} had an error:"
            f" {type(error).__name__}: {error}"
        )
        self.condition = condition
        self.error = error
        self.traceback = "".join(traceback.format_tb(error.__traceback__))
        super().__init__(message, *args)


class MissingConditionError(OpenBakeryRunnerError):
    """This is a serious problem with the check suite profile
    and it must be solved, most probably a typo.
    """

    def __init__(self, condition_name, error, *args):
        message = (
            f"The condition named {condition_name} is missing:"
            f" {type(error).__name__}: {error}"
        )
        self.error = error
        self.traceback = "".join(traceback.format_tb(error.__traceback__))
        super().__init__(message, *args)


class FailedDependenciesError(OpenBakeryRunnerError):
    def __init__(self, check, error, *args):
        message = f"The check {check} had an error:" f" {type(error).__name__}: {error}"
        self.check = check
        self.error = error
        self.traceback = "".join(traceback.format_tb(error.__traceback__))
        super().__init__(message, *args)


class SetupError(OpenBakeryRunnerError):
    pass


class MissingValueError(OpenBakeryRunnerError):
    pass


class CircularAliasError(OpenBakeryRunnerError):
    pass


class NamespaceError(OpenBakeryRunnerError):
    pass


class ValueValidationError(OpenBakeryRunnerError):
    pass
