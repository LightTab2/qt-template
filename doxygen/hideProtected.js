document.addEventListener('DOMContentLoaded', function() 
{
    var groupHeaders = document.querySelectorAll('.groupheader')

    groupHeaders.forEach(function(h2)
    {
        var splitContent = h2.innerHTML.split('\n')
        if (h2.nextElementSibling && h2.nextElementSibling.nextElementSibling && h2.nextElementSibling.nextElementSibling.nextElementSibling && h2.nextElementSibling.nextElementSibling.nextElementSibling.className === 'memitem')
        {
            var nextSibling = h2
            while (nextSibling.nextElementSibling && nextSibling.nextElementSibling.nextElementSibling && nextSibling.nextElementSibling.nextElementSibling.nextElementSibling && nextSibling.nextElementSibling.nextElementSibling.nextElementSibling.className === 'memitem')
            {
                nextSibling = nextSibling.nextElementSibling.nextElementSibling.nextElementSibling
                if (h2.textContent === 'Constructor and Destructor' || h2.textContent === 'Functions' || h2.textContent === 'Members' || h2.textContent === 'Variables')
                {
                    const spanElements = nextSibling.querySelectorAll('.mlabel')
                    spanElements.forEach(spanElement =>
                    {
                        if (spanElement.textContent === 'protected')
                            nextSibling.style = 'display: none !important;'
                    })
                }
            }
        }
    })
})
