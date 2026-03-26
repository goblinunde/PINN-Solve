<template>
  <div id="app">
    <nav class="navbar">
      <h1>PINN-Solve</h1>
      <div class="nav-links">
        <router-link to="/">配置</router-link>
        <router-link to="/monitor">监控</router-link>
        <router-link to="/results">结果</router-link>
        <router-link to="/history">历史</router-link>
      </div>
    </nav>
    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
}

.navbar {
  background: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.nav-links a {
  color: white;
  text-decoration: none;
  margin-left: 2rem;
  transition: opacity 0.3s;
}

.nav-links a:hover {
  opacity: 0.8;
}

.container {
  max-width: 1400px;
  margin: 2rem auto;
  padding: 0 2rem;
}
</style>
