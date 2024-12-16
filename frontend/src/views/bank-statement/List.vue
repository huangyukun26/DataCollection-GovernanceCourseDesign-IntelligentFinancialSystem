<template>
  <div class="bank-statement-list">
    <el-card class="box-card">
      <template #header>
        <div class="card-header">
          <span>银行流水管理</span>
          <el-button type="primary" @click="handleUpload">上传流水</el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :inline="true" :model="searchForm" class="search-form">
        <el-form-item label="账号">
          <el-input v-model="searchForm.accountNumber" placeholder="请输入账号"></el-input>
        </el-form-item>
        <el-form-item label="日期范围">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          ></el-date-picker>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="resetSearch">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 数据统计 -->
      <el-row :gutter="20" class="statistics">
        <el-col :span="6">
          <el-card shadow="hover">
            <template #header>总收入</template>
            <span class="amount income">{{ formatAmount(statistics.totalIncome) }}</span>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <template #header>总支出</template>
            <span class="amount expense">{{ formatAmount(statistics.totalExpense) }}</span>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <template #header>净额</template>
            <span class="amount" :class="statistics.netAmount >= 0 ? 'income' : 'expense'">
              {{ formatAmount(statistics.netAmount) }}
            </span>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover">
            <template #header>交易笔数</template>
            <span class="count">{{ statistics.transactionCount }}</span>
          </el-card>
        </el-col>
      </el-row>

      <!-- 批量操作按钮 -->
      <div class="batch-operations">
        <el-button
          type="danger"
          :disabled="selectedRows.length === 0"
          @click="handleBatchDelete"
        >
          批量删除
        </el-button>
      </div>

      <!-- 数据表格 -->
      <el-table
        v-loading="loading"
        :data="tableData"
        style="width: 100%"
        border
        @selection-change="handleSelectionChange"
        table-layout="fixed"
        :max-height="500"
      >
        <el-table-column type="selection" width="55"></el-table-column>
        <el-table-column prop="id" label="ID" width="80"></el-table-column>
        <el-table-column prop="accountNumber" label="账号" width="180"></el-table-column>
        <el-table-column prop="transactionDate" label="交易日期" width="180">
          <template #default="scope">
            {{ formatDate(scope.row.transaction_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="transactionType" label="交易类型" width="100">
          <template #default="scope">
            <el-tag :type="scope.row.transaction_type === '收入' ? 'success' : 'danger'">
              {{ scope.row.transaction_type }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="amount" label="金额" width="150">
          <template #default="scope">
            <span :class="scope.row.transaction_type === '收入' ? 'income' : 'expense'">
              {{ formatAmount(scope.row.amount) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="balance" label="余额" width="150">
          <template #default="scope">
            {{ formatAmount(scope.row.balance) }}
          </template>
        </el-table-column>
        <el-table-column prop="counterparty" label="交易对手方"></el-table-column>
        <el-table-column prop="description" label="交易描述"></el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="scope">
            <el-button size="small" @click="handleEdit(scope.row)">编辑</el-button>
            <el-button size="small" @click="handlePreview(scope.row)">预览</el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDelete(scope.row)"
            >删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        ></el-pagination>
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <el-dialog
      v-model="uploadDialogVisible"
      title="上传银行流水"
      width="500px"
    >
      <el-upload
        class="upload-demo"
        drag
        action="/api/bank-statements/upload/"
        :headers="{
          'Accept': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        }"
        name="file"
        :on-success="handleUploadSuccess"
        :on-error="handleUploadError"
        :before-upload="beforeUpload"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            只能上传jpg/png/pdf文件，且不超过10MB
          </div>
        </template>
      </el-upload>
    </el-dialog>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑银行流水"
      width="600px"
      :close-on-click-modal="false"
      :destroy-on-close="true"
      @closed="handleDialogClosed"
    >
      <el-form
        ref="editFormRef"
        :model="editForm"
        :rules="editRules"
        label-width="100px"
      >
        <el-form-item label="账号" prop="accountNumber">
          <el-input v-model="editForm.accountNumber"></el-input>
        </el-form-item>
        <el-form-item label="交易日期" prop="transactionDate">
          <el-date-picker
            v-model="editForm.transactionDate"
            type="datetime"
            placeholder="选择日期时间"
          ></el-date-picker>
        </el-form-item>
        <el-form-item label="交易类型" prop="transactionType">
          <el-select v-model="editForm.transactionType">
            <el-option label="收入" value="收入"></el-option>
            <el-option label="支出" value="支出"></el-option>
          </el-select>
        </el-form-item>
        <el-form-item label="金额" prop="amount">
          <el-input-number
            v-model="editForm.amount"
            :precision="2"
            :step="0.01"
          ></el-input-number>
        </el-form-item>
        <el-form-item label="余额" prop="balance">
          <el-input-number
            v-model="editForm.balance"
            :precision="2"
            :step="0.01"
          ></el-input-number>
        </el-form-item>
        <el-form-item label="交易对手方" prop="counterparty">
          <el-input v-model="editForm.counterparty"></el-input>
        </el-form-item>
        <el-form-item label="交易描述" prop="description">
          <el-input
            v-model="editForm.description"
            type="textarea"
            :rows="3"
          ></el-input>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitEdit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      title="预览"
      width="800px"
      :close-on-click-modal="false"
      :destroy-on-close="true"
      @closed="handleDialogClosed"
    >
      <div class="preview-container">
        <img :src="previewUrl" alt="银行流水单" style="width: 100%;">
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, reactive } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import axios from 'axios'

// 数据定义
const loading = ref(false)
const tableData = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)
const uploadDialogVisible = ref(false)
const editDialogVisible = ref(false)
const previewDialogVisible = ref(false)
const previewUrl = ref('')
const selectedRows = ref([])
const statistics = reactive({
  totalIncome: 0,
  totalExpense: 0,
  netAmount: 0,
  transactionCount: 0
})

// 搜索表单
const searchForm = reactive({
  accountNumber: '',
  dateRange: []
})

// 编辑表单
const editForm = reactive({
  id: null,
  accountNumber: '',
  transactionDate: '',
  transactionType: '',
  amount: 0,
  balance: 0,
  counterparty: '',
  description: ''
})

// 编辑表单校验规则
const editRules = {
  accountNumber: [
    { required: true, message: '请输入账号', trigger: 'blur' }
  ],
  transactionDate: [
    { required: true, message: '请选择交易日期', trigger: 'change' }
  ],
  transactionType: [
    { required: true, message: '请选择交易类型', trigger: 'change' }
  ],
  amount: [
    { required: true, message: '请输入金额', trigger: 'blur' }
  ]
}

// 获取数据列表
const fetchData = async () => {
  loading.value = true
  try {
    const params = {
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      account_number: searchForm.accountNumber || undefined,
      start_date: searchForm.dateRange?.[0] || undefined,
      end_date: searchForm.dateRange?.[1] || undefined
    }
    const response = await axios.get('/api/bank-statements/list/', { params })
    if (response.data.status === 'success') {
      tableData.value = response.data.data
      total.value = response.data.total
      // 获取统计数据
      const statsResponse = await axios.get('/api/bank-statements/statistics/', { params })
      if (statsResponse.data.status === 'success') {
        Object.assign(statistics, statsResponse.data.data)
      }
    } else {
      ElMessage.error('获取数据失败')
    }
  } catch (error) {
    console.error('获取数据失败:', error)
    ElMessage.error(error.response?.data?.detail || '获取数据失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchData()
}

// 重置搜索
const resetSearch = () => {
  searchForm.accountNumber = ''
  searchForm.dateRange = []
  handleSearch()
}

// 上传相关
const handleUpload = () => {
  uploadDialogVisible.value = true
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isPDF = file.type === 'application/pdf'
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isImage && !isPDF) {
    ElMessage.error('上传文件只能是图片或PDF格式!')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('上传文件大小不能超过 10MB!')
    return false
  }
  return true
}

const handleUploadSuccess = () => {
  ElMessage.success('上传成功')
  uploadDialogVisible.value = false
  fetchData()
}

const handleUploadError = () => {
  ElMessage.error('上传失败')
}

// 编辑相关
const handleEdit = (row) => {
  Object.assign(editForm, {
    id: row.id,
    accountNumber: row.account_number,
    transactionDate: row.transaction_date,
    transactionType: row.transaction_type,
    amount: row.amount,
    balance: row.balance,
    counterparty: row.counterparty,
    description: row.description
  })
  editDialogVisible.value = true
}

const submitEdit = async () => {
  try {
    await axios.put(`/api/bank-statements/${editForm.id}`, editForm)
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    fetchData()
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// 预览相关
const handlePreview = (row) => {
  previewUrl.value = row.file_path
  previewDialogVisible.value = true
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm(
    '确定要删除这条记录吗？',
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      await axios.delete(`/api/bank-statements/${row.id}`)
      ElMessage.success('删除成功')
      fetchData()
    } catch (error) {
      ElMessage.error('删除失败')
    }
  })
}

// 批量删除相关
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handleBatchDelete = () => {
  if (selectedRows.value.length === 0) {
    return
  }

  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedRows.value.length} 条记录吗？`,
    '警告',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  ).then(async () => {
    try {
      const ids = selectedRows.value.map(row => row.id)
      await axios.post('/api/bank-statements/batch-delete/', { ids: ids })
      ElMessage.success('批量删除成功')
      selectedRows.value = []
      fetchData()
    } catch (error) {
      ElMessage.error(error.response?.data?.detail || '批量删除失败')
    }
  })
}

// 分页相关
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchData()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchData()
}

// 格式化函数
const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString()
}

const formatAmount = (amount) => {
  if (amount === undefined || amount === null) return '0.00'
  return amount.toFixed(2)
}

// 对话框关闭处理
const handleDialogClosed = () => {
  // 清理相关数据
  if (!editDialogVisible.value) {
    Object.keys(editForm).forEach(key => {
      editForm[key] = ''
    })
    editForm.amount = 0
    editForm.balance = 0
  }
  if (!previewDialogVisible.value) {
    previewUrl.value = ''
  }
}

// 修改初始化
onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.bank-statement-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.search-form {
  margin-bottom: 20px;
}

.statistics {
  margin-bottom: 20px;
}

.batch-operations {
  margin-bottom: 10px;
}

.amount {
  font-size: 24px;
  font-weight: bold;
}

.income {
  color: #67C23A;
}

.expense {
  color: #F56C6C;
}

.count {
  font-size: 24px;
  font-weight: bold;
  color: #409EFF;
}

.pagination {
  margin-top: 20px;
  text-align: right;
}

.preview-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style> 