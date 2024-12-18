<template>
  <div class="bank-statement-upload">
    <el-form :model="form" label-width="120px">
      <el-form-item label="银行类型">
        <el-select v-model="form.bankType" placeholder="请选择银行类型">
          <el-option label="北京银行" value="beijing_bank" />
          <!-- 后续添加其他银行选项 -->
        </el-select>
      </el-form-item>
      
      <el-form-item label="流水文件">
        <el-upload
          class="upload-demo"
          action="/api/bank-statements/upload"
          :headers="headers"
          :data="{ bank_type: form.bankType }"
          :on-success="handleSuccess"
          :on-error="handleError"
          :before-upload="beforeUpload"
          accept="image/*"
          :limit="1"
        >
          <el-button type="primary">选择文件</el-button>
          <template #tip>
            <div class="el-upload__tip">
              只能上传jpg/png文件，且不超过10MB
            </div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>
    
    <!-- 上传结果展示 -->
    <div v-if="uploadResult" class="upload-result">
      <h3>上传结果</h3>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="账号">
          {{ uploadResult.account_number }}
        </el-descriptions-item>
        <el-descriptions-item label="交易笔数">
          {{ uploadResult.transaction_count }}
        </el-descriptions-item>
        <el-descriptions-item label="总收入">
          {{ formatAmount(uploadResult.total_income) }}
        </el-descriptions-item>
        <el-descriptions-item label="总支出">
          {{ formatAmount(uploadResult.total_expense) }}
        </el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'BankStatementUpload',
  setup() {
    const form = reactive({
      bankType: 'beijing_bank'
    })
    
    const uploadResult = ref(null)
    
    const headers = {
      // 添加需要的请求头
    }
    
    const handleSuccess = (response) => {
      ElMessage.success('上传成功')
      uploadResult.value = response.data
    }
    
    const handleError = (error) => {
      ElMessage.error(`上传失败: ${error.message || '未知错误'}`)
    }
    
    const beforeUpload = (file) => {
      const isImage = file.type.startsWith('image/')
      const isLt10M = file.size / 1024 / 1024 < 10
      
      if (!isImage) {
        ElMessage.error('只能上传图片文件!')
        return false
      }
      if (!isLt10M) {
        ElMessage.error('文件大小不能超过 10MB!')
        return false
      }
      return true
    }
    
    const formatAmount = (amount) => {
      return amount ? `¥${amount.toFixed(2)}` : '¥0.00'
    }
    
    return {
      form,
      headers,
      uploadResult,
      handleSuccess,
      handleError,
      beforeUpload,
      formatAmount
    }
  }
}
</script>

<style scoped>
.bank-statement-upload {
  padding: 20px;
}

.upload-result {
  margin-top: 20px;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
}

.el-upload__tip {
  color: #909399;
  font-size: 12px;
  margin-top: 7px;
}
</style> 