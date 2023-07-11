def setup(app):
    app.add_crossref_type(
        directivename="setting",
        rolename="setting",
        indextemplate="pair: %s; setting",
    )

    return {
        'version': 'builtin',
        'parallel_read_safe': True,
        'parallel_write_safe': True,
    }
