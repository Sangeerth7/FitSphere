export function getRows(data) {
  return Array.isArray(data) ? data : data?.results || [];
}
