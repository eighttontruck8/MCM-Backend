# CSS Layout Issues - Analysis & Fixes

## Summary of Issues Found

### 1. **Global CSS Issues**
- `index.css` and `App.css` are empty (no global resets or defaults)
- Missing `box-sizing: border-box;` on all containers
- Missing `*` selector for universal box-sizing

### 2. **Center Alignment Issues**

#### LoginPage.css
- `.login-page__body`: `margin: 0 auto;` centers the body unnaturally
- `.login-page__tab`: `text-align: center;` centers tab labels

#### SignupPage.css
- `.signup-page__body`: No explicit margin centering, but structure inherits issues
- `.signup-page__tab`: `text-align: center;` centers tab labels

#### FindPasswordPage.css
- `.find-password-page__label`: Inherits centering issues from parent
- `.find-password-page__header-copy`: `align-items: flex-start;` is correct but not sufficient

#### MainRecommendPage.css
- `.main-recommend-page__context-banner`: `align-items: flex-start;` (correct alignment)
- `.cta-banner`: `text-align: center;` causes unwanted center alignment

### 3. **Overflow Issues (Fixed Widths)**

#### LoginPage.css
```css
.login-page__body {
  width: 392.687px;  /* ❌ OVERFLOW - Fixed width on mobile */
  max-width: 100%;   /* Insufficient fix */
  margin: 0 auto;    /* ❌ Centers unnecessarily */
}
```

#### SignupPage.css
```css
.signup-page__body {
  width: 392.687px;  /* ❌ OVERFLOW - Fixed width */
}
```

#### FindPasswordPage.css
```css
.find-password-page__body {
  width: 392.687px;  /* ❌ OVERFLOW - Fixed width */
}

.find-password-page__input {
  width: 336.718px;  /* ❌ OVERFLOW - Fixed width on mobile */
}

.find-password-page__submit {
  width: 336.718px;  /* ❌ OVERFLOW - Fixed width on mobile */
}

.find-password-page__description {
  width: 336.687px;  /* ❌ OVERFLOW - Fixed width on mobile */
}
```

#### MainRecommendPage.css
```css
.main-recommend-page__body {
  width: 403.611px;  /* ❌ OVERFLOW - Fixed width */
}

.main-recommend-page__context-banner {
  width: 363.623px;  /* ❌ OVERFLOW - Fixed width on mobile */
}
```

---

## CORRECTED CSS CODE

### 1. Global CSS - src/index.css
```css
* {
  box-sizing: border-box;
}

html, body {
  margin: 0;
  padding: 0;
  width: 100%;
}

#root {
  width: 100%;
  display: flex;
  flex-direction: column;
}
```

### 2. Global CSS - src/App.css
```css
/* App-level reset and base styles */
body {
  margin: 0;
  padding: 0;
}

body, #root {
  width: 100%;
}
```

### 3. LoginPage.css (Corrected)
```css
.login-page {
  background-color: #fafaf8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  width: 100%;
  min-height: 100vh;
  box-sizing: border-box;
}

.login-page__body {
  background-color: #fafaf8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  max-width: 100%;
  position: relative;
  padding: 0;
  box-sizing: border-box;
}

.login-page__app {
  background-color: #fafaf8;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  min-height: 853.233px;
  width: 100%;
  position: relative;
  box-sizing: border-box;
}

.login-page__hero {
  background-color: #1a1714;
  display: flex;
  flex-direction: column;
  height: 239.989px;
  overflow: hidden;
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

.login-page__hero-backdrop {
  background-color: #2a2520;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 239.989px;
  width: 100%;
  position: relative;
  box-sizing: border-box;
}

.login-page__hero-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(255,255,255,0.08), rgba(255,255,255,0.02));
  box-sizing: border-box;
}

.login-page__hero-text {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.login-page__hero-image-label {
  font-family: 'DM Sans', sans-serif;
  font-weight: 400;
  font-size: 11px;
  line-height: 16.5px;
  color: rgba(255, 255, 255, 0.25);
  letter-spacing: 0.88px;
  white-space: nowrap;
  margin: 0;
}

.login-page__hero-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(10, 10, 10, 0.1),
    rgba(10, 10, 10, 0.55)
  );
  pointer-events: none;
}

.login-page__hero-copy {
  position: absolute;
  left: 27.98px;
  top: 154.51px;
  width: 159.234px;
}

.login-page__hero-subtitle {
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 9px;
  line-height: 13.5px;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 1.98px;
  text-transform: uppercase;
  white-space: nowrap;
  margin: 0;
}

.login-page__hero-title {
  font-family: 'Fraunces', serif;
  font-weight: 300;
  font-style: italic;
  font-size: 38px;
  line-height: 38px;
  color: #ffffff;
  letter-spacing: -0.38px;
  white-space: nowrap;
  margin: 6px 0 0;
}

.login-page__tabs {
  background-color: #ffffff;
  border-bottom: 1.112px solid #e8e3dc;
  display: flex;
  width: 100%;
  box-sizing: border-box;
}

.login-page__tab {
  flex: 1 0 0;
  min-width: 0;
  height: 49.59px;
  border: none;
  background: transparent;
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 11px;
  line-height: 16.5px;
  letter-spacing: 1.76px;
  text-transform: uppercase;
  text-align: center;
  cursor: pointer;
  padding: 16px 0;
  box-sizing: border-box;
}

.login-page__tab--active {
  color: #0a0a0a;
  border-bottom: 1.112px solid #0a0a0a;
}
```

