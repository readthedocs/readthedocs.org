/* Public task tracking */

var jquery = require('jquery');

function poll_task(data) {
    var defer = jquery.Deferred();
    var tries = 5;

    function poll_task_loop() {
        jquery
            .getJSON(data.url)
            .done(function (task) {
                if (task.finished) {
                    if (task.success) {
                        defer.resolve();
                    }
                    else {
                        defer.reject({message: task.error});
                    }
                }
                else {
                    setTimeout(poll_task_loop, 2000);
                }
            })
            .fail(function (error) {
                console.error('Error polling task:', error);
                tries -= 1;
                if (tries > 0) {
                    setTimeout(poll_task_loop, 2000);
                }
                else {
                    var error_msg = error.responseJSON.detail || error.statusText;
                    defer.reject({message: error_msg});
                }
            });
    }

    setTimeout(poll_task_loop, 2000);

    return defer;
}

function trigger_task(config) {
    var defer = jquery.Deferred();
    var url = config.url;
    var token = config.token;
    var data = {csrfmiddlewaretoken: token};

    $.ajax({
        method: 'POST',
        url: url,
        data: data,
        success: function (data) {
            poll_task(data)
                .then(function () {
                    defer.resolve();
                })
                .fail(function (error) {
                    // The poll_task function defer will only reject with
                    // normalized error objects
                    defer.reject(error);
                });
        },
        error: function (error) {
            var error_msg = error.responseJSON.detail || error.statusText;
            defer.reject({message: error_msg});
        }
    });

    return defer;
}

module.exports = {
    poll_task: poll_task,
    trigger_task: trigger_task
};
