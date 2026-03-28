<template>
  <div id="app" class="app-shell">
    <div class="app-aurora"></div>
    <div class="app-grid"></div>
    <nav class="navbar">
      <div class="nav-brand">
        <div class="brand-emblem">PS</div>
        <div class="brand-copy">
          <h1 class="logo">PINN-Solve</h1>
          <p class="brand-subtitle">{{ locale === 'zh' ? '偏微分方程求解工作台' : 'Physics-Informed PDE Studio' }}</p>
        </div>
        <span class="version">v0.2.0</span>
      </div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">
          <span class="icon">01</span>
          {{ t('nav.config') }}
        </router-link>
        <router-link to="/monitor" class="nav-link">
          <span class="icon">02</span>
          {{ t('nav.monitor') }}
        </router-link>
        <router-link to="/results" class="nav-link">
          <span class="icon">03</span>
          {{ t('nav.results') }}
        </router-link>
        <router-link to="/history" class="nav-link">
          <span class="icon">04</span>
          {{ t('nav.history') }}
        </router-link>
      </div>
      <div class="nav-right">
        <button @click="toggleLocale" class="lang-btn">
          {{ locale === 'zh' ? 'EN' : '中文' }}
        </button>
      </div>
    </nav>
    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { i18n } from './locales'

const locale = computed(() => i18n.locale)
const t = (key) => i18n.t(key)

const toggleLocale = () => {
  i18n.setLocale(locale.value === 'zh' ? 'en' : 'zh')
}
</script>

<style>
:root {
  --bg-base: #07111f;
  --bg-elevated: rgba(10, 22, 40, 0.82);
  --bg-panel: rgba(14, 30, 54, 0.76);
  --bg-panel-strong: rgba(16, 35, 62, 0.94);
  --bg-soft: rgba(130, 197, 255, 0.08);
  --line-soft: rgba(122, 176, 231, 0.16);
  --line-strong: rgba(122, 176, 231, 0.32);
  --text-main: #eff6ff;
  --text-soft: #9cb3ce;
  --text-dim: #7186a4;
  --accent: #57b8ff;
  --accent-strong: #8be1ff;
  --accent-warm: #ffb36b;
  --success: #6df0b7;
  --danger: #ff8f8f;
  --shadow-lg: 0 24px 80px rgba(0, 0, 0, 0.34);
  --radius-xl: 28px;
  --radius-lg: 22px;
  --radius-md: 16px;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html {
  scroll-behavior: smooth;
}

body {
  font-family: 'Avenir Next', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background:
    radial-gradient(circle at top left, rgba(87, 184, 255, 0.16), transparent 30%),
    radial-gradient(circle at 85% 15%, rgba(255, 179, 107, 0.12), transparent 24%),
    linear-gradient(180deg, #08111d 0%, #0a1528 42%, #08101d 100%);
  color: var(--text-main);
  overflow-x: hidden;
}

a {
  color: inherit;
}

button,
input,
select,
textarea {
  font: inherit;
}

#app {
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  position: relative;
}

.app-aurora,
.app-grid {
  position: fixed;
  inset: 0;
  z-index: -1;
  pointer-events: none;
}

.app-aurora {
  background:
    radial-gradient(circle at 15% 18%, rgba(87, 184, 255, 0.18), transparent 0 30%),
    radial-gradient(circle at 80% 24%, rgba(255, 179, 107, 0.12), transparent 0 20%),
    radial-gradient(circle at 72% 74%, rgba(139, 225, 255, 0.11), transparent 0 24%);
  filter: blur(20px);
}

.app-grid {
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 72px 72px;
  mask-image: linear-gradient(180deg, rgba(0, 0, 0, 0.66), transparent 88%);
}

.navbar {
  width: min(1440px, calc(100% - 32px));
  margin: 18px auto 0;
  background: rgba(7, 17, 31, 0.72);
  backdrop-filter: blur(18px);
  border: 1px solid var(--line-soft);
  border-radius: 999px;
  padding: 0.95rem 1.1rem 0.95rem 1.4rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.22);
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  min-width: 0;
}

