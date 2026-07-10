// Member badges for the doxygen theme - jQuery-based (F5)
// Requires jQuery 3.7.1, loaded before this script (C1); does not feature-detect.
// Coupled to the Doxygen 1.17.0 member DOM: span.mlabels / span.mlabel,
// table.memname, td.mlabels-right, table.memberdecls, div.memitem > div.memproto.
// Three jobs in one jQuery-ready pass:
//   1. type-color existing mlabels by trimmed text -> add .mlabel-<kind> CLASS
//   2. const de-dup (F4): each const method shows `const` EXACTLY once as a badge
//   3. public badge (F4): tag public-section detail items doxygen never labels
// Idempotent on re-run - guards: colorMlabel only adds a class (re-add is a
//   no-op); const de-dup short-circuits when span.mlabel-const already exists
//   (else it colors the existing const label rather than adding one); the public
//   badge skips a memproto already holding span.mlabel-public; the fx-badge skips
//   a link already holding sup.fx-badge.
// No inline style.backgroundColor; colors come from doxygen-style-revamped-badges.css.

(function()
{
	'use strict'

	// trimmed mlabel text -> kind class suffix; `inline` hides via class
	var KIND_BY_TEXT = {
		'static': 'static',
		'protected': 'protected',
		'private': 'private',
		'slot': 'slot',
		'signal': 'signal',
		'noexcept': 'noexcept',
		'constexpr': 'constexpr',
		'friend': 'friend',
		'const': 'const',
		'inline': 'inline'
	}

	// public declaration sections with stable header ids
	var PUBLIC_SECTION_RE = /^header-pub-(methods|static-methods|attribs|static-attribs|types)$/
	var ANCHOR_RE = /memitem:([0-9a-zA-Z_:.-]+)/
	var CONST_RE = /\bconst\b/

	// add .mlabel-<kind> to one span by its trimmed text; idempotent, no inline style
	function colorMlabel(span)
	{
		if (!span)
		{
			return
		}
		var kind = KIND_BY_TEXT[span.textContent.trim()]
		if (kind)
		{
			$(span).addClass('mlabel-' + kind)
		}
	}

	// color every existing mlabel on the page
	function colorAllMlabels()
	{
		$('span.mlabel').each(function()
		{
			colorMlabel(this)
		})
	}

	// true if this memproto declares a const-qualified member (const outside params)
	// doxygen 1.17 puts the qualifier in the memname table tail cell, never a mlabel
	function isConstMemproto(memproto)
	{
		if (!memproto)
		{
			return false
		}
		var memname = $(memproto).find('table.memname').first()
		if (!memname.length)
		{
			return false
		}
		var cells = memname.find('tr > td')
		if (!cells.length)
		{
			return false
		}
		return CONST_RE.test(cells.last().text())
	}

	// existing mlabel whose trimmed text is `const`, or null; mlabels is a jQuery set
	function findConstMlabel(mlabels)
	{
		var found = null
		mlabels.find('span.mlabel').each(function()
		{
			if (!found && this.textContent.trim() === 'const')
			{
				found = this
			}
		})
		return found
	}

	// where to insert a fresh const badge: after a hidden inline, after static, else
	// front. mlabels is a jQuery set; returns a jQuery set (empty means "append")
	function constInsertRef(mlabels)
	{
		var first = mlabels.children().first()
		if (first.length && first.text().trim() === 'inline')
		{
			first = first.next()
		}
		if (first.length && first.text().trim() === 'static')
		{
			return first.next()
		}
		return first
	}

	// ensure EXACTLY one const indicator in this memproto (F4 de-dup)
	function ensureSingleConstBadge(memproto)
	{
		if (!isConstMemproto(memproto))
		{
			return
		}
		var mlabels = $(memproto).find('span.mlabels').first()
		// already added by a previous run -> never add a second
		if (mlabels.length && mlabels.find('span.mlabel-const').length)
		{
			return
		}
		// doxygen-supplied const label exists -> just color it, add nothing
		if (mlabels.length)
		{
			var existing = findConstMlabel(mlabels)
			if (existing)
			{
				$(existing).addClass('mlabel-const')
				return
			}
		}
		// no const label anywhere -> create the single badge
		var badge = $('<span>').addClass('mlabel mlabel-const').text('const')
		if (!mlabels.length)
		{
			// proto has no right-side labels cell -> graft one so the pill has a home
			var right = $(memproto).find('td.mlabels-right').first()
			if (!right.length)
			{
				return
			}
			mlabels = $('<span>').addClass('mlabels')
			right.append(mlabels)
		}
		var ref = constInsertRef(mlabels)
		if (ref.length)
		{
			ref.before(badge)
		}
		else
		{
			mlabels.append(badge)
		}
	}

	// run const de-dup for every member detail block
	function dedupConstBadges()
	{
		$('div.memitem > div.memproto').each(function()
		{
			ensureSingleConstBadge(this)
		})
	}

	// collect detail anchors from public declaration sections (skip inherited rows)
	function collectPublicAnchors()
	{
		var anchors = new Set()
		$('table.memberdecls').each(function()
		{
			var table = $(this)
			var h2 = table.find('tr.heading h2.groupheader').first()
			if (!h2.length || !PUBLIC_SECTION_RE.test(h2[0].id))
			{
				return
			}
			table.find('tr').each(function()
			{
				if (this.className.indexOf('inherit') !== -1)
				{
					return
				}
				var m = ANCHOR_RE.exec(this.className)
				if (m)
				{
					anchors.add(m[1])
				}
			})
		})
		return anchors
	}

	// append a `public` badge to one detail item's memproto; idempotent
	function badgePublicAnchor(anchor)
	{
		// anchor ids carry ':' and '.', so getElementById (not a CSS selector) is required
		var a = document.getElementById(anchor)
		if (!a)
		{
			return
		}
		var item = $(a).nextAll('div.memitem').first()
		if (!item.length)
		{
			return
		}
		var memproto = item.find('.memproto').first()
		if (!memproto.length)
		{
			return
		}
		// already badged -> do not double-add
		if (memproto.find('span.mlabel-public').length)
		{
			return
		}
		var badge = $('<span>').addClass('mlabel mlabel-public').text('public')
		var mlabels = memproto.find('span.mlabels').first()
		if (mlabels.length)
		{
			mlabels.append(badge)
		}
		else
		{
			memproto.addClass('memproto-public-only')
			memproto.append(badge)
		}
	}

	// add public badges across all public-section detail items
	function addPublicBadges()
	{
		collectPublicAnchors().forEach(badgePublicAnchor)
	}

	// true if same-page anchor id resolves to a function detail block (doxygen gives only function memprotos a td.paramname)
	function anchorIsFunction(anchorId)
	{
		// anchor ids carry ':' and '.', so getElementById (not a CSS selector) is required
		var a = document.getElementById(anchorId)
		if (!a)
		{
			return false
		}
		var item = $(a).nextAll('div.memitem').first()
		if (!item.length)
		{
			return false
		}
		var memproto = item.find('.memproto').first()
		return !!(memproto.length && memproto.find('td.paramname').length)
	}

	// append a superscript `f(x)` badge INSIDE one inline #member reference whose target is a function; idempotent, no-op otherwise
	function badgeFunctionRef(a)
	{
		// already badged -> the f(x) sup is the link's own last child
		if ($(a).find('sup.fx-badge').length)
		{
			return
		}
		var href = a.getAttribute('href')
		// #member_ convention targets same-class members -> only same-page anchors are resolvable here
		if (!href || href.charAt(0) !== '#')
		{
			return
		}
		if (!anchorIsFunction(href.slice(1)))
		{
			return
		}
		var sup = $('<sup>').addClass('fx-badge').text('f(x)')
		$(a).append(sup)
	}

	// tag inline member-function references in prose; skip the declaration-table signature cells and the memtitle permalinks
	function addFunctionRefBadges()
	{
		$('a.el[href^="#"]').each(function()
		{
			var a = this
			if ($(a).closest('h2.memtitle').length)
			{
				return
			}
			if ($(a).closest('td.memItemLeft, td.memItemRight').length)
			{
				return
			}
			badgeFunctionRef(a)
		})
	}

	function run()
	{
		colorAllMlabels()
		dedupConstBadges()
		addPublicBadges()
		addFunctionRefBadges()
	}

	// expose pure helpers for headless unit tests; harmless in the browser
	if (typeof module !== 'undefined' && module.exports)
	{
		module.exports = {
			colorMlabel: colorMlabel,
			isConstMemproto: isConstMemproto,
			ensureSingleConstBadge: ensureSingleConstBadge,
			collectPublicAnchors: collectPublicAnchors,
			badgePublicAnchor: badgePublicAnchor,
			anchorIsFunction: anchorIsFunction,
			badgeFunctionRef: badgeFunctionRef,
			addFunctionRefBadges: addFunctionRefBadges,
			run: run
		}
	}

	jQuery(run)
})()
