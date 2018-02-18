// -------------------------------------------------------------------
// markItUp!
// -------------------------------------------------------------------
// Copyright (C) 2008 Jay Salvat
// http://markitup.jaysalvat.com/
// -------------------------------------------------------------------
// ReStructured Text
// http://docutils.sourceforge.net/
// http://docutils.sourceforge.net/rst.html
// -------------------------------------------------------------------
// Mark Renron <indexofire@gmail.com>
// http://www.indexofire.com
// -------------------------------------------------------------------
// Jannis Leidel <jannis@leidel.info>
// http://enn.io
// -------------------------------------------------------------------
mySettings = {
	nameSpace: 'ReST',
	onShiftEnter: {keepDefault:false, openWith:'\n\n'},
	onTab: {keepDefault:false, replaceWith:'    '},
	markupSet: [
		//{name:'Level 1 Heading', key:'1', placeHolder:'Your title Here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '#'); } },
		//{name:'Level 2 Heading', key:'2', placeHolder:'Your title here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '*'); } },
		{name:'Level 1 Heading', key:'1', placeHolder:'Your heading here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '='); } },
		{name:'Level 2 Heading', key:'2', placeHolder:'Your sub-heading here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '-'); } },
		{name:'Level 3 Heading', key:'3', placeHolder:'Your sub-sub-heading here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '^'); } },
		//{name:'Level 6 Heading', key:'6', placeHolder:'Your title here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '"'); } },
		{separator:'---------------' },
		{name:'Bold', key:'B', openWith:'**', closeWith:'**', placeHolder:'Input Your Bold Text Here...'},
		{name:'Italic', key:'I', openWith:'`', closeWith:'`', placeHolder:'Input Your Italic Text Here...'},
		{separator:'---------------' },
		{name:'Bulleted List', openWith:'* ' },
		{name:'Numeric List', openWith:function(markItUp) { return markItUp.line+'. '; } },
		{separator:'---------------' },
		{name:'Internal Link',  key:"L", openWith:':doc:`', closeWith:' <[![Heading:!:]!]>`', placeHolder:'Your text to link here...' },
        {name:'External Link',  key:"E", openWith:'`', closeWith:' <[![Url:!:http://]!]>`_', placeHolder:'Your text to link here...' },
		{separator:'---------------' },
		{name:'Picture', key:'P', openWith:'.. image:: ', placeHolder:'Link Your Images Here...'},
		{name:'Quotes', placeHolder: 'block quote text here...', replaceWith:function(markItUp) {
            return miu.indentText(markItUp);
        }},
        {name:'Code Block / Code', placeHolder:'Code here...', replaceWith:function(markItUp) {
            directive = '\n.. code-block:: python\n\n';
            indented = miu.indentText(markItUp);
            return directive + indented;
        }},
        {separator:'---------------'},
        {name:'Indent', replaceWith:function(markItUp) {
            return miu.indentText(markItUp);
        }}
	]
};


// mIu nameSpace to avoid conflict.
miu = {
	markdownTitle: function(markItUp, character) {
		heading = '';
		n = $.trim(markItUp.selection||markItUp.placeHolder).length;
		for(i = 0; i < n; i++) {
			heading += character;
		}
		return '\n'+heading + '\n';
	},
	indentText: function(markItUp) {
        text_block = markItUp.selection || markItUp.placeHolder;
        indented = '';
        $.each(text_block.split('\n'), function(idx, text) {
            indented += '    ' + text + '\n';
        });
        return indented;
    }
};
