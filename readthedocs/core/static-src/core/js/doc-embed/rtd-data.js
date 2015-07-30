/*
 * This exposes data injected during the RTD build into the template. It's
 * provided via the global READTHEDOCS_DATA variable and is exposed here as a
 * module for cleaner usage.
 */


var data = READTHEDOCS_DATA;


if (data.api_host === undefined) {
    data.api_host = 'https://readthedocs.org';
}


module.exports = data;
