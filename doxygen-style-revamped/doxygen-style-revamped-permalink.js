// Relocate the member permalink diamond into the memname - jQuery-based (mirrors doxygen-style-revamped-colormembers.js)
// Requires jQuery 3.7.1, loaded before this script (C1); does not feature-detect.
// Coupled to the Doxygen 1.17.0 member DOM: div.memitem, h2.memtitle,
// div.memproto td.memname, span.permalink.
// Doxygen emits the per-member permalink (the small diamond anchor) inside the
// h2.memtitle that precedes each memitem. The theme hides h2.memtitle, so that
// anchor - and the copy-link/navigation it carries - is lost. This moves the
// span.permalink out of the obsolete memtitle and prepends it into the first
// td.memname of the memitem, so the diamond sits in the left gutter ahead of
// the member name (doxygen-style-revamped-theme.css styles it small + muted). The move
// (not a clone) is jQuery .prepend, which relocates the existing element.
// Idempotent: a memname that already holds a permalink is left alone.

(function()
{
	'use strict'

	// the h2.memtitle that doxygen renders immediately before this memitem
	function titleOf(item)
	{
		var prev = $(item).prev()
		if (prev.is('h2.memtitle'))
		{
			return prev[0]
		}
		return null
	}

	// move the permalink diamond from the hidden memtitle into the memname gutter
	function relocate(item)
	{
		var name = $(item).find('div.memproto td.memname').first()
		// skip a memname that already holds a permalink (idempotent)
		if (!name.length || name.find('span.permalink').length)
		{
			return
		}
		var title = titleOf(item)
		if (!title)
		{
			return
		}
		var perma = $(title).find('span.permalink').first()
		if (!perma.length)
		{
			return
		}
		name.prepend(perma)
	}

	function run()
	{
		$('div.memitem').each(function()
		{
			relocate(this)
		})
	}

	// expose pure helpers for headless tests; harmless in the browser
	if (typeof module !== 'undefined' && module.exports)
	{
		module.exports = { run: run, relocate: relocate, titleOf: titleOf }
	}

	jQuery(run)
})()
