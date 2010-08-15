SphinxDocsSettings = {
    nameSpace:          'restructuredtext',
    onShiftEnter:       {keepDefault:false, openWith:'\n\n'},
    markupSet: [
        {name:'Top-level Heading', className: 'btnHeading', key:"1", placeHolder:'Your heading here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '=') } },
        {name:'Sub-heading', className: 'btnSubheading', key:"2", placeHolder:'Your sub-heading here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '-') } },
        {name:'Sub-sub-heading', className: 'btnSubsubheading', key:"3", placeHolder:'Your sub-sub-heading here...', closeWith:function(markItUp) { return miu.markdownTitle(markItUp, '^') } },
        {separator:'---------------' },        
        {name:'Bold', className: 'btnBold', key:"B", openWith:'**', closeWith:'**'},
        {name:'Italic', className: 'btnItalic', key:"I", openWith:'*', closeWith:'*'},
        {separator:'---------------' },
        {name:'Bulleted List', className: 'btnBulletedList', openWith:'* ' },
        {name:'Numeric List', className: 'btnNumberedList', openWith:function(markItUp) {
            return markItUp.line+'. ';
        }},
        {separator:'---------------' },
        //{name:'Picture', key:"P", replaceWith:'![[![Alternative text]!]]([![Url:!:http://]!] "[![Title]!]")'},
        {name:'Internal Link', className: 'btnInternalLink', key:"L", openWith:':doc:`', closeWith:' <[![Heading:!:]!]>`', placeHolder:'Your text to link here...' },
        {name:'External Link', className: 'btnLink', key:"E", openWith:'`', closeWith:' <[![Url:!:http://]!]>`_', placeHolder:'Your text to link here...' },
        {separator:'---------------'},    
        {name:'Quotes', className: 'btnQuotes', openWith:'\t'},
        {name:'Code Block / Code', className: 'btnCode', openWith:'\n.. code-block:: python\n\t', closeWith:'\n', placeHolder:'Code here...'},
        //{separator:'---------------'},
        //{name:'Preview', call:'preview', className:"preview"}
    ]
}

// mIu nameSpace to avoid conflict.
miu = {
    markdownTitle: function(markItUp, char) {
        heading = '';
        n = $.trim(markItUp.selection||markItUp.placeHolder).length;
        for(i = 0; i < n; i++) {
            heading += char;
        }
        return '\n'+heading+'\n';
    }
}
