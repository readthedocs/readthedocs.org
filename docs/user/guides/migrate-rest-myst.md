# How to migrate from reStructuredText to MyST Markdown

In this guide, you will find
how you can start writing Markdown in your existing reStructuredText project,
or migrate it completely.

Sphinx is usually associated with reStructuredText, the markup language
{pep}`designed for the CPython project in the early '00s <287>`.
However, for quite some time Sphinx has been compatible with Markdown as well,
thanks to a number of extensions.

The most powerful of such extensions is {doc}`MyST-Parser <myst-parser:index>`,
which implements a CommonMark-compliant, extensible Markdown dialect
with support for the Sphinx roles and directives that make it so useful.

If, **instead of migrating**, you are starting a new project from scratch,
have a look at {doc}`myst-parser:intro`.
If you are starting a **project for Jupyter**, you can start with Jupyter Book, which uses ``MyST-Parser``, see the official Jupyter Book tutorial: {doc}`jupyterbook:start/your-first-book`

## How to write  your content both in reStructuredText and MyST

It is useful to ask whether a migration is necessary in the first place.
Doing bulk migrations of large projects with lots of work in progress
will create conflicts for ongoing changes.
On the other hand, your writers might prefer to have some files in Markdown
and some others in reStructuredText, for whatever reason.
Luckily, Sphinx supports reading both types of markup at the same time without problems.

To start using MyST in your existing Sphinx project,
first [install the `myst-parser` Python package](https://myst-parser.readthedocs.io/en/stable/intro.html#installation)
and then [enable it on your configuration](https://myst-parser.readthedocs.io/en/stable/intro.html#enable-myst-in-sphinx):

```{code-block} py
:caption: conf.py
:emphasize-lines: 4

extensions = [
    # Your existing extensions
    ...,
    "myst_parser",
]
```

Your reStructuredText documents will keep rendering,
and you will be able to add MyST documents with the `.md` extension
that will be processed by MyST-Parser.

As an example, _this guide_ is written in MyST
while the rest of the Read the Docs documentation is written in reStructuredText.

```{note}
By default, MyST-Parser registers the `.md` suffix for MyST source files.
If you want to use a different suffix, you can do so by changing your
`source_suffix` configuration value in `conf.py`.
```

## How to convert existing reStructuredText documentation to MyST

To convert existing reST documents to MyST, you can use
the `rst2myst` CLI script shipped by {doc}`rst-to-myst:index`.
The script supports converting the documents one by one,
or scanning a series of directories to convert them in bulk.

After {doc}``installing `rst-to-myst` <rst-to-myst:index>``,
you can run the script as follows:

```console
$ rst2myst convert docs/source/index.rst  # Converts index.rst to index.md
$ rst2myst convert docs/**/*.rst  # Convert every .rst file under the docs directory
```

This will create a `.md` MyST file for every `.rst` source file converted.

### How to modify the behaviour of `rst2myst`

The `rst2myst` accepts several flags to modify its behavior.
All of them have sensible defaults, so you don't have to specify them
unless you want to.

These are a few options you might find useful:

{option}``-d, --dry-run <rst-to-myst:rst2myst-convert.--dry-run>``
: Only verify that the script would work correctly,
  without actually writing any files.

{option}``-R, --replace-files <rst-to-myst:rst2myst-convert.--replace-files>``
: Replace the `.rst` files by their `.md` equivalent,
  rather than writing a new `.md` file next to the old `.rst` one.

You can read the full list of options in
{doc}``the `rst2myst` documentation <rst-to-myst:cli>``.

## How to enable optional syntax

Some reStructuredText syntax will require you to enable certain MyST plugins.
For example, to write [reST definition lists], you need to add a
`myst_enable_extensions` variable to your Sphinx configuration, as follows:

```{code-block} py
:caption: conf.py
myst_enable_extensions = [
    "deflist",
]
```

You can learn more about {doc}`other MyST-Parser plugins <myst-parser:syntax/optional>`
in their documentation.

[reST definition lists]: https://docutils.sourceforge.io/docs/user/rst/quickref.html#definition-lists

## How to write reStructuredText syntax within MyST

There is a small chance that `rst2myst` does not properly understand a piece of reST syntax,
either because there is a bug in the tool
or because that syntax does not have a MyST equivalent yet.
For example, {ref}`as explained in the documentation <myst-parser:howto/autodoc>`,
the `sphinx.ext.autodoc` extension is incompatible with MyST.

Fortunately, MyST supports an `eval-rst` directive
that will parse the content as reStructuredText, rather than MyST.
For example:

````
```{eval-rst}
.. note::

   Complete MyST migration.

```
````

will produce the following result:

```{eval-rst}
.. note::

   Complete MyST migration.

```

As a result, this allows you to conduct a gradual migration,
at the expense of having heterogeneous syntax in your source files.
In any case, the HTML output will be the same.
