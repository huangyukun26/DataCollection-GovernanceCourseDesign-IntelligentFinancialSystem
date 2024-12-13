<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <el-container>
        <!-- 头部 -->
        <el-header height="60px">
          <div class="header-content">
            <div class="logo">
              <h1>智慧金融数据采集系统</h1>
            </div>
            <el-menu
              mode="horizontal"
              :router="true"
              :default-active="activeMenu"
            >
              <el-menu-item index="/upload">
                <el-icon><upload-filled /></el-icon>
                发票上传
              </el-menu-item>
              <el-menu-item index="/list">
                <el-icon><document /></el-icon>
                发票列表
              </el-menu-item>
            </el-menu>
          </div>
        </el-header>

        <!-- 主要内容区 -->
        <el-main>
          <router-view v-slot="{ Component }">
            <transition name="fade" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </el-main>

        <!-- 页脚 -->
        <el-footer height="60px">
          <div class="footer-content">
            <p>© 2024 智慧金融数据采集系统 v1.0.0</p>
          </div>
        </el-footer>
      </el-container>
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { UploadFilled } from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: #f0f2f5;
}

#app {
  height: 100%;
}

.app-container {
  min-height: 100vh;
}

.el-container {
  min-height: 100vh;
}

.el-header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  z-index: 1;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  height: 100%;
}

.logo {
  margin-right: 40px;
}

.logo h1 {
  margin: 0;
  font-size: 20px;
  color: #409EFF;
}

.el-main {
  padding: 20px;
  background-color: #f0f2f5;
}

.el-footer {
  background-color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.footer-content {
  text-align: center;
  color: #909399;
}

/* 路由过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style> 