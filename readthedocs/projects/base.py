class BuildRequest(celery.worker.request.Request):

    def on_timeout(self, soft, timeout):
        super().on_timeout(soft, timeout)
        log.warning(
            'A timeout was enforced for task.',
            task_name=self.task.name,
            project_slug=self.task.args.project_slug,
            build_id=self.task.args.build_id,
            timeout=timeout,
            soft=soft,
        )


class BuildTaskBase(celery.Task):

    autoretry_for = (
        ConcurrencyLimiteReached,
    )
    max_retries = 5  # 5 per normal builds, 25 per concurrency limited
    default_retry_delay = 7 * 60

    # Expected exceptions that will be logged as info only and not retried
    throws = (
        DuplicatedBuildError,
        VersionLockedError,
        ProjectBuildsSkippedError,
        ConfigError,
        YAMLParseError,
    )

    acks_late = True
    track_started = True

    # These values have to be dynamic based on project
    time_limit = None
    soft_time_limit = None

    Request = BuildRequest

    # 1. raise Reject(requeue=False) on duplicated builds
    # 2. use a global `task_cls` (https://docs.celeryproject.org/en/latest/userguide/tasks.html#app-wide-usage) to logs actions
    # 3. use CELERY_IMPORTS to register the tasks (https://docs.celeryproject.org/en/latest/userguide/configuration.html#std-setting-imports)
    # 4. use CELERY_TASK_IGNORE_RESULT=True since we are not using the result at all


    def _setup_sigterm():
        def sigterm_received(*args, **kwargs):
            log.warning('SIGTERM received. Waiting for build to stop gracefully after it finishes.')

        # Do not send the SIGTERM signal to children (pip is automatically killed when
        # receives SIGTERM and make the build to fail one command and stop build)
        signal.signal(signal.SIGTERM, sigterm_received)

    def _check_concurrency_limit():
        try:
            response = api_v2.build.concurrent.get(project__slug=self.project.slug)
            concurrency_limit_reached = response.get('limit_reached', False)
            max_concurrent_builds = response.get(
                'max_concurrent',
                settings.RTD_MAX_CONCURRENT_BUILDS,
            )
        except Exception:
            log.exception(
                'Error while hitting/parsing API for concurrent limit checks from builder.',
                project_slug=self.project.slug,
                version_slug=self.version.slug,
            )
            concurrency_limit_reached = False
            max_concurrent_builds = settings.RTD_MAX_CONCURRENT_BUILDS

        if concurrency_limit_reached:
            log.warning(
                'Delaying tasks due to concurrency limit.',
                project_slug=self.project.slug,
                version_slug=self.version.slug,
            )

            # This is done automatically on the environment context, but
            # we are executing this code before creating one
            api_v2.build(self.build['id']).patch({
                'error': BuildMaxConcurrencyError.message.format(
                    limit=max_concurrent_builds,
                ),
                'builder': socket.gethostname(),
            })
            self.task.retry(
                exc=BuildMaxConcurrencyError,
                throw=False,
                # We want to retry this build more times
                max_retries=25,
            )
            return False

    def _check_duplicated_build(self, build):
        if self.build.get('status') == DuplicatedBuildError.status:
            log.warning(
                'NOOP: build is marked as duplicated.',
                project_slug=self.project.slug,
                version_slug=self.version.slug,
                build_id=build_pk,
                commit=self.commit,
            )
            raise DuplicatedBuildError

    def before_start(self, task_id, args, kwargs):
        version_pk = kwargs.get('version_pk')
        build_pk = kwargs.get('build_pk')
        commit = kwargs.get('commit')
        record = kwargs.get('record')
        force = kwargs.get('force')

        build = self.get_build(build_pk)
        version = self.get_version(version_pk)
        project = self.version.project

        log.bind(
            build_pk=build.pk,
            commit=commit,
            project_slug=project.slug,
            version_slug=version.slug,
            force=force,
            record=record,
        )
        log.info('Running task.', name=self.name)

        self.data = BuildData(
            build=build,
            version=version,
            project=project,
            record=record,
        )

        # NOTE: this is never called. I didn't find anything in the logs, so we can probably remove it
        self._setup_sigterm()

        self._check_duplicated_build(build)
        self._check_concurrency_limit(project)
        self._reset_build(build)

    def _reset_build(self, build):
        # Reset build only if it has some commands already. We need this here
        # in case the build was retried due an internal error (e.g. the AWS
        # instance was killed while building). Note that this is possible
        # because we are using `acks_late=True` in Celery
        if self.build.get('commands'):
            api_v2.build(self.build['id']).reset.post()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        # Take a proper action based on the ``exc``. For example, if
        # ``vcs_support_utils.LockTimeout`` retry the task Note that some
        # exceptions may require access to the ``environment`` variable to
        # update the context (hiting the API to set the build status)

        if exc is SoftTimeLimitExceeded:
            log.warning('Build is taking too much time. Risk to be killed soon.')

        if exc is HardTimeLimitExceeded:
            log.warning('Build killed because timeout.')


        if isinstance(exc, ConfigError):
            self.build['error'] = str(
                YAMLParseError(
                    YAMLParseError.GENERIC_WITH_PARSE_EXCEPTION.format(
                        exception=str(exc),
                    ),
                ),
            )

        log.exception('An unhandled exception was raised during build setup')

        # # We should check first for build_env.
        # # If isn't None, it means that something got wrong
        # # in the second step (`self.run_build`)
        # if self.build_env is not None:
        #     self.build_env.failure = BuildEnvironmentError(
        #         BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
        #             build_id=build_pk,
        #         ),
        #     )
        #     self.update_build(BUILD_STATE_FINISHED)
        # elif self.setup_env is not None:
        #     self.setup_env.failure = BuildEnvironmentError(
        #         BuildEnvironmentError.GENERIC_WITH_BUILD_ID.format(
        #             build_id=build_pk,
        #         ),
        #     )
        #     self.update_build(BUILD_STATE_FINISHED)

        # TODO: do not send notifications on ``VersionLockedError``
        # (vcs_support_utils.LockTimeout) since it's not a problem for the user

        # Send notifications for unhandled errors
        self.send_notifications(
            version_pk,
            build_pk,
            event=WebHookEvent.BUILD_FAILED,
        )

    def on_success(self, retval, task_id, args, kwargs):
        # send build status to github
        # send webhook notification
        # emit django signal for build success
        if not self.project.has_valid_clone:
            self.set_valid_clone()

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        pass

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        build_complete.send(sender=Build, build=self.build_env.build)

        if self.commit:
            # TODO: check for proper status values :)
            if status == 'failed':
                build_status = BUILD_STATUS_FAILURE
            if status == 'success':
                build_status = BUILD_STATUS_SUCCESS

            send_external_build_status(
                version_type=self.version.type,
                build_pk=self.build['id'],
                commit=self.commit,
                status=build_status,
            )

        if status == 'failed':
            event = WebHookEvent.BUILD_FAILED
        if status == 'success':
            event = WebHookEvent.BUILD_PASSED

        self.send_notifications(
            version_pk,
            build_pk,
            event=event,
        )


        clean_build(version_pk)
