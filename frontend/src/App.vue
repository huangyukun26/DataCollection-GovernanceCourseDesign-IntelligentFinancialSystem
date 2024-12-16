<template>
  <el-container class="app-wrapper">
    <el-aside width="200px">
      <el-menu
        router
        :default-active="$route.path"
        class="el-menu-vertical"
      >
        <el-menu-item index="/invoices">
          <el-icon><Receipt /></el-icon>
          <span>发票管理</span>
        </el-menu-item>
        <el-menu-item index="/upload">
          <el-icon><Upload /></el-icon>
          <span>发票上传</span>
        </el-menu-item>
        <el-menu-item index="/bank-statements">
          <el-icon><Money /></el-icon>
          <span>银行流水管理</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header>
        <div class="header-title">智慧金融数据采集系统</div>
      </el-header>
      <el-main>
        <router-view></router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { Receipt, Upload, Money } from '@element-plus/icons-vue'
</script>

<style>
.app-wrapper {
  height: 100vh;
}

.el-aside {
  background-color: #304156;
  color: #fff;
}

.el-menu {
  border-right: none;
}

.el-header {
  background-color: #fff;
  color: #333;
  line-height: 60px;
  border-bottom: 1px solid #dcdfe6;
}

.header-title {
  font-size: 18px;
  font-weight: bold;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style> 