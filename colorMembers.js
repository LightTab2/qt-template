const Access = {
  PUBLIC: 0,
  PROTECTED: 1,
  PRIVATE: 2
}

const const_regex = /\bconst\b/

document.addEventListener('DOMContentLoaded', function() 
{
    var groupHeaders = document.querySelectorAll('.groupheader')
    var types = false
    var slots = false
    var static_functions = false
    var functions = false
    var static_members = false
    var members = false

    groupHeaders.forEach(function(h2)
    {
        var splitContent = h2.innerHTML.split('\n')
        if (splitContent[1] === 'Public Types:' || splitContent[1] === 'Protected Types:' || splitContent[1] === 'Private Types:') 
        {
            if (types)
            {
                h2.style.display = 'none'
            }
            else
            {
                h2.innerHTML = splitContent[0] + '\nTypes:'
                types = true
            }
        } 
        else if (splitContent[1] === 'Public Slots:' || splitContent[1] === 'Protected Slots:' || splitContent[1] === 'Private Slots:') 
        {
            if (slots)
            {
                h2.style.display = 'none'
            }
            else
            {
                h2.innerHTML = splitContent[0] + '\nSlots:'
                slots = true
            }
        }
        else if (splitContent[1] === 'Static Public Functions:' || splitContent[1] === 'Static Protected Functions:' || splitContent[1] === 'Static Private Functions:') 
        {
            if (static_functions)
            {
                h2.style.display = 'none'
            }
            else
            {
                h2.innerHTML = splitContent[0] + '\nStatic Functions:'
                static_functions = true
            }
        }
        else if (splitContent[1] === 'Public Functions:' || splitContent[1] === 'Protected Functions:' || splitContent[1] === 'Private Functions:') 
        {
            if (functions)
            {
                h2.style.display = 'none'
            }
            else
            {
                h2.innerHTML = splitContent[0] + '\nFunctions:'
                functions = true
            }
        }
        else if (splitContent[1] === 'Static Public Members:' || splitContent[1] === 'Static Protected Members:' || splitContent[1] === 'Static Private Members:') 
        {
            if (static_members)
            {
                h2.style.display = 'none'
            }
            else
            {
                h2.innerHTML = splitContent[0] + '\nStatic Members:'
                static_members = true
            }
        }
        else if (splitContent[1] === 'Public Members:' || splitContent[1] === 'Protected Members:' || splitContent[1] === 'Private Members:') 
        {
            if (members)
            {
                h2.style.display = 'none'
            }
            else
            {
                h2.innerHTML = splitContent[0] + '\nMembers:'
                members = true
            }
        }
        else if (h2.nextElementSibling && h2.nextElementSibling.nextElementSibling && h2.nextElementSibling.nextElementSibling.nextElementSibling && h2.nextElementSibling.nextElementSibling.nextElementSibling.className === 'memitem')
        {
            var nextSibling = h2
            while (nextSibling.nextElementSibling && nextSibling.nextElementSibling.nextElementSibling && nextSibling.nextElementSibling.nextElementSibling.nextElementSibling && nextSibling.nextElementSibling.nextElementSibling.nextElementSibling.className === 'memitem')
            {
                nextSibling = nextSibling.nextElementSibling.nextElementSibling.nextElementSibling
                const tdElements = nextSibling.querySelectorAll('td.mlabels-left td:not(.memname)')
                tdElements.forEach(td =>
                {
                    if (const_regex.test(td.innerHTML)) 
                    {
                        const spanElement = document.createElement('span')
                        spanElement.style.backgroundColor = 'var(--const-mlabel-color)'
                        spanElement.textContent = 'const'
                        spanElement.className = 'mlabel'
                        const mlabels = nextSibling.querySelector('span.mlabels')
                        td.innerHTML = td.innerHTML.replace(const_regex, '<span style="color: var(--const-color);">$&</span>')
                        var firstChild = mlabels.firstChild 
                        if (!firstChild)
                            mlabels.appendChild(spanElement)
                        else
                        {
                            if (firstChild.textContent === 'inline')
                                firstChild = firstChild.nextElementSibling 

                            if (!firstChild)
                                mlabels.appendChild(spanElement)
                            else if (firstChild.textContent === 'static')
                            {
                                if (firstChild.nextElementSibling)
                                    mlabels.insertBefore(spanElement, firstChild.nextElementSibling)
                                else
                                    mlabels.appendChild(spanElement)
                            }
                            else
                                mlabels.insertBefore(spanElement, firstChild)
                        }
                    }
                })
                
                if (h2.textContent === 'Types')
                    nextSibling.querySelector('.memproto').style.backgroundColor = 'var(--types-memproto-color)'
                else if (h2.textContent === 'Friends')
                {
                    const spanElements = nextSibling.querySelectorAll('.mlabel')
                    spanElements.forEach(spanElement =>
                    {
                        if (spanElement.textContent.trim() === 'friend')
                            spanElement.style.backgroundColor = 'var(--friends-mlabel-color)'
                    })

                    nextSibling.querySelector('.memproto').style.backgroundColor = 'var(--friends-memproto-color)'
                }
                else if (h2.textContent === 'Constructor and Destructor' || h2.textContent === 'Functions' || h2.textContent === 'Members' || h2.textContent === 'Variables')
                {
                    nextSibling.querySelector('.memproto').style.backgroundColor = 'var(--public-memproto-color)'
                    const spanElements = nextSibling.querySelectorAll('.mlabel')
                    spanElements.forEach(spanElement =>
                    {
                        if (spanElement.textContent === 'static')
                        {
                            spanElement.style.backgroundColor = 'var(--static-mlabel-color)'
                            nextSibling.querySelector('.memname').style.color = 'var(--static-memproto-color)'
                        }
                        else if (spanElement.textContent === 'protected')
                        {
                            spanElement.style.backgroundColor = 'var(--protected-mlabel-color)'
                            nextSibling.querySelector('.memproto').style.backgroundColor = 'var(--protected-memproto-color)'
                        }
                        else if (spanElement.textContent === 'private')
                        {
                            spanElement.style.backgroundColor = 'var(--private-mlabel-color)'
                            nextSibling.querySelector('.memproto').style.backgroundColor = 'var(--private-memproto-color)'
                        }
                        else if (spanElement.textContent === 'slot')
                        {
                            spanElement.style.backgroundColor = 'var(--slots-mlabel-color)'
                            nextSibling.querySelector('.memname').style.color = 'var(--slots-memproto-color)'
                        }
                        else if (spanElement.textContent === 'signal')
                        {
                            spanElement.style.backgroundColor = 'var(--signals-mlabel-color)'
                            nextSibling.querySelector('.memname').style.color = 'var(--signals-memproto-color)'
                        }
                        else if (spanElement.textContent === 'noexcept')
                        {
                            spanElement.style.backgroundColor = 'var(--noexcept-mlabel-color)'
                        }
                        else if (spanElement.textContent === 'constexpr')
                        {
                            spanElement.style.backgroundColor = 'var(--const-mlabel-color)'
                        }
                        else if (spanElement.textContent === 'inline')
                        {
                            spanElement.style.display = 'none'
                        }
                    })
                }
            }
        }
    })
})
