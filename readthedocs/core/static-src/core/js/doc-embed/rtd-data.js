/*
 * This exposes data injected during the RTD build into the template. It's
 * provided via the global READTHEDOCS_DATA variable and is exposed here as a
 * module for cleaner usage.
 */


/*
 * Access READTHEDOCS_DATA on call, not on module load. The reason is that the
 * READTHEDOCS_DATA might not be available during script load time.
 */
function get() {
    return $.extend({
        api_host: 'https://readthedocs.org'
    }, window.READTHEDOCS_DATA);
}


module.exports = {
    get: get
};
