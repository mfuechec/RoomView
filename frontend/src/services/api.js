/**
 * API Service
 * Handles communication with RoomView backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000'

/**
 * Upload blueprint and detect rooms
 * @param {File} file - Blueprint image file
 * @param {number} maxRetries - Maximum retry attempts
 * @returns {Promise<Object>} Detection results
 */
export async function uploadBlueprint(file, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const formData = new FormData()
      formData.append('blueprint', file)

      const response = await fetch(`${API_BASE_URL}/detect`, {
        method: 'POST',
        body: formData
      })

      const data = await response.json()

      if (!response.ok) {
        throw {
          code: data.error_code || 'INTERNAL_ERROR',
          message: data.message || 'Failed to process blueprint',
          suggestions: data.suggestions,
          status: response.status
        }
      }

      return data
    } catch (error) {
      // Don't retry on 4xx errors (client errors)
      if (error.status >= 400 && error.status < 500) {
        throw error
      }

      // Retry on network/server errors
      if (attempt === maxRetries) {
        throw {
          code: 'NETWORK_ERROR',
          message: `Upload failed after ${maxRetries} attempts. Please check your connection.`,
          suggestions: ['Check your internet connection', 'Try again later']
        }
      }

      // Exponential backoff
      const delay = Math.pow(2, attempt - 1) * 1000
      await sleep(delay)

      console.log(`Retry attempt ${attempt}/${maxRetries} after ${delay}ms`)
    }
  }
}

/**
 * Sleep utility for retry delays
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>}
 */
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Mock API for development without backend
 * @param {File} file - Blueprint image file
 * @returns {Promise<Object>} Mock detection results
 */
export async function mockUploadBlueprint(file) {
  // Simulate network delay
  await sleep(2000)

  // Mock response
  return {
    status: 'success',
    blueprint_id: `bp_${Date.now()}_mock`,
    processing_time_seconds: 2.5,
    image_dimensions: {
      width_pixels: 2000,
      height_pixels: 1500
    },
    total_rooms_detected: 3,
    rooms: [
      {
        id: 'room_001',
        bounding_box_normalized: [0.1, 0.1, 0.4, 0.5],
        bounding_box_pixels: [200, 150, 800, 750],
        confidence_score: 0.92,
        type_hint: 'room',
        area_normalized: 0.12,
        area_pixels: 450000
      },
      {
        id: 'room_002',
        bounding_box_normalized: [0.5, 0.1, 0.9, 0.5],
        bounding_box_pixels: [1000, 150, 1800, 750],
        confidence_score: 0.88,
        type_hint: 'room',
        area_normalized: 0.16,
        area_pixels: 480000
      },
      {
        id: 'hallway_001',
        bounding_box_normalized: [0.1, 0.55, 0.9, 0.7],
        bounding_box_pixels: [200, 825, 1800, 1050],
        confidence_score: 0.75,
        type_hint: 'hallway',
        area_normalized: 0.12,
        area_pixels: 360000
      }
    ]
  }
}
