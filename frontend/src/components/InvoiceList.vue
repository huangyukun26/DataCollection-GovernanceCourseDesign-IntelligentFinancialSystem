<template>
  <div class="list-container">
    <el-card class="list-card">
      <template #header>
        <div class="card-header">
          <h2>发票列表</h2>
          <el-button type="primary" @click="refreshList">刷新</el-button>
        </div>
      </template>

      <!-- 搜索栏 -->
      <div class="search-bar">
        <el-input
          v-model="searchQuery"
          placeholder="搜索发票号码或销售方"
          class="search-input"
          clearable
          @clear="handleSearch"
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><search /></el-icon>
          </template>
        </el-input>
      </div>

      <!-- 发票列表表格 -->
      <el-table
        :data="filteredInvoices"
        style="width: 100%"
        v-loading="loading"
        border
        :lazy="true"
        :max-height="500"
        table-layout="fixed"
        size="default"
        :default-sort="{ prop: 'invoice_date', order: 'descending' }"
      >
        <el-table-column prop="invoice_code" label="发票代码" width="180" show-overflow-tooltip />
        <el-table-column prop="invoice_number" label="发票号码" width="180" show-overflow-tooltip />
        <el-table-column prop="invoice_date" label="开票日期" width="120" sortable />
        <el-table-column prop="total_amount" label="金额" width="120" align="right">
          <template #default="scope">
            ¥{{ scope.row.total_amount }}
          </template>
        </el-table-column>
        <el-table-column prop="seller" label="销售方" show-overflow-tooltip min-width="200" />
        <el-table-column prop="buyer" label="购买方" show-overflow-tooltip min-width="200" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              link
              @click="viewInvoice(scope.row)"
            >
              查看
            </el-button>
            <el-button
              type="danger"
              link
              @click="handleDelete(scope.row)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页器 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 发票详情对话框 -->
    <el-dialog
      v-model="dialogVisible"
      title="发票详情"
      width="70%"
      :destroy-on-close="true"
      :close-on-click-modal="false"
      @open="handleDialogOpen"
    >
      <template #default>
        <div v-loading="dialogLoading">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="发票代码">
              {{ currentInvoice?.invoice_code }}
            </el-descriptions-item>
            <el-descriptions-item label="发票号码">
              {{ currentInvoice?.invoice_number }}
            </el-descriptions-item>
            <el-descriptions-item label="开票日期">
              {{ currentInvoice?.invoice_date }}
            </el-descriptions-item>
            <el-descriptions-item label="金额">
              ¥{{ currentInvoice?.total_amount }}
            </el-descriptions-item>
            <el-descriptions-item label="税额">
              ¥{{ currentInvoice?.tax_amount }}
            </el-descriptions-item>
            <el-descriptions-item label="价税合计">
              ¥{{ calculateTotal(currentInvoice?.total_amount, currentInvoice?.tax_amount) }}
            </el-descriptions-item>
            <el-descriptions-item label="销售方" :span="2">
              {{ currentInvoice?.seller }}
            </el-descriptions-item>
            <el-descriptions-item label="购买方" :span="2">
              {{ currentInvoice?.buyer }}
            </el-descriptions-item>
          </el-descriptions>

          <!-- 商品明细表格 -->
          <div class="items-table" style="margin-top: 20px;">
            <h3>商品明细</h3>
            <el-table
              ref="itemsTable"
              :data="currentInvoice?.items || []"
              style="width: 100%"
              border
              stripe
              :lazy="true"
              :max-height="300"
              table-layout="fixed"
              size="default"
              v-if="dialogVisible"
            >
              <el-table-column prop="item_name" label="商品名称" min-width="200" show-overflow-tooltip />
              <el-table-column prop="quantity" label="数量" width="100" align="right">
                <template #default="scope">
                  {{ scope.row.quantity }} {{ scope.row.unit }}
                </template>
              </el-table-column>
              <el-table-column prop="unit_price" label="单价" width="120" align="right">
                <template #default="scope">
                  ¥{{ formatNumber(scope.row.unit_price) }}
                </template>
              </el-table-column>
              <el-table-column prop="amount" label="金额" width="120" align="right">
                <template #default="scope">
                  ¥{{ formatNumber(scope.row.amount) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </template>
    </el-dialog>

    <!-- 删除确认对话框 -->
    <el-dialog
      v-model="deleteDialogVisible"
      title="确认删除"
      width="30%"
    >
      <span>确定要删除这张发票吗？此操作不可恢复。</span>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="deleteDialogVisible = false">取消</el-button>
          <el-button type="danger" @click="confirmDelete">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import axios from 'axios'

const loading = ref(false)
const invoices = ref([])
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const dialogVisible = ref(false)
const currentInvoice = ref(null)
const deleteDialogVisible = ref(false)
const invoiceToDelete = ref(null)
const dialogLoading = ref(false)
const itemsTable = ref(null)

// 获取发票列表
const fetchInvoices = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/invoices/list/')
    if (response.data.status === 'success') {
      invoices.value = response.data.data
      total.value = response.data.data.length
    } else {
      ElMessage.error('获取发票列表失败')
    }
  } catch (error) {
    ElMessage.error('获取发票列表失败：' + error.message)
  } finally {
    loading.value = false
  }
}

// 刷新列表
const refreshList = () => {
  fetchInvoices()
}

// 搜索处理
const handleSearch = () => {
  currentPage.value = 1
}

// 格式化数字
const formatNumber = (num) => {
  if (!num) return '0.00'
  return Number(num).toFixed(2)
}

// 计算价税���计
const calculateTotal = (amount, tax) => {
  const total = (Number(amount) || 0) + (Number(tax) || 0)
  return formatNumber(total)
}

// 处理对话框打开事件
const handleDialogOpen = () => {
  nextTick(() => {
    if (itemsTable.value) {
      itemsTable.value.doLayout()
    }
  })
}

// 查看发票详情
const viewInvoice = async (invoice) => {
  dialogLoading.value = true
  dialogVisible.value = true
  
  try {
    // 获取发票详细信息，包括商品明细
    const response = await axios.get(`/api/invoices/${invoice.id}`)
    if (response.data.status === 'success') {
      currentInvoice.value = response.data.data
    } else {
      ElMessage.error('获取发票详情失败')
    }
  } catch (error) {
    ElMessage.error('获取发票详情失败：' + error.message)
  } finally {
    dialogLoading.value = false
  }
}

// 处理删除
const handleDelete = (invoice) => {
  invoiceToDelete.value = invoice
  deleteDialogVisible.value = true
}

// 确认删除
const confirmDelete = async () => {
  try {
    const response = await axios.delete(`/api/invoices/${invoiceToDelete.value.id}`)
    if (response.data.status === 'success') {
      ElMessage.success('删除成功')
      deleteDialogVisible.value = false
      refreshList()
    } else {
      ElMessage.error('删除失败')
    }
  } catch (error) {
    ElMessage.error('删除失败：' + error.message)
  }
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}

const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 计算过滤后的发票列表
const filteredInvoices = computed(() => {
  let filtered = invoices.value
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(invoice => 
      invoice.invoice_number.toLowerCase().includes(query) ||
      invoice.seller.toLowerCase().includes(query)
    )
  }
  
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filtered.slice(start, end)
})

// 组件挂载时获取发票列表
onMounted(() => {
  fetchInvoices()
})
</script>

<style scoped>
.list-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}

.list-card {
  background: #fff;
  border-radius: 8px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-bar {
  margin-bottom: 20px;
}

.search-input {
  width: 300px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style> 