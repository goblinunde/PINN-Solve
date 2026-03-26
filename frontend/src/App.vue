<template>
  <div id="app" class="tech-theme">
    <nav class="navbar">
      <div class="nav-left">
        <h1 class="logo">
          <span class="logo-icon">⚡</span>
          PINN-Solve
          <span class="version">v0.2.0</span>
        </h1>
      </div>
      <div class="nav-links">
        <router-link to="/" class="nav-link">
          <span class="icon">⚙️</span>
          {{ t('nav.config') }}
        </router-link>
        <router-link to="/monitor" class="nav-link">
          <span class="icon">📊</span>
          {{ t('nav.monitor') }}
        </router-link>
        <router-link to="/results" class="nav-link">
          <span class="icon">🎯</span>
          {{ t('nav.results') }}
        </router-link>
        <router-link to="/history" class="nav-link">
          <span class="icon">📜</span>
          {{ t('nav.history') }}
        </router-link>
      </div>
      <div class="nav-right">
        <button @click="toggleLocale" class="lang-btn">
          {{ locale === 'zh' ? 'EN' : '中文' }}
        </button>
      </div>
    </nav>
    <div class="tech-bg"></div>
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
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
  background: #0a0e27;
  color: #e0e0e0;
  overflow-x: hidden;
}

.tech-theme {
  min-height: 100vh;
  position: relative;
}

.tech-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: 
    linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%),
    radial-gradient(circle at 20% 50%, rgba(0, 150, 255, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(138, 43, 226, 0.1) 0%, transparent 50%);
  z-index: -1;
}

.tech-bg::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(0, 150, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 150, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: grid-move 20s linear infinite;
}

@keyframes grid-move {
  0% { transform: translate(0, 0); }
  100% { transform: translate(50px, 50px); }
}

.navbar {
  background: rgba(10, 14, 39, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(0, 150, 255, 0.3);
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 4px 20px rgba(0, 150, 255, 0.1);
}

.nav-left {
  display: flex;
  align-items: center;
}

.logo {
  font-size: 1.5rem;
  font-weight: 700;
  background: linear-gradient(135deg, #00d4ff 0%, #0096ff 50%, #8a2be2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logo-icon {
  font-size: 1.8rem;
  filter: drop-shadow(0 0 10px rgba(0, 212, 255, 0.5));
}

.version {
  font-size: 0.7rem;
  background: rgba(0, 150, 255, 0.2);
  padding: 0.2rem 0.5rem;
  border-radius: 12px;
  border: 1px solid rgba(0, 150, 255, 0.4);
  color: #00d4ff;
}

.nav-links {
  display: flex;
  gap: 0.5rem;
}

.nav-link {
  color: #a0a0a0;
  text-decoration: none;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  border: 1px solid transparent;
  position: relative;
  overflow: hidden;
}

.nav-link::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(0, 150, 255, 0.2), transparent);
  transition: left 0.5s;
}

.nav-link:hover::before {
  left: 100%;
}

.nav-link:hover {
  color: #00d4ff;
  border-color: rgba(0, 150, 255, 0.5);
  background: rgba(0, 150, 255, 0.1);
  transform: translateY(-2px);
}

.nav-link.router-link-active {
  color: #00d4ff;
  background: rgba(0, 150, 255, 0.15);
  border-color: rgba(0, 150, 255, 0.6);
  box-shadow: 0 0 20px rgba(0, 150, 255, 0.3);
}

.icon {
  font-size: 1.2rem;
}

.nav-right {
  display: flex;
  align-items: center;
}

.lang-btn {
  background: rgba(0, 150, 255, 0.1);
  border: 1px solid rgba(0, 150, 255, 0.4);
  color: #00d4ff;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.3s;
}

.lang-btn:hover {
  background: rgba(0, 150, 255, 0.2);
  border-color: rgba(0, 150, 255, 0.6);
  box-shadow: 0 0 15px rgba(0, 150, 255, 0.4);
  transform: scale(1.05);
}

.container {
  max-width: 1400px;
  margin: 2rem auto;
  padding: 0 2rem;
}
</style>
