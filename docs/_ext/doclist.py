from docutils import nodes
from sphinx.util.docutils import SphinxDirective


class MyListDirective(SphinxDirective):
    has_content = True

    def run(self):
        docname = self.content[0]
        doc = self.state.document.settings.env.get_doctree(docname)

        definition_list = nodes.definition_list()

        paragraphs = [p for p in doc.traverse() if isinstance(p, nodes.paragraph)]
        if not paragraphs:
            return []

        paragraph = paragraphs[0]
        content = paragraph.astext()
        sentences = content.split(".")[:2]

        text = ". ".join(sentences)

        builder = self.state.document.settings.env.app.builder
        refuri = builder.get_relative_uri(
            self.state.document.settings.env.docname, docname
        )

        # import ipdb; ipdb.set_trace()

        title = doc.next_node(nodes.title)
        if title:
            link = nodes.reference("", "")
            link["refdocname"] = docname
            link["refuri"] = refuri
            link.append(nodes.Text(title.astext()))

        para = nodes.paragraph()
        para += nodes.Text(text)

        definition_list += nodes.definition_list_item(
            "Test2", nodes.term("", "", link), nodes.definition("", para)
        )

        return [definition_list]


def setup(app):
    app.add_directive("doclist", MyListDirective)
    return {"parallel_read_safe": True}
