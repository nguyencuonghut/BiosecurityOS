import apiClient from '@/api/client.js'

// ── Presigned Upload Flow ──────────────────────────────────────

export async function presignUpload(fileName, mimeType, entityType, entityId) {
  const { data } = await apiClient.post('/attachments/presign', {
    file_name: fileName,
    mime_type: mimeType,
    entity_type: entityType,
    entity_id: entityId,
  })
  return data.data // { attachment_id, upload_url, object_key }
}

export async function finalizeUpload(attachmentId, payload) {
  const { data } = await apiClient.post(`/attachments/${attachmentId}/finalize`, payload)
  return data.data
}

// ── Read / Download ────────────────────────────────────────────

export async function getAttachment(attachmentId) {
  const { data } = await apiClient.get(`/attachments/${attachmentId}`)
  return data.data
}

export async function getDownloadUrl(attachmentId) {
  const { data } = await apiClient.get(`/attachments/${attachmentId}/download`)
  return data.data // { download_url }
}

export async function getViewUrl(attachmentId) {
  const { data } = await apiClient.get(`/attachments/${attachmentId}/view`)
  return data.data // { view_url, file_name, mime_type }
}

// ── Delete ─────────────────────────────────────────────────────

export async function deleteAttachment(attachmentId) {
  await apiClient.delete(`/attachments/${attachmentId}`)
}

// ── Upload helper (presign → PUT → finalize) ──────────────────

export async function uploadFile(file, entityType, entityId, onProgress) {
  // Step 1: Get presigned URL
  const presign = await presignUpload(file.name, file.type, entityType, entityId)

  // Step 2: Upload directly to MinIO via presigned URL
  await new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('PUT', presign.upload_url)
    xhr.setRequestHeader('Content-Type', file.type)
    if (onProgress) {
      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable) onProgress(Math.round((e.loaded / e.total) * 100))
      }
    }
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(`Upload failed: ${xhr.status}`)))
    xhr.onerror = () => reject(new Error('Upload network error'))
    xhr.send(file)
  })

  // Step 3: Finalize
  const attachment = await finalizeUpload(presign.attachment_id, {
    file_size_bytes: file.size,
  })

  return attachment
}
