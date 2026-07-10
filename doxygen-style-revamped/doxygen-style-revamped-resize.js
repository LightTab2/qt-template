// Side-nav width as a viewport fraction - jQuery port (F5).
// Requires jQuery 3.7.1 loaded first; coupled to the Doxygen 1.17.0 navtree markup
// (#splitbar / #side-nav / #doc-content / #nav-path / #main-nav).
// Load-order requirement: init binds on window 'load' (NOT DOM-ready) so it runs AFTER
// stock navtree.js initResizable (also on 'load') and our #splitbar takeover + width win.
// Stock doxygen navtree.js stores the side-nav width in px (cookie 'width') and
// re-applies that same px on window resize. Two consequences this fixes:
//   1. browser zoom changes window.innerWidth but the px stays fixed, so the
//      sidebar's screen fraction drifts - we re-apply the width as a % of the
//      window on every resize/zoom so it always occupies the same share
//   2. the stock left-splitbar drag has no lower floor (its clamp only fires
//      when content gets squeezed), so dragging past the left edge yields a
//      negative width - we clamp every drag to [MIN_PX, MAX_FRAC*innerWidth]
// We take over the #splitbar drag (clone the node to drop stock listeners) and leave
// stock height handling + the right page-nav rail untouched. The low-level drag
// listeners stay native addEventListener so touchmove can use { passive: false } and
// preventDefault keeps firing during the drag (jQuery .on cannot set passive:false).
// Idempotent: the clone + replace drops stock's mousedown and a re-run re-clones the bar.

(function()
{
	'use strict'

	var STORE_KEY = 'doxygen-sidenav-frac'
	var MIN_PX = 140
	var MIN_FRAC = 0.10
	var MAX_FRAC = 0.45
	var DEFAULT_FRAC = 0.22

	function clampFrac(f)
	{
		return Math.max(MIN_FRAC, Math.min(MAX_FRAC, f))
	}

	function readFrac()
	{
		var v = NaN
		try
		{
			v = parseFloat(localStorage.getItem(STORE_KEY))
		}
		catch (e)
		{
			v = NaN
		}
		return isFinite(v) ? clampFrac(v) : DEFAULT_FRAC
	}

	function writeFrac(f)
	{
		try
		{
			localStorage.setItem(STORE_KEY, clampFrac(f))
		}
		catch (e)
		{
		}
	}

	// clamp a desired px width to the floor + the max viewport share
	function clampPx(px)
	{
		var max = window.innerWidth * MAX_FRAC
		return Math.max(MIN_PX, Math.min(px, max))
	}

	// set the side-nav width + every element stock keeps in lockstep (full-sidebar layout offsets content/footer/main-nav by marginLeft)
	function applyPx(px)
	{
		var $sidenav = $('#side-nav')
		if (!$sidenav.length)
		{
			return 0
		}
		var w = clampPx(px)
		var s = w + 'px'
		$sidenav.css('width', s)
		$('#doc-content').css('marginLeft', s)
		$('#nav-path').css('marginLeft', s)
		$('#main-nav').css('marginLeft', s)
		return w
	}

	// re-apply the stored fraction against the current viewport width
	function applyFrac()
	{
		applyPx(readFrac() * window.innerWidth)
	}

	// replace #splitbar with a clone (drops stock's mousedown) and wire a clamped drag
	function takeover()
	{
		var $bar = $('#splitbar')
		var $sidenav = $('#side-nav')
		if (!$bar.length || !$sidenav.length)
		{
			return false
		}
		var bar = $bar[0]
		var fresh = bar.cloneNode(true)
		bar.parentNode.replaceChild(fresh, bar)
		fresh.classList.add('ui-resizable-e')
		fresh.style.zIndex = 90

		function onMove(ev)
		{
			var x = ev.clientX
			if (x === undefined && ev.touches && ev.touches[0])
			{
				x = ev.touches[0].clientX
			}
			if (x === undefined)
			{
				return
			}
			// side-nav starts at viewport left, so its right edge x == width; clampPx kills negatives
			var w = applyPx(x)
			writeFrac(w / window.innerWidth)
			if (ev.cancelable)
			{
				ev.preventDefault()
			}
		}

		function onUp()
		{
			document.body.classList.remove('resizing')
			document.body.style.cursor = ''
			document.removeEventListener('mousemove', onMove)
			document.removeEventListener('touchmove', onMove)
			document.removeEventListener('mouseup', onUp)
			document.removeEventListener('touchend', onUp)
		}

		function onDown(ev)
		{
			document.body.classList.add('resizing')
			document.body.style.cursor = 'col-resize'
			document.addEventListener('mousemove', onMove)
			document.addEventListener('touchmove', onMove, { passive: false })
			document.addEventListener('mouseup', onUp)
			document.addEventListener('touchend', onUp)
			if (ev.cancelable)
			{
				ev.preventDefault()
			}
		}

		// keep the drag wiring native: jQuery .on cannot pass { passive: false }, which
		// touchmove needs for preventDefault to fire during the drag
		fresh.addEventListener('mousedown', onDown)
		fresh.addEventListener('touchstart', onDown, { passive: false })
		return true
	}

	function init()
	{
		if (!takeover())
		{
			return
		}
		applyFrac()
		// re-assert the fraction after any resize/zoom (stock's resize handler only preserves px).
		// off() first so a re-run of init() never stacks a second identical handler: jQuery .on
		// does NOT de-dup by fn ref (unlike the pre-port addEventListener), so the bare .on would
		// leak a listener per init() call (FC03.3 idempotency).
		$(window).off('resize', applyFrac).on('resize', applyFrac)
	}

	// expose pure helpers for headless tests; harmless in the browser
	if (typeof module !== 'undefined' && module.exports)
	{
		module.exports = { clampFrac: clampFrac, clampPx: clampPx, applyPx: applyPx, applyFrac: applyFrac, MIN_PX: MIN_PX, MIN_FRAC: MIN_FRAC, MAX_FRAC: MAX_FRAC }
	}

	// stock navtree.js runs initResizable on 'load'; bind after it so our splitbar + width win
	$(window).on('load', init)
})()
