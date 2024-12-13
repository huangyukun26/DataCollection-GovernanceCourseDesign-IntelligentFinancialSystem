<template>
  <div class="upload-container">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <h2>发票上传</h2>
        </div>
      </template>
      
      <el-upload
        class="upload-area"
        drag
        :action="uploadUrl"
        :on-success="handleSuccess"
        :on-error="handleError"
        :before-upload="beforeUpload"
        :on-progress="handleProgress"
        accept="image/*"
        ref="uploadRef"
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持jpg/png格式的发票图片
          </div>
        </template>
      </el-upload>

      <!-- 上传和识别状态 -->
      <div v-if="uploadStatus.show" class="status-container">
        <el-alert
          :title="uploadStatus.message"
          :type="uploadStatus.type"
          :closable="false"
          show-icon
        />
        <el-progress 
          v-if="uploadStatus.showProgress"
          :percentage="uploadStatus.progress"
          :status="uploadStatus.progressStatus"
        />
      </div>

      <div class="preview-and-result">
        <!-- 图片预览 -->
        <div v-if="imageUrl" class="image-preview">
          <h3>发票图片</h3>
          <el-image
            :src="imageUrl"
            fit="contain"
            :preview-src-list="[imageUrl]"
          />
        </div>

        <!-- 识别结果展示 -->
        <div v-if="recognitionResult" class="recognition-result">
          <h3>识别结果</h3>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="发票代码">
              {{ recognitionResult.invoice_code }}
            </el-descriptions-item>
            <el-descriptions-item label="发票号码">
              {{ recognitionResult.invoice_number }}
            </el-descriptions-item>
            <el-descriptions-item label="开票日期">
              {{ recognitionResult.invoice_date }}
            </el-descriptions-item>
            <el-descriptions-item label="金额">
              {{ recognitionResult.total_amount }}
            </el-descriptions-item>
            <el-descriptions-item label="税额">
              {{ recognitionResult.tax_amount }}
            </el-descriptions-item>
            <el-descriptions-item label="销售方">
              {{ recognitionResult.seller }}
            </el-descriptions-item>
            <el-descriptions-item label="购买方">
              {{ recognitionResult.buyer }}
            </el-descriptions-item>
          </el-descriptions>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'

const uploadUrl = 'http://localhost:8000/api/invoices/upload/'
const recognitionResult = ref(null)
const uploadRef = ref(null)
const imageUrl = ref(null)

// 上传状态管理
const uploadStatus = ref({
  show: false,
  message: '',
  type: 'info',
  showProgress: false,
  progress: 0,
  progressStatus: ''
})

const handleProgress = (event) => {
  uploadStatus.value.show = true
  uploadStatus.value.showProgress = true
  uploadStatus.value.progress = Math.round(event.percent)
  uploadStatus.value.message = '正在上传...'
  uploadStatus.value.type = 'info'
  uploadStatus.value.progressStatus = event.percent === 100 ? '' : 'exception'
}

const handleSuccess = (response) => {
  if (response.status === 'success') {
    uploadStatus.value.message = '识别完成'
    uploadStatus.value.type = 'success'
    uploadStatus.value.progress = 100
    uploadStatus.value.progressStatus = 'success'
    
    // 设置图片预览URL
    if (response.data.image_url) {
      imageUrl.value = response.data.image_url
    }
    
    recognitionResult.value = response.data.invoice_info
    ElMessage.success('发票识别成功')
  } else {
    uploadStatus.value.message = '识别失败'
    uploadStatus.value.type = 'error'
    uploadStatus.value.progressStatus = 'exception'
    ElMessage.error(response.message || '上传失败')
  }
}

const handleError = (error) => {
  uploadStatus.value.message = '上传失败'
  uploadStatus.value.type = 'error'
  uploadStatus.value.progressStatus = 'exception'
  ElMessage.error('上传失败：' + error.message)
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isImage) {
    ElMessage.error('只能上传图片文件！')
    return false
  }
  if (!isLt10M) {
    ElMessage.error('图片大小不能超过 10MB！')
    return false
  }

  // 重置状态
  uploadStatus.value = {
    show: true,
    message: '准备上传...',
    type: 'info',
    showProgress: true,
    progress: 0,
    progressStatus: ''
  }
  
  // 创建本地预览URL
  imageUrl.value = URL.createObjectURL(file)
  
  // 清理之前的识别结果
  recognitionResult.value = null
  
  return true
}

// 组件卸载时清理本地预览URL
onUnmounted(() => {
  if (imageUrl.value && imageUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(imageUrl.value)
  }
})
</script>

<style scoped>
.upload-container {
  max-width: 1200px;
  margin: 20px auto;
  padding: 0 20px;
}

.upload-card {
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-area {
  width: 100%;
}

.status-container {
  margin: 20px 0;
}

.preview-and-result {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 20px;
}

@media (max-width: 768px) {
  .preview-and-result {
    grid-template-columns: 1fr;
  }
}

.image-preview {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 4px;
  height: fit-content;
}

.image-preview h3 {
  margin-bottom: 20px;
  color: #409EFF;
}

.image-preview :deep(.el-image) {
  width: 100%;
  max-height: 600px;
  border-radius: 4px;
  overflow: hidden;
  box-shadow: 0 2px 12px 0 rgba(0,0,0,0.1);
}

.recognition-result {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 4px;
  height: fit-content;
}

.recognition-result h3 {
  margin-bottom: 20px;
  color: #409EFF;
}

:deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
}

:deep(.el-upload) {
  width: 100%;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409EFF;
}

:deep(.el-upload__tip) {
  color: #909399;
}

:deep(.el-progress) {
  margin-top: 10px;
}

:deep(.el-alert) {
  margin-bottom: 10px;
}
</style> 