# Prastora

Prastora is an experimental CSS toolkit for layouts that scale as a whole.

Responsive layouts usually adapt to the screen by rearranging their elements: columns stretch, text rewraps and elements shift relative to each other. But with so many devices, browsers and browser versions, side panels and extensions in use, the visible area of a page can take an enormous number of width and height combinations – and ideally each one needs checking.

Prastora builds the composition differently. It replaces this zoo of possible states with a few stable modes for different classes of device – phone, desktop, large display, plus a lighter variant for low windows – in which the composition depends, in essence, on a single parameter. This gives the developer a clear picture of how elements will be positioned and proportioned in each case, without extensive testing.

Within each mode the page scales as a whole, much like a vector image: as elements change size, their proportions and relative positions stay the same. This makes possible techniques that fluid layouts cannot deliver, or cannot deliver reliably – graphics locked to text, compositions that cross section boundaries and more. The page ends up working as a single, coherent image.

Prastora also covers the ground common to frameworks of this kind: grids and navigation in plain HTML and CSS, a typographic scale, a baseline that evens out browser differences, a dark theme out of the box and so on.

Examples: https://a-rozum.github.io/prastora/

Getting started: https://a-rozum.github.io/prastora/start.html · Templates: https://a-rozum.github.io/prastora/templates/ · Components: https://a-rozum.github.io/prastora/components/ · Why another CSS framework: https://a-rozum.github.io/prastora/why.html
