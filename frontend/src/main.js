import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import App from './App.vue'
import router from './router'
import axios from 'axios'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

// 处理 ResizeObserver 错误
const debounce = (fn, delay) => {
    let timeoutId
    return (...args) => {
        clearTimeout(timeoutId)
        timeoutId = setTimeout(() => fn.apply(this, args), delay)
    }
}

// 检查是否为ResizeObserver相关错误
const isResizeObserverError = (error) => {
    if (!error) return false
    const errorString = error.message || error.toString()
    return errorString.includes('ResizeObserver') ||
           errorString.includes('ResizeObserver loop completed') ||
           errorString.includes('ResizeObserver loop limit exceeded')
}

const handleError = debounce((error) => {
    // 忽略空错误
    if (!error) return

    // 忽略ResizeObserver错误
    if (isResizeObserverError(error)) {
        return
    }

    // 记录其他错误
    console.error('Application Error:', error)
}, 250)

// 全局错误处理
window.addEventListener('error', (event) => {
    if (event && event.error) {
        handleError(event.error)
    }
})

// Promise错误处理
window.addEventListener('unhandledrejection', (event) => {
    if (event && event.reason) {
        handleError(event.reason)
    }
})

// 创建Vue应用实例
const app = createApp(App)

// 全局错误处理器
app.config.errorHandler = (err) => {
    handleError(err)
}

// 注册所有图标
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
    app.component(key, component)
}

// 配置Element Plus
app.use(ElementPlus, {
    size: 'default',
    zIndex: 3000,
    locale: zhCn,
})

app.use(router)

// 配置axios
axios.defaults.baseURL = process.env.VUE_APP_API_URL || 'http://localhost:8000'
app.config.globalProperties.$axios = axios

app.mount('#app') 