.brand-emblem {
  width: 44px;
  height: 44px;
  display: grid;
  place-items: center;
  border-radius: 14px;
  font-size: 0.9rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  color: #06111f;
  background: linear-gradient(135deg, var(--accent-strong), var(--accent-warm));
  box-shadow: 0 12px 30px rgba(87, 184, 255, 0.28);
}

.logo {
  font-size: 1.15rem;
  line-height: 1.1;
  font-weight: 800;
  letter-spacing: 0.04em;
  color: var(--text-main);
}

.brand-copy {
  min-width: 0;
}

.brand-subtitle {
  margin-top: 0.2rem;
  color: var(--text-dim);
  font-size: 0.76rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.version {
  margin-left: 0.35rem;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 179, 107, 0.24);
  background: rgba(255, 179, 107, 0.1);
  color: #ffd5ad;
  font-size: 0.72rem;
  font-weight: 700;
}

.nav-links {
  display: flex;
  gap: 0.45rem;
  padding: 0.2rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.03);
}

.nav-link {
  color: var(--text-soft);
  text-decoration: none;
  padding: 0.7rem 1rem;
  border-radius: 999px;
  transition: all 0.28s ease;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  border: 1px solid transparent;
  position: relative;
  font-weight: 600;
}

.nav-link:hover {
  color: var(--text-main);
  background: rgba(87, 184, 255, 0.08);
  border-color: rgba(87, 184, 255, 0.14);
}

.nav-link.router-link-active {
  color: #07111f;
  background: linear-gradient(135deg, var(--accent-strong), var(--accent));
  border-color: transparent;
  box-shadow: 0 10px 24px rgba(87, 184, 255, 0.24);
}

.icon {
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  opacity: 0.8;
}

.nav-right {
  display: flex;
  align-items: center;
}

.lang-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--line-soft);
  color: var(--text-main);
  padding: 0.7rem 1rem;
  border-radius: 999px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.28s ease;
}

.lang-btn:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--line-strong);
}

.container {
  width: min(1440px, calc(100% - 32px));
  margin: 24px auto 0;
  padding: 0 0 32px;
}

.page-shell {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-hero,
.surface-card {
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), transparent),
    var(--bg-elevated);
  border: 1px solid var(--line-soft);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
  backdrop-filter: blur(18px);
}

.page-hero {
  padding: 28px;
}

.surface-card {
  padding: 24px;
}

.section-kicker {
  display: inline-flex;
  align-items: center;
  gap: 0.55rem;
  margin-bottom: 0.9rem;
  padding: 0.32rem 0.8rem;
  border-radius: 999px;
  background: rgba(87, 184, 255, 0.08);
  border: 1px solid rgba(87, 184, 255, 0.16);
  color: var(--accent-strong);
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.page-title {
  font-size: clamp(2rem, 3vw, 3.4rem);
  line-height: 0.98;
  letter-spacing: -0.04em;
  color: var(--text-main);
}

.page-subtitle {
  margin-top: 0.9rem;
  color: var(--text-soft);
  max-width: 760px;
  line-height: 1.7;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 14px;
}

.metric-tile {
  padding: 16px 18px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.metric-tile-label {
  display: block;
  color: var(--text-dim);
  font-size: 0.78rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.metric-tile-value {
  display: block;
  margin-top: 0.55rem;
  color: var(--text-main);
  font-size: 1.35rem;
  font-weight: 700;
}

@media (max-width: 1120px) {
  .navbar {
    width: min(100%, calc(100% - 24px));
    border-radius: 28px;
    flex-wrap: wrap;
    gap: 14px;
  }

  .nav-links {
    order: 3;
    width: 100%;
    justify-content: space-between;
    overflow-x: auto;
  }

  .container {
    width: min(100%, calc(100% - 24px));
  }
}

@media (max-width: 720px) {
  .navbar {
    padding: 1rem;
  }

  .nav-brand {
    width: 100%;
  }

  .brand-subtitle {
    display: none;
  }

  .version {
    margin-left: auto;
  }

  .nav-links {
    gap: 0.35rem;
    justify-content: flex-start;
  }

  .nav-link {
    min-width: max-content;
  }

  .page-hero,
  .surface-card {
    padding: 18px;
    border-radius: 22px;
  }
}
</style>
