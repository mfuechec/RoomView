/**
 * Coordinate conversion utilities
 */

/**
 * Convert normalized coordinates (0.0-1.0) back to pixel coordinates
 * @param {Array<number>} normalizedBox - [x_min, y_min, x_max, y_max] in 0.0-1.0 range
 * @param {number} targetWidth - Target canvas width in pixels
 * @param {number} targetHeight - Target canvas height in pixels
 * @returns {Object} { x, y, width, height } in pixels
 */
export function denormalizeCoords(normalizedBox, targetWidth, targetHeight) {
  const [xMinNorm, yMinNorm, xMaxNorm, yMaxNorm] = normalizedBox

  return {
    x: Math.round(xMinNorm * targetWidth),
    y: Math.round(yMinNorm * targetHeight),
    width: Math.round((xMaxNorm - xMinNorm) * targetWidth),
    height: Math.round((yMaxNorm - yMinNorm) * targetHeight)
  }
}

/**
 * Convert pixel coordinates to normalized (0.0-1.0) coordinates
 * @param {Object} pixelBox - { x, y, width, height } in pixels
 * @param {number} imageWidth - Original image width
 * @param {number} imageHeight - Original image height
 * @returns {Array<number>} [x_min, y_min, x_max, y_max] in 0.0-1.0 range
 */
export function normalizeCoords(pixelBox, imageWidth, imageHeight) {
  const { x, y, width, height } = pixelBox

  return [
    parseFloat((x / imageWidth).toFixed(4)),
    parseFloat((y / imageHeight).toFixed(4)),
    parseFloat(((x + width) / imageWidth).toFixed(4)),
    parseFloat(((y + height) / imageHeight).toFixed(4))
  ]
}

/**
 * Calculate area from normalized coordinates
 * @param {Array<number>} normalizedBox - [x_min, y_min, x_max, y_max]
 * @returns {number} Area in normalized units (0.0-1.0)
 */
export function calculateNormalizedArea(normalizedBox) {
  const [xMin, yMin, xMax, yMax] = normalizedBox
  const width = xMax - xMin
  const height = yMax - yMin
  return parseFloat((width * height).toFixed(6))
}