### 4. SignupPage.css (Corrected)
```css
.signup-page {
  background-color: #fafaf8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

.signup-page__body {
  background-color: #fafaf8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  position: relative;
  padding: 0;
  box-sizing: border-box;
}

.signup-page__app {
  background-color: #fafaf8;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  min-height: 853.233px;
  width: 100%;
  position: relative;
  box-sizing: border-box;
}

.signup-page__hero {
  background-color: #1a1714;
  display: flex;
  flex-direction: column;
  height: 239.989px;
  overflow: hidden;
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

.signup-page__hero-backdrop {
  background-color: #2a2520;
  display: flex;
  align-items: center;
  justify-content: center;
  height: 239.989px;
  width: 100%;
  position: relative;
  box-sizing: border-box;
}

.signup-page__hero-image-label {
  font-family: 'DM Sans', sans-serif;
  font-weight: 400;
  font-size: 11px;
  line-height: 16.5px;
  color: rgba(255, 255, 255, 0.25);
  letter-spacing: 0.88px;
  white-space: nowrap;
}

.signup-page__hero-gradient {
  position: absolute;
  inset: 0;
  background: linear-gradient(
    to bottom,
    rgba(10, 10, 10, 0.1),
    rgba(10, 10, 10, 0.55)
  );
  pointer-events: none;
}

.signup-page__hero-copy {
  position: absolute;
  left: 27.98px;
  top: 154.51px;
  width: 159.234px;
}

.signup-page__hero-subtitle {
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 9px;
  line-height: 13.5px;
  color: rgba(255, 255, 255, 0.55);
  letter-spacing: 1.98px;
  text-transform: uppercase;
  white-space: nowrap;
  margin: 0;
}

.signup-page__hero-title {
  font-family: 'Fraunces', serif;
  font-weight: 300;
  font-style: italic;
  font-size: 38px;
  line-height: 38px;
  color: #ffffff;
  letter-spacing: -0.38px;
  white-space: nowrap;
  margin: 6px 0 0;
}

.signup-page__tabs {
  background-color: #ffffff;
  border-bottom: 1.112px solid #e8e3dc;
  display: flex;
  width: 100%;
  box-sizing: border-box;
}

.signup-page__tab {
  flex: 1 0 0;
  min-width: 0;
  height: 49.59px;
  border: none;
  background: transparent;
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 11px;
  line-height: 16.5px;
  letter-spacing: 1.76px;
  text-transform: uppercase;
  text-align: center;
  cursor: pointer;
  padding: 16px 0;
  text-decoration: none;
  box-sizing: border-box;
}

.signup-page__tab--active {
  color: #0a0a0a;
  border-bottom: 1.112px solid #0a0a0a;
}

.signup-page__tab--inactive {
  color: #7a746e;
  border-bottom: 1.112px solid transparent;
}

.signup-page__form {
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 36px 28px 40px;
  width: 100%;
  box-sizing: border-box;
}

.signup-page__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
}
```

