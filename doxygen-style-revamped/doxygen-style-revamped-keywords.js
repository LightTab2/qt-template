// Color the const qualifier in member protos - jQuery-based (F5)
// Requires jQuery 3.7.1, loaded before this script (C1); does not feature-detect.
// Coupled to the Doxygen 1.17.0 proto DOM: div.memproto td.paramtype and
// div.memproto table.memname tr > td:last-child.
// Doxygen leaves the const qualifier as bare text in td.paramtype and the
// memname tail cell (never a keyword span), so it renders in the muted proto
// color. Wrap each standalone `const` in span.const-kw so doxygen-style-revamped-badges.css tints
// it via --const-color. Scope = member protos only; never the badge pills.
// jQuery has no text-node primitive, so the inner splitting stays vanilla
// (createTreeWalker + fragment); only the outer scope selection runs on jQuery.
// Idempotent on re-run: a const already inside span.const-kw is left alone.

(function()
{
	'use strict'

	// standalone const only: not when hyphen/word-adjacent (e.g. foo-const)
	var KW_RE = /(?<![-\w])const\b/

	// split one text node, wrapping every const match in span.const-kw
	function wrapTextNode(node)
	{
		var text = node.nodeValue
		var re = new RegExp(KW_RE.source, 'g')
		if (!re.test(text))
		{
			return
		}
		re.lastIndex = 0
		var frag = document.createDocumentFragment()
		var last = 0
		var m
		while ((m = re.exec(text)) !== null)
		{
			if (m.index > last)
			{
				frag.appendChild(document.createTextNode(text.slice(last, m.index)))
			}
			var span = document.createElement('span')
			span.className = 'const-kw'
			span.textContent = m[0]
			frag.appendChild(span)
			last = m.index + m[0].length
			if (m.index === re.lastIndex)
			{
				re.lastIndex++
			}
		}
		if (last < text.length)
		{
			frag.appendChild(document.createTextNode(text.slice(last)))
		}
		node.parentNode.replaceChild(frag, node)
	}

	// wrap const in every bare text node under one scope element; skip ours (idempotent)
	function wrapConstInScope(scope)
	{
		if (!scope)
		{
			return
		}
		var bareNodes = []
		var walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, null)
		var node = walker.nextNode()
		while (node)
		{
			var parent = node.parentNode
			// already wrapped by a prior run -> leave it alone (idempotent)
			if (parent.classList && parent.classList.contains('const-kw'))
			{
				node = walker.nextNode()
				continue
			}
			if (KW_RE.test(node.nodeValue))
			{
				bareNodes.push(node)
			}
			node = walker.nextNode()
		}
		bareNodes.forEach(wrapTextNode)
	}

	function run()
	{
		$('div.memproto td.paramtype').each(function()
		{
			wrapConstInScope(this)
		})
		$('div.memproto table.memname tr > td:last-child').each(function()
		{
			wrapConstInScope(this)
		})
	}

	// expose pure helpers for headless tests; harmless in the browser
	if (typeof module !== 'undefined' && module.exports)
	{
		module.exports = { run: run, wrapConstInScope: wrapConstInScope, KW_RE: KW_RE }
	}

	jQuery(run)
})()
