// Tint bare C++ operators/punctuation in code fragments - jQuery-based (F5)
// Requires jQuery 3.7.1, loaded before this script (C1); does not feature-detect.
// Coupled to the Doxygen 1.17.0 fragment DOM: div.fragment, .line, <pre>.
// Doxygen wraps keywords/strings/comments in spans but leaves ( ) & * = as bare
// text between tokens; wrap each in a .codepunct span so doxygen-style-revamped-badges.css colors
// them via --fragment-punct. Only bare text on a code line is touched, never the
// text inside string/comment/keyword spans or <a> links. jQuery has no text-node
// primitive, so the inner splitting stays vanilla (createTreeWalker + fragment);
// only the outer div.fragment selection runs on jQuery.
// Idempotent on re-run: a text node already inside a span.codepunct is skipped.

(function()
{
	'use strict'

	var PUNCT_RE = /[()&*=]/

	// split one bare text node, wrapping each punctuation char in span.codepunct
	function wrapTextNode(node)
	{
		var text = node.nodeValue
		if (!PUNCT_RE.test(text))
		{
			return
		}
		var frag = document.createDocumentFragment()
		var last = 0
		for (var i = 0; i < text.length; i++)
		{
			if (!PUNCT_RE.test(text[i]))
			{
				continue
			}
			if (i > last)
			{
				frag.appendChild(document.createTextNode(text.slice(last, i)))
			}
			var span = document.createElement('span')
			span.className = 'codepunct'
			span.textContent = text[i]
			frag.appendChild(span)
			last = i + 1
		}
		if (last < text.length)
		{
			frag.appendChild(document.createTextNode(text.slice(last)))
		}
		node.parentNode.replaceChild(frag, node)
	}

	// collect then wrap bare text directly on a .line or inside <pre>; skip ours
	function processFragment(frag)
	{
		var bareNodes = []
		var walker = document.createTreeWalker(frag, NodeFilter.SHOW_TEXT, null)
		var node = walker.nextNode()
		while (node)
		{
			var parent = node.parentNode
			// already wrapped by a prior run -> leave it alone (idempotent)
			if (parent.classList && parent.classList.contains('codepunct'))
			{
				node = walker.nextNode()
				continue
			}
			var bLineText = parent.classList && parent.classList.contains('line')
			var bPreText = parent.tagName === 'PRE'
			if (bLineText || bPreText)
			{
				bareNodes.push(node)
			}
			node = walker.nextNode()
		}
		bareNodes.forEach(wrapTextNode)
	}

	function run()
	{
		$('div.fragment').each(function()
		{
			processFragment(this)
		})
	}

	// expose for headless tests; harmless in the browser
	if (typeof module !== 'undefined' && module.exports)
	{
		module.exports = { run: run, processFragment: processFragment }
	}

	jQuery(run)
})()
