import { createRouter, createWebHistory } from 'vue-router'
import InvoiceList from '../components/InvoiceList.vue'
import InvoiceUpload from '../components/InvoiceUpload.vue'
import BankStatementList from '../views/bank-statement/List.vue'

const routes = [
  {
    path: '/',
    redirect: '/invoices'
  },
  {
    path: '/invoices',
    name: 'InvoiceList',
    component: InvoiceList,
    meta: { title: '发票管理' }
  },
  {
    path: '/upload',
    name: 'InvoiceUpload',
    component: InvoiceUpload,
    meta: { title: '发票上传' }
  },
  {
    path: '/bank-statements',
    name: 'BankStatementList',
    component: BankStatementList,
    meta: { title: '银行流水管理' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '智慧金融数据采集系统'
  next()
})

export default router 