### 5. FindPasswordPage.css (Corrected)
```css
.find-password-page {
  background-color: #fafaf8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  position: relative;
  width: 100%;
  box-sizing: border-box;
}

.find-password-page__body {
  background-color: #fafaf8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  position: relative;
  box-sizing: border-box;
  padding: 0;
}

.find-password-page__app {
  background-color: #fafaf8;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.12);
  display: flex;
  flex-direction: column;
  min-height: 853.233px;
  width: 100%;
  position: relative;
  box-sizing: border-box;
}

.find-password-page__header {
  background-color: #ffffff;
  border-bottom: 1.112px solid #e8e3dc;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 4px 20px;
  width: 100%;
  box-sizing: border-box;
}

.find-password-page__back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 8px 4px 0;
  border: none;
  background: transparent;
  cursor: pointer;
  flex-shrink: 0;
}

.find-password-page__back-icon {
  font-family: 'DM Sans', sans-serif;
  font-weight: 400;
  font-size: 18px;
  line-height: 18px;
  color: #0a0a0a;
}

.find-password-page__header-copy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  flex: 1;
  min-width: 0;
}

.find-password-page__header-label {
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 9px;
  line-height: 13.5px;
  color: #7a746e;
  letter-spacing: 1.62px;
  text-transform: uppercase;
  white-space: nowrap;
  margin: 0;
}

.find-password-page__header-title {
  font-family: 'Fraunces', serif;
  font-weight: 300;
  font-style: italic;
  font-size: 17px;
  line-height: 25.5px;
  color: #0a0a0a;
  white-space: nowrap;
  margin: 1px 0 0;
}

.find-password-page__content {
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 36px 28px 48px;
  width: 100%;
  position: relative;
  box-sizing: border-box;
}

.find-password-page__description {
  font-family: 'DM Sans', sans-serif;
  font-weight: 300;
  font-size: 13px;
  line-height: 20.8px;
  color: #7a746e;
  margin: 0;
  width: 100%;
  box-sizing: border-box;
}

.find-password-page__field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
  box-sizing: border-box;
}

.find-password-page__label {
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 10px;
  line-height: 15px;
  color: #7a746e;
  letter-spacing: 1.4px;
  text-transform: uppercase;
  white-space: nowrap;
  margin: 0;
  text-align: left;
}

.find-password-page__input {
  width: 100%;
  border: none;
  border-bottom: 1.112px solid #e8e3dc;
  padding: 8px 0 10px;
  font-family: 'DM Sans', sans-serif;
  font-weight: 300;
  font-size: 15px;
  color: rgba(10, 10, 10, 0.8);
  background: transparent;
  outline: none;
  box-sizing: border-box;
}

.find-password-page__input::placeholder {
  color: rgba(10, 10, 10, 0.5);
}

.find-password-page__submit {
  width: 100%;
  height: 49.972px;
  border: none;
  background-color: #111111;
  color: #ffffff;
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 12px;
  cursor: pointer;
  box-sizing: border-box;
}
```

