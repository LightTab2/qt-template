// Light/dark toggle - jQuery port (mirrors doxygen-style-revamped-badges.js).
// Requires jQuery 3.7.1 loaded first; coupled to the Doxygen 1.17.0 title-area markup
// (#projectrow / #projectlogo / #MSearchBox). Toggle target is <html>: dark mode =
// class "dark-mode", light = its absence. Choice persists in
// localStorage['doxygen-darkmode'] as 'dark' or 'light'; with no saved choice the mode
// follows prefers-color-scheme. The top-level apply(preferredMode()) call stays at
// module scope, before the deferred DOM-ready entry and pre-jQuery in <head>, so the
// first paint - including the OS-dark path the inline anti-flash snippet does not cover
// - never flashes. Idempotent: the #darkmode-toggle guard stops a re-run adding a
// second button.

(function()
{
	'use strict'

	var KEY = 'doxygen-darkmode'

	// persisted choice if valid, else the OS preference -> 'dark' | 'light'
	function preferredMode()
	{
		var saved = null
		try
		{
			saved = localStorage.getItem(KEY)
		}
		catch (e)
		{
			// storage blocked -> fall through to the system preference
		}
		if (saved === 'dark' || saved === 'light')
		{
			return saved
		}
		var bPrefersDark = typeof window !== 'undefined' && window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
		return bPrefersDark ? 'dark' : 'light'
	}

	// reflect a mode onto <html>
	function apply(mode)
	{
		document.documentElement.classList.toggle('dark-mode', mode === 'dark')
	}

	// persist a mode; tolerate storage being unavailable
	function persist(mode)
	{
		try
		{
			localStorage.setItem(KEY, mode)
		}
		catch (e)
		{
			// persistence unavailable -> toggle still works for this session
		}
	}

	// sun when dark (click -> light), moon when light (click -> dark)
	function glyph(mode)
	{
		return mode === 'dark' ? '☀' : '☾'
	}

	// build the toggle button, place it, wire its click; idempotent (DOM-dependent, on $)
	function run()
	{
		// already built by a prior run -> never add a second button
		if ($('#darkmode-toggle').length)
		{
			return
		}
		var mode = preferredMode()
		apply(mode)
		var $btn = $('<button>')
			.attr({ id: 'darkmode-toggle', type: 'button', 'aria-label': 'Toggle dark mode' })
			.text(glyph(mode))
		// place left of the logo: a new table cell before #projectlogo so the button sits
		// before the logo, vertically centred to the project-row (logo) height via css
		var $logo = $('#projectlogo')
		if ($logo.length && $logo.parent().length)
		{
			var $cell = $('<td>').attr('id', 'darkmode-cell').append($btn)
			$logo.before($cell)
			// new cell adds a column; widen search row to span it so search bar stays full width
			var $searchCell = $('#MSearchBox').closest('td')
			if ($searchCell.length)
			{
				$searchCell.prop('colSpan', $logo.parent().children().length)
			}
		}
		else
		{
			// no project row (e.g. search-only pages) -> fall back to titlearea/search/body
			var host = document.getElementById('titlearea') || document.getElementById('MSearchBox') || document.body
			$(host).append($btn)
		}
		$btn.on('click', function()
		{
			var next = document.documentElement.classList.contains('dark-mode') ? 'light' : 'dark'
			apply(next)
			persist(next)
			$btn.text(glyph(next))
		})
	}

	// apply ASAP (head) before DOM is ready, to reduce the first-paint flash
	if (typeof document !== 'undefined')
	{
		apply(preferredMode())
	}

	// expose pure helpers for headless tests; harmless in the browser
	if (typeof module !== 'undefined' && module.exports)
	{
		module.exports = { run: run, preferredMode: preferredMode, apply: apply }
	}

	// button insertion needs the DOM, so defer run to jQuery DOM-ready
	jQuery(run)
})()
