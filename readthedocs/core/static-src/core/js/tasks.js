/* Public task tracking */

var jquery = require('jquery');

function poll_task (data) {
    var defer = jquery.Deferred();

    function poll_task_loop () {
        jquery
            .getJSON(data.url)
            .success(function (task) {
                if (task.finished) {
                    if (task.success) {
                        defer.resolve();
                    }
                    else {
                        defer.reject(task.error || 'Error');
                    }
                }
                else {
                    setTimeout(poll_task_loop, 2000);
                }
            })
            .error(function (error) {
                console.error('Error polling task:', error);
                setTimeout(poll_task_loop, 2000);
            });
    }

    setTimeout(poll_task_loop, 2000);

    return defer;
}

function trigger_task (url) {
    var defer = jquery.Deferred();

    $.ajax({
        method: 'POST',
        url: url,
        success: function (data) {
            poll_task(data)
                .then(function () {
                    defer.resolve();
                })
                .fail(function (error) {
                    defer.reject(error);
                });
        },
        error: function (error) {
            defer.reject(error);
        }
    });

    return defer;
}

module.exports = {
    poll_task: poll_task,
    trigger_task: trigger_task
};
