import { createRouter, createWebHistory } from 'vue-router'
import InvoiceUpload from '../components/InvoiceUpload.vue'
import InvoiceList from '../components/InvoiceList.vue'

const routes = [
  {
    path: '/',
    redirect: '/upload'
  },
  {
    path: '/upload',
    name: 'upload',
    component: InvoiceUpload,
    meta: {
      title: '发票上传'
    }
  },
  {
    path: '/list',
    name: 'list',
    component: InvoiceList,
    meta: {
      title: '发票列表'
    }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由标题
router.beforeEach((to, from, next) => {
  document.title = to.meta.title ? `${to.meta.title} - 智慧金融数据采集系统` : '智慧金融数据采集系统'
  next()
})

export default router 