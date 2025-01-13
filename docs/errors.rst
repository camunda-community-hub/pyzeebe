==========
Errors
==========

All ``pyzeebe`` errors inherit from :py:class:`PyZeebeError`

.. autoexception:: pyzeebe.errors.PyZeebeError

.. autoexception:: pyzeebe.errors.TaskNotFoundError

.. autoexception:: pyzeebe.errors.NoVariableNameGivenError

.. autoexception:: pyzeebe.errors.SettingsError

.. autoexception:: pyzeebe.errors.DuplicateTaskTypeError

.. autoexception:: pyzeebe.errors.ActivateJobsRequestInvalidError

.. autoexception:: pyzeebe.errors.JobAlreadyDeactivatedError

.. autoexception:: pyzeebe.errors.JobNotFoundError

.. autoexception:: pyzeebe.errors.MessageAlreadyExistsError

.. autoexception:: pyzeebe.errors.ProcessDefinitionNotFoundError

.. autoexception:: pyzeebe.errors.ProcessInstanceNotFoundError

.. autoexception:: pyzeebe.errors.ProcessDefinitionHasNoStartEventError

.. autoexception:: pyzeebe.errors.ProcessTimeoutError

.. autoexception:: pyzeebe.errors.ProcessInvalidError

.. autoexception:: pyzeebe.errors.DecisionNotFoundError

.. autoexception:: pyzeebe.errors.InvalidJSONError

.. autoexception:: pyzeebe.errors.ZeebeError

.. autoexception:: pyzeebe.errors.ZeebeBackPressureError

.. autoexception:: pyzeebe.errors.ZeebeGatewayUnavailableError

.. autoexception:: pyzeebe.errors.ZeebeInternalError

.. autoexception:: pyzeebe.errors.ZeebeDeadlineExceeded

.. autoexception:: pyzeebe.errors.InvalidOAuthCredentialsError

.. autoexception:: pyzeebe.errors.UnknownGrpcStatusCodeError


=================
Exception Handler
=================

.. autofunction:: pyzeebe.default_exception_handler
