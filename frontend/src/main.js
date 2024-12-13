import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'

// 创建Vue应用实例
const app = createApp(App)

// 配置axios
axios.defaults.baseURL = 'http://localhost:8000'
app.config.globalProperties.$axios = axios

// 使用插件
app.use(ElementPlus)
app.use(router)

// 挂载应用
app.mount('#app') 