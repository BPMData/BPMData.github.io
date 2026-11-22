# The "click this next" glow

A faint gold light on a button's left edge that slowly breathes in and out. It first shipped on OverHeard's **Pop out captions** button ([BPMData/OverHeard#61](https://github.com/BPMData/OverHeard/pull/61)). It's meant to work like the glow in a video game that says "this is the thing you want next," without being loud about it.

---

## 1. How it's built in OverHeard

There are two parts: a gold icon, and a glow drawn by a pseudo-element on top of the button's normal background.

### The CSS (`src/index.css`)

```css
/* "Click me" glow: a faint gold light at the left edge that slowly breathes in and out */
.oh-beckon {
  position: relative;   /* anchors the ::after layer */
  overflow: hidden;     /* keeps the glow inside the button's corners */
}
.oh-beckon::after {
  content: '';
  position: absolute;
  inset: 0;
  pointer-events: none; /* clicks pass straight through to the button */
  background: linear-gradient(90deg,
    rgba(245, 158, 11, 0.32) 0%,   /* amber, for light mode */
    rgba(245, 158, 11, 0.12) 14%,
    transparent 32%);
  opacity: 0.25;
  animation: oh-beckon-breathe 3.6s ease-in-out infinite alternate;
}
.dark .oh-beckon::after {
  background: linear-gradient(90deg,
    rgba(250, 204, 21, 0.34) 0%,   /* brighter gold on dark navy */
    rgba(250, 204, 21, 0.12) 14%,
    transparent 32%);
}
@keyframes oh-beckon-breathe {
  from { opacity: 0.25; }
  to   { opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .oh-beckon::after { animation: none; opacity: 0.7; }  /* still visible, just not moving */
}
```

### The button (`src/header/AppHeader.tsx`)

```tsx
<button
  className={pipWindow
    ? '…green "Close Pop-out" styles…'
    : 'oh-btn oh-beckon …usual button styles…'}
>
  <PictureInPicture2 className={pipWindow ? '' : 'text-[#D97706] dark:text-[#FACC15]'} />
  …
</button>
```

### Why it's built this way

- **It's a layer, not a new background.** The glow sits on top of the existing glossy `.oh-btn` gradient, so the button still matches the rest of the toolbar. Adding `oh-beckon` to any button turns the effect on, and removing it turns it off.
- **It only animates opacity.** The browser can animate opacity without recalculating layout or repainting, so it costs almost nothing, even on old school Chromebooks.
- **It breathes; it doesn't sweep.** The first version swept a glint across the whole button every 4 seconds, which was too busy. Staying at the left edge and fading between 25% and 100% over 3.6 s each way (`alternate`) reads as "alive" without pulling attention from the lecture.
- **The colors follow the theme.** On dark navy it's bright gold, `#FACC15`. On white, gold washes out, so light mode uses amber, `#F59E0B` / `#D97706`.
- **It turns off once it's done its job.** When the pop-out opens, the button switches to its green "Close Pop-out" state and loses `oh-beckon`. The glow only shows while there's still something to do.
- **It respects reduced motion.** People with "reduce motion" turned on in their system settings see a steady glow, not nothing. The cue is still there; it just doesn't move.
- **Why gold, not purple.** Start Listening is already the big purple primary button. A second purple button would compete with it. Gold reads as "bonus, look here" and stays secondary.

---

## 2. Using it across the Over/All fleet

The idea: in every app, **at most one** control at a time glows, and it's the one that moves the person forward from where they are right now. If several things glow, it means nothing.

### Make it a shared style

- **One class name for the whole fleet:** `beckon`. Or keep `oh-beckon`: AllAboard already uses the `oh-btn-*` names, so the prefix carries over cleanly.
- **One CSS file:** copy the block above into each app's global stylesheet (OverHeard `src/index.css`, AllAboard `src/index.css`, AllHail `src/styles.css`, and wherever OverBoard keeps its global CSS). If the fleet ever gets a shared design package, this is a good first thing to move into it.
- **Theme hooks:** OverHeard switches themes with a `.dark` class on `<html>`. Apps that use another switch (`data-theme`, `prefers-color-scheme`) only need the selector on the `.dark .oh-beckon::after` rule changed.
- **The icon is part of the cue.** The glow works best with the button's icon tinted gold (amber in light mode). The glow alone is quite subtle.

### Rules so it keeps meaning something

1. **One glow per screen.** If two things need attention, the step that comes first glows. The other waits.
2. **Glow the next step, not the main action.** The main action (Start Listening, Join, Submit) already has the solid purple style. Use the glow for the step people miss: a feature they haven't found, the next item in a setup flow, or "you're ready, now do this."
3. **Stop once it's clicked.** Remove the class when the step is done (the pop-out is open, the pack has downloaded, the room is joined). A glow that never goes away turns into decoration.
4. **Consider remembering it.** For "discover this feature" glows, keep a per-browser flag in `localStorage`, such as `beckon:popout:seen`, so it stops glowing once someone has used the feature. Wrap the read in `try/catch` so school devices with blocked storage still work.
5. **Never put it on a destructive button.** Delete, Clear and End room never glow.
6. **Never rely on it alone.** The label and tooltip still have to explain the button. The glow is only a hint.

### Places it could go, per app

These are ideas to check against each app, not decisions:

- **OverHeard:**
  - **Pop out captions** (done).
  - **Start Listening** on a first visit, before captions have ever run. This one needs care, since it's already the purple primary button.
  - **Download** on a language pack offer, until the pack is installed.
- **AllAboard:**
  - The single next step in its own flow: whatever a first-time teacher or student is most likely to miss.
- **OverBoard:**
  - The step that moves a board forward, such as adding the first card or sharing the board with the class.
- **AllHail:**
  - Whichever control kicks off its main loop on a first visit.
- **Student pages** (all apps):
  - The language picker or **Join** button, when a student lands on a room link and hasn't chosen yet.

### Possible later additions

- **A `strong` version for a single moment that really matters:** a slightly brighter peak, or a gold 1px border during the peak. Use it only once per flow.
- **A slower "idle" version** (6 s or more) for features that are nice to know about but never urgent.
- **Wrapping it in a component** (React or plain JS) such as `<Beckon until={condition}>`, which adds and removes the class from app state. That keeps the "stop once clicked" rule out of every caller.
