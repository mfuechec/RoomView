/**
 * Client-side validation utilities
 */

const VALID_TYPES = ['image/png', 'image/jpeg', 'application/pdf']
const MAX_FILE_SIZE = 10 * 1024 * 1024 // 10MB
const MIN_FILE_SIZE = 10 * 1024 // 10KB

/**
 * Validate blueprint file before upload
 * @param {File} file - File to validate
 * @returns {Array<Object>} Array of validation errors
 */
export function validateBlueprint(file) {
  const errors = []

  if (!file) {
    errors.push({
      code: 'NO_FILE',
      message: 'No file selected',
      severity: 'error'
    })
    return errors
  }

  // Check file type
  if (!VALID_TYPES.includes(file.type)) {
    errors.push({
      code: 'INVALID_TYPE',
      message: 'Please upload PNG, JPG, or PDF files only',
      severity: 'error'
    })
  }

  // Check file size
  if (file.size > MAX_FILE_SIZE) {
    errors.push({
      code: 'FILE_TOO_LARGE',
      message: `File size (${(file.size / 1024 / 1024).toFixed(1)}MB) exceeds 10MB limit`,
      severity: 'error'
    })
  }

  if (file.size < MIN_FILE_SIZE) {
    errors.push({
      code: 'FILE_TOO_SMALL',
      message: 'File appears to be too small or corrupted',
      severity: 'warning'
    })
  }

  return errors
}

/**
 * Check if file is a valid image by checking magic bytes
 * @param {File} file - File to check
 * @returns {Promise<boolean>} True if valid image format
 */
export async function isValidImageFormat(file) {
  return new Promise((resolve) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      const arr = new Uint8Array(e.target.result)

      // Check PNG signature
      if (arr.length >= 8 &&
          arr[0] === 0x89 && arr[1] === 0x50 &&
          arr[2] === 0x4E && arr[3] === 0x47) {
        resolve(true)
        return
      }

      // Check JPEG signature
      if (arr.length >= 2 &&
          arr[0] === 0xFF && arr[1] === 0xD8) {
        resolve(true)
        return
      }

      // Check PDF signature
      if (arr.length >= 4 &&
          arr[0] === 0x25 && arr[1] === 0x50 &&
          arr[2] === 0x44 && arr[3] === 0x46) {
        resolve(true)
        return
      }

      resolve(false)
    }

    reader.onerror = () => resolve(false)

    reader.readAsArrayBuffer(file.slice(0, 8))
  })
}
