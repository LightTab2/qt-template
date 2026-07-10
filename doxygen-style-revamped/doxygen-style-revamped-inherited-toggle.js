// Collapsible "Additional Inherited Members" section - jQuery port (F5).
// Requires jQuery 3.7.1 loaded first; coupled to the Doxygen 1.17.0 memberdecls
// markup: Doxygen renders the heading (id "header-inherited") in a <tr class="heading">
// inside a memberdecls table, and every following sibling row belongs to it. Make the
// whole block one collapsible unit, collapsed by default, with button semantics +
// aria-expanded. Idempotent: the inherited-toggle class guard means a re-run never
// rebinds or double-toggles.

(function()
{
	'use strict'

	function run()
	{
		var $heading = $('#header-inherited')
		if (!$heading.length)
		{
			return
		}
		// already wired by a prior run -> stop
		if ($heading.hasClass('inherited-toggle'))
		{
			return
		}
		var $headingRow = $heading.closest('tr')
		if (!$headingRow.length)
		{
			return
		}
		// every element row after the heading row belongs to the inherited block
		var $rows = $headingRow.nextAll()

		var bExpanded = false

		// reflect state into the DOM + ARIA
		function apply()
		{
			if (bExpanded)
			{
				$rows.css('display', '').removeAttr('aria-hidden')
			}
			else
			{
				$rows.css('display', 'none').attr('aria-hidden', 'true')
			}
			$heading.toggleClass('inherited-collapsed', !bExpanded)
			$heading.toggleClass('inherited-expanded', bExpanded)
			$heading.attr('aria-expanded', bExpanded ? 'true' : 'false')
		}

		function toggle()
		{
			bExpanded = !bExpanded
			apply()
		}

		// button semantics on the heading
		$heading.addClass('inherited-toggle').attr({ role: 'button', tabindex: '0' })
		$heading.on('click', toggle)
		$heading.on('keydown', function(e)
		{
			if (e.key === 'Enter' || e.key === ' ' || e.key === 'Spacebar')
			{
				e.preventDefault()
				toggle()
			}
		})

		apply()
	}

	// expose for headless tests; harmless in the browser
	if (typeof module !== 'undefined' && module.exports)
	{
		module.exports = { run: run }
	}

	// the collapsible needs the DOM, so defer run to jQuery DOM-ready
	jQuery(run)
})()