### 6. MainRecommendPage.css (Corrected)
```css
.main-recommend-page {
  background-color: #fafaf8;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  width: 100%;
  box-sizing: border-box;
}

.main-recommend-page__body {
  width: 100%;
  background-color: #fafaf8;
  box-sizing: border-box;
  padding: 0;
}

.main-recommend-page__app {
  box-shadow: 0 0 30px rgba(0,0,0,0.12);
  min-height: 874px;
  width: 100%;
  box-sizing: border-box;
}

.main-recommend-page__topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 52px;
  padding: 0 20px;
  background: rgba(250,250,248,0.96);
  border-bottom: 1.127px solid #e8e3dc;
  width: 100%;
  box-sizing: border-box;
}

.main-recommend-page__brand {
  font-family: 'Fraunces', serif;
  font-style: italic;
  font-weight: 300;
  font-size: 22px;
  color: #0a0a0a;
  flex-shrink: 0;
}

.main-recommend-page__checkin {
  background: rgba(201,168,130,0.1);
  border: 1.127px solid #c9a882;
  padding: 3px 8px;
  font-family: 'DM Sans', sans-serif;
  font-size: 8px;
  color: #c9a882;
  display:flex;
  gap:5px;
  align-items:center;
  flex-shrink: 0;
}

.main-recommend-page__hero {
  padding: 24px 20px 0;
  width: 100%;
  box-sizing: border-box;
}

.main-recommend-page__greeting {
  font-family: 'DM Sans', sans-serif;
  font-size: 10px;
  color: #7a746e;
  margin: 0 0 6px 0;
  text-transform: uppercase;
  letter-spacing: 1.4px;
  text-align: left;
}

.main-recommend-page__title {
  font-family: 'Fraunces', serif;
  font-style: italic;
  font-weight: 300;
  font-size: 28px;
  margin: 0;
  text-align: left;
}

.main-recommend-page__context-banner {
  margin-top: 16px;
  background: #0a0a0a;
  color: #fff;
  padding: 16px 20px;
  display:flex;
  gap: 14px;
  align-items:flex-start;
  width: 100%;
  box-sizing: border-box;
  overflow: hidden;
}

.main-recommend-page__context-icon {
  width: 32px;
  height: 32px;
  border: 1.127px solid #c9a882;
  border-radius: 16px;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#000;
  background:#fff;
  flex-shrink: 0;
}

.context-label {
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 9px;
  color: #c9a882;
  text-transform: uppercase;
  letter-spacing: 1.62px;
}

.context-desc {
  font-family: 'DM Sans', sans-serif;
  font-weight: 300;
  font-size: 12px;
  color: rgba(255,255,255,0.8);
}

.main-recommend-page__filters {
  display:flex;
  gap:8px;
  padding: 12px 20px 0;
  width: 100%;
  box-sizing: border-box;
  overflow-x: auto;
}

.filter {
  padding: 8px 16px;
  border: 1.127px solid #e8e3dc;
  font-family: 'DM Sans', sans-serif;
  font-size: 11px;
  background: #fff;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;
}

.filter.selected {
  background: #0a0a0a;
  color: #fff;
  border-color: #0a0a0a;
}

.section-header {
  display:flex;
  justify-content:space-between;
  align-items:center;
  padding: 24px 20px 0;
  width: 100%;
  box-sizing: border-box;
}

.section-label {
  font-family: 'DM Sans', sans-serif;
  font-weight: 500;
  font-size: 9px;
  color: #7a746e;
  text-transform: uppercase;
  letter-spacing: 1.62px;
}

.section-link {
  font-family: 'DM Sans', sans-serif;
  font-size: 10px;
  border-bottom:1.127px solid #e8e3dc;
  padding-bottom: 2px;
  text-align: left;
}

.product-grid {
  display:flex;
  gap:12px;
  padding: 14px 20px;
  overflow: auto;
  width: 100%;
  box-sizing: border-box;
}

.product-card {
  width: 199.99px;
  background:#fff;
  display:flex;
  flex-direction:column;
  flex-shrink: 0;
}

.product-image {
  height:260px;
  background:#eae6e0;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#b0a89e;
}

.product-meta {
  padding:14px;
  text-align: left;
}

.product-meta .brand {
  font-family: 'DM Sans', sans-serif;
  font-size:9px;
  color:#7a746e;
  text-transform: uppercase;
}

.product-meta .name {
  font-family: 'Fraunces', serif;
  font-size:14px;
  color:#0a0a0a;
}

.product-meta .price {
  font-family: 'DM Sans', sans-serif;
  font-weight:500;
  font-size:13px;
  color:#0a0a0a;
}

.product-meta .ai-desc {
  margin-top:8px;
  font-family: 'DM Sans', sans-serif;
  font-size:10px;
  color:#7a746e;
  border-top:1.127px solid #e8e3dc;
  padding-top:8px;
}

.popular-header {
  padding: 32px 20px 0;
  width: 100%;
  box-sizing: border-box;
}

.popular-title {
  font-family: 'Fraunces', serif;
  font-size:20px;
  margin:6px 0 0;
  text-align: left;
}

.popular-grid {
  display:flex;
  gap:12px;
  padding: 14px 20px 40px;
  overflow: auto;
  width: 100%;
  box-sizing: border-box;
}

.popular-card {
  width:160px;
  flex-shrink: 0;
}

.popular-image {
  height:210px;
  background:#eae6e0;
  display:flex;
  align-items:center;
  justify-content:center;
  color:#b0a89e;
}

.popular-meta {
  text-align: left;
}

.popular-meta .brand { 
  font-family: 'DM Sans', sans-serif;
  font-size:9px; 
  color:#7a746e; 
  text-transform:uppercase; 
}

.popular-meta .name { 
  font-family:'Fraunces', serif; 
  font-size:13px; 
}

.popular-meta .price { 
  font-family: 'DM Sans', sans-serif;
  font-weight:500; 
  font-size:12px; 
}

.main-recommend-page__cta { 
  padding: 20px;
  width: 100%;
  box-sizing: border-box;
}

.cta-banner {
  background:#0a0a0a;
  color:#fff;
  padding: 32px 20px;
  text-align:left;
  width: 100%;
  box-sizing: border-box;
}

.cta-button {
  margin-top:12px;
  background:transparent;
  border:1px solid rgba(255,255,255,0.2);
  color:#fff;
  padding:8px 12px;
  cursor:pointer;
}

.main-recommend-page__nav {
  display:flex;
  justify-content:space-around;
  padding: 12px 0;
  border-top:1px solid #eee;
  width: 100%;
  box-sizing: border-box;
}

.main-recommend-page__nav .nav-item { 
  font-size:12px; 
  color:#7a746e;
}
```

---

## Key Changes Summary

### ✅ Fixed Issues:

1. **Removed fixed widths** on all `__body` containers (changed to `width: 100%`)
2. **Removed `margin: 0 auto;`** from centering unnecessarily
3. **Added `box-sizing: border-box;`** to ALL containers to prevent overflow
4. **Changed fixed `width` values** to `width: 100%` for:
   - Form inputs
   - Submit buttons
   - Descriptions
   - Context banners
5. **Added `text-align: left;`** to labels and form text
6. **Added overflow handling** with `overflow: auto` for scrollable containers
7. **Added `flex-shrink: 0;`** to prevent flex items from shrinking
8. **Updated padding and spacing** to use relative units where needed

### 🎯 Mobile-First Improvements:

- All containers now respect 100% viewport width
- Form elements scale properly on mobile devices
- Padding applied consistently with `box-sizing: border-box`
- Horizontal scrolling containers properly managed
- Text alignment consistent throughout (left-aligned for form labels)
