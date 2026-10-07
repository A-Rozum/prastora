# CSS layering
CSS lives in css/ by layer: core.css; themes/ (custom properties only); components/; pages/ (CSS of one page, named as the page; a folder's index takes the folder name; a demo site's shared styles take the site's name); dev/ (development aids). Pages link only what they use, in that order.
Why: the cascade order is the architecture; a page that links more than it uses or in another order breaks predictability.
