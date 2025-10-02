# PWA Icons

To complete the PWA setup, add the following icon files to the `static/` directory:

## Required Icons

1. **icon-192.png** (192x192 pixels)
   - Used for Android home screen icon
   - Should be a simple, recognizable icon (honeycomb or bee theme)

2. **icon-512.png** (512x512 pixels)
   - Used for splash screen and larger displays
   - Same design as icon-192.png, higher resolution

3. **screenshot-mobile.png** (390x844 pixels) - Optional
   - Mobile app screenshot for app stores/PWA listing
   - Shows the app in use

## Icon Design Tips

- Use the bee yellow (#f7da21) as the primary color
- Simple, clean design works best (honeycomb pattern or bee emoji)
- Ensure good contrast for visibility
- Square icons with rounded corners

## Quick Icon Generation

You can use these tools to generate PWA icons:
- https://www.pwabuilder.com/imageGenerator
- https://realfavicongenerator.net/
- Figma or Canva with honeycomb/bee templates

## Favicon

Optionally add `favicon.ico` to the static directory and reference it in index.html:
```html
<link rel="icon" type="image/x-icon" href="/favicon.ico">
```
