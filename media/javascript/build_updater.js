(function () {

    // An updater that renders details about a build.
    this.BuildUpdater = function(buildId) {
        this.buildId = buildId;
        this.buildUrl = '/api/v1/build/' + this.buildId;
        this.buildDiv = 'div#build-' + this.buildId;
        this.buildLoadingImg = this.buildDiv + ' img.build-loading';
        this.intervalId = null;
        return this;
    };

    BuildUpdater.prototype.stopPolling = function() {
        $(this.buildLoadingImg).addClass('hide');
        clearInterval(this.intervalId);
    };

    // Show an animated 'loading' gif while we get the current details of the build
    // with `buildId` from the server.
    //
    // If the build was successful, hide the loading gif, populate any <span>
    // nodes that have ids matching the pattern "build-<field name in `data`
    // object>" and clear `this.intervalId`.
    BuildUpdater.prototype.render = function(data) {
        var _this = this;

        for (var prop in data) {
            if (data.hasOwnProperty(prop)) {
                var val = data[prop];
                var el = $(this.buildDiv + ' span#build-' + prop);

                if (prop == 'success') {
                    if (data.hasOwnProperty('state') && data['state'] != 'finished') {
                        val = "Not yet finished";
                    }
                    else {
                        val = val ? "Passed" : "Failed";
                    }
                }

                if (prop == 'state') {
                    val = val.charAt(0).toUpperCase() + val.slice(1);

                    if (val == 'Finished') {
                        _this.stopPolling();
                    }
                }

                if (el) {
                    el.text(val);
                }
            }
        }
    };

    BuildUpdater.prototype.getBuild = function() {
        _this = this;
        
        $.get(this.buildUrl, function(data) {
            _this.render(data);
        });
    };

    // If the build with ID `this.buildId` has a state other than finished, poll
    // the server every 5 seconds for the current status. Update the details
    // page with the latest values from the server, to keep the user informed of
    // progress.
    //
    // If we haven't received a 'finished' state back the server in 10 minutes,
    // stop polling.
    BuildUpdater.prototype.startPolling = function() {
        var stateSpan = $(this.buildDiv + ' span#build-state');
        var _this = this;

        // If the build is already finished, or it isn't displayed on the page,
        // ignore it.
        if (stateSpan.text() == 'Finished' || stateSpan.length === 0) {
            return;
        }

        $(this.buildLoadingImg).removeClass('hide');

        // Get build data and render.
        this.getBuild();

        // Get build data and render every 5 seconds until finished.
        var intervalId = setInterval(function () {
            _this.getBuild();
        }, 5000);

        // Stop polling after 10 minutes, in case the build never finishes.
        setTimeout(function() {
            _this.stopPolling();
        }, 600000);
    };


    // An updater that renders builds in a list of builds.
    this.BuildListUpdater = function(buildId) {
        BuildUpdater.call(this, buildId);
        return this;
    };

    BuildListUpdater.prototype = new BuildUpdater();

    BuildListUpdater.prototype.render = function(data) {
        var _this = this;

        data['success'] = data['success'] ? "Passed" : "Failed";
        data['state'] = data['state'].charAt(0).toUpperCase() + data['state'].slice(1);

        for (var prop in data) {
            if (data.hasOwnProperty(prop)) {
                var val = data[prop];
                var el = $(this.buildDiv + ' span#build-' + prop);

                if (prop == 'state') {
                    // Show the success value ("Passed" or "Failed") if the build
                    // finished. Otherwise, show the state value.
                    if (val == 'Finished') {
                        val = data['success'];
                        _this.stopPolling();
                    } else {
                        data['success'] = '';
                    }
                }

                if (el) {
                    el.text(val);
                }
            }
        }
    };


}).call(this);

