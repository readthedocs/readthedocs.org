/* UGGGGH at javascript */

exports.get_param = function (name) {
    var url = window.location.search.substring(1),
    vars = url.split('&');

    for (n in vars) {
        var param = vars[n].split('='),
            param_name = param[0],
            param_val = param[1];
        if (name == param_name) {
            return param_val;
        }
    }
    return false
}
