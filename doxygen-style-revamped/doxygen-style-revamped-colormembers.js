// Per-access member-proto banding - jQuery-based (mirrors doxygen-style-revamped-keywords.js)
// Requires jQuery 3.7.1, loaded before this script (C1); does not feature-detect.
// Coupled to the Doxygen 1.17.0 proto DOM: div.memproto, span.mlabel, td.memname.
// Doxygen renders every member-detail proto on a uniform code-bg. The old
// qt6-template colorMembers.js tinted each proto by access (public/protected/
// private/friend) + accented signal/slot/static names. This re-adds that as
// CSS classes only (JS adds the class, doxygen-style-revamped-badges.css maps it to a palette var
// via color-mix - no inline style, the old smell). Access is read from the
// mlabel badges doxygen already emits in each proto; public has no label.
// Idempotent: a proto already bucketed (has a mp- class) is left alone.

(function()
{
	'use strict'

	// collect the mlabel badge texts inside one memproto
	function labelsOf(proto)
	{
		var out = []
		$(proto).find('span.mlabel').each(function()
		{
			out.push($(this).text().trim())
		})
		return out
	}

	// most-specific access bucket wins; public is the unlabeled default
	function accessClass(labels)
	{
		if (labels.indexOf('friend') !== -1)
		{
			return 'mp-friend'
		}
		if (labels.indexOf('private') !== -1)
		{
			return 'mp-private'
		}
		if (labels.indexOf('protected') !== -1)
		{
			return 'mp-protected'
		}
		return 'mp-public'
	}

	// tint one proto by access + accent its name for signal/slot/static (kind, not access)
	function colorProto(proto)
	{
		var $proto = $(proto)
		// already bucketed (has a mp- class) -> idempotent no-op
		if (($proto.attr('class') || '').indexOf('mp-') !== -1)
		{
			return
		}
		var labels = labelsOf(proto)
		$proto.addClass(accessClass(labels))
		var name = $proto.find('td.memname').first()
		if (!name.length)
		{
			return
		}
		if (labels.indexOf('signal') !== -1)
		{
			name.addClass('mn-signal')
		}
		else if (labels.indexOf('slot') !== -1)
		{
			name.addClass('mn-slot')
		}
		else if (labels.indexOf('static') !== -1)
		{
			name.addClass('mn-static')
		}
	}

	function run()
	{
		$('div.memproto').each(function()
		{
			colorProto(this)
		})
	}

	// expose pure helpers for headless tests; harmless in the browser
	if (typeof module !== 'undefined' && module.exports)
	{
		module.exports = { run: run, accessClass: accessClass, labelsOf: labelsOf }
	}

	jQuery(run)
})